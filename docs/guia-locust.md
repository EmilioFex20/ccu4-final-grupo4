# Guía de pruebas de carga con Locust

Responsable: Johana. Los scripts usan el contrato real de [`docs/api.md`](api.md) y el destino por defecto es el ambiente local `http://localhost:8000`.

## Endpoints probados

| Endpoint | Uso en la prueba | Validación |
|---|---|---|
| `GET /menu` | Clientes consultan el menú (peso 4) y se usa para elegir `item_id` disponibles | 200 y JSON con `id`/`available` |
| `POST /orders` | Clientes hacen pedidos (peso 3) con `customer_name` e `items` | 201 y JSON con `id` y `total` |
| `GET /orders/{id}` | Clientes consultan pedidos creados por la prueba (peso 2) | 200 |
| `GET /health` | Disponibilidad (peso 1) | 200; otro código cuenta como fallo |

IDs de pedido se guardan por usuario (máximo 50) para consultar pedidos reales, sin inventar identificadores.

## Escenarios

`EscenariosCafeteria` es un `LoadTestShape` con siete fases consecutivas:

| Fase | Usuarios | Duración por defecto |
|---|---|---|
| normal | `NORMAL_USERS` (10) | 30 s |
| incremento gradual | hasta `PEAK_USERS` (100) a `RAMP_RATE` (10) usuarios/s | 60 s |
| pico | `SPIKE_USERS` (150) | 30 s |
| carga sostenida | `PEAK_USERS` (100) | 60 s |
| disminución | baja a `NORMAL_USERS` a `RAMP_RATE` usuarios/s | 60 s |
| recuperación | `NORMAL_USERS` (10) | 30 s |
| finalización | el shape devuelve `None` y Locust se detiene | — |

Duración total por defecto: 270 segundos (4.5 minutos), dentro de la ventana de 5 a 10 minutos que el README exige para instancias AWS.

## Ejecución

```powershell
cd loadtest
powershell -ExecutionPolicy Bypass -File .\run_loadtest.ps1
```

Ejemplo con otro destino y parámetros (solo con autorización para ese destino):

```powershell
powershell -ExecutionPolicy Bypass -File .\run_loadtest.ps1 -TargetHost http://localhost:8000 -NormalUsers 5 -PeakUsers 40 -RampRate 5 -AllowRemoteTarget
```

En Linux:

```bash
cd loadtest && ./run_loadtest.sh
```

La variable `TARGET_HOST` debe ser `localhost` o `127.0.0.1`; cualquier otro destino se bloquea a menos que se defina `ALLOW_REMOTE_TARGET=1`. Esto evita enviar tráfico a AWS o ambientes compartidos por accidente.

### Variables

`TARGET_HOST`, `NORMAL_USERS`, `PEAK_USERS`, `SPIKE_USERS`, `RAMP_RATE`, `DURATION_NORMAL`, `DURATION_RAMP`, `DURATION_SPIKE`, `DURATION_SUSTAINED`, `DURATION_RAMPDOWN`, `DURATION_RECOVERY`.

## Resultados

Cada ejecución genera en `loadtest/results/`:

- `locust-<fecha-hora>_stats.csv`: tipo de petición, número, fallos, RPS, min, max, promedio y percentiles (50/90/95/99).
- `locust-<fecha-hora>_stats_history.csv`: serie temporal de las métricas.
- `locust-<fecha-hora>_failures.csv` y `_exceptions.csv`.
- `locust-<fecha-hora>-report.html`: informe HTML.
- `fases.log`: marca de inicio, fin y cambio de fase con timestamp UTC.

Estos archivos están ignorados por Git por defecto (`.gitignore` cubre `loadtest/results/`). Para esta entrega se versionan de forma selectiva `fases.log` y los cuatro CSV de la ejecución `20261127-130704`; el HTML se genera localmente pero no se sube por tamaño. El resumen con fecha, hora y comandos exactos está en `docs/evidencia/`.

## Correlación con AWS

`fases.log` registra cuándo aumenta y disminuye la carga con sello de tiempo. Para correlacionar con el controller de Emilio:

1. Anotar la hora del inicio de la fase `ramp_up` y de `ramp_down`.
2. Comparar con los logs de `RunInstances` y `TerminateInstances` del controller.
3. Adjuntar ambos registros en la misma evidencia y verificar que ninguna instancia supere los 10 minutos de vida.

Sin el controller disponible, la prueba sigue siendo válida para medir la API local, pero no se debe afirmar que hubo escalamiento.

## Estado de ejecución

Ejecutada el 2026-11-27 de 21:07:07Z a 21:11:38Z contra `http://localhost:8000` con los parámetros por defecto. Resultado: 14,076 peticiones, 0 fallos, promedio 22.6 ms, máximo 195 ms y p95 agregado de 84 ms. Las siete fases y sus timestamps están en `loadtest/results/fases.log`; los CSV versionados en `loadtest/results/locust-20261127-130704_{stats,stats_history,failures,exceptions}.csv`. El HTML se generó localmente pero no se versiona.

No hubo correlación con AWS porque el controller de Emilio aún no existe. Detalle: `docs/evidencia/2026-11-27-1314-stack-monitoreo-carga-chaos.md`.
