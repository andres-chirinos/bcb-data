from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

_UNPIVOTR_SRC = Path(os.environ.get("UNPIVOTR_SRC", "/home/andreschirinos/Proyectos/unpivotr-clone/src"))
if _UNPIVOTR_SRC.exists():
    sys.path.insert(0, str(_UNPIVOTR_SRC))

from unpivotr.coercers import SPANISH_MONTHS, parse_date

EXTENSIONES_DATOS = {".xlsx", ".xlsm", ".xlsb", ".xls", ".ods", ".csv", ".tsv"}
PATRON_FORMULARIO = re.compile(
    r"(formulario|form_\d|solicitud|plantilla|licitacionesbcb|/riof/|open_bcb)",
    re.IGNORECASE,
)


def parse_publication(relpath: str, filename: str, downloaded_at: str = "") -> str:
    p = relpath.replace("\\", "/")
    name = filename
    upper = name.upper()

    m = re.search(r"publicacionesbcb/(\d{4})/(\d{2})/(\d{2})/", p)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"

    m = re.search(r"semanal\s*(?:n[°º]?\s*)?(\d{1,2})[_\s-]+(\d{4})", upper)
    if m:
        try:
            return date.fromisocalendar(int(m.group(2)), int(m.group(1)), 1).isoformat()
        except ValueError:
            pass

    m = re.search(r"\bTD[_\s-]+(\d{1,2})[_\s-]+(\d{1,2})[_\s-]+(\d{4})\b", upper)
    if m:
        return f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"

    m = re.search(r"\bPUBLICACION\s+(\d{4})\s+(\d{1,2})\s+(\d{1,2})\b", upper)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"

    m = re.search(r"\bBOP[_\s-]*T([1-4])[_\s-]+(\d{4})\b", upper)
    if m:
        q = int(m.group(1))
        return f"{m.group(2)}-{ {1: '03-31', 2: '06-30', 3: '09-30', 4: '12-31'}[q] }"

    for clave, mes in SPANISH_MONTHS.items():
        if re.search(rf"\b{clave}\b", upper):
            m_yr = re.search(r"\b(19\d{2}|20\d{2})\b", upper)
            if m_yr:
                import calendar

                last = calendar.monthrange(int(m_yr.group(1)), mes)[1]
                return f"{m_yr.group(1)}-{mes:02d}-{last:02d}"

    m = re.search(r"\b(19\d{2}|20\d{2})\b", upper)
    if m:
        return f"{m.group(1)}-01-01"

    d = parse_date(downloaded_at)
    return d or ""


def _familia_tasas(name: str) -> str:
    u = name.upper()
    if u.startswith("TD_"):
        return "tasas_diarias"
    if u.startswith(("PUBLICACION", "TASAS ACT Y PAS")):
        return "tasas_publicacion"
    if u.startswith(("NUEVA TRE", "TRE GESTION")):
        return "tasas_referencia"
    if re.search(r"30\s*DC\s*S|30DCS", u):
        return "tasas_destino_credito_semanal"
    if re.search(r"30\s*DC\s*M|30DCM|30DCANUAL", u):
        return "tasas_destino_credito_mensual"
    if re.search(r"28\s*AH\s*M|28AHM", u):
        return "tasas_historicas_mensuales"
    if re.search(r"28\s*AH\s*ANUAL|28AHANUAL", u):
        return "tasas_historicas_anuales"
    if re.search(r"28\s*AH\s*S|28AHS|B28PAASEMTOT", u):
        return "tasas_historicas_semanales"
    return "tasas_otras"


def _familia_publicaciones(name: str) -> str:
    u = name.upper()
    if "BOP" in u or "BALANZA DE PAGOS" in u:
        return "balanza_pagos"
    if "PII" in u or "POSICION DE INVERSION" in u or "POSICIÓN DE INVERSIÓN" in u:
        return "posicion_inversion_internacional"
    if "DEUDA_EXTERNA" in u or "DEUDA EXTERNA" in u:
        return "deuda_externa_bruta"
    if "MEMORIA" in u:
        return "memoria_anual"
    if "RESUMEN" in u:
        return "resumen_cifras"
    return "publicaciones_bcb_varias"


def classify(relpath: str, filename: str) -> dict[str, Any]:
    p = relpath.replace("\\", "/")
    name = filename
    ext = Path(name).suffix.lower()
    familia = ""
    motivo = ""

    if PATRON_FORMULARIO.search(p):
        return {
            "familia": "",
            "procesar": False,
            "es_formulario": True,
            "motivo": "formulario o plantilla",
        }
    if p.startswith("webdocs/licitacionesbcb/"):
        return {
            "familia": "",
            "procesar": False,
            "es_formulario": True,
            "motivo": "solicitud de licitacion",
        }
    if p.startswith("webdocs/riof/"):
        return {
            "familia": "",
            "procesar": False,
            "es_formulario": True,
            "motivo": "plantilla RIOF",
        }
    if p.startswith("webdocs/open_bcb/"):
        return {
            "familia": "",
            "procesar": False,
            "es_formulario": True,
            "motivo": "formulario Open BCB",
        }
    if p.startswith("webdocs/serviciosbcb/formularios/"):
        return {
            "familia": "",
            "procesar": False,
            "es_formulario": True,
            "motivo": "formulario de servicios",
        }

    if p.startswith("webdocs/tasas_interes/"):
        familia = _familia_tasas(name)
    elif p.startswith("webdocs/") and p.count("/") == 1 and re.search(
        r"30\s*DC\s*S|30DCS", name.upper()
    ):
        familia = "tasas_destino_credito_semanal"
    elif p.startswith("webdocs/05_estadisticassemanales/"):
        familia = "estadisticas_semanales"
    elif p.startswith("webdocs/publicacionesbcb/"):
        if re.search(r"publicacionesbcb/\d{4}/\d{2}/\d{2}/", p):
            familia = "boletin_estadistico"
        else:
            familia = _familia_publicaciones(name)
    elif p.startswith("webdocs/sistema_pagos/"):
        familia = "sistema_pagos"
    elif p.startswith("webdocs/sector_externo/A "):
        familia = "sector_externo_comercio_bienes"
    elif p.startswith("webdocs/sector_externo/B "):
        familia = "sector_externo_comercio_servicios"
    elif p.startswith("webdocs/sector_externo/C "):
        familia = "sector_externo_remesas"
    elif p.startswith("webdocs/sector_externo/D "):
        familia = "sector_externo_inversion_directa"
    elif p.startswith("webdocs/sector_externo/E "):
        familia = "sector_externo_deuda_externa"
    elif p.startswith("webdocs/sector_externo/F "):
        familia = "sector_externo_reservas"
    elif p.startswith("webdocs/sector_externo/G "):
        familia = "sector_externo_otras_variables"
    elif p.startswith("webdocs/sector_monetario/Balances Consolidados/"):
        familia = "sector_monetario_balances_consolidados"
    elif p.startswith("webdocs/sector_monetario/Créditos y Depósitos/OSD/"):
        familia = "sector_monetario_creditos_depositos_osd"
    elif p.startswith("webdocs/sector_monetario/Créditos y Depósitos/BCB/"):
        familia = "sector_monetario_creditos_depositos_bcb"
    elif p.startswith("webdocs/sector_monetario/Cuentas Monetarias"):
        familia = "sector_monetario_cuentas_monetarias"
    elif p.startswith("webdocs/sector_monetario/Indicadores Monetarios/"):
        familia = "sector_monetario_indicadores"
    elif p.startswith("webdocs/sector_monetario/Tasas Monetarias/"):
        familia = "sector_monetario_tasas_monetarias"
    elif p.startswith("webdocs/sector_precios/INFLACION NUCLEO/"):
        familia = "sector_precios_inflacion_nucleo"
    elif p.startswith("webdocs/sector_precios/INFLACION SUBYACENTE/"):
        familia = "sector_precios_inflacion_subyacente"
    elif p.startswith("webdocs/Documentos Adjuntos/"):
        familia = "programa_monetario"
    elif p.startswith("webdocs/Otros/"):
        familia = "calendario_publicaciones"
    elif p.startswith("webdocs/"):
        familia = "otros_webdocs"
    else:
        motivo = "fuera de webdocs"

    if familia == "calendario_publicaciones":
        motivo = "calendario de publicaciones, sin datos"
    procesar = bool(familia) and ext in EXTENSIONES_DATOS and not motivo
    if ext not in EXTENSIONES_DATOS:
        motivo = f"extension no tabular {ext}"
        procesar = False
    return {
        "familia": familia,
        "procesar": procesar,
        "es_formulario": False,
        "motivo": motivo,
    }


def read_manifest(docs_dir: Path) -> list[dict[str, str]]:
    path = docs_dir / "manifiesto.csv"
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def build_catalog(
    docs_dir: Path, incluir_duplicados: bool = False
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = read_manifest(docs_dir)
    descargados = [r for r in rows if r.get("status") == "descargado"]
    stems_xlsx = {
        (Path(r["relpath"]).parent, Path(r["filename"]).stem.lower())
        for r in descargados
        if Path(r["filename"]).suffix.lower() in {".xlsx", ".xlsm"}
    }
    catalog: list[dict[str, Any]] = []
    for r in rows:
        relpath = r.get("relpath", "")
        filename = r.get("filename", "")
        ext = Path(filename).suffix.lower()
        info = classify(relpath, filename)
        duplicado = False
        if (
            not incluir_duplicados
            and ext == ".ods"
            and (Path(relpath).parent, Path(filename).stem.lower()) in stems_xlsx
        ):
            duplicado = True
            info["procesar"] = False
            info["motivo"] = "ODS duplicado de XLSX"
        catalog.append(
            {
                "familia": info["familia"],
                "procesar": "si" if info["procesar"] else "no",
                "es_formulario": "si" if info["es_formulario"] else "no",
                "motivo": info["motivo"],
                "archivo": filename,
                "relpath": relpath,
                "extension": ext,
                "size_bytes": r.get("size_bytes", ""),
                "publicacion": parse_publication(relpath, filename, r.get("downloaded_at", "")),
                "requiere_conversion": "si" if ext in {".xls", ".xlsb", ".ods"} else "no",
                "duplicado": "si" if duplicado else "no",
                "sha256": r.get("sha256", ""),
                "status_descarga": r.get("status", ""),
            }
        )

    familias = Counter(r["familia"] for r in catalog if r["familia"] and r["procesar"] == "si")
    resumen = {
        "total_manifiesto": len(rows),
        "archivos_catalogo": len(catalog),
        "procesables": sum(1 for r in catalog if r["procesar"] == "si"),
        "formularios_excluidos": sum(1 for r in catalog if r["es_formulario"] == "si"),
        "duplicados_excluidos": sum(1 for r in catalog if r["duplicado"] == "si"),
        "familias": dict(sorted(familias.items())),
    }
    return catalog, resumen


def write_catalog(catalog: list[dict[str, Any]], out_csv: Path) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(catalog[0].keys()))
        writer.writeheader()
        writer.writerows(catalog)


def main() -> int:
    parser = argparse.ArgumentParser(description="Clasifica documentos BCB en familias de datos.")
    parser.add_argument("--docs", type=Path, default=Path(__file__).resolve().parents[3] / "data" / "documentos")
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parents[3] / "data" / "familias" / "catalogo.csv")
    parser.add_argument("--resumen", type=Path, default=Path(__file__).resolve().parents[3] / "data" / "familias" / "resumen_familias.json")
    parser.add_argument("--incluir-duplicados", action="store_true")
    args = parser.parse_args()

    catalog, resumen = build_catalog(args.docs, args.incluir_duplicados)
    write_catalog(catalog, args.out)
    args.resumen.parent.mkdir(parents=True, exist_ok=True)
    args.resumen.write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(resumen, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
