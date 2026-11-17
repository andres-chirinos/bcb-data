---
type: BCB Statistical Sector
title: Tipos de cambio y valor referencial del dólar estadounidense
description: Sector 'Tipos de cambio y valor referencial del dólar estadounidense' del panel de Estadísticas Semanales del BCB con 4 variables y 4 series.
tags:
- bcb
- sector
- tipos_de_cambio_y_valor_referencial_del_dolar_estadounidense
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
resource: ../data/sectores/tipos_de_cambio_y_valor_referencial_del_dolar_estadounidense.csv
---

# Tipos de cambio y valor referencial del dólar estadounidense

## Description & Domain Context

Sector **Tipos de cambio y valor referencial del dólar estadounidense** del panel del BCB. Agrupa **4 variables** y
**4 series** (combinaciones variable × denominación). El CSV ancho del
sector contiene **451 filas** de fechas.

## Variables y denominaciones

| Variable | Denominaciones | Series |
| :--- | :--- | ---: |
| Valor referencial de compra del dólar estadounidense | `Total` | 1 |
| Valor referencial de venta del dólar estadounidense | `Total` | 1 |
| Tipo de cambio de venta en el Bolsín | `Total` | 1 |
| Tipo de Cambio Oficial compra BCB | `Total` | 1 |

## Operational Interaction & Example Queries

```sql
-- Serie más reciente de Tipos de cambio y valor referencial del dólar estadounidense
SELECT variable, moneda, fecha, valor
FROM read_csv_auto('data/series_long.csv')
WHERE sector = 'Tipos de cambio y valor referencial del dólar estadounidense'
ORDER BY fecha_iso DESC
LIMIT 20;
```

```python
import pandas as pd

df = pd.read_csv("data/sectores/tipos_de_cambio_y_valor_referencial_del_dolar_estadounidense.csv", parse_dates=["fecha_iso"])
print(df.tail())
```

## Archivos

* [CSV ancho del sector](../data/sectores/tipos_de_cambio_y_valor_referencial_del_dolar_estadounidense.csv)
* [Serie larga completa](../data/series_long.csv)
