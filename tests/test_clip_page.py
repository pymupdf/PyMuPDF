"""
Test Page method clip_to_rect.
"""

import os
import pymupdf


def test_clip():
    """
    Clip a Page to a rectangle and confirm that no text has survived
    that is completely outside the rectangle..
    """
    scriptdir = os.path.dirname(os.path.abspath(__file__))
    rect = pymupdf.Rect(200, 200, 400, 500)
    filename = os.path.join(scriptdir, "resources", "v110-changes.pdf")
    doc = pymupdf.open(filename)
    page = doc[0]
    page.clip_to_rect(rect)  # clip the page to the rectangle
    # capture font warning message of MuPDF
    assert pymupdf.TOOLS.mupdf_warnings() == "bogus font ascent/descent values (0 / 0)"
    # extract all text characters and assert that each one
    # has a non-empty intersection with the rectangle.
    chars = [
        c
        for b in page.get_text("rawdict")["blocks"]
        for l in b["lines"]
        for s in l["spans"]
        for c in s["chars"]
    ]
    for char in chars:
        bbox = pymupdf.Rect(char["bbox"])
        if bbox.is_empty:
            continue
        assert bbox.intersects(
            rect
        ), f"Character '{char['c']}' at {bbox} is outside of {rect}."
