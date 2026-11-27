import json
import logging
import os
import random
import re
from datetime import datetime, timezone
from pathlib import Path

from locust import HttpUser, LoadTestShape, between, events, task

RESULTS_DIR = Path(__file__).resolve().parent / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
LOG = logging.getLogger("ccu4_locust")
LOG.setLevel(logging.INFO)
LOG.addHandler(logging.FileHandler(RESULTS_DIR / "fases.log", encoding="utf-8"))

TARGET_HOST = os.getenv("TARGET_HOST", "http://localhost:8000")
NORMAL_USERS = int(os.getenv("NORMAL_USERS", "10"))
PEAK_USERS = int(os.getenv("PEAK_USERS", "100"))
SPIKE_USERS = int(os.getenv("SPIKE_USERS", "150"))
RAMP_RATE = int(os.getenv("RAMP_RATE", "10"))
DURATIONS = {
    "normal": int(os.getenv("DURATION_NORMAL", "30")),
    "ramp_up": int(os.getenv("DURATION_RAMP", "60")),
    "spike": int(os.getenv("DURATION_SPIKE", "30")),
    "sustained": int(os.getenv("DURATION_SUSTAINED", "60")),
    "ramp_down": int(os.getenv("DURATION_RAMPDOWN", "60")),
    "recovery": int(os.getenv("DURATION_RECOVERY", "30")),
}


def timestamp():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def is_local_host(host):
    return re.fullmatch(r"https?://(localhost|127\.0\.0\.1)(:\d+)?/?", host) is not None


@events.init.add_listener
def verificar_destino(environment, **kwargs):
    if not is_local_host(TARGET_HOST) and os.getenv("ALLOW_REMOTE_TARGET") != "1":
        raise SystemExit(
            f"Destino remoto bloqueado: {TARGET_HOST}. Use el default local o "
            "configure ALLOW_REMOTE_TARGET=1 solo con autorizacion explícita."
        )


@events.test_start.add_listener
def inicio_prueba(environment, **kwargs):
    LOG.info(
        "%s INICIO host=%s normal=%d pico=%d spike=%d rampa=%d/s duraciones=%s",
        timestamp(), TARGET_HOST, NORMAL_USERS, PEAK_USERS, SPIKE_USERS, RAMP_RATE,
        json.dumps(DURATIONS, sort_keys=True),
    )


@events.test_stop.add_listener
def fin_prueba(environment, **kwargs):
    if environment.stats:
        LOG.info(
            "%s FIN total_requests=%d failures=%d avg_response_ms=%.1f max_response_ms=%d",
            timestamp(),
            environment.stats.total.num_requests,
            environment.stats.total.num_failures,
            environment.stats.total.avg_response_time,
            environment.stats.total.max_response_time,
        )


class CafeteriaUser(HttpUser):
    wait_time = between(0.5, 2.0)

    def on_start(self):
        self.pedidos = []
        self.nombre = f"Locust-{random.randint(1, 100000)}"
        self.menu_items = [1, 2, 4, 5]
        self.cargar_menu()

    def cargar_menu(self):
        with self.client.get("/menu", name="GET /menu", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"GET /menu devolvió {response.status_code}")
                return
            try:
                items = response.json()
                disponibles = [item["id"] for item in items if item.get("available")]
                if disponibles:
                    self.menu_items = disponibles
            except (ValueError, KeyError, TypeError):
                response.failure("GET /menu no devolvió un JSON válido")

    @task(4)
    def ver_menu(self):
        self.cargar_menu()

    @task(3)
    def hacer_pedido(self):
        items = [
            {"item_id": random.choice(self.menu_items), "quantity": random.randint(1, 3)}
            for _ in range(random.randint(1, 3))
        ]
        body = {"customer_name": self.nombre, "items": items}
        with self.client.post("/orders", json=body, name="POST /orders", catch_response=True) as response:
            if response.status_code != 201:
                response.failure(f"POST /orders devolvió {response.status_code}: {response.text[:120]}")
                return
            try:
                data = response.json()
                if "id" not in data or "total" not in data:
                    response.failure("POST /orders no devolvió id y total")
                    return
                self.pedidos.append(data["id"])
                if len(self.pedidos) > 50:
                    self.pedidos.pop(0)
            except ValueError:
                response.failure("POST /orders no devolvió JSON")

    @task(2)
    def consultar_pedido(self):
        if not self.pedidos:
            self.cargar_menu()
            return
        pedido_id = random.choice(self.pedidos)
        with self.client.get(
            f"/orders/{pedido_id}", name="GET /orders/{id}", catch_response=True
        ) as response:
            if response.status_code != 200:
                response.failure(f"GET /orders/{id} devolvió {response.status_code}")

    @task(1)
    def health(self):
        with self.client.get("/health", name="GET /health", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"GET /health devolvió {response.status_code}")


class EscenariosCafeteria(LoadTestShape):
    def __init__(self):
        super().__init__()
        self.fase_actual = None

    def cambiar_fase(self, fase, usuarios):
        if self.fase_actual != fase:
            self.fase_actual = fase
            LOG.info("%s FASE %s usuarios=%d", timestamp(), fase, usuarios)
            print(f"[{timestamp()}] FASE {fase}: {usuarios} usuarios", flush=True)

    def tick(self):
        elapsed = self.get_run_time()
        normal = NORMAL_USERS
        pico = max(PEAK_USERS, normal + 1)
        spike = max(SPIKE_USERS, pico + 1)
        acumulado = 0

        for fase, duracion in DURATIONS.items():
            fin = acumulado + duracion
            if elapsed < fin:
                dentro = elapsed - acumulado
                if fase == "normal":
                    usuarios = normal
                elif fase == "ramp_up":
                    usuarios = min(pico, normal + int(RAMP_RATE * dentro))
                elif fase == "spike":
                    usuarios = spike
                elif fase == "sustained":
                    usuarios = pico
                elif fase == "ramp_down":
                    usuarios = max(normal, pico - int(RAMP_RATE * dentro))
                else:
                    usuarios = normal
                self.cambiar_fase(fase, usuarios)
                return usuarios, RAMP_RATE
            acumulado = fin

        self.cambiar_fase("finalizada", 0)
        return None
