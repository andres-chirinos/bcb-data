#!/usr/bin/env python3
"""Explorador y extractor de hojas de cálculo del sitio Drupal del BCB.

Recorre https://www.bcb.gob.bo respetando robots.txt, descubre enlaces a
archivos .xls/.xlsx/.xlsm/.xlsb/.ods/.csv y los descarga preservando la
estructura de rutas del sitio. Genera manifiestos CSV/JSONL y un resumen.

Ejemplos:
    python3 bcb_drupal_scraper.py --dry-run
    python3 bcb_drupal_scraper.py --max-pages 200 --max-files 100
    python3 bcb_drupal_scraper.py --seed https://www.bcb.gob.bo/?q=tasas_interes
    python3 bcb_drupal_scraper.py --from-candidates knowledge/data/documentos/candidatos.csv
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import os
import re
import sys
import time
import unicodedata
import xml.etree.ElementTree as ET
from collections import deque
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse, urlunparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

LOGGER = logging.getLogger("bcb_drupal_scraper")

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 "
    "Firefox/128.0 bcb-data-crawler/1.0"
)

DEFAULT_HOSTS = {"www.bcb.gob.bo", "bcb.gob.bo"}

DEFAULT_SEEDS = [
    "https://www.bcb.gob.bo/",
    "https://www.bcb.gob.bo/rss.xml",
    "https://www.bcb.gob.bo/?q=estad-sticas-semanales",
    "https://www.bcb.gob.bo/?q=indicadores_inflacion",
    "https://www.bcb.gob.bo/?q=tasas_interes",
    "https://www.bcb.gob.bo/?q=cotizaciones_tc",
    "https://www.bcb.gob.bo/?q=servicios/ufv/datos_estadisticos",
    "https://www.bcb.gob.bo/?q=content/sector-externo-0",
    "https://www.bcb.gob.bo/?q=content/sector-monetario",
    "https://www.bcb.gob.bo/?q=content/sector-financiero-0",
    "https://www.bcb.gob.bo/?q=content/sector-precios",
    "https://www.bcb.gob.bo/?q=content/estados-de-la-deuda-externa",
    "https://www.bcb.gob.bo/?q=content/encaje-legal",
    "https://www.bcb.gob.bo/?q=content/posici%C3%B3n-de-cambios",
    "https://www.bcb.gob.bo/?q=operaciones-mercado-abierto",
    "https://www.bcb.gob.bo/?q=moneda-mercado-diario",
    "https://www.bcb.gob.bo/?q=moneda-mercado-semanal",
    "https://www.bcb.gob.bo/?q=informes-deuda-externa-publica",
    "https://www.bcb.gob.bo/?q=pub_informes-sobre-inversion",
    "https://www.bcb.gob.bo/?q=reporte-estadistico",
    "https://www.bcb.gob.bo/?q=boletines-mensuales",
    "https://www.bcb.gob.bo/?q=boletin_informativo_omm",
    "https://www.bcb.gob.bo/?q=programa-financiero",
    "https://www.bcb.gob.bo/?q=content/programa-monetario-0",
    "https://www.bcb.gob.bo/?q=pagos_qr_bcb_bolivia",
    "https://www.bcb.gob.bo/?q=informe-vigilancia-sistema-pagos",
]

SPREADSHEET_EXTS = {".xls", ".xlsx", ".xlsm", ".xlsb", ".ods", ".csv", ".tsv"}
DOCUMENT_EXTS = {
    ".pdf", ".doc", ".docx", ".ppt", ".pptx", ".zip", ".rar", ".7z",
    ".gz", ".tar", ".txt", ".xml", ".json", ".jpg", ".jpeg", ".png",
    ".gif", ".svg", ".webp", ".ico", ".mp3", ".mp4", ".avi", ".mov",
    ".css", ".js", ".woff", ".woff2", ".ttf", ".eot",
}
MIME_EXT = {
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "application/vnd.ms-excel": ".xls",
    "application/vnd.ms-excel.sheet.macroenabled.12": ".xlsm",
    "application/vnd.ms-excel.sheet.binary.macroenabled.12": ".xlsb",
    "application/vnd.oasis.opendocument.spreadsheet": ".ods",
    "text/csv": ".csv",
    "text/tab-separated-values": ".tsv",
}
BLOCKED_PREFIXES = (
    "/admin", "/user", "/search", "/comment", "/filter", "/node/add",
    "/cron.php", "/install.php", "/update.php", "/xmlrpc.php",
    "/misc", "/modules", "/profiles", "/scripts", "/themes", "/includes",
    "/bcb_estadisticas",
)
TRACKING_PARAMS = {"utm_source", "utm_medium", "utm_campaign", "utm_term",
                   "utm_content", "fbclid", "gclid", "mc_cid", "mc_eid"}

MANIFEST_FIELDS = [
    "url", "final_url", "filename", "relpath", "size_bytes", "sha256",
    "content_type", "source_page", "source_title", "link_text", "node_id",
    "downloaded_at", "status",
]
PAGE_FIELDS = ["url", "status", "title", "node_id", "content_type", "links",
               "spreadsheets", "depth", "fetched_at"]
ERROR_FIELDS = ["url", "source_page", "error", "at"]


@dataclass
class Candidate:
    url: str
    source_page: str
    source_title: str
    link_text: str
    depth: int


@dataclass
class Stats:
    pages_ok: int = 0
    pages_error: int = 0
    files_found: int = 0
    downloaded: int = 0
    skipped: int = 0
    errors: int = 0
    bytes_downloaded: int = 0
    started_at: str = ""
    finished_at: str = ""


@dataclass
class Config:
    outdir: Path
    hosts: set[str]
    seeds: list[str]
    max_depth: int
    max_pages: int
    max_files: int
    delay: float | None
    timeout: float
    retries: int
    dry_run: bool
    force: bool
    ignore_robots: bool
    allow_external_docs: bool
    verbose: bool
    from_candidates: Path | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_url(url: str) -> str:
    url = url.strip().replace("&amp;", "&")
    parsed = urlparse(url)
    if not parsed.scheme:
        return url
    scheme = "https" if parsed.scheme in {"http", "https"} else parsed.scheme
    host = parsed.netloc.lower()
    if host == "bcb.gob.bo":
        host = "www.bcb.gob.bo"
    path = re.sub(r"/{2,}", "/", parsed.path or "/")
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")
    query_pairs = []
    if parsed.query:
        for chunk in parsed.query.split("&"):
            if not chunk:
                continue
            key = unquote(chunk.split("=", 1)[0])
            if key in TRACKING_PARAMS:
                continue
            query_pairs.append(chunk)
    query_pairs.sort(key=lambda pair: unquote(pair.split("=", 1)[0]))
    query = "&".join(query_pairs)
    return urlunparse((scheme, host, path, "", query, ""))


def is_spreadsheet(url: str) -> bool:
    path = unquote(urlparse(url).path).lower()
    return Path(path).suffix in SPREADSHEET_EXTS


def is_document(url: str) -> bool:
    path = unquote(urlparse(url).path).lower()
    return Path(path).suffix in DOCUMENT_EXTS


def safe_component(name: str, fallback: str = "archivo") -> str:
    name = unicodedata.normalize("NFC", name)
    name = name.replace("\x00", "").strip()
    name = re.sub(r"[\x00-\x1f\x7f]", "", name)
    name = name.replace("/", "_").replace("\\", "_")
    if name in {"", ".", ".."}:
        name = fallback
    if len(name) > 180:
        ext = Path(name).suffix
        stem = Path(name).stem[: max(1, 180 - len(ext) - 9)]
        name = f"{stem}__{hashlib.sha1(name.encode('utf-8')).hexdigest()[:8]}{ext}"
    return name


def relpath_for(
    url: str,
    root_hosts: set[str],
    used: dict[str, str],
    filename: str | None = None,
) -> str:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if host == "bcb.gob.bo":
        host = "www.bcb.gob.bo"
    parts = [unquote(p) for p in parsed.path.split("/") if p]
    components = [safe_component(p) for p in parts]
    name = safe_component(filename) if filename else (components[-1] if components else "archivo")
    if components:
        components[-1] = name
    else:
        components = [name]
    prefix = "" if host in root_hosts else safe_component(host)
    rel = Path(*([prefix] if prefix else []), *components)
    rel_str = rel.as_posix()
    previous = used.get(rel_str)
    if previous and previous != url:
        digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:8]
        rel = rel.with_name(f"{rel.stem}__{digest}{rel.suffix}")
        rel_str = rel.as_posix()
    used[rel_str] = url
    return rel_str


def content_disposition_name(header: str) -> str:
    if not header:
        return ""
    match = re.search(r"filename\*\s*=\s*([^']*)''([^;]+)", header, re.IGNORECASE)
    if match:
        return unquote(match.group(2).strip().strip('"'))
    match = re.search(r'filename\s*=\s*"?([^";]+)"?', header, re.IGNORECASE)
    return unquote(match.group(1).strip()) if match else ""


def filename_for(url: str, content_type: str, disposition: str) -> str:
    url_name = safe_component(unquote(Path(urlparse(url).path).name) or "archivo")
    disposition_name = safe_component(content_disposition_name(disposition)) if disposition else ""
    chosen = disposition_name if disposition_name and Path(disposition_name).suffix else url_name
    suffix = Path(chosen).suffix.lower()
    if suffix not in SPREADSHEET_EXTS:
        extension = MIME_EXT.get(content_type.lower(), "")
        if extension:
            chosen = f"{chosen}{extension}"
    return chosen


def node_id_from(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path
    match = re.search(r"/node/(\d+)", path)
    if match:
        return match.group(1)
    query = parsed.query
    match = re.search(r"(?:^|&)(?:q|nid)=node/(\d+)", query)
    if match:
        return match.group(1)
    match = re.search(r"(?:^|&)nid=(\d+)", query)
    return match.group(1) if match else ""


def setup_session(cfg: Config) -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-BO,es;q=0.9,en;q=0.8",
    })
    retry = Retry(
        total=cfg.retries,
        connect=cfg.retries,
        read=cfg.retries,
        backoff_factor=1.0,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET", "HEAD"),
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=8, pool_maxsize=8)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def load_robots(session: requests.Session, cfg: Config) -> tuple[RobotFileParser, float]:
    parser = RobotFileParser()
    parser.set_url("https://www.bcb.gob.bo/robots.txt")
    delay = 10.0
    try:
        response = session.get("https://www.bcb.gob.bo/robots.txt", timeout=cfg.timeout)
        parser.parse(response.text.splitlines())
        parsed_delay = parser.crawl_delay(USER_AGENT) or parser.crawl_delay("*")
        if parsed_delay:
            delay = float(parsed_delay)
    except (requests.RequestException, ValueError, OSError) as exc:
        LOGGER.warning("No se pudo leer robots.txt: %s", exc)
    return parser, delay


def allowed_by_robots(parser: RobotFileParser, cfg: Config, url: str) -> bool:
    if cfg.ignore_robots:
        return True
    return parser.can_fetch(USER_AGENT, url)


def should_crawl(url: str, cfg: Config) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False
    host = parsed.netloc.lower()
    if host == "bcb.gob.bo":
        host = "www.bcb.gob.bo"
    spreadsheet = is_spreadsheet(url)
    external_bcb = host.endswith(".bcb.gob.bo") and cfg.allow_external_docs
    if host not in cfg.hosts and not (spreadsheet and external_bcb):
        return False
    path = unquote(parsed.path).lower()
    for prefix in BLOCKED_PREFIXES:
        if path == prefix or path.startswith(prefix + "/"):
            return False
    query = unquote(parsed.query).lower()
    if re.search(r"(?:^|&)q=search(?:/|&|$)", query):
        return False
    if spreadsheet or path.endswith("/rss.xml"):
        return True
    return not is_document(url)


def decode_response(response: requests.Response) -> str:
    if not response.encoding or response.encoding.lower() == "iso-8859-1":
        response.encoding = response.apparent_encoding or "utf-8"
    return response.text


def page_title(soup: BeautifulSoup) -> str:
    for selector in ("h1.page-header", "h1.title", "h1", "title"):
        node = soup.select_one(selector)
        if node:
            text = " ".join(node.get_text(" ", strip=True).split())
            if text:
                return text[:300]
    meta = soup.find("meta", attrs={"property": "og:title"})
    if meta and meta.get("content"):
        return " ".join(meta["content"].split())[:300]
    return ""


def extract_links(soup: BeautifulSoup, base: str) -> list[tuple[str, str]]:
    links = []
    seen = set()
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:", "data:")):
            continue
        text = " ".join(anchor.get_text(" ", strip=True).split())[:300]
        absolute = normalize_url(urljoin(base, href))
        if absolute in seen:
            continue
        seen.add(absolute)
        links.append((absolute, text))
    return links


def parse_rss(content: bytes) -> list[tuple[str, str]]:
    items = []
    try:
        root = ET.fromstring(content)
    except ET.ParseError:
        return items
    for item in root.iter("item"):
        link = item.findtext("link")
        title = item.findtext("title") or ""
        if link:
            items.append((normalize_url(link), " ".join(title.split())[:300]))
    return items


class Crawler:
    def __init__(self, cfg: Config) -> None:
        self.cfg = cfg
        self.session = setup_session(cfg)
        self.robots, self.robots_delay = load_robots(self.session, cfg)
        self.delay = cfg.delay if cfg.delay is not None else self.robots_delay
        self.stats = Stats(started_at=utc_now())
        self.queue: deque[Candidate] = deque()
        self.file_queue: deque[Candidate] = deque()
        self.queued_files: set[str] = set()
        if cfg.from_candidates:
            self.load_candidates(cfg.from_candidates)
        else:
            for seed in cfg.seeds:
                url = normalize_url(seed)
                target = self.file_queue if is_spreadsheet(url) else self.queue
                target.append(Candidate(url, "", "", "", 0))
        self.visited: set[str] = set()
        self.used_paths: dict[str, str] = {}
        self.existing: dict[str, dict] = {}
        self.last_request = 0.0
        self.outdir = cfg.outdir
        self._open_outputs()
        self._log_site_profile()

    def load_candidates(self, path: Path) -> None:
        with path.open("r", newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                url = normalize_url(row.get("url", ""))
                if not url or not is_spreadsheet(url) or url in self.queued_files:
                    continue
                if len(self.queued_files) >= self.cfg.max_files:
                    break
                self.queued_files.add(url)
                self.file_queue.append(Candidate(
                    url,
                    row.get("source_page", ""),
                    row.get("source_title", ""),
                    row.get("link_text", ""),
                    0,
                ))
        LOGGER.info("Candidatos cargados: %d", len(self.file_queue))

    def _open_outputs(self) -> None:
        self.pages_path = self.outdir / "paginas.csv"
        self.manifest_path = self.outdir / "manifiesto.csv"
        self.manifest_jsonl = self.outdir / "manifiesto.jsonl"
        self.errors_path = self.outdir / "errores.csv"
        self.candidates_path = self.outdir / "candidatos.csv"
        self.log_path = self.outdir / "crawl.log"
        for path, fields in (
            (self.pages_path, PAGE_FIELDS),
            (self.manifest_path, MANIFEST_FIELDS),
            (self.candidates_path, MANIFEST_FIELDS),
        ):
            if not path.exists():
                with path.open("w", newline="", encoding="utf-8") as handle:
                    csv.DictWriter(handle, fieldnames=fields).writeheader()
        if not self.errors_path.exists():
            with self.errors_path.open("w", newline="", encoding="utf-8") as handle:
                csv.DictWriter(handle, fieldnames=ERROR_FIELDS).writeheader()
        if self.manifest_jsonl.exists():
            with self.manifest_jsonl.open("r", encoding="utf-8") as handle:
                for line in handle:
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    self.existing[record.get("url", "")] = record
                    relpath = record.get("relpath", "")
                    if relpath:
                        self.used_paths[relpath] = record.get("url", "")

    def _log_site_profile(self) -> None:
        try:
            response = self.session.get(
                "https://www.bcb.gob.bo/", timeout=self.cfg.timeout
            )
            soup = BeautifulSoup(decode_response(response), "html.parser")
            generator = soup.find("meta", attrs={"name": re.compile("^generator$", re.IGNORECASE)})
            label = generator.get("content") if generator else "desconocido"
            LOGGER.info("Sitio: %s | Generador: %s", response.url, label)
        except (requests.RequestException, ValueError, OSError) as exc:
            LOGGER.warning("No se pudo perfilar el sitio: %s", exc)
        LOGGER.info(
            "robots.txt: crawl-delay=%ss | hosts=%s",
            self.robots_delay,
            ",".join(sorted(self.cfg.hosts)),
        )
        LOGGER.info(
            "Delay de rastreo: %.2fs | max_pages=%d | max_depth=%d | max_files=%d",
            self.delay,
            self.cfg.max_pages,
            self.cfg.max_depth,
            self.cfg.max_files,
        )
        if self.cfg.delay is not None and self.cfg.delay < self.robots_delay:
            LOGGER.warning(
                "El delay manual %.2fs es menor al crawl-delay de robots.txt (%.0fs)",
                self.cfg.delay,
                self.robots_delay,
            )

    def throttle(self) -> None:
        elapsed = time.monotonic() - self.last_request
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        self.last_request = time.monotonic()

    def run(self) -> Stats:
        while self.file_queue or (
            self.queue
            and self.stats.pages_ok < self.cfg.max_pages
            and len(self.queued_files) < self.cfg.max_files
        ):
            if self.file_queue:
                candidate = self.file_queue.popleft()
            elif self.stats.pages_ok < self.cfg.max_pages:
                candidate = self.queue.popleft()
            else:
                LOGGER.info("Límite de páginas alcanzado (%d)", self.cfg.max_pages)
                break
            url = candidate.url
            if url in self.visited:
                continue
            self.visited.add(url)
            if not should_crawl(url, self.cfg):
                continue
            if not allowed_by_robots(self.robots, self.cfg, url):
                LOGGER.debug("Bloqueado por robots.txt: %s", url)
                continue
            if is_spreadsheet(url):
                self.stats.files_found += 1
                self.handle_file(candidate)
                continue
            if candidate.depth > self.cfg.max_depth:
                continue
            self.handle_page(candidate)
        if self.queue and self.stats.pages_ok >= self.cfg.max_pages:
            LOGGER.info("Límite de páginas alcanzado (%d)", self.cfg.max_pages)
        self.stats.finished_at = utc_now()
        self.write_summary()
        return self.stats

    def fetch(self, url: str) -> requests.Response:
        self.throttle()
        return self.session.get(url, timeout=self.cfg.timeout, allow_redirects=True)

    def handle_page(self, candidate: Candidate) -> None:
        try:
            response = self.fetch(candidate.url)
            content_type = response.headers.get("Content-Type", "")
            if response.status_code != 200:
                self.record_error(candidate.url, candidate.source_page,
                                  f"HTTP {response.status_code}")
                self.stats.pages_error += 1
                return
            if "xml" in content_type or candidate.url.endswith("rss.xml"):
                links = parse_rss(response.content)
                title = "RSS"
                soup = None
            elif "html" in content_type or not content_type:
                soup = BeautifulSoup(decode_response(response), "html.parser")
                title = page_title(soup)
                links = extract_links(soup, response.url)
            else:
                return
            node_id = node_id_from(response.url) or node_id_from(candidate.url)
            file_count = 0
            for link, text in links:
                if is_spreadsheet(link):
                    if should_crawl(link, self.cfg):
                        file_count += 1
                        if link not in self.queued_files and len(self.queued_files) < self.cfg.max_files:
                            self.queued_files.add(link)
                            self.file_queue.append(Candidate(link, candidate.url, title, text, candidate.depth))
                elif candidate.depth < self.cfg.max_depth and should_crawl(link, self.cfg):
                    self.queue.append(Candidate(link, candidate.url, title, text, candidate.depth + 1))
            self.stats.pages_ok += 1
            self.write_page({
                "url": candidate.url,
                "status": response.status_code,
                "title": title,
                "node_id": node_id,
                "content_type": content_type,
                "links": len(links),
                "spreadsheets": file_count,
                "depth": candidate.depth,
                "fetched_at": utc_now(),
            })
            if self.cfg.verbose:
                LOGGER.info("Página [%d] %s | %d enlaces | %d hojas",
                             candidate.depth, candidate.url, len(links), file_count)
            elif self.stats.pages_ok % 25 == 0:
                LOGGER.info("Progreso: %d páginas, %d hojas encontradas, %d descargadas",
                             self.stats.pages_ok, self.stats.files_found, self.stats.downloaded)
        except (requests.RequestException, ValueError, OSError, UnicodeError) as exc:
            self.stats.pages_error += 1
            self.record_error(candidate.url, candidate.source_page, str(exc))
            LOGGER.warning("Error de página %s: %s", candidate.url, exc)

    def handle_file(self, candidate: Candidate) -> None:
        url = candidate.url
        if url in self.existing and not self.cfg.force:
            relpath = self.existing[url].get("relpath", "")
            if relpath and (self.outdir / relpath).exists():
                self.stats.skipped += 1
                return
        if self.cfg.dry_run:
            record = self.base_record(candidate)
            record["relpath"] = relpath_for(url, self.cfg.hosts, self.used_paths)
            record["status"] = "candidato"
            self.write_candidate(record)
            return
        try:
            self.throttle()
            response = self.session.get(url, timeout=self.cfg.timeout, stream=True,
                                        allow_redirects=True)
            if response.status_code != 200:
                self.record_error(url, candidate.source_page, f"HTTP {response.status_code}")
                self.stats.errors += 1
                return
            content_type = response.headers.get("Content-Type", "").split(";")[0].strip()
            if "text/html" in content_type.lower():
                self.record_error(url, candidate.source_page,
                                  "El servidor devolvió HTML en lugar de una hoja de cálculo")
                self.stats.errors += 1
                return
            if content_type and "text/plain" in content_type.lower():
                LOGGER.debug("Tipo de contenido genérico para %s", url)
            filename = filename_for(
                url, content_type, response.headers.get("Content-Disposition", "")
            )
            relpath = relpath_for(url, self.cfg.hosts, self.used_paths, filename=filename)
            destination = self.outdir / relpath
            destination.parent.mkdir(parents=True, exist_ok=True)
            temp = destination.with_name(destination.name + ".part")
            digest = hashlib.sha256()
            size = 0
            with temp.open("wb") as handle:
                for chunk in response.iter_content(chunk_size=128 * 1024):
                    if not chunk:
                        continue
                    handle.write(chunk)
                    digest.update(chunk)
                    size += len(chunk)
            os.replace(temp, destination)
            record = {
                "url": url,
                "final_url": response.url,
                "filename": destination.name,
                "relpath": relpath,
                "size_bytes": size,
                "sha256": digest.hexdigest(),
                "content_type": content_type,
                "source_page": candidate.source_page,
                "source_title": candidate.source_title,
                "link_text": candidate.link_text,
                "node_id": node_id_from(candidate.source_page),
                "downloaded_at": utc_now(),
                "status": "descargado",
            }
            self.append_manifest(record)
            self.stats.downloaded += 1
            self.stats.bytes_downloaded += size
            if self.stats.downloaded % 10 == 0 or self.cfg.verbose:
                LOGGER.info("Descargadas %d hojas (%.1f MB)",
                             self.stats.downloaded, self.stats.bytes_downloaded / 1e6)
        except (requests.RequestException, ValueError, OSError) as exc:
            self.stats.errors += 1
            self.record_error(url, candidate.source_page, str(exc))
            LOGGER.warning("Error de archivo %s: %s", url, exc)

    def base_record(self, candidate: Candidate) -> dict:
        return {
            "url": candidate.url,
            "final_url": candidate.url,
            "filename": Path(unquote(urlparse(candidate.url).path)).name,
            "relpath": "",
            "size_bytes": "",
            "sha256": "",
            "content_type": "",
            "source_page": candidate.source_page,
            "source_title": candidate.source_title,
            "link_text": candidate.link_text,
            "node_id": node_id_from(candidate.source_page),
            "downloaded_at": "",
            "status": "candidato",
        }

    def write_page(self, record: dict) -> None:
        with self.pages_path.open("a", newline="", encoding="utf-8") as handle:
            csv.DictWriter(handle, fieldnames=PAGE_FIELDS).writerow(record)

    def write_candidate(self, record: dict) -> None:
        with self.candidates_path.open("a", newline="", encoding="utf-8") as handle:
            csv.DictWriter(handle, fieldnames=MANIFEST_FIELDS).writerow(record)

    def append_manifest(self, record: dict) -> None:
        with self.manifest_path.open("a", newline="", encoding="utf-8") as handle:
            csv.DictWriter(handle, fieldnames=MANIFEST_FIELDS).writerow(record)
        with self.manifest_jsonl.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        self.existing[record["url"]] = record

    def record_error(self, url: str, source_page: str, error: str) -> None:
        with self.errors_path.open("a", newline="", encoding="utf-8") as handle:
            csv.DictWriter(handle, fieldnames=ERROR_FIELDS).writerow({
                "url": url, "source_page": source_page, "error": error, "at": utc_now(),
            })

    def write_summary(self) -> None:
        manifest_files = 0
        manifest_bytes = 0
        if self.manifest_path.exists():
            with self.manifest_path.open("r", newline="", encoding="utf-8") as handle:
                for row in csv.DictReader(handle):
                    if row.get("status") != "descargado":
                        continue
                    manifest_files += 1
                    try:
                        manifest_bytes += int(row.get("size_bytes") or 0)
                    except ValueError:
                        continue
        summary = {
            "started_at": self.stats.started_at,
            "finished_at": self.stats.finished_at,
            "pages_ok": self.stats.pages_ok,
            "pages_error": self.stats.pages_error,
            "spreadsheets_found": self.stats.files_found,
            "downloaded": self.stats.downloaded,
            "skipped": self.stats.skipped,
            "errors": self.stats.errors,
            "bytes_downloaded": self.stats.bytes_downloaded,
            "manifest_files": manifest_files,
            "manifest_bytes": manifest_bytes,
            "max_depth": self.cfg.max_depth,
            "max_pages": self.cfg.max_pages,
            "max_files": self.cfg.max_files,
            "delay_seconds": self.delay,
            "robots_crawl_delay": self.robots_delay,
            "hosts": sorted(self.cfg.hosts),
            "seeds": self.cfg.seeds,
            "from_candidates": str(self.cfg.from_candidates) if self.cfg.from_candidates else "",
            "dry_run": self.cfg.dry_run,
        }
        (self.outdir / "resumen.json").write_text(
            json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )


def parse_args(argv: Iterable[str] | None = None) -> Config:
    parser = argparse.ArgumentParser(
        description="Explora el sitio Drupal del BCB y descarga sus hojas de cálculo.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--outdir", default=str(Path(__file__).resolve().parents[3] / "data" / "documentos"),
                        help="Directorio de salida")
    parser.add_argument("--seed", action="append", default=None,
                        help="URL semilla (repetible); reemplaza las semillas por defecto")
    parser.add_argument("--max-depth", type=int, default=4,
                        help="Profundidad máxima de navegación HTML")
    parser.add_argument("--max-pages", type=int, default=1000,
                        help="Máximo de páginas HTML a visitar")
    parser.add_argument("--max-files", type=int, default=2000,
                        help="Máximo de hojas de cálculo a descargar")
    parser.add_argument("--delay", type=float, default=None,
                        help="Segundos entre peticiones; por defecto usa robots.txt")
    parser.add_argument("--timeout", type=float, default=60.0,
                        help="Timeout por petición en segundos")
    parser.add_argument("--retries", type=int, default=3,
                        help="Reintentos por petición")
    parser.add_argument("--dry-run", action="store_true",
                        help="Descubre hojas sin descargarlas")
    parser.add_argument("--force", action="store_true",
                        help="Vuelve a descargar archivos ya registrados")
    parser.add_argument("--ignore-robots", action="store_true",
                        help="No respeta robots.txt (usar con precaución)")
    parser.add_argument("--allow-external-docs", action="store_true",
                        help="Permite descargar hojas de subdominios *.bcb.gob.bo")
    parser.add_argument("--from-candidates", type=Path, default=None,
                        help="Descarga los URLs de un candidatos.csv sin rastrear páginas")
    parser.add_argument("--verbose", action="store_true", help="Registro detallado")
    args = parser.parse_args(list(argv) if argv is not None else None)

    outdir = Path(args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(outdir / "crawl.log", encoding="utf-8"),
        ],
    )
    hosts = set(DEFAULT_HOSTS)
    seeds = [normalize_url(s) for s in (args.seed or DEFAULT_SEEDS)]
    if args.allow_external_docs:
        for seed in seeds:
            hosts.add(urlparse(seed).netloc.lower())
    return Config(
        outdir=outdir,
        hosts=hosts,
        seeds=seeds,
        max_depth=max(0, args.max_depth),
        max_pages=max(1, args.max_pages),
        max_files=max(1, args.max_files),
        delay=args.delay,
        timeout=max(1.0, args.timeout),
        retries=max(0, args.retries),
        dry_run=args.dry_run,
        force=args.force,
        ignore_robots=args.ignore_robots,
        allow_external_docs=args.allow_external_docs,
        verbose=args.verbose,
        from_candidates=args.from_candidates,
    )


def main(argv: Iterable[str] | None = None) -> int:
    cfg = parse_args(argv)
    crawler = Crawler(cfg)
    stats = crawler.run()
    LOGGER.info(
        "Fin: %d páginas, %d hojas encontradas, %d descargadas (%.1f MB), %d errores",
        stats.pages_ok, stats.files_found, stats.downloaded,
        stats.bytes_downloaded / 1e6, stats.errors,
    )
    LOGGER.info("Salida: %s", cfg.outdir)
    return 0 if stats.pages_ok > 0 or stats.files_found > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
