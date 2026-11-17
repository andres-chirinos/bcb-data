---
type: Software Pipeline
title: bcb_tidy_families.py — normalización de familias BCB
description: Extrae y normaliza hojas de cálculo del BCB a un esquema tidy por familia usando unpivotr, con detección de layouts long, wide y category.
tags:
- python
- etl
- unpivotr
- tidy-data
- bcb
generated:
  by: process:bcb_tidy_families.py/1.0
  at: '2026-11-16T23:01:50-04:00'
verified:
- by: process:bcb_tidy_families.py/1.0
  at: '2026-11-16T23:01:50-04:00'
status: stable
stale_after: '2027-06-30T00:00:00Z'
sources:
- id: portal-bcb
  resource: https://www.bcb.gob.bo/
  title: Portal del Banco Central de Bolivia
  author: Banco Central de Bolivia
  last_modified: '2026-11-16T00:00:00Z'
resource: scripts/04_tidy/bcb_tidy_families.py
executor:
  resource: scripts/04_tidy/bcb_tidy_families.py
attester:
  resource: scripts/04_tidy/bcb_tidy_families.py
---

# bcb_tidy_families.py — normalización de familias BCB

## Description & Domain Context

Este pipeline toma el catálogo generado por `bcb_families.py`, abre cada archivo procesable con
`WorkbookGrid` de `unpivotr`, detecta el layout de cada hoja y produce un
panel tidy. Los XLS, XLSB y ODS se convierten primero a XLSX con LibreOffice
(`soffice`) en una caché local.

* Script: [scripts/04_tidy/bcb_tidy_families.py](scripts/04_tidy/bcb_tidy_families.py)
* Dependencias: [requirements-familias.txt](scripts/04_tidy/requirements-familias.txt)
  (`pandas`, `openpyxl`, `xlrd`, `odfpy`) y el clon local de `unpivotr`
  apuntado por `UNPIVOTR_SRC` (por defecto
  `/home/andreschirinos/Proyectos/unpivotr-clone/src`).
* SHA-256: `sha256:47d15cfc4b6369abfe6964ea637fa92ba78247840134c90ee287cef76bf568a8`

## Operational Interaction & Example Queries

```bash
# Prueba con dos archivos por familia
python3 knowledge/pipeline/scripts/04_tidy/bcb_tidy_families.py \
  --out /tmp/bcb-prueba \
  --max-archivos 2

# Una familia concreta, sin reconvertir archivos
python3 knowledge/pipeline/scripts/04_tidy/bcb_tidy_families.py \
  --familias tasas_diarias \
  --out knowledge/data/familias \
  --sin-conversion

# Reanudar y forzar reprocesamiento de una familia
python3 knowledge/pipeline/scripts/04_tidy/bcb_tidy_families.py --out knowledge/data/familias --force --familias boletin_estadistico
```

| Opción | Efecto |
| :--- | :--- |
| `--docs` | Corpus descargado (por defecto `documentos-bcb`). |
| `--catalogo` | Catálogo CSV de entrada. |
| `--out` | Directorio raíz de salida. |
| `--familias` | Lista separada por comas; vacío significa todas. |
| `--excluir-familias` | Familias a omitir. |
| `--max-archivos` | Límite de archivos por familia; útil para pruebas. |
| `--min-valores` | Mínimo de filas para aceptar una hoja (por defecto 8). |
| `--cache` | Directorio de XLSX convertidos. |
| `--sin-conversion` | No convierte XLS/XLSB/ODS. |
| `--no-resume` | Ignora salidas previas. |
| `--force` | Borra la salida de la familia antes de procesar. |
| `--guardar-partes` | Guarda un CSV por archivo/hoja en `partes/`. |
| `--reclasificar` | Recalcula el catálogo antes de procesar. |
| `--dry-run` | Muestra el plan sin extraer datos. |
| `--verbose` | Registra cada hoja procesada. |

## Estrategia de extracción

1. **`long`**: una fila por período; detecta columnas de fecha/año y etiquetas
   laterales. Es el modo de `tasas_referencia`, `boletin_estadistico` o
   `30 DC S`.
2. **`wide`**: los períodos están en los encabezados de columna y las series
   en las filas. Es el modo de `estadisticas_semanales`, `sector_externo` y
   varios balances.
3. **`category`**: tablas de corte transversal sin fecha por fila; usan la
   fecha de publicación como período. Es el modo de `posicion_inversion_internacional`
   y de varios cuadros de comercio.

El detector prefiere `wide` cuando hay una fila con muchos períodos y un
abanico ancho de columnas; en caso contrario prueba `long` y luego `category`.
Los encabezados combinados se leen con `WorkbookGrid` (no en modo `read_only`)
para no perder `merged_ranges`.

## Data Dictionary & Semantic Anchors

Cada familia produce `datos.csv` con este esquema:

| Columna | Descripción |
| :--- | :--- |
| `familia` | Familia asignada por `bcb_families.py`. |
| `archivo` | Ruta relativa del archivo. |
| `hoja` | Hoja de cálculo de origen. |
| `serie_id` | Identificador estable: familia + nombre normalizado de la serie. |
| `serie` | Etiqueta jerárquica legible de la serie. |
| `fecha` | Fecha ISO (`AAAA-MM-DD`) o período normalizado. |
| `periodo` | Período original o etiqueta de la tabla. |
| `valor` | Valor numérico limpio. |
| `unidad` | Unidad detectada o unidad por defecto de la familia. |
| `publicacion` | Fecha de publicación del archivo. |
| `metodo` | `long`, `wide` o `category`. |
| `fila` / `columna` | Coordenadas de la celda de origen. |

Cada familia genera además:

| Ruta | Contenido |
| :--- | :--- |
| `datos.csv` | Panel tidy completo de la familia. |
| `series.csv` | Una fila por `serie_id` con cobertura y número de observaciones. |
| `archivos.csv` | Estado, filas y método por archivo/hoja. |
| `resumen.json` | Conteos de la familia. |

En la raíz de salida se escriben `catalogo_series.csv` y
`resumen_familias_datos.json`. La corrida completa se guarda fuera del bundle,
en `data/familias/`, porque su volumen es mucho mayor que el catálogo.

## Methodology, Scope & Biases

* **Detección heurística:** el layout se infiere por densidad de números,
  períodos y etiquetas. Hojas con varios cuadros apilados o gráficos pueden
  requerir revisión manual.
* **Hojas vacías o de notas:** se omiten mediante `SKIP_SHEET` y el umbral
  `--min-valores`.
* **Duplicados:** la clave `serie_id + fecha` conserva la última publicación;
  esto evita repetir la misma observación entre ediciones del mismo reporte.
* **Unidades:** se buscan leyendas entre paréntesis; si no aparecen, se usan
  valores por defecto para tasas y precios. No debe asumirse que toda la
  familia comparte unidad.
* **Fechas:** se normalizan meses, trimestres, semanas y fechas con texto
  español. Algunas tablas apiladas pueden asignar la fecha de la sección
  anterior a una fila de corte transversal.
* **Cobertura:** no todas las series cubren el mismo rango; use `series.csv`
  para revisar `primera_fecha`, `ultima_fecha` y `n_observaciones`.
* **Calidad:** antes de analizar una familia, revise `archivos.csv` y una
  muestra de `datos.csv`; las hojas `G1/G2` del boletín y los archivos
  históricos de estadísticas semanales son casos conocidos de baja calidad.
