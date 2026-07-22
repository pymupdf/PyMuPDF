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

PyMuPDF table cell-span resolution (opt-in extension).

Provides SpanCell and resolve_spans (plus the _span_* helpers), which
reconstruct a detected table's merged-cell (colspan / rowspan) structure.
Re-exported by pymupdf.table; never runs on the default find_tables() path.
Reuses the word-selection helpers of pymupdf._table_refine.
"""

import pymupdf

from pymupdf._table_refine import (
    _refine_is_vertical_or_rotated,
    _refine_page_words,
)


class SpanCell:
    """One reconstructed table cell after span resolution (PyMuPDF extension).

    ``bbox`` is the placement's ``(x0, y0, x1, y1)`` union rect, ``text`` the
    page text it claims (lines joined by ``\\n``), and ``colspan``/``rowspan``
    how many grid columns/rows it covers. resolve_spans always sets a real bbox;
    a caller padding its own grid may construct SpanCells with ``bbox=None``.

    ``tag`` is the cell's HTML tag (``"td"``/``"th"``), defaulting to ``"td"``.
    resolve_spans leaves it at the default; find_tables(refine=True) overwrites
    it from the resolved header region so Table.to_html() can serialize the grid
    directly, and a caller building its own grid may set it too."""

    def __init__(self, bbox, text, colspan, rowspan, tag="td"):
        self.bbox = bbox
        self.text = text
        self.colspan = colspan
        self.rowspan = rowspan
        self.tag = tag


# --- slot geometry: cluster cell edges into column/row boundaries ------------
def _span_clustered_boundaries(values, *, tolerance=3.0):
    """Greedy 1-D clustering of edge coordinates into slot boundaries.

    Keeps a sorted value only when it is more than ``tolerance`` from the last
    kept boundary, so the first value of each run is the retained boundary."""
    boundaries = []
    for value in sorted(values):
        if boundaries and value - boundaries[-1] <= tolerance:
            continue
        boundaries.append(float(value))
    return boundaries


def _span_covered_slot_count(start, end, boundaries, *, tolerance=1.0):
    """How many [boundaries[i], boundaries[i+1]] slots the span start..end covers."""
    count = 0
    for index in range(len(boundaries) - 1):
        midpoint = (boundaries[index] + boundaries[index + 1]) / 2.0
        if start - tolerance <= midpoint <= end + tolerance:
            count += 1
    return max(1, count)


def _span_slot_range(rect, x_boundaries, *, tolerance=1.0):
    """The half-open column-slot range (first, last+1) a rect's x-extent covers."""
    hits = []
    for index in range(len(x_boundaries) - 1):
        midpoint = (x_boundaries[index] + x_boundaries[index + 1]) / 2.0
        if rect.x0 - tolerance <= midpoint <= rect.x1 + tolerance:
            hits.append(index)
    if not hits:
        return (0, 1)
    return (min(hits), max(hits) + 1)


def _span_ranges_intersect(a, b):
    return a[0] < b[1] and b[0] < a[1]


def _span_point_in_rect(x, y, rect):
    return float(rect.x0) <= x <= float(rect.x1) and float(rect.y0) <= y <= float(rect.y1)


def _span_rect_union(rects):
    return pymupdf.Rect(
        min(rect.x0 for rect in rects),
        min(rect.y0 for rect in rects),
        max(rect.x1 for rect in rects),
        max(rect.y1 for rect in rects),
    )


def _span_x_overlap(a, b):
    return min(a.x1, b.x1) - max(a.x0, b.x0)


def _span_substantial_x_overlap(span_rect, cell_rect):
    """True if a text span overlaps a cell by enough x to signal a merge.

    A few points of overlap is noise (a span drifting across a column line with
    trailing whitespace or a currency glyph); require >2pt and >=15% of the cell
    width before treating it as a merged-cell signal."""
    overlap = _span_x_overlap(span_rect, cell_rect)
    if overlap <= 2.0:
        return False
    cell_width = max(1.0, cell_rect.width)
    return overlap / cell_width >= 0.15


def _span_contiguous_ranges(indices):
    """Collapse a sorted index list into (start, end) inclusive runs."""
    if not indices:
        return []
    ranges = []
    start = end = indices[0]
    for index in indices[1:]:
        if index == end + 1:
            end = index
            continue
        ranges.append((start, end))
        start = end = index
    ranges.append((start, end))
    return ranges


def _span_merge_intervals(intervals):
    """Merge overlapping (start, end, text) intervals, accumulating their texts."""
    merged = []
    for start, end, text in sorted(intervals, key=lambda item: (item[0], item[1])):
        if start == end:
            continue
        if not merged or start > merged[-1][1]:
            merged.append((start, end, [text]))
            continue
        prev_start, prev_end, texts = merged[-1]
        merged[-1] = (prev_start, max(prev_end, end), texts + [text])
    return merged


# --- cell text: page words + vertical-text lines claimed by a placement -------
def _span_line_text(line):
    """Space-joined non-empty span texts of a get_text('dict') line."""
    parts = [
        str(span.get("text") or "").strip()
        for span in line.get("spans", [])
        if str(span.get("text") or "").strip()
    ]
    return " ".join(parts)


def _span_line_rect(line):
    """Bounding rect of a dict line (its bbox, else the union of its span bboxes)."""
    bbox = line.get("bbox")
    if bbox:
        rect = pymupdf.Rect(bbox)
        if not rect.is_empty:
            return rect
    rects = [
        pymupdf.Rect(span.get("bbox") or [])
        for span in line.get("spans", [])
        if span.get("bbox")
    ]
    rects = [rect for rect in rects if not rect.is_empty]
    if not rects:
        return None
    return _span_rect_union(rects)


def _span_vertical_text_lines(page):
    """Vertical/rotated text lines as (rect, text), cached on the page.

    Selects non-horizontal lines whose reading order get_text('dict') already
    preserves."""
    cached = getattr(page, "_span_vertical_lines_cache", None)
    if cached is not None:
        return cached
    lines = []
    for block in page.get_text("dict").get("blocks", []):
        if block.get("type") not in (None, 0):
            continue
        for line in block.get("lines", []):
            if not _refine_is_vertical_or_rotated(line):
                continue
            text = _span_line_text(line)
            if not text:
                continue
            rect = _span_line_rect(line)
            if rect is None:
                continue
            lines.append((rect, text))
    try:
        setattr(page, "_span_vertical_lines_cache", lines)
    except Exception:
        pass
    return lines


def _span_vertical_text_for_rect(page, rect, selected_words):
    """Text of vertical lines centered in rect, when they dominate the rect.

    Returns the stacked line text only if vertical lines are centered in the rect,
    cover >=60% of the rect's selected words, and carry >=2 tokens; else None so
    the caller falls back to horizontal line synthesis."""
    if not selected_words:
        return None
    candidates = []
    for line_rect, text in _span_vertical_text_lines(page):
        cx = (float(line_rect.x0) + float(line_rect.x1)) * 0.5
        cy = (float(line_rect.y0) + float(line_rect.y1)) * 0.5
        if _span_point_in_rect(cx, cy, rect):
            candidates.append((line_rect, text))
    if not candidates:
        return None
    vertical_hits = 0
    for _, (wx0, wy0, wx1, wy1, _) in selected_words:
        cx = (wx0 + wx1) * 0.5
        cy = (wy0 + wy1) * 0.5
        if any(_span_point_in_rect(cx, cy, line_rect) for line_rect, _ in candidates):
            vertical_hits += 1
    if vertical_hits / max(1, len(selected_words)) < 0.6:
        return None
    if sum(len(text.split()) for _, text in candidates) < 2:
        return None
    return "\n".join(
        text
        for _, text in sorted(
            candidates,
            key=lambda item: (float(item[0].x0), -float((item[0].y0 + item[0].y1) * 0.5)),
        )
    )


def _span_words_to_line_text(words):
    """Join center-point-selected cell words into text, re-synthesizing lines.

    ``words`` are (y0, x0, y1, text) tuples; they are grouped into lines by an
    adaptive median-height nearest-line rule, each line's words ordered by x, and
    the lines joined by newlines."""
    if not words:
        return ""
    heights = [max(0.1, y1 - y0) for y0, _, y1, _ in words]
    median_height = sorted(heights)[len(heights) // 2]
    line_threshold = max(2.0, median_height * 0.55)
    lines = []
    for y0, x0, y1, text in sorted(words, key=lambda item: (item[0], item[1])):
        cy = (y0 + y1) / 2.0
        best_line = None
        best_distance = line_threshold
        for line in lines:
            distance = abs(cy - float(line["center_y"]))
            if distance <= best_distance:
                best_line = line
                best_distance = distance
        if best_line is None:
            lines.append({"center_y": cy, "words": [(x0, text)]})
            continue
        best_line["words"].append((x0, text))
        count = len(best_line["words"])
        best_line["center_y"] = (float(best_line["center_y"]) * (count - 1) + cy) / count
    text_lines = []
    for line in sorted(lines, key=lambda item: float(item["center_y"])):
        text_lines.append(" ".join(text for _, text in sorted(line["words"], key=lambda item: item[0])))
    return "\n".join(text_lines)


def _span_word_line_tuple(word):
    """Reorder a (x0, y0, x1, y1, text) word to the (y0, x0, y1, text) line tuple."""
    x0, y0, _x1, y1, text = word
    return (float(y0), float(x0), float(y1), str(text))


def _span_select_words_in_rect(page_words, rect):
    """(index, word) pairs whose center lies in rect, index into ``page_words``.

    The index is what lets resolve_spans claim each page word for exactly one
    placement (an earlier cell's word is not re-claimed by a later one)."""
    selected = []
    for index, word in enumerate(page_words):
        wx0, wy0, wx1, wy1, text = word
        if not str(text).strip():
            continue
        cx = (wx0 + wx1) * 0.5
        cy = (wy0 + wy1) * 0.5
        if _span_point_in_rect(cx, cy, rect):
            selected.append((index, word))
    return selected


def _span_words_text_for_rect(page, rect, selected_words):
    """Text for a rect: vertical-line text if it dominates, else line synthesis."""
    vertical_text = _span_vertical_text_for_rect(page, rect, selected_words)
    if vertical_text is not None:
        return vertical_text
    return _span_words_to_line_text([_span_word_line_tuple(word) for _, word in selected_words])


def _span_claim_text_in_rect(page, rect, page_words, claimed_words):
    """Text of rect's words, skipping words already claimed and claiming the rest."""
    selected = [
        (index, word)
        for index, word in _span_select_words_in_rect(page_words, rect)
        if index not in claimed_words
    ]
    for index, _ in selected:
        claimed_words.add(index)
    return _span_words_text_for_rect(page, rect, selected)


def _span_text_spans(page):
    """Page text spans as (rect, text), length>=2, cached on the page.

    These drive merged-cell detection: a single span whose x-extent crosses a
    grid column line signals cells the line grid split but text joins."""
    cached = getattr(page, "_span_text_spans_cache", None)
    if cached is not None:
        return cached
    spans = []
    for block in page.get_text("dict").get("blocks", []):
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = str(span.get("text") or "").strip()
                if len(text) < 2:
                    continue
                bbox = span.get("bbox")
                if not bbox:
                    continue
                rect = pymupdf.Rect(bbox)
                if rect.is_empty:
                    continue
                spans.append((rect, text))
    try:
        setattr(page, "_span_text_spans_cache", spans)
    except Exception:
        pass
    return spans


def _span_crossing_intervals(entries, text_spans):
    """Column ranges within one grid row that a single text span crosses.

    ``entries`` are the row's cell rects (in column order). A text span centered
    in the row band and substantially overlapping >=2 adjacent cells marks those
    cells for merging; overlapping intervals are merged. Returns
    (start, end, texts) with end>start."""
    if len(entries) < 2:
        return []
    row_y0 = min(entry.y0 for entry in entries)
    row_y1 = max(entry.y1 for entry in entries)
    intervals = []
    for span_rect, span_text in text_spans:
        center_y = (span_rect.y0 + span_rect.y1) / 2.0
        if center_y < row_y0 - 1.0 or center_y > row_y1 + 1.0:
            continue
        hit_positions = [
            position
            for position, entry in enumerate(entries)
            if _span_substantial_x_overlap(span_rect, entry)
        ]
        if len(hit_positions) < 2:
            continue
        for start, end in _span_contiguous_ranges(hit_positions):
            if end > start:
                intervals.append((start, end, span_text))
    return _span_merge_intervals(intervals)


# --- strict-colspan gate: reject a merge that fights the header/body split ----
# When strict_colspan is set, a header cell may only merge across columns if the
# body rows below actually split there (and vice-versa for a body cell against a
# leaf header). This keeps a stray text span from collapsing a real column.
def _span_is_leaf_header_range(row_idx, cols, base, body_start):
    if row_idx >= body_start:
        return False
    for other in base:
        if other["role"] not in {"header", "header_leaf", "header_group"}:
            continue
        if other["row"] <= row_idx or other["row"] >= body_start:
            continue
        if _span_ranges_intersect(cols, other["cols"]):
            return False
    return True


def _span_build_base_cells(cells, x_boundaries, body_start):
    """Describe every grid cell by row/slot-range/role for the strict-colspan gate.

    Header cells split into ``header_leaf`` (no header cell below within body) vs
    ``header_group`` (spans over a lower leaf), which the reject rules compare
    against the body split."""
    base = []
    for row_idx, row in enumerate(cells):
        for position, cell in enumerate([cell for cell in row if cell is not None]):
            rect = pymupdf.Rect(cell)
            cols = _span_slot_range(rect, x_boundaries)
            base.append(
                {
                    "row": row_idx,
                    "position": position,
                    "rect": rect,
                    "cols": cols,
                    "colspan": cols[1] - cols[0],
                    "role": "body" if row_idx >= body_start else "header",
                }
            )
    for item in base:
        if item["role"] != "header":
            continue
        item["role"] = (
            "header_leaf"
            if _span_is_leaf_header_range(item["row"], item["cols"], base, body_start)
            else "header_group"
        )
    return base


def _span_body_rows_split_under(cols, base, body_start):
    """True if some body row splits the column range ``cols`` into >1 cell."""
    body_rows = sorted({item["row"] for item in base if item["role"] == "body" and item["row"] >= body_start})
    for row_idx in body_rows:
        hits = [
            item
            for item in base
            if item["role"] == "body" and item["row"] == row_idx and _span_ranges_intersect(cols, item["cols"])
        ]
        if not hits:
            continue
        if len(hits) == 1 and hits[0]["cols"] == cols:
            continue
        covered_start = min(max(cols[0], item["cols"][0]) for item in hits)
        covered_end = max(min(cols[1], item["cols"][1]) for item in hits)
        if covered_start <= cols[0] and covered_end >= cols[1]:
            return True
    return False


def _span_header_leafs_split_over(cols, base):
    """True if leaf-header cells split the column range ``cols`` into >1 cell."""
    hits = [item for item in base if item["role"] == "header_leaf" and _span_ranges_intersect(cols, item["cols"])]
    if not hits:
        return False
    if len(hits) == 1 and hits[0]["cols"] == cols:
        return False
    covered_start = min(max(cols[0], item["cols"][0]) for item in hits)
    covered_end = max(min(cols[1], item["cols"][1]) for item in hits)
    return covered_start <= cols[0] and covered_end >= cols[1]


def _span_reject_colspan_mismatch_merge(*, row_idx, cols, base, body_start):
    """Whether to reject a candidate merge over ``cols`` as a (reason,) mismatch."""
    if cols[1] - cols[0] <= 1:
        return False, ""
    if row_idx < body_start:
        if not _span_is_leaf_header_range(row_idx, cols, base, body_start):
            return False, ""
        if _span_body_rows_split_under(cols, base, body_start):
            return True, "header_leaf_colspan_changed_against_body_split"
        return False, ""
    if _span_header_leafs_split_over(cols, base):
        return True, "body_colspan_changed_against_header_leaf_split"
    return False, ""


def _span_cell_texts_for_entries(page, entries, start, end, page_words):
    texts = []
    for entry in entries[start : end + 1]:
        words = _span_select_words_in_rect(page_words, entry)
        texts.append(_span_words_text_for_rect(page, entry, words))
    return texts


def _span_allow_header_colspan_merge_with_empty_part(*, reason, page, entries, start, end, page_words):
    """Allow an otherwise-rejected header merge when a covered part is empty.

    A header leaf that would be rejected against a body split is still merged if
    one of the merged parts has no text (an empty header slot the body fills)."""
    if reason != "header_leaf_colspan_changed_against_body_split":
        return False
    part_texts = [text.strip() for text in _span_cell_texts_for_entries(page, entries, start, end, page_words)]
    return not all(part_texts)


def resolve_spans(page, cells, *, header_row_count=None, strict_colspan=False):
    """Resolve a detected table's merged-cell (colspan/rowspan) structure.

    ``cells`` is a row-major grid: a list of rows, each a list of ``[x0, y0, x1,
    y1]`` cell rectangles (``None`` for a gap) -- the same grid shape
    :func:`refine_grid` accepts. Returns a row-major grid of :class:`SpanCell`
    placements, ragged where cells span: each placement carries its union
    ``bbox``, the page ``text`` it claims, and its ``colspan``/``rowspan`` (how
    many clustered column/row slots it covers). Every page word is claimed by at
    most one placement.

    ``header_row_count`` is the number of leading header rows (default a
    conservative 1); it only matters together with ``strict_colspan``.
    ``strict_colspan`` (default False), when set, refuses a merge whose colspan
    would contradict the header/body column split. This is a PyMuPDF extension;
    it reads page text/graphics but does not mutate the page.
    """
    rows = len(cells)

    x_edges = []
    y_edges = []
    for row in cells:
        for cell in row:
            if cell is None:
                continue
            rect = pymupdf.Rect(cell)
            x_edges.extend([rect.x0, rect.x1])
            y_edges.extend([rect.y0, rect.y1])

    x_boundaries = _span_clustered_boundaries(x_edges)
    y_boundaries = _span_clustered_boundaries(y_edges)
    body_start = max(1, min(int(header_row_count or 1), rows)) if rows else 0
    base_cells = _span_build_base_cells(cells, x_boundaries, body_start) if strict_colspan else []

    text_spans = _span_text_spans(page)
    page_words = _refine_page_words(page)
    claimed_words = set()
    placements = []
    for row_idx, row in enumerate(cells):
        placement_row = []
        entries = [pymupdf.Rect(cell) for cell in row if cell is not None]
        intervals = _span_crossing_intervals(entries, text_spans)
        intervals_by_start = {start: (end, texts) for start, end, texts in intervals}
        position = 0
        while position < len(entries):
            interval = intervals_by_start.get(position)
            if interval is not None:
                end_position, _crossing_texts = interval
                rect = _span_rect_union(entries[position : end_position + 1])
                if strict_colspan:
                    candidate_cols = _span_slot_range(rect, x_boundaries)
                    reject, reason = _span_reject_colspan_mismatch_merge(
                        row_idx=row_idx,
                        cols=candidate_cols,
                        base=base_cells,
                        body_start=body_start,
                    )
                    if reject and _span_allow_header_colspan_merge_with_empty_part(
                        reason=reason,
                        page=page,
                        entries=entries,
                        start=position,
                        end=end_position,
                        page_words=page_words,
                    ):
                        reject = False
                    if reject:
                        rect = entries[position]
                        position += 1
                    else:
                        position = end_position + 1
                else:
                    position = end_position + 1
            else:
                rect = entries[position]
                position += 1

            if rect.is_empty:
                continue
            colspan = _span_covered_slot_count(rect.x0, rect.x1, x_boundaries)
            rowspan = _span_covered_slot_count(rect.y0, rect.y1, y_boundaries)
            placement_row.append(
                SpanCell(
                    bbox=tuple(rect),
                    text=_span_claim_text_in_rect(page, rect, page_words, claimed_words),
                    colspan=colspan,
                    rowspan=rowspan,
                )
            )
        placements.append(placement_row)

    return placements
