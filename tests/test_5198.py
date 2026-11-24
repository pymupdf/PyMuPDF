"""Table.extract() keeps "0.74" on one line whatever the quad-corrections toggle says.

Issue #5198: with quad corrections off, which is the state after importing
pymupdf4llm and always the state on the layout path, every character keeps its
exact glyph box. The "." of "0.74" then starts about 7 pt below the digits and
extract_text() grouped it onto a line of its own, so the cell read "0 74\\n.".
Spaces between words were lost the same way when the space character landed in
another line cluster. Cell text is now grouped by the top of the text line
derived from each char's baseline and font metrics, which is the same for every
char on a line in both toggle states.
"""
import pymupdf
import pytest
from pymupdf.table import extract_text, extract_words

GRID = [
    ["P for interaction", "Cooking fuel type"],
    ["0.74", "12.5 mg"],
]


def _bordered_grid(page, bbox, texts, fontsize=11):
    x0, y0, x1, y1 = bbox
    rows, cols = len(texts), len(texts[0])
    rh, cw = (y1 - y0) / rows, (x1 - x0) / cols
    for r in range(rows + 1):
        page.draw_line((x0, y0 + r * rh), (x1, y0 + r * rh))
    for c in range(cols + 1):
        page.draw_line((x0 + c * cw, y0), (x0 + c * cw, y1))
    for r, values in enumerate(texts):
        for c, value in enumerate(values):
            page.insert_text(
                (x0 + c * cw + 8, y0 + (r + 1) * rh - 12), value, fontsize=fontsize
            )


def _rotated(expected, rotation):
    for _ in range(rotation // 90):
        expected = [list(row) for row in zip(*reversed(expected))]
    return expected


class _quad_corrections_off:
    """Set the toggle as an import of pymupdf4llm does, restore afterwards."""

    def __init__(self, off):
        self.off = off

    def __enter__(self):
        self.old = pymupdf.TOOLS.unset_quad_corrections()
        pymupdf.TOOLS.unset_quad_corrections(self.off)

    def __exit__(self, *exc):
        pymupdf.TOOLS.unset_quad_corrections(self.old)


# --------------------------------------------------------------------------
# Unit tests on the word extractor with hand-made char dicts (no PDF, no toggle)
# --------------------------------------------------------------------------
def _char(text, x0, top, bottom, line_top=None, width=6):
    d = {
        "text": text,
        "x0": x0,
        "x1": x0 + width,
        "top": top,
        "bottom": bottom,
        "doctop": top,
        "upright": True,
        "matrix": (1, 0, 0, 1, x0, bottom),
    }
    if line_top is not None:
        d["line_top"] = line_top
    return d


def test_line_top_groups_a_low_glyph_with_its_line():
    """Glyph-tight boxes: the "." starts 6.5 pt below the digits. Grouped by
    the shared line top it stays in the number; grouped by the glyph top (the
    fallback for chars without line_top) it does not."""
    tops = {"0": 100, ".": 106.5, "7": 100, "4": 100}
    with_line_top = [
        _char(t, 10 + 6 * i, tops[t], 108, line_top=100) for i, t in enumerate("0.74")
    ]
    assert extract_text(with_line_top) == "0.74"
    legacy = [_char(t, 10 + 6 * i, tops[t], 108) for i, t in enumerate("0.74")]
    assert extract_text(legacy) == "0 74\n."


def test_word_line_top_is_its_smallest_char_line_top():
    """With corrections on every char's line_top equals its box top, and a
    word's line top must then equal its bbox top (the smallest char top) so
    that line clustering of words is unchanged: a word mixing a tall first
    char with lower ones still shares the line of a word at the tall top."""
    word = [_char(t, 10 + 6 * i, top, top + 8, line_top=top)
            for i, (t, top) in enumerate(zip("ABCCC", (100, 102, 104, 104, 104)))]
    other = [_char("X", 60, 100, 108, line_top=100)]
    words = extract_words(word + other)
    assert [w["text"] for w in words] == ["ABCCC", "X"]
    assert words[0]["line_top"] == 100 == words[0]["top"]
    assert extract_text(word + other) == "ABCCC X"


# --------------------------------------------------------------------------
# Integration tests through find_tables()
# --------------------------------------------------------------------------
@pytest.mark.parametrize("quad_off", (False, True))
@pytest.mark.parametrize("rotation", (0, 90, 180, 270))
def test_decimal_point_line_based(rotation, quad_off):
    with _quad_corrections_off(quad_off), pymupdf.open() as doc:
        page = doc.new_page()
        _bordered_grid(page, (72, 72, 472, 152), GRID)
        page.set_rotation(rotation)
        tables = page.find_tables(use_layout=False).tables
        assert len(tables) == 1
        assert tables[0].extract() == _rotated(GRID, rotation)
        # find_tables() leaves the toggle as it found it
        assert pymupdf.TOOLS.unset_quad_corrections() == quad_off


@pytest.mark.parametrize("quad_off", (False, True))
def test_decimal_point_layout_path(quad_off):
    if not pymupdf._layout_available():
        pytest.skip("pymupdf-layout not installed")
    with _quad_corrections_off(quad_off), pymupdf.open() as doc:
        page = doc.new_page()
        _bordered_grid(page, (72, 72, 472, 152), GRID)
        tables = page.find_tables().tables
        assert len(tables) == 1
        # The layout path may add an empty column (a separate issue); each
        # row's non-empty cells must still read as written.
        rows = [[c for c in row if c] for row in tables[0].extract()]
        assert rows == GRID


@pytest.mark.parametrize("quad_off", (False, True))
def test_superscript_stays_on_its_line(quad_off):
    """A raised, smaller footnote marker belongs to the line it annotates.

    Grouping by the baseline alone would put "a" (raised 3.5 pt) on a line of
    its own; the font-metric line top keeps it with "Total", as the corrected
    boxes did.
    """
    with _quad_corrections_off(quad_off), pymupdf.open() as doc:
        page = doc.new_page()
        x0, y0, x1, y1, xm = 72, 380, 372, 420, 222
        for p1, p2 in (((x0, y0), (x1, y0)), ((x0, y1), (x1, y1)),
                       ((x0, y0), (x0, y1)), ((xm, y0), (xm, y1)), ((x1, y0), (x1, y1))):
            page.draw_line(p1, p2)
        page.insert_text((80, 405), "Total", fontsize=11)
        page.insert_text((80 + pymupdf.get_text_length("Total", fontsize=11) + 1, 401.5), "a", fontsize=7)
        page.insert_text((230, 405), "12.5", fontsize=11)
        page.insert_text((230 + pymupdf.get_text_length("12.5", fontsize=11) + 1, 401.5), "*", fontsize=7)
        tables = page.find_tables(use_layout=False).tables
        assert len(tables) == 1
        assert tables[0].extract() == [["Totala", "12.5*"]]


@pytest.mark.parametrize("quad_off", (False, True))
def test_spaces_between_words(quad_off):
    """Small text: word gaps are under the 3 pt x tolerance, so the space
    characters themselves must stay on the line to separate the words."""
    texts = [["Class A/B Overcollateralization", "Event of Default"]]
    with _quad_corrections_off(quad_off), pymupdf.open() as doc:
        page = doc.new_page()
        _bordered_grid(page, (72, 72, 472, 100), texts, fontsize=8)
        tables = page.find_tables(use_layout=False).tables
        assert len(tables) == 1
        assert tables[0].extract() == texts
