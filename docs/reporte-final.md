# Reporte final · CCU4 Grupo 4

- Versión editable: [`CCU4-FinalProject-4.md`](CCU4-FinalProject-4.md)
- PDF generado: `CCU4-FinalProject-4.pdf` (en la raíz del repositorio)
- Generador: [`generar_pdf.py`](generar_pdf.py)
- Estado: **BORRADOR**. Incluye resultados reales de stack local, monitoreo, Locust, chaos y capturas de IAM/Budget en AWS; sigue marcando explícitamente lo que falta de los otros integrantes y las verificaciones AWS pendientes.
- Fecha de generación: 2026-11-27 13:15 -08:00; actualizado el 2026-11-27 14:47 -08:00 con evidencia AWS.

## Para completar la versión definitiva

1. Ejecutar la matriz de pruebas (`docs/matriz-pruebas.md`) con Docker activo: T13–T16 ya están ejecutadas y documentadas.
2. Copiar los resultados reales de Locust y chaos a `docs/evidencia/`: ya están en `2026-11-27-1314-stack-monitoreo-carga-chaos.md`.
3. Adjuntar la política IAM creada y ejecutar la prueba controlada de denegación; confirmar la entrega del correo de alerta del budget.
4. Obtener de Emilio los logs de creación y terminación de instancias AWS (5 a 10 minutos).
5. Obtener de Emilio y Jesús las capturas de Floci y GHCR Packages.
6. Obtener de Jesús el reverse proxy y de Emilio el controller para activar los targets de `prometheus/targets.d/` y cerrar el escenario `reverse_proxy` de chaos.
7. Actualizar `docs/CCU4-FinalProject-4.md` y volver a ejecutar:

```powershell
python docs/generar_pdf.py --input docs/CCU4-FinalProject-4.md --output CCU4-FinalProject-4.pdf
```

Si se prefiere otro entorno: `python -m pip install reportlab==4.4.10` y `python docs/generar_pdf.py`.

## Seguridad de credenciales

El 2026-11-27 GitGuardian detectó una contraseña genérica asociada al administrador de Grafana en el commit `cd6ffea` (ID `41459752`). La credencial se rotó en la base persistente sin borrar volúmenes; la anterior devuelve `401` y la nueva `200`. `.env.example` ya no contiene valores de contraseña y el Compose carga la credencial desde `.env` ignorado. El incidente está mitigado, pero no se declara cerrado hasta retirar el valor del historial o resolver la alerta en GitGuardian. Detalle: [`incidente-gitguardian-41459752.md`](incidente-gitguardian-41459752.md).

## Índice de documentación de Johana

| Tema | Archivo |
|---|---|
| Arquitectura y diagrama Mermaid | `docs/arquitectura.md` |
| IAM y Budget | `docs/guia-aws.md` |
| Evidencia real de IAM y Budget en AWS | `docs/evidencia/2026-11-27-1440-aws-iam-budget.md` |
| Milestone 1 | `docs/reporte-milestone-1.md` |
| Milestones 2 a 4 | `docs/reportes-milestones.md` |
| Integración con el equipo | `docs/integracion.md` |
| Monitoreo y Prometheus | `docs/guia-monitoreo.md` |
| Grafana | `docs/guia-grafana.md` |
| Locust | `docs/guia-locust.md` |
| Chaos engineering | `docs/guia-chaos.md` |
| Matriz de pruebas | `docs/matriz-pruebas.md` |
| Incidencias | `docs/incidencias.md` |
| Incidente GitGuardian 41459752 | `docs/incidente-gitguardian-41459752.md` |
| Post-mortem | `docs/post-mortem.md` |
| Evidencias | `docs/evidencia/README.md` |
