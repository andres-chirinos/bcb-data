---
type: Tabular Resource
title: kpis_long.csv — indicadores de coyuntura
description: KPI por sector, corte, variación, variable y fecha.
tags:
- csv
- kpi
- coyuntura
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
resource: ../data/kpis_long.csv
---

# kpis_long.csv

## Description & Domain Context

Indicadores de coyuntura calculados por el BCB para cada sector. Una fila por
combinación de sector, corte, variación, variable y fecha.

* Filas: **430**
* Columnas: **9**
* Tamaño: **60.414 bytes**
* SHA-256: `sha256:b305802290664d63a4e7c0f4b7e9b1f829536ff21495bc23fcfffb88514d13ce`

## Data Dictionary & Semantic Anchors

| Columna | Tipo | Descripción |
| :--- | :--- | :--- |
| `sector` | string | Sector del KPI. |
| `corte` | string | `mensual`, `semanal` o `diario`. |
| `variacion` | string | `mensual`, `interanual` o `acumulada`. |
| `fecha` | string | Fecha del indicador (`dd/mm/aaaa`). |
| `fecha_iso` | string | Fecha ISO 8601. |
| `variable` | string | Variable del indicador. |
| `valor` | number | Valor actual. |
| `anterior` | number | Valor de referencia informado por el API. |
| `delta` | number | `valor - anterior` calculado por el scraper. |

> `anterior` depende del corte y de la variación; no lo interprete como una
> fecha fija. Para series históricas use `series_long.csv`.

## Operational Interaction & Example Queries

```sql
-- Últimos KPI diarios de Banca Central
SELECT variable, valor, anterior, delta, fecha
FROM read_csv_auto('data/kpis_long.csv')
WHERE sector = 'Banca Central' AND corte = 'diario'
ORDER BY variable;
```

## Archivo

* [kpis_long.csv](../data/kpis_long.csv)
