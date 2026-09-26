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

PyMuPDF table union stage, behind find_tables(union=True): fuse the layout
analyzer's table grids with the line-based finder's candidates. Table,
TableFinder and _iou come from pymupdf.table; find_tables is imported lazily.
"""

from bisect import bisect_left
from collections import namedtuple

import pymupdf

from pymupdf.table import CHARS, EDGES, Table, TableFinder, _cells_to_rows, _iou


# ---------------------------------------------------------------------------
# find_tables(union=True) fuses two table sources on one page: PRIMARY grids
# from the layout analyzer (each "table" group's GridPrediction, read from
# page.get_layout(return_raw=True) by _layout_table_grids in its raw form) and
# CANDIDATE grids from a nested line-based find_tables. A candidate matching a
# primary 1:1 (high IoU) may REPLACE its grid (grid-ref), several candidates
# each contained in one primary may SPLIT it, and candidates owned by no primary
# are APPENDED. The output order -- primaries (kept / grid-ref'd / split) then
# appended candidates -- is contractual: downstream consumers key tables by it.
#
# _layout_table_grids also replaces find_tables' make_table_from_bbox path,
# which silently yields an empty Table because the stext grid block it needs is
# not emitted; make_table_from_bbox is left in place pending a separate cleanup.
# ---------------------------------------------------------------------------
_UNION_STRATEGY = "lines_strict"          # candidate detection strategy
_UNION_GRID_REF_IOU = 0.9                 # min IoU for a 1:1 grid-ref replacement
_UNION_GRID_REF_SPAN_MULT_GATE = True     # reject under-segmented candidate grids
_UNION_GRID_REF_SPAN_MULT_THRESHOLD = 3.0  # max horizontally-separated span groups per cell
_UNION_OWNER_CONTAINMENT = 0.85           # min containment for a split candidate's owner
_UNION_OWNER_AMBIGUOUS_OVERLAP = 0.25     # overlap above which an unowned candidate is suppressed
_UNION_PICTURE_CONTAINMENT = 0.8          # area fraction that puts a candidate inside a picture

# How a candidate grid's text is laid out; see _union_grid_content_support.
_UnionContent = namedtuple(
    "_UnionContent", "supported dense_rows dense_columns concrete slots"
)


def _layout_table_grids(page):
    """Primary table grids from the raw layout analyzer result.

    Reads page.layout_information in its raw (return_raw=True) form and yields a
    ``(bbox, grid)`` pair per "table" group -- ``grid`` is the full row-major cell
    grid built from the group box plus its interior GridPrediction lines, in
    layout (reading) order. Boxes without a usable grid are skipped.
    """
    grids = []
    for group in (page.layout_information or []):
        if not isinstance(group, dict):
            # The union path needs the raw (return_raw=True) layout form; the
            # normalized [x0, y0, x1, y1, class] tuples carry no table_grid.
            continue
        if group.get("class_name") != "table":
            continue
        group_bbox = group.get("group_bbox")
        grid_pred = group.get("table_grid")
        if not group_bbox or grid_pred is None:
            continue
        x0, y0, x1, y1 = group_bbox[0], group_bbox[1], group_bbox[2], group_bbox[3]
        h_lines = [y0] + [h + y0 for h in grid_pred.h_lines] + [y1]
        v_lines = [x0] + [v + x0 for v in grid_pred.v_lines] + [x1]
        grid = []
        for i in range(len(h_lines) - 1):
            row = []
            for j in range(len(v_lines) - 1):
                row.append((v_lines[j], h_lines[i], v_lines[j + 1], h_lines[i + 1]))
            grid.append(row)
        grids.append((pymupdf.Rect(group_bbox[:4]), grid))
    return grids


def _union_line_candidates(page, *, add_lines=None, add_boxes=None):
    """Line-based table candidates for the union stage as ``(bbox, grid)`` pairs.

    Runs a nested find_tables (strategy=_UNION_STRATEGY, use_layout=False) and
    keeps each detected table's bbox and row-major cell grid (None for a gap),
    deduped by rounded bbox. Caller-supplied virtual lines / boxes are forwarded
    to that nested finder so they take part in the same union decisions as
    PDF-native vector rules. Admission (see ``admit``) runs on the finder's cell
    groups, before a Table is built for any of them. Returns ``(candidates,
    finder)``; the finder is reused as the returned TableFinder shell.
    """
    # Imported here, not at module top, to break the import cycle: this
    # module is itself imported lazily by table.find_tables (union path).
    from pymupdf.table import find_tables
    candidates = []

    def admit(live_page, groups):
        """Keep the cell groups that may become tables, in detection order.

        A candidate is admitted as before: the line grid is evidence in its own
        right and the layout model can miss a table entirely. The one exception is
        a candidate sitting inside a region the layout model called a picture,
        which has to show table-shaped text instead. That cheap geometric test
        therefore gates the character scan, and the scan itself is built once for
        the whole call.
        """
        kept = []
        seen = set()
        points = None
        for cells in groups:
            bbox = pymupdf.Rect(
                min(cell[0] for cell in cells),
                min(cell[1] for cell in cells),
                max(cell[2] for cell in cells),
                max(cell[3] for cell in cells),
            )
            if bbox.is_empty:
                continue
            grid = [row.cells for row in _cells_to_rows(cells)]
            if not grid:
                continue
            key = tuple(round(value) for value in bbox)
            if key in seen:
                continue
            if _union_candidate_inside_picture(live_page, bbox):
                if points is None:
                    points = _union_char_midpoints()
                content = _union_grid_content_support(grid, points)
                # A chart labels one row and one column -- its axes -- and its
                # partial gridlines leave most slots without a cell. A table has
                # a header row and a label column that are each at least half
                # full, and cell coverage that is mostly rectangular.
                if not (
                    content.supported
                    and content.dense_rows >= 2
                    and content.dense_columns >= 2
                    and content.concrete * 2 >= content.slots
                ):
                    continue
            # Dedup only admitted candidates: a rejected one must not shadow a
            # later, differently gridded candidate with the same rounded bbox.
            seen.add(key)
            kept.append(cells)
            candidates.append((bbox, grid))
        return kept

    finder = find_tables(
        page,
        strategy=_UNION_STRATEGY,
        use_layout=False,
        add_lines=add_lines,
        add_boxes=add_boxes,
        _cell_group_filter=admit,
    )
    if finder is None:
        # Nested detection failure must not leak partially admitted candidates.
        candidates.clear()
    return candidates, finder


def _union_rect_area(rect):
    return max(0.0, float(rect.x1 - rect.x0)) * max(0.0, float(rect.y1 - rect.y0))


def _union_intersection_area(left, right):
    x0 = max(float(left.x0), float(right.x0))
    y0 = max(float(left.y0), float(right.y0))
    x1 = min(float(left.x1), float(right.x1))
    y1 = min(float(left.y1), float(right.y1))
    if x1 <= x0 or y1 <= y0:
        return 0.0
    return (x1 - x0) * (y1 - y0)


def _union_x_overlap(left, right):
    return max(0.0, min(float(left.x1), float(right.x1)) - max(float(left.x0), float(right.x0)))


def _union_find_owner(candidate_bbox, existing_bboxes):
    """The primary a split candidate belongs inside, plus an ambiguity flag.

    Returns ``(owner_index, ambiguous)``: owner is the best-contained primary
    (candidate>=_UNION_OWNER_CONTAINMENT inside it), else None; ambiguous is True
    when the candidate overlaps some primary enough to be unsafe to append."""
    candidate_area = _union_rect_area(candidate_bbox)
    if candidate_area <= 0:
        return None, True
    best_owner = None
    best_containment = 0.0
    ambiguous = False
    for index, existing_bbox in enumerate(existing_bboxes):
        existing_area = _union_rect_area(existing_bbox)
        inter_area = _union_intersection_area(candidate_bbox, existing_bbox)
        if inter_area <= 0 or existing_area <= 0:
            continue
        candidate_containment = inter_area / candidate_area
        existing_coverage = inter_area / existing_area
        if candidate_containment >= _UNION_OWNER_CONTAINMENT and candidate_containment > best_containment:
            best_owner = index
            best_containment = candidate_containment
        elif candidate_containment >= _UNION_OWNER_AMBIGUOUS_OVERLAP or existing_coverage >= _UNION_OWNER_AMBIGUOUS_OVERLAP:
            ambiguous = True
    return best_owner, ambiguous


def _union_char_midpoints():
    """The page's non-blank character midpoints as ``(v_mid, h_mid)``, y-sorted.

    One pass over CHARS replaces the per-cell character scan of the admission
    tests, which read midpoints only. Sorting by the vertical midpoint lets each
    grid row take its own characters as one slice.
    """
    points = []
    for char in CHARS:
        if not str(char.get("text") or "").strip():
            continue
        try:
            h_mid = (float(char["x0"]) + float(char["x1"])) / 2.0
            v_mid = (float(char["top"]) + float(char["bottom"])) / 2.0
        except (KeyError, TypeError, ValueError):
            continue
        points.append((v_mid, h_mid))
    points.sort()
    return points


def _union_grid_content_support(grid, points):
    """How a candidate line grid's text is distributed, in one scan.

    ``supported`` means at least two rows with text in at least two columns and
    at least two columns with text in at least two rows -- two being the smallest
    non-trivial count in each dimension, not a fitted one. A populated cell counts
    for every column its x-range covers, so a grid whose missing horizontal rules
    leave a spanning header above one record row is supported just like the same
    table with all its rules.

    ``dense_rows`` / ``dense_columns`` count the rows and columns whose own
    concrete cells are at least half populated, and ``concrete`` / ``slots`` are
    the concrete cells and the grid's total slots. Those describe the *shape* of
    the text rather than its amount, which is what separates a chart from a
    sparse table (see _union_candidate_inside_picture).

    Character membership follows Table.extract()'s half-open cell rule. ``None``
    grid slots are span/gap placeholders, not empty text cells. The decision is
    candidate-local: page area, layout ownership, file identity and virtual-line
    provenance are not inputs.
    """
    columns = sorted({float(cell[0]) for row in grid for cell in row if cell is not None})
    width = max((len(row) for row in grid), default=0)
    column_populated = [0] * width
    column_concrete = [0] * width
    row_columns = []
    row_counts = []
    concrete = 0
    slots = 0
    for row in grid:
        slots += len(row)
        covered = set()
        row_populated = 0
        rects = [(index, pymupdf.Rect(cell)) for index, cell in enumerate(row) if cell is not None]
        rects = [(index, rect) for index, rect in rects if not rect.is_empty]
        concrete += len(rects)
        if rects:
            band = _union_row_points(rects, points)
            for index, rect in rects:
                column_concrete[index] += 1
                if not _union_rect_has_point(rect, band):
                    continue
                row_populated += 1
                column_populated[index] += 1
                spanned = [
                    column
                    for column, x in enumerate(columns)
                    if float(rect.x0) <= x < float(rect.x1)
                ]
                covered.update(spanned or (index,))
        row_columns.append(covered)
        row_counts.append((row_populated, len(rects)))
    supported = sum(len(covered) >= 2 for covered in row_columns) >= 2 and sum(
        sum(column in covered for covered in row_columns) >= 2
        for column in range(len(columns))
    ) >= 2
    return _UnionContent(
        supported=supported,
        dense_rows=sum(total > 0 and filled * 2 >= total for filled, total in row_counts),
        dense_columns=sum(
            total > 0 and filled * 2 >= total
            for filled, total in zip(column_populated, column_concrete)
        ),
        concrete=concrete,
        slots=slots,
    )


def _union_row_points(rects, points):
    """The y-sorted midpoints falling in one grid row's vertical band."""
    y0 = min(float(rect.y0) for _index, rect in rects)
    y1 = max(float(rect.y1) for _index, rect in rects)
    return points[bisect_left(points, (y0,)) : bisect_left(points, (y1,))]


def _union_rect_has_point(rect, band):
    """Whether any midpoint of the row band lies in rect (half-open, as extract)."""
    x0, y0, x1, y1 = float(rect.x0), float(rect.y0), float(rect.x1), float(rect.y1)
    for v_mid, h_mid in band:
        if x0 <= h_mid < x1 and y0 <= v_mid < y1:
            return True
    return False


def _union_layout_groups(page):
    """The page's layout groups as ``(class_name, rect)``, skipping unusable ones."""
    groups = []
    for group in (page.layout_information or []):
        if not isinstance(group, dict):
            continue
        group_bbox = group.get("group_bbox")
        if not group_bbox:
            continue
        try:
            rect = pymupdf.Rect(group_bbox[:4])
        except (TypeError, ValueError):
            continue
        if rect.is_empty:
            continue
        groups.append((group.get("class_name"), rect))
    return groups


def _union_candidate_inside_picture(page, candidate_bbox):
    """Whether a candidate sits inside a layout picture group without covering it.

    The layout model classified that region as a picture, so a line grid found
    almost entirely inside one is as likely to be a chart's gridlines as a table,
    and overriding the model's verdict needs table-shaped text. The shape, not the
    amount, is what tells them apart: a chart's text sits along its two axes, so
    exactly one row and one column are well filled and its partial gridlines leave
    most of the grid without a cell at all, while a table has a header row and a
    label column that are each at least half full over mostly complete cell
    coverage -- which a sparse matrix of scattered marks still satisfies. See the
    admission rule in _union_line_candidates.

    A candidate larger than the picture contains it instead -- a bordered table
    with an image in one of its cells -- and keeps the ordinary rule.
    """
    candidate_area = _union_rect_area(candidate_bbox)
    if candidate_area <= 0:
        return False
    threshold = _UNION_PICTURE_CONTAINMENT * candidate_area
    for class_name, rect in _union_layout_groups(page):
        if class_name != "picture":
            continue
        if _union_intersection_area(candidate_bbox, rect) < threshold:
            continue
        if candidate_area > _union_rect_area(rect):
            continue  # the candidate is the larger region: it holds the picture
        return True
    return False


def _union_text_span_rects(page):
    """Non-empty page text-span rects, cached on the page.

    Drives the grid-ref span-multiplicity gate: every non-blank span as a bare
    rect."""
    cached = getattr(page, "_union_text_spans_cache", None)
    if cached is not None:
        return cached
    spans = []
    for block in page.get_text("dict").get("blocks", []) or []:
        for line in block.get("lines", []) or []:
            for span in line.get("spans", []) or []:
                if not str(span.get("text") or "").strip():
                    continue
                bbox = span.get("bbox")
                if not bbox:
                    continue
                rect = pymupdf.Rect(bbox)
                if not rect.is_empty:
                    spans.append(rect)
    try:
        setattr(page, "_union_text_spans_cache", spans)
    except Exception:
        pass
    return spans


def _union_cell_span_group_count(cell, text_spans):
    """Max horizontally-separated text-span groups on any single text line in a cell."""
    line_bands = []
    for span in text_spans:
        center_y = (float(span.y0) + float(span.y1)) / 2.0
        if center_y < float(cell.y0) - 1.0 or center_y > float(cell.y1) + 1.0:
            continue
        if _union_x_overlap(span, cell) <= 1.0:
            continue
        x0 = max(float(cell.x0), float(span.x0))
        x1 = min(float(cell.x1), float(span.x1))
        if x1 <= x0:
            continue
        for index, (band_y, intervals) in enumerate(line_bands):
            if abs(center_y - band_y) <= 4.0:
                intervals.append((x0, x1))
                line_bands[index] = ((band_y + center_y) / 2.0, intervals)
                break
        else:
            line_bands.append((center_y, [(x0, x1)]))
    best = 0
    for _, intervals in line_bands:
        groups = 0
        last_x1 = None
        for x0, x1 in sorted(intervals):
            if last_x1 is None or x0 - last_x1 > 4.0:
                groups += 1
                last_x1 = x1
            else:
                last_x1 = max(last_x1, x1)
        best = max(best, groups)
    return best


def _union_span_multiplicity(page, grid):
    """Max cell span-group count over a grid (high => under-segmented grid)."""
    if page is None:
        return None
    text_spans = _union_text_span_rects(page)
    best = None
    for row in grid:
        for cell in row:
            if cell is None:
                continue
            rect = pymupdf.Rect(cell)
            if rect.is_empty:
                continue
            count = _union_cell_span_group_count(rect, text_spans)
            if count > 0:
                best = count if best is None else max(best, count)
    return float(best) if best is not None else None


def _union_one_to_one_grid_refs(existing, candidates, *, iou_threshold, page, span_mult_gate, span_mult_threshold):
    """Primaries a candidate can grid-ref (replace grid with), 1:1 by IoU.

    ``existing``/``candidates`` are ``(bbox, grid)`` lists. Returns ``(refs,
    consumed)``: ``refs`` maps a primary index to the candidate supplying its
    grid (mutual 1:1 IoU>=threshold matches passing the span-multiplicity gate),
    ``consumed`` the candidate indexes used."""
    existing_matches = {}
    candidate_matches = {}
    for existing_index, (existing_bbox, _grid) in enumerate(existing):
        for candidate_index, (candidate_bbox, _cgrid) in enumerate(candidates):
            iou = _iou(existing_bbox, candidate_bbox)
            if iou >= iou_threshold:
                existing_matches.setdefault(existing_index, []).append((candidate_index, float(iou)))
                candidate_matches.setdefault(candidate_index, []).append((existing_index, float(iou)))
    refs = {}
    consumed = set()
    for existing_index, matches in existing_matches.items():
        if len(matches) != 1:
            continue
        candidate_index, _ = matches[0]
        if len(candidate_matches.get(candidate_index, [])) != 1:
            continue
        if span_mult_gate:
            span_mult = _union_span_multiplicity(page, candidates[candidate_index][1])
            if span_mult is not None and span_mult >= span_mult_threshold:
                continue
        refs[existing_index] = candidates[candidate_index]
        consumed.add(candidate_index)
    return refs, consumed


def _union_replace_append(existing, candidates, *, page, grid_ref, grid_ref_iou, span_mult_gate, span_mult_threshold):
    """Fuse primary and candidate ``(bbox, grid)`` entries.

    Applies grid-ref replacement, split replacement (>=2 candidates owned by one
    primary replace it, ordered by y0/x0) and append of unowned candidates,
    returning the fused entry list in the contractual order."""
    existing_bboxes = [entry[0] for entry in existing]
    if grid_ref:
        grid_refs, consumed = _union_one_to_one_grid_refs(
            existing,
            candidates,
            iou_threshold=grid_ref_iou,
            page=page,
            span_mult_gate=span_mult_gate,
            span_mult_threshold=span_mult_threshold,
        )
    else:
        grid_refs, consumed = {}, set()
    replacements = {}
    append_candidates = []
    for candidate_index, candidate in enumerate(candidates):
        if candidate_index in consumed:
            continue
        owner_index, ambiguous = _union_find_owner(candidate[0], existing_bboxes)
        if owner_index is not None:
            replacements.setdefault(owner_index, []).append(candidate)
        elif ambiguous:
            continue  # overlaps a primary but is not contained -> suppress
        else:
            append_candidates.append(candidate)
    final_replacements = {
        index: sorted(items, key=lambda entry: (float(entry[0].y0), float(entry[0].x0)))
        for index, items in replacements.items()
        if len(items) >= 2
    }
    entries = []
    for index, entry in enumerate(existing):
        if index in final_replacements:
            entries.extend(final_replacements[index])
        elif index in grid_refs:
            # Grid-ref: keep the primary's (layout) bbox, take the candidate grid.
            entries.append((entry[0], grid_refs[index][1]))
        else:
            entries.append(entry)
    entries.extend(append_candidates)
    return entries


def _find_tables_union(page, *, add_lines=None, add_boxes=None):
    """Detect a page's tables by fusing layout grids with line-based candidates.

    Ensures the raw layout (computed only when page.layout_information is None,
    like the official use_layout path), reads primary grids, detects candidates
    (forwarding the caller's virtual lines / boxes to the nested finder), applies
    grid-ref / split / append, and returns a TableFinder whose .tables carry the
    fused grids in contractual order (grid-ref tables keep their explicit layout
    bbox)."""
    if page.layout_information is None:
        page.get_layout(return_raw=True)
    primaries = _layout_table_grids(page)
    candidates, finder = _union_line_candidates(
        page, add_lines=add_lines, add_boxes=add_boxes
    )
    entries = _union_replace_append(
        primaries,
        candidates,
        page=page,
        grid_ref=True,
        grid_ref_iou=_UNION_GRID_REF_IOU,
        span_mult_gate=_UNION_GRID_REF_SPAN_MULT_GATE,
        span_mult_threshold=_UNION_GRID_REF_SPAN_MULT_THRESHOLD,
    )
    if finder is None:
        # Candidate detection failed mid-way; the nested find_tables may have
        # left partially-filled EDGES/CHARS state behind, and TableFinder's
        # constructor runs a full detection from that state -- clear it first
        # so the fallback really is an empty shell.
        EDGES.clear()
        CHARS.clear()
        finder = TableFinder(page)
    tables = []
    for bbox, grid in entries:
        flat = [cell for row in grid for cell in row if cell is not None]
        if not flat:
            continue
        tables.append(Table(page, flat, bbox=bbox))
    finder.tables = tables
    return finder
