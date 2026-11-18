#!/usr/bin/env python3
"""Registra el linaje RAW → limpio en ``datapackage.json`` y lo valida con datamesh-sdk.

Por cada familia en ``data/familias/<familia>/datos.csv`` añade un recurso
``familia_<familia>`` al datapackage con:

* ``lineage.sources``: un documento crudo por archivo realmente usado (columna
  ``archivo`` de ``datos.csv``), con su SHA-256 y el enlace a la captura en la
  Wayback Machine (``archivo.csv``, etapa 05) o, si falta, la URL original.
* ``lineage.transformations``: ``bcb_families.py`` y ``bcb_tidy_families.py``
  con el hash de cada script.

Luego construye el grafo con ``datamesh`` (``dm.lineage``) y comprueba que cada
recurso limpio tenga origen aguas arriba. Es idempotente.

    python3 bcb_lineage.py
    python3 bcb_lineage.py --mermaid linaje.mmd
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
from pathlib import Path

import pandas as pd

KNOWLEDGE = Path(__file__).resolve().parents[3]
SCRIPTS = Path(__file__).resolve().parents[1]
_SDK = Path(os.environ.get("DATAMESH_SDK", "/home/andreschirinos/Proyectos/datamesh-sdk/bindings/python"))
if _SDK.exists():
    sys.path.insert(0, str(_SDK))

PREFIX = "familia_"
STEPS = [
    ("bcb_families.py", "03_familias", "Clasifica el corpus en familias tabulares y genera el catálogo."),
    ("bcb_tidy_families.py", "04_tidy", "Aplana cada hoja a un panel tidy (long/wide/category) con unpivotr."),
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def build_resource(fam_dir: Path, manifest: dict[str, dict], archive: dict[str, str], pkg_root: Path) -> dict:
    datos = fam_dir / "datos.csv"
    frame = pd.read_csv(datos, dtype=str, usecols=["archivo", "serie_id"])
    sources = []
    for relpath in sorted(frame["archivo"].dropna().unique()):
        row = manifest.get(relpath, {})
        original = row.get("url", "")
        sources.append({
            "name": relpath,
            "url": archive.get(original) or original,
            "format": Path(relpath).suffix.lstrip(".").lower(),
            "hash": f"sha256:{row['sha256']}" if row.get("sha256") else None,
            "description": f"Original: {original}" if original else None,
        })
    sources = [{k: v for k, v in s.items() if v} for s in sources]
    transformations = [
        {
            "tool": name,
            "type": "python",
            "hash": f"sha256:{sha256_file(SCRIPTS / folder / name)}",
            "description": desc,
            "params": {"familia": fam_dir.name},
        }
        for name, folder, desc in STEPS
    ]
    return {
        "name": PREFIX + fam_dir.name,
        "path": datos.relative_to(pkg_root).as_posix(),
        "format": "csv",
        "mediatype": "text/csv",
        "bytes": datos.stat().st_size,
        "hash": f"sha256:{sha256_file(datos)}",
        "rows": len(frame),
        "series": int(frame["serie_id"].nunique()),
        "lineage": {"sources": sources, "transformations": transformations},
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--package", type=Path, default=KNOWLEDGE / "datapackage.json")
    ap.add_argument("--docs", type=Path, default=KNOWLEDGE / "data" / "documentos")
    ap.add_argument("--familias", type=Path, default=KNOWLEDGE / "data" / "familias")
    ap.add_argument("--mermaid", type=Path, default=None, help="Escribe el grafo en Mermaid")
    args = ap.parse_args()

    manifest = {r["relpath"]: r for r in read_csv(args.docs / "manifiesto.csv")}
    archive = {r["url"]: r["archive_url"] for r in read_csv(args.docs / "archivo.csv") if r["status"] == "archivado"}
    pkg = json.loads(args.package.read_text(encoding="utf-8"))
    root = args.package.parent

    resources = [build_resource(d.parent, manifest, archive, root) for d in sorted(args.familias.glob("*/datos.csv"))]
    pkg["resources"] = [r for r in pkg["resources"] if not r["name"].startswith(PREFIX)] + resources
    args.package.write_text(json.dumps(pkg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    archived = sum(
        1
        for r in resources
        for s in r["lineage"]["sources"]
        if "web.archive.org" in s.get("url", "") or "archive.org/download/" in s.get("url", "")
    )
    total = sum(len(r["lineage"]["sources"]) for r in resources)
    print(f"{len(resources)} recursos | {total} fuentes crudas | {archived} con respaldo")

    from datamesh.usecases.dataset_lineage import DatasetLineageUseCase

    graph = DatasetLineageUseCase().build_graph(search_dirs=[str(root)])
    missing = [r["name"] for r in resources if not graph.upstream(f"{pkg['name']}:{r['name']}")
               and not graph.upstream(r["name"])]
    print(f"grafo: {len(graph.nodes)} nodos, {len(graph.edges)} aristas")
    if missing:
        print("sin origen aguas arriba:", ", ".join(missing))
    if args.mermaid:
        args.mermaid.write_text(graph.to_mermaid(), encoding="utf-8")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
