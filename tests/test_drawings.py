"""
Extract drawings of a PDF page and compare result with content of
a stored text file.
"""
import io
import os
from pprint import pprint

import fitz

scriptdir = os.path.abspath(os.path.dirname(__file__))
filename = os.path.join(scriptdir, "resources", "symbol-list.pdf")
symbols = os.path.join(scriptdir, "resources", "symbols.txt")


def test_drawings():
    symbols_text = open(symbols).read()
    doc = fitz.open(filename)
    page = doc[0]
    paths = page.get_drawings()
    out = io.StringIO()
    pprint(paths, stream=out)
    assert symbols_text == out.getvalue()
