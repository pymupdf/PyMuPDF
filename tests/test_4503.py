"""
Test for issue #4503 in pymupdf:
Correct recognition of strikeout and underline styles in text spans.
"""

import os
import pymupdf
from pymupdf import mupdf

STRIKEOUT = mupdf.FZ_STEXT_STRIKEOUT
UNDERLINE = mupdf.FZ_STEXT_UNDERLINE


def test_4503():
    """
    Check that the text span with the specified text has the correct styling:
    strikeout, but no underline.
    Previously, the text was broken in multiple spans with span breaks at
    every space. and some parts were not detected as strikeout at all.
    """
    scriptdir = os.path.dirname(os.path.abspath(__file__))
    text = "the right to request the state to review and, if appropriate,"
    filename = os.path.join(scriptdir, "resources", "test-4503.pdf")
    doc = pymupdf.open(filename)
    page = doc[0]
    flags = pymupdf.TEXT_ACCURATE_BBOXES | pymupdf.TEXT_COLLECT_STYLES
    spans = [
        s
        for b in page.get_text("dict", flags=flags)["blocks"]
        for l in b["lines"]
        for s in l["spans"]
        if s["text"] == text
    ]
    assert spans, "No spans found with the specified text"
    span = spans[0]

    assert span["char_flags"] & STRIKEOUT
    assert not span["char_flags"] & UNDERLINE
