# Evidencia real: stack local, monitoreo, Locust y chaos

Fecha y hora: 2026-11-27 13:14 -08:00 (21:14 UTC).
Responsable: Johana. Todo lo registrado aquí se ejecutó en la raíz del repositorio, rama `feature/johana-sre`, sin recursos AWS reales.

## Comandos ejecutados

```powershell
docker compose up -d --build
docker compose -f infra/monitoring/docker-compose.monitoring.yml up -d --build
powershell -ExecutionPolicy Bypass -File ./loadtest/run_loadtest.ps1
powershell -ExecutionPolicy Bypass -File ./chaos/run_chaos.ps1
```

## Stack principal

`docker compose ps` mostró `api`, `web`, `postgres` y `redis` activos; Postgres y Redis en estado `healthy`.

`GET http://localhost:8000/health` respondió:

```json
{"status":"ok","db":"ok","cache":"ok"}
```

También se verificaron `GET /menu` (200), `POST /orders` (201, pedido 1 por 90.0) y `GET /orders/1` (200, cliente `SRE-Verificacion`). `GET http://localhost:3000` devolvió 200.

## Prometheus y Grafana

- Targets activos: `app-exporter`, `docker-exporter` y `prometheus`, los tres con `health=up`.
- `cafeteria_probe_up`: 2 series (health y menu).
- `cafeteria_container_running`: 9 series con valor 1, incluidos `api`, `web`, `postgres`, `redis` y los cuatro contenedores de monitoreo.
- Reglas: 2 grupos, 8 reglas, todas con `health=ok`; `ContainerHighCPU` en `pending` y las demás `inactive`.
- Grafana: 1 datasource `Prometheus` con UID `prometheus-ccu4` y 1 dashboard `CCU4 · Estado general de la cafetería`.

Durante la verificación se corrigió el exporter de Docker: Python 3.13 no acepta `unix_socket` en `http.client.HTTPConnection`, por lo que ahora usa un socket `AF_UNIX` propio y rutas versionadas `/v1.41/...`. Tras el rebuild, `cafeteria_docker_exporter_errors_total=0`.

## Locust contra la API real

Archivos generados: se versionan `loadtest/results/fases.log` y `loadtest/results/locust-20261127-130704_{stats,stats_history,failures,exceptions}.csv`. Se excluye `locust-20261127-130704-report.html` (~1 MB) por ser derivable con Locust y no aportar datos nuevos.

Registro de fases:

| Hora UTC | Fase | Usuarios |
|---|---|---:|
| 21:07:07Z | inicio / normal | 10 |
| 21:07:37Z | ramp_up | 11 |
| 21:08:38Z | spike | 150 |
| 21:09:08Z | sustained | 100 |
| 21:10:08Z | ramp_down | 91 |
| 21:11:08Z | recovery | 10 |
| 21:11:38Z | finalizada | 0 |

Resultado final de `fases.log`: `total_requests=14076 failures=0 avg_response_ms=22.6 max_response_ms=195`, código de salida 0.

Snapshot agregado del CSV `locust-20261127-130704_stats.csv`: 14,073 peticiones, 0 fallos, promedio 22.64 ms, p95 84 ms, 52.10 req/s. La diferencia de tres peticiones con el log se debe al cierre del runner.

| Endpoint | Peticiones | Fallos | Promedio (ms) | p95 (ms) | req/s |
|---|---:|---:|---:|---:|---:|
| `GET /health` | 1,361 | 0 | 8.18 | 15 | 5.04 |
| `GET /menu` | 5,772 | 0 | 8.91 | 19 | 21.37 |
| `GET /orders/{id}` | 2,716 | 0 | 8.08 | 15 | 10.06 |
| `POST /orders` | 4,224 | 0 | 55.42 | 70 | 15.64 |

No se correlacionó con AWS: el controller de Emilio no existe todavía y no se autorizó crear instancias.

## Chaos engineering

Informe canónico: `chaos/results/chaos-20261127-131336.json`. Pedido de referencia: 4231. Código de salida: 0.

| Escenario | Estado | Hora local |
|---|---|---|
| `precondicion_pedido` | ok | 13:13:36 |
| `caida_api` | ok | 13:13:37 |
| `recuperacion_api` | ok | 13:13:41 |
| `persistencia_pedidos` | ok | 13:13:41 |
| `reinicio_api` | ok | 13:13:45 |
| `perdida_nodo_web` | ok | 13:13:48 |
| `recuperacion_web` | ok | 13:13:49 |
| `reverse_proxy` | pendiente | 13:13:50 |
| `recuperacion_final` | ok | 13:13:50 |

El pedido 4231 quedó íntegro tras reiniciar la API. No se borraron volúmenes ni recursos ajenos. `reverse_proxy` sigue pendiente porque Jesús aún no despliega ese componente.

Durante la ejecución se corrigieron tres defectos del propio script: la precondición consultaba la raíz de la API (404) en lugar de `/health`, el wrapper de Docker convertía la salida de progreso en error terminante, y PowerShell 5.1 necesita BOM para interpretar los acentos del archivo.

## Estado de la evidencia

- Obtenida: stack local, endpoints reales, targets de Prometheus, datos en Grafana, Locust real y chaos real.
- Pendiente y fuera del alcance de Johana: correlación con AWS, captura de Floci, captura visual de GHCR Packages y reverse proxy de Jesús.
