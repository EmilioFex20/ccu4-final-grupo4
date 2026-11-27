# Índice de evidencias

Toda evidencia debe incluir fecha y hora. Los archivos de este directorio son registros reales obtenidos con comandos de solo lectura o ejecuciones locales; no se incluyen capturas inventadas.

| Fecha y hora (local -08:00) | Archivo | Qué demuestra | Estado |
|---|---|---|---|
| 2026-11-27 12:43 | `2026-11-27-1243-pipeline-ci.md` | Pipeline en verde, run 45953227796, cuatro checks exitosos | Obtenida |
| 2026-11-27 12:43 | `2026-11-27-1243-ghcr.md` | Push de imágenes `api` y `web` a GHCR según logs del pipeline | Obtenida (falta captura visual de Packages) |
| 2026-11-27 12:44 | `2026-11-27-1244-herramientas.md` | Herramientas disponibles y validación local de IAM/Budget | Obtenida |
| 2026-11-27 13:14 | `2026-11-27-1314-stack-monitoreo-carga-chaos.md` | Stack real, Prometheus/Grafana, Locust y chaos ejecutados | Obtenida |
| 2026-11-27 22:00 | `2026-11-27-2200-gitguardian.md` | Rotación y verificación de la credencial de Grafana tras GitGuardian 41459752 | Obtenida; historial pendiente |

## Evidencias pendientes

| Evidencia | Responsable | Motivo |
|---|---|---|
| Captura del dashboard de Floci con el stack desplegado | Emilio | Floci no está corriendo en el equipo de Johana |
| Captura visual de GHCR Packages | Jesús o Emilio | El token de Johana no tiene scope `read:packages`; los logs sí prueban el push |
| Logs de creación y terminación de instancias AWS con sello de tiempo | Emilio | Requiere el controller y autorización explícita para crear recursos reales |
| Correlación Locust ↔ AWS | Johana + Emilio | Locust ya se ejecutó; falta el controller de Emilio |
| Validación del reverse proxy en chaos | Jesús | No existe proxy desplegado; el escenario se registró como `pendiente` |
| Retirar la credencial del historial de `feature/johana-sre` | Johana + equipo | Requiere autorización para reescribir la rama y hacer `force push` |

Los resultados generados por Locust se guardan en `loadtest/results/` y los de chaos en `chaos/results/`; ambos directorios están ignorados por Git por defecto. Para esta entrega se versionan de forma selectiva `loadtest/results/fases.log`, los cuatro CSV de `locust-20261127-130704` y `chaos/results/chaos-20261127-131336.json`; se excluye el HTML derivable. El resumen con fecha, hora y comandos exactos es `2026-11-27-1314-stack-monitoreo-carga-chaos.md`.
