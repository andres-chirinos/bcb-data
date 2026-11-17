---
type: API Endpoint
title: API JSON de Estadísticas Semanales del BCB
description: Endpoint POST que entrega metadata, series y KPI del panel del BCB.
tags:
- bcb
- api
- json
- scraping
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
resource: https://www.bcb.gob.bo/bcb_estadisticas/api.php?v=4.0.5
---

# API JSON de Estadísticas Semanales del BCB

## Description & Domain Context

El panel `bcb_estadisticas` consume un único endpoint JSON. El scraper lo usa
para descubrir y descargar todo el catálogo sin depender de capturas de red (HAR).

* **URL:** `https://www.bcb.gob.bo/bcb_estadisticas/api.php?v=4.0.5`
* **Método:** `POST`
* **Content-Type:** `application/json`
* **Respuesta:** JSON con `ok: true` o `ok: false` + `error`/`message`.

## Autenticación

Cada carga de `index.php` genera un token y una cookie de sesión. Ambos deben
usarse juntos; el token por sí solo devuelve `invalid_token`. El pipeline lo
obtiene con `requests` y `beautifulsoup4`:

```python
import requests
from bs4 import BeautifulSoup

INDEX_URL = "https://www.bcb.gob.bo/bcb_estadisticas/index.php"
API_URL = "https://www.bcb.gob.bo/bcb_estadisticas/api.php?v=4.0.5"

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0", "Referer": INDEX_URL})
html = session.get(INDEX_URL, timeout=60).text
meta = BeautifulSoup(html, "html.parser").find(
    "meta", attrs={"name": "bcb-api-token"}
)
token = meta["content"]

response = session.post(
    API_URL,
    json={"action": "metadata"},
    headers={"X-BCB-Token": token},
    timeout=60,
)
print(response.json()["conteos"])
```

También puede fijarse `BCB_API_TOKEN` en el entorno o pasarse `--token` al
scraper para reutilizar un token vigente. Ver
[pipeline](../pipeline/bcb_scraper.md).

## Acciones

### `metadata`

Descubre sectores, variables, denominaciones y fechas disponibles.

```json
{"action": "metadata"}
```

Respuesta (abreviada):

```json
{
  "ok": true,
  "meses": ["31/12/1987", "31/12/1988", "..."],
  "series": {
    "Banca Central": {
      "Base Monetaria": ["Total"],
      "Reservas bancarias": ["MN", "ME", "MVDOL", "UFV", "Total"]
    }
  },
  "actualizado": "6/11/2026",
  "conteos": {"temas": 10, "series": 144}
}
```

### `series`

Descarga una o más variables de un sector para una denominación y rango.

```json
{
  "action": "series",
  "sector": "Banca Central",
  "variables": ["Base Monetaria"],
  "moneda": "Total",
  "desde": "31/12/1987",
  "hasta": "6/11/2026"
}
```

Respuesta:

```json
{
  "ok": true,
  "meses": ["31/12/1987", "31/12/1988", "..."],
  "series": {
    "Base Monetaria": {"Total": [584.827413, 930.793738, "..."]}
  }
}
```

**Límites observados:** entre 1 y 5 variables por petición, y solo
combinaciones predefinidas por el panel. El pipeline solicita **una variable
por petición** para evitar el error
`La combinación de variables no está permitida.`

### `kpis`

Entrega indicadores de coyuntura de un sector.

```json
{
  "action": "kpis",
  "sector": "Banca Central",
  "corte": "diario",
  "variacion": "acumulada"
}
```

* `corte`: `mensual`, `semanal`, `diario`.
* `variacion`: `mensual`, `interanual`, `acumulada`.
* `semanal` y `diario` solo admiten `acumulada`.

Respuesta (abreviada):

```json
{
  "ok": true,
  "fecha": "6/11/2026",
  "items": [
    {"variable": "Base Monetaria", "valor": 153156.92, "fecha": "6/11/2026", "anterior": 150581.90}
  ]
}
```

## Errores y recomendaciones

| Señal | Causa | Acción |
| :--- | :--- | :--- |
| `invalid_token` | Token vencido o cookie ausente | Volver a cargar `index.php` y renovar ambos. |
| `La combinación de variables no está permitida.` | Variables de grupos distintos o más de 5 | Pedir una variable por vez. |
| `Debe solicitar entre una y cinco variables.` | Lista vacía o demasiado grande | Ajustar el lote. |
| HTTP 429/5xx | Límite o fallo transitorio | Backoff exponencial y reintentos. |

El scraper usa `--delay 0.35` por defecto, reintenta con backoff y renueva la
sesión automáticamente ante `invalid_token`.
