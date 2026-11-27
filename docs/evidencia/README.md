# Índice de evidencias

Toda evidencia debe incluir fecha y hora. Los archivos de este directorio son registros reales obtenidos con comandos de solo lectura o ejecuciones locales; no se incluyen capturas inventadas.

| Fecha y hora (local -08:00) | Archivo | Qué demuestra | Estado |
|---|---|---|---|
| 2026-11-27 12:43 | `2026-11-27-1243-pipeline-ci.md` | Pipeline en verde, run 45953227796, cuatro checks exitosos | Obtenida |
| 2026-11-27 12:43 | `2026-11-27-1243-ghcr.md` | Push de imágenes `api` y `web` a GHCR según logs del pipeline | Obtenida (falta captura visual de Packages) |
| 2026-11-27 12:44 | `2026-11-27-1244-herramientas.md` | Herramientas disponibles y validación local de IAM/Budget | Obtenida |
| 2026-11-27 13:14 | `2026-11-27-1314-stack-monitoreo-carga-chaos.md` | Stack real, Prometheus/Grafana, Locust y chaos ejecutados | Obtenida |
| 2026-11-27 22:00 | `2026-11-27-2200-gitguardian.md` | Rotación y verificación de la credencial de Grafana tras GitGuardian 41459752 | Obtenida; historial pendiente |
| 2026-11-27 14:40 | `AWS_IAM_Policy.png` | Política IAM real `CCU4-RestrictEC2MicroInstances` creada; denegación de tipos distintos de `t2.micro`/`t3.micro` | Obtenida; copia pública redactada |
| 2026-11-27 14:47 | `AWS_Budget_Alarm.png` | Presupuesto real `CCU4-Budget-1USD`: 1.00 USD mensual, umbral y notificación configurada | Obtenida; correo redactado y verificación pendiente |
| 2026-11-27 14:40–14:47 | `2026-11-27-1440-aws-iam-budget.md` | Descripción técnica de ambos recursos, distinción entre creación/configuración/prueba y limitaciones | Obtenida |

## Evidencias pendientes

| Evidencia | Responsable | Motivo |
|---|---|---|
| Captura del dashboard de Floci con el stack desplegado | Emilio | Floci no está corriendo en el equipo de Johana |
| Captura visual de GHCR Packages | Jesús o Emilio | El token de Johana no tiene scope `read:packages`; los logs sí prueban el push |
| Logs de creación y terminación de instancias AWS con sello de tiempo | Emilio | La política y el budget ya existen; falta el controller y autorización explícita para crear instancias |
| Correlación Locust ↔ AWS | Johana + Emilio | Locust ya se ejecutó; falta el controller de Emilio |
| Adjuntar la política IAM y probar denegación de `t3.small` | Johana + Emilio | La captura prueba la creación, no la adjunción ni una prueba de autorización |
| Confirmar entrega del correo de alerta del budget | Johana | La regla está configurada, pero el destinatario aparece con verificación pendiente |
| Validación del reverse proxy en chaos | Jesús | No existe proxy desplegado; el escenario se registró como `pendiente` |
| Resolver GitGuardian 41459752 en el dashboard | Johana + equipo | La credencial fue rotada; el check sigue rojo por la ocurrencia antigua en `cd6ffea` |

Los resultados generados por Locust se guardan en `loadtest/results/` y los de chaos en `chaos/results/`; ambos directorios están ignorados por Git por defecto. Para esta entrega se versionan de forma selectiva `loadtest/results/fases.log`, los cuatro CSV de `locust-20261127-130704` y `chaos/results/chaos-20261127-131336.json`; se excluye el HTML derivable. El resumen con fecha, hora y comandos exactos es `2026-11-27-1314-stack-monitoreo-carga-chaos.md`.
