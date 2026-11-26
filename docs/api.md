# Contrato de la API · Cafetería

Este documento define cómo se comunica la API con el frontend, el proxy, el controller y las pruebas de carga. **Si alguien necesita cambiar algo de aquí, lo avisa al equipo antes de cambiarlo en el código.**

## Datos generales

| Concepto | Valor |
|---|---|
| URL base (local) | `http://localhost:8000` |
| Formato | JSON en peticiones y respuestas (`Content-Type: application/json`) |
| Autenticación | Ninguna (fuera del alcance del proyecto) |
| Estado | La API es **stateless**: no guarda sesiones ni datos en memoria. Todo vive en Postgres o en Redis |

### Formato de errores

Todos los errores regresan el mismo formato:

```json
{
  "error": "ORDER_NOT_FOUND",
  "message": "No existe un pedido con id 42"
}
```

| Código | Cuándo |
|---|---|
| `400` | El body está mal formado o le faltan campos |
| `404` | El recurso no existe |
| `500` | Error interno del servidor |

---

## Modelos

### MenuItem

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | entero | Identificador del producto |
| `name` | texto | Nombre del producto |
| `price` | decimal | Precio en MXN |
| `available` | booleano | Si se puede pedir |

### Order

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | entero | Identificador del pedido |
| `customer_name` | texto | Nombre del cliente |
| `items` | lista de `{ item_id, quantity }` | Productos del pedido |
| `total` | decimal | Total calculado por la API (el cliente **no** lo manda) |
| `status` | texto | `pending`, `preparing` o `ready` |
| `receipt_status` | texto | `pending` o `generated` (lo actualiza la Lambda en la Fase 2) |
| `receipt_url` | texto o `null` | Enlace al recibo en S3 cuando ya se generó |
| `created_at` | fecha ISO 8601 | Fecha y hora de creación |

---

## Endpoints

### `GET /health`

Revisión de salud. La usan el reverse proxy y el controller para saber si un nodo está vivo.

**Respuesta `200`**
```json
{
  "status": "ok",
  "db": "ok",
  "cache": "ok"
}
```

Si Postgres o Redis no responden, regresa `503` con el servicio que falló marcado como `"error"`.

---

### `GET /menu`

Lista los productos del menú. Se guarda en cache en Redis para no consultar Postgres en cada petición.

**Respuesta `200`**
```json
[
  { "id": 1, "name": "Americano", "price": 45.00, "available": true },
  { "id": 2, "name": "Latte", "price": 60.00, "available": true },
  { "id": 3, "name": "Croissant", "price": 40.00, "available": false }
]
```

---

### `POST /orders`

Crea un pedido. La API calcula el total, lo guarda en Postgres y, a partir de la Fase 2, deja un evento (SQS o S3) para que la Lambda genere el recibo de forma asíncrona.

**Body**
```json
{
  "customer_name": "Ana",
  "items": [
    { "item_id": 1, "quantity": 2 },
    { "item_id": 2, "quantity": 1 }
  ]
}
```

**Respuesta `201`**
```json
{
  "id": 42,
  "customer_name": "Ana",
  "items": [
    { "item_id": 1, "quantity": 2 },
    { "item_id": 2, "quantity": 1 }
  ],
  "total": 150.00,
  "status": "pending",
  "receipt_status": "pending",
  "receipt_url": null,
  "created_at": "2026-11-27T12:00:00Z"
}
```

**Errores**
- `400` si `items` está vacío, falta `customer_name` o `quantity` es menor a 1.
- `400` si algún `item_id` no existe o no está disponible.

---

### `GET /orders/{id}`

Consulta un pedido por su id.

**Respuesta `200`:** el mismo formato que la respuesta de `POST /orders`.

**Errores**
- `404` si el pedido no existe.

---

## Pendientes para fases siguientes

- **Fase 2:** definir el formato del evento que recibe la Lambda (cola SQS o archivo en S3) y cómo actualiza `receipt_status` y `receipt_url`.
- **Fase 3:** agregar un endpoint que consuma CPU a propósito durante la prueba de carga, para que el controller tenga una métrica clara para escalar. Ejemplo: `POST /orders/quote`, que calcula un presupuesto con un cálculo pesado.
- **Fase 3:** confirmar con Johana si la API expone un endpoint `/metrics` para Prometheus.
