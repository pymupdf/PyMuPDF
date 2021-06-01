"""
Extract drawings of a PDF page and compare with stored expected result.
"""
import io
import os
from pprint import pprint

import fitz

scriptdir = os.path.abspath(os.path.dirname(__file__))
filename = os.path.join(scriptdir, "resources", "symbol-list.pdf")
symbols = os.path.join(scriptdir, "resources", "symbols.txt")


def test_drawings1():
    symbols_text = open(symbols).read()  # expected result
    doc = fitz.open(filename)
    page = doc[0]
    paths = page.get_drawings()
    out = io.StringIO()  # pprint output goes here
    pprint(paths, stream=out)
    assert symbols_text == out.getvalue()


def test_drawings2():
    doc = fitz.open()
    page = doc.new_page()
    page.draw_circle((100, 100), 2)
