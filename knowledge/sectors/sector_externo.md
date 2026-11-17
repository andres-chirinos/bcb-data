---
type: BCB Statistical Sector
title: Sector Externo
description: Sector 'Sector Externo' del panel de Estadísticas Semanales del BCB con 24 variables y 24 series.
tags:
- bcb
- sector
- sector_externo
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
resource: ../data/sectores/sector_externo.csv
---

# Sector Externo

## Description & Domain Context

Sector **Sector Externo** del panel del BCB. Agrupa **24 variables** y
**24 series** (combinaciones variable × denominación). El CSV ancho del
sector contiene **469 filas** de fechas.

## Variables y denominaciones

| Variable | Denominaciones | Series |
| :--- | :--- | ---: |
| Reservas Internacionales Brutas | `Total` | 1 |
| Oro en toneladas | `Total` | 1 |
| Reservas de Oro neto de Pasivos en toneladas | `Total` | 1 |
| Oro | `Total` | 1 |
| Reservas de Oro neto de Pasivos | `Total` | 1 |
| Pasivos relacionados con operaciones con oro | `Total` | 1 |
| Divisas | `Total` | 1 |
| DEG | `Total` | 1 |
| Posición con el FMI | `Total` | 1 |
| Obligaciones de reservas | `Total` | 1 |
| Reservas Internacionales Netas | `Total` | 1 |
| RIN (Incluyendo obligaciones relativas al oro) | `Total` | 1 |
| Activos externos netos de entidades financieras de intermediación | `Total` | 1 |
| Adjudicación de dólares en el Bolsín (Sistema Financiero) | `Total` | 1 |
| Adjudicación de dólares en el Bolsín (Sector Privado) | `Total` | 1 |
| Adjudicación de dólares en Ventas Directas (Sistema Financiero) | `Total` | 1 |
| Adjudicación de dólares en Ventas Directas (Sector Privado) | `Total` | 1 |
| Compras de dólares al Sistema Financiero | `Total` | 1 |
| Transferencias del exterior al  Sistema Financiero a través del BCB | `Total` | 1 |
| Transferencias del Sistema Financiero al exterior a través del BCB  | `Total` | 1 |
| Transferencias al Exterior | `Total` | 1 |
| Transferencias del Exterior | `Total` | 1 |
| Índice de tipo de cambio real (base diciembre 2022=100) | `Total` | 1 |
| Recursos de Alta Líquidez | `Total` | 1 |

## Operational Interaction & Example Queries

```sql
-- Serie más reciente de Sector Externo
SELECT variable, moneda, fecha, valor
FROM read_csv_auto('data/series_long.csv')
WHERE sector = 'Sector Externo'
ORDER BY fecha_iso DESC
LIMIT 20;
```

```python
import pandas as pd

df = pd.read_csv("data/sectores/sector_externo.csv", parse_dates=["fecha_iso"])
print(df.tail())
```

## Archivos

* [CSV ancho del sector](../data/sectores/sector_externo.csv)
* [Serie larga completa](../data/series_long.csv)
