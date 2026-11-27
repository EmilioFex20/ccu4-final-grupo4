# Diagrama de arquitectura (borrador)

Borrador del Milestone 1, actualizado con los componentes de monitoreo implementados por Johana. Los bloques marcados como `planeado` dependen de código que aún no existe en el repositorio (controller, proxy y Lambda).

```mermaid
flowchart LR
    Cliente[Cliente web / Locust] -->|HTTP| Web[web: Nginx :3000 -> :8080]
    Cliente -->|API_URL :8000| API[api: FastAPI]

    subgraph Local[Stack local · docker compose]
        Web --> API
        API --> PG[(Postgres 16 · pgdata)]
        API --> Redis[(Redis 7 · cache /menu)]
    end

    subgraph CI[CI/CD · Jesús]
        GH[GitHub Actions] -->|build + test| GHCR[(GHCR api/web)]
        GH -->|smoke test| Local
    end

    subgraph Floci[Floci · Emilio]
        GHCR --> Tasks[Task definitions ECS locales]
        Tasks --> PG
        Tasks --> Redis
        Tasks --> API
        Tasks --> Web
    end

    subgraph AWS[AWS · Emilio]
        Controller[Controller planeado] -->|boto3 RunInstances t2/t3.micro| EC2[Instancias EC2 5-10 min]
        Controller -->|TerminateInstances| EC2
        IAM[IAM Policy · Johana] -.->|limita tipo y región| Controller
        Budget[Budget 1 USD · Johana] -.->|notifica| Email[Correo del equipo]
    end

    subgraph Observability[Observabilidad · Johana]
        Exporter[app-exporter + docker-exporter] -->|scrape| Prom[Prometheus + reglas]
        Prom --> Grafana[Grafana · dashboards aprovisionados]
        Exporter -->|/health, /menu| API
        Exporter -->|Docker Engine API| Local
        Controller -.->|targets.d pendiente| Prom
        Proxy[Reverse proxy planeado · Jesús] -.->|targets.d pendiente| Prom
    end

    Lambda[Lambda planeada · Carlos] -.->|recibos| S3[(S3 planeado)]
    API -.->|evento pendiente| Lambda
```

## Contratos pendientes para completar el diagrama

| Componente | Integrante | Contrato que necesita Johana |
|---|---|---|
| Controller | Emilio | Dirección y puerto de `/metrics`, o alta de un archivo en `prometheus/targets.d/controller.json` con `{"targets":["host:9090"]}` |
| Reverse proxy | Jesús | Endpoint de métricas o registro en `targets.d/reverse-proxy.json` |
| Lambda | Carlos | Definición del evento `order created` y formato del recibo |

Las líneas punteadas representan integraciones pendientes, no flujos verificados.
