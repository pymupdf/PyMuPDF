"""Regression tests for source-aware escaping in Table.to_markdown(clean=True)."""

from contextlib import contextmanager

import pymupdf
import pytest


@contextmanager
def _detected_table(value, fontname="helv", merged=False):
    """Create a small real PDF table; keep its page alive until export finishes."""
    doc = pymupdf.open()
    page = doc.new_page(width=500, height=320)
    xs = (40, 250, 460)
    ys = (60, 124, 188, 252) if merged else (60, 124, 188)
    page.draw_rect((xs[0], ys[0], xs[-1], ys[1]), color=None, fill=(0.9, 0.9, 0.9))
    for y in ys:
        page.draw_line((xs[0], y), (xs[-1], y))
    for x in (xs[0], xs[-1]):
        page.draw_line((x, ys[0]), (x, ys[-1]))
    if merged:
        page.draw_line((xs[1], ys[0]), (xs[1], ys[1]))
        page.draw_line((xs[1], ys[2]), (xs[1], ys[3]))
    else:
        page.draw_line((xs[1], ys[0]), (xs[1], ys[-1]))
    rows = [[value, "H2"], [value, None if merged else "KEEP"]]
    if merged:
        rows.append(["LEFT", "RIGHT"])
    for row_no, row in enumerate(rows):
        for col_no, cell in enumerate(row):
            if cell is None:
                continue
            for line_no, line in enumerate(cell.split("\n")):
                page.insert_text((xs[col_no] + 8, ys[row_no] + 20 + line_no * 16),
                                 line, fontname=fontname if row_no == 1 and col_no == 0 else "helv",
                                 fontsize=10)
    try:
        finder = page.find_tables(strategy="lines", use_layout=False)
        assert len(finder.tables) == 1
        table = finder.tables[0]
        assert table.extract() == rows
        assert table.header.external is False
        yield table
    finally:
        doc.close()


@pytest.mark.parametrize("value, expected", [
    ("First line\nSecond line", "First line<br>Second line"),
    ("A-B / -12.5", "A-B / -12.5"),
    ("A--B---C", "A--B---C"),
    ("A<br>B", "A&lt;br&gt;B"),
    ("A&#45;B", "A&amp;#45;B"),
    ("A&amp;B", "A&amp;amp;B"),
    ("A&lt;br&gt;B", "A&amp;lt;br&amp;gt;B"),
    ('"yes" < >', "&quot;yes&quot; &lt; &gt;"),
    ("<b>A-B</b>\nA&B", "&lt;b&gt;A-B&lt;/b&gt;<br>A&amp;B"),
])
def test_markdown_clean_escapes_source_not_generated_line_breaks(value, expected):
    """Headers and body cells distinguish literal markup from actual newlines."""
    with _detected_table(value) as table:
        before_text = table.extract()
        before_names = list(table.header.names)
        assert table.to_markdown(clean=True) == (
            f"|{expected}|H2|\n|---|---|\n|{expected}|KEEP|\n\n"
        )
        assert table.extract() == before_text
        assert table.header.names == before_names


@pytest.mark.parametrize("clean", [False, True])
@pytest.mark.parametrize("fontname, prefix, suffix", [
    ("hebo", "**", "**"),
    ("heit", "_", "_"),
    ("cour", "`", "`"),
    ("hebi", "**_", "_**"),
    ("cobo", "**`", "`**"),
])
def test_markdown_clean_keeps_generated_font_styles(clean, fontname, prefix, suffix):
    """Moving escaping must retain generated formatting around each line."""
    with _detected_table("A-B\nC-D", fontname=fontname) as table:
        body = f"{prefix}A-B{suffix}<br>{prefix}C-D{suffix}"
        assert table.to_markdown(clean=clean) == (
            f"|A-B<br>C-D|H2|\n|---|---|\n|{body}|KEEP|\n\n"
        )


@pytest.mark.parametrize("value", ["A-B\nC-D", "A<br>B", "A&#45;B", "A&B"])
def test_markdown_default_behavior_is_unchanged(value):
    """The opt-in fix must not change default or explicitly unclean output."""
    with _detected_table(value) as table:
        cell = value.replace("\n", "<br>")
        expected = f"|{cell}|H2|\n|---|---|\n|{cell}|KEEP|\n\n"
        assert table.to_markdown() == expected
        assert table.to_markdown(clean=False) == expected


@pytest.mark.parametrize("fill_empty", [False, True])
def test_markdown_clean_preserves_missing_cell_fill(fill_empty):
    """An actual merged cell remains subject to the existing fill_empty rule."""
    with _detected_table("A-B\nC-D", merged=True) as table:
        cell = "A-B<br>C-D"
        filled = cell if fill_empty else ""
        assert table.to_markdown(clean=True, fill_empty=fill_empty) == (
            f"|{cell}|H2|\n|---|---|\n|{cell}|{filled}|\n|LEFT|RIGHT|\n\n"
        )


@pytest.mark.parametrize("external", [False, True])
def test_markdown_clean_external_header_export(external):
    """Exercise the export contract without changing header detection heuristics."""
    with _detected_table("BODY") as table:
        # Export a supplied header; detection itself is tested by the fixture above.
        table.header = pymupdf.table.TableHeader(
            table.bbox, table.rows[0].cells, ["A-B\n<br>", "H2"], above=external
        )
        expected = "|A-B<br>&lt;br&gt;|H2|\n|---|---|\n"
        if external:
            expected += "|BODY|H2|\n"
        expected += "|BODY|KEEP|\n\n"
        assert table.to_markdown(clean=True) == expected
        assert table.header.names == ["A-B\n<br>", "H2"]


@pytest.mark.parametrize("name", [None, ""])
def test_markdown_clean_preserves_generated_empty_header_names(name):
    with _detected_table("BODY") as table:
        table.header = pymupdf.table.TableHeader(
            table.bbox, table.rows[0].cells, [name, "H2"], above=False
        )
        assert table.to_markdown(clean=True) == "|Col1|H2|\n|---|---|\n|BODY|KEEP|\n\n"
        assert table.header.names == [name, "H2"]
