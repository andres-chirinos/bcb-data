---
type: Software Pipeline
title: bcb_families.py — clasificación documental del BCB
description: Clasifica el corpus descargado del BCB en familias tabulares, excluye formularios, calendarios y ODS duplicados, y genera el catálogo de entrada para la normalización.
tags:
- python
- etl
- clasificacion
- bcb
- reproducibilidad
generated:
  by: process:bcb_families.py/1.0
  at: '2026-11-16T23:01:50-04:00'
verified:
- by: process:bcb_families.py/1.0
  at: '2026-11-16T23:01:50-04:00'
status: stable
stale_after: '2027-06-30T00:00:00Z'
sources:
- id: portal-bcb
  resource: https://www.bcb.gob.bo/
  title: Portal del Banco Central de Bolivia
  author: Banco Central de Bolivia
  last_modified: '2026-11-16T00:00:00Z'
resource: scripts/03_familias/bcb_families.py
executor:
  resource: scripts/03_familias/bcb_families.py
attester:
  resource: scripts/03_familias/bcb_families.py
---

# bcb_families.py — clasificación documental del BCB

## Description & Domain Context

El scraper del portal del BCB descarga publicaciones heterogéneas: boletines,
reportes de tasas, estadísticas semanales, balances monetarios, documentos de
sistema de pagos, formularios y plantillas. Este script lee
`documentos-bcb/manifiesto.csv`, clasifica cada archivo en una **familia
tabular** y escribe un catálogo que sirve de entrada al normalizador
[bcb_tidy_families.py](bcb_tidy_families.md).

* Script: [scripts/03_familias/bcb_families.py](scripts/03_familias/bcb_families.py)
* SHA-256: `sha256:7ab2f75b4b8ead641baca43d0b48a0bcced8fd6576c2bb736199e83b865ba288`
* Catálogo: [familias_catalogo.csv](../data/familias_catalogo.csv)
* Resumen: [familias_resumen.json](../data/familias_resumen.json)

## Operational Interaction & Example Queries

```bash
# Catálogo estándar sobre ./documentos-bcb
python3 knowledge/pipeline/scripts/03_familias/bcb_families.py

# Rutas explícitas
python3 knowledge/pipeline/scripts/03_familias/bcb_families.py \
  --docs documentos-bcb \
  --out knowledge/data/familias/catalogo.csv \
  --resumen knowledge/data/familias/resumen_familias.json
```

| Opción | Efecto |
| :--- | :--- |
| `--docs` | Directorio con `manifiesto.csv` y archivos descargados. |
| `--out` | Ruta del catálogo CSV de salida. |
| `--resumen` | Ruta del resumen JSON de conteos. |
| `--incluir-duplicados` | No excluye los ODS que duplican un XLSX. |

## Reglas de clasificación

* **Rutas:** `tasas_interes/`, `05_estadisticassemanales/`,
  `publicacionesbcb/`, `sistema_pagos/`, `sector_externo/A–G/`,
  `sector_monetario/…`, `sector_precios/…` y `Documentos Adjuntos/`.
* **Nombres:** patrones como `Semanal NN_AAAA`, `TD_dd_mm_aaaa`,
  `30 DC S`, `BOP_Tn_AAAA` o `Publicacion AAAA M D` alimentan la fecha de
  publicación.
* **Formularios:** se excluyen rutas de `serviciosbcb/formularios/`,
  `riof/`, `open_bcb/`, `licitacionesbcb/` y nombres `Form_*`.
* **No tabulares:** sólo se procesan `.xlsx`, `.xlsm`, `.xlsb`, `.xls`,
  `.ods`, `.csv` y `.tsv`.
* **Duplicados:** un `.ods` se excluye si existe un `.xlsx` con el mismo
  directorio y nombre base.
* **Calendario editorial:** `Otros/Cronograma_anual_de_publicaciones_2026.xlsx`
  se cataloga como `calendario_publicaciones`, pero no se procesa porque no
  contiene datos.

## Cobertura del catálogo

| Grupo | Archivos procesables |
| :--- | ---: |
| Tasas y precios | 650 |
| Boletín estadístico | 226 |
| Sistema de pagos | 109 |
| Estadísticas semanales | 99 |
| Sector externo | 84 |
| Sector monetario | 56 |
| Balanza de pagos | 15 |
| Posición de inversión internacional | 16 |
| Deuda externa, memoria, programa monetario y resumen | 11 |
| **Total** | **1.266** |

El manifiesto contiene 1.345 archivos. El catálogo marca además **7
formularios** y **71 ODS duplicados** como no procesables.

## Data Dictionary & Semantic Anchors

| Columna | Descripción |
| :--- | :--- |
| `familia` | Familia tabular asignada; vacía si es formulario. |
| `procesar` | `si` o `no`. |
| `es_formulario` | Marca de formulario o plantilla. |
| `motivo` | Razón de exclusión, si aplica. |
| `archivo` | Nombre del archivo. |
| `relpath` | Ruta relativa dentro de `documentos-bcb/`. |
| `extension` | Extensión en minúsculas. |
| `size_bytes` | Tamaño descargado. |
| `publicacion` | Fecha de publicación inferida (`AAAA-MM-DD`). |
| `requiere_conversion` | `si` para XLS, XLSB y ODS. |
| `duplicado` | `si` para ODS duplicado de XLSX. |
| `sha256` | Hash del archivo descargado. |
| `status_descarga` | Estado reportado por el manifiesto. |

## Methodology, Scope & Biases

* La clasificación es **heurística por ruta y nombre**; un archivo mal
  nombrado puede caer en `otros_webdocs` o en una familia vecina.
* El catálogo es una fotografía del manifiesto: no vuelve a descargar ni
  verifica el contenido interno del archivo.
* Los conteos de familias se calculan sólo sobre `procesar == "si"`.
* La fecha de publicación se infiere del nombre o de la ruta; no siempre es
  la fecha editorial exacta.
