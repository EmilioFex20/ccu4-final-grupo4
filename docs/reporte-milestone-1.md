# Reporte del Milestone 1 · Base y pipeline

- Autor: Johana, Site Reliability Engineer y Documentación
- Fecha: 2026-11-27
- Estado: actualizado con evidencias reales de API/logs, ejecución local y capturas de IAM/Budget en AWS; pendientes las capturas visuales de Floci y GHCR, la adjunción de la política y la verificación de entrega del correo

## 1. Introducción

El Milestone 1 establece la base del proyecto CCU4-FINAL: una mini-PaaS para un sistema de pedidos de cafetería que corre en local con Floci y puede crecer hacia AWS. El alcance de este reporte cubre lo que existe en el repositorio hasta el commit `55044eb` en `main` y las responsabilidades asignadas a Johana en el README.

## 2. Objetivo del proyecto

Construir una plataforma híbrida autoescalable donde la aplicación de cafetería atienda tráfico normal en contenedores locales y, ante aumentos de carga, el controller cree instancias EC2 controladas por políticas estrictas de tipo y presupuesto. La aplicación debe ser stateless y conservar pedidos en Postgres y Redis.

## 3. Arquitectura actual

- `web`: frontend estático servido por Nginx no privilegiado en el puerto 8080 del contenedor, publicado en `localhost:3000`.
- `api`: FastAPI, consume Postgres y Redis, expone `/health`, `/menu`, `POST /orders` y `/orders/{id}`.
- `postgres`: `postgres:16-alpine` con volumen `pgdata`; inicializa menú y tablas de pedidos desde `api/app/db.py`.
- `redis`: `redis:7-alpine`, caché del menú con TTL de 60 segundos.
- `infra/floci`: definiciones de tareas ECS para `postgres`, `redis`, `api`, `web`, una tarea de ejemplo `nginx` y un `compose.yaml` de Floci.
- `.github/workflows/ci.yml`: validación de la API, smoke test del stack y publicación de imágenes en GHCR.
- Aún no existen en el repositorio: `infra/controller`, `infra/proxy`, `infra/lambda`, ni los scripts boto3 de Emilio.

El borrador del diagrama está en [`arquitectura.md`](arquitectura.md).

## 4. Tecnologías utilizadas

Python 3.13, FastAPI, Uvicorn, psycopg 3, Redis-py, PostgreSQL 16, Redis 7, Nginx, Docker y Docker Compose, Floci (ECS local), GitHub Actions, GHCR, AWS IAM y AWS Budgets (recursos creados y capturados en la cuenta gratuita), Prometheus y Grafana (fase 3 en adelante), Locust (fase 5).

## 5. Responsabilidades de los integrantes

| Integrante | Responsabilidades principales | Estado observado en el repositorio |
|---|---|---|
| Emilio | Floci, scripts AWS con boto3 y auto-scaler | Archivos de Floci presentes; controller y scripts AWS aún no aparecen |
| Jesús | CI/CD, GHCR, rolling update y reverse proxy | `ci.yml` presente y en verde; proxy aún no aparece |
| Carlos | API, frontend, Postgres, Redis, Dockerfiles y Lambda | API, web y compose presentes; Lambda aún no aparece |
| Johana | Prometheus, Grafana, Locust, chaos, IAM, Budget, reportes y PDF | IAM/Budget implementados y validados; monitoreo, carga y chaos ejecutados en local |

## 6. Descripción del pipeline

`ci.yml` se dispara en `push` y `pull_request` contra `main`:

1. `validate-api`: instala dependencias desde `api/requirements.txt`, ejecuta `ruff check . --select E9,F63,F7,F82` y `pytest` si existe carpeta `tests/`.
2. `smoke-test`: copia `.env.example` a `.env`, levanta `docker compose up -d --build`, espera `GET /health`, verifica el frontend y baja el stack con `down -v`.
3. `build-and-push`: construye `api` y `web` en matriz, y solo en push a `main` inicia sesión en GHCR y publica tags `latest` y `sha-<commit>`.

Última ejecución verificada: run `45953227796`, `completed/success`, 2026-11-27T06:39:14Z–06:40:34Z. Los cuatro checks terminaron en `success`.

## 7. Integración con GHCR

Las imágenes se publican como:

- `ghcr.io/emiliofex20/ccu4-final-grupo4/api:latest` y `:sha-55044eb`
- `ghcr.io/emiliofex20/ccu4-final-grupo4/web:latest` y `:sha-55044eb`

Los manifiestos REALES publicados aparecen en los logs del run (digests `sha256:3c4b896e...` para api y `sha256:d80937cb...` para web). La API REST no permitió listar paquetes con el token de Johana (403 por scope `read:packages`), por lo que queda pendiente la captura visual de la pestaña Packages.

## 8. Despliegue en Floci

Existen `infra/floci/compose.yaml`, `deploy.bat` y los archivos `*-task.json` para `postgres`, `redis`, `api`, `web` y una tarea de prueba de Nginx. `api-task.json` apunta a la imagen `api:latest` de GHCR y usa `host.docker.internal` para Postgres y Redis.

Johana **no ejecutó ni verificó** el despliegue en Floci: la evidencia del dashboard queda pendiente y debe aportarla Emilio. El stack local sí se levantó y verificó el 2026-11-27, con Prometheus, Grafana, Locust y chaos funcionando.

## 9. Configuración de seguridad IAM

La política `infra/aws/iam-policy-micro-only.json` declara cuatro `Deny`:

1. `ec2:RunInstances` con tipo distinto de `t2.micro`/`t3.micro`.
2. `ec2:RunInstances` sin `ec2:InstanceType` explícito.
3. `ec2:ModifyInstanceAttribute` hacia tipos no autorizados.
4. Acciones EC2 fuera de `us-east-1`.

Los `Allow` se limitan a la lectura necesaria para el controller más `RunInstances`, `CreateTags` y `TerminateInstances`. No se asume que las instancias micro sean gratuitas. La política sí se creó en la cuenta gratuita como `CCU4-RestrictEC2MicroInstances` (captura 14:40), pero **no se adjuntó a ningún principal** y no se probó una denegación en vivo. Detalle: `evidencia/2026-11-27-1440-aws-iam-budget.md`.

## 10. Configuración del presupuesto

`infra/aws/budget.json` define 1.00 USD mensual con notificaciones `ACTUAL` al 50/80/100 % y `FORECASTED` al 100 %, dirigidas al correo configurado en `AWS_BUDGET_EMAIL`. En AWS se creó `CCU4-Budget-1USD` (captura 14:47): 1.00 USD, periodo mensual, inicio `2026-11-01` y regla visible `Costo real > 100%`. El destinatario aparece en la consola, pero se ocultó en la copia pública y su verificación está pendiente; no hay evidencia de entrega. El presupuesto avisa, **no detiene costos**; la terminación de instancias depende del controller.

## 11. Resultados verificables

- `python infra/aws/verify.py` → `RESULTADO: OK` (2026-11-27 12:44 -08:00).
- `python infra/aws/setup_iam.py` y `setup_budget.py` → modo simulación, sin llamadas a AWS.
- Capturas reales de AWS: política creada 14:40 y presupuesto creado 14:47; revisadas y redactadas sin datos sensibles.
- Pipeline: run `45953227796`, 4/4 checks en success; el PR #3 también tiene la ejecución `46075104127` en success tras el fix de CI.
- GHCR: dos manifiestos publicados según logs del pipeline.
- `docker compose -f docker-compose.yml config --quiet` → código 0.

## 12. Problemas encontrados

1. Docker Desktop estuvo apagado al inicio: se inició y permitió levantar el stack, scrapear Prometheus y ejecutar Locust y chaos; detalle en `docs/evidencia/2026-11-27-1314-stack-monitoreo-carga-chaos.md`.
2. Token de GitHub sin scope `read:packages`: no se pueden listar paquetes GHCR por API.
3. No hay dashboard de Floci accesible desde este equipo; no se inventó evidencia.
4. `docs/api.md` marca como pendiente confirmar si la API expondrá `/metrics`: la API actual solo expone los cuatro endpoints funcionales.
5. Todavía no existen `infra/controller` ni `infra/proxy`, de modo que las métricas de escalamiento y ruteo no pueden instrumentarse todavía.

## 13. Conclusiones

La base del proyecto existe y el pipeline está funcionando. Las responsabilidades de Johana de seguridad y control de gasto están creadas en AWS y documentadas con capturas reales, además de permanecer como código reproducible. Monitoreo, carga y resiliencia ya tienen evidencia real del stack local. Quedan pendientes la adjunción y prueba de la política, la verificación de entrega del correo, las capturas visuales que requieren entornos de otros integrantes y la correlación con el controller de Emilio.

## 14. Evidencias disponibles y pendientes

Ver [`docs/evidencia/README.md`](evidencia/README.md). Disponibles: pipeline, GHCR por logs, herramientas/validación local, stack real, Grafana con datos, Locust, chaos y capturas de IAM/Budget en AWS. Pendientes: Floci, Packages visual, adjunción/prueba de la política, entrega del correo de alerta y correlación Locust ↔ AWS.
