---
type: Tabular Resource
title: series_wide.csv — formato ancho
description: Matriz de fechas por series con columnas 'Sector | Variable [Moneda]'.
tags:
- csv
- wide-data
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
resource: ../data/series_wide.csv
---

# series_wide.csv

## Description & Domain Context

Matriz ancha con una fila por fecha y una columna por serie. Los nombres de
columna siguen el patrón `Sector | Variable [Moneda]`.

* Filas: **469**
* Columnas: **146** (2 de fecha + 144 series)
* Tamaño: **882.194 bytes**
* SHA-256: `sha256:f4a2e29520afee5fff375033f9380b9dd25b0a08fa79dc6d9a72dc4bcb27fa08`

## Data Dictionary & Semantic Anchors

| Columna | Tipo | Descripción |
| :--- | :--- | :--- |
| `fecha` | string | Fecha original `dd/mm/aaaa`. |
| `fecha_iso` | string | Fecha ISO 8601. |
| `Sector \| Variable [Moneda]` | number | Valor de la serie; celda vacía si no hay dato. |

## Operational Interaction & Example Queries

```python
import pandas as pd

wide = pd.read_csv("data/series_wide.csv", parse_dates=["fecha_iso"])
col = "Banca Central | Base Monetaria [Total]"
print(wide[["fecha_iso", col]].dropna().tail())
```

## Archivo

* [series_wide.csv](../data/series_wide.csv)
