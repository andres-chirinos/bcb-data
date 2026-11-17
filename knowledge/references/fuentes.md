---
type: Reference
title: Fuentes y procedencia
description: Origen de los datos, fecha de actualización y condiciones de reutilización.
tags:
- fuentes
- procedencia
- licencia
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

# Fuentes y procedencia

## Fuente primaria

* **Panel:** [Estadísticas Semanales del BCB](https://www.bcb.gob.bo/bcb_estadisticas/index.php)
* **API:** [`api.php?v=4.0.5`](https://www.bcb.gob.bo/bcb_estadisticas/api.php?v=4.0.5)
* **Entidad:** [Banco Central de Bolivia](https://www.bcb.gob.bo/)
* **Última actualización declarada por el BCB:** 6/11/2026
* **Extracción:** 2026-11-16T20:42:27-04:00

## Cadena de procedencia

1. `index.php` entrega el token y la cookie de sesión.
2. `action=metadata` descubre 10 sectores, 86 variables y
   144 series, con 469 períodos.
3. Una petición `action=series` por serie (una variable y una denominación).
4. Peticiones `action=kpis` por sector y combinación válida de corte/variación.
5. El pipeline normaliza a CSV y conserva las respuestas crudas en `raw/`.

## Licencia

El bundle declara `NOASSERTION`. Los datos pertenecen al BCB y su reutilización
debe regirse por los términos publicados en el portal. Este bundle no reclama
titularidad sobre las cifras originales; solo documenta su extracción y
normalización.

## Cita sugerida

> Banco Central de Bolivia. *Estadísticas Semanales*. Panel
> `bcb_estadisticas`, actualizado al 6/11/2026.
> Extraído y normalizado en el bundle `bcb_estadisticas_semanales`.
