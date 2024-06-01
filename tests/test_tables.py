import os
import io
from pprint import pprint
import pymupdf
import pickle

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


def test_3062():
    """Tests the fix for #3062.
    After table extraction, a rotated page should behave and look
    like as before."""
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
    text = (
        "|Header1|Header2|Header3|\n"
        "|---|---|---|\n"
        "|Col11 Col12|Col21 Col22|Col31 Col32 Col33|\n"
        "|Col13|Col23|Col34 Col35|\n"
        "|Col14|Col24|Col36|\n"
        "|Col15|Col25 Col26||\n\n"
    )
    assert tab.to_markdown() == text


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
