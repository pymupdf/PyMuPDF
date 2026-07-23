import os
import io
from pprint import pprint
import textwrap
import pickle
import platform
from concurrent.futures import ThreadPoolExecutor

import pymupdf

scriptdir = os.path.abspath(os.path.dirname(__file__))
filename = os.path.join(scriptdir, "resources", "chinese-tables.pdf")
pickle_file = os.path.join(scriptdir, "resources", "chinese-tables.pickle")


def test_table1():
    """Compare pickled tables with those of the current run."""
    pickle_in = open(pickle_file, "rb")
    doc = pymupdf.open(filename)
    page = doc[0]
    tabs = page.find_tables()
    cells = tabs[0].cells + tabs[1].cells  # all table cell tuples on page
    extracts = [tabs[0].extract(), tabs[1].extract()]  # all table cell content
    old_data = pickle.load(pickle_in)  # previously saved data

    # Compare cell contents
    assert old_data["extracts"] == extracts  # same cell contents

    # Compare cell coordinates.
    # Cell rectangles may get somewhat larger due to more cautious border
    # computations, but any differences must be small.
    old_cells = old_data["cells"][0] + old_data["cells"][1]
    assert len(cells) == len(old_cells)
    for i in range(len(cells)):
        c1 = pymupdf.Rect(cells[i])  # new cell coordinates
        c0 = pymupdf.Rect(old_cells[i])  # old cell coordinates
        assert c0 in c1  # always: old contained in new
        assert abs(c1 - c0) < 0.2  # difference must be small


def test_table2():
    """Confirm header properties."""
    doc = pymupdf.open(filename)
    page = doc[0]
    tab1, tab2 = page.find_tables().tables
    # both tables contain their header data
    assert tab1.header.external == False
    assert tab1.header.cells == tab1.rows[0].cells
    assert tab2.header.external == False
    assert tab2.header.cells == tab2.rows[0].cells


def test_2812():
    """Ensure table detection and extraction independent from page rotation.

    Make 4 pages with rotations 0, 90, 180 and 270 degrees respectively.
    Each page shows the same 8x5 table.
    We will check that each table is detected and delivers the same content.
    """
    doc = pymupdf.open()
    # Page 0: rotation 0
    page = doc.new_page(width=842, height=595)
    rect = page.rect + (72, 72, -72, -72)
    cols = 5
    rows = 8
    # define the cells, draw the grid and insert unique text in each cell.
    cells = pymupdf.make_table(rect, rows=rows, cols=cols)
    for i in range(rows):
        for j in range(cols):
            page.draw_rect(cells[i][j])
    for i in range(rows):
        for j in range(cols):
            page.insert_textbox(
                cells[i][j],
                f"cell[{i}][{j}]",
                align=pymupdf.TEXT_ALIGN_CENTER,
            )
    page.clean_contents()

    # Page 1: rotation 90 degrees
    page = doc.new_page()
    rect = page.rect + (72, 72, -72, -72)
    cols = 8
    rows = 5
    cells = pymupdf.make_table(rect, rows=rows, cols=cols)
    for i in range(rows):
        for j in range(cols):
            page.draw_rect(cells[i][j])
    for i in range(rows):
        for j in range(cols):
            page.insert_textbox(
                cells[i][j],
                f"cell[{j}][{rows-i-1}]",
                rotate=90,
                align=pymupdf.TEXT_ALIGN_CENTER,
            )
    page.set_rotation(90)
    page.clean_contents()

    # Page 2: rotation 180 degrees
    page = doc.new_page(width=842, height=595)
    rect = page.rect + (72, 72, -72, -72)
    cols = 5
    rows = 8
    cells = pymupdf.make_table(rect, rows=rows, cols=cols)
    for i in range(rows):
        for j in range(cols):
            page.draw_rect(cells[i][j])
    for i in range(rows):
        for j in range(cols):
            page.insert_textbox(
                cells[i][j],
                f"cell[{rows-i-1}][{cols-j-1}]",
                rotate=180,
                align=pymupdf.TEXT_ALIGN_CENTER,
            )
    page.set_rotation(180)
    page.clean_contents()

    # Page 3: rotation 270 degrees
    page = doc.new_page()
    rect = page.rect + (72, 72, -72, -72)
    cols = 8
    rows = 5
    cells = pymupdf.make_table(rect, rows=rows, cols=cols)
    for i in range(rows):
        for j in range(cols):
            page.draw_rect(cells[i][j])
    for i in range(rows):
        for j in range(cols):
            page.insert_textbox(
                cells[i][j],
                f"cell[{cols-j-1}][{i}]",
                rotate=270,
                align=pymupdf.TEXT_ALIGN_CENTER,
            )
    page.set_rotation(270)
    page.clean_contents()

    pdfdata = doc.tobytes()
    # doc.ez_save("test-2812.pdf")
    doc.close()

    # -------------------------------------------------------------------------
    # Test PDF prepared. Extract table on each page and
    # ensure identical extracted table data.
    # -------------------------------------------------------------------------
    doc = pymupdf.open("pdf", pdfdata)
    extracts = []
    for page in doc:
        tabs = page.find_tables()
        assert len(tabs.tables) == 1
        tab = tabs[0]
        fp = io.StringIO()
        pprint(tab.extract(), stream=fp)
        extracts.append(fp.getvalue())
        fp = None
        assert tab.row_count == 8
        assert tab.col_count == 5
    e0 = extracts[0]
    for e in extracts[1:]:
        assert e == e0


def test_2979():
    """This tests fix #2979 and #3001.

    2979: identical cell count for each row
    3001: no change of global glyph heights
    """
    filename = os.path.join(scriptdir, "resources", "test_2979.pdf")
    doc = pymupdf.open(filename)
    page = doc[0]
    tab = page.find_tables()[0]  # extract the table
    lengths = set()  # stores all row cell counts
    for e in tab.extract():
        lengths.add(len(e))  # store number of cells for row

    # test 2979
    assert len(lengths) == 1

    # test 3001
    assert (
        pymupdf.TOOLS.set_small_glyph_heights() is False
    ), f"{pymupdf.TOOLS.set_small_glyph_heights()=}"

    wt = pymupdf.TOOLS.mupdf_warnings()
    if pymupdf.mupdf_version_tuple >= (1, 28, 0):
        assert ( wt == '' )
    else:
        assert (
            wt
            == "bogus font ascent/descent values (3117 / -2463)\n... repeated 2 times..."
        )


def test_3062():
    """Tests the fix for #3062.
    After table extraction, a rotated page should behave and look
    like as before."""
    if platform.python_implementation() == 'GraalVM':
        print(f'test_3062(): Not running because slow on GraalVM.')
        return
    
    filename = os.path.join(scriptdir, "resources", "test_3062.pdf")
    doc = pymupdf.open(filename)
    page = doc[0]
    tab0 = page.find_tables()[0]
    cells0 = tab0.cells

    page = None
    page = doc[0]
    tab1 = page.find_tables()[0]
    cells1 = tab1.cells
    assert cells1 == cells0


def test_strict_lines():
    """Confirm that ignoring borderless rectangles improves table detection."""
    filename = os.path.join(scriptdir, "resources", "strict-yes-no.pdf")
    doc = pymupdf.open(filename)
    page = doc[0]

    tab1 = page.find_tables()[0]
    tab2 = page.find_tables(strategy="lines_strict")[0]
    assert tab2.row_count < tab1.row_count
    assert tab2.col_count < tab1.col_count


def test_add_lines():
    """Test new parameter add_lines for table recognition."""
    if platform.python_implementation() == 'GraalVM':
        print(f'test_add_lines(): Not running because breaks later tests on GraalVM.')
        return
    
    filename = os.path.join(scriptdir, "resources", "small-table.pdf")
    doc = pymupdf.open(filename)
    page = doc[0]
    assert page.find_tables().tables == []

    more_lines = [
        ((238.9949951171875, 200.0), (238.9949951171875, 300.0)),
        ((334.5559997558594, 200.0), (334.5559997558594, 300.0)),
        ((433.1809997558594, 200.0), (433.1809997558594, 300.0)),
    ]

    # these 3 additional vertical lines should additional 3 columns
    tab2 = page.find_tables(add_lines=more_lines)[0]
    assert tab2.col_count == 4
    assert tab2.row_count == 5


def _make_find_tables_state_doc():
    doc = pymupdf.open()
    page = doc.new_page(width=360, height=220)
    rect = pymupdf.Rect(40, 40, 320, 180)
    cells = pymupdf.make_table(rect, rows=3, cols=3)
    for row_index, row in enumerate(cells):
        for col_index, cell in enumerate(row):
            page.draw_rect(cell)
            page.insert_textbox(
                cell,
                f"r{row_index}c{col_index}",
                align=pymupdf.TEXT_ALIGN_CENTER,
            )
    return doc.tobytes()


def _find_tables_use_layout_false_signature(pdf_bytes):
    doc = pymupdf.open("pdf", pdf_bytes)
    try:
        table = doc[0].find_tables(strategy="lines_strict", use_layout=False)[0]
        return table.row_count, table.col_count, table.extract()
    finally:
        doc.close()


def test_find_tables_use_layout_false_does_not_call_get_layout():
    """use_layout=False must keep find_tables on the pure line-based path."""
    pdf_bytes = _make_find_tables_state_doc()
    doc = pymupdf.open("pdf", pdf_bytes)
    page = doc[0]
    page_cls = type(page)
    original_get_layout = page_cls.get_layout

    def fail_get_layout(self, *args, **kwargs):
        raise AssertionError("get_layout() should not be called")

    page_cls.get_layout = fail_get_layout
    try:
        table = page.find_tables(strategy="lines_strict", use_layout=False)[0]
        assert table.row_count == 3
        assert table.col_count == 3
        assert table.extract()[1][1] == "r1c1"
    finally:
        page_cls.get_layout = original_get_layout
        doc.close()


def test_find_tables_state_is_call_local_for_threads():
    """Concurrent find_tables calls must not mix text/vector extraction state."""
    if platform.python_implementation() == "GraalVM":
        print("test_find_tables_state_is_call_local_for_threads(): not running because slow on GraalVM.")
        return
    if os.environ.get('PYODIDE_ROOT'):
        print('test_find_tables_state_is_call_local_for_threads(): not running on Pyodide - threads unsupported.')
        return

    pdf_bytes = _make_find_tables_state_doc()
    expected = _find_tables_use_layout_false_signature(pdf_bytes)

    # find_tables() saves and restores the process-global TOOLS flags (small
    # glyph heights, quad corrections) around each call; concurrent calls can
    # race that save/restore and leave a flag set. Snapshot the flags here and
    # restore them explicitly so the suite's global-state checks stay clean.
    small_before = bool(pymupdf.TOOLS.set_small_glyph_heights())
    quad_before = bool(pymupdf.TOOLS.unset_quad_corrections())
    try:
        with ThreadPoolExecutor(max_workers=8) as executor:
            results = list(
                executor.map(
                    lambda _: _find_tables_use_layout_false_signature(pdf_bytes),
                    range(32),
                )
            )
    finally:
        pymupdf.TOOLS.set_small_glyph_heights(small_before)
        pymupdf.TOOLS.unset_quad_corrections(quad_before)

    assert results == [expected] * 32


def test_3148():
    """Ensure correct extraction text of rotated text."""
    doc = pymupdf.open()
    page = doc.new_page()
    rect = pymupdf.Rect(100, 100, 300, 300)
    text = (
        "rotation 0 degrees",
        "rotation 90 degrees",
        "rotation 180 degrees",
        "rotation 270 degrees",
    )
    degrees = (0, 90, 180, 270)
    delta = (2, 2, -2, -2)
    cells = pymupdf.make_table(rect, cols=3, rows=4)
    for i in range(3):
        for j in range(4):
            page.draw_rect(cells[j][i])
            k = (i + j) % 4
            page.insert_textbox(cells[j][i] + delta, text[k], rotate=degrees[k])
    # doc.save("multi-degree.pdf")
    tabs = page.find_tables()
    tab = tabs[0]
    for extract in tab.extract():
        for item in extract:
            item = item.replace("\n", " ")
            assert item in text


def test_3179():
    """Test correct separation of multiple tables on page."""
    filename = os.path.join(scriptdir, "resources", "test_3179.pdf")
    doc = pymupdf.open(filename)
    page = doc[0]
    tabs = page.find_tables()
    assert len(tabs.tables) == 3


def test_battery_file():
    """Tests correctly ignoring non-table suspects.

    Earlier versions erroneously tried to identify table headers
    where there existed no table at all.
    """
    filename = os.path.join(scriptdir, "resources", "battery-file-22.pdf")
    doc = pymupdf.open(filename)
    page = doc[0]
    tabs = page.find_tables()
    assert len(tabs.tables) == 0


def test_markdown():
    """Confirm correct markdown output."""
    filename = os.path.join(scriptdir, "resources", "strict-yes-no.pdf")
    doc = pymupdf.open(filename)
    page = doc[0]
    tab = page.find_tables(strategy="lines_strict")[0]
    md_expected = (
        "|Header1|Header2|Header3|\n"
        "|---|---|---|\n"
        "|Col11<br>Col12|Col21<br>Col22|Col31<br>Col32<br>Col33|\n"
        "|Col13|Col23|Col34<br>Col35|\n"
        "|Col14|Col24|Col36|\n"
        "|Col15|Col25<br>Col26||\n\n"
    )


    md = tab.to_markdown()
    assert md == md_expected, f'Incorrect md:\n{textwrap.indent(md, "    ")}'


def test_paths_param():
    """Confirm acceptance of supplied vector graphics list."""
    filename = os.path.join(scriptdir, "resources", "strict-yes-no.pdf")
    doc = pymupdf.open(filename)
    page = doc[0]
    tabs = page.find_tables(paths=[])  # will cause all tables are missed
    assert tabs.tables == []


def test_boxes_param():
    """Confirm acceptance of supplied boxes list."""
    filename = os.path.join(scriptdir, "resources", "small-table.pdf")
    doc = pymupdf.open(filename)
    page = doc[0]
    paths = page.get_drawings()
    box0 = page.cluster_drawings(drawings=paths)[0]
    boxes = [box0]
    words = page.get_text("words")
    x_vals = [w[0] - 5 for w in words if w[4] in ("min", "max", "avg")]
    for x in x_vals:
        r = +box0
        r.x1 = x
        boxes.append(r)

    y_vals = sorted(set([round(w[3]) for w in words]))
    for y in y_vals[:-1]:  # skip last one to avoid empty row
        r = +box0
        r.y1 = y
        boxes.append(r)

    tabs = page.find_tables(paths=[], add_boxes=boxes)
    tab = tabs.tables[0]
    assert tab.extract() == [
        ["Boiling Points °C", "min", "max", "avg"],
        ["Noble gases", "-269", "-62", "-170.5"],
        ["Nonmetals", "-253", "4827", "414.1"],
        ["Metalloids", "335", "3900", "741.5"],
        ["Metals", "357", ">5000", "2755.9"],
    ]


def test_dotted_grid():
    """Confirm dotted lines are detected as gridlines."""
    filename = os.path.join(scriptdir, "resources", "dotted-gridlines.pdf")
    doc = pymupdf.open(filename)
    page = doc[0]
    tabs = page.find_tables()
    assert len(tabs.tables) == 3  # must be 3 tables
    t0, t1, t2 = tabs  # extract them
    # check that they have expected dimensions
    assert t0.row_count, t0.col_count == (11, 12)
    assert t1.row_count, t1.col_count == (25, 11)
    assert t2.row_count, t2.col_count == (1, 10)


def test_4017():
    path = os.path.normpath(f"{__file__}/../../tests/resources/test_4017.pdf")
    with pymupdf.open(path) as document:
        page = document[0]

        tables = page.find_tables(add_lines=None)
        print(f"{len(tables.tables)=}.")
        tables_text = list()
        for i, table in enumerate(tables):
            print(f"## {i=}.")
            t = table.extract()
            for tt in t:
                print(f"    {tt}")

        # 2024-11-29: expect current incorrect output for last two tables.

        expected_a = [
            ["Class A/B Overcollateralization", "131.44%", ">=", "122.60%", "", "PASS"],
            [None, None, None, None, None, "PASS"],
            ["Class D Overcollateralization", "112.24%", ">=", "106.40%", "", "PASS"],
            [None, None, None, None, None, "PASS"],
            ["Event of Default", "156.08%", ">=", "102.50%", "", "PASS"],
            [None, None, None, None, None, "PASS"],
            ["Class A/B Interest Coverage", "N/A", ">=", "120.00%", "", "N/A"],
            [None, None, None, None, None, "N/A"],
            ["Class D Interest Coverage", "N/A", ">=", "105.00%", "", "N/A"],
        ]
        assert tables[-2].extract() == expected_a

        expected_b = [
            [
                "Moody's Maximum Rating Factor Test",
                "2,577",
                "<=",
                "3,250",
                "",
                "PASS",
                "2,581",
            ],
            [None, None, None, None, None, "PASS", None],
            [
                "Minimum Floating Spread",
                "3.5006%",
                ">=",
                "2.0000%",
                "",
                "PASS",
                "3.4871%",
            ],
            [None, None, None, None, None, "PASS", None],
            [
                "Minimum Weighted Average S&P Recovery\nRate Test",
                "40.50%",
                ">=",
                "40.00%",
                "",
                "PASS",
                "40.40%",
            ],
            [None, None, None, None, None, "PASS", None],
            ["Weighted Average Life", "4.83", "<=", "9.00", "", "PASS", "4.92"],
        ]
        assert tables[-1].extract() == expected_b


def test_md_styles():
    """Test output of table with MD-styled cells."""
    filename = os.path.join(scriptdir, "resources", "test-styled-table.pdf")
    doc = pymupdf.open(filename)
    page = doc[0]
    tabs = page.find_tables()[0]
    text = """|Column 1|Column 2|Column 3|\n|---|---|---|\n|Zelle (0,0)|**Bold (0,1)**|Zelle (0,2)|\n|~~Strikeout (1,0), Zeile 1~~<br>~~Hier kommt Zeile 2.~~|Zelle (1,1)|~~Strikeout (1,2)~~|\n|**`Bold-monospaced`**<br>**`(2,0)`**|_Italic (2,1)_|**_Bold-italic_**<br>**_(2,2)_**|\n|Zelle (3,0)|~~**Bold-strikeout**~~<br>~~**(3,1)**~~|Zelle (3,2)|\n\n"""
    assert tabs.to_markdown() == text


def _make_marker_table_doc(marker):
    """Build a 1-page doc with a small drawn table whose cells embed `marker`."""
    doc = pymupdf.open()
    page = doc.new_page(width=360, height=220)
    rect = pymupdf.Rect(40, 40, 320, 180)
    cells = pymupdf.make_table(rect, rows=2, cols=2)
    for row_index, row in enumerate(cells):
        for col_index, cell in enumerate(row):
            page.draw_rect(cell)
            page.insert_textbox(
                cell,
                f"{marker}-{row_index}{col_index}",
                align=pymupdf.TEXT_ALIGN_CENTER,
            )
    page.clean_contents()
    return doc


def test_table_extract_stable_after_second_find_tables():
    """Regression test for the stale-CHARS bug.

    find_tables() snapshots table._chars right after each call so that an
    already-returned Table's extract() cannot silently pick up a later,
    unrelated find_tables() call's live (ContextVar-backed) CHARS content.
    """
    doc1 = _make_marker_table_doc("PAGE1")
    doc2 = _make_marker_table_doc("PAGE2")
    try:
        table1 = doc1[0].find_tables(strategy="lines_strict")[0]
        first = table1.extract()

        # An unrelated find_tables() call on a different page/doc resets and
        # repopulates the shared CHARS state used during text extraction.
        doc2[0].find_tables(strategy="lines_strict")

        assert table1.extract() == first
        flat_text = " ".join(cell for row in first for cell in row if cell)
        assert "PAGE1" in flat_text  # guard against both-empty passes
        assert "PAGE2" not in flat_text
    finally:
        doc1.close()
        doc2.close()


def test_find_tables_use_layout_true_without_layout_is_line_based():
    """use_layout=True (the default) must gracefully degrade to the pure
    line-based detection path when the optional layout wheel/model is not
    available: get_layout() becomes a no-op, page.layout_information stays
    None, and results must match use_layout=False exactly."""
    pdf_bytes = _make_find_tables_state_doc()
    doc = pymupdf.open("pdf", pdf_bytes)
    page = doc[0]
    original_get_layout_fn = pymupdf._get_layout
    pymupdf._get_layout = None  # simulate: pymupdf.layout wheel not installed
    try:
        tables_true = page.find_tables(strategy="lines_strict", use_layout=True)
        assert page.layout_information is None

        tables_false = page.find_tables(strategy="lines_strict", use_layout=False)

        assert len(tables_true.tables) == 1
        assert [t.extract() for t in tables_true] == [
            t.extract() for t in tables_false
        ]
        table = tables_true[0]
        assert table.row_count == 3
        assert table.col_count == 3
        assert table.extract()[1][1] == "r1c1"
    finally:
        pymupdf._get_layout = original_get_layout_fn
        doc.close()


def _make_overmerged_page():
    """A page whose line grid detects one tall body row that actually holds
    three record lines -- an under-segmented (over-merged) grid the refinement
    is meant to repair. Needs no layout, so it exercises the standalone benefit.
    """
    doc = pymupdf.open()
    page = doc.new_page(width=400, height=300)
    # 2-column grid: header row 100-120, a single tall body row 120-200.
    for y in (100, 120, 200):
        page.draw_line((100, y), (300, y))
    for x in (100, 200, 300):
        page.draw_line((x, 100), (x, 200))
    page.insert_text((130, 114), "A")
    page.insert_text((230, 114), "B")
    # Three record lines crammed into the one body row.
    for i, y in enumerate((140, 160, 180), start=1):
        page.insert_text((130, y), str(i))
        page.insert_text((230, y), str(i * 10))
    return doc, page


def test_refine_grid_splits_overmerged_body():
    """refine_grid() splits an over-merged body row into one row per record.

    *** PyMuPDF extension (opt-in grid refinement). ***
    """
    doc, page = _make_overmerged_page()
    try:
        grid = [
            [[100, 100, 200, 120], [200, 100, 300, 120]],  # header row
            [[100, 120, 200, 200], [200, 120, 300, 200]],  # one over-merged body row
        ]
        refined = pymupdf.table.refine_grid(page, grid, header_row_count=1)
        # header kept, body row split into the three record rows
        assert len(grid) == 2  # input untouched
        assert len(refined) == 4
        assert refined[0] == grid[0]  # header preserved verbatim
        assert all(len(r) == 2 for r in refined)
    finally:
        doc.close()


def test_find_tables_refine_splits_rows_default_unchanged():
    """find_tables(refine=True) repairs the over-merged grid; the default result
    is unchanged -- refinement is strictly opt-in.

    *** PyMuPDF extension. ***
    """
    doc, page = _make_overmerged_page()
    try:
        default = page.find_tables(use_layout=False)
        refined = page.find_tables(use_layout=False, refine=True)
        assert len(default.tables) == 1
        assert len(refined.tables) == 1

        # Default detects the merged 2-row grid (unchanged behaviour).
        assert default.tables[0].row_count == 2
        assert default.tables[0].col_count == 2

        # refine=True splits the body into three record rows.
        t = refined.tables[0]
        assert t.row_count == 4
        assert t.col_count == 2
        assert t.extract() == [
            ["A", "B"],
            ["1", "10"],
            ["2", "20"],
            ["3", "30"],
        ]
    finally:
        doc.close()


def _make_merged_header_page():
    """A page whose line grid detects a header cell that spans both body columns.

    The middle vertical divider is drawn only in the body (below the header
    separator), so the top row is one wide cell over two columns while each body
    row has two cells -- a merged header cell find_tables detects on its own.
    Needs no layout, so it exercises the standalone benefit.
    """
    doc = pymupdf.open()
    page = doc.new_page(width=400, height=300)
    for y in (100, 120, 140, 160):
        page.draw_line((100, y), (300, y))
    page.draw_line((100, 100), (100, 160))  # left border
    page.draw_line((300, 100), (300, 160))  # right border
    page.draw_line((200, 120), (200, 160))  # middle divider: body only
    page.insert_text((150, 114), "Merged Header")
    page.insert_text((120, 134), "a")
    page.insert_text((220, 134), "b")
    page.insert_text((120, 154), "c")
    page.insert_text((220, 154), "d")
    return doc, page


def test_resolve_spans_merged_header():
    """resolve_spans() surfaces a merged header cell as a colspan-2 SpanCell.

    *** PyMuPDF extension (opt-in span resolution). ***
    """
    doc, page = _make_merged_header_page()
    try:
        grid = [
            [[100, 100, 300, 120]],  # header spanning both columns
            [[100, 120, 200, 140], [200, 120, 300, 140]],
            [[100, 140, 200, 160], [200, 140, 300, 160]],
        ]
        placements = pymupdf.table.resolve_spans(page, grid)
        assert len(placements) == 3
        # header is one placement spanning both columns
        assert len(placements[0]) == 1
        head = placements[0][0]
        assert (head.colspan, head.rowspan) == (2, 1)
        assert head.bbox == (100.0, 100.0, 300.0, 120.0)
        assert "Merged Header" in head.text
        # resolve_spans leaves the HTML tag at its default; tagging td/th is the
        # caller's job (find_tables(refine=True) / the engine model builder).
        assert head.tag == "td"
        # body cells stay 1x1
        assert [(c.colspan, c.rowspan) for c in placements[1]] == [(1, 1), (1, 1)]
        assert [c.text for c in placements[2]] == ["c", "d"]
    finally:
        doc.close()


def test_find_tables_refine_exposes_placements_default_none():
    """find_tables(refine=True) attaches Table.placements with the colspan/rowspan
    structure; the default result exposes no placements and is otherwise unchanged.

    *** PyMuPDF extension. ***
    """
    doc, page = _make_merged_header_page()
    try:
        default = page.find_tables(use_layout=False)
        refined = page.find_tables(use_layout=False, refine=True)
        assert len(default.tables) == 1
        assert len(refined.tables) == 1

        # Default detects the merged-header grid but resolves no spans.
        dt = default.tables[0]
        assert (dt.row_count, dt.col_count) == (3, 2)
        assert dt.placements is None

        # refine=True exposes the header cell's colspan via .placements.
        t = refined.tables[0]
        assert t.placements is not None
        assert t.placements[0][0].colspan == 2
        assert t.placements[0][0].rowspan == 1
        assert [c.colspan for c in t.placements[1]] == [1, 1]
        # placements are tagged: the top header row is th, body rows are td.
        assert t.placements[0][0].tag == "th"
        assert [c.tag for c in t.placements[1]] == ["td", "td"]
        assert [c.tag for c in t.placements[2]] == ["td", "td"]
    finally:
        doc.close()


def test_find_tables_refine_to_html_merged_header():
    """find_tables(refine=True) + Table.to_html() serialize a merged header as a
    <th colspan=2>, with body rows as <td>.

    *** PyMuPDF extension (opt-in header tagging + HTML serialization). ***
    """
    doc, page = _make_merged_header_page()
    try:
        t = page.find_tables(use_layout=False, refine=True).tables[0]
        html = t.to_html()
        assert html == (
            "<table>"
            '<tr><th colspan="2">Merged Header</th></tr>'
            "<tr><td>a</td><td>b</td></tr>"
            "<tr><td>c</td><td>d</td></tr>"
            "</table>"
        )
    finally:
        doc.close()


def test_find_tables_refine_header_meta():
    """find_tables(refine=True) exposes the header meta (header_rows/section_rows)
    on the Table; the default path leaves the conservative defaults.

    *** PyMuPDF extension. ***
    """
    doc, page = _make_merged_header_page()
    try:
        default = page.find_tables(use_layout=False).tables[0]
        assert (default.header_rows, default.section_rows) == (0, ())

        t = page.find_tables(use_layout=False, refine=True).tables[0]
        assert isinstance(t.header_rows, int) and t.header_rows == 1
        assert isinstance(t.section_rows, tuple) and t.section_rows == ()
    finally:
        doc.close()


def test_table_to_html_fallback_flat():
    """Table.to_html() on a default (non-refined) table returns a well-formed,
    td-only flat <table> built from extract() -- no placements needed.

    *** PyMuPDF extension. ***
    """
    doc, page = _make_merged_header_page()
    try:
        t = page.find_tables(use_layout=False).tables[0]
        assert t.placements is None
        html = t.to_html()
        assert html.startswith("<table>") and html.endswith("</table>")
        assert "<th" not in html  # flat fallback is td-only
        assert html.count("<tr>") == t.row_count
        # every cell is a plain <td>; the merged header text lands in one cell
        assert "<td>Merged Header</td>" in html
        assert "<td>a</td>" in html and "<td>d</td>" in html
    finally:
        doc.close()


def test_render_table_html_section_row_collapse():
    """The core serializer collapses a section-label row (a lone centered label)
    to a single <th colspan=N>, and honours per-cell td/th tags + colspan.

    *** PyMuPDF extension (HTML serialization). ***
    """
    from pymupdf._table_headers import render_table_html
    from pymupdf.table import SpanCell

    def cell(text, colspan=1, rowspan=1, tag="td"):
        return SpanCell(bbox=None, text=text, colspan=colspan, rowspan=rowspan, tag=tag)

    rows = [
        [cell("Group", colspan=3, tag="th")],
        [cell(""), cell("Section", tag="th"), cell("")],  # centered section label
        [cell("x"), cell("1"), cell("2")],
    ]
    html = render_table_html(rows, section_header_rows=(1,))
    assert html == (
        "<table>"
        '<tr><th colspan="3">Group</th></tr>'
        '<tr><th colspan="3">Section</th></tr>'
        "<tr><td>x</td><td>1</td><td>2</td></tr>"
        "</table>"
    )
    # escaping (& < >) and <br/> line joins, quotes left literal
    assert render_table_html([[cell('a & b < c > "d"\nsecond')]]) == (
        '<table><tr><td>a &amp; b &lt; c &gt; "d"<br/>second</td></tr></table>'
    )


def _make_bordered_table(page, x0, y0, texts):
    """Draw a bordered 2x2 table (cells 100 wide, 20 tall) at (x0, y0), with the
    2x2 ``texts`` grid inserted into its cells; returns nothing (mutates page)."""
    x1, x2 = x0 + 100, x0 + 200
    y1, y2 = y0 + 20, y0 + 40
    for y in (y0, y1, y2):
        page.draw_line((x0, y), (x2, y))
    for x in (x0, x1, x2):
        page.draw_line((x, y0), (x, y2))
    for r, ry in enumerate((y0, y1)):
        for c, cx in enumerate((x0, x1)):
            page.insert_text((cx + 5, ry + 14), texts[r][c])


def test_find_tables_union_fuses_layout_grid_with_line_candidate():
    """find_tables(union=True) fuses the layout analyzer's GNN table grids with
    the line-based finder's candidates: a layout table with no matching line
    candidate is kept from its GNN grid, and a disjoint line-detected table is
    appended -- layout order first, then appended candidates.

    *** PyMuPDF extension (opt-in layout/candidate union). ***
    """
    import types

    doc = pymupdf.open()
    page = doc.new_page(width=500, height=500)
    # Table B: a real bordered 2x2 table the line finder detects (disjoint from A).
    _make_bordered_table(page, 80, 300, [["b00", "b01"], ["b10", "b11"]])
    try:
        # Table A: only a layout (GNN) grid, no drawn lines. Inject the raw layout
        # form union reads (return_raw=True shape): a "table" group whose
        # table_grid carries interior h_lines/v_lines offsets.
        grid_pred = types.SimpleNamespace(h_lines=[20.0], v_lines=[100.0])
        page.layout_information = [
            {
                "class_name": "table",
                "group_bbox": [80.0, 80.0, 280.0, 120.0],
                "table_grid": grid_pred,
            }
        ]
        tf = page.find_tables(use_layout=True, union=True)
        tables = tf.tables
        assert len(tables) == 2

        # A first (layout order): a 2x2 grid built from group_bbox + interior lines.
        a = tables[0]
        assert (a.row_count, a.col_count) == (2, 2)
        assert tuple(a.bbox) == (80.0, 80.0, 280.0, 120.0)
        a_cells = [[cell for cell in row.cells] for row in a.rows]
        assert a_cells[0][0] == (80.0, 80.0, 180.0, 100.0)
        assert a_cells[1][1] == (180.0, 100.0, 280.0, 120.0)

        # B appended after the layout table: the line-detected grid, extractable.
        b = tables[1]
        assert (b.row_count, b.col_count) == (2, 2)
        assert b.extract()[0][0] == "b00"
    finally:
        doc.close()


def test_find_tables_union_no_layout_degrades_to_line_candidates():
    """union=True degrades to the pure line-based candidates when the layout
    analyzer is unavailable: get_layout() is a no-op, layout_information stays
    None, there are no primary grids, so every line-detected table is appended --
    matching the plain line-based find_tables result.

    *** PyMuPDF extension. ***
    """
    doc = pymupdf.open()
    page = doc.new_page(width=400, height=400)
    _make_bordered_table(page, 80, 80, [["a", "b"], ["c", "d"]])
    original_get_layout_fn = pymupdf._get_layout
    pymupdf._get_layout = None  # simulate: pymupdf.layout wheel not installed
    try:
        union = page.find_tables(use_layout=True, union=True)
        assert page.layout_information is None

        line = page.find_tables(strategy="lines_strict", use_layout=False)
        assert len(union.tables) == 1
        # Same table as the pure line-based path, just routed through the union.
        assert [t.extract() for t in union.tables] == [t.extract() for t in line.tables]
        t = union.tables[0]
        assert (t.row_count, t.col_count) == (2, 2)
        assert t.extract()[0][0] == "a"
    finally:
        pymupdf._get_layout = original_get_layout_fn
        doc.close()
