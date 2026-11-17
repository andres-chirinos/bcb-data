---
type: BCB Statistical Sector
title: Unidad de Fomento de Vivienda
description: Sector 'Unidad de Fomento de Vivienda' del panel de Estadísticas Semanales del BCB con 2 variables y 2 series.
tags:
- bcb
- sector
- unidad_de_fomento_de_vivienda
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
resource: ../data/sectores/unidad_de_fomento_de_vivienda.csv
---

# Unidad de Fomento de Vivienda

## Description & Domain Context

Sector **Unidad de Fomento de Vivienda** del panel del BCB. Agrupa **2 variables** y
**2 series** (combinaciones variable × denominación). El CSV ancho del
sector contiene **312 filas** de fechas.

## Variables y denominaciones

| Variable | Denominaciones | Series |
| :--- | :--- | ---: |
| UFV (día hábil) | `Total` | 1 |
| UFV (último día del mes) | `Total` | 1 |

## Operational Interaction & Example Queries

```sql
-- Serie más reciente de Unidad de Fomento de Vivienda
SELECT variable, moneda, fecha, valor
FROM read_csv_auto('data/series_long.csv')
WHERE sector = 'Unidad de Fomento de Vivienda'
ORDER BY fecha_iso DESC
LIMIT 20;
```

```python
import pandas as pd

df = pd.read_csv("data/sectores/unidad_de_fomento_de_vivienda.csv", parse_dates=["fecha_iso"])
print(df.tail())
```

## Archivos

* [CSV ancho del sector](../data/sectores/unidad_de_fomento_de_vivienda.csv)
* [Serie larga completa](../data/series_long.csv)
