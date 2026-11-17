---
type: BCB Statistical Sector
title: Sector Financiero
description: Sector 'Sector Financiero' del panel de Estadísticas Semanales del BCB con 14 variables y 35 series.
tags:
- bcb
- sector
- sector_financiero
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
resource: ../data/sectores/sector_financiero.csv
---

# Sector Financiero

## Description & Domain Context

Sector **Sector Financiero** del panel del BCB. Agrupa **14 variables** y
**35 series** (combinaciones variable × denominación). El CSV ancho del
sector contiene **469 filas** de fechas.

## Variables y denominaciones

| Variable | Denominaciones | Series |
| :--- | :--- | ---: |
| Ahorro en el Sistema Financiero | `MN`, `ME`, `Total`, `PRO MEMORIA MN` | 4 |
| Depósitos | `MN`, `ME`, `Total`, `PRO MEMORIA MN` | 4 |
| A la vista | `MN`, `ME`, `Total`, `PRO MEMORIA MN` | 4 |
| Caja de ahorro | `MN`, `ME`, `Total`, `PRO MEMORIA MN` | 4 |
| Plazo | `MN`, `ME`, `Total`, `PRO MEMORIA MN` | 4 |
| Otros | `MN`, `ME`, `Total`, `PRO MEMORIA MN` | 4 |
| Cartera | `MN`, `ME`, `Total`, `PRO MEMORIA MN` | 4 |
| Bolivianización del Ahorro | `Total` | 1 |
| Bolivianización de Depósitos | `Total` | 1 |
| Bolivianización Créditos | `Total` | 1 |
| Bolivianización Otros | `Total` | 1 |
| Bolivianización Plazo | `Total` | 1 |
| Bolivianización Caja de Ahorro | `Total` | 1 |
| Bolivianización Vista | `Total` | 1 |

## Operational Interaction & Example Queries

```sql
-- Serie más reciente de Sector Financiero
SELECT variable, moneda, fecha, valor
FROM read_csv_auto('data/series_long.csv')
WHERE sector = 'Sector Financiero'
ORDER BY fecha_iso DESC
LIMIT 20;
```

```python
import pandas as pd

df = pd.read_csv("data/sectores/sector_financiero.csv", parse_dates=["fecha_iso"])
print(df.tail())
```

## Archivos

* [CSV ancho del sector](../data/sectores/sector_financiero.csv)
* [Serie larga completa](../data/series_long.csv)
