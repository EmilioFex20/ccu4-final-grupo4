# Reporte final · CCU4 Grupo 4

- Versión editable: [`CCU4-FinalProject-4.md`](CCU4-FinalProject-4.md)
- PDF generado: `CCU4-FinalProject-4.pdf` (en la raíz del repositorio)
- Generador: [`generar_pdf.py`](generar_pdf.py)
- Estado: **BORRADOR**. Incluye resultados reales de stack local, monitoreo, Locust y chaos; sigue marcando explícitamente lo que falta de los otros integrantes.
- Fecha de generación: 2026-11-27 13:15 -08:00.

## Para completar la versión definitiva

1. Ejecutar la matriz de pruebas (`docs/matriz-pruebas.md`) con Docker activo: T13–T16 ya están ejecutadas y documentadas.
2. Copiar los resultados reales de Locust y chaos a `docs/evidencia/`: ya están en `2026-11-27-1314-stack-monitoreo-carga-chaos.md`.
3. Obtener de Emilio los logs de creación y terminación de instancias AWS (5 a 10 minutos).
4. Obtener de Emilio y Jesús las capturas de Floci y GHCR Packages.
5. Obtener de Jesús el reverse proxy y de Emilio el controller para activar los targets de `prometheus/targets.d/` y cerrar el escenario `reverse_proxy` de chaos.
6. Actualizar `docs/CCU4-FinalProject-4.md` y volver a ejecutar:

```powershell
python docs/generar_pdf.py --input docs/CCU4-FinalProject-4.md --output CCU4-FinalProject-4.pdf
```

Si se prefiere otro entorno: `python -m pip install reportlab==4.4.10` y `python docs/generar_pdf.py`.

## Índice de documentación de Johana

| Tema | Archivo |
|---|---|
| Arquitectura y diagrama Mermaid | `docs/arquitectura.md` |
| IAM y Budget | `docs/guia-aws.md` |
| Milestone 1 | `docs/reporte-milestone-1.md` |
| Milestones 2 a 4 | `docs/reportes-milestones.md` |
| Integración con el equipo | `docs/integracion.md` |
| Monitoreo y Prometheus | `docs/guia-monitoreo.md` |
| Grafana | `docs/guia-grafana.md` |
| Locust | `docs/guia-locust.md` |
| Chaos engineering | `docs/guia-chaos.md` |
| Matriz de pruebas | `docs/matriz-pruebas.md` |
| Incidencias | `docs/incidencias.md` |
| Post-mortem | `docs/post-mortem.md` |
| Evidencias | `docs/evidencia/README.md` |
