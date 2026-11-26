import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import timezone

import redis
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, StrictInt, StringConstraints
from starlette.exceptions import HTTPException
from typing_extensions import Annotated

from .cache import client as cache
from .db import init_db, pool

log = logging.getLogger("uvicorn.error")

MENU_KEY = "menu"
MENU_TTL_SECONDS = 60


@asynccontextmanager
async def lifespan(app: FastAPI):
    pool.open(wait=True, timeout=30)
    init_db()
    yield
    pool.close()


app = FastAPI(title="Cafeteria API", lifespan=lifespan)

# The frontend runs on a different port, so the browser needs CORS.
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


# ---------- Errors: every error uses {"error": ..., "message": ...} ----------

class ApiError(Exception):
    def __init__(self, status: int, error: str, message: str):
        self.status, self.error, self.message = status, error, message


def error_response(status: int, error: str, message: str) -> JSONResponse:
    return JSONResponse({"error": error, "message": message}, status_code=status)


@app.exception_handler(ApiError)
def handle_api_error(request: Request, exc: ApiError):
    return error_response(exc.status, exc.error, exc.message)


@app.exception_handler(RequestValidationError)
def handle_validation_error(request: Request, exc: RequestValidationError):
    return error_response(400, "INVALID_REQUEST", "La petición está mal formada o le faltan campos")


@app.exception_handler(HTTPException)
def handle_http_error(request: Request, exc: HTTPException):
    error = "NOT_FOUND" if exc.status_code == 404 else "HTTP_ERROR"
    return error_response(exc.status_code, error, str(exc.detail))


@app.exception_handler(Exception)
def handle_unexpected_error(request: Request, exc: Exception):
    log.error("Unexpected error: %r", exc)
    return error_response(500, "INTERNAL_ERROR", "Error interno del servidor")


# ---------- Request body ----------

class OrderItemIn(BaseModel):
    item_id: Annotated[StrictInt, Field(ge=1, le=2_147_483_647)]
    quantity: Annotated[StrictInt, Field(ge=1, le=100)]


class OrderIn(BaseModel):
    customer_name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100, pattern=r"^[^\x00]*$")]
    items: Annotated[list[OrderItemIn], Field(min_length=1, max_length=50)]


# ---------- Endpoints ----------

@app.get("/health")
def health():
    result = {"status": "ok", "db": "ok", "cache": "ok"}
    try:
        with pool.connection(timeout=2) as conn:
            conn.execute("SELECT 1")
    except Exception:
        result["db"] = result["status"] = "error"
    try:
        cache.ping()
    except redis.RedisError:
        result["cache"] = result["status"] = "error"
    return JSONResponse(result, status_code=200 if result["status"] == "ok" else 503)


@app.get("/menu")
def get_menu():
    # If Redis fails, the menu still works by reading from Postgres.
    try:
        cached = cache.get(MENU_KEY)
        if cached:
            return json.loads(cached)
    except redis.RedisError:
        log.warning("Redis unavailable, reading menu from Postgres")

    with pool.connection() as conn:
        rows = conn.execute("SELECT id, name, price, available FROM menu_items ORDER BY id").fetchall()
    menu = [{**row, "price": float(row["price"])} for row in rows]

    try:
        cache.set(MENU_KEY, json.dumps(menu), ex=MENU_TTL_SECONDS)
    except redis.RedisError:
        pass
    return menu


def fetch_order(conn, order_id: int):
    order = conn.execute("SELECT * FROM orders WHERE id = %s", (order_id,)).fetchone()
    if order is None:
        return None
    items = conn.execute(
        "SELECT item_id, quantity FROM order_items WHERE order_id = %s ORDER BY position",
        (order_id,),
    ).fetchall()
    return {
        "id": order["id"],
        "customer_name": order["customer_name"],
        "items": items,
        "total": float(order["total"]),
        "status": order["status"],
        "receipt_status": order["receipt_status"],
        "receipt_url": order["receipt_url"],
        "created_at": order["created_at"].astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


@app.post("/orders", status_code=201)
def create_order(body: OrderIn):
    # One transaction: the whole order is saved, or nothing is.
    with pool.connection() as conn:
        ids = list({item.item_id for item in body.items})
        rows = conn.execute(
            "SELECT id, price FROM menu_items WHERE available AND id = ANY(%s)", (ids,)
        ).fetchall()
        prices = {row["id"]: row["price"] for row in rows}

        for item in body.items:
            if item.item_id not in prices:
                raise ApiError(400, "ITEM_UNAVAILABLE", f"El producto {item.item_id} no existe o no está disponible")

        # The server calculates the total, using Decimal to avoid rounding errors.
        total = sum(prices[item.item_id] * item.quantity for item in body.items)

        order_id = conn.execute(
            "INSERT INTO orders (customer_name, total) VALUES (%s, %s) RETURNING id",
            (body.customer_name, total),
        ).fetchone()["id"]

        for position, item in enumerate(body.items):
            conn.execute(
                "INSERT INTO order_items (order_id, position, item_id, quantity) VALUES (%s, %s, %s, %s)",
                (order_id, position, item.item_id, item.quantity),
            )
        order = fetch_order(conn, order_id)

    # Phase 2: publish the "order created" event for the receipt Lambda here.
    return order


@app.get("/orders/{order_id}")
def get_order(order_id: int):
    with pool.connection() as conn:
        order = fetch_order(conn, order_id)
    if order is None:
        raise ApiError(404, "ORDER_NOT_FOUND", f"No existe un pedido con id {order_id}")
    return order
