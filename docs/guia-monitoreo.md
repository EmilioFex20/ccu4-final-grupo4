# Guía de monitoreo · Prometheus

Responsable: Johana. Los archivos viven en `infra/monitoring/` y se levantan con un Compose complementario, sin modificar `docker-compose.yml` de Carlos ni el pipeline de Jesús.

## Qué se mide hoy

| Requisito | Métrica real disponible | Origen |
|---|---|---|
| Estado de servicios | `cafeteria_probe_up`, `cafeteria_container_running`, `up` | app-exporter, docker-exporter, Prometheus |
| Disponibilidad de la API | `avg_over_time(cafeteria_probe_up{endpoint="health"}[5m])` | sonda real a `GET /health` |
| Solicitudes por segundo | `cafeteria_probe_requests_total` | sondas del exportador (**no** tráfico de clientes) |
| Latencia promedio y p95 | `cafeteria_probe_duration_seconds_*` | sondas reales a `/health` y `/menu` |
| Tasa de errores HTTP | `cafeteria_probe_errors_total`, `cafeteria_probe_http_responses_total` | sondas reales |
| CPU y memoria | `cafeteria_container_cpu_seconds_total`, `cafeteria_container_memory_bytes` | Docker Engine API de contenedores reales |
| Estado de instancias | `cafeteria_container_running`, `cafeteria_container_restart_count` | Docker Engine API |
| Escalamiento y controller | Sin métricas: `targets.d/controller.json` está vacío | Depende de Emilio |
| Reverse proxy | Sin métricas: `targets.d/reverse-proxy.json` está vacío | Depende de Jesús |
| Tráfico local vs AWS | Sin datos de origen; no se muestra como dato | Depende del controller |

La API actual (`api/app/main.py`) solo expone `/health`, `/menu`, `POST /orders` y `/orders/{id}`. No se le agregó `/metrics` porque eso modificaría código de Carlos: `docs/api.md` lo deja como decisión pendiente. Tampoco se agregó un proxy propio porque eso sustituiría el ruteo de Jesús. Las métricas anteriores son reales y están nombradas explícitamente como sondas.

## Arquitectura de monitoreo

- `prometheus/prometheus.yml`: scrapea Prometheus, app-exporter, docker-exporter y dos jobs `file_sd_configs`.
- `prometheus/rules/cafeteria-alerts.yml`: ocho alertas sobre métricas existentes.
- `prometheus/targets.d/*.json`: archivos de descubrimiento versionados; hoy contienen `[]` (sin destinos inventados).
- `exporters/app_exporter.py`: sondea endpoints configurables con `urllib` y expone en `:9101`.
- `exporters/docker_exporter.py`: consulta `/containers/json` y `/containers/{id}/stats` por el socket de Docker y expone en `:9102`.
- `docker-compose.monitoring.yml`: Prometheus, ambos exportadores y Grafana, en red `monitoring` más la red externa de la app.
- Volúmenes `prometheus-data` (TSDB con retención de 15 días) y `grafana-data` (SQLite y configuración).

## Seguridad del socket de Docker

- `/var/run/docker.sock` se monta solo en `docker-exporter` con `:ro` y sin mapping `ports`.
- `docker-exporter` pertenece únicamente a la red interna `monitoring`; Prometheus lo consulta en `:9102` dentro de Compose.
- El código usa solo `GET` versionados `/v1.41/...` y rechaza `DOCKER_HOST` con esquema distinto de `unix`; no existe fallback TCP.
- Riesgo residual: el socket de Docker equivale a acceso al daemon. Cualquier código ejecutado dentro de ese contenedor podría abusar de él; por eso no debe exponerse ni ejecutar código de terceros.

## Puesta en marcha

Requisitos: Docker daemon activo y el stack principal levantado desde la raíz del repo (crea la red `ccu4-final-grupo4_default`).

```powershell
cp .env.example .env
docker compose up -d --build

cd infra/monitoring
cp .env.example .env
docker compose -f docker-compose.monitoring.yml up -d --build
```

- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001 (usuario por defecto `admin`, password de `.env`)
- Estado de targets: http://localhost:9090/targets
- Alertas: http://localhost:9090/alerts

Para bajar solo monitoreo: `docker compose -f docker-compose.monitoring.yml down` (sin `-v`, para conservar datos). Para bajar todo: `docker compose down`.

## Configuración

Variables en `infra/monitoring/.env`:

| Variable | Descripción | Valor por defecto |
|---|---|---|
| `GRAFANA_ADMIN_USER` | usuario admin de Grafana | `admin` |
| `GRAFANA_ADMIN_PASSWORD` | obligatoria; sin valor el Compose falla | — |
| `GRAFANA_PORT` | puerto host de Grafana | `3001` |
| `PROMETHEUS_PORT` | puerto host de Prometheus | `9090` |
| `APP_NETWORK` | red externa del stack principal | `ccu4-final-grupo4_default` |
| `PROBE_TARGETS` | lista `nombre=url` separada por comas | `health=http://api:8000/health,menu=http://api:8000/menu` |
| `PROBE_INTERVAL_SECONDS` | intervalo de sondas | `15` |
| `PROBE_TIMEOUT_SECONDS` | timeout por sonda | `3` |
| `COLLECT_INTERVAL_SECONDS` | intervalo del exporter de Docker | `15` |

Si se ejecuta la API directamente en el host (sin Docker), cambiar `PROBE_TARGETS` a `health=http://host.docker.internal:8000/health,...`.

## Integración del controller y el proxy

No se modificaron sus archivos. Cuando Emilio o Jesús tengan endpoints de métricas, deben escribir un archivo JSON válido, por ejemplo:

```json
[{"targets": ["controller:9100"], "labels": {"componente": "controller"}}]
```

en `infra/monitoring/prometheus/targets.d/controller.json` o `reverse-proxy.json`. Prometheus recarga el archivo cada 30 segundos. Solo entonces aparecerán los paneles de escalamiento y ruteo.

## Validación

```powershell
python -c "import json,pathlib; json.loads(pathlib.Path('infra/monitoring/grafana/dashboards/ccu4-overview.json').read_text(encoding='utf-8')); print('dashboard JSON OK')"
docker compose -f infra/monitoring/docker-compose.monitoring.yml --env-file infra/monitoring/.env.example config --quiet
docker run --rm -v ${PWD}/infra/monitoring/prometheus:/etc/prometheus prom/prometheus:v2.55.0 promtool check config /etc/prometheus/prometheus.yml
```

La última validación requiere Docker daemon y se reportará como pendiente si no está disponible. Las alertas no tienen Alertmanager configurado: se visualizan en `/alerts` de Prometheus; integrar Alertmanager queda como mejora futura y no se simularon notificaciones.

## Seguridad

El exporter de Docker monta `/var/run/docker.sock` en modo solo lectura. El socket equivale a acceso root sobre el daemon: usarlo solo en entorno local de pruebas, sin exponer sus puertos fuera del host y con el Compose complementario desactivado en producción hasta revisar permisos.
