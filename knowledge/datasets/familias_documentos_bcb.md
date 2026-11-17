---
type: dcat:Dataset
title: Familias de documentos tabulares del BCB
description: Catálogo de los 1.345 documentos descargados del portal del BCB, clasificados en 32 familias tabulares y con reglas de exclusión de formularios y duplicados.
tags:
- bcb
- catalogo
- documentos
- clasificacion
- bolivia
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
id: familias_documentos_bcb
conformsTo: https://openknowledge.org/okf/v0.2
spatial:
  country: BO
license: NOASSERTION
resources:
- name: familias_catalogo
  path: data/familias_catalogo.csv
  format: csv
  rows: 1345
  columns: 13
  bytes: 290384
  hash: sha256:77bffb705fb532d2a00e4b3af9072ff631026035f9aa56f70bae0adfc214a9f1
- name: familias_resumen
  path: data/familias_resumen.json
  format: json
  bytes: 1353
  hash: sha256:d5995f25665ce58f61e0f5cd7d8df84ce1fdd9653848705568374f42b1af8ca5
---

# Familias de documentos tabulares del BCB

## Description & Domain Context

El portal del BCB publica boletines, reportes de tasas, estadísticas semanales,
balances monetarios, documentos del sistema de pagos y material administrativo.
El scraper descargó **1.345 archivos**; este dataset documenta su clasificación
en **32 familias tabulares** antes de la extracción de datos.

El catálogo es la entrada de dos pipelines:

* [bcb_families.py](../pipeline/bcb_families.md) asigna familia y decide qué
  archivos son procesables.
* [bcb_tidy_families.py](../pipeline/bcb_tidy_families.md) extrae las hojas a
  un panel tidy por familia.

## Cobertura

| Concepto | Cantidad |
| :--- | ---: |
| Archivos en el manifiesto | 1.345 |
| Archivos en el catálogo | 1.345 |
| Procesables | 1.266 |
| Formularios o plantillas excluidos | 7 |
| ODS duplicados de XLSX | 71 |
| Familias tabulares | 32 |

| Grupo | Procesables |
| :--- | ---: |
| Tasas y precios | 650 |
| Boletín estadístico | 226 |
| Sistema de pagos | 109 |
| Estadísticas semanales | 99 |
| Sector externo | 84 |
| Sector monetario | 56 |
| Balanza de pagos | 15 |
| Posición de inversión internacional | 16 |
| Otros (deuda, memoria, programa, resumen) | 11 |

## Data Dictionary & Semantic Anchors

`familias_catalogo.csv` contiene una fila por archivo del manifiesto. Las
columnas principales son `familia`, `procesar`, `es_formulario`, `motivo`,
`archivo`, `relpath`, `extension`, `publicacion`, `requiere_conversion`,
`duplicado`, `sha256` y `status_descarga`.

`familias_resumen.json` resume los totales y el conteo por familia. Consulte el
[dataset de Estadísticas Semanales](estadisticas_semanales_bcb.md) para las
series del panel principal.

## Operational Interaction & Example Queries

```python
import pandas as pd

catalogo = pd.read_csv("data/familias_catalogo.csv")
print(catalogo.groupby("familia")["procesar"].apply(lambda s: (s == "si").sum()).sort_values(ascending=False))
```

```sql
-- Archivos procesables de la familia de tasas diarias
SELECT archivo, relpath, publicacion
FROM read_csv_auto('data/familias_catalogo.csv')
WHERE familia = 'tasas_diarias' AND procesar = 'si'
ORDER BY publicacion;
```

## Method, Scope & Biases

* **Clasificación por ruta y nombre:** no inspecciona el contenido de cada
  archivo; un nombre atípico puede terminar en `otros_webdocs`.
* **Una familia por archivo:** un libro con varias tablas heterogéneas se
  asigna a la familia dominante de su ruta.
* **Duplicados por nombre base:** un ODS se excluye cuando existe un XLSX
  equivalente en el mismo directorio.
* **Calendario editorial:** se cataloga pero no se procesa por no contener
  datos.
* **Extracción posterior:** la calidad final depende de la detección de layout
  de cada hoja; revise `archivos.csv` y `series.csv` de la familia antes de
  usar los datos.
