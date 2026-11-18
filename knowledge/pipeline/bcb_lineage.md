---
type: Software Pipeline
title: bcb_lineage.py — linaje RAW → limpio con datamesh-sdk
description: Escribe el linaje de cada familia limpia (documentos crudos y scripts) en datapackage.json y lo valida con el grafo de datamesh-sdk.
tags:
- python
- linaje
- datamesh
- prov-o
- bcb
generated:
  by: process:bcb_lineage.py/1.0
  at: '2026-11-17T00:05:00-04:00'
verified:
- by: process:bcb_lineage.py/1.0
  at: '2026-11-17T00:05:00-04:00'
status: stable
stale_after: '2027-06-30T00:00:00Z'
sources:
- id: datamesh-sdk
  resource: https://github.com/datosbolivia/datamesh
  title: datamesh-sdk (DatasetLineageUseCase)
  author: Banco Central de Bolivia
  last_modified: '2026-11-16T00:00:00Z'
resource: scripts/06_linaje/bcb_lineage.py
executor:
  resource: scripts/06_linaje/bcb_lineage.py
attester:
  resource: scripts/06_linaje/bcb_lineage.py
---

# bcb_lineage.py — linaje RAW → limpio con datamesh-sdk

## Description & Domain Context

Etapa 06. Por cada `data/familias/<familia>/datos.csv` añade al
[datapackage](../datapackage.json) un recurso `familia_<familia>` con SHA-256,
tamaño, filas y series, más un bloque `lineage`:

* `sources`: un documento crudo por cada valor distinto de la columna `archivo`,
  con su SHA-256 y como `url` la captura de [bcb_archive.py](bcb_archive.md), el
  respaldo en archive.org o la URL original si aún no existe respaldo.
* `transformations`: [bcb_families.py](bcb_families.md) y
  [bcb_tidy_families.py](bcb_tidy_families.md) con el hash de cada script.

Después construye el grafo con `DatasetLineageUseCase` de datamesh-sdk y falla si
algún recurso limpio no tiene origen aguas arriba. Consulta posterior:
`datamesh lineage bcb_estadisticas_semanales:familia_tasas_referencia`.

* Script: [scripts/06_linaje/bcb_lineage.py](scripts/06_linaje/bcb_lineage.py)
* SHA-256: `sha256:80491712ce44900b7a016f7bbacf1f44db0f6cda7f5ffc5f7781a7a85f9d3d81`
* Dependencias: [scripts/06_linaje/requirements.txt](scripts/06_linaje/requirements.txt)

## Operational Interaction & Example Queries

```bash
python3 knowledge/pipeline/scripts/06_linaje/bcb_lineage.py
python3 knowledge/pipeline/scripts/06_linaje/bcb_lineage.py --mermaid linaje.mmd
```

| Opción | Efecto |
| :--- | :--- |
| `--package` | `datapackage.json` a actualizar. |
| `--docs` | Directorio con `manifiesto.csv` y `archivo.csv`. |
| `--familias` | Directorio de salidas por familia. |
| `--mermaid` | Escribe el grafo en Mermaid. |

La ruta del SDK se toma de `DATAMESH_SDK` (por defecto
`/home/andreschirinos/Proyectos/datamesh-sdk/bindings/python`).

## Data Dictionary & Semantic Anchors

Cada fuente usa `name` = ruta relativa del crudo, `url` = enlace Wayback, de IA
o original, `hash` = `sha256:…`, `format` = extensión y `description` = URL original.

## Methodology, Scope & Biases

* Idempotente: reemplaza los recursos `familia_*` y conserva el resto.
* Las fuentes salen de lo realmente usado (`archivo` en `datos.csv`), no del catálogo.
* Estado actual: 32 recursos, 1.144 fuentes crudas con respaldo permanente,
  grafo de 1.211 nodos y 2.290 aristas.

