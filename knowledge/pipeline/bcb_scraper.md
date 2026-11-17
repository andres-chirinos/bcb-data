---
type: Software Pipeline
title: bcb_scraper.py — pipeline de extracción
description: Script Python que descarga todo el catálogo del BCB y genera CSV tabulares.
tags:
- python
- scraping
- etl
- reproducibilidad
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
resource: scripts/01_api/bcb_scraper.py
executor:
  resource: scripts/01_api/bcb_scraper.py
attester:
  resource: scripts/01_api/bcb_scraper.py
---

# bcb_scraper.py — pipeline de extracción

## Description & Domain Context

Script autocontenido (más `requests` y `beautifulsoup4`) que:

1. abre una `requests.Session` contra `index.php`,
2. extrae el token `bcb-api-token` del HTML con `BeautifulSoup`,
3. solicita `metadata` y construye el plan completo,
4. descarga cada serie y cada KPI,
5. escribe respuestas crudas y CSV normalizados.

* Script: [scripts/01_api/bcb_scraper.py](scripts/01_api/bcb_scraper.py)
* Dependencias: [scripts/01_api/requirements.txt](scripts/01_api/requirements.txt)
* SHA-256: `sha256:59f3881dd16b4c1ee29e1abe27c5abec3477f0660bf4683fe83c020ad5609a45`

## Operational Interaction & Example Queries

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Descarga completa en ./datos-bcb
python3 knowledge/pipeline/scripts/01_api/bcb_scraper.py

# Ver el plan sin descargar
python3 knowledge/pipeline/scripts/01_api/bcb_scraper.py --dry-run

# Un solo sector y reanudar lo ya descargado
python3 knowledge/pipeline/scripts/01_api/bcb_scraper.py --sector "Sector Externo" --resume
```

| Opción | Efecto |
| :--- | :--- |
| `--outdir` | Directorio de salida (por defecto `datos-bcb`). |
| `--dry-run` | Imprime el plan y termina. |
| `--resume` | Reutiliza respuestas crudas existentes. |
| `--sector` | Limita a uno o más sectores (repetible). |
| `--desde` / `--hasta` | Sobrescribe el rango `dd/mm/aaaa`. |
| `--delay` | Pausa entre peticiones (por defecto 0.35 s). |
| `--timeout` / `--retries` | Timeout HTTP y reintentos. |
| `--token` | Token explícito; si se omite usa `BCB_API_TOKEN` o `index.php`. |
| `--quiet` | Reduce la salida por consola. |

## Salidas

| Ruta | Contenido |
| :--- | :--- |
| `series_long.csv` | Formato largo canónico. |
| `series_wide.csv` | Matriz fecha × serie. |
| `kpis_long.csv` | Indicadores de coyuntura. |
| `csv/<sector>.csv` | Matriz ancha por sector. |
| `raw/metadata/*.json` | Respuesta de metadata. |
| `raw/series/*.json` | Envoltorio `{request, response}` por serie. |
| `raw/kpis/*.json` | Envoltorio por consulta de KPI. |
| `manifest.json` | Conteos, hashes de archivos, errores y procedencia. |

## Methodology, Scope & Biases

* **Una variable por petición:** obligatorio por las restricciones del API.
* **Idempotencia:** los nombres de archivo crudos derivan de un hash del
  payload; `--resume` los reutiliza.
* **Tolerancia a fallos:** backoff exponencial para HTTP 429/5xx y renovación
  automática de token ante `invalid_token`.
* **Sin HAR:** el pipeline ya no requiere capturas de red; todo se descubre
  desde `metadata`.
* **Fotografía, no incremental:** cada ejecución sobrescribe los CSV.
