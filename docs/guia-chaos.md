# Guía de chaos engineering

Responsable: Johana. Script: `chaos/run_chaos.ps1`. Se ejecuta contra el stack local aislado (`docker-compose.yml`), nunca contra AWS ni ambientes compartidos sin autorización.

## Principios

- No se eliminan contenedores, volúmenes, bases de datos ni recursos de otros integrantes: solo `stop`, `start` y `restart` de `api` y `web`.
- Toda falla inyectada tiene recuperación automática en un bloque `finally`.
- El objetivo por defecto debe ser `localhost` o `127.0.0.1`; otra URL se rechaza salvo `-AllowRemoteTarget`.
- Se crea un pedido real antes del caos para comprobar persistencia en Postgres.

## Criterios de éxito

| Escenario | Acción | Criterio verificable |
|---|---|---|
| Caída de un contenedor | `docker compose stop api` | `/health` deja de responder en menos de 30 s |
| Recuperación de la API | `docker compose start api` | `/health` responde 2xx en menos de 90 s |
| Persistencia de pedidos | consultar el pedido creado antes del caos | mismo `id` y `customer_name` |
| Reinicio de la API | `docker compose restart api` | `/health` responde 2xx en menos de 90 s |
| Pérdida temporal de un nodo | `docker compose stop web` | la API sigue disponible |
| Recuperación del frontend | `docker compose start web` | `http://localhost:3000` responde 2xx |
| Reverse proxy | inspección de contenedores | `pendiente` si Jesús aún no lo despliega; no se marca como éxito |
| Recuperación final | estado al salir | API y web activos, informe JSON escrito |

## Ejecución

```powershell
cp .env.example .env
docker compose up -d --build

powershell -ExecutionPolicy Bypass -File .\chaos\run_chaos.ps1
```

El informe se guarda en `chaos/results/chaos-<fecha-hora>.json` con timestamp por escenario. Cualquier criterio fallido produce código de salida 1.

### Recuperación durante carga

1. Iniciar Locust en otra terminal con `docs/guia-locust.md` y anotar su PID.
2. Ejecutar `run_chaos.ps1 -LoadPid <PID>`.
3. El informe registra si el proceso de carga sigue activo en cada fase y si `/health` se recupera sin detener la prueba.
4. Crucar el JSON de chaos con `loadtest/results/fases.log` y con los graficos de Grafana.

## Pérdida de un nodo AWS

No se simula en este script: terminar una instancia real sería un cambio en infraestructura de Emilio y requeriría autorización explícita. Cuando el controller exista, su drenado y terminación se verifican con los logs de boto3 y con la marca de tiempo de Locust, respetando el límite de 5 a 10 minutos del README.

## Estado de ejecución

Ejecutado el 2026-11-27 de 13:13:36 a 13:13:50 -08:00 contra el stack local. Informe canónico: `chaos/results/chaos-20261127-131336.json`. Resultado: ocho escenarios en `ok` y `reverse_proxy` en `pendiente`, código de salida 0. El pedido 4231 permaneció íntegro tras el reinicio de la API y el stack quedó recuperado.

La raíz de la API responde 404, por lo que el script usa `/health` para las comprobaciones de disponibilidad. Detalle: `docs/evidencia/2026-11-27-1314-stack-monitoreo-carga-chaos.md`.
