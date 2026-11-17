---
type: BCB Statistical Sector
title: Precios y tasas de intéres
description: Sector 'Precios y tasas de intéres' del panel de Estadísticas Semanales del BCB con 11 variables y 11 series.
tags:
- bcb
- sector
- precios_y_tasas_de_interes
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
resource: ../data/sectores/precios_y_tasas_de_interes.csv
---

# Precios y tasas de intéres

## Description & Domain Context

Sector **Precios y tasas de intéres** del panel del BCB. Agrupa **11 variables** y
**11 series** (combinaciones variable × denominación). El CSV ancho del
sector contiene **469 filas** de fechas.

## Variables y denominaciones

| Variable | Denominaciones | Series |
| :--- | :--- | ---: |
| Variación mensual inflación total | `Total` | 1 |
| Variación acumulada en el año inflación total | `Total` | 1 |
| Variación a doce meses inflación total | `Total` | 1 |
| Variación mensual inflación núcleo | `Total` | 1 |
| Variación acumulada en el año inflación núcleo | `Total` | 1 |
| Variación a doce meses inflación núcleo | `Total` | 1 |
| Variación mensual inflación subyacente | `Total` | 1 |
| Variación acumulada en el año inflación subyacente | `Total` | 1 |
| Variación a doce meses inflación subyacente | `Total` | 1 |
| Tasa premio de reporto del BCB en MN | `Total` | 1 |
| Tasa premio de reporto del BCB en ME | `Total` | 1 |

## Operational Interaction & Example Queries

```sql
-- Serie más reciente de Precios y tasas de intéres
SELECT variable, moneda, fecha, valor
FROM read_csv_auto('data/series_long.csv')
WHERE sector = 'Precios y tasas de intéres'
ORDER BY fecha_iso DESC
LIMIT 20;
```

```python
import pandas as pd

df = pd.read_csv("data/sectores/precios_y_tasas_de_interes.csv", parse_dates=["fecha_iso"])
print(df.tail())
```

## Archivos

* [CSV ancho del sector](../data/sectores/precios_y_tasas_de_interes.csv)
* [Serie larga completa](../data/series_long.csv)
