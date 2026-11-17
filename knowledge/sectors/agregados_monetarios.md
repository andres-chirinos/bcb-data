---
type: BCB Statistical Sector
title: Agregados Monetarios
description: Sector 'Agregados Monetarios' del panel de Estadísticas Semanales del BCB con 6 variables y 15 series.
tags:
- bcb
- sector
- agregados_monetarios
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
resource: ../data/sectores/agregados_monetarios.csv
---

# Agregados Monetarios

## Description & Domain Context

Sector **Agregados Monetarios** del panel del BCB. Agrupa **6 variables** y
**15 series** (combinaciones variable × denominación). El CSV ancho del
sector contiene **469 filas** de fechas.

## Variables y denominaciones

| Variable | Denominaciones | Series |
| :--- | :--- | ---: |
| M1' | `MN`, `ME`, `Total`, `PRO MEMORIA ME` | 4 |
| M2' | `MN`, `ME`, `Total`, `PRO MEMORIA ME` | 4 |
| M3' | `MN`, `ME`, `Total`, `PRO MEMORIA ME` | 4 |
| M1/M1' | `Total` | 1 |
| M2/M2' | `Total` | 1 |
| M3/M3' | `Total` | 1 |

## Operational Interaction & Example Queries

```sql
-- Serie más reciente de Agregados Monetarios
SELECT variable, moneda, fecha, valor
FROM read_csv_auto('data/series_long.csv')
WHERE sector = 'Agregados Monetarios'
ORDER BY fecha_iso DESC
LIMIT 20;
```

```python
import pandas as pd

df = pd.read_csv("data/sectores/agregados_monetarios.csv", parse_dates=["fecha_iso"])
print(df.tail())
```

## Archivos

* [CSV ancho del sector](../data/sectores/agregados_monetarios.csv)
* [Serie larga completa](../data/series_long.csv)
