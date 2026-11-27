# Contratos de integración con el equipo

Responsable: Johana. Este documento evita que el monitoreo, la carga o el chaos modifiquen responsabilidades de Emilio, Jesús o Carlos.

| Componente | Responsable | Estado en el repositorio | Contrato que necesita Johana | Efecto hoy |
|---|---|---|---|---|
| API y endpoints `/health`, `/menu`, `/orders` | Carlos | Implementados y verificados por el pipeline | Ninguno para sondas; para RPS/latencia real se requiere autorización para agregar `/metrics` con `prometheus_client` | Se miden sondas reales, no tráfico de clientes |
| `docker-compose.yml` y Dockerfiles | Carlos | Implementados | Solo se usa como red externa `ccu4-final-grupo4_default` | Compose de monitoreo es complementario; no se editó el original |
| Reverse proxy | Jesús | Aún no existe | Escribir `infra/monitoring/prometheus/targets.d/reverse-proxy.json` con `[{"targets":["host:puerto"]}]` cuando exponga métricas | Job `reverse-proxy` configurado con `[]`; sin métricas inventadas |
| Pipeline y GHCR | Jesús | Implementado y en verde | Ninguno; no se tocó `ci.yml` | Evidencia de pipeline y push obtenida de logs |
| Floci | Emilio | Archivos de tareas presentes | Confirmar red y nombre de contenedores si se desea scrapear desde Floci | Sin cambios; evidencia pendiente |
| Scripts AWS boto3 y controller | Emilio | Aún no existen | Registrar `targets.d/controller.json`; publicar métricas con etiquetas de fase/origen para escalamiento y local vs AWS | Sin paneles de escalamiento con datos |
| IAM policy del auto-scaler | Johana + Emilio | Creada en AWS como `CCU4-RestrictEC2MicroInstances`; no adjuntada | El controller debe pasar `InstanceType` explícito y operar en `us-east-1`; además debe adjuntarse la política | Si Emilio necesita otro tipo/región, se coordina cambio de política |
| Budget de 1 USD | Johana | Creado en AWS como `CCU4-Budget-1USD`; 1.00 USD mensuales y alerta configurada | Emilio debe terminar instancias; el budget solo avisa | Sin evidencia de entrega de correo ni de gasto real |
| Lambda y recibos | Carlos | Aún no existe | Definir el evento `order created` para extender Locust con esa ruta | No se simula el evento |

## Reglas que se respetaron

- No se agregó `/metrics` a `api/app/main.py`: sería una modificación directa de Carlos.
- No se creó un proxy propio ni se cambió el flujo HTTP: pertenece a Jesús.
- No se escribieron scripts boto3 ni se crearon instancias: pertenece a Emilio y requiere autorización.
- No se eliminaron archivos, volúmenes ni contenedores de los demás integrantes.
- Los archivos de `targets.d/` están vacíos a propósito: Prometheus los lee, pero no genera series falsas.
