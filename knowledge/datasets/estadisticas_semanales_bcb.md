---
type: dcat:Dataset
title: Estadísticas Semanales del Banco Central de Bolivia
description: Serie histórica de estadísticas semanales del BCB normalizada a formato tabular.
tags:
- bcb
- series-temporales
- bolivia
- macroeconomia
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
id: bcb_estadisticas_semanales
conformsTo: https://openknowledge.org/okf/v0.2
spatial:
  country: BO
temporal:
  start: '1987-12-31T00:00:00Z'
  end: '2026-11-06T00:00:00Z'
  frequency: monthly
license: NOASSERTION
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
---

# Estadísticas Semanales del Banco Central de Bolivia

## Description & Domain Context

El Banco Central de Bolivia publica en su panel `bcb_estadisticas` un conjunto
de series monetarias, financieras, cambiarias y de precios. Este bundle las
descarga mediante el API JSON del propio panel y las reorganiza en tres
artefactos tabulares:

* **`series_long.csv`** — formato largo, una fila por
  `(sector, variable, moneda, fecha)`. Es la fuente canónica.
* **`series_wide.csv`** — matriz de 469 filas por
  144 columnas de series, útil para gráficos y modelos.
* **`kpis_long.csv`** — indicadores de coyuntura por sector, corte
  (`mensual`, `semanal`, `diario`) y tipo de variación
  (`mensual`, `interanual`, `acumulada`).

Cobertura: **10 sectores**, **86 variables**,
**144 series** y **469 períodos** entre 31/12/1987 y
6/11/2026. La fecha de actualización declarada por el BCB al momento de la
extracción fue **6/11/2026**.

## Methodology, Scope & Biases

* **Fuente primaria:** API JSON del panel de Estadísticas Semanales del BCB
  (`action: metadata | series | kpis`, versión `v=4.0.5`).
* **Grano temporal:** mensual para `series`; los KPI agregan el último dato
  disponible según el corte solicitado.
* **Denominaciones:** cada variable puede publicarse en `MN` (moneda nacional),
  `ME` (moneda extranjera), `MVDOL` (unidad indexada), `UFV` (Unidad de Fomento
  de Vivienda), `Total` y variantes `PRO MEMORIA`. No sume denominaciones
  distintas sin verificar la definición en el [glosario](../references/glosario.md).
* **Revisiones:** el BCB puede corregir cifras históricas; este bundle es una
  fotografía y no un flujo incremental. Vuelva a ejecutar el scraper para
  refrescar.
* **Unidades:** el API no entrega unidades por variable. Consulte la definición
  del sector y del indicador antes de interpretar magnitudes.
* **Cobertura histórica:** las series comienzan en 1987; los primeros años
  incluyen el período de alta inflación y cambios de régimen monetario, por lo
  que las comparaciones de largo plazo requieren cautela.
* **KPI:** son un resumen de coyuntura, no una serie histórica completa. Para
  análisis temporal use `series_long.csv`.

## Operational Interaction & Example Queries

```sql
-- Último valor disponible por serie de Sector Externo
SELECT variable, moneda, fecha, valor
FROM read_csv_auto('data/series_long.csv')
WHERE sector = 'Sector Externo'
QUALIFY row_number() OVER (
    PARTITION BY variable, moneda ORDER BY fecha_iso DESC
) = 1
ORDER BY variable, moneda;
```

```python
import pandas as pd

df = pd.read_csv("data/series_long.csv")
print(df.groupby("sector").size().sort_values(ascending=False))
```

## Data Dictionary & Semantic Anchors

Los esquemas completos están en [Recursos tabulares](../resources/index.md).
Los conceptos monetarios y macroeconómicos se anclan en el
[glosario](../references/glosario.md).

## Archivos

* [series_long.csv](../data/series_long.csv)
* [series_wide.csv](../data/series_wide.csv)
* [kpis_long.csv](../data/kpis_long.csv)
* [Ejemplo: Banca Central](../data/sectores/banca_central.csv)
