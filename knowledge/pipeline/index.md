# Pipeline

Automatización reproducible de la descarga y normalización.

## Conceptos

* [bcb_scraper.py: token con requests/BeautifulSoup, plan completo, salidas y opciones CLI.](bcb_scraper.md)
* [bcb_drupal_scraper.py: rastreo del sitio Drupal y descarga de hojas de cálculo crudas con manifiesto.](bcb_drupal_scraper.md)
* [bcb_archive.py: captura o respalda cada crudo en archive.org para citarlo como procedencia.](bcb_archive.md)
* [bcb_lineage.py: linaje RAW → limpio en el datapackage, validado con datamesh-sdk.](bcb_lineage.md)
* [bcb_families.py: clasificación del corpus documental en familias y catálogo de entrada.](bcb_families.md)
* [bcb_tidy_families.py: extracción de hojas a un panel tidy por familia con unpivotr.](bcb_tidy_families.md)
