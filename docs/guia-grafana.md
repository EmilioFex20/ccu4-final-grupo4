# Guía de Grafana

Responsable: Johana. Grafana se aprovisiona automáticamente desde `infra/monitoring/grafana/`.

## Archivos versionados

| Archivo | Función |
|---|---|
| `grafana/provisioning/datasources/prometheus.yml` | Datasource `Prometheus`, UID `prometheus-ccu4`, URL `http://prometheus:9090`, predeterminado y no editable desde la UI |
| `grafana/provisioning/dashboards/dashboards.yml` | Proveedor de archivos, carpeta `CCU4`, sin borrado ni edición desde la UI |
| `grafana/dashboards/ccu4-overview.json` | Dashboard “CCU4 · Estado general de la cafetería” |
| `docker-compose.monitoring.yml` | Persistencia en volumen `grafana-data`; credencial cargada desde `.env` local ignorado |

## Arranque

```powershell
cd infra/monitoring
cp .env.example .env
# Definir GF_SECURITY_ADMIN_PASSWORD solo en el .env local antes de arrancar
docker compose -f docker-compose.monitoring.yml up -d --build
```

Abrir http://localhost:3001. El primer arranque crea la carpeta `CCU4` y el dashboard sin intervención manual. Si el dashboard no aparece, revisar `docker compose -f docker-compose.monitoring.yml logs grafana`.

## Configuración segura de credenciales

- `.env.example` deja `GF_SECURITY_ADMIN_PASSWORD=` vacío: no contiene credenciales reales ni valores de ejemplo reutilizables.
- El Compose usa `env_file: .env`; la contraseña no aparece como literal en ningún archivo versionado.
- `.env` está ignorado por Git y debe permanecer solo en la máquina local. Nunca se sube al repositorio ni a las evidencias.
- Si el volumen `grafana-data` ya existe, cambiar la variable de entorno no actualiza la contraseña guardada en la base de Grafana. La rotación debe hacerse con la CLI de Grafana dentro del contenedor, conservando el volumen.
- Detalle del incidente y verificación: [`incidente-gitguardian-41459752.md`](incidente-gitguardian-41459752.md).

## Dashboard

Paneles con unidades correctas y ventana temporal configurable:

1. Disponibilidad de `/health` en ventana de 5 minutos (`%`).
2. Sondas por segundo (`reqps`).
3. Tasa de errores de sonda (`reqps`).
4. Contenedores en ejecución (entero).
5. Latencia promedio y p95 de sondas (segundos).
6. Tráfico de sondas por endpoint (`reqps`).
7. Tasa de errores HTTP de sondas (`percentunit`).
8. Tabla de estado actual de endpoints.
9. CPU por contenedor (núcleos).
10. Memoria por contenedor (`bytes`).
11. Targets de Prometheus (`up`).
12. Panel de texto con los contratos pendientes de escalamiento, proxy y AWS.

Variables: `endpoint`, `container` y `job`, todas multi-selección con opción “All”. El rango temporal por defecto es `now-1h` a `now`, con refresco automático cada 30 segundos. El historial se conserva en el volumen de Prometheus durante 15 días.

**No hay paneles con métricas inventadas.** El panel 12 explica qué señales faltan y cómo integrarlas. RPS, latencia y errores mostrados corresponden a las sondas del exportador, no al tráfico real de Locust; para medir el tráfico real se necesita autorización de Carlos para instrumentar la API.

## Verificación

- En `Administration > Data sources`, debe existir `Prometheus` con UID `prometheus-ccu4` y estado verde.
- En la carpeta `CCU4`, debe existir el dashboard con 12 paneles.
- Al seleccionar un rango de 1 hora con tráfico real, los paneles muestran datos; sin stack levantado, las sondas aparecen en 0 y el panel de texto sigue siendo válido.
- Los cambios en el JSON se recargan automáticamente cada 30 segundos (o al reiniciar Grafana).
