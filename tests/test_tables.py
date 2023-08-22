import os
import fitz
import pickle

scriptdir = os.path.abspath(os.path.dirname(__file__))
filename = os.path.join(scriptdir, "resources", "chinese-tables.pdf")
pickle_file = os.path.join(scriptdir, "resources", "chinese-tables.pickle")


def test_table1():
    """Compare pickled tables with those of the current run."""
    pickle_in = open(pickle_file, "rb")
    doc = fitz.open(filename)
    page = doc[0]
    tabs = page.find_tables()
    cells = [tabs[0].cells, tabs[1].cells]
    extracts = [tabs[0].extract(), tabs[1].extract()]
    new_data = {"cells": cells, "extracts": extracts}
    old_data = pickle.load(pickle_in)
    assert old_data == new_data


def test_table2():
    """Confirm header properties."""
    doc = fitz.open(filename)
    page = doc[0]
    tab1, tab2 = page.find_tables().tables
    # both tables contain their header data
    assert tab1.header.external == False
    assert tab1.header.cells == tab1.rows[0].cells
    assert tab2.header.external == False
    assert tab2.header.cells == tab2.rows[0].cells
