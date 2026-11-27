# CCU4-FINAL · PaaS híbrido autoescalable · Grupo 4

Proyecto final de Cloud Computing (CETYS). Construimos una mini-PaaS que corre en local con **Floci** y, cuando sube el tráfico, crece sola hacia **AWS**. Cuando el tráfico baja, termina esos recursos de forma automática.

La aplicación de ejemplo es un **sistema de pedidos para una cafetería**: los clientes ven el menú y hacen pedidos, y cada pedido genera un recibo en segundo plano.

---

## Equipo y roles

| Integrante | Rol                                                                | Responsabilidades en todo el proyecto                                                                                                                                             |
| ---------- | ------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Emilio** | Team Leader · Controller Developer · Infrastructure Engineer (AWS) | Despliegue en Floci, scripts de AWS con boto3 (crear, configurar y terminar instancias sin usar la consola) y el auto-scaler ("The Brain": umbrales, cooldown y drenado de nodos) |
| **Jesús**  | DevOps & Automation Engineer · Infrastructure Engineer (ruteo)     | Pipeline de CI/CD con GitHub Actions, validación automática, registry (GHCR), rolling update en Floci y reverse proxy con ruteo dinámico                                          |
| **Carlos** | Application & Serverless Architect                                 | Microservicios (frontend y API stateless), Postgres y Redis, Dockerfiles, docker-compose y la función Lambda                                                                      |
| **Johana** | Site Reliability Engineer · Documentación                          | Monitoreo (Prometheus y Grafana), prueba de carga con Locust, chaos engineering, IAM policy, Budget Alarm, reportes de milestones y PDF final                                     |

---

## Estructura del proyecto

```
ccu4-final-grupo4/
├── .github/
│   └── workflows/      # Pipelines de GitHub Actions (ci.yml)          → Jesús
├── api/                # API stateless: código, tests y Dockerfile     → Carlos
├── web/                # Frontend: código y Dockerfile                 → Carlos
├── infra/              # Todo lo de infraestructura:
│   ├── floci/          #   despliegue en Floci                         → Emilio
│   ├── aws/            #   scripts de boto3 e IAM policy               → Emilio / Johana
│   ├── controller/     #   auto-scaler ("The Brain")                   → Emilio
│   ├── proxy/          #   configuración del reverse proxy             → Jesús
│   ├── monitoring/     #   Prometheus y Grafana                        → Johana
│   └── lambda/         #   función serverless                          → Carlos
├── loadtest/           # Scripts de Locust                             → Johana
├── docs/
│   ├── api.md          # Contrato de la API (endpoints y JSON)
│   └── evidencia/      # Capturas para el reporte, con fecha y hora
├── docker-compose.yml  # Levanta todo el stack en local                → Carlos
└── README.md
```

Las subcarpetas de `infra/`, `loadtest/` y `docs/evidencia/` se van creando conforme avance el proyecto. No hace falta crearlas todas desde ya.

**Reglas:**

- **La API y el web son stateless.** Nada de guardar sesiones, carritos ni datos en memoria del contenedor. Todo va a Postgres o a Redis. Si un contenedor se reinicia, no se debe perder nada.
- **Nunca subir credenciales.** Las llaves de AWS y los passwords van en un `.env` (que está en el `.gitignore`) o en los Secrets de GitHub.
- **Todo cambio entra por Pull Request a `main`.** Un push a `main` dispara el pipeline.

---

## La aplicación: pedidos de cafetería

| Servicio              | Qué hace                                                                   |
| --------------------- | -------------------------------------------------------------------------- |
| **web**               | Página para ver el menú, hacer un pedido y consultar su estado             |
| **api**               | Recibe los pedidos, los guarda en Postgres y usa Redis como cache del menú |
| **postgres**          | Base de datos con el menú y los pedidos                                    |
| **redis**             | Cache                                                                      |
| **lambda** _(Fase 2)_ | Genera el recibo de cada pedido de forma asíncrona y lo guarda en S3       |

Endpoints principales (el detalle está en [`docs/api.md`](docs/api.md)):

| Método | Ruta           | Descripción                                      |
| ------ | -------------- | ------------------------------------------------ |
| `GET`  | `/menu`        | Lista los productos del menú                     |
| `POST` | `/orders`      | Crea un pedido                                   |
| `GET`  | `/orders/{id}` | Consulta un pedido                               |
| `GET`  | `/health`      | Revisión de salud, para el proxy y el controller |

Variables de entorno que todos deben usar igual:

| Variable       | Ejemplo                                        |
| -------------- | ---------------------------------------------- |
| `DATABASE_URL` | `postgres://user:pass@postgres:5432/cafeteria` |
| `REDIS_URL`    | `redis://redis:6379`                           |
| `API_PORT`     | `8000`                                         |

---

## Milestone 1 (25%): base y pipeline

**Qué piden:**

1. La app escrita, en contenedores y corriendo en Floci (puede desplegarse a mano).
2. Un pipeline que, al hacer commit, construya las imágenes y las suba a un registry.
3. Capturas de los logs del pipeline y del dashboard de Floci.

**Tareas:**

- **Emilio**
  - [x] Crear el repo y la estructura de carpetas
  - [x] Escribir el contrato de la API en `docs/api.md`
  - [x] Probar Floci con una imagen de ejemplo (jueves)
  - [x] Desplegar el stack en Floci con las imágenes de GHCR (viernes)
- **Jesús**
  - [x] Crear `.github/workflows/ci.yml` que, en cada push a `main`, valide el código, construya las imágenes de `api` y `web` y las suba a GHCR
  - [x] Confirmar que las imágenes aparecen en la sección Packages del repo
- **Carlos**
  - [x] API stateless con Postgres y Redis, incluyendo `/health`
  - [x] Frontend sencillo que consuma la API
  - [x] Dockerfiles de `api` y `web`
  - [x] `docker-compose.yml` para levantar todo en local
- **Johana**
  - [ ] IAM policy que solo permita instancias Free Tier (t2.micro y t3.micro)
  - [ ] Budget Alarm de $1.00 en AWS
  - [ ] Capturas del pipeline, de GHCR y del dashboard de Floci en `docs/evidencia/`
  - [ ] Reporte del Milestone 1
  - [ ] Borrador del diagrama de arquitectura

---

## Fechas

| Fecha                | Meta                                                         |
| -------------------- | ------------------------------------------------------------ |
| Jue 26 nov           | Cada quien tiene su parte funcionando                        |
| Vie 27 nov, mediodía | Milestone 1 completo: app en Floci y pipeline en verde       |
| Sáb 28 nov           | Milestone 2: scripts de AWS y Lambda                         |
| Lun 30 nov           | Milestone 3: controller, monitoreo y proxy integrados        |
| Mar 1 dic            | Prueba de carga final y capturas                             |
| **Mié 2 dic, 11PM**  | **Entrega del PDF** `CCU4-FinalProject-4.pdf`                |
| **Vie 4 dic, 4PM**   | **Presentación y demo en vivo por Zoom** (cámaras prendidas) |

---

## Cómo correrlo en local

```bash
cp .env.example .env      # y llenar los valores
docker compose up --build
```

- Web: http://localhost:3000
- API: http://localhost:8000/health

_(Los puertos pueden cambiar cuando Carlos defina los servicios.)_

---

## Recordatorios

- Tomen capturas de todo con **fecha y hora visibles**. Las de Locust deben coincidir con las de creación y terminación de instancias en AWS.
- Anoten los problemas que les salgan (estado, latencia, ruteo). Los vamos a necesitar para el post-mortem.
- Las instancias de AWS solo deben vivir de 5 a 10 minutos. Si algo se queda prendido, avisen.
