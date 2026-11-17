from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

_UNPIVOTR_SRC = Path(
    os.environ.get("UNPIVOTR_SRC", "/home/andreschirinos/Proyectos/unpivotr-clone/src")
)
if _UNPIVOTR_SRC.exists():
    sys.path.insert(0, str(_UNPIVOTR_SRC))

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "03_familias"))

import pandas as pd
from unpivotr import TableFlattener, WorkbookGrid, clean_number, parse_date, to_slug
from unpivotr.coercers import SPANISH_MONTHS

from bcb_families import build_catalog

SKIP_SHEET = re.compile(
    r"(portada|índice|indice|metodolog|notas|formulario|instrucciones)", re.IGNORECASE
)
FORM_WORDS = re.compile(
    r"(formulario|solicitud|llenar|\bfirma\b|señores|senores|proponente|datos del solicitante)",
    re.IGNORECASE,
)
YEAR_RE = re.compile(r"\b(19\d{2}|20\d{2})\b")
DATE_HEADER_RE = re.compile(
    r"^(DESDE|HASTA|PERIODO|PERÍODO|FECHA|AÑO|ANIO|GESTI[OÓ]N)$",
    re.IGNORECASE,
)
MONTH_LABEL_RE = re.compile(
    r"^(ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC)(?:\s*\(\d+\))?$",
    re.IGNORECASE,
)
QUARTER_RE = re.compile(
    r"(?:(19\d{2}|20\d{2})\s*[-_ ]?\s*([1-4])\s*[TQ])|"
    r"(?:([1-4])\s*[TQ]\s*[-_ ]?\s*(19\d{2}|20\d{2}))|"
    r"\bT\s*([1-4])\b",
    re.IGNORECASE,
)
TRIM_RE = re.compile(r"\bTRIM(?:ESTRE)?\.?\s*(I{1,3}|IV|1|2|3|4)\b", re.IGNORECASE)
WEEK_RE = re.compile(
    r"SEM(?:ANA)?\s*(?:DEL|N[°º]?)?\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})", re.IGNORECASE
)
WEEK_YEAR_RE = re.compile(
    r"SEM(?:ANA)?\s*(?:N[°º]?)?\s*(\d{1,2})[\s_-]+(?:DE\s*)?(19\d{2}|20\d{2})",
    re.IGNORECASE,
)
MONTH_RANGE_RE = re.compile(
    r"\b([A-ZÁÉÍÓÚ]{3,10})\s*[-–]\s*([A-ZÁÉÍÓÚ]{3,10})\s*(?:DE\s*)?(19\d{2}|20\d{2})",
    re.IGNORECASE,
)
QUARTER_END = {1: "03-31", 2: "06-30", 3: "09-30", 4: "12-31"}
DEFAULT_UNITS = {
    "tasas_diarias": "%",
    "tasas_publicacion": "%",
    "tasas_referencia": "%",
    "tasas_destino_credito_semanal": "%",
    "tasas_destino_credito_mensual": "%",
    "tasas_historicas_anuales": "%",
    "tasas_historicas_mensuales": "%",
    "tasas_historicas_semanales": "%",
    "sector_monetario_tasas_monetarias": "%",
    "sector_precios_inflacion_nucleo": "%",
    "sector_precios_inflacion_subyacente": "%",
}


def _ne(value: Any) -> bool:
    return value is not None and str(value).strip() != ""


def _is_text(value: Any) -> bool:
    return _ne(value) and clean_number(value) is None


def _is_label(value: Any) -> bool:
    return _is_text(value) and not re.fullmatch(r"[\s\-–—_.]+", str(value))


def _fmt_date(value: Any) -> str | None:
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return None


def parse_period(value: Any, default_year: int | None = None) -> str | None:
    if value is None:
        return None
    exact = _fmt_date(value)
    if exact:
        return exact
    text = str(value).strip()
    if not text:
        return None
    upper = text.upper()
    year_match = YEAR_RE.search(upper)
    year = int(year_match.group(1)) if year_match else default_year

    quarter = QUARTER_RE.search(upper)
    if quarter:
        y = int(quarter.group(1) or quarter.group(4) or year or 0)
        q = int(quarter.group(2) or quarter.group(3) or quarter.group(5) or 0)
        if y and 1 <= q <= 4:
            return f"{y}-{QUARTER_END[q]}"
    trim = TRIM_RE.search(upper)
    if trim and year:
        raw_q = trim.group(1).upper()
        q = {"I": 1, "II": 2, "III": 3, "IV": 4}.get(raw_q)
        q = q or int(raw_q)
        if 1 <= q <= 4:
            return f"{year}-{QUARTER_END[q]}"

    week = WEEK_RE.search(upper)
    if week:
        d, m, y = week.groups()
        return f"{y}-{int(m):02d}-{int(d):02d}"
    week_year = WEEK_YEAR_RE.search(upper)
    if week_year:
        try:
            return date.fromisocalendar(int(week_year.group(2)), int(week_year.group(1)), 1).isoformat()
        except ValueError:
            pass

    day_month = re.search(
        r"\b(\d{1,2})\s*(?:de|[-/])\s*([A-ZÁÉÍÓÚ]{3,10})(?:\s*(?:de|[-/])?\s*(19\d{2}|20\d{2}))?",
        upper,
        re.IGNORECASE,
    )
    if day_month:
        day, month_name, year_text = day_month.groups()
        for key, month in SPANISH_MONTHS.items():
            if month_name.startswith(key):
                y = int(year_text) if year_text else (default_year or datetime.now().astimezone().year)
                return f"{y}-{month:02d}-{int(day):02d}"

    month_range = MONTH_RANGE_RE.search(upper)
    if month_range:
        end = month_range.group(2)
        for key, month in SPANISH_MONTHS.items():
            if end.startswith(key):
                import calendar

                last = calendar.monthrange(int(month_range.group(3)), month)[1]
                return f"{month_range.group(3)}-{month:02d}-{last:02d}"

    return parse_date(value, default_year=year)


def _specificity(value: Any, parsed: str | None) -> int:
    if not parsed:
        return 0
    text = str(value).upper()
    if re.search(r"\d{1,2}[/-]\d{1,2}[/-]\d{4}", text) or "SEM" in text:
        return 3
    if re.search(r"\b(T[1-4]|TRIM|ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC)\b", text):
        return 2
    if YEAR_RE.search(text):
        return 1
    return 1


def _header_value(grid: Any, row: int, col: int) -> Any:
    value = grid.cell_value(row, col)
    if _ne(value):
        return value
    for r1, c1, r2, c2 in grid.merged_ranges:
        if r1 <= row <= r2 and c1 <= col <= c2:
            return grid.cell_value(r1, c1)
    return None


def _header_detection(grid: Any, row: int, col: int) -> Any:
    for r1, c1, r2, c2 in grid.merged_ranges:
        if r1 <= row <= r2 and c1 <= col <= c2:
            if c2 - c1 + 1 > 3:
                return None
            return grid.cell_value(r1, c1)
    return grid.cell_value(row, col)


def _header_left(grid: Any, row: int, col: int) -> Any:
    for current in range(col, 0, -1):
        value = _header_value(grid, row, current)
        if _ne(value):
            return value
    return None


def _column_up(grid: Any, row: int, col: int) -> Any:
    for current in range(row, 0, -1):
        value = grid.cell_value(current, col)
        if _is_text(value) and not _period_like(value):
            return value
    return None


def _last_period_above(grid: Any, row: int, col: int) -> Any:
    for current in range(row, 0, -1):
        value = grid.cell_value(current, col)
        if _period_like(value) or parse_period(value) or MONTH_LABEL_RE.match(str(value or "")):
            return value
    return None


def _effective_bounds(grid: Any, max_rows: int = 1500, max_cols: int = 700) -> tuple[int, int]:
    max_row = min(grid.max_row, max_rows)
    max_col = min(grid.max_col, max_cols)
    last_row = 0
    last_col = 0
    for r_idx, row in enumerate(grid._rows[:max_row], start=1):
        for c_idx, value in enumerate(row[:max_col], start=1):
            if _ne(value):
                last_row = max(last_row, r_idx)
                last_col = max(last_col, c_idx)
    return last_row, last_col


def _count_numeric(grid: Any, row: int, col_start: int, col_end: int) -> int:
    return sum(
        1 for c in range(col_start, col_end + 1) if clean_number(grid.cell_value(row, c)) is not None
    )


def _count_text(grid: Any, row: int, col_start: int, col_end: int) -> int:
    return sum(1 for c in range(col_start, col_end + 1) if _is_text(grid.cell_value(row, c)))


def _numeric_ratio(grid: Any, col: int, row_start: int, row_end: int) -> tuple[int, int]:
    values = [grid.cell_value(r, col) for r in range(row_start, row_end + 1)]
    non_empty = [v for v in values if _ne(v)]
    numeric = sum(1 for v in non_empty if clean_number(v) is not None)
    return numeric, len(non_empty)


def _text_ratio(grid: Any, col: int, row_start: int, row_end: int) -> tuple[int, int]:
    values = [grid.cell_value(r, col) for r in range(row_start, row_end + 1)]
    non_empty = [v for v in values if _ne(v)]
    text = sum(1 for v in non_empty if _is_text(v))
    return text, len(non_empty)


def _is_label_col(grid: Any, col: int, row_start: int, row_end: int) -> bool:
    values = [grid.cell_value(r, col) for r in range(row_start, row_end + 1)]
    non_empty = [v for v in values if _ne(v)]
    labels = [v for v in non_empty if _is_label(v) and not _period_like(v)]
    return len(non_empty) >= 2 and len(labels) / max(len(non_empty), 1) >= 0.6


def _shift_data_start_after_header(
    grid: Any,
    data_start: int,
    first_value_col: int,
    max_row: int,
    max_col: int,
) -> int:
    for row in range(data_start, min(data_start + 12, max_row) + 1):
        text = _count_text(grid, row, first_value_col, max_col)
        numeric = _count_numeric(grid, row, first_value_col, max_col)
        if text < 2 or text < numeric:
            continue
        end = row
        for nxt in range(row + 1, min(row + 4, max_row) + 1):
            nxt_text = _count_text(grid, nxt, first_value_col, max_col)
            nxt_numeric = _count_numeric(grid, nxt, first_value_col, max_col)
            if nxt_text >= 1 and nxt_text >= nxt_numeric:
                end = nxt
            else:
                break
        if any(
            _count_numeric(grid, nxt, first_value_col, max_col) >= 2
            for nxt in range(end + 1, min(end + 5, max_row) + 1)
        ):
            return end + 1
    return data_start


def _nearest_year(grid: Any, rows: list[int], col: int, max_col: int) -> int | None:
    for distance in range(1, 12):
        for target in (col + distance, col - distance):
            if 1 <= target <= max_col:
                for row in rows:
                    value = _header_left(grid, row, target)
                    if value is None:
                        continue
                    match = YEAR_RE.search(str(value))
                    if match:
                        return int(match.group(1))
    return None


def _date_for_col(grid: Any, rows: list[int], col: int, max_col: int) -> tuple[str | None, str]:
    raw_values: list[str] = []
    for row in rows:
        value = _header_left(grid, row, col)
        if _ne(value):
            text = str(value).strip()
            if text not in raw_values:
                raw_values.append(text)
    raw = " | ".join(raw_values)
    parsed = parse_period(raw)
    if parsed:
        return parsed, raw
    year = _nearest_year(grid, rows, col, max_col)
    parsed = parse_period(raw, default_year=year)
    if parsed:
        if year and raw and not YEAR_RE.search(raw):
            raw = f"{year} | {raw}"
        return parsed, raw
    for value in raw_values:
        parsed = parse_period(value, default_year=year)
        if parsed:
            return parsed, raw
    return None, raw


def _period_like(value: Any) -> bool:
    if not _ne(value):
        return False
    text = str(value).upper().strip()
    if parse_period(value):
        return True
    return bool(
        re.fullmatch(r"T\s*[1-4]", text)
        or TRIM_RE.search(text)
        or re.fullmatch(r"(I{1,3}|IV|1|2|3|4)", text)
    )


@dataclass
class Layout:
    mode: str
    max_row: int
    max_col: int
    data_start: int
    data_end: int
    data_start_col: int
    data_end_col: int
    date_rows: list[int] = field(default_factory=list)
    date_col: int | None = None
    year_col: int | None = None
    header_rows: list[int] = field(default_factory=list)
    label_cols: list[int] = field(default_factory=list)
    constant_date: str | None = None


def _detect_wide(grid: Any, max_row: int, max_col: int) -> Layout | None:
    candidates: list[tuple[int, int, list[int]]] = []
    for row in range(1, min(max_row, 45) + 1):
        date_cols = []
        for col in range(1, max_col + 1):
            value = _header_detection(grid, row, col)
            if parse_period(value):
                date_cols.append(col)
        if len(date_cols) >= 3:
            candidates.append((row, len(date_cols), date_cols))
    if not candidates:
        return None

    chosen = max(candidates, key=lambda item: (item[1], -item[0]))[0]
    date_rows = [chosen]
    while date_rows[0] > 1:
        previous = date_rows[0] - 1
        count = sum(1 for c in range(1, max_col + 1) if _period_like(_header_detection(grid, previous, c)))
        if count >= 2:
            date_rows.insert(0, previous)
        else:
            break
    while date_rows[-1] < min(max_row, 45):
        following = date_rows[-1] + 1
        count = sum(1 for c in range(1, max_col + 1) if _period_like(_header_detection(grid, following, c)))
        if count >= 3:
            date_rows.append(following)
        else:
            break

    date_map = {c: _date_for_col(grid, date_rows, c, max_col) for c in range(1, max_col + 1)}
    valid_dates = [c for c, (iso, _) in date_map.items() if iso]
    if len(valid_dates) < 3:
        return None

    data_start = None
    threshold = max(2, int(0.12 * len(valid_dates)))
    for row in range(date_rows[-1] + 1, min(max_row, date_rows[-1] + 40) + 1):
        if _count_numeric(grid, row, min(valid_dates), max(valid_dates)) >= threshold:
            data_start = row
            break
    if not data_start:
        return None

    sample_end = min(max_row, data_start + 40)
    series_rows = [
        row
        for row in range(min(date_rows), data_start)
        if row not in date_rows
        and _count_text(grid, row, min(valid_dates), max_col) >= 1
        and _count_text(grid, row, min(valid_dates), max_col)
        >= _count_numeric(grid, row, min(valid_dates), max_col)
    ]

    label_cols = [
        col
        for col in range(1, min(valid_dates))
        if _is_label_col(grid, col, data_start, sample_end)
    ]

    first_data_col = None
    for col in range(1, min(valid_dates) + 2):
        if col in label_cols:
            continue
        numeric, _ = _numeric_ratio(grid, col, data_start, sample_end)
        if numeric >= 2:
            first_data_col = col
            break
    first_data_col = first_data_col or min(valid_dates)

    last_data_col = first_data_col
    for col in range(first_data_col, max_col + 1):
        numeric, _ = _numeric_ratio(grid, col, data_start, sample_end)
        if numeric >= 1:
            last_data_col = col

    last_data_row = data_start
    for row in range(data_start, max_row + 1):
        if _count_numeric(grid, row, first_data_col, last_data_col) >= 2:
            last_data_row = row

    return Layout(
        mode="wide",
        max_row=max_row,
        max_col=max_col,
        data_start=data_start,
        data_end=last_data_row,
        data_start_col=first_data_col,
        data_end_col=last_data_col,
        date_rows=date_rows,
        header_rows=series_rows,
        label_cols=label_cols,
    )


def _detect_long(grid: Any, max_row: int, max_col: int) -> Layout | None:
    candidates: list[tuple[int, int, int, bool, int]] = []
    scan_end = min(max_row, 90)
    for col in range(1, min(max_col, 10) + 1):
        count = 0
        best_specificity = 0
        keyword = False
        for row in range(2, scan_end + 1):
            value = grid.cell_value(row, col)
            parsed = parse_period(value)
            if parsed:
                count += 1
                best_specificity = max(best_specificity, _specificity(value, parsed))
            if _ne(value) and re.search(
                r"(SEM|MES|TRIM|FECHA|PERIODO|PERÍODO|AÑO|ANIO)", str(value), re.IGNORECASE
            ):
                keyword = True
        numeric, non_empty = _numeric_ratio(grid, col, 2, scan_end)
        text, _ = _text_ratio(grid, col, 2, scan_end)
        if count >= 3 and (count >= 0.25 * max(non_empty, 1) or keyword):
            candidates.append((best_specificity, count, col, keyword, text))
    if not candidates:
        return None

    candidates.sort(key=lambda item: (item[0], item[1], item[3], -item[2]), reverse=True)
    _, _, date_col, _, _ = candidates[0]

    year_col = None
    sample_dates = [
        grid.cell_value(row, date_col)
        for row in range(2, min(scan_end, 60) + 1)
        if parse_period(grid.cell_value(row, date_col))
    ]
    lacks_year = any(not YEAR_RE.search(str(v)) for v in sample_dates) if sample_dates else False
    if lacks_year:
        for _, _, candidate_col, _, _ in candidates[1:]:
            if candidate_col != date_col:
                values = [grid.cell_value(r, candidate_col) for r in range(2, min(scan_end, 60) + 1)]
                if sum(1 for v in values if YEAR_RE.search(str(v))) >= 3:
                    year_col = candidate_col
                    break

    value_cols = []
    for col in range(1, max_col + 1):
        if col in (date_col, year_col):
            continue
        numeric, _ = _numeric_ratio(grid, col, 2, min(scan_end, 60))
        if numeric >= 2:
            value_cols.append(col)
    if not value_cols:
        return None
    first_value_col = min(value_cols)

    data_start = None
    for row in range(4, min(max_row, 100) + 1):
        if _count_numeric(grid, row, first_value_col, max_col) >= 3:
            data_start = row
            break
    if not data_start:
        return None

    data_start = _shift_data_start_after_header(
        grid, data_start, first_value_col, max_row, max_col
    )

    header_rows = []
    for row in range(1, data_start):
        text = _count_text(grid, row, first_value_col, max_col)
        numeric = _count_numeric(grid, row, first_value_col, max_col)
        minimum = 3 if max_col > 12 else 2
        if text >= minimum and text >= numeric:
            header_rows.append(row)
    header_rows = header_rows[-4:]

    sample_end = min(max_row, data_start + 40)
    label_cols = [
        col
        for col in range(1, first_value_col)
        if col not in (date_col, year_col) and _is_label_col(grid, col, data_start, sample_end)
    ]

    last_data_col = first_value_col
    for col in range(first_value_col, max_col + 1):
        numeric, _ = _numeric_ratio(grid, col, data_start, sample_end)
        if numeric >= 1:
            last_data_col = col

    last_data_row = data_start
    for row in range(data_start, max_row + 1):
        if _count_numeric(grid, row, first_value_col, last_data_col) >= 2:
            last_data_row = row

    return Layout(
        mode="long",
        max_row=max_row,
        max_col=max_col,
        data_start=data_start,
        data_end=last_data_row,
        data_start_col=first_value_col,
        data_end_col=last_data_col,
        date_col=date_col,
        year_col=year_col,
        header_rows=header_rows,
        label_cols=label_cols,
    )


def _detect_category(grid: Any, max_row: int, max_col: int) -> Layout | None:
    constant = None
    best_specificity = 0
    for row in range(1, min(max_row, 12) + 1):
        for col in range(1, min(max_col, 12) + 1):
            raw = grid.cell_value(row, col)
            parsed = parse_period(raw)
            if parsed:
                specificity = _specificity(raw, parsed)
                if specificity > best_specificity:
                    best_specificity = specificity
                    constant = parsed

    header_row = None
    for row in range(1, min(max_row, 30) + 1):
        text = _count_text(grid, row, 1, max_col)
        numeric = _count_numeric(grid, row, 1, max_col)
        if text >= 3 and text >= numeric:
            header_row = row
            break
    if not header_row:
        return None

    header_rows = [header_row]
    for row in range(header_row + 1, min(max_row, header_row + 4) + 1):
        text = _count_text(grid, row, 1, max_col)
        numeric = _count_numeric(grid, row, 1, max_col)
        if numeric >= 3:
            break
        if text >= 2:
            header_rows.append(row)
        elif text == 0:
            break

    data_start = None
    for row in range(header_rows[-1] + 1, min(max_row, header_rows[-1] + 25) + 1):
        if _count_numeric(grid, row, 1, max_col) >= 3:
            data_start = row
            break
    if not data_start:
        return None

    sample_end = min(max_row, data_start + 40)
    first_data_col = None
    for col in range(1, max_col + 1):
        numeric, _ = _numeric_ratio(grid, col, data_start, sample_end)
        if numeric >= 2:
            first_data_col = col
            break
    if not first_data_col:
        return None

    label_cols = [
        col
        for col in range(1, first_data_col)
        if _is_label_col(grid, col, data_start, sample_end)
        or (col == 1 and _count_text(grid, col, data_start, sample_end) >= 2)
    ]

    last_data_col = first_data_col
    for col in range(first_data_col, max_col + 1):
        numeric, _ = _numeric_ratio(grid, col, data_start, sample_end)
        if numeric >= 1:
            last_data_col = col

    last_data_row = data_start
    for row in range(data_start, max_row + 1):
        if _count_numeric(grid, row, first_data_col, last_data_col) >= 2:
            last_data_row = row

    return Layout(
        mode="category",
        max_row=max_row,
        max_col=max_col,
        data_start=data_start,
        data_end=last_data_row,
        data_start_col=first_data_col,
        data_end_col=last_data_col,
        header_rows=header_rows,
        label_cols=label_cols,
        constant_date=constant,
    )


def detect_layout(grid: Any) -> Layout | None:
    max_row, max_col = _effective_bounds(grid)
    if max_row < 4 or max_col < 4:
        return None
    wide = _detect_wide(grid, max_row, max_col)
    if wide and wide.date_rows and wide.data_end_col - wide.data_start_col >= 10:
        return wide
    for detector in (_detect_long, _detect_wide, _detect_category):
        layout = detector(grid, max_row, max_col)
        if layout:
            return layout
    return None


def _detect_unit(grid: Any, max_col: int) -> str:
    pattern = re.compile(
        r"\(([^)]*(?:En\s+|Porcentajes?|Millones|Miles|Bs\.?|USD|Dólares|Dolares|"
        r"Índice|Indice)[^)]*)\)",
        re.IGNORECASE,
    )
    for row in range(1, min(grid.max_row, 14) + 1):
        for col in range(1, min(max_col, 8) + 1):
            value = grid.cell_value(row, col)
            if not _ne(value):
                continue
            match = pattern.search(str(value))
            if match:
                return match.group(1).strip()
    return ""


def _section_label(
    grid: Any,
    row: int,
    header_end: int,
    label_cols: list[int],
    data_start_col: int,
    data_end_col: int,
) -> str:
    for current in range(row - 1, max(header_end, row - 25), -1):
        if _count_numeric(grid, current, data_start_col, data_end_col) > 0:
            continue
        values = [
            str(grid.cell_value(current, col)).strip()
            for col in label_cols
            if _is_label(grid.cell_value(current, col))
        ]
        if values:
            return " | ".join(dict.fromkeys(values))
    return ""


def _series_for(ctx: Any, header_rows: list[int], label_cols: list[int]) -> str:
    parts: list[str] = []
    for row in header_rows:
        value = ctx.row_ffill(row)
        if _is_label(value):
            text = str(value).strip()
            if text not in parts:
                parts.append(text)
    for col in label_cols:
        value = ctx.col_ffill(col)
        if _is_label(value):
            text = str(value).strip()
            if text not in parts:
                parts.append(text)
    parts = [
        part
        for part in parts
        if not _period_like(part) and not DATE_HEADER_RE.match(part.strip())
    ]
    if not parts:
        return f"COL_{ctx.col}"
    return " | ".join(parts)


def _is_form_sheet(grid: Any, max_col: int) -> bool:
    numeric = 0
    for row in range(1, min(grid.max_row, 80) + 1):
        text = " ".join(
            str(grid.cell_value(row, c))
            for c in range(1, min(max_col, 10) + 1)
            if _ne(grid.cell_value(row, c))
        )
        if FORM_WORDS.search(text):
            return True
        numeric += _count_numeric(grid, row, 1, max_col)
    return numeric < 8


def extract_sheet(
    grid: Any,
    familia: str,
    archivo: str,
    hoja: str,
    publicacion: str,
) -> tuple[pd.DataFrame | None, str]:
    layout = detect_layout(grid)
    if not layout:
        return None, "sin_layout"
    if _is_form_sheet(grid, layout.max_col):
        return None, "formulario"

    flattener = TableFlattener(f"{familia}:{archivo}:{hoja}").from_grid(grid)
    flattener.data_bounds(
        layout.data_start,
        layout.data_start_col,
        layout.data_end,
        layout.data_end_col,
    )

    if layout.mode == "wide":
        date_map = {
            col: _date_for_col(grid, layout.date_rows, col, layout.max_col)
            for col in range(layout.data_start_col, layout.data_end_col + 1)
        }
        fallback = publicacion or layout.constant_date or ""

        def fecha_wide(ctx: Any) -> str:
            parsed, raw = date_map.get(ctx.col, (None, ""))
            return parsed or fallback or raw or f"F{ctx.row}"

        def periodo_wide(ctx: Any) -> str:
            parsed, raw = date_map.get(ctx.col, (None, ""))
            return raw or parsed or fallback

        flattener.bind("fecha", fecha_wide)
        flattener.bind("periodo", periodo_wide)

        def serie_fn(ctx: Any) -> str:
            return _series_for(ctx, layout.header_rows, layout.label_cols)

    elif layout.mode == "long":
        date_cache: dict[int, tuple[str | None, str]] = {}

        def fecha_long(ctx: Any) -> str:
            row = ctx.row
            if row not in date_cache:
                raw = _last_period_above(ctx.grid, ctx.row, layout.date_col) if layout.date_col else None
                default_year = None
                if layout.year_col:
                    year_raw = _last_period_above(ctx.grid, ctx.row, layout.year_col)
                    match = YEAR_RE.search(str(year_raw or ""))
                    default_year = int(match.group(1)) if match else None
                parsed = parse_period(raw, default_year=default_year)
                if parsed is None and default_year:
                    raw = str(default_year)
                    parsed = str(default_year)
                date_cache[row] = (parsed, str(raw or ""))
            parsed, raw = date_cache[row]
            return parsed or publicacion or raw or f"F{row}"

        def periodo_long(ctx: Any) -> str:
            row = ctx.row
            if row not in date_cache:
                raw = _last_period_above(ctx.grid, ctx.row, layout.date_col) if layout.date_col else None
                default_year = None
                if layout.year_col:
                    year_raw = _last_period_above(ctx.grid, ctx.row, layout.year_col)
                    match = YEAR_RE.search(str(year_raw or ""))
                    default_year = int(match.group(1)) if match else None
                parsed = parse_period(raw, default_year=default_year)
                if parsed is None and default_year:
                    raw = str(default_year)
                    parsed = str(default_year)
                date_cache[row] = (parsed, str(raw or ""))
            parsed, raw = date_cache[row]
            return raw or parsed or publicacion

        flattener.bind("fecha", fecha_long)
        flattener.bind("periodo", periodo_long)

        def serie_fn(ctx: Any) -> str:
            parts = _series_for(ctx, layout.header_rows, layout.label_cols).split(" | ")
            if layout.date_col:
                value = ctx.col_val(layout.date_col)
                if _is_label(value) and not _period_like(value):
                    text = str(value).strip()
                    if text not in parts:
                        parts.append(text)
            header = _column_up(grid, ctx.row - 1, ctx.col)
            if (
                _is_text(header)
                and not _period_like(header)
                and not DATE_HEADER_RE.match(str(header).strip())
            ):
                text = str(header).strip()
                if text not in parts:
                    parts.append(text)
            return " | ".join(part for part in parts if part and not part.startswith("COL_"))

    else:
        constant = layout.constant_date or publicacion or ""

        flattener.bind("fecha", constant or f"P{layout.data_start}")
        flattener.bind("periodo", constant or f"P{layout.data_start}")

        section_cache: dict[int, str] = {}

        def serie_fn(ctx: Any) -> str:
            parts = _series_for(ctx, layout.header_rows, layout.label_cols).split(" | ")
            if ctx.row not in section_cache:
                section_cache[ctx.row] = _section_label(
                    grid,
                    ctx.row,
                    max(layout.header_rows),
                    layout.label_cols,
                    layout.data_start_col,
                    layout.data_end_col,
                )
            group = section_cache[ctx.row]
            if group:
                for part in group.split(" | "):
                    if part and part not in parts:
                        parts.append(part)
            return " | ".join(parts)

    flattener.bind("serie", serie_fn)

    def serie_id(ctx: Any) -> str:
        serie = serie_fn(ctx).strip()
        if not serie:
            return ""
        return f"{to_slug(familia)}__{to_slug(serie)}"

    flattener.bind("serie_id", serie_id)
    flattener.primary_key("serie_id", "fecha")
    flattener.on_duplicate("keep_last")

    try:
        frame = flattener.to_dataframe(include_coords=True)
    except Exception as exc:  # noqa: BLE001
        return None, f"error:{type(exc).__name__}:{exc}"

    if frame.empty:
        return None, "sin_datos"

    frame = frame.rename(columns={"_row": "fila", "_col": "columna"})
    frame["familia"] = familia
    frame["archivo"] = archivo
    frame["hoja"] = hoja
    frame["unidad"] = _detect_unit(grid, layout.max_col) or DEFAULT_UNITS.get(familia, "")
    frame["publicacion"] = publicacion
    frame["metodo"] = layout.mode
    frame["serie"] = frame["serie"].fillna("").astype(str)
    frame["periodo"] = frame["periodo"].fillna("").astype(str)
    frame["fecha"] = frame["fecha"].fillna("").astype(str)
    frame["serie_id"] = frame["serie_id"].fillna("").astype(str)
    frame = frame[frame["serie_id"] != ""]
    frame = frame[frame["serie"].str.strip() != ""]
    frame = frame[
        ~frame["serie"].str.contains(r"(?:al trimestre|eje derecho)", case=False, regex=True)
    ]
    frame = frame[frame["valor"].notna()]
    if len(frame) < 8:
        return None, "muy_pocos_valores"
    columns = [
        "familia",
        "archivo",
        "hoja",
        "serie_id",
        "serie",
        "fecha",
        "periodo",
        "valor",
        "unidad",
        "publicacion",
        "metodo",
        "fila",
        "columna",
    ]
    return frame[columns].copy(), "ok"


def ensure_xlsx(path: Path, cache_dir: Path) -> Path:
    suffix = path.suffix.lower()
    if suffix in {".xlsx", ".xlsm"}:
        return path
    stat = path.stat()
    key = hashlib.sha1(f"{path}|{stat.st_mtime_ns}|{stat.st_size}".encode()).hexdigest()[:16]
    out_dir = cache_dir / key
    target = out_dir / f"{path.stem}.xlsx"
    if target.exists():
        return target
    out_dir.mkdir(parents=True, exist_ok=True)
    profile = Path("/tmp/bcb_lo_profile")
    command = [
        "soffice",
        f"-env:UserInstallation=file://{profile}",
        "--headless",
        "--convert-to",
        "xlsx",
        "--outdir",
        str(out_dir),
        str(path),
    ]
    result = subprocess.run(command, capture_output=True, text=True, timeout=240, check=False)
    if result.returncode != 0 or not target.exists():
        candidates = list(out_dir.glob("*.xlsx"))
        if candidates:
            return candidates[0]
        raise RuntimeError((result.stderr or result.stdout or "LibreOffice no generó XLSX").strip())
    return target


def _read_catalog(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


class FamilyOutput:
    def __init__(self, out_dir: Path, resume: bool, keep_parts: bool) -> None:
        self.out_dir = out_dir
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.parts_dir = out_dir / "partes"
        if keep_parts:
            self.parts_dir.mkdir(parents=True, exist_ok=True)
        self.keep_parts = keep_parts
        self.archivos_path = out_dir / "archivos.csv"
        self.datos_path = out_dir / "datos.csv"
        self.archivos: dict[tuple[str, str], dict[str, str]] = {}
        if resume and self.archivos_path.exists():
            for row in _read_catalog(self.archivos_path):
                self.archivos[(row.get("archivo", ""), row.get("hoja", ""))] = row
        self.frame: pd.DataFrame | None = None
        self.buffer: list[pd.DataFrame] = []
        if resume and self.datos_path.exists():
            self.frame = pd.read_csv(self.datos_path, dtype={"serie_id": str, "fecha": str})
        self.rows = 0

    def done(self, archivo: str, hoja: str) -> bool:
        row = self.archivos.get((archivo, hoja))
        return bool(row and row.get("estado") == "ok")

    def record(self, archivo: str, hoja: str, estado: str, filas: int, metodo: str, error: str = "") -> None:
        self.archivos[(archivo, hoja)] = {
            "archivo": archivo,
            "hoja": hoja,
            "estado": estado,
            "filas": str(filas),
            "metodo": metodo,
            "error": error,
        }

    def add(self, frame: pd.DataFrame, archivo: str, hoja: str, keep_part: bool = False) -> None:
        if keep_part and self.keep_parts:
            safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", f"{archivo}__{hoja}")[-180:]
            frame.to_csv(self.parts_dir / f"{safe}.csv", index=False)
        self.buffer.append(frame)
        self.rows += len(frame)
        if sum(len(part) for part in self.buffer) >= 200_000:
            self.flush()

    def flush(self) -> None:
        if not self.buffer:
            return
        chunk = pd.concat(self.buffer, ignore_index=True)
        self.buffer.clear()
        if self.frame is None:
            self.frame = chunk
        else:
            self.frame = pd.concat([self.frame, chunk], ignore_index=True)
        self.frame["_clave_fecha"] = (
            self.frame["fecha"].fillna("").astype(str).where(
                self.frame["fecha"].fillna("").astype(str).str.len() > 0,
                self.frame["periodo"].fillna("").astype(str),
            )
        )
        self.frame["_clave_fecha"] = self.frame["_clave_fecha"].where(
            self.frame["_clave_fecha"].str.len() > 0,
            self.frame["publicacion"].fillna("").astype(str),
        )
        self.frame["_clave_fecha"] = self.frame["_clave_fecha"].where(
            self.frame["_clave_fecha"].str.len() > 0,
            self.frame["archivo"].astype(str)
            + ":"
            + self.frame["hoja"].astype(str)
            + ":"
            + self.frame["fila"].astype(str)
            + ":"
            + self.frame["columna"].astype(str),
        )
        self.frame = self.frame.sort_values(
            ["serie_id", "_clave_fecha", "publicacion"]
        ).drop_duplicates(["serie_id", "_clave_fecha"], keep="last")

    def finalize(self) -> pd.DataFrame:
        self.flush()
        if self.frame is None or self.frame.empty:
            self.frame = pd.DataFrame()
        frame = self.frame.drop(columns=["_clave_fecha"], errors="ignore")
        if not frame.empty:
            frame = frame.sort_values(["serie_id", "fecha", "publicacion"]).reset_index(drop=True)
        frame.to_csv(self.datos_path, index=False)
        if not frame.empty:
            series = (
                frame.groupby("serie_id", dropna=False)
                .agg(
                    familia=("familia", "first"),
                    serie=("serie", "first"),
                    unidad=("unidad", "first"),
                    primera_fecha=("fecha", "min"),
                    ultima_fecha=("fecha", "max"),
                    n_observaciones=("valor", "size"),
                    n_archivos=("archivo", "nunique"),
                    publicacion_ultima=("publicacion", "max"),
                )
                .reset_index()
            )
            series.to_csv(self.out_dir / "series.csv", index=False)
        else:
            pd.DataFrame(
                columns=[
                    "serie_id",
                    "familia",
                    "serie",
                    "unidad",
                    "primera_fecha",
                    "ultima_fecha",
                    "n_observaciones",
                    "n_archivos",
                    "publicacion_ultima",
                ]
            ).to_csv(self.out_dir / "series.csv", index=False)
        rows = sorted(self.archivos.values(), key=lambda r: (r["archivo"], r["hoja"]))
        with self.archivos_path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(
                fh,
                fieldnames=["archivo", "hoja", "estado", "filas", "metodo", "error"],
            )
            writer.writeheader()
            writer.writerows(rows)
        return frame


def _select_files(
    catalog: list[dict[str, str]],
    familias: set[str] | None,
    excluir: set[str],
    max_archivos: int,
) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in catalog:
        if row.get("procesar") != "si":
            continue
        family = row.get("familia", "")
        if familias and family not in familias:
            continue
        if family in excluir:
            continue
        grouped.setdefault(family, []).append(row)
    for family, rows in grouped.items():
        rows.sort(key=lambda r: (r.get("publicacion", ""), r.get("relpath", "")))
        if max_archivos:
            grouped[family] = rows[:max_archivos]
    return grouped


def _process_family(
    family: str,
    files: list[dict[str, str]],
    docs_dir: Path,
    out_root: Path,
    cache_dir: Path,
    resume: bool,
    force: bool,
    convertir: bool,
    keep_parts: bool,
    verbose: bool,
) -> dict[str, Any]:
    out_dir = out_root / family
    if force and out_dir.exists():
        shutil.rmtree(out_dir)
    output = FamilyOutput(out_dir, resume=resume and not force, keep_parts=keep_parts)
    processed = 0
    errors = 0
    for index, row in enumerate(files, start=1):
        relpath = row.get("relpath", "")
        archivo = row.get("archivo", "")
        source = docs_dir / relpath
        if not source.exists():
            output.record(archivo, "", "error", 0, "", "archivo no existe")
            errors += 1
            continue
        try:
            workbook_path = ensure_xlsx(source, cache_dir) if convertir else source
            if workbook_path.suffix.lower() not in {".xlsx", ".xlsm"}:
                output.record(archivo, "", "omitido", 0, "", "requiere conversion")
                continue
            workbook = WorkbookGrid.from_excel(workbook_path)
        except Exception as exc:  # noqa: BLE001
            output.record(archivo, "", "error", 0, "", f"{type(exc).__name__}: {exc}")
            errors += 1
            if verbose:
                print(f"  ! {relpath}: {type(exc).__name__}: {exc}")
            continue

        if verbose:
            print(f"  [{index}/{len(files)}] {relpath}")
        for sheet_name in workbook.sheet_names:
            if SKIP_SHEET.search(sheet_name):
                output.record(archivo, sheet_name, "omitido", 0, "", "hoja no tabular")
                continue
            if output.done(archivo, sheet_name):
                continue
            try:
                frame, status = extract_sheet(
                    workbook.sheet(sheet_name),
                    family,
                    relpath,
                    sheet_name,
                    row.get("publicacion", ""),
                )
            except Exception as exc:  # noqa: BLE001
                frame = None
                status = f"error:{type(exc).__name__}:{exc}"
            if frame is None:
                output.record(archivo, sheet_name, status, 0, "", status if status.startswith("error") else "")
                if status.startswith("error"):
                    errors += 1
                continue
            metodo = str(frame["metodo"].iloc[0]) if not frame.empty else ""
            output.add(frame, relpath, sheet_name, keep_part=True)
            output.record(archivo, sheet_name, "ok", len(frame), metodo)
            processed += 1

    frame = output.finalize()
    summary = {
        "familia": family,
        "archivos_entrada": len(files),
        "hojas_ok": processed,
        "filas": len(frame),
        "series": int(frame["serie_id"].nunique()) if not frame.empty else 0,
        "errores": errors,
    }
    (out_dir / "resumen.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Normaliza documentos BCB en familias tidy.")
    parser.add_argument("--docs", type=Path, default=Path(__file__).resolve().parents[3] / "data" / "documentos")
    parser.add_argument("--catalogo", type=Path, default=Path(__file__).resolve().parents[3] / "data" / "familias" / "catalogo.csv")
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parents[3] / "data" / "familias")
    parser.add_argument("--familias", default="")
    parser.add_argument("--excluir-familias", default="")
    parser.add_argument("--max-archivos", type=int, default=0)
    parser.add_argument("--min-valores", type=int, default=8)
    parser.add_argument("--cache", type=Path, default=Path(__file__).resolve().parents[3] / "data" / "familias" / ".cache")
    parser.add_argument("--sin-conversion", action="store_true")
    parser.add_argument("--no-resume", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--guardar-partes", action="store_true")
    parser.add_argument("--reclasificar", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if args.reclasificar or not args.catalogo.exists():
        catalog, _ = build_catalog(args.docs)
        args.catalogo.parent.mkdir(parents=True, exist_ok=True)
        from bcb_families import write_catalog

        write_catalog(catalog, args.catalogo)
    else:
        catalog = _read_catalog(args.catalogo)

    familias = {f.strip() for f in args.familias.split(",") if f.strip()} or None
    excluir = {f.strip() for f in args.excluir_familias.split(",") if f.strip()}
    grouped = _select_files(catalog, familias, excluir, args.max_archivos)
    if args.dry_run:
        for family, rows in sorted(grouped.items()):
            print(f"{family}: {len(rows)} archivos")
            for row in rows[:3]:
                print(f"  - {row['relpath']}")
        return 0

    args.out.mkdir(parents=True, exist_ok=True)
    args.cache.mkdir(parents=True, exist_ok=True)
    summaries = []
    for family, rows in sorted(grouped.items()):
        print(f"[{family}] {len(rows)} archivos")
        summary = _process_family(
            family,
            rows,
            args.docs,
            args.out,
            args.cache,
            resume=not args.no_resume,
            force=args.force,
            convertir=not args.sin_conversion,
            keep_parts=args.guardar_partes,
            verbose=args.verbose,
        )
        print(
            f"  -> {summary['filas']:,} filas, {summary['series']:,} series, "
            f"{summary['errores']} errores"
        )
        summaries.append(summary)

    series_frames = []
    for summary in summaries:
        path = args.out / summary["familia"] / "series.csv"
        if path.exists():
            series_frames.append(pd.read_csv(path, dtype={"serie_id": str}))
    if series_frames:
        pd.concat(series_frames, ignore_index=True).to_csv(
            args.out / "catalogo_series.csv", index=False
        )
    (args.out / "resumen_familias_datos.json").write_text(
        json.dumps(
            {
                "familias": summaries,
                "total_filas": sum(s["filas"] for s in summaries),
                "total_series": sum(s["series"] for s in summaries),
                "total_errores": sum(s["errores"] for s in summaries),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
