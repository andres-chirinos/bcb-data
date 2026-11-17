#!/usr/bin/env python3
"""Archiva en la Wayback Machine los documentos crudos del BCB.

Lee ``manifiesto.csv`` (etapa 02) y, por cada archivo descargado, pide a Save
Page Now de web.archive.org una captura de su URL original. Escribe
``archivo.csv`` junto al manifiesto con el enlace permanente al RAW
(``https://web.archive.org/web/<timestamp>/<url>``) y el SHA-256 local, para que
la etapa 06 (linaje) cite el crudo y el repositorio conserve solo datos limpios.

Es reanudable: las URLs ya archivadas se omiten. Credenciales opcionales
(``IA_ACCESS_KEY`` / ``IA_SECRET_KEY``, de https://archive.org/account/s3.php)
suben el límite de peticiones.

    python3 bcb_archive.py --dry-run
    python3 bcb_archive.py --limit 5 --verify
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

DATA = Path(__file__).resolve().parents[3] / "data"
SAVE = "https://web.archive.org/save/"
AVAILABLE = "https://archive.org/wayback/available"
FIELDS = ["url", "relpath", "sha256", "archive_url", "snapshot", "status", "archived_at"]


def load_env(start: Path) -> None:
    """Carga el primer ``.env`` hallado desde ``start`` hacia arriba (sin pisar el entorno)."""
    for folder in [start, *start.parents]:
        env = folder / ".env"
        if env.is_file():
            for line in env.read_text(encoding="utf-8").splitlines():
                key, sep, value = line.partition("=")
                if sep and not line.lstrip().startswith("#"):
                    os.environ.setdefault(key.strip(), value.strip().strip("\"'"))
            return


def read_manifest(docs: Path) -> list[dict[str, str]]:
    with (docs / "manifiesto.csv").open(encoding="utf-8", newline="") as fh:
        return [r for r in csv.DictReader(fh) if r.get("status") == "descargado"]


def read_done(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8", newline="") as fh:
        return {r["url"]: r for r in csv.DictReader(fh) if r["status"] == "archivado"}


def existing_snapshot(session: requests.Session, url: str) -> str | None:
    try:
        r = session.get(AVAILABLE, params={"url": url}, timeout=30)
        snap = r.json().get("archived_snapshots", {}).get("closest")
        return snap["url"].replace("http://", "https://") if snap and snap.get("available") else None
    except (requests.RequestException, ValueError):
        return None


def save(session: requests.Session, url: str, timeout: float) -> str | None:
    r = session.get(SAVE + url, timeout=timeout, allow_redirects=True)
    location = r.headers.get("Content-Location", "")
    if location.startswith("/web/"):
        return "https://web.archive.org" + location
    if r.ok and "/web/" in r.url and "/save/" not in r.url:
        return r.url
    return None


def snapshot_matches(session: requests.Session, archive_url: str, sha256: str) -> bool:
    """Descarga el crudo archivado (``id_``) y compara su SHA-256 con el local."""
    stamp, _, original = archive_url.partition("/web/")[2].partition("/")
    raw = f"https://web.archive.org/web/{stamp}id_/{original}"
    digest = hashlib.sha256()
    with session.get(raw, timeout=120, stream=True) as r:
        if not r.ok:
            return False
        for chunk in r.iter_content(65536):
            digest.update(chunk)
    return digest.hexdigest() == sha256


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--docs", type=Path, default=DATA / "documentos")
    ap.add_argument("--out", type=Path, default=None, help="Por defecto <docs>/archivo.csv")
    ap.add_argument("--delay", type=float, default=6.0, help="Segundos entre capturas")
    ap.add_argument("--timeout", type=float, default=180.0)
    ap.add_argument("--limit", type=int, default=0, help="Máximo de archivos por corrida (0 = todos)")
    ap.add_argument("--force", action="store_true", help="Pide captura nueva aunque exista una")
    ap.add_argument("--verify", action="store_true", help="Compara el SHA-256 del crudo archivado")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    load_env(Path.cwd())
    out = args.out or args.docs / "archivo.csv"
    rows = read_manifest(args.docs)
    done = read_done(out)
    pending = [r for r in rows if r["url"] not in done]
    if args.limit:
        pending = pending[: args.limit]
    print(f"manifiesto: {len(rows)} | archivados: {len(done)} | pendientes: {len(pending)}")
    if args.dry_run:
        for r in pending[:10]:
            print("  -", r["url"])
        return 0

    session = requests.Session()
    session.headers["User-Agent"] = "bcb-data-archiver/1.0 (+https://github.com/datosbolivia)"
    if os.environ.get("IA_ACCESS_KEY") and os.environ.get("IA_SECRET_KEY"):
        session.headers["Authorization"] = f"LOW {os.environ['IA_ACCESS_KEY']}:{os.environ['IA_SECRET_KEY']}"

    new = not out.exists()
    with out.open("a", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        if new:
            writer.writeheader()
        for i, r in enumerate(pending, 1):
            url = r["url"]
            snap = None if args.force else existing_snapshot(session, url)
            status = "archivado"
            try:
                snap = snap or save(session, url, args.timeout)
                if not snap:
                    status = "fallo"
                elif args.verify and not snapshot_matches(session, snap, r["sha256"]):
                    # La captura previa puede ser de otra versión: pide una nueva y reverifica.
                    fresh = save(session, url, args.timeout)
                    snap = fresh or snap
                    if not (fresh and snapshot_matches(session, fresh, r["sha256"])):
                        status = "hash_distinto"
            except requests.RequestException as exc:
                snap, status = None, f"error: {type(exc).__name__}"
            writer.writerow({
                "url": url,
                "relpath": r["relpath"],
                "sha256": r["sha256"],
                "archive_url": snap or "",
                "snapshot": snap.split("/web/")[1].split("/")[0] if snap else "",
                "status": status,
                "archived_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            })
            fh.flush()
            print(f"[{i}/{len(pending)}] {status} {url}")
            time.sleep(args.delay)
    return 0


if __name__ == "__main__":
    sys.exit(main())
