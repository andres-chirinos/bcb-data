---
type: BCB Statistical Sector
title: Encaje Legal
description: Sector 'Encaje Legal' del panel de Estadísticas Semanales del BCB con 8 variables y 11 series.
tags:
- bcb
- sector
- encaje_legal
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
resource: ../data/sectores/encaje_legal.csv
---

# Encaje Legal

## Description & Domain Context

Sector **Encaje Legal** del panel del BCB. Agrupa **8 variables** y
**11 series** (combinaciones variable × denominación). El CSV ancho del
sector contiene **341 filas** de fechas.

## Variables y denominaciones

| Variable | Denominaciones | Series |
| :--- | :--- | ---: |
| Encaje Constituido | `Total` | 1 |
| Efectivo MN, UFV | `Total`, `PRO MEMORIA MN` | 2 |
| Títulos MN, UFV | `Total`, `PRO MEMORIA MN` | 2 |
| Efectivo ME, MVDOL | `Total` | 1 |
| Títulos ME, MVDOL | `Total` | 1 |
| Excedente de Encaje | `Total` | 1 |
| Excedente MN, UFV | `Total`, `PRO MEMORIA MN` | 2 |
| Excedente ME, MVDOL | `Total` | 1 |

## Operational Interaction & Example Queries

```sql
-- Serie más reciente de Encaje Legal
SELECT variable, moneda, fecha, valor
FROM read_csv_auto('data/series_long.csv')
WHERE sector = 'Encaje Legal'
ORDER BY fecha_iso DESC
LIMIT 20;
```

```python
import pandas as pd

df = pd.read_csv("data/sectores/encaje_legal.csv", parse_dates=["fecha_iso"])
print(df.tail())
```

## Archivos

* [CSV ancho del sector](../data/sectores/encaje_legal.csv)
* [Serie larga completa](../data/series_long.csv)
