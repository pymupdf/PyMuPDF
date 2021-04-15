"""
Search for some text on a PDF page, and compare content of returned hit
rectangle with its actual content.
"""
import os

import fitz

scriptdir = os.path.abspath(os.path.dirname(__file__))
filename = os.path.join(scriptdir, "resources", "2.pdf")


def test_search():
    doc = fitz.open(filename)
    page = doc[0]
    needle = "version"
    rlist = page.search_for(needle)
    assert needle == page.get_textbox(rlist[0])
