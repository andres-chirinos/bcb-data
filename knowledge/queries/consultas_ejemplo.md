---
type: Playbook
title: Consultas de ejemplo
description: Recetas SQL (DuckDB) y pandas para explorar los CSV del bundle.
tags:
- sql
- duckdb
- pandas
- ejemplos
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
---

# Consultas de ejemplo

## DuckDB

```sql
-- 1. Panorama por sector
SELECT sector, count(*) AS filas, count(DISTINCT variable) AS variables
FROM read_csv_auto('data/series_long.csv')
GROUP BY sector ORDER BY filas DESC;

-- 2. Último dato de cada serie de Banca Central
SELECT variable, moneda, fecha, valor
FROM read_csv_auto('data/series_long.csv')
WHERE sector = 'Banca Central'
QUALIFY row_number() OVER (
    PARTITION BY variable, moneda ORDER BY fecha_iso DESC
) = 1
ORDER BY variable, moneda;

-- 3. Evolución anual de la Base Monetaria (Total)
SELECT date_trunc('year', fecha_iso) AS anio, avg(valor) AS promedio
FROM read_csv_auto('data/series_long.csv')
WHERE variable = 'Base Monetaria' AND moneda = 'Total'
GROUP BY 1 ORDER BY 1;

-- 4. KPI diarios más recientes
SELECT sector, variable, valor, anterior, delta, fecha
FROM read_csv_auto('data/kpis_long.csv')
WHERE corte = 'diario'
ORDER BY sector, variable;

-- 5. Exportar una serie a CSV
COPY (
  SELECT fecha_iso, valor
  FROM read_csv_auto('data/series_long.csv')
  WHERE sector = 'Sector Externo'
    AND variable = 'Reservas Internacionales Brutas'
    AND moneda = 'Total'
  ORDER BY fecha_iso
) TO 'rin.csv' (HEADER, DELIMITER ',');
```

## pandas

```python
import pandas as pd

largo = pd.read_csv("data/series_long.csv", parse_dates=["fecha_iso"])
ancho = pd.read_csv("data/series_wide.csv", parse_dates=["fecha_iso"])

# Serie mensual de inflación
inflacion = largo.query(
    "sector == 'Precios y tasas de intéres' and moneda == 'Total'"
)
print(inflacion.groupby("variable")["valor"].describe())

# Matriz de correlaciones de las series de Agregados Monetarios
agregados = [c for c in ancho.columns if c.startswith("Agregados Monetarios")]
print(ancho[agregados].corr())
```
