---
type: Tabular Resource
title: familias_catalogo.csv — catálogo de documentos BCB
description: Una fila por archivo descargado, con familia, estado de procesamiento y metadatos de descarga.
tags:
- csv
- catalogo
- bcb
- clasificacion
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
resource: ../data/familias_catalogo.csv
---

# familias_catalogo.csv

## Description & Domain Context

Catálogo de entrada del normalizador. Contiene los 1.345 archivos del
manifiesto, la familia asignada y las banderas de exclusión. Es la fuente para
decidir qué archivos procesa [bcb_tidy_families.py](../pipeline/bcb_tidy_families.md).

* Filas: **1.345**
* Columnas: **13**
* Tamaño: **290.384 bytes**
* SHA-256: `sha256:77bffb705fb532d2a00e4b3af9072ff631026035f9aa56f70bae0adfc214a9f1`

## Data Dictionary & Semantic Anchors

| Columna | Tipo | Descripción |
| :--- | :--- | :--- |
| `familia` | string | Familia tabular; vacía para formularios. |
| `procesar` | string | `si` o `no`. |
| `es_formulario` | string | `si` para formularios o plantillas. |
| `motivo` | string | Razón de exclusión. |
| `archivo` | string | Nombre del archivo. |
| `relpath` | string | Ruta relativa al corpus. |
| `extension` | string | Extensión del archivo. |
| `size_bytes` | integer | Tamaño descargado. |
| `publicacion` | date | Fecha de publicación inferida. |
| `requiere_conversion` | string | `si` para XLS/XLSB/ODS. |
| `duplicado` | string | `si` para ODS duplicado. |
| `sha256` | string | Hash del archivo. |
| `status_descarga` | string | Estado del manifiesto. |

## Operational Interaction & Example Queries

```sql
-- Familias con más archivos procesables
SELECT familia, count(*) AS archivos
FROM read_csv_auto('data/familias_catalogo.csv')
WHERE procesar = 'si'
GROUP BY familia
ORDER BY archivos DESC;
```

## Archivo

* [familias_catalogo.csv](../data/familias_catalogo.csv)
