---
type: Software Pipeline
title: bcb_archive.py — archivo de crudos en la Wayback Machine
description: Pide a Save Page Now una captura de cada documento crudo del manifiesto y registra el enlace permanente como procedencia.
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

# bcb_archive.py — archivo de crudos en la Wayback Machine

## Description & Domain Context

Etapa 05. Lee `manifiesto.csv` y por cada archivo `descargado` obtiene una captura
de su URL original en la Wayback Machine (reutiliza una existente vía la API
`available` o solicita una nueva con Save Page Now). Escribe `archivo.csv` con el
enlace `https://web.archive.org/web/<timestamp>/<url>`. Así el repositorio solo
conserva datos limpios y cada uno remite a su crudo mediante
`bcb_lineage.py`.

* Script: [scripts/05_archivo/bcb_archive.py](scripts/05_archivo/bcb_archive.py)
* SHA-256: `sha256:960d63268f81d1a279a4ccb7932761b4ec8001352f0719917aa5ebb3e17b6981`
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
| `archive_url` | Enlace permanente a la captura. |
| `snapshot` | Timestamp Wayback `AAAAMMDDhhmmss`. |
| `status` | `archivado`, `hash_distinto`, `fallo` o `error: …`. |
| `archived_at` | Momento de la captura (UTC). |

## Methodology, Scope & Biases

* Reanudable: solo reintenta lo que no tiene `status = archivado`.
* Wayback puede capturar una versión distinta si el BCB reemplazó el archivo;
  `--verify` lo detecta con `hash_distinto`.
* Sin red o sin cuota el estado queda `fallo`/`error` y el linaje cae a la URL original.

