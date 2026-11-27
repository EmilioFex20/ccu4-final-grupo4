# Matriz de pruebas

Leyenda: **Ejecutada** significa que se corrió el comando en esta sesión y se registró su resultado real. **Pendiente** significa que el entorno o un componente de otro integrante no estaba disponible.

| ID | Prueba | Comando | Resultado | Evidencia |
|---|---|---|---|---|
| T01 | Validación JSON/YAML de IAM, Budget, Prometheus y Grafana | `python -c "import json,pathlib,yaml; ..."` | Ejecutada: 10 archivos válidos | `docs/evidencia/2026-11-27-1244-herramientas.md` y QA |
| T02 | Validación IAM/Budget offline | `python infra/aws/verify.py` | Ejecutada: `RESULTADO: OK` | `docs/evidencia/2026-11-27-1244-herramientas.md` |
| T03 | Simulación de creación IAM | `python infra/aws/setup_iam.py` | Ejecutada: modo simulación, sin AWS | índice de evidencias |
| T04 | Simulación de creación Budget | `python infra/aws/setup_budget.py` | Ejecutada: modo simulación, sin AWS | índice de evidencias |
| T05 | Validación remota IAM/Budget | `python infra/aws/verify.py --live` | Pendiente: requiere autorización y credenciales | — |
| T06 | Validación Compose principal | `docker compose -f docker-compose.yml config --quiet` | Ejecutada: código 0 | evidencia de herramientas |
| T07 | Validación Compose de monitoreo | `docker compose -f infra/monitoring/docker-compose.monitoring.yml --env-file infra/monitoring/.env.example config --quiet` | Ejecutada: código 0 | QA |
| T08 | Validación Prometheus config | `promtool check config infra/monitoring/prometheus/prometheus.yml` | Ejecutada: SUCCESS, 1 rule file | QA |
| T09 | Validación de reglas | `promtool check rules infra/monitoring/prometheus/rules/cafeteria-alerts.yml` | Ejecutada: SUCCESS, 8 reglas | QA |
| T10 | Compilación Python de exportadores | `python -m py_compile infra/monitoring/exporters/*.py` | Ejecutada: código 0 | QA |
| T11 | Compilación Python de Locust | `python -m py_compile loadtest/locustfile.py` | Ejecutada en QA | QA |
| T12 | Arranque de exporters y exposición de métricas | `docker compose -f infra/monitoring/docker-compose.monitoring.yml up -d --build` | Ejecutada: 2 series de sondas y 9 contenedores; errores del exporter en 0 | evidencia 13:14 |
| T13 | Levantar stack con Docker | `docker compose up -d --build` | Ejecutada: `api`, `web`, `postgres` y `redis` activos; `/health` ok | evidencia 13:14 |
| T14 | Scrape real de Prometheus y visualización en Grafana | `docker compose -f infra/monitoring/docker-compose.monitoring.yml up -d` | Ejecutada: 3 targets `up`, 8 reglas cargadas, 1 datasource y 1 dashboard | evidencia 13:14 |
| T15 | Prueba de carga real | `powershell -ExecutionPolicy Bypass -File ./loadtest/run_loadtest.ps1` | Ejecutada: 14,076 peticiones, 0 fallos, p95 84 ms, código 0 | evidencia 13:14 |
| T16 | Chaos engineering real | `powershell -ExecutionPolicy Bypass -File ./chaos/run_chaos.ps1` | Ejecutada: 8 escenarios `ok`, proxy `pendiente`, código 0 | evidencia 13:14 |
| T17 | Correlación Locust ↔ AWS | `fases.log` + logs boto3 | Pendiente: requiere controller de Emilio | — |
| T18 | Verificación de credenciales expuestas | escaneo de `git diff` y archivos | Ejecutada en QA | QA |
| T19 | Creación real de la política IAM | Consola AWS, captura `AWS_IAM_Policy.png` | Ejecutada por el usuario: `CCU4-RestrictEC2MicroInstances` creada; sin adjunción ni prueba de denegación | `docs/evidencia/2026-11-27-1440-aws-iam-budget.md` |
| T20 | Creación real del presupuesto | Consola AWS, captura `AWS_Budget_Alarm.png` | Ejecutada por el usuario: `CCU4-Budget-1USD`, 1.00 USD mensuales y regla `Costo real > 100%`; entrega de correo pendiente | `docs/evidencia/2026-11-27-1440-aws-iam-budget.md` |
| T21 | Revisión y redacción de capturas AWS | OCR local sobre copias públicas | Ejecutada: ID/alias de cuenta, nombres y correo ya no aparecen | `docs/evidencia/2026-11-27-1440-aws-iam-budget.md` |

Los resultados T08/T09 se obtuvieron con `promtool` oficial v2.55.0 descargado en un directorio temporal fuera del repositorio. Los resultados T12–T16 están detallados en `docs/evidencia/2026-11-27-1314-stack-monitoreo-carga-chaos.md`.
