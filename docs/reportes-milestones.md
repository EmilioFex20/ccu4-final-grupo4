# Reportes de milestones posteriores

Estado: borradores al 2026-11-27. Solo se afirma lo ejecutado; las entregas de otros integrantes se marcan como pendientes cuando no están en el repositorio o no pudieron verificarse.

## Milestone 2 · Scripts de AWS y Lambda

| Responsable | Entrega esperada | Estado observable |
|---|---|---|
| Emilio | Scripts boto3 para crear, configurar y terminar instancias | Pendiente: `infra/aws/` solo contiene los archivos de Johana |
| Carlos | Lambda que genera recibos en S3 | Pendiente: `infra/lambda/` no existe |
| Johana | Política IAM y Budget que limiten el costo de esos scripts | Implementados como código y validados localmente; sin `--apply` |

Dependencia: el controller debe crear instancias con `InstanceType` explícito para que la política IAM no bloquee la prueba.

## Milestone 3 · Controller, monitoreo y proxy

| Responsable | Entrega esperada | Estado observable |
|---|---|---|
| Emilio | Auto-scaler con umbrales, cooldown y drenado | Pendiente: `infra/controller/` no existe |
| Jesús | Reverse proxy con ruteo dinámico | Pendiente: `infra/proxy/` no existe |
| Johana | Prometheus y Grafana integrados | Implementados en `infra/monitoring/`: exporters propios, 8 alertas, datasource y dashboard aprovisionados; `promtool check config` y `check rules` ejecutados con éxito |

Dependencia: cuando controller y proxy expongan `/metrics`, se agregan sus targets en `prometheus/targets.d/`. No se activaron paneles con métricas inexistentes.

## Milestone 4 · Prueba de carga final y capturas

| Responsable | Entrega esperada | Estado observable |
|---|---|---|
| Johana | Locust, chaos, capturas y PDF | Locust y chaos ejecutados en local: 14,076 peticiones, 0 fallos y 8 escenarios `ok`; borrador del PDF generado; capturas externas pendientes |
| Emilio | Logs de creación y terminación de instancias de 5 a 10 minutos | Pendiente |
| Jesús y Emilio | Capturas de Floci y GHCR | GHCR por logs obtenido; captura visual pendiente |
| Carlos | API estable durante la carga | Pipeline en verde; carga real ejecutada sin fallos |

La correlación de evidencias se hará con `loadtest/results/fases.log` (timestamps de fases) y los logs boto3 del controller. Sin esos registros no se afirmará que hubo escalamiento.
