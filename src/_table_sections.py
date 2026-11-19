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
PyMuPDF centered section-title placements.
"""

"""Whole-table specialization of the existing H6 centered-title extent rule.

Only proven, bold single-title/repeated-label blocks enter this policy. Existing
native words/drawings/characters are supplied by the refine call; no extraction,
layout decision, inference, GT or filename is consulted. Partial extents abstain.
"""
from copy import copy


def centered_extent(title, bounds):
    """H6's existing 5%-of-interval-width test, restricted to the whole row."""
    x0, x1 = title
    left, right = bounds
    if not (left <= x0 < x1 <= right and x1 - x0 < right - left):
        return False
    return abs((x0 + x1 - left - right) * 0.5) <= 0.05 * (right - left)


def interior_vertical(paths, band, *, Rect, is_line_like, min_length):
    """True physical interior partitions at the title band, not TGIF slots.

    Keep native segment extents: the existing border-line sets discard them.
    Outer borders and underlines do not partition a title. Reuse the finder's
    existing simulated-line predicate and minimum length, without new cutoffs.
    """
    x0, y0, x1, y1 = band
    for path in paths:
        for item in path['items']:
            if item[0] == 'l':
                a, b = item[1:3]
                if a.x != b.x:
                    continue
                segments = [(a.x, min(a.y, b.y), max(a.y, b.y))]
            elif item[0] == 're':
                r = Rect(item[1])
                if path.get('type') in ('s', 'fs'):
                    segments = [(r.x0, r.y0, r.y1), (r.x1, r.y0, r.y1)]
                elif is_line_like(r, min_length) and r.width < r.height:
                    segments = [((r.x0 + r.x1) * .5, r.y0, r.y1)]
                else:
                    continue
            else:
                continue
            if any(x0 < x < x1 and high - low >= min_length
                   and low < y1 and y0 < high for x, low, high in segments):
                return True
    return False


def title_row_proof(grid, index, words, word_members, chars, char_members,
                    paths, *, width, section_like, Rect, is_line_like,
                    min_length):
    row = grid[index]
    occupied = [cell for cell in row if cell.text.strip()]
    if len(occupied) != 1 or not section_like([cell.text for cell in row]):
        return None, 'not_single_section_title'
    if not row or any(cell.bbox is None or cell.rowspan != 1 for cell in row):
        return None, 'nonflat_title_row'
    if any(ri + cell.rowspan > index for ri, earlier in enumerate(grid[:index])
           for cell in earlier):
        return None, 'incoming_rowspan'
    if sum(cell.colspan for cell in row) != width:
        return None, 'incomplete_title_slots'
    boxes = [Rect(cell.bbox) for cell in row]
    if len({(r.y0, r.y1) for r in boxes}) != 1:
        return None, 'unequal_title_bands'
    band = (min(r.x0 for r in boxes), boxes[0].y0,
            max(r.x1 for r in boxes), boxes[0].y1)
    if interior_vertical(paths, band, Rect=Rect, is_line_like=is_line_like,
                         min_length=min_length):
        return None, 'physical_vertical_partition'
    title = occupied[0]
    selected = tuple(word_members(Rect(title.bbox)))
    whole_row = tuple(word_members(Rect(band)))
    if not selected or selected != whole_row:
        return None, 'competing_or_unproved_title_words'
    actual = tuple(char_members(Rect(title.bbox)))
    if not actual or not all(chars[i].get('bold', False) for i in actual):
        return None, 'section_emphasis_not_proven'
    extent = min(words[i][0] for i in selected), max(words[i][2] for i in selected)
    if not centered_extent(extent, (band[0], band[2])):
        return None, 'not_centered_over_whole_row'
    return {'band': band, 'text': title.text, 'word_indices': selected,
            'width': width, 'word_extent': extent}, 'centered_title'


def aligned_blocks(rows, depth, grid, *, repeat_labels, prove):
    cuts = tuple(repeat_labels(rows, depth))
    if not cuts or grid is None:
        return cuts, (), 'no_repeated_label_blocks'
    normalized = [tuple(text.casefold() for text in row) for row in rows]
    signature = normalized[cuts[0]]
    first = next(i for i, row in enumerate(normalized) if row == signature)
    proofs = []
    for index, end in zip([first, *cuts], [*(cut - 1 for cut in cuts), len(rows)]):
        if index == 0:
            return cuts, (), 'untitled_repeat'
        if not any(any(text.strip() for text in row) for row in rows[index + 1:end]):
            return cuts, (), 'no_record_after_labels'
        proof, reason = prove(index - 1)
        if proof is None:
            return cuts, (), reason
        proofs.append(proof)
    return tuple(cut - 1 for cut in cuts), tuple(proofs), 'centered_section_aligned'


def merge_title_row(grid, proofs, *, width, Rect, word_members):
    """Return actual placements, preserving all body cells and source fields."""
    if not grid:
        return grid, None
    row = grid[0]
    populated = [cell for cell in row if cell.text.strip()]
    if len(populated) != 1 or any(cell.bbox is None or cell.rowspan != 1 for cell in row):
        return grid, None
    boxes = [Rect(cell.bbox) for cell in row]
    band = (min(r.x0 for r in boxes), min(r.y0 for r in boxes),
            max(r.x1 for r in boxes), max(r.y1 for r in boxes))
    title = populated[0]
    proof = next((p for p in proofs if p['band'] == band and p['text'] == title.text
                  and p['width'] == width and tuple(word_members(Rect(band))) == p['word_indices']), None)
    if proof is None or sum(cell.colspan for cell in row) != width:
        return grid, None
    merged = copy(title)
    merged.bbox, merged.colspan, merged.rowspan = band, width, 1
    return [[merged], *grid[1:]], {'text': title.text, 'bbox': band, 'colspan': width,
                                  'word_indices': proof['word_indices']}

import pymupdf
from pymupdf._table_headers import section_label_row_like
from pymupdf._table_refine import (
    _WordCenterIndex, _refine_word_candidates, _refine_word_in_rect,
)


def _section_word_members(page, words, rect):
    return tuple(i for i, word in _refine_word_candidates(page, words, rect)
                 if word[4].strip() and _refine_word_in_rect(*word[:4], *tuple(rect)))


def section_repeat_plan(page, grid, rows, depth, cuts, chars, *, width,
                        is_line_like, min_length):
    """Plan section cuts using materials already prepared by find_tables.

    Missing caches abstain; never re-extract page text or drawings. The plan is
    scoped to the current refined parent and carries real page-word indices.
    """
    words = getattr(page, '_refine_words_cache', None)
    cache = getattr(page, '_table_drawings_cache', None)
    if not cuts or grid is None or words is None or not cache:
        return cuts, ()
    char_words = [(c['x0'], c['top'], c['x1'], c['bottom'], c['text']) for c in chars]
    index = _WordCenterIndex(char_words)
    def char_members(rect):
        return tuple(i for i in index.candidates(rect) if chars[i]['text'].strip()
                     and _refine_word_in_rect(*char_words[i][:4], *tuple(rect)))
    def prove(row_index):
        return title_row_proof(grid, row_index, words,
            lambda rect: _section_word_members(page, words, rect), chars,
            char_members, cache[0], width=width,
            section_like=section_label_row_like, Rect=pymupdf.Rect,
            is_line_like=is_line_like, min_length=min_length)
    aligned, proofs, _reason = aligned_blocks(rows, depth, grid,
        repeat_labels=lambda _rows, _depth: cuts, prove=prove)
    return aligned, proofs


def apply_section_title(page, grid, proofs, *, width):
    """Apply the actual title placement after strict final span resolution."""
    merged, _event = merge_title_row(grid, proofs, width=width, Rect=pymupdf.Rect,
        word_members=lambda rect: _section_word_members(page, page._refine_words_cache, rect))
    return merged
