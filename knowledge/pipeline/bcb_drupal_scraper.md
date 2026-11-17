---
type: Software Pipeline
title: bcb_drupal_scraper.py — descarga de documentos crudos
description: Rastrea el sitio Drupal del BCB respetando robots.txt, descubre hojas de cálculo y las descarga con un manifiesto SHA-256.
tags:
- python
- scraping
- bcb
- raw
generated:
  by: process:bcb_drupal_scraper.py/1.0
  at: '2026-11-17T00:05:00-04:00'
verified:
- by: process:bcb_drupal_scraper.py/1.0
  at: '2026-11-17T00:05:00-04:00'
status: stable
stale_after: '2027-06-30T00:00:00Z'
sources:
- id: portal-bcb
  resource: https://www.bcb.gob.bo/
  title: Portal del Banco Central de Bolivia
  author: Banco Central de Bolivia
  last_modified: '2026-11-16T00:00:00Z'
resource: scripts/02_documentos/bcb_drupal_scraper.py
executor:
  resource: scripts/02_documentos/bcb_drupal_scraper.py
attester:
  resource: scripts/02_documentos/bcb_drupal_scraper.py
---

# bcb_drupal_scraper.py — descarga de documentos crudos

## Description & Domain Context

Etapa 02 del flujo. Navega `www.bcb.gob.bo` (HTML y `sitemap`), encuentra enlaces a
`.xls`, `.xlsx`, `.xlsm`, `.xlsb`, `.ods` y `.csv`, y los guarda preservando la
ruta del sitio. Cada descarga queda en `manifiesto.csv`/`manifiesto.jsonl` con URL,
tamaño y SHA-256; ese manifiesto es la entrada de
[bcb_families.py](bcb_families.md) y de [bcb_archive.py](bcb_archive.md).

* Script: [scripts/02_documentos/bcb_drupal_scraper.py](scripts/02_documentos/bcb_drupal_scraper.py)
* SHA-256: `sha256:5dafeac871cf42f628a56de5044711e6e297760c2cbaf91fde7cee4b62364190`
* Dependencias: [scripts/02_documentos/requirements.txt](scripts/02_documentos/requirements.txt)
* Salida: `knowledge/data/documentos/` (`manifiesto.csv`, `manifiesto.jsonl`, `resumen.json`, `crawl.log`, `webdocs/…`)

## Operational Interaction & Example Queries

```bash
pip install -r knowledge/pipeline/scripts/02_documentos/requirements.txt

# Descubrir sin descargar
python3 knowledge/pipeline/scripts/02_documentos/bcb_drupal_scraper.py --dry-run

# Rastreo acotado
python3 knowledge/pipeline/scripts/02_documentos/bcb_drupal_scraper.py --max-pages 200 --max-files 100

# Descargar URLs ya conocidas
python3 knowledge/pipeline/scripts/02_documentos/bcb_drupal_scraper.py --from-candidates knowledge/data/documentos/candidatos.csv
```

| Opción | Efecto |
| :--- | :--- |
| `--outdir` | Salida (por defecto `knowledge/data/documentos`). |
| `--seed` | URL semilla repetible; reemplaza las semillas por defecto. |
| `--max-depth`, `--max-pages`, `--max-files` | Límites del rastreo (4, 1000, 2000). |
| `--delay`, `--timeout`, `--retries` | Cortesía y robustez de red. |
| `--dry-run` | Lista hojas sin descargarlas. |
| `--force` | Vuelve a descargar archivos ya registrados. |
| `--ignore-robots` | No respeta `robots.txt`; usar con precaución. |
| `--allow-external-docs` | Acepta hojas de subdominios `*.bcb.gob.bo`. |
| `--from-candidates` | Descarga desde un `candidatos.csv` sin rastrear. |

## Data Dictionary & Semantic Anchors

`manifiesto.csv`: `url`, `final_url`, `filename`, `relpath`, `size_bytes`,
`sha256`, `content_type`, `source_page`, `source_title`, `link_text`, `node_id`,
`downloaded_at`, `status`.

## Methodology, Scope & Biases

* Solo descarga del dominio del BCB (y subdominios con `--allow-external-docs`).
* Reanudable: omite archivos ya registrados salvo `--force`.
* Los crudos no se versionan: se archivan con [bcb_archive.py](bcb_archive.md) y el
  datapackage los cita desde [bcb_lineage.py](bcb_lineage.md).

