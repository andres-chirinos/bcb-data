---
type: BCB Statistical Sector
title: Operaciones con Títulos Públicos y financiamiento del BCB
description: Sector 'Operaciones con Títulos Públicos y financiamiento del BCB' del panel de Estadísticas Semanales del BCB con 6 variables y 14 series.
tags:
- bcb
- sector
- operaciones_con_titulos_publicos_y_financiamiento_del_bcb
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
resource: ../data/sectores/operaciones_con_titulos_publicos_y_financiamiento_del_bcb.csv
---

# Operaciones con Títulos Públicos y financiamiento del BCB

## Description & Domain Context

Sector **Operaciones con Títulos Públicos y financiamiento del BCB** del panel del BCB. Agrupa **6 variables** y
**14 series** (combinaciones variable × denominación). El CSV ancho del
sector contiene **351 filas** de fechas.

## Variables y denominaciones

| Variable | Denominaciones | Series |
| :--- | :--- | ---: |
| Saldos netos de títulos | `Total` | 1 |
| Tesoro General de la Nación | `MN, UFV`, `ME, MVDOL`, `Total` | 3 |
| Banco Central de Bolivia | `MN, UFV`, `ME, MVDOL`, `Total` | 3 |
| Financiamiento de corto plazo al sistema financiero | `Total` | 1 |
| Créditos de Liquidez c/garantía del encaje legal en títulos | `MN, UFV`, `ME, MVDOL`, `Total` | 3 |
| Reportos | `MN, UFV`, `ME, MVDOL`, `Total` | 3 |

## Operational Interaction & Example Queries

```sql
-- Serie más reciente de Operaciones con Títulos Públicos y financiamiento del BCB
SELECT variable, moneda, fecha, valor
FROM read_csv_auto('data/series_long.csv')
WHERE sector = 'Operaciones con Títulos Públicos y financiamiento del BCB'
ORDER BY fecha_iso DESC
LIMIT 20;
```

```python
import pandas as pd

df = pd.read_csv("data/sectores/operaciones_con_titulos_publicos_y_financiamiento_del_bcb.csv", parse_dates=["fecha_iso"])
print(df.tail())
```

## Archivos

* [CSV ancho del sector](../data/sectores/operaciones_con_titulos_publicos_y_financiamiento_del_bcb.csv)
* [Serie larga completa](../data/series_long.csv)
