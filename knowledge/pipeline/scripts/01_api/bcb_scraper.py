#!/usr/bin/env python3
"""Scraper completo de las Estadisticas Semanales del Banco Central de Bolivia.

Usa ``requests`` para la sesion HTTP y ``beautifulsoup4`` para extraer el
token ``X-BCB-Token`` del panel, y descarga:

  * metadata (sectores, variables, monedas y rango de fechas disponible),
  * todas las series de cada combinacion (sector, variable, moneda),
  * todos los KPI de cada combinacion valida (sector, corte, variacion).

Guarda las respuestas JSON crudas y genera CSV largos y anchos listos para
analisis. La API solo admite una variable por peticion y requiere una cookie
de sesion ligada al token, por lo que el cliente reutiliza una ``Session``.

Ejemplos:
    python3 bcb_scraper.py                     # descarga todo en vivo
    python3 bcb_scraper.py --dry-run           # muestra el plan sin descargar
    python3 bcb_scraper.py --sector "Sector Externo"
    python3 bcb_scraper.py --resume --delay 0.5

Requisitos:
    pip install -r requirements.txt
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
import time
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.bcb.gob.bo"
API_URL = f"{BASE_URL}/bcb_estadisticas/api.php?v=4.0.5"
INDEX_URL = f"{BASE_URL}/bcb_estadisticas/index.php"
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64; rv:158.0) Gecko/20100101 Firefox/158.0"
)

CORTES = ("mensual", "semanal", "diario")
VARIACIONES = ("mensual", "interanual", "acumulada")
TOKEN_META_NAME = "bcb-api-token"

SERIES_COLUMNS = ("sector", "variable", "moneda", "fecha", "fecha_iso", "valor")
KPI_COLUMNS = (
    "sector",
    "corte",
    "variacion",
    "fecha",
    "fecha_iso",
    "variable",
    "valor",
    "anterior",
    "delta",
)


class ApiError(RuntimeError):
    """Error devuelto por la API del BCB o fallo de red persistente."""


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def log(message: str) -> None:
    print(f"[{datetime.now():%H:%M:%S}] {message}", flush=True)


def slugify(text: Any, maxlen: int = 60) -> str:
    text = "" if text is None else str(text)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^0-9A-Za-z]+", "_", text).strip("_").lower()
    return (text or "sin_nombre")[:maxlen].strip("_") or "sin_nombre"


def canonical(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def parse_fecha(value: Any):
    if not isinstance(value, str):
        return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    return None


def fecha_iso(value: Any) -> str:
    parsed = parse_fecha(value)
    return parsed.isoformat() if parsed else (value if isinstance(value, str) else "")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    tmp.replace(path)


def write_csv(path: Path, columns: Iterable[str], rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = list(columns)
    tmp = path.with_suffix(path.suffix + ".tmp")
    count = 0
    with tmp.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
            count += 1
    tmp.replace(path)
    return count


# ---------------------------------------------------------------------------
# Cliente HTTP (requests + BeautifulSoup)
# ---------------------------------------------------------------------------


class BcbClient:
    def __init__(
        self,
        api_url: str = API_URL,
        index_url: str = INDEX_URL,
        timeout: float = 60.0,
        retries: int = 4,
        delay: float = 0.35,
        token: str | None = None,
        verbose: bool = True,
    ) -> None:
        self.api_url = api_url
        self.index_url = index_url
        self.timeout = timeout
        self.retries = retries
        self.delay = delay
        self.verbose = verbose
        self.token = token or None
        self.token_source = "argumento/env" if self.token else "index.php"
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": USER_AGENT,
                "Accept-Language": "es,en;q=0.9",
                "Referer": self.index_url,
                "Origin": BASE_URL,
            }
        )

    def _log(self, message: str) -> None:
        if self.verbose:
            log(message)

    def refresh_token(self) -> str:
        """Descarga index.php y extrae el token del meta tag con BeautifulSoup."""
        if self.token:
            return self.token
        self._log(f"Obteniendo token desde {self.index_url}")
        try:
            response = self.session.get(self.index_url, timeout=self.timeout)
        except requests.RequestException as exc:
            raise ApiError(f"Fallo de red al abrir index.php: {exc}") from exc
        if response.status_code != 200:
            raise ApiError(f"index.php devolvio HTTP {response.status_code}")

        soup = BeautifulSoup(response.text, "html.parser")
        meta = soup.find("meta", attrs={"name": TOKEN_META_NAME})
        token = (meta.get("content") if meta else None) or None
        if not token:
            raise ApiError(f"No se encontro el meta '{TOKEN_META_NAME}' en index.php")
        self.token = token
        self.token_source = "index.php"
        self._log(f"Sesion iniciada (token {token[:12]}...)")
        return token

    def api(self, payload: dict[str, Any]) -> dict[str, Any]:
        last_error = "error desconocido"
        for attempt in range(1, self.retries + 1):
            token = self.refresh_token()
            headers = {"X-BCB-Token": token, "Content-Type": "application/json"}
            try:
                response = self.session.post(
                    self.api_url,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout,
                )
            except requests.RequestException as exc:
                last_error = f"fallo de red: {exc}"
                wait = min(2**attempt, 20)
                self._log(
                    f"Red inestable; reintentando en {wait}s ({attempt}/{self.retries})"
                )
                time.sleep(wait)
                continue

            try:
                data = response.json()
            except ValueError:
                data = None

            if (
                response.status_code == 200
                and isinstance(data, dict)
                and data.get("ok") is True
            ):
                return data

            if isinstance(data, dict) and data.get("error") == "invalid_token":
                last_error = data.get("message") or "token invalido"
                self._log(
                    f"Token invalido (intento {attempt}/{self.retries}); renovando"
                )
                self.token = None
                self.session.cookies.clear()
                time.sleep(min(2**attempt, 8))
                continue

            last_error = (
                (data or {}).get("message") if isinstance(data, dict) else None
            ) or f"HTTP {response.status_code}: {response.text[:160]!r}"

            if response.status_code >= 500 or response.status_code == 429:
                wait = min(2**attempt, 20)
                self._log(
                    f"HTTP {response.status_code}; reintentando en {wait}s "
                    f"({attempt}/{self.retries})"
                )
                time.sleep(wait)
                continue
            raise ApiError(f"{last_error} | payload={canonical(payload)}")

        raise ApiError(f"Se agotaron los reintentos: {last_error} | {canonical(payload)}")


# ---------------------------------------------------------------------------
# Plan de descarga
# ---------------------------------------------------------------------------


def build_plan(
    metadata: dict[str, Any],
    desde: str,
    hasta: str,
    sectors: set[str] | None = None,
) -> list[dict[str, Any]]:
    series_map = metadata.get("series") or {}
    plan: list[dict[str, Any]] = []
    for sector, variables in series_map.items():
        if sectors and sector not in sectors:
            continue
        if not isinstance(variables, dict):
            continue
        por_moneda: dict[str, list[str]] = {}
        for variable, monedas in variables.items():
            if isinstance(monedas, str):
                monedas = [monedas]
            for moneda in monedas or []:
                por_moneda.setdefault(moneda, []).append(variable)
        # La API solo admite combinaciones de variables predefinidas por el
        # panel, por lo que se solicita una variable por peticion.
        for moneda in sorted(por_moneda):
            for variable in por_moneda[moneda]:
                plan.append(
                    {
                        "action": "series",
                        "sector": sector,
                        "variables": [variable],
                        "moneda": moneda,
                        "desde": desde,
                        "hasta": hasta,
                    }
                )
        for corte in CORTES:
            for variacion in VARIACIONES:
                if corte in ("semanal", "diario") and variacion != "acumulada":
                    continue
                plan.append(
                    {
                        "action": "kpis",
                        "sector": sector,
                        "corte": corte,
                        "variacion": variacion,
                    }
                )
    return plan


# ---------------------------------------------------------------------------
# Almacenamiento crudo
# ---------------------------------------------------------------------------


def raw_path(outdir: Path, payload: dict[str, Any]) -> Path:
    action = payload.get("action") or "request"
    parts = [action]
    if payload.get("sector"):
        parts.append(slugify(payload["sector"], 45))
    if action == "series" and payload.get("moneda"):
        parts.append(slugify(payload["moneda"], 20))
    if action == "kpis":
        parts.extend(
            [slugify(payload.get("corte"), 12), slugify(payload.get("variacion"), 12)]
        )
    digest = hashlib.sha1(canonical(payload).encode("utf-8")).hexdigest()[:10]
    name = "_".join(p for p in parts if p) + f"_{digest}.json"
    return outdir / "raw" / action / name


def save_envelope(
    path: Path,
    payload: dict[str, Any],
    response: dict[str, Any],
    source: str,
) -> None:
    write_json(
        path,
        {
            "source": source,
            "fetched_at": now_iso(),
            "request": payload,
            "response": response,
        },
    )


def load_envelope(path: Path) -> dict[str, Any] | None:
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return None
    response = data.get("response")
    return response if isinstance(response, dict) and response.get("ok") is True else None


# ---------------------------------------------------------------------------
# Recoleccion
# ---------------------------------------------------------------------------


@dataclass
class Collection:
    metadata: dict[str, Any] | None = None
    series: list[tuple[dict[str, Any], dict[str, Any]]] = field(default_factory=list)
    kpis: list[tuple[dict[str, Any], dict[str, Any]]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    counters: dict[str, int] = field(default_factory=dict)

    def count(self, key: str, amount: int = 1) -> None:
        self.counters[key] = self.counters.get(key, 0) + amount


def collect_live(
    client: BcbClient,
    plan: list[dict[str, Any]],
    outdir: Path,
    args: argparse.Namespace,
    collection: Collection,
) -> None:
    total = len(plan)
    for index, payload in enumerate(plan, 1):
        action = payload["action"]
        if action == "series":
            label = f"series | {payload['sector']} | {payload['moneda']} | 1 var."
        else:
            label = f"kpis   | {payload['sector']} | {payload['corte']}/{payload['variacion']}"
        log(f"[{index}/{total}] {label}")

        path = raw_path(outdir, payload)
        if args.resume and path.exists():
            cached = load_envelope(path)
            if cached is not None:
                if action == "series":
                    collection.series.append((payload, cached))
                elif action == "kpis":
                    collection.kpis.append((payload, cached))
                collection.count(f"{action}_cached")
                continue

        try:
            response = client.api(payload)
        except ApiError as exc:
            collection.errors.append(f"{label}: {exc}")
            collection.count(f"{action}_error")
            log(f"  ERROR: {exc}")
            continue

        save_envelope(path, payload, response, "live")
        if action == "series":
            collection.series.append((payload, response))
            collection.count("series_ok")
        elif action == "kpis":
            collection.kpis.append((payload, response))
            collection.count("kpis_ok")
        if args.delay:
            time.sleep(args.delay)


# ---------------------------------------------------------------------------
# Exportacion a CSV
# ---------------------------------------------------------------------------


def series_rows(
    responses: Iterable[tuple[dict[str, Any], dict[str, Any]]],
    errors: list[str],
) -> list[dict[str, Any]]:
    dedup: dict[tuple[str, str, str, str], Any] = {}
    for payload, response in responses:
        sector = payload.get("sector") or ""
        meses = response.get("meses") or []
        series = response.get("series") or {}
        if not isinstance(series, dict):
            errors.append(f"Respuesta series inesperada para {sector}: {type(series)!r}")
            continue
        for variable, monedas in series.items():
            if isinstance(monedas, list):
                monedas = {"Total": monedas}
            if not isinstance(monedas, dict):
                continue
            for moneda, valores in monedas.items():
                if not isinstance(valores, list):
                    continue
                if len(valores) != len(meses):
                    errors.append(
                        f"Longitud distinta en {sector} | {variable} | {moneda}: "
                        f"{len(valores)} valores vs {len(meses)} fechas"
                    )
                for fecha, valor in zip(meses, valores):
                    if valor is None or valor == "":
                        continue
                    dedup[(sector, variable, moneda, fecha)] = valor

    rows = [
        {
            "sector": sector,
            "variable": variable,
            "moneda": moneda,
            "fecha": fecha,
            "fecha_iso": fecha_iso(fecha),
            "valor": valor,
        }
        for (sector, variable, moneda, fecha), valor in dedup.items()
    ]
    rows.sort(
        key=lambda r: (
            r["sector"],
            r["variable"],
            r["moneda"],
            r["fecha_iso"] or r["fecha"],
        )
    )
    return rows


def kpi_rows(
    responses: Iterable[tuple[dict[str, Any], dict[str, Any]]],
    errors: list[str],
) -> list[dict[str, Any]]:
    dedup: dict[tuple[str, str, str, str, str], dict[str, Any]] = {}
    for payload, response in responses:
        sector = payload.get("sector") or ""
        corte = payload.get("corte") or ""
        variacion = payload.get("variacion") or ""
        items = response.get("items") or []
        if not isinstance(items, list):
            errors.append(f"Respuesta kpis inesperada para {sector}: {type(items)!r}")
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            variable = item.get("variable") or ""
            fecha = item.get("fecha") or response.get("fecha") or ""
            valor = item.get("valor")
            anterior = item.get("anterior")
            delta = None
            if isinstance(valor, (int, float)) and isinstance(anterior, (int, float)):
                delta = valor - anterior
            dedup[(sector, corte, variacion, variable, fecha)] = {
                "sector": sector,
                "corte": corte,
                "variacion": variacion,
                "fecha": fecha,
                "fecha_iso": fecha_iso(fecha),
                "variable": variable,
                "valor": valor,
                "anterior": anterior,
                "delta": delta,
            }
    rows = list(dedup.values())
    rows.sort(
        key=lambda r: (
            r["sector"],
            r["corte"],
            r["variacion"],
            r["variable"],
            r["fecha_iso"] or r["fecha"],
        )
    )
    return rows


def write_wide(path: Path, rows: list[dict[str, Any]]) -> int:
    if not rows:
        write_csv(path, ("fecha", "fecha_iso"), [])
        return 0
    present_sectors = {r["sector"] for r in rows}
    multi_sector = len(present_sectors) > 1
    keys = sorted(
        {
            (
                (r["sector"] + " | " if multi_sector else "")
                + f"{r['variable']} [{r['moneda']}]"
            )
            for r in rows
        }
    )
    columns = ["fecha", "fecha_iso", *keys]
    by_date: dict[str, dict[str, Any]] = {}
    for row in rows:
        key = (
            (row["sector"] + " | " if multi_sector else "")
            + f"{row['variable']} [{row['moneda']}]"
        )
        date_key = row["fecha_iso"] or row["fecha"]
        by_date.setdefault(
            date_key, {"fecha": row["fecha"], "fecha_iso": row["fecha_iso"]}
        )
        by_date[date_key][key] = row["valor"]
    ordered = [by_date[k] for k in sorted(by_date)]
    return write_csv(path, columns, ordered)


def export_csvs(
    collection: Collection,
    outdir: Path,
    errors: list[str],
) -> dict[str, int]:
    csv_dir = outdir / "csv"
    counts: dict[str, int] = {}

    series = series_rows(collection.series, errors)
    counts["series_long"] = write_csv(outdir / "series_long.csv", SERIES_COLUMNS, series)
    counts["series_wide"] = write_wide(outdir / "series_wide.csv", series)

    for sector in sorted({r["sector"] for r in series}):
        subset = [r for r in series if r["sector"] == sector]
        counts[f"series_{slugify(sector, 40)}"] = write_wide(
            csv_dir / f"{slugify(sector, 60)}.csv", subset
        )

    kpis = kpi_rows(collection.kpis, errors)
    counts["kpis_long"] = write_csv(outdir / "kpis_long.csv", KPI_COLUMNS, kpis)

    return counts


# ---------------------------------------------------------------------------
# Manifiesto y resumen
# ---------------------------------------------------------------------------


def collect_files(outdir: Path) -> dict[str, int]:
    files: dict[str, int] = {}
    for path in sorted(outdir.rglob("*")):
        if path.is_file() and path.suffix != ".tmp":
            files[str(path.relative_to(outdir))] = path.stat().st_size
    return files


def write_manifest(
    outdir: Path,
    api_url: str,
    token_source: str,
    collection: Collection,
    counts: dict[str, int],
    errors: list[str],
    started_at: str,
) -> Path:
    metadata = collection.metadata or {}
    meses = metadata.get("meses") or []
    manifest = {
        "generated_at": now_iso(),
        "started_at": started_at,
        "api_url": api_url,
        "token_source": token_source,
        "metadata": {
            "actualizado": metadata.get("actualizado"),
            "conteos": metadata.get("conteos"),
            "periodos": len(meses),
            "desde": meses[0] if meses else None,
            "hasta": meses[-1] if meses else None,
        },
        "counters": collection.counters,
        "csv_rows": counts,
        "series_responses": len(collection.series),
        "kpi_responses": len(collection.kpis),
        "errors": errors,
        "files": collect_files(outdir),
    }
    path = outdir / "manifest.json"
    write_json(path, manifest)
    return path


def print_summary(collection: Collection, counts: dict[str, int], manifest: Path) -> None:
    print()
    print("=" * 68)
    print("Resumen de la descarga")
    print("=" * 68)
    for key in sorted(collection.counters):
        print(f"  {key:<22} {collection.counters[key]}")
    print(f"  {'respuestas series':<22} {len(collection.series)}")
    print(f"  {'respuestas kpis':<22} {len(collection.kpis)}")
    print()
    for key in sorted(counts):
        print(f"  {key:<22} {counts[key]} filas")
    if collection.errors:
        print(f"\n  Errores/avisos: {len(collection.errors)} (ver manifest.json)")
    print(f"\n  Manifiesto: {manifest}")
    print("=" * 68)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scraper completo de las Estadisticas Semanales del BCB.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path(__file__).resolve().parents[3] / "data" / "api",
        help="Directorio de salida (por defecto: knowledge/data/api).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Muestra el plan de peticiones sin descargar nada.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Reutiliza respuestas crudas ya guardadas en --outdir.",
    )
    parser.add_argument(
        "--sector",
        action="append",
        default=[],
        metavar="NOMBRE",
        help="Limita la descarga a un sector (repetible).",
    )
    parser.add_argument(
        "--desde",
        help="Fecha inicial dd/mm/aaaa (por defecto: primera de metadata).",
    )
    parser.add_argument(
        "--hasta",
        help="Fecha final dd/mm/aaaa (por defecto: ultima de metadata).",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.35,
        help="Segundos entre peticiones (por defecto: 0.35).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        help="Timeout HTTP en segundos (por defecto: 60).",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=4,
        help="Reintentos por peticion (por defecto: 4).",
    )
    parser.add_argument(
        "--token",
        default=None,
        help="Token explicito (por defecto: variable BCB_API_TOKEN o index.php).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Reduce la salida por consola.",
    )
    return parser.parse_args(argv)


def select_sectors(metadata: dict[str, Any], requested: list[str]) -> set[str] | None:
    available = list((metadata.get("series") or {}).keys())
    if not requested:
        return None
    selected = set()
    for name in requested:
        if name in available:
            selected.add(name)
            continue
        matches = [s for s in available if slugify(s) == slugify(name)]
        if matches:
            selected.add(matches[0])
            continue
        raise SystemExit(
            f"Sector no encontrado: {name!r}\nDisponibles:\n  - "
            + "\n  - ".join(available)
        )
    return selected


def print_plan(plan: list[dict[str, Any]]) -> None:
    print()
    print(f"Plan de peticiones ({len(plan)})")
    print("-" * 68)
    for index, payload in enumerate(plan, 1):
        action = payload.get("action")
        if action == "series":
            print(
                f"{index:>3}. series  {payload['sector']} | {payload['moneda']} | "
                f"{payload['variables'][0]}"
            )
        elif action == "kpis":
            print(
                f"{index:>3}. kpis    {payload['sector']} | "
                f"{payload['corte']}/{payload['variacion']}"
            )
        else:
            print(f"{index:>3}. {action} {payload}")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    started_at = now_iso()
    outdir = args.outdir.expanduser()
    outdir.mkdir(parents=True, exist_ok=True)

    token = args.token or os.environ.get("BCB_API_TOKEN")
    client = BcbClient(
        timeout=args.timeout,
        retries=args.retries,
        delay=args.delay,
        token=token,
        verbose=not args.quiet,
    )
    collection = Collection()

    try:
        metadata = client.api({"action": "metadata"})
    except ApiError as exc:
        raise SystemExit(f"No se pudo obtener metadata: {exc}")
    collection.metadata = metadata
    collection.count("metadata_ok")
    save_envelope(
        raw_path(outdir, {"action": "metadata"}),
        {"action": "metadata"},
        metadata,
        "live",
    )

    sectores = select_sectors(metadata, args.sector)
    meses = metadata.get("meses") or []
    desde = args.desde or (meses[0] if meses else "")
    hasta = args.hasta or (meses[-1] if meses else "")
    if not desde or not hasta:
        raise SystemExit("Metadata sin rango de fechas; use --desde/--hasta.")
    log(f"Rango solicitado: {desde} -> {hasta}")

    plan = build_plan(metadata, desde, hasta, sectores)

    if args.dry_run:
        print_plan(plan)
        return 0

    log(f"Peticiones planificadas: {len(plan)}")
    try:
        collect_live(client, plan, outdir, args, collection)
    except KeyboardInterrupt:
        log("Interrumpido por el usuario; exportando lo descargado...")

    counts = export_csvs(collection, outdir, collection.errors)
    manifest = write_manifest(
        outdir,
        client.api_url,
        client.token_source,
        collection,
        counts,
        collection.errors,
        started_at,
    )
    print_summary(collection, counts, manifest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
