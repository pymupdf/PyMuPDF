"""
Copyright (C) 2026 Artifex Software, Inc.

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

Approximate substring search, with offsets into the extracted page text.
"""

from bisect import bisect_right
import re


def _normalize(text):
    """Case-fold and collapse whitespace, retaining original character ranges."""
    parts, offsets = [], []
    for match in re.finditer(r"\s+|\S+", text):
        start, end = match.span()
        token = match.group()
        if token.isspace():
            # Join only a single line break between letters, retaining the
            # original hyphen and newline through the surrounding offsets.
            if token == "\n" and start >= 2 and end < len(text):
                if (text[start - 1] == "-" and text[start - 2].isalpha()
                        and text[end].isalpha()):
                    parts[-1] = parts[-1][:-1]
                    offsets.pop()
                    continue
            parts.append(" ")
            offsets.append((start, end))
        else:
            parts.append(token.casefold())
            if token.isascii():
                offsets.extend(zip(range(start, end), range(start + 1, end + 1)))
            else:
                for i, char in enumerate(token, start):
                    offsets.extend([(i, i + 1)] * len(char.casefold()))
    return "".join(parts), offsets


def _windows(text, needle, max_edits):
    """A match with k edits must contain one of k+1 query pieces unchanged."""
    size = len(needle)
    windows = []
    for part in range(max_edits + 1):
        offset = part * size // (max_edits + 1)
        piece = needle[offset:(part + 1) * size // (max_edits + 1)]
        pos = text.find(piece)
        while pos >= 0:
            windows.append((max(0, pos - offset - max_edits),
                            min(len(text), pos - offset + size + max_edits)))
            # Repetitive text or large budgets can make filtering cost more
            # than a full scan. Bound the work and memory spent on seed hits.
            if len(windows) * size >= len(text):
                return [(0, len(text))]
            pos = text.find(piece, pos + 1)
    merged = []
    for start, end in sorted(windows):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def _candidates(text, needle, max_edits, boundaries=None):
    """Yield (distance, start, end), choosing the earliest optimal start per end."""
    size = len(needle)
    if max_edits == 0:
        start = text.find(needle)
        while start >= 0:
            end = start + size
            if boundaries is None or (boundaries[start] and boundaries[end]):
                yield 0, start, end
            start = text.find(needle, start + 1)
        return

    for first, last in _windows(text, needle, max_edits):
        bounds = boundaries[first:last + 1] if boundaries is not None else None
        for cost, start, end in _levenshtein(text[first:last], needle, max_edits, bounds):
            yield cost, first + start, first + end


def _levenshtein(text, needle, max_edits, boundaries):
    """Semi-global Levenshtein, with two rows of costs and start offsets.

    Skipping a text prefix is free; deleting a query character costs one.
    """
    size = len(needle)
    previous = list(range(size + 1))
    active = list(range(max_edits + 1))
    if boundaries is not None and not boundaries[0]:
        previous = [max_edits + 1] * (size + 1)
        active = []
    starts = [0] * (size + 1)
    dense = False
    for end, char in enumerate(text, 1):
        boundary = boundaries is None or boundaries[end]
        current = [max_edits + 1] * (size + 1)
        current_starts = [end] * (size + 1)
        current[0] = 0 if boundary else max_edits + 1
        # An over-budget state cannot lead to an in-budget alignment. Visit
        # only active states, successors and deletions from a new start.
        # Once states become dense, avoid bookkeeping for the rest of this
        # window (important for repeated characters or large edit budgets).
        if dense or len(active) > size // 3:
            dense = True
            columns = enumerate(needle, 1)
        else:
            columns = sorted(set(active) | {i + 1 for i in active if i < size}
                             | set(range(1, max_edits + 1) if boundary else ()))
            columns = ((i, needle[i - 1]) for i in columns if i)
        next_active = [0] if boundary else []
        for i, wanted in columns:
            cost = previous[i - 1] + (char != wanted)
            start = starts[i - 1]
            insertion = previous[i] + 1
            if insertion < cost or (insertion == cost and starts[i] < start):
                cost, start = insertion, starts[i]
            deletion = current[i - 1] + 1
            if deletion < cost or (deletion == cost and current_starts[i - 1] < start):
                cost, start = deletion, current_starts[i - 1]
            current[i], current_starts[i] = cost, start
            if not dense and cost <= max_edits:
                next_active.append(i)
        if boundary and current[-1] <= max_edits and current_starts[-1] < end:
            yield current[-1], current_starts[-1], end
        previous, starts, active = current, current_starts, next_active


def _page_text(raw):
    """Return text and span ranges; RAWDICT already stores individual chars."""
    text, spans = [], []
    offset = 0
    for block in raw["blocks"]:
        if block["type"] != 0:
            continue
        if text:
            text.append("\n")
            offset += 1
        for line in block["lines"]:
            for span in line["spans"]:
                # Each RAWDICT char holds one Unicode code point, including
                # preserved ligatures. Store one range per span, not per char.
                value = "".join(char["c"] for char in span["chars"])
                text.append(value)
                spans.append((offset, offset + len(value), line["dir"], span))
                offset += len(value)
            text.append("\n")
            offset += 1
    return "".join(text), spans


def search_for_fuzzy(page, needle, *, max_edits, clip=None, textpage=None):
    from . import CheckParent, TEXT_MEDIABOX_CLIP, TEXT_PRESERVE_LIGATURES
    from . import TEXT_PRESERVE_WHITESPACE, TOOLS, Quad, recover_span_quad

    CheckParent(page)
    if not isinstance(needle, str):
        raise TypeError("needle must be a string")
    if not isinstance(max_edits, int) or isinstance(max_edits, bool):
        raise TypeError("max_edits must be an integer")
    if max_edits < 0:
        raise ValueError("max_edits must be non-negative")
    needle = _normalize(needle)[0].strip()
    if not needle:
        return []
    if max_edits >= len(needle):
        raise ValueError("max_edits must be less than the normalized needle length")
    if textpage is None:
        # Preserve the actual line breaks, hyphens and glyphs for result text
        # and quads. Normalization happens only in the search representation.
        textpage = page.get_textpage(clip=clip, flags=(
            TEXT_PRESERVE_WHITESPACE | TEXT_PRESERVE_LIGATURES | TEXT_MEDIABOX_CLIP
        ))
    elif getattr(textpage, "parent", None) != page:
        raise ValueError("not a textpage of this page")

    # With corrections disabled, RAWDICT's font metrics cannot recover the
    # native quads. Retain those only when needed, without changing global state.
    raw = textpage._textpage_dict(raw=2 if TOOLS.unset_quad_corrections() else 1)
    original, spans = _page_text(raw)
    text, offsets = _normalize(original)
    boundaries = [True] + [a[0] != b[0] for a, b in zip(offsets, offsets[1:])] + [True]
    candidates = sorted(_candidates(text, needle, max_edits, boundaries),
                        key=lambda hit: (hit[0], abs(hit[2] - hit[1] - len(needle)),
                                         hit[1], hit[2]))
    # Resolve overlaps in original coordinates too: case-folding can expand
    # one glyph (e.g. sharp s) into several searchable characters.
    occupied = bytearray(len(original))
    selected = []
    for distance, start, end in candidates:
        first, last = offsets[start][0], offsets[end - 1][1]
        if any(occupied[first:last]):
            continue
        occupied[first:last] = b"\1" * (last - first)
        selected.append((first, last, distance))

    results = []
    for first, last, distance in sorted(selected):
        quads = []
        index = bisect_right(spans, first, key=lambda item: item[1])
        while index < len(spans):
            start, end, direction, span = spans[index]
            if start >= last:
                break
            chars = span["chars"][max(0, first - start):last - start]
            if chars:
                if "quad" in chars[0]:
                    left, right = chars[0]["quad"], chars[-1]["quad"]
                    quads.append(Quad(left[0], right[1], left[2], right[3]))
                else:
                    quads.append(recover_span_quad(direction, span, chars))
            index += 1
        results.append(dict(text=original[first:last], distance=distance, quads=quads))
    return results
