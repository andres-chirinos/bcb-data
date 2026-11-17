---
type: Reference
title: Glosario monetario y macroeconómico
description: Definiciones de denominaciones, agregados y términos usados por el BCB.
tags:
- glosario
- macroeconomia
- bcb
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

# Glosario monetario y macroeconómico

## Denominaciones

| Término | Significado |
| :--- | :--- |
| `MN` | Moneda nacional (boliviano). |
| `ME` | Moneda extranjera, principalmente dólares estadounidenses. |
| `MVDOL` | Unidad de cuenta indexada al dólar estadounidense mantenida por el BCB. |
| `UFV` | Unidad de Fomento de Vivienda, unidad indexada a la inflación. |
| `Total` | Agregado publicado por el BCB; no siempre equivale a `MN + ME`. |
| `PRO MEMORIA` | Partida informativa que no forma parte del total. |

## Agregados y sectores

| Término | Significado |
| :--- | :--- |
| `M1'` | Medio circulante ampliado (billetes, monedas y depósitos a la vista). |
| `M2'` | `M1'` más depósitos de ahorro y a plazo. |
| `M3'` | `M2'` más otros pasivos del sistema financiero. |
| `Base Monetaria` | Billetes y monedas en circulación más reservas bancarias. |
| `SPNF` | Sector Público No Financiero. |
| `TGN` | Tesoro General de la Nación. |
| `RIN` | Reservas Internacionales Netas. |
| `DEG` | Derechos Especiales de Giro del FMI. |
| `Encaje Legal` | Reservas obligatorias que los bancos mantienen en el BCB. |
| `Reporto` | Operación de venta con pacto de recompra usada para proveer liquidez. |
| `Bolsín` | Mecanismo de subasta de dólares del BCB al sistema financiero. |
| `Bolivianización` | Proporción de depósitos o créditos en moneda nacional. |

## Convenciones de este bundle

* `fecha` conserva el formato del API (`dd/mm/aaaa`); `fecha_iso` es la versión
  ordenable (`aaaa-mm-dd`).
* `delta = valor - anterior` en `kpis_long.csv`; `anterior` depende del corte y
  la variación.
* Las filas con valor nulo se omiten; una serie puede empezar después de 1987.
