# Incidente de seguridad · GitGuardian 41459752

- Fecha de detección: 2026-11-27.
- ID de GitGuardian: `41459752`.
- Tipo: Generic Password.
- Commit público señalado: `cd6ffea`.
- Archivo señalado: `infra/monitoring/docker-compose.monitoring.yml`, línea 53.
- Rama: `feature/johana-sre`; PR: #3.
- Credencial afectada: contraseña del usuario administrador de Grafana. El valor no se reproduce en este documento.

## Alcance

El único servicio que consumía esa credencial era `grafana` en el Compose complementario de monitoreo. Prometheus y los exportadores `app-exporter` y `docker-exporter` no la usan. La credencial tampoco aparece en la API, Postgres, Redis, IAM ni en los scripts de carga o chaos.

## Causa raíz

La configuración versionada combinaba dos prácticas inseguras:

1. `infra/monitoring/.env.example` contenía un valor de ejemplo para la contraseña de Grafana. Ese valor podía copiarse tal cual a `.env` y parecer una credencial real.
2. `docker-compose.monitoring.yml` hacía referencia explícita a la variable de la contraseña en la sección `environment`, por lo que el detector asoció la línea 53 con la credencial.

GitGuardian señaló la línea de Compose, pero el valor detectable provenía del patrón de configuración de la contraseña administrativa de Grafana,no de una credencial de AWS ni del repositorio base.

## Remediación aplicada

- `docker-compose.monitoring.yml` ya no contiene la variable de contraseña en `environment`; el servicio `grafana` carga la configuración desde `env_file: .env`.
- `infra/monitoring/.env.example` deja `GF_SECURITY_ADMIN_PASSWORD=` vacío y documenta que el valor debe definirse solo en el `.env` local.
- `infra/monitoring/.env` está ignorado por Git y contiene una credencial aleatoria nueva generada localmente. No se subió al repositorio.
- La contraseña de la base persistente de Grafana se rotó con `grafana-cli admin reset-admin-password` dentro del contenedor, sin borrar el volumen `ccu4-monitoring_grafana-data`.
- Tras la rotación se verificó que la credencial anterior devuelve `401` y la nueva devuelve `200` en `GET /api/user`.
- El datasource `Prometheus` y el dashboard `CCU4 · Estado general de la cafetería` siguen presentes, con 1 y 1 elementos respectivamente.

## Verificación

- Escaneo del árbol de trabajo, archivos ignorados, PDF, evidencias e historial de commits: sin credenciales reales adicionales.
- No había `gitleaks`, `ggshield`, `trufflehog` ni `detect-secrets` instalados en el entorno; se ejecutó un escaneo determinista con patrones para AWS, GitHub, Slack, llaves privadas y contraseñas/tokens genéricos.
- `docker compose config --quiet`, Prometheus, exporters y Grafana se validaron después del cambio.

## Medidas preventivas

- Ninguna contraseña real en archivos versionados; `.env.example` solo documenta nombres de variables.
- Rotación inmediata ante cualquier detección, aun cuando el valor parezca de prueba.
- Revisión de secretos antes de cada commit y ejecución del escaneo en CI con una herramienta dedicada.
- Uso de un gestor de secretos para entornos compartidos; `.env` solo para desarrollo local.
- La alerta de GitGuardian no debe cerrarse solo por el nuevo commit: el valor original sigue existiendo en el historial del commit `cd6ffea`.

## Pendiente

Retirar la credencial del historial requiere reescribir la rama y hacer `force push`, acción que no se ejecutó porque el usuario no la autorizó explícitamente. Hasta que se autorice y se complete, la alerta de GitGuardian puede permanecer abierta aunque la credencial ya esté rotada y no permita acceso.
