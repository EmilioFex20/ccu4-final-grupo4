# CCU4-FinalProject-4

**Documento editable · BORRADOR PARA REVISIÓN DEL EQUIPO**

Proyecto: CCU4-FINAL · PaaS híbrido autoescalable · Grupo 4
Autor de este documento: Johana, Site Reliability Engineer y Documentación
Fecha: 2026-11-27
Entrega prevista: `CCU4-FinalProject-4.pdf` (miércoles 2 de diciembre, 11 PM)

**Estado del borrador:** incluye resultados reales verificables hasta el commit `55044eb` en `main`, con stack local, monitoreo, Locust y chaos ejecutados, y capturas reales de la política IAM y del presupuesto en la cuenta AWS gratuita. No incluye capturas de Floci, adjunción de la política, prueba de denegación, entrega de correo de alerta ni logs de instancias porque no están disponibles. No se inventaron capturas, despliegues ni métricas.

## 1. Introducción

Este reporte documenta el estado del proyecto final de Cloud Computing del CETYS, una mini-PaaS para un sistema de pedidos de cafetería. La plataforma corre en local con Floci y, cuando aumenta el tráfico, debe crecer hacia AWS bajo control de políticas de costo y seguridad, para luego liberar recursos automáticamente.

## 2. Objetivo del proyecto

Construir una plataforma híbrida autoescalable con una API stateless, frontend, Postgres, Redis, pipeline de CI/CD, despliegue en Floci, auto-scaler en AWS, monitoreo, pruebas de carga y resiliencia verificable. La aplicación de ejemplo permite ver el menú, crear pedidos y consultarlos.

## 3. Arquitectura actual

El stack local (`docker-compose.yml`) está formado por `web` (Nginx en `localhost:3000`), `api` (FastAPI en `localhost:8000`), `postgres` con volumen `pgdata` y `redis`. La API usa Postgres para pedidos y Redis como caché del menú.

El pipeline de GitHub Actions construye y publica imágenes en GHCR; Floci registra tareas ECS locales a partir de `infra/floci/*-task.json`. El monitoreo se levanta con un Compose complementario en `infra/monitoring/`: Prometheus, dos exportadores propios y Grafana.

Diagrama Mermaid completo: `docs/arquitectura.md`. Su contenido no se reproduce aquí para evitar duplicación.

```mermaid
flowchart LR
  Cliente --> API
  API --> Postgres
  API --> Redis
  GHCR --> Floci
  Exporters --> Prometheus --> Grafana
```

## 4. Tecnologías utilizadas

Python 3.13, FastAPI, Uvicorn, psycopg 3, Redis-py, PostgreSQL 16, Redis 7, Nginx, Docker y Docker Compose, Floci, GitHub Actions, GHCR, AWS IAM y AWS Budgets, Prometheus y Grafana, Locust, boto3 (responsabilidad de Emilio) y reportlab para generar este PDF.

## 5. Responsabilidades del equipo

| Integrante | Responsabilidades oficiales | Estado en el repositorio al 2026-11-27 |
|---|---|---|
| Emilio | Floci, scripts AWS con boto3 y auto-scaler | Tareas de Floci presentes; controller y scripts AWS pendientes; la política y el budget ya existen en AWS |
| Jesús | GitHub Actions, GHCR, rolling update y reverse proxy | Pipeline en verde e imágenes publicadas; proxy pendiente |
| Carlos | Frontend, API, Postgres, Redis, Dockerfiles y Lambda | API, web y compose presentes; Lambda pendiente |
| Johana | Monitoreo, Locust, chaos, IAM, Budget, reportes y PDF | IAM y Budget creados en AWS con capturas redactadas; Prometheus/Grafana/Locust/chaos verificados en local; documentación actualizada |

## 6. Hitos y resultados verificables

### Milestone 1

- Pipeline `CI` con cuatro checks en verde: run `45953227796`, 2026-11-27T06:39:14Z a 06:40:34Z.
- Imágenes `api` y `web` publicadas en GHCR con tags `latest` y `sha-55044eb`, según logs del pipeline.
- Política IAM `CCU4-RestrictEC2MicroInstances` y presupuesto `CCU4-Budget-1USD` creados en AWS; capturas 14:40 y 14:47, redactadas y documentadas.
- Reporte del Milestone 1 y diagrama de arquitectura en `docs/`.
- Detalle: `docs/reporte-milestone-1.md`.

### Milestone 2

- Scripts boto3 y Lambda: pendientes de Emilio y Carlos.
- IAM y Budget ya existen en AWS; falta adjuntar la política a un principal. El controller debe enviar `InstanceType` explícito (`t2.micro` o `t3.micro`).

### Milestone 3

- Prometheus con 3 jobs estáticos, 2 jobs `file_sd_configs`, 8 reglas de alerta y retención de 15 días.
- Grafana con datasource y dashboard aprovisionados, 12 paneles y 3 variables.
- `promtool check config`: SUCCESS. `promtool check rules`: SUCCESS, 8 reglas.
- Controller y proxy: pendientes; sus archivos `targets.d/` están vacíos a propósito.

### Milestone 4

- Locust con siete fases: normal, incremento gradual, pico, sostenida, disminución, recuperación y fin.
- Ejecución real: 14,076 peticiones, 0 fallos, promedio 22.6 ms, p95 agregado de 84 ms y 52 req/s, de 21:07:07Z a 21:11:38Z.
- Chaos controlado con ocho criterios verificables, recuperación automática y sin borrado de volúmenes.
- Ejecución real: ocho escenarios en `ok`, `reverse_proxy` en `pendiente`, pedido 4231 íntegro y código de salida 0.

## 7. Seguridad IAM y AWS Budget

La política real creada en la consola es `CCU4-RestrictEC2MicroInstances`, no el nombre por defecto del script reproducible. La regla visible es `Deny` de `ec2:RunInstances` cuando `ec2:InstanceType` no es `t2.micro` ni `t3.micro`; el recurso es `arn:aws:ec2:*:*:instance/*`. Como una sentencia `Deny` explícita prevalece sobre cualquier `Allow`, un principal que use esta política no podrá lanzar instancias de otros tipos ni omitir el tipo. La política no concede `RunInstances` por sí sola y **no está adjuntada** a ningún principal; tampoco se ejecutó una prueba de denegación en vivo.

### Evidencia 7.1 · Política IAM creada en AWS

![Política IAM CCU4-RestrictEC2MicroInstances](evidencia/AWS_IAM_Policy.png)

La captura de las 14:40 muestra el mensaje de creación y el JSON de la política. Se ocultaron el identificador/alias de cuenta y el nombre del usuario; la regla de tipos permaneció visible.

### Evidencia 7.2 · Presupuesto mensual creado en AWS

![Presupuesto CCU4-Budget-1USD](evidencia/AWS_Budget_Alarm.png)

La captura de las 14:47 muestra `CCU4-Budget-1USD`, 1.00 USD mensuales, periodo `Mensual`, inicio `2026-11-01`, estado `En buen estado`, gasto visible de 0,00 US$ y la regla `Costo real > 100%`. El destinatario del correo se ocultó en la copia pública y aparece con verificación pendiente: hay configuración de notificación, pero **no hay evidencia de entrega**. AWS Budget solo avisa; la terminación de instancias depende del controller de Emilio.

La plantilla `infra/aws/budget.json` conserva las alertas `ACTUAL` al 50/80/100 % y `FORECASTED` al 100 % como contrato reproducible; la captura confirma únicamente la regla visible indicada. No se crearon instancias, no se ampliaron permisos y no se modificó el trabajo de otros integrantes. Detalle completo y limitaciones: `docs/evidencia/2026-11-27-1440-aws-iam-budget.md`.

## 8. Monitoreo

Se instrumentó sin modificar la API de Carlos: `app-exporter` sondea `/health` y `/menu` y expone disponibilidad, latencia, RPS de sondas y errores HTTP; `docker-exporter` consulta Docker Engine para CPU, memoria y estado de contenedores. Prometheus persiste 15 días en un volumen; las alertas están visibles en `/alerts` y aún no tienen Alertmanager.

Para medir RPS, latencia y errores del tráfico real de clientes se necesita autorización para agregar `/metrics` a la API. Hasta entonces, los paneles están nombrados como sondas.

## 9. Grafana

Datasource `Prometheus` con UID `prometheus-ccu4`, impulsado por archivos versionados y carpeta `CCU4`. El dashboard `ccu4-overview.json` incluye disponibilidad, tráfico de sondas, latencia promedio y p95, errores, CPU, memoria, contenedores activos, targets y un panel de texto con los contratos pendientes. Incluye filtros por endpoint, contenedor y job, y rango temporal de una hora por defecto.

## 10. Pruebas de carga

Locust usa el contrato real de `docs/api.md`: `GET /menu`, `POST /orders`, `GET /orders/{id}` y `GET /health`. El destino por defecto es local y se bloquea cualquier otro salvo autorización explícita. La ejecución real generó 14,076 peticiones sin fallos; el desglose fue 5,772 `GET /menu`, 4,224 `POST /orders`, 2,716 `GET /orders/{id}` y 1,361 `GET /health` en el snapshot final del CSV. El registro de fases con timestamps permitirá correlacionar el escalamiento con los logs de AWS cuando el controller exista, sin superar los 5 a 10 minutos de vida de instancias que indica el README.

## 11. Chaos engineering

El script `chaos/run_chaos.ps1` detiene y reinicia `api`, detiene temporalmente `web`, verifica la persistencia de un pedido real y deja el stack recuperado. No elimina volúmenes ni recursos ajenos. Incluye un modo con PID de Locust para observar recuperación bajo carga. En la ejecución real el pedido 4231 permaneció íntegro y solo quedó pendiente el escenario del reverse proxy, porque Jesús aún no lo despliega. La pérdida de un nodo AWS no se simula sin autorización.

## 12. Matriz de pruebas y resultados reales

| Prueba | Resultado |
|---|---|
| Validación IAM/Budget (`verify.py`) | Ejecutada: OK |
| Simulación `setup_iam.py` y `setup_budget.py` | Ejecutada: sin llamadas a AWS |
| Creación real de IAM y Budget en AWS | Ejecutada por el usuario: capturas 14:40 y 14:47, sin adjunción ni prueba de denegación |
| Revisión y redacción de capturas AWS | Ejecutada: OCR sin ID/alias de cuenta, nombres ni correo en copias públicas |
| Validación JSON/YAML | Ejecutada: 10 archivos válidos |
| Validación Compose principal y de monitoreo | Ejecutada: código 0 |
| `promtool check config` y `check rules` | Ejecutada: SUCCESS, 8 reglas |
| Compilación Python | Ejecutada: código 0 |
| Pipeline y GHCR | Verificado por API y logs de GitHub Actions |
| Stack local, Prometheus en vivo y Grafana | Ejecutada: 3 targets `up`, 9 contenedores y dashboard con datos |
| Locust real | Ejecutada: 14,076 peticiones, 0 fallos, p95 84 ms |
| Chaos real | Ejecutada: 8 escenarios `ok`, proxy `pendiente` |
| Correlación Locust ↔ AWS y logs de instancias | Pendientes: requieren controller de Emilio; IAM y Budget ya están creados |

Matriz completa: `docs/matriz-pruebas.md`.

## 13. Incidencias y post-mortem

Incidencias principales: daemon de Docker apagado al inicio (resuelto), falta de scope `read:packages` para listar GHCR, ausencia de controller y proxy, falta de `/metrics` en la API y ausencia de dashboard de Floci en este equipo. Durante la integración se corrigieron tres defectos propios: el exporter de Docker no soportaba socket Unix en Python 3.13, el script de chaos comprobaba la raíz de la API en lugar de `/health`, y PowerShell 5.1 necesitaba BOM para codificar el informe. `promtool` no estaba instalado y se resolvió descargando el release oficial a un directorio temporal; las rutas del config se ajustaron para que la validación local no emitiera advertencias.

El 2026-11-27 se detectó además el incidente GitGuardian `41459752`: una contraseña genérica asociada al administrador de Grafana quedó referenciada en el Compose del commit `cd6ffea`. La causa raíz fue un valor de ejemplo en `.env.example` junto con una referencia explícita a la variable en `environment`. La credencial se rotó en la base persistente de Grafana sin borrar volúmenes: la anterior devuelve `401` y la nueva `200`; el datasource y el dashboard permanecen intactos. El Compose ahora carga la credencial desde `.env` ignorado y `.env.example` no contiene valores sensibles. La alerta sigue pendiente de cierre porque el valor original permanece en el historial; se eligió gestionarla en el dashboard sin reescribir la rama. Los cuatro jobs de GitHub Actions del PR #3 pasaron en el run `46075104127`, pero el check de GitGuardian sigue en `FAILURE` por la ocurrencia antigua. Detalle: `docs/incidente-gitguardian-41459752.md`.

Detalle: `docs/incidencias.md`, `docs/post-mortem.md` e `incidente-gitguardian-41459752.md`.

## 14. Evidencias disponibles y pendientes

Disponibles: pipeline CI, push a GHCR por logs, herramientas y validación local IAM/Budget, capturas reales de la política IAM y del budget con datos sensibles ocultos, validación de Prometheus con `promtool`, evidencia de stack real, targets y dashboard, CSV de Locust y JSON de chaos.

Pendientes: captura visual de Floci, captura de GHCR Packages, adjunción y prueba de la política IAM, entrega del correo de alerta, correlación Locust ↔ AWS, logs de instancias del controller y validación del reverse proxy de Jesús.

Índice: `docs/evidencia/README.md`. Toda evidencia incluye fecha y hora.

## 15. Conclusiones y trabajo pendiente

La parte de Johana quedó implementada como código reproducible e integrada sin sobrescribir el trabajo de sus compañeros: stack local, Prometheus, Grafana, Locust y chaos funcionaron con datos reales, y la política IAM y el presupuesto quedaron creados en AWS con capturas verificadas y redactadas. Para completar el PDF definitivo se necesita: capturas de Floci y GHCR, adjunción/prueba de la política, confirmación de entrega del correo de alerta, el reverse proxy de Jesús y los logs de creación y terminación de instancias del controller de Emilio. Hasta entonces este documento es un borrador honesto, sin datos ficticios.

## 16. Comandos de referencia

```bash
python infra/aws/verify.py
docker compose up -d --build
docker compose -f infra/monitoring/docker-compose.monitoring.yml --env-file infra/monitoring/.env.example config --quiet
promtool check config infra/monitoring/prometheus/prometheus.yml
promtool check rules infra/monitoring/prometheus/rules/cafeteria-alerts.yml
powershell -ExecutionPolicy Bypass -File ./loadtest/run_loadtest.ps1
powershell -ExecutionPolicy Bypass -File ./chaos/run_chaos.ps1
```
