---
okf_version: '0.2'
type: dcat:Dataset
id: bcb_estadisticas_semanales
title: Estadísticas Semanales del Banco Central de Bolivia
description: Series monetarias, financieras, externas, de precios y de encaje publicadas por el BCB, normalizadas a CSV tabular, más el catálogo de familias documentales y la documentación del API y de los pipelines.
conformsTo: https://openknowledge.org/okf/v0.2
publisher:
  name: Banco Central de Bolivia (BCB)
  url: https://www.bcb.gob.bo/
spatial:
  country: BO
temporal:
  start: '1987-12-31T00:00:00Z'
  end: '2026-11-06T00:00:00Z'
  frequency: monthly
license: NOASSERTION
tags:
- bcb
- bolivia
- estadisticas
- macroeconomia
- series-temporales
- banca-central
resources:
- name: series_long
  path: data/series_long.csv
  format: csv
  rows: 53938
  columns: 6
  bytes: 4866684
  hash: sha256:82d3dcedc1ece1930a88a025fd5e7184326f85e824f57abba9a9d36595ff45ad
- name: series_wide
  path: data/series_wide.csv
  format: csv
  rows: 469
  columns: 146
  bytes: 882194
  hash: sha256:f4a2e29520afee5fff375033f9380b9dd25b0a08fa79dc6d9a72dc4bcb27fa08
- name: kpis_long
  path: data/kpis_long.csv
  format: csv
  rows: 430
  columns: 9
  bytes: 60414
  hash: sha256:b305802290664d63a4e7c0f4b7e9b1f829536ff21495bc23fcfffb88514d13ce
- name: familias_catalogo
  path: data/familias_catalogo.csv
  format: csv
  rows: 1345
  columns: 13
  bytes: 290384
  hash: sha256:77bffb705fb532d2a00e4b3af9072ff631026035f9aa56f70bae0adfc214a9f1
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
generated:
  by: process:okf_build.py/1.0
  at: '2026-11-16T20:42:27-04:00'
verified:
- by: process:bcb_scraper.py/1.0
  at: '2026-11-16T20:42:27-04:00'
status: stable
stale_after: '2027-06-30T00:00:00Z'
---

# Estadísticas Semanales del Banco Central de Bolivia

Este bundle documenta la extracción completa del panel **Estadísticas
Semanales** del Banco Central de Bolivia (BCB). Reúne 144 series
(86 variables en 10 sectores) para
469 cortes mensuales entre el **31/12/1987** y el **6/11/2026**,
más 430 filas de indicadores (KPI) diarios, semanales y mensuales.

## Contenido

* [Dataset: Estadísticas Semanales del BCB](datasets/estadisticas_semanales_bcb.md) - Alcance, metodología, cobertura y sesgos.
* [Familias de documentos tabulares](datasets/familias_documentos_bcb.md) - Catálogo de 1.345 archivos, exclusiones y cobertura por familia.
* [Recursos tabulares](resources/index.md) - Esquemas de `series_long.csv`, `series_wide.csv`, `kpis_long.csv` y `familias_catalogo.csv`.
* [Sectores](sectors/index.md) - Variables y denominaciones de cada uno de los 10 sectores.
* [API del BCB](api/bcb_estadisticas_api.md) - Endpoint, token, acciones `metadata`/`series`/`kpis` y límites.
* [Pipeline de extracción](pipeline/bcb_scraper.md) - Script reproducible, opciones CLI y manejo de errores.
* [Clasificación documental](pipeline/bcb_families.md) - Familias, exclusiones y catálogo de entrada.
* [Normalización tidy](pipeline/bcb_tidy_families.md) - Extracción con `unpivotr` y esquema de salida.
* [Referencias](references/index.md) - Glosario monetario, fuentes y limitaciones.
* [Consultas de ejemplo](queries/consultas_ejemplo.md) - SQL con DuckDB y pandas.
* [Historial de cambios](log.md) - Trazabilidad de la generación.

## Cifras clave

| Indicador | Valor |
| :--- | ---: |
| Sectores | 10 |
| Variables | 86 |
| Series (variable × moneda) | 144 |
| Períodos mensuales | 469 |
| Filas en `series_long.csv` | 53.938 |
| Filas en `kpis_long.csv` | 430 |
| Rango temporal | 31/12/1987 → 6/11/2026 |
| Última actualización BCB | 6/11/2026 |

## Inicio rápido

```python
import pandas as pd

df = pd.read_csv("data/series_long.csv", parse_dates=["fecha_iso"])
ultimo = (
    df[df["sector"] == "Banca Central"]
    .sort_values("fecha_iso")
    .groupby(["variable", "moneda"], as_index=False)
    .tail(1)
)
print(ultimo[["variable", "moneda", "fecha", "valor"]])
```

```sql
-- DuckDB: valor más reciente de cada serie de Banca Central
SELECT variable, moneda, fecha, valor
FROM read_csv_auto('data/series_long.csv')
WHERE sector = 'Banca Central'
QUALIFY row_number() OVER (
    PARTITION BY variable, moneda ORDER BY fecha_iso DESC
) = 1;
```

## Procedencia y licencia

Los datos son publicados por el BCB en su panel público. Este bundle los
redistribuye con fines de análisis y reproducibilidad; la licencia figura como
`NOASSERTION` porque los términos de reutilización deben confirmarse con el BCB.
Consulte [Fuentes](references/fuentes.md) para más detalle.
