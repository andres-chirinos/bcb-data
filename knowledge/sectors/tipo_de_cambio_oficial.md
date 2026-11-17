---
type: BCB Statistical Sector
title: Tipo de Cambio Oficial
description: Sector 'Tipo de Cambio Oficial' del panel de Estadísticas Semanales del BCB con 1 variables y 1 series.
tags:
- bcb
- sector
- tipo_de_cambio_oficial
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
resource: ../data/sectores/tipo_de_cambio_oficial.csv
---

# Tipo de Cambio Oficial

## Description & Domain Context

Sector **Tipo de Cambio Oficial** del panel del BCB. Agrupa **1 variables** y
**1 series** (combinaciones variable × denominación). El CSV ancho del
sector contiene **18 filas** de fechas.

## Variables y denominaciones

| Variable | Denominaciones | Series |
| :--- | :--- | ---: |
| Tipo de Cambio Oficial | `Total` | 1 |

## Operational Interaction & Example Queries

```sql
-- Serie más reciente de Tipo de Cambio Oficial
SELECT variable, moneda, fecha, valor
FROM read_csv_auto('data/series_long.csv')
WHERE sector = 'Tipo de Cambio Oficial'
ORDER BY fecha_iso DESC
LIMIT 20;
```

```python
import pandas as pd

df = pd.read_csv("data/sectores/tipo_de_cambio_oficial.csv", parse_dates=["fecha_iso"])
print(df.tail())
```

## Archivos

* [CSV ancho del sector](../data/sectores/tipo_de_cambio_oficial.csv)
* [Serie larga completa](../data/series_long.csv)
