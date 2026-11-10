"""
Regression test for issue #5185: table cell extraction dropped characters with
an empty bbox, e.g. the second character of an expanded ligature when quad
corrections are unset ("fine" became "fne").
"""

from pymupdf.table import extract_cells


class _TextPage:
    """Minimal stand-in for a TextPage, providing extractRAWDICT() only."""

    def __init__(self, chars):
        bbox = (0, 0, 500, 30)
        span = {"bbox": bbox, "flags": 0, "char_flags": 0, "chars": chars}
        line = {"bbox": bbox, "dir": (1, 0), "spans": [span]}
        self.rawdict = {"blocks": [{"type": 0, "bbox": bbox, "lines": [line]}]}

    def extractRAWDICT(self):
        return self.rawdict


def test_5185():
    cell = (0, 0, 100, 30)
    chars = [
        {"c": "f", "bbox": (10, 10, 15, 20), "origin": (10, 18)},
        # zero-width bbox of the expanded "fi" ligature, inside the cell
        {"c": "i", "bbox": (15, 10, 15, 20), "origin": (15, 18)},
        {"c": "n", "bbox": (15, 10, 20, 20), "origin": (15, 18)},
        {"c": "e", "bbox": (20, 10, 25, 20), "origin": (20, 18)},
        # zero-width char outside the cell must still be excluded
        {"c": "x", "bbox": (150, 10, 150, 20), "origin": (150, 18)},
    ]
    assert extract_cells(_TextPage(chars), cell) == "fine"
