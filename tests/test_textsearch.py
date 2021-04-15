"""
Search for some text on a PDF page, and compare content of returned hit
rectangle with the searched text.
"""
import os

import fitz

scriptdir = os.path.abspath(os.path.dirname(__file__))
filename = os.path.join(scriptdir, "resources", "2.pdf")


def test_search():
    doc = fitz.open(filename)
    page = doc[0]
    needle = "mupdf"
    rlist = page.search_for(needle)
    for rect in rlist:
        assert needle in page.get_textbox(rect).lower()
