# Post-mortem · Limitaciones de verificación

Fecha: 2026-11-27. Autor: Johana. Estado: actualizado con stack local, monitoreo, Locust, chaos y capturas de IAM/Budget en AWS; sigue pendiente la correlación con el controller.

## Qué pasó

La implementación de monitoreo, carga y resiliencia quedó lista y se verificó contra el stack local tras iniciar Docker Desktop. Locust completó 14,076 peticiones sin fallos y chaos validó la recuperación de `api` y `web` con un pedido real. Tampoco existen aún el controller de Emilio ni el reverse proxy de Jesús, y la API de Carlos no expone `/metrics`.

## Impacto

- Sí hay series temporales reales en Prometheus y un dashboard de Grafana aprovisionado con datos de sondas y contenedores.
- Sí hay CSV/HTML de Locust con 14,076 peticiones, 0 fallos, 52 req/s y p95 de 84 ms; 4,224 de esas peticiones fueron `POST /orders` reales.
- Sí hay resultados de chaos: ocho escenarios en `ok` y el de reverse proxy en `pendiente`.
- Sí hay evidencia visual de la creación de la política IAM y del presupuesto de 1 USD, con capturas redactadas.
- No hay evidencia de creación/terminación de instancias AWS ni correlación con `fases.log`; la política tampoco está adjuntada ni probada en vivo.
- Sí hay validaciones estáticas reales: IAM/Budget, JSON/YAML, Compose y Prometheus con `promtool`.

## Causa raíz

1. Entorno local inicialmente incompleto: Docker CLI instalado, daemon sin iniciar; se resolvió iniciando Docker Desktop.
2. Dependencias entre integrantes: las señales de escalamiento y ruteo requieren componentes que aún no están en `main`.
3. Decisión deliberada de no modificar código ajeno: instrumentar la API o sustituir el proxy cambiaría responsabilidades de Carlos y Jesús.
4. Defectos propios detectados al integrar: soporte de socket Unix en el exporter de Docker, uso de `/health` en chaos y codificación de PowerShell 5.1; todos corregidos y documentados en `docs/incidencias.md`.
5. Configuración de Grafana con un valor de contraseña de ejemplo y referencia explícita en Compose, detectada por GitGuardian como INC-12; credencial rotada y rotación verificada.

## Acciones correctivas

| Acción | Responsable | Estado |
|---|---|---|
| Iniciar Docker Desktop y ejecutar T13–T16 de la matriz | Johana | Completada; evidencia 13:14 |
| Registrar métricas del controller y del proxy en `targets.d/` | Emilio y Jesús | Pendiente |
| Autorizar o rechazar la instrumentación `/metrics` de la API | Carlos y equipo | Pendiente |
| Aportar captura de Floci y de GHCR Packages | Emilio/Jesús | Pendiente |
| Repetir el post-mortem con datos de AWS reales | Johana | Pendiente: requiere controller y autorización |
| Rotar y verificar la credencial de Grafana tras GitGuardian 41459752 | Johana | Completada; anterior `401`, nueva `200` |
| Resolver GitGuardian 41459752 en el dashboard | Johana + equipo | Pendiente: se eligió gestionar el incidente sin reescribir el historial; el check sigue rojo por `cd6ffea` |

## Lecciones aprendidas

- Separar las métricas de sonda de las métricas de tráfico real evita reportar información engañosa.
- Un Compose complementario permite integrar observabilidad sin editar el stack de otra persona.
- `promtool` permitió validar la configuración aunque Docker no estuviera disponible.
- La correlación temporal entre Locust y AWS debe quedar registrada desde el inicio de la prueba, no reconstruirse después.
- Probar los scripts contra el stack real reveló fallos que las pruebas estáticas no podían detectar; la verificación en vivo fue necesaria antes de entregar.
