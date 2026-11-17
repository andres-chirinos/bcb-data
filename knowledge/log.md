# Historial de Actualizaciones

## 2026-11-16
* **Creación**: Se generó el bundle OKF v0.2 `bcb_estadisticas_semanales` con 10 sectores, 86 variables y 144 series.
* **Descarga**: Se extrajeron 469 períodos (31/12/1987 → 6/11/2026) mediante `action=series` y 430 filas de KPI mediante `action=kpis`.
* **Normalización**: Se publicaron [series_long.csv](data/series_long.csv), [series_wide.csv](data/series_wide.csv) y [kpis_long.csv](data/kpis_long.csv).
* **Limpieza**: Se eliminaron los archivos HAR utilizados durante el descubrimiento inicial del API.
* **Autenticación**: El token `X-BCB-Token` ahora se obtiene con `requests` y `beautifulsoup4` desde `index.php`.
* **Documentación**: Se añadieron el [dataset](datasets/estadisticas_semanales_bcb.md), el [API](api/bcb_estadisticas_api.md), el [pipeline](pipeline/bcb_scraper.md), los [sectores](sectors/index.md) y las [referencias](references/index.md).
* **Catálogo documental**: Se clasificaron 1.345 archivos en 32 familias; 1.266 quedaron procesables, con 7 formularios y 71 ODS duplicados excluidos. Se publicó [familias_catalogo.csv](data/familias_catalogo.csv) y su [dataset](datasets/familias_documentos_bcb.md).
* **Normalización por familias**: Se añadieron [bcb_families.py](pipeline/bcb_families.md) y [bcb_tidy_families.py](pipeline/bcb_tidy_families.md), con detección de layouts `long`, `wide` y `category`, caché de conversión y salidas tidy por familia.
