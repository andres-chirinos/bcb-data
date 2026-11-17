---
type: Reference
title: Limitaciones y advertencias de uso
description: Sesgos, cobertura irregular, revisiones y precauciones analíticas.
tags:
- limitaciones
- calidad-de-datos
- advertencias
generated:
  by: process:okf_build.py/1.0
  at: '2026-11-16T20:42:27-04:00'
verified:
- by: process:bcb_scraper.py/1.0
  at: '2026-11-16T20:42:27-04:00'
status: stable
stale_after: '2027-06-30T00:00:00Z'
sources:
- id: panel-bcb
  resource: https://www.bcb.gob.bo/bcb_estadisticas/index.php
  title: Panel de Estadísticas Semanales del BCB
  author: Banco Central de Bolivia
  last_modified: '2026-11-06T00:00:00Z'
- id: api-bcb
  resource: https://www.bcb.gob.bo/bcb_estadisticas/api.php?v=4.0.5
  title: API JSON de Estadísticas Semanales (v=4.0.5)
  author: Banco Central de Bolivia
  last_modified: '2026-11-06T00:00:00Z'
---

# Limitaciones y advertencias de uso

1. **Fotografía temporal.** Los datos reflejan la respuesta del BCB al
   6/11/2026; revisiones posteriores no se propagan
   automáticamente.
2. **Cobertura irregular.** De las 144 series, no todas cubren los
   469 períodos. Use `fecha_iso` y verifique nulos implícitos.
3. **Denominaciones no sumables.** `MN`, `ME`, `MVDOL`, `UFV` y `Total` miden
   cosas distintas. No agregue denominaciones sin revisar el
   [glosario](glosario.md).
4. **Partidas `PRO MEMORIA`.** Son informativas y no deben sumarse al total.
5. **Unidades ausentes.** El API no expone unidades por variable; consulte la
   definición del indicador antes de comparar magnitudes.
6. **KPI no históricos.** `kpis_long.csv` contiene el último dato según corte;
   para análisis temporal use `series_long.csv`.
7. **Rupturas estructurales.** La serie arranca en 1987 e incluye cambios de
   régimen monetario y de política cambiaria; las comparaciones de muy largo
   plazo pueden no ser homogéneas.
8. **Dependencia del portal.** El token y las rutas del API pueden cambiar sin
   aviso; si el scraper falla, revise `index.php` y el error registrado en
   `manifest.json`.
9. **Extracción documental heurística.** Las familias se clasifican por ruta y
   nombre, y los layouts se infieren por densidad de datos. Hojas con varios
   cuadros apilados, gráficos o encabezados atípicos pueden requerir revisión
   manual; contraste `archivos.csv` y `series.csv` antes de usar una familia.
10. **Cobertura desigual.** El catálogo tiene 1.266 archivos procesables en 32
    familias, pero no todas las hojas producen series útiles. Las hojas de
    gráficos, notas y cuadros de una sola fecha pueden quedar fuera o generar
    series de cobertura mínima.
