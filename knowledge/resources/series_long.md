---
type: Tabular Resource
title: series_long.csv — formato largo
description: Una fila por sector, variable, moneda y fecha; fuente canónica del bundle.
tags:
- csv
- tidy-data
- series-temporales
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
resource: ../data/series_long.csv
---

# series_long.csv

## Description & Domain Context

Formato largo canónico: una fila por combinación de sector, variable,
denominación monetaria y fecha. Es el artefacto recomendado para filtros,
agregaciones y series temporales.

* Filas: **53.938**
* Columnas: **6**
* Tamaño: **4.866.684 bytes**
* SHA-256: `sha256:82d3dcedc1ece1930a88a025fd5e7184326f85e824f57abba9a9d36595ff45ad`

## Data Dictionary & Semantic Anchors

| Columna | Tipo | Descripción |
| :--- | :--- | :--- |
| `sector` | string | Sector temático del BCB (p. ej. `Banca Central`). |
| `variable` | string | Nombre de la variable tal como la publica el BCB. |
| `moneda` | string | Denominación: `MN`, `ME`, `MVDOL`, `UFV`, `Total` o `PRO MEMORIA …`. |
| `fecha` | string | Fecha original del API en formato `dd/mm/aaaa`. |
| `fecha_iso` | string | Fecha normalizada ISO 8601 (`aaaa-mm-dd`) para ordenar y unir. |
| `valor` | number | Valor de la serie; puede ser negativo (p. ej. depósitos). |

Los valores nulos se omiten (no hay filas con `valor` vacío). Cada serie puede
tener una longitud distinta; no todas cubren los 469 períodos.

## Operational Interaction & Example Queries

```sql
-- Promedio anual de la Base Monetaria (Total)
SELECT date_trunc('year', fecha_iso) AS anio, avg(valor) AS promedio
FROM read_csv_auto('data/series_long.csv')
WHERE variable = 'Base Monetaria' AND moneda = 'Total'
GROUP BY 1 ORDER BY 1;
```

## Archivo

* [series_long.csv](../data/series_long.csv)
