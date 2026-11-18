---
type: Software Pipeline
title: bcb_archive.py — archivo y respaldo de crudos
description: Captura cada documento crudo en Wayback o lo respalda en archive.org y registra el enlace permanente como procedencia.
tags:
- python
- wayback
- procedencia
- bcb
generated:
  by: process:bcb_archive.py/1.0
  at: '2026-11-17T00:05:00-04:00'
verified:
- by: process:bcb_archive.py/1.0
  at: '2026-11-17T00:05:00-04:00'
status: stable
stale_after: '2027-06-30T00:00:00Z'
sources:
- id: wayback
  resource: https://web.archive.org/
  title: Internet Archive — Wayback Machine
  author: Banco Central de Bolivia
  last_modified: '2026-11-16T00:00:00Z'
- id: ia-respaldo
  resource: https://archive.org/details/bcb-documentos-respaldo-20261118
  title: Internet Archive — respaldo de crudos BCB
  author: bcb-data
  last_modified: '2026-11-18T00:00:00Z'
- id: portal-bcb
  resource: https://www.bcb.gob.bo/
  title: Portal del Banco Central de Bolivia
  author: Banco Central de Bolivia
  last_modified: '2026-11-16T00:00:00Z'
resource: scripts/05_archivo/bcb_archive.py
executor:
  resource: scripts/05_archivo/bcb_archive.py
attester:
  resource: scripts/05_archivo/bcb_archive.py
---

# bcb_archive.py — archivo y respaldo de crudos

## Description & Domain Context

Etapa 05. Lee `manifiesto.csv` y por cada archivo `descargado` obtiene una captura
de su URL original en la Wayback Machine (reutiliza una existente vía la API
`available` o solicita una nueva con Save Page Now). Los crudos que Wayback no
logra capturar se respaldan en el ítem público `bcb-documentos-respaldo-20261118`
de archive.org. Así el repositorio solo conserva datos limpios y cada uno remite
a su crudo mediante `bcb_lineage.py`.

* Script: [scripts/05_archivo/bcb_archive.py](scripts/05_archivo/bcb_archive.py)
* SHA-256: `sha256:ec128e97f9d4092189be112864d5cdea2acad9e1316f168095a32fb508bec6d0`
* Dependencias: [scripts/05_archivo/requirements.txt](scripts/05_archivo/requirements.txt)
* Salida: `knowledge/data/documentos/archivo.csv`

## Operational Interaction & Example Queries

```bash
pip install -r knowledge/pipeline/scripts/05_archivo/requirements.txt

python3 knowledge/pipeline/scripts/05_archivo/bcb_archive.py --dry-run
python3 knowledge/pipeline/scripts/05_archivo/bcb_archive.py --limit 5 --verify

# Opcional: credenciales S3 de archive.org para un límite de peticiones mayor
export IA_ACCESS_KEY=… IA_SECRET_KEY=…
python3 knowledge/pipeline/scripts/05_archivo/bcb_archive.py
```

| Opción | Efecto |
| :--- | :--- |
| `--docs` | Directorio con `manifiesto.csv` (por defecto `knowledge/data/documentos`). |
| `--out` | Ruta de `archivo.csv`. |
| `--delay` | Segundos entre capturas (6). |
| `--limit` | Máximo de archivos por corrida. |
| `--force` | Pide captura nueva aunque exista una. |
| `--verify` | Descarga el crudo archivado (`id_`) y compara su SHA-256 con el local. |
| `--dry-run` | Lista pendientes sin tocar la red. |

## Data Dictionary & Semantic Anchors

| Columna | Descripción |
| :--- | :--- |
| `url` | URL original en bcb.gob.bo. |
| `relpath` | Ruta relativa dentro de `data/documentos/`. |
| `sha256` | Hash del archivo descargado. |
| `archive_url` | Enlace permanente a la captura Wayback o al archivo respaldado en IA. |
| `snapshot` | Timestamp Wayback `AAAAMMDDhhmmss`; vacío para respaldos de IA. |
| `status` | `archivado`, `hash_distinto`, `fallo` o `error: …`. |
| `archived_at` | Momento de la captura (UTC). |

## Methodology, Scope & Biases

* Reanudable: solo reintenta lo que no tiene `status = archivado`.
* Wayback puede capturar una versión distinta si el BCB reemplazó el archivo;
  `--verify` lo detecta con `hash_distinto`.
* Sin red o sin cuota el estado queda `fallo`/`error` y el linaje cae a la URL original.
* Estado actual: 1.345 filas en `archivo.csv` para las 1.345 URLs únicas del
  manifiesto, todas `archivado`: 1.232 capturas Wayback y 113 respaldos en el
  ítem público `bcb-documentos-respaldo-20261118`, verificados por SHA-256. Las
  1.144 fuentes usadas por las familias limpias tienen enlace permanente. El
  script es reanudable, por lo que una nueva corrida procesa sólo los
  pendientes.

