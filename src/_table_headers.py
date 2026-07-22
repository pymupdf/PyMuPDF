"""
Copyright (C) 2023 Artifex Software, Inc.

This file is part of PyMuPDF.

PyMuPDF is free software: you can redistribute it and/or modify it under the
terms of the GNU Affero General Public License as published by the Free
Software Foundation, either version 3 of the License, or (at your option)
any later version.

PyMuPDF is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for more
details.

You should have received a copy of the GNU Affero General Public License
along with MuPDF. If not, see <https://www.gnu.org/licenses/agpl-3.0.en.html>

Alternative licensing terms are available from the licensor.
For commercial licensing, see <https://www.artifex.com/> or contact
Artifex Software, Inc., 39 Mesa Street, Suite 108A, San Francisco,
CA 94129, USA, for further information.

---------------------------------------------------------------------

PyMuPDF table header detection and HTML serialization (opt-in extension).

Pure text-grid module (no pymupdf import): the header-region rules operate on a
row-major ``[[cell text]]`` grid, and the serializer turns a tagged placement
grid into an HTML ``<table>``. Used only by find_tables(refine=True) (via
pymupdf.table) and Table.to_html(); never runs on the default detection path.
"""
from __future__ import annotations
from dataclasses import dataclass
from statistics import mean
from typing import Any
import re



_TOKEN_RE = re.compile(r"[A-Za-z]+|\d+(?:[.,:/-]\d+)*|[%$€£¥()–—-]+")
_MONTH_RE = re.compile(
    r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?\b",
    re.IGNORECASE,
)
_MONEY_RE = re.compile(r"(?:[$€£¥]\s*[-(]?\d|(?:usd|eur|gbp|jpy)\b)", re.IGNORECASE)
_PERCENT_RE = re.compile(r"[-(]?\d+(?:\.\d+)?\s*%")
_YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")
_CODE_RE = re.compile(r"^(?=.*[A-Za-z])(?=.*\d)[A-Za-z0-9][A-Za-z0-9._/# -]{0,24}$")
_RANGE_RE = re.compile(r"(?:>=|<=|<|>| thru | through | to |\b\d+\s*[-–]\s*\d+\b)", re.IGNORECASE)
_DOTTED_ENUM_RE = re.compile(r"^\s*\d+(?:\.\d+){2,}\b")
_REF_TOKEN_RE = re.compile(r"[\[(]\s*\d{1,2}\s*[\])]|\[\s*\d{1,2}\s*\)")
_REF_FORMULA_ALLOWED_RE = re.compile(r"^[\s\d\[\]\(\)=+\-*/xX.]+$")
_UNIT_ROW_TERMS = ("in million", "in thousand", "in billion", "$ in", "usd", "'000", "%")

VALUE_TYPES = {"number", "money", "percent"}
LABEL_TYPES = {"text_label", "long_text", "code_id", "date_period", "unit"}


def count_alpha(text: str) -> int:
    return sum(1 for char in text if char.isalpha())


def count_digit(text: str) -> int:
    return sum(1 for char in text if char.isdigit())


def tokens(text: str) -> list[str]:
    return _TOKEN_RE.findall(text)


def numeric_like(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    alpha = count_alpha(stripped)
    digit = count_digit(stripped)
    if digit == 0:
        return False
    if _MONTH_RE.search(stripped):
        return False
    return alpha / max(1, alpha + digit) <= 0.30


def date_or_period_like(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    return bool(_MONTH_RE.search(stripped) or re.search(r"\b(?:q[1-4]|fy|year|month|period)\b", stripped, re.I))


def cell_type(text: str) -> str:
    stripped = " ".join(text.strip().split())
    if not stripped:
        return "empty"

    alpha = count_alpha(stripped)
    digit = count_digit(stripped)
    token_count = len(tokens(stripped))
    lowered = stripped.lower()

    if _MONEY_RE.search(stripped):
        return "money"
    if _PERCENT_RE.fullmatch(stripped) or (stripped.endswith("%") and digit > 0 and alpha == 0):
        return "percent"
    if date_or_period_like(stripped) or (_YEAR_RE.fullmatch(stripped) and token_count == 1):
        return "date_period"
    if _RANGE_RE.search(stripped) and digit > 0 and token_count <= 8:
        return "range"
    if numeric_like(stripped):
        return "number"
    if lowered in {"%", "$", "$000", "$m", "usd", "eur", "gbp", "amount", "rate", "ratio"}:
        return "unit"
    if _CODE_RE.match(stripped) and token_count <= 4:
        return "code_id"
    if alpha > 0 and digit > 0 and token_count <= 6:
        return "code_id"
    if token_count >= 8:
        return "long_text"
    return "text_label"


def cell_type_ratios(texts: list[str]) -> dict[str, float]:
    nonempty_types = [cell_type(text) for text in texts if text.strip()]
    if not nonempty_types:
        return {
            "value_type_ratio": 0.0,
            "label_type_ratio": 0.0,
            "long_text_type_ratio": 0.0,
            "code_type_ratio": 0.0,
            "date_period_type_ratio": 0.0,
            "range_type_ratio": 0.0,
        }
    total = len(nonempty_types)
    return {
        "value_type_ratio": sum(1 for item in nonempty_types if item in VALUE_TYPES) / total,
        "label_type_ratio": sum(1 for item in nonempty_types if item in LABEL_TYPES) / total,
        "long_text_type_ratio": sum(1 for item in nonempty_types if item == "long_text") / total,
        "code_type_ratio": sum(1 for item in nonempty_types if item == "code_id") / total,
        "date_period_type_ratio": sum(1 for item in nonempty_types if item == "date_period") / total,
        "range_type_ratio": sum(1 for item in nonempty_types if item == "range") / total,
    }


def row_features(texts: list[str]) -> dict[str, float]:
    nonempty = [text for text in texts if text.strip()]
    if not texts:
        return {
            "cell_count": 0.0,
            "nonempty_count": 0.0,
            "nonempty_ratio": 0.0,
            "empty_ratio": 0.0,
            "numeric_ratio": 0.0,
            "alpha_ratio": 0.0,
            "date_period_ratio": 0.0,
            "avg_tokens": 0.0,
            **cell_type_ratios([]),
        }
    return {
        "cell_count": float(len(texts)),
        "nonempty_count": float(len(nonempty)),
        "nonempty_ratio": len(nonempty) / len(texts),
        "empty_ratio": (len(texts) - len(nonempty)) / len(texts),
        "numeric_ratio": sum(1 for text in nonempty if numeric_like(text)) / max(1, len(nonempty)),
        "alpha_ratio": sum(1 for text in nonempty if count_alpha(text) > 0) / max(1, len(nonempty)),
        "date_period_ratio": sum(1 for text in nonempty if date_or_period_like(text)) / max(1, len(nonempty)),
        "avg_tokens": mean([len(tokens(text)) for text in nonempty]) if nonempty else 0.0,
        **cell_type_ratios(texts),
    }


def column_text(row: list[str], col: int) -> str:
    return row[col] if col < len(row) else ""


def row_vector(texts: list[str]) -> dict[str, float]:
    features = row_features(texts)
    first = column_text(texts, 0)
    rest = [text for text in texts[1:] if text.strip()]
    rest_types = [cell_type(text) for text in rest]
    first_nonempty = bool(first.strip())
    return {
        **features,
        "first_empty": 0.0 if first_nonempty else 1.0,
        "first_alpha": 1.0 if count_alpha(first) > 0 else 0.0,
        "first_numeric": 1.0 if numeric_like(first) else 0.0,
        "first_value_type": 1.0 if cell_type(first) in VALUE_TYPES else 0.0,
        "first_label_type": 1.0 if cell_type(first) in LABEL_TYPES else 0.0,
        "rest_numeric_ratio": sum(1 for text in rest if numeric_like(text)) / max(1, len(rest)),
        "rest_alpha_ratio": sum(1 for text in rest if count_alpha(text) > 0) / max(1, len(rest)),
        "rest_value_type_ratio": sum(1 for item in rest_types if item in VALUE_TYPES) / max(1, len(rest_types)),
        "rest_label_type_ratio": sum(1 for item in rest_types if item in LABEL_TYPES) / max(1, len(rest_types)),
        "rest_long_text_type_ratio": sum(1 for item in rest_types if item == "long_text") / max(1, len(rest_types)),
        "avg_tokens_norm": min(1.0, features["avg_tokens"] / 8.0),
    }


def header_candidate_row(row: list[str]) -> bool:
    features = row_features(row)
    if features["nonempty_count"] == 0:
        return False
    short_or_sparse = features["avg_tokens"] <= 6.0 or features["empty_ratio"] >= 0.20
    return bool(short_or_sparse)


def grouped_header_scaffold(row: list[str]) -> bool:
    features = row_features(row)
    if features["cell_count"] == 0:
        return False
    texts = [text.strip() for text in row]
    nonempty = [text for text in texts if text]
    unique_nonempty = {text.lower() for text in nonempty}
    repeated_labels = len(nonempty) >= 3 and len(unique_nonempty) <= max(1, len(nonempty) // 2)
    sparse_labels = features["empty_ratio"] >= 0.20 or features["nonempty_ratio"] <= 0.70
    return bool(sparse_labels or repeated_labels)


def data_row_like(row: list[str]) -> bool:
    vector = row_vector(row)
    return bool(
        vector["first_alpha"] > 0
        and vector["first_numeric"] == 0
        and vector["rest_numeric_ratio"] >= 0.35
        and vector["numeric_ratio"] >= 0.25
    )


def dense_numeric_row_like(row: list[str]) -> bool:
    vector = row_vector(row)
    return bool(vector["numeric_ratio"] >= 0.70 and vector["alpha_ratio"] <= 0.35)


def money_or_percent_heavy(row: list[str]) -> bool:
    types = [cell_type(text) for text in row if text.strip()]
    if not types:
        return False
    return sum(1 for item in types if item in {"money", "percent"}) / len(types) >= 0.25


def rest_date_period_ratio(row: list[str]) -> float:
    rest = [cell for cell in row[1:] if cell.strip()]
    if not rest:
        return 0.0
    return sum(1 for cell in rest if cell_type(cell) == "date_period") / len(rest)


def first_row_period_restore_guard(row: list[str]) -> bool:
    features = row_features(row)
    return bool(features["date_period_type_ratio"] >= 0.25 or rest_date_period_ratio(row) >= 0.35)


def first_row_date_or_unit_restore_guard(row: list[str]) -> bool:
    rest = [cell for cell in row[1:] if cell.strip()]
    if not rest:
        return False
    rest_types = [cell_type(cell) for cell in rest]
    dp_unit_ratio = sum(1 for item in rest_types if item in {"date_period", "unit"}) / len(rest_types)
    money_or_percent = any(item in {"money", "percent"} for item in rest_types)
    row_text = " ".join(row).lower()
    unit_row = any(term in row_text for term in _UNIT_ROW_TERMS)
    return bool((dp_unit_ratio >= 0.50 or unit_row) and not money_or_percent)


def first_row_restore_guards(row: list[str]) -> list[str]:
    guards = []
    if first_row_period_restore_guard(row):
        guards.append("first_row_period_restore")
    if first_row_date_or_unit_restore_guard(row):
        guards.append("first_row_date_or_unit_restore")
    return guards


def headerless_dotted_enum_guard(rows: list[list[str]]) -> bool:
    if len(rows) < 3:
        return False
    row = rows[0]
    cells = [cell.strip() for cell in row if cell and cell.strip()]
    if not cells or not _DOTTED_ENUM_RE.search(cells[0]):
        return False
    features = row_features(row)
    return bool(features["long_text_type_ratio"] >= 0.25 or features["avg_tokens"] >= 5.0)




def simple_integer_enum_header_like(row: list[str]) -> bool:
    vector = row_vector(row)
    if vector["first_label_type"] <= 0 or vector["first_value_type"] > 0:
        return False
    values = []
    for text in [text.strip() for text in row[1:] if text.strip()]:
        if not re.fullmatch(r"\d{1,2}", text):
            return False
        values.append(int(text))
    if len(values) < 2:
        return False
    ordered = values == sorted(values)
    unique = len(set(values)) == len(values)
    contiguous = max(values) - min(values) == len(values) - 1
    return bool(ordered and unique and contiguous)


def reference_formula_header_row_like(candidate: list[str], following_rows: list[list[str]]) -> bool:
    """A bracket/formula reference row under a grouped header, e.g. [3] = [1] * [2]."""
    nonempty = [text.strip() for text in candidate if text.strip()]
    if len(nonempty) < 3:
        return False
    if any(any(char.isalpha() for char in text) for text in nonempty):
        return False
    if any(("$" in text or "%" in text or "," in text) for text in nonempty):
        return False
    if not all(_REF_FORMULA_ALLOWED_RE.match(text) for text in nonempty):
        return False
    ref_cells = [text for text in nonempty if _REF_TOKEN_RE.search(text)]
    formula_cells = [text for text in nonempty if "=" in text and len(_REF_TOKEN_RE.findall(text)) >= 2]
    if len(ref_cells) / len(nonempty) < 0.75:
        return False
    if not formula_cells and len(ref_cells) < 4:
        return False
    if len(following_rows) < 2:
        return False

    following_profiles = row_profiles(following_rows)
    body_features = body_window_features_from_profiles(following_profiles, 0)
    if body_window_is_stable(body_features):
        return True
    if following_profiles[0]["section_label_row"] and len(following_profiles) >= 3:
        shifted = body_window_features_from_profiles(following_profiles, 1)
        return body_window_is_stable(shifted)
    return False


def dense_integer_axis_row_like(row: list[str]) -> bool:
    values = []
    alpha_cells = 0
    nonempty = [text.strip() for text in row if text.strip()]
    for text in nonempty:
        if re.fullmatch(r"\d{1,2}", text):
            values.append(int(text))
        elif any(char.isalpha() for char in text):
            alpha_cells += 1
        else:
            return False
    if len(values) < 5:
        return False
    unique = sorted(set(values))
    if unique != list(range(unique[0], unique[-1] + 1)):
        return False
    if unique[0] not in {0, 1}:
        return False
    if alpha_cells > max(4, len(nonempty) // 5):
        return False
    return True


def sparse_prefix_extension_prefix_like(row: list[str]) -> bool:
    features = row_features(row)
    if features["nonempty_count"] == 0:
        return False
    if features["nonempty_count"] <= 2:
        return features["alpha_ratio"] >= 0.50 or features["date_period_ratio"] >= 0.20
    if features["empty_ratio"] < 0.25:
        return False
    return bool(features["alpha_ratio"] >= 0.50 or features["date_period_ratio"] >= 0.20)


def next_header_row_value_guard(candidate: list[str], following_rows: list[list[str]]) -> bool:
    features = row_features(candidate)
    vector = row_vector(candidate)
    if features["nonempty_count"] < 2:
        return False
    if features["avg_tokens"] > 7.0 or features["long_text_type_ratio"] >= 0.35:
        return False
    if money_or_percent_heavy(candidate):
        return False
    if reference_formula_header_row_like(candidate, following_rows):
        return True
    if features["value_type_ratio"] > 0.85:
        return False

    # date_period_type_ratio recognises a bare-year header row that the
    # keyword-based date_period_ratio misses; combine them only in this guard.
    date_period_signal = max(features["date_period_ratio"], features["date_period_type_ratio"])
    has_label_signal = (
        features["alpha_ratio"] >= 0.30
        or date_period_signal >= 0.20
        or vector["first_label_type"] > 0
    )
    if not has_label_signal:
        return False

    if len(following_rows) < 2:
        return False
    following_profiles = row_profiles(following_rows)
    body_features = body_window_features_from_profiles(following_profiles, 0)
    if not body_window_is_stable(body_features):
        return False

    if features["numeric_ratio"] >= 0.50 or features["value_type_ratio"] >= 0.50:
        if vector["first_label_type"] <= 0 and date_period_signal < 0.20:
            return False
        if vector["first_value_type"] > 0:
            return False

    types = [cell_type(text) for text in candidate if text.strip()]
    type_count = len(types)
    if not type_count:
        return False
    date_type_ratio = sum(1 for item in types if item == "date_period") / type_count
    code_range_number_ratio = sum(1 for item in types if item in {"code_id", "range", "number"}) / type_count

    if features["value_type_ratio"] > 0.25:
        return simple_integer_enum_header_like(candidate)
    if code_range_number_ratio >= 0.50 and date_type_ratio < 0.30:
        return simple_integer_enum_header_like(candidate)
    return True


def sparse_prefix_conservative_extension_guard(rows: list[list[str]], top_header_rows: int) -> bool:
    if top_header_rows != 1 or len(rows) < 3:
        return False
    prefix = rows[0]
    candidate = rows[1]
    prefix_features = row_features(prefix)
    candidate_features = row_features(candidate)
    if prefix_features["empty_ratio"] < 0.50:
        return False
    if candidate_features["nonempty_count"] < 3 and candidate_features["date_period_ratio"] < 0.50:
        return False
    if not sparse_prefix_extension_prefix_like(prefix):
        return False
    if candidate_features["label_type_ratio"] < 0.50:
        return False
    if candidate_features["value_type_ratio"] >= 0.50:
        return False
    if section_label_row_like(candidate):
        return False
    following_profiles = row_profiles(rows[2:])
    body_features = body_window_features_from_profiles(following_profiles, 0)
    return body_window_is_stable(body_features)


def sparse_prefix_next_header_guard(rows: list[list[str]], top_header_rows: int) -> bool:
    """Return True when the first body row should be included as a second header row."""
    if top_header_rows < 1 or top_header_rows >= len(rows) - 1:
        return False
    return sparse_prefix_conservative_extension_guard(rows, top_header_rows)


def rowspan_leaf_header_guard(rows: list[list[str]], top_header_rows: int) -> bool:
    """Promote a leaf-label row under a sparse/grouped rowspan header scaffold.

    An empty first cell in the candidate row is the textual shadow of the row-0
    rowspan label; treat it as header only when later rows form a stable body.
    """
    if top_header_rows != 1 or len(rows) < 3:
        return False
    max_cols = max((len(row) for row in rows), default=0)
    if max_cols < 3:
        return False

    prefix = rows[0]
    candidate = rows[1]
    prefix_features = row_features(prefix)
    candidate_features = row_features(candidate)
    candidate_vector = row_vector(candidate)
    shifted_by_rowspan = len(candidate) < max_cols
    if column_text(candidate, 0).strip() and not shifted_by_rowspan:
        return False
    sparse_rowspan_prefix = len(prefix) < max_cols and len(prefix) <= max(2, int(max_cols * 0.50))
    if not (grouped_header_scaffold(prefix) or prefix_features["empty_ratio"] >= 0.35 or sparse_rowspan_prefix):
        return False
    if candidate_features["nonempty_count"] < max(2, int(max_cols * 0.45)):
        return False
    if candidate_features["value_type_ratio"] > 0.25 or candidate_features["numeric_ratio"] > 0.35:
        return False
    if candidate_vector["rest_label_type_ratio"] < 0.50 and candidate_features["alpha_ratio"] < 0.50:
        return False
    if section_label_row_like(candidate) or dense_numeric_row_like(candidate):
        return False

    following_profiles = row_profiles(rows[2:])
    body_features = body_window_features_from_profiles(following_profiles, 0)
    return body_window_is_stable(body_features)


def leading_body_record_like(row: list[str]) -> bool:
    vector = row_vector(row)
    if vector["nonempty_count"] < 2:
        return False
    first_is_label = vector["first_label_type"] > 0 and vector["first_value_type"] == 0
    rest_is_values = vector["rest_numeric_ratio"] >= 0.50 or vector["rest_value_type_ratio"] >= 0.50
    value_heavy = vector["numeric_ratio"] >= 0.35 or vector["value_type_ratio"] >= 0.35
    return bool(first_is_label and rest_is_values and value_heavy and not grouped_header_scaffold(row))


def leading_long_form_row_like(row: list[str]) -> bool:
    vector = row_vector(row)
    return bool(
        vector["nonempty_count"] >= 4
        and vector["long_text_type_ratio"] >= 0.30
        and vector["value_type_ratio"] <= 0.20
        and vector["empty_ratio"] <= 0.35
    )


def section_label_row_like(row: list[str]) -> bool:
    if len(row) < 2:
        return False
    features = row_features(row)
    first = column_text(row, 0).strip()
    nonempty = [text for text in row if text.strip()]
    first_only = bool(first and not [text for text in row[1:] if text.strip()])
    sparse_label = (
        features["nonempty_count"] <= 3
        and features["empty_ratio"] >= 0.60
        and features["alpha_ratio"] >= 0.50
    )
    return bool(first_only or (nonempty and sparse_label))


def centered_section_label_row_like(row: list[str]) -> bool:
    if not section_label_row_like(row):
        return False
    nonempty_indices = [idx for idx, text in enumerate(row) if text.strip()]
    return bool(len(nonempty_indices) == 1 and nonempty_indices[0] > 0 and len(row) >= 3)


def section_header_rows(rows: list[list[str]], top_header_rows: int) -> list[int]:
    """Return sparse section-label rows inside the detected top header prefix."""
    section_rows = []
    for row_idx, row in enumerate(rows[:top_header_rows]):
        if row_idx == 0 or not centered_section_label_row_like(row):
            continue
        nonempty = [text.strip() for text in row if text.strip()]
        if len(nonempty) != 1:
            continue
        if len(row) < 2:
            continue
        section_rows.append(row_idx)
    return section_rows


def row_profile(row: list[str], index: int) -> dict[str, Any]:
    vector = row_vector(row)
    coordinate_header_row = dense_integer_axis_row_like(row)
    body_value_row = (
        vector["first_alpha"] > 0
        and vector["first_numeric"] == 0
        and vector["rest_numeric_ratio"] >= 0.35
        and vector["numeric_ratio"] >= 0.25
    )
    body_dense_row = vector["numeric_ratio"] >= 0.70 and vector["alpha_ratio"] <= 0.35
    body_long_form_row = (
        vector["first_label_type"] > 0
        and vector["first_value_type"] == 0
        and vector["rest_long_text_type_ratio"] >= 0.50
        and vector["value_type_ratio"] <= 0.25
        and vector["empty_ratio"] <= 0.35
    )
    if coordinate_header_row:
        body_value_row = False
        body_dense_row = False
        body_long_form_row = False
    return {
        "index": index,
        "vector": vector,
        "nonempty": vector["nonempty_count"] > 0,
        "body_value_row": body_value_row,
        "body_dense_row": body_dense_row,
        "body_long_form_row": body_long_form_row,
        "body_like_row": body_value_row or body_dense_row or body_long_form_row,
        "coordinate_header_row": coordinate_header_row,
        "leading_body_record_row": leading_body_record_like(row),
        "leading_long_form_row": leading_long_form_row_like(row),
        "section_label_row": section_label_row_like(row),
        "grouped_header_scaffold": grouped_header_scaffold(row),
        "header_candidate": header_candidate_row(row),
    }


def row_profiles(rows: list[list[str]]) -> list[dict[str, Any]]:
    return [row_profile(row, index) for index, row in enumerate(rows)]


def combine_body_vectors(vectors: list[dict[str, float]]) -> dict[str, float]:
    if not vectors:
        return {
            "count": 0.0,
            "first_label_ratio": 0.0,
            "rest_numeric_ratio": 0.0,
            "numeric_ratio": 0.0,
            "alpha_ratio": 0.0,
            "avg_tokens_norm": 0.0,
            "body_row_ratio": 0.0,
            "dense_numeric_row_ratio": 0.0,
            "long_form_row_ratio": 0.0,
            "value_type_ratio": 0.0,
            "rest_value_type_ratio": 0.0,
            "rest_long_text_type_ratio": 0.0,
            "long_text_type_ratio": 0.0,
        }
    return {
        "count": float(len(vectors)),
        "first_label_ratio": sum(1 for item in vectors if item["first_label_type"] > 0 and item["first_value_type"] == 0)
        / len(vectors),
        "rest_numeric_ratio": sum(item["rest_numeric_ratio"] for item in vectors) / len(vectors),
        "numeric_ratio": sum(item["numeric_ratio"] for item in vectors) / len(vectors),
        "alpha_ratio": sum(item["alpha_ratio"] for item in vectors) / len(vectors),
        "avg_tokens_norm": sum(item["avg_tokens_norm"] for item in vectors) / len(vectors),
        "value_type_ratio": sum(item["value_type_ratio"] for item in vectors) / len(vectors),
        "rest_value_type_ratio": sum(item["rest_value_type_ratio"] for item in vectors) / len(vectors),
        "rest_long_text_type_ratio": sum(item["rest_long_text_type_ratio"] for item in vectors) / len(vectors),
        "long_text_type_ratio": sum(item["long_text_type_ratio"] for item in vectors) / len(vectors),
        "body_row_ratio": sum(
            1
            for item in vectors
            if (
                item["first_alpha"] > 0
                and item["first_numeric"] == 0
                and item["rest_numeric_ratio"] >= 0.35
                and item["numeric_ratio"] >= 0.25
            )
            or (item["numeric_ratio"] >= 0.70 and item["alpha_ratio"] <= 0.35)
        )
        / len(vectors),
        "dense_numeric_row_ratio": sum(
            1 for item in vectors if item["numeric_ratio"] >= 0.70 and item["alpha_ratio"] <= 0.35
        )
        / len(vectors),
        "long_form_row_ratio": sum(
            1
            for item in vectors
            if (
                item["first_label_type"] > 0
                and item["first_value_type"] == 0
                and item["rest_long_text_type_ratio"] >= 0.50
                and item["value_type_ratio"] <= 0.25
                and item["empty_ratio"] <= 0.35
            )
        )
        / len(vectors),
    }


def body_window_features_from_profiles(
    profiles: list[dict[str, Any]], start: int, size: int = 4
) -> dict[str, float]:
    vectors = [profile["vector"] for profile in profiles[start : start + size] if profile["nonempty"]]
    return combine_body_vectors(vectors)


def body_window_is_stable(features: dict[str, float]) -> bool:
    if features["count"] < 2:
        return False
    value_body = (
        features["body_row_ratio"] >= 0.50
        and features["rest_numeric_ratio"] >= 0.45
        and features["first_label_ratio"] >= 0.35
    )
    dense_numeric_body = (
        features["dense_numeric_row_ratio"] >= 0.50
        and features["numeric_ratio"] >= 0.60
        and features["alpha_ratio"] <= 0.55
    )
    long_form_body = (
        features["long_form_row_ratio"] >= 0.50
        and features["first_label_ratio"] >= 0.50
        and features["rest_long_text_type_ratio"] >= 0.50
        and features["value_type_ratio"] <= 0.25
        and features["numeric_ratio"] <= 0.25
    )
    return value_body or dense_numeric_body or long_form_body


def boundary_distance(header_row: list[str], body_features: dict[str, float]) -> float:
    header = row_vector(header_row)
    distance = 0.0
    distance += abs(header["numeric_ratio"] - body_features["numeric_ratio"])
    distance += abs(header["alpha_ratio"] - body_features["alpha_ratio"])
    distance += abs(header["rest_numeric_ratio"] - body_features["rest_numeric_ratio"])
    distance += abs(header["first_alpha"] - body_features["first_label_ratio"])
    distance += 0.5 * abs(header["avg_tokens_norm"] - body_features["avg_tokens_norm"])
    if header["empty_ratio"] >= 0.20:
        distance += 0.25
    return distance


def header_prefix_ok(
    rows: list[list[str]],
    profiles: list[dict[str, Any]],
    body_start: int,
    body_features: dict[str, float],
) -> bool:
    reasons = []
    if body_start <= 1:
        return True
    if body_start > 5:
        return False

    candidate_profiles = profiles[1:body_start]
    if not candidate_profiles:
        return True

    allowed_section_prefix = all(centered_section_label_row_like(rows[profile["index"]]) for profile in candidate_profiles)
    coordinate_prefix = any(profile.get("coordinate_header_row", False) for profile in candidate_profiles)
    disallowed_section_profiles = []
    for profile in candidate_profiles:
        if not profile["section_label_row"]:
            continue
        idx = int(profile["index"])
        sparse_coordinate_tail = (
            coordinate_prefix
            and idx == body_start - 1
            and profile["header_candidate"]
            and not profile["body_like_row"]
            and profile["vector"]["nonempty_count"] <= 3
            and idx > 1
            and profiles[idx - 1]["header_candidate"]
        )
        if not centered_section_label_row_like(rows[idx]) and not sparse_coordinate_tail:
            disallowed_section_profiles.append(profile)
    if any(profile["section_label_row"] for profile in candidate_profiles) and not allowed_section_prefix:
        if disallowed_section_profiles:
            reasons.append("section_label_before_body")
    elif disallowed_section_profiles:
        reasons.append("section_label_before_body")
    if any(profile["body_like_row"] for profile in candidate_profiles):
        reasons.append("body_like_row_before_body")
    if not all(profile["header_candidate"] for profile in candidate_profiles):
        reasons.append("non_header_candidate_before_body")

    previous = profiles[body_start - 2]
    last_candidate = profiles[body_start - 1]
    contrast = boundary_distance(rows[body_start - 1], body_features)
    if (
        body_start == 2
        and last_candidate["vector"]["first_empty"] == 0
        and last_candidate["vector"]["numeric_ratio"] > 0.0
        and not previous["grouped_header_scaffold"]
    ):
        reasons.append("numeric_first_row_without_group_scaffold")
    if last_candidate["body_dense_row"] and not previous["grouped_header_scaffold"]:
        reasons.append("dense_candidate_without_group_scaffold")
    if last_candidate["vector"]["alpha_ratio"] < 0.20 and not previous["grouped_header_scaffold"]:
        reasons.append("low_alpha_candidate_without_group_scaffold")
    if contrast < 1.05:
        reasons.append("weak_header_body_contrast")

    return not reasons


def body_start_candidates(
    profiles: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    candidates = []
    max_start = min(5, len(profiles) - 2)
    for start in range(1, max_start + 1):
        body_features = body_window_features_from_profiles(profiles, start)
        start_row_body_like = profiles[start]["body_like_row"]
        stable = start_row_body_like and body_window_is_stable(body_features)
        prior_body_seen = any(
            profile["body_like_row"] and not profile.get("coordinate_header_row", False)
            for profile in profiles[1:start]
        )
        candidates.append(
            {
                "body_start": start,
                "body_like": stable,
                "start_row_body_like": start_row_body_like,
                "prior_body_seen": prior_body_seen,
                "body": body_features,
            }
        )
    return candidates


def _nonempty_col_indices(row: list[str], max_cols: int) -> set[int]:
    return {idx for idx in range(min(max_cols, len(row))) if column_text(row, idx).strip()}


def _header_column_incomplete(rows: list[list[str]], top_header_rows: int) -> bool:
    if top_header_rows <= 0:
        return False
    max_cols = max((len(row) for row in rows), default=0)
    if max_cols < 3:
        return False
    filled: set[int] = set()
    for row in rows[:top_header_rows]:
        filled.update(_nonempty_col_indices(row, max_cols))
    return len(filled) < max_cols and len(filled) <= max(1, int(max_cols * 0.75))


def _bare_year_value_row_like(row: list[str]) -> bool:
    nonempty = [text.strip() for text in row if text.strip()]
    if len(nonempty) < 2:
        return False
    return all(_YEAR_RE.fullmatch(text) for text in nonempty)


def _undertag_extension_candidate(row: list[str], following_rows: list[list[str]], max_cols: int) -> bool:
    features = row_features(row)
    profile = row_profile(row, 0)
    filled_cols = sorted(_nonempty_col_indices(row, max_cols))
    nonempty_after_stub = [column_text(row, col) for col in range(1, min(max_cols, len(row))) if column_text(row, col).strip()]
    reasons: list[str] = []

    if features["nonempty_count"] < 2 or len(filled_cols) < 2:
        reasons.append("single_or_sparse_row")
    if len(nonempty_after_stub) < 1:
        reasons.append("no_column_header_cells_after_stub")
    if profile["body_like_row"] or data_row_like(row) or dense_numeric_row_like(row):
        reasons.append("body_like_row")
    if money_or_percent_heavy(row) or features["value_type_ratio"] > 0.35 or features["numeric_ratio"] > 0.50:
        reasons.append("strong_value_row")
    if _bare_year_value_row_like(row):
        reasons.append("bare_year_value_row")
    if section_label_row_like(row):
        reasons.append("section_label_row")
    if features["avg_tokens"] > 8.0 or features["long_text_type_ratio"] >= 0.35:
        reasons.append("long_text_row")
    if len(following_rows) >= 2:
        following_profiles = row_profiles(following_rows)
        body_features = body_window_features_from_profiles(following_profiles, 0)
        if not body_window_is_stable(body_features):
            reasons.append("following_body_not_stable")

    label_signal = features["alpha_ratio"] >= 0.25 or features["date_period_ratio"] >= 0.20
    if not label_signal:
        reasons.append("weak_label_signal")

    return not reasons


def extend_header_undertag(
    rows: list[list[str]],
    top_header_rows: int,
    *,
    cap: int = 3,
) -> int:
    """Promote under-tagged column-header rows immediately below the base boundary."""
    max_cols = max((len(row) for row in rows), default=0)
    if top_header_rows <= 0:
        return top_header_rows
    if top_header_rows >= len(rows):
        return top_header_rows
    if not _header_column_incomplete(rows, top_header_rows):
        return top_header_rows

    new_top = top_header_rows
    for row_idx in range(top_header_rows, min(len(rows), top_header_rows + cap)):
        if row_idx >= len(rows) - 1:
            break
        ok = _undertag_extension_candidate(rows[row_idx], rows[row_idx + 1 :], max_cols)
        if not ok:
            break
        new_top = row_idx + 1

    return new_top


def find_top_header_rows_by_body_change(
    rows: list[list[str]],
) -> int:
    if not rows:
        return 0
    if len(rows) == 1:
        return 1

    profiles = row_profiles(rows)
    candidates = body_start_candidates(profiles)
    for candidate in candidates:
        body_start = int(candidate["body_start"])
        if not candidate["body_like"] or candidate["prior_body_seen"]:
            continue

        if body_start == 1:
            if profiles[0]["leading_body_record_row"]:
                restore_guards = first_row_restore_guards(rows[0])
                if restore_guards:
                    return 1
                return 0
            if headerless_dotted_enum_guard(rows):
                return 0
            if sparse_prefix_next_header_guard(rows, 1):
                return 2
            if rowspan_leaf_header_guard(rows, 1):
                return 2
            # A dense period/label header (row 0) over a value-like sub-row (bare
            # years, enumerated headers) is not caught by the sparse-prefix guards.
            if len(rows) >= 3 and next_header_row_value_guard(rows[1], rows[2:]):
                return 2
            return 1

        if header_prefix_ok(rows, profiles, body_start, candidate["body"]):
            return body_start

    if headerless_dotted_enum_guard(rows):
        return 0

    if sparse_prefix_next_header_guard(rows, 1):
        return 2

    if rowspan_leaf_header_guard(rows, 1):
        return 2

    return 1


@dataclass(frozen=True)
class HeaderRegion:
    top_header_rows: int
    section_header_rows: tuple[int, ...]


def find_header_region(rows: list[list[str]]) -> HeaderRegion:
    top_header_rows = find_top_header_rows_by_body_change(rows)
    # Promote under-tagged column-header rows immediately below the detected
    # header/body boundary.
    top_header_rows = extend_header_undertag(rows, top_header_rows)
    section_rows = tuple(section_header_rows(rows, top_header_rows))
    return HeaderRegion(
        top_header_rows=top_header_rows,
        section_header_rows=section_rows,
    )


# --- HTML serialization: tagged placement grid -> <table> --------------------
def collapse_cell_ws(text: str) -> str:
    """Whitespace-collapse a cell's text (runs of whitespace/newlines -> one space)."""
    return " ".join(text.split())


def escape_html_text(text: str) -> str:
    """Escape a cell's text for the serializer: only ``& < >`` (quotes left literal)."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _cell_inner(text: str) -> str:
    """A cell's inner HTML: escaped non-empty lines joined by ``<br/>``."""
    return "<br/>".join(escape_html_text(part.strip()) for part in text.splitlines() if part.strip())


def render_table_html(rows, section_header_rows=()) -> str:
    """Serialize a tagged placement grid to its final ``<table>`` HTML in one pass.

    ``rows`` is a row-major grid of cells duck-typed with ``text`` / ``colspan``
    / ``rowspan`` / ``tag`` (e.g. :class:`pymupdf.table.SpanCell`): each cell
    emits its tag, its ``colspan`` / ``rowspan`` attributes and its ``<br/>``-
    joined escaped inner HTML. A row whose index is in ``section_header_rows``
    and that carries a single non-empty label collapses to one
    ``<th colspan=N>`` spanning the row."""
    section_rows = set(section_header_rows or ())
    parts = ["<table>"]
    for row_idx, cells in enumerate(rows):
        if row_idx in section_rows:
            nonempty = [collapse_cell_ws(cell.text) for cell in cells if collapse_cell_ws(cell.text)]
            if len(nonempty) == 1 and len(cells) >= 2:
                parts.append(
                    '<tr><th colspan="%d">%s</th></tr>'
                    % (len(cells), escape_html_text(nonempty[0]))
                )
                continue
        parts.append("<tr>")
        for cell in cells:
            attrs = ""
            if cell.colspan > 1:
                attrs += ' colspan="%d"' % cell.colspan
            if cell.rowspan > 1:
                attrs += ' rowspan="%d"' % cell.rowspan
            parts.append(
                "<%s%s>%s</%s>" % (cell.tag, attrs, _cell_inner(cell.text), cell.tag)
            )
        parts.append("</tr>")
    parts.append("</table>")
    return "".join(parts)
