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

PyMuPDF table grid refinement (opt-in extension).

Provides the refine_grid / refine_grid_structure / refine_grid_rows API that
refines a detected table's cell grid using page text and vector-graphics
geometry. Re-exported by pymupdf.table; never runs on the default
find_tables() path.
"""

import itertools
import re
import pymupdf


# Grid refinement runs three splitters, each taking (page, grid) and returning a
# grid without mutating the page:
#   * _split_shaded_rows            split rows the line grid merged but a cell
#                                   background-shading rectangle separates,
#   * _split_undersegmented_columns split a column that jams several values into
#                                   one cell,
#   * _split_overmerged_rows        split body rows that collapsed several
#                                   records into a single grid row.
# Word selection uses center-point cell membership with rotated/vertical span
# substitution; it is independent of the CHARS/extract_words path in
# pymupdf.table, so refinement needs no CHARS state.

_REFINE_LINE_GAP = 3.0  # center-y gap (points) that groups body words into lines


# --- word selection: center-point membership + rotated-span substitution -----
def _refine_rawdict_spans(page):
    """Flattened rawdict text spans carrying line-direction metadata.

    Only used to locate vertical/rotated text so those words can be replaced by
    span-level bboxes in _refine_page_words. Minimal fields (bbox/text/dir/wmode)
    -- the only ones the consumers read."""
    spans = []
    raw = page.get_text("rawdict")
    for block in raw.get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            direction = line.get("dir")
            wmode = line.get("wmode")
            for span in line.get("spans", []):
                text = "".join(str(char.get("c", "")) for char in span.get("chars", []))
                if not text.strip():
                    continue
                spans.append(
                    {
                        "bbox": [float(v) for v in span.get("bbox", [])],
                        "text": text,
                        "dir": direction,
                        "wmode": wmode,
                    }
                )
    return spans


def _refine_is_vertical_or_rotated(span):
    """True when a rawdict span's direction indicates non-horizontal text flow.

    wmode != 0 is vertical; otherwise compare |dir_x| vs |dir_y| (a missing or
    unparsable direction counts as horizontal)."""
    if span.get("wmode") not in (None, 0):
        return True
    direction = span.get("dir")
    if not isinstance(direction, (list, tuple)) or len(direction) < 2:
        return False
    try:
        dx = abs(float(direction[0]))
        dy = abs(float(direction[1]))
    except (TypeError, ValueError):
        return False
    return dy > dx


def _refine_page_words(page):
    """Center-point word list for grid refinement, cached on the page object.

    Extract page words once (page.get_text("words")), then substitute vertical/
    rotated text: any horizontal word whose center falls inside a rotated span's
    bbox is dropped, and each rotated span is appended as a single word."""
    cache = getattr(page, "_refine_words_cache", None)
    if cache is not None:
        return cache
    words = [
        (float(w[0]), float(w[1]), float(w[2]), float(w[3]), str(w[4]))
        for w in page.get_text("words")
        if str(w[4]).strip()
    ]
    rotated_spans = [
        span
        for span in _refine_rawdict_spans(page)
        if _refine_is_vertical_or_rotated(span) and str(span.get("text") or "").strip()
    ]
    if rotated_spans:
        rotated_rects = [pymupdf.Rect(span.get("bbox") or []) for span in rotated_spans]
        kept = []
        for word in words:
            wx0, wy0, wx1, wy1, _ = word
            center = pymupdf.Point((wx0 + wx1) * 0.5, (wy0 + wy1) * 0.5)
            if any(rect.contains(center) for rect in rotated_rects if not rect.is_empty):
                continue
            kept.append(word)
        for span, rect in zip(rotated_spans, rotated_rects):
            if rect.is_empty:
                continue
            kept.append(
                (float(rect.x0), float(rect.y0), float(rect.x1), float(rect.y1), str(span["text"]))
            )
        words = sorted(kept, key=lambda item: (item[1], item[0]))
    try:
        setattr(page, "_refine_words_cache", words)
    except Exception:
        pass
    return words


def _refine_word_in_rect(wx0, wy0, wx1, wy1, x0, y0, x1, y1):
    """Word-to-cell membership by CENTER point (inclusive), not clip-overlap.

    A word straddling a column line is claimed by exactly one cell."""
    cx = (wx0 + wx1) * 0.5
    cy = (wy0 + wy1) * 0.5
    return x0 <= cx <= x1 and y0 <= cy <= y1


def _refine_words_in_rect(page, rect):
    """Page words whose center lies in rect, as (x0, y0, x1, y1, text) tuples."""
    x0, y0, x1, y1 = float(rect.x0), float(rect.y0), float(rect.x1), float(rect.y1)
    return [
        (wx0, wy0, wx1, wy1, text)
        for wx0, wy0, wx1, wy1, text in _refine_page_words(page)
        if _refine_word_in_rect(wx0, wy0, wx1, wy1, x0, y0, x1, y1)
    ]


def _refine_has_digit(text):
    """Loose value-like predicate: the text contains any digit."""
    return bool(re.search(r"\d", text.strip()))


def _refine_has_digit_no_alpha(text):
    """Strict value-like predicate: contains a digit and no letters."""
    stripped = text.strip()
    return bool(re.search(r"\d", stripped)) and not any(char.isalpha() for char in stripped)


# --- stage 1: split rows separated by cell background shading ----------------
def _refine_is_white(fill, *, threshold=0.95):
    if fill is None:
        return True
    try:
        r, g, b = fill[:3]
    except Exception:
        return True
    return float(r) > threshold and float(g) > threshold and float(b) > threshold


def _refine_table_rect(cells, table_bbox):
    if table_bbox is not None:
        rect = pymupdf.Rect(table_bbox)
        if not rect.is_empty:
            return rect
    rects = [
        pymupdf.Rect(cell)
        for row in cells
        for cell in row
        if cell is not None and not pymupdf.Rect(cell).is_empty
    ]
    if not rects:
        return None
    rect = pymupdf.Rect(rects[0])
    for item in rects[1:]:
        rect.include_rect(item)
    return rect


def _refine_raw_shaded_rects(page, table_rect, *, min_dim):
    out = []
    page_width = float(page.rect.width)
    for drawing in page.get_drawings():
        if _refine_is_white(drawing.get("fill")):
            continue
        for item in drawing.get("items", []):
            if item[0] != "re":
                continue
            rect = pymupdf.Rect(item[1])
            rect.normalize()
            if rect.width >= 0.95 * page_width:
                continue
            if rect.width < min_dim or rect.height < min_dim:
                continue
            if (rect & table_rect).is_empty:
                continue
            out.append(rect)
    return out


def _refine_cell_background_rects(raw_rects, *, contain_frac=0.9):
    keep = []
    for index, rect in enumerate(raw_rects):
        area = rect.get_area()
        if area <= 0:
            continue
        nested = any(
            other_index != index
            and (rect & other).get_area() >= contain_frac * area
            and other.get_area() > area * 1.05
            for other_index, other in enumerate(raw_rects)
        )
        if not nested:
            keep.append(rect)
    return keep


def _refine_cluster(values, *, tolerance):
    clusters = []
    current = []
    for value in sorted(values):
        if current and value - current[-1] > tolerance:
            clusters.append(sum(current) / len(current))
            current = []
        current.append(value)
    if current:
        clusters.append(sum(current) / len(current))
    return clusters


def _refine_border_lines(page, table_rect):
    xs = set()
    ys = set()
    for drawing in page.get_drawings():
        stroked = drawing.get("type") in ("s", "fs")
        for item in drawing.get("items", []):
            kind = item[0]
            if kind == "l":
                p1, p2 = item[1], item[2]
                if (
                    abs(p1.y - p2.y) < 1.0
                    and abs(p1.x - p2.x) > 10.0
                    and table_rect.y0 - 2.0 < (p1.y + p2.y) * 0.5 < table_rect.y1 + 2.0
                ):
                    ys.add(round((p1.y + p2.y) * 0.5, 1))
                elif (
                    abs(p1.x - p2.x) < 1.0
                    and abs(p1.y - p2.y) > 10.0
                    and table_rect.x0 - 2.0 < (p1.x + p2.x) * 0.5 < table_rect.x1 + 2.0
                ):
                    xs.add(round((p1.x + p2.x) * 0.5, 1))
                continue
            if kind != "re":
                continue
            rect = pymupdf.Rect(item[1])
            rect.normalize()
            if (rect & table_rect).is_empty:
                continue
            if rect.height < 2.0 and rect.width > 10.0:
                ys.add(round((rect.y0 + rect.y1) * 0.5, 1))
            elif rect.width < 2.0 and rect.height > 10.0:
                xs.add(round((rect.x0 + rect.x1) * 0.5, 1))
            elif stroked:
                ys.add(round(rect.y0, 1))
                ys.add(round(rect.y1, 1))
                xs.add(round(rect.x0, 1))
                xs.add(round(rect.x1, 1))
    return sorted(xs), sorted(ys)


def _refine_drop_near(edges, borders, *, tolerance):
    return [edge for edge in edges if not any(abs(edge - border) <= tolerance for border in borders)]


def _refine_has_text(words, x0, y0, x1, y1, *, margin):
    for wx0, wy0, wx1, wy1, text in words:
        if not str(text).strip():
            continue
        cx = (wx0 + wx1) * 0.5
        cy = (wy0 + wy1) * 0.5
        if x0 + margin < cx < x1 - margin and y0 + margin < cy < y1 - margin:
            return True
    return False


def _refine_content_filter_row_edges(words, y0, y1, candidates, x0, x1, *, margin):
    edges = sorted(edge for edge in candidates if y0 + margin < edge < y1 - margin)
    while edges:
        bounds = [y0, *edges, y1]
        empty_index = None
        for index in range(len(bounds) - 1):
            if not _refine_has_text(words, x0, bounds[index], x1, bounds[index + 1], margin=margin):
                empty_index = index
                break
        if empty_index is None:
            break
        if empty_index < len(edges):
            edges.pop(empty_index)
        elif empty_index - 1 >= 0:
            edges.pop(empty_index - 1)
        else:
            break
    return edges


def _split_shaded_rows(
    page,
    cells,
    table_bbox=None,
    *,
    cluster_tolerance=3.0,
    margin=2.0,
    min_dim=6.0,
    border_tolerance=2.5,
):
    """Split rows the line grid merged but a cell background rectangle separates.

    Cell background-shading rectangles give row boundaries the border lines do
    not; candidate y-edges from those rectangles (minus edges that coincide with
    real borders, minus edges that would cut an empty band) subdivide each row."""
    table_rect = _refine_table_rect(cells, table_bbox)
    if table_rect is None or not cells:
        return cells

    raw_rects = _refine_raw_shaded_rects(page, table_rect, min_dim=min_dim)
    background_rects = _refine_cell_background_rects(raw_rects)
    if not background_rects:
        return cells

    y_edges = _refine_cluster(
        [edge for rect in background_rects for edge in (float(rect.y0), float(rect.y1))],
        tolerance=cluster_tolerance,
    )
    _border_xs, border_ys = _refine_border_lines(page, table_rect)
    y_edges = _refine_drop_near(y_edges, border_ys, tolerance=border_tolerance)
    if not y_edges:
        return cells

    words = _refine_page_words(page)
    new_cells = []
    added_rows = 0
    for row in cells:
        live = [pymupdf.Rect(cell) for cell in row if cell is not None]
        if not live:
            new_cells.append(row)
            continue
        ry0 = min(float(cell.y0) for cell in live)
        ry1 = max(float(cell.y1) for cell in live)
        rx0 = min(float(cell.x0) for cell in live)
        rx1 = max(float(cell.x1) for cell in live)
        cuts = _refine_content_filter_row_edges(words, ry0, ry1, y_edges, rx0, rx1, margin=margin)
        if not cuts:
            new_cells.append(row)
            continue
        bounds = [ry0, *cuts, ry1]
        for band_index in range(len(bounds) - 1):
            band = []
            for cell in row:
                if cell is None:
                    band.append(None)
                else:
                    rect = pymupdf.Rect(cell)
                    band.append(
                        [float(rect.x0), bounds[band_index], float(rect.x1), bounds[band_index + 1]]
                    )
            new_cells.append(band)
        added_rows += len(bounds) - 2

    if added_rows <= 0:
        return cells
    return new_cells


# --- stage 2: split under-segmented columns ----------------------------------
def _refine_value_like(text):
    return _refine_has_digit_no_alpha(text)


def _refine_span_value_like(text):
    return _refine_has_digit(text)


def _refine_cell_span_signal(page, cell, *, gap, line_tolerance):
    """True if a cell holds two value-like groups separated by a wide gap on one
    text line -- the signal that a single grid column packs several columns."""
    rect = pymupdf.Rect(cell)
    words = []
    for x0, y0, x1, y1, text in _refine_words_in_rect(page, rect):
        stripped = str(text).strip()
        if not stripped:
            continue
        cx = (float(x0) + float(x1)) / 2.0
        cy = (float(y0) + float(y1)) / 2.0
        if rect.x0 <= cx <= rect.x1 and rect.y0 <= cy <= rect.y1:
            words.append((float(x0), float(x1), cy, stripped))
    if len(words) < 2:
        return False

    words.sort(key=lambda item: item[2])
    lines = []
    current = [words[0]]
    for word in words[1:]:
        if word[2] - current[-1][2] > line_tolerance:
            lines.append(current)
            current = [word]
        else:
            current.append(word)
    lines.append(current)

    for line in lines:
        line.sort(key=lambda item: item[0])
        for index in range(len(line) - 1):
            if line[index + 1][0] - line[index][1] <= gap:
                continue
            left = " ".join(word[3] for word in line[: index + 1])
            right = " ".join(word[3] for word in line[index + 1 :])
            if _refine_span_value_like(left) and _refine_span_value_like(right):
                return True
    return False


def _refine_detect_span_columns(
    page, cells, *, gap=12.0, line_tolerance=4.0, support_ratio=0.3, min_support=2
):
    """Return the column indices that fire the under-segmentation gate: columns
    where enough rows carry the two-value-group signal (a support threshold)."""
    rows = len(cells)
    support_threshold = max(min_support, int(support_ratio * rows))
    col_hits = {}
    for row in cells:
        for col_index, cell in enumerate(row):
            if cell is None:
                continue
            if _refine_cell_span_signal(page, cell, gap=gap, line_tolerance=line_tolerance):
                col_hits[col_index] = col_hits.get(col_index, 0) + 1
    return sorted(col for col, count in col_hits.items() if count >= support_threshold)


def _refine_column_words(page, cells, col):
    rows = []
    for row in cells:
        words = []
        if col < len(row) and row[col] is not None:
            rect = pymupdf.Rect(row[col])
            for x0, y0, x1, y1, text in _refine_words_in_rect(page, rect):
                if not str(text).strip():
                    continue
                cx = (float(x0) + float(x1)) / 2.0
                cy = (float(y0) + float(y1)) / 2.0
                if rect.x0 <= cx <= rect.x1 and rect.y0 <= cy <= rect.y1:
                    words.append((float(x0), float(x1), str(text)))
        rows.append(sorted(words))
    return rows


def _refine_cut_xs(rows_words, *, bridge_tolerance=0):
    intervals = [(x0, x1, row_index) for row_index, words in enumerate(rows_words) for (x0, x1, _) in words]
    if len(intervals) < 2:
        return []

    lo = min(x0 for x0, _, _ in intervals)
    hi = max(x1 for _, x1, _ in intervals)
    if hi - lo < 1:
        return []

    channels = []
    current = None
    x = lo
    while x <= hi:
        crossing_rows = {row_index for x0, x1, row_index in intervals if x0 < x < x1}
        if len(crossing_rows) > bridge_tolerance:
            if current is not None:
                channels.append((current[0], current[1]))
                current = None
        else:
            current = [x, x] if current is None else [current[0], x]
        x += 1.0
    if current is not None:
        channels.append((current[0], current[1]))

    cuts = []
    for left_edge, right_edge in channels:
        if left_edge <= lo + 1 or right_edge >= hi - 1:
            continue
        cut_x = (left_edge + right_edge) / 2.0
        crossing_count = sum(1 for words in rows_words if any(x0 < cut_x < x1 for x0, x1, _ in words))
        # Evaluate the symmetry/value guards on non-bridging rows only, so a
        # merged label spanning value subcolumns does not block column recovery.
        body_rows = [words for words in rows_words if not any(x0 < cut_x < x1 for x0, x1, _ in words)]
        left_rows = right_rows = 0
        left_ok = right_ok = 0
        left_n = right_n = 0
        left_values = []
        right_values = []
        for words in body_rows:
            left = [text for x0, x1, text in words if x1 <= cut_x]
            right = [text for x0, x1, text in words if x0 >= cut_x]
            if left:
                left_rows += 1
                left_n += 1
                left_ok += _refine_value_like(" ".join(left))
                left_values.extend(left)
            if right:
                right_rows += 1
                right_n += 1
                right_ok += _refine_value_like(" ".join(right))
                right_values.extend(right)

        if left_rows < 2 or right_rows < 2:
            continue
        if crossing_count > 0:
            if not _refine_value_like(" ".join(left_values)) or not _refine_value_like(" ".join(right_values)):
                continue
        elif (left_n and left_ok / left_n < 0.5) or (right_n and right_ok / right_n < 0.5):
            continue
        cuts.append(cut_x)

    return sorted(cuts)


def _refine_split_columns(page, cells, *, bridge_tolerance=0, allowed_cols=None):
    ncols = max((len(row) for row in cells), default=0)
    active_cols = None if allowed_cols is None else set(allowed_cols)
    col_cuts = {}
    for col in range(ncols):
        if active_cols is not None and col not in active_cols:
            continue
        cuts = _refine_cut_xs(_refine_column_words(page, cells, col), bridge_tolerance=bridge_tolerance)
        if cuts:
            col_cuts[col] = cuts

    if not col_cuts:
        return cells

    new_cells = []
    for row in cells:
        new_row = []
        for col, cell in enumerate(row):
            cuts = col_cuts.get(col)
            if not cuts:
                new_row.append(cell)
            elif cell is None:
                new_row.extend([None] * (len(cuts) + 1))
            else:
                x0, y0, x1, y1 = pymupdf.Rect(cell)
                xs = [x0] + [cut_x for cut_x in cuts if x0 < cut_x < x1] + [x1]
                for index in range(len(xs) - 1):
                    new_row.append([xs[index], y0, xs[index + 1], y1])
        new_cells.append(new_row)

    return new_cells


def _split_undersegmented_columns(
    page,
    cells,
    *,
    gap=12.0,
    line_tolerance=4.0,
    support_ratio=0.3,
    min_support=2,
    bridge_tolerance=0,
):
    """Split under-segmented columns, but only those that fire the value-group
    gate -- so ordinary single-value columns are never disturbed."""
    fired_cols = _refine_detect_span_columns(
        page,
        cells,
        gap=gap,
        line_tolerance=line_tolerance,
        support_ratio=support_ratio,
        min_support=min_support,
    )
    if not fired_cols:
        return cells
    return _refine_split_columns(
        page, cells, bridge_tolerance=bridge_tolerance, allowed_cols=set(fired_cols)
    )


# --- stage 3: split over-merged body rows ------------------------------------
def _refine_rects_from_cells(cells):
    return [pymupdf.Rect(cell) for row in cells for cell in row if cell is not None]


def _refine_union_rect(rects):
    if not rects:
        return None
    rect = pymupdf.Rect(rects[0])
    for item in rects[1:]:
        rect.include_rect(item)
    return rect


def _refine_best_column_bounds(cells):
    best_row = max(
        cells,
        key=lambda row: (sum(1 for cell in row if cell is not None), len(row)),
        default=[],
    )
    bounds = sorted(
        (float(rect.x0), float(rect.x1))
        for cell in best_row
        if cell is not None
        for rect in [pymupdf.Rect(cell)]
        if rect.x1 > rect.x0
    )
    return bounds


def _refine_cluster_words_by_y(words):
    """Group center-point words into body "lines" by a fixed center-y gap,
    returning each line's union bbox and joined text."""
    if not words:
        return []
    words = sorted(words, key=lambda item: ((item[1] + item[3]) / 2.0, item[0]))
    clusters = [[words[0]]]
    last_center = (words[0][1] + words[0][3]) / 2.0
    for word in words[1:]:
        center = (word[1] + word[3]) / 2.0
        if center - last_center > _REFINE_LINE_GAP:
            clusters.append([word])
        else:
            clusters[-1].append(word)
        last_center = center

    lines = []
    for cluster in clusters:
        lines.append(
            {
                "x0": min(word[0] for word in cluster),
                "y0": min(word[1] for word in cluster),
                "x1": max(word[2] for word in cluster),
                "y1": max(word[3] for word in cluster),
                "text": " ".join(word[4] for word in sorted(cluster, key=lambda item: item[0])),
            }
        )
    return lines


def _refine_line_columns(line, col_bounds):
    cols = set()
    line_x0 = float(line["x0"])
    line_x1 = float(line["x1"])
    center = (line_x0 + line_x1) / 2.0
    for index, (x0, x1) in enumerate(col_bounds):
        overlap = min(line_x1, x1) - max(line_x0, x0)
        if overlap > 0 or x0 <= center <= x1:
            cols.add(index)
    return cols


def _refine_page_words_in_rect(page, rect):
    words = []
    rx0, ry0, rx1, ry1 = float(rect.x0), float(rect.y0), float(rect.x1), float(rect.y1)
    for x0, y0, x1, y1, text in _refine_page_words(page):
        cx = (x0 + x1) * 0.5
        cy = (y0 + y1) * 0.5
        if rx0 <= cx <= rx1 and ry0 <= cy <= ry1:
            text = str(text).strip()
            if text:
                words.append((float(x0), float(y0), float(x1), float(y1), text))
    return words


def _refine_merge_overlapping_lines(lines, *, frac):
    if not lines:
        return []
    items = sorted(lines)
    merged = [[float(items[0][0]), float(items[0][1])]]
    for y0, y1 in items[1:]:
        current = merged[-1]
        overlap = current[1] - float(y0)
        min_height = min(current[1] - current[0], float(y1) - float(y0))
        if min_height > 0 and overlap / min_height >= frac:
            current[0] = min(current[0], float(y0))
            current[1] = max(current[1], float(y1))
        else:
            merged.append([float(y0), float(y1)])
    return [(y0, y1) for y0, y1 in merged]


def _refine_detect_row_overmerge(page, cells, *, clean_threshold=0.85, header_row_count=1):
    """Decide whether the body rows are over-merged. Returns the geometry needed
    to re-cut them (body bbox, column bounds, per-record y-bounds) or None.

    Fires only when the body text clusters into clean multi-column "record" lines
    (clean_ratio >= clean_threshold) and there are more records than existing body
    rows -- i.e. several records collapsed into one grid row."""
    col_bounds = _refine_best_column_bounds(cells)
    header_row_count = max(1, min(int(header_row_count), len(cells))) if cells else 0
    existing_body_rows = max(0, len(cells) - header_row_count)
    if len(cells) <= header_row_count:
        return None
    if len(col_bounds) < 2:
        return None

    body_rect = _refine_union_rect(_refine_rects_from_cells(cells[header_row_count:]))
    if body_rect is None or body_rect.is_empty:
        return None

    words = _refine_page_words_in_rect(page, body_rect)
    lines = _refine_cluster_words_by_y(words)
    if not lines:
        return None

    min_cols = max(2, (len(col_bounds) + 1) // 2)  # == max(2, ceil(len/2))
    record_lines = []
    for line in lines:
        cols = sorted(_refine_line_columns(line, col_bounds))
        if len(cols) >= min_cols:
            record_lines.append(line)

    clean_ratio = len(record_lines) / len(lines)
    if clean_ratio < clean_threshold:
        return None
    if len(record_lines) <= existing_body_rows:
        return None

    return {
        "body_bbox": [body_rect.x0, body_rect.y0, body_rect.x1, body_rect.y1],
        "col_bounds": [[round(x0, 2), round(x1, 2)] for x0, x1 in col_bounds],
        "record_line_bounds": [[float(line["y0"]), float(line["y1"])] for line in record_lines],
        "existing_body_rows": existing_body_rows,
        "header_row_count": header_row_count,
    }


def _split_overmerged_rows(
    page, cells, *, clean_threshold=0.85, merge_overlap_frac=0.35, header_row_count=1
):
    """Re-cut over-merged body rows into one grid row per detected record.

    Keeps the header rows intact, then rebuilds the body as evenly-bounded rows
    (cut at the midpoints between consecutive record centers) across the detected
    column bounds. header_row_count is the number of leading header rows to keep."""
    meta = _refine_detect_row_overmerge(
        page, cells, clean_threshold=clean_threshold, header_row_count=header_row_count
    )
    if meta is None:
        return cells

    body_bbox = pymupdf.Rect(meta["body_bbox"])
    col_bounds = [(float(x0), float(x1)) for x0, x1 in meta["col_bounds"]]
    raw_line_bounds = [(float(y0), float(y1)) for y0, y1 in meta["record_line_bounds"]]
    line_bounds = _refine_merge_overlapping_lines(raw_line_bounds, frac=merge_overlap_frac)
    if len(line_bounds) <= int(meta["existing_body_rows"]):
        return cells

    centers = [(y0 + y1) / 2.0 for y0, y1 in line_bounds]
    edges = [float(body_bbox.y0)]
    for prev, nxt in zip(centers, centers[1:]):
        edges.append((prev + nxt) / 2.0)
    edges.append(float(body_bbox.y1))

    header_rows = cells[: int(meta["header_row_count"])]
    new_body = []
    for row_index in range(len(line_bounds)):
        y0 = edges[row_index]
        y1 = edges[row_index + 1]
        new_row = []
        for x0, x1 in col_bounds:
            rect = pymupdf.Rect(x0, y0, x1, y1)
            new_row.append([float(rect.x0), float(rect.y0), float(rect.x1), float(rect.y1)])
        new_body.append(new_row)

    return [*header_rows, *new_body]


# --- public seam -------------------------------------------------------------
def refine_grid_structure(page, cells, *, table_bbox=None):
    """Structural half of refine_grid: split shaded rows, then under-segmented
    columns. Exposed separately so a caller that must know the header/body
    boundary of the post-structure grid can insert that computation between the
    two phases. table_bbox, when given, bounds the shaded-rectangle search;
    otherwise the cells' union is used."""
    cells = _split_shaded_rows(page, cells, table_bbox)
    cells = _split_undersegmented_columns(page, cells)
    return cells


def refine_grid_rows(page, cells, *, header_row_count=1, clean_threshold=0.85, merge_overlap_frac=0.35):
    """Row half of refine_grid: split body rows that collapsed several records
    into one grid row. header_row_count is the number of leading header rows to
    keep intact; callers that resolve a header region pass it in, and the default
    of 1 is a conservative single-header assumption."""
    return _split_overmerged_rows(
        page,
        cells,
        clean_threshold=clean_threshold,
        merge_overlap_frac=merge_overlap_frac,
        header_row_count=header_row_count,
    )


def refine_grid(page, cells, *, table_bbox=None, header_row_count=1):
    """Refine a detected table's cell grid and return the refined grid.

    ``cells`` is a row-major grid: a list of rows, each a list of ``[x0, y0, x1,
    y1]`` cell rectangles (``None`` for a gap). The grid is refined in three
    stages -- split rows that cell background shading separates, split columns
    that jam several values into one cell, and split body rows that merged
    several records -- using the page's words and vector graphics. The result is
    a new grid in the same format (rows may be added and rows may widen).

    ``table_bbox`` optionally bounds the table (else the cells' union is used).
    ``header_row_count`` is the number of leading header rows to preserve when
    re-cutting body rows (default 1). This is the all-in-one convenience wrapper;
    a caller needing the header boundary of the intermediate grid can instead
    call :func:`refine_grid_structure` then :func:`refine_grid_rows`.
    """
    cells = refine_grid_structure(page, cells, table_bbox=table_bbox)
    cells = refine_grid_rows(page, cells, header_row_count=header_row_count)
    return cells


def _refine_cells_to_grid(cells):
    """Convert a Table's flat cell list into the row-major grid refine_grid wants.

    Mirrors Table.rows: columns are the sorted distinct left edges, rows are the
    cells grouped by top edge, each padded with None where a column has no cell."""
    if not cells:
        return []
    xs = sorted({c[0] for c in cells})
    col_index = {x: i for i, x in enumerate(xs)}
    grid = []
    ordered = sorted(cells, key=lambda c: (c[1], c[0]))
    for _y, row_cells in itertools.groupby(ordered, key=lambda c: c[1]):
        row = [None] * len(xs)
        for cell in row_cells:
            row[col_index[cell[0]]] = [float(cell[0]), float(cell[1]), float(cell[2]), float(cell[3])]
        grid.append(row)
    return grid


def _refine_grid_to_cells(grid):
    """Flatten a refined grid back to a Table's flat (x0, y0, x1, y1) cell list."""
    return [
        (float(cell[0]), float(cell[1]), float(cell[2]), float(cell[3]))
        for row in grid
        for cell in row
        if cell is not None
    ]
