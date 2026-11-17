---
type: BCB Statistical Sector
title: Banca Central
description: Sector 'Banca Central' del panel de Estadísticas Semanales del BCB con 10 variables y 27 series.
tags:
- bcb
- sector
- banca_central
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
resource: ../data/sectores/banca_central.csv
---

# Banca Central

## Description & Domain Context

Sector **Banca Central** del panel del BCB. Agrupa **10 variables** y
**27 series** (combinaciones variable × denominación). El CSV ancho del
sector contiene **469 filas** de fechas.

## Variables y denominaciones

| Variable | Denominaciones | Series |
| :--- | :--- | ---: |
| Base Monetaria | `Total` | 1 |
| Billetes y Monedas | `Total` | 1 |
| Reservas bancarias | `MN`, `ME`, `MVDOL`, `UFV`, `Total`, `PRO MEMORIA ME + MVDOL` | 6 |
| Base monetaria en moneda nacional (MN + UFV) | `Total` | 1 |
| Crédito Interno Neto | `MN`, `ME`, `Total`, `PRO MEMORIA ME` | 4 |
| Crédito Neto al SPNF | `Total` | 1 |
| Crédito del BCB al SPNF | `MN`, `ME`, `Total`, `PRO MEMORIA ME` | 4 |
| Depósitos del SPNF en el BCB | `MN`, `ME`, `Total`, `PRO MEMORIA ME` | 4 |
| Crédito a otros sectores (financiero y privado) | `MN`, `ME`, `Total`, `PRO MEMORIA ME` | 4 |
| Emisión Monetaria | `Total` | 1 |

## Operational Interaction & Example Queries

```sql
-- Serie más reciente de Banca Central
SELECT variable, moneda, fecha, valor
FROM read_csv_auto('data/series_long.csv')
WHERE sector = 'Banca Central'
ORDER BY fecha_iso DESC
LIMIT 20;
```

```python
import pandas as pd

df = pd.read_csv("data/sectores/banca_central.csv", parse_dates=["fecha_iso"])
print(df.tail())
```

## Archivos

* [CSV ancho del sector](../data/sectores/banca_central.csv)
* [Serie larga completa](../data/series_long.csv)
