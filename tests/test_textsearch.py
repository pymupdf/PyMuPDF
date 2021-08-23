"""
"test_search1":
Search for some text on a PDF page, and compare content of returned hit
rectangle with the searched text.

"test_search2":
Text search with 'clip' parameter - clip rectangle contains two occurrences
of searched text. Confirm search locations are inside clip.
"""
import os

import fitz

scriptdir = os.path.abspath(os.path.dirname(__file__))
filename1 = os.path.join(scriptdir, "resources", "2.pdf")
filename2 = os.path.join(scriptdir, "resources", "github_sample.pdf")


def test_search1():
    doc = fitz.open(filename1)
    page = doc[0]
    needle = "mupdf"
    rlist = page.search_for(needle)
    assert rlist != []
    for rect in rlist:
        assert needle in page.get_textbox(rect).lower()


def test_search2():
    doc = fitz.open(filename2)
    page = doc[0]
    needle = "the"
    clip = fitz.Rect(40.5, 228.31436157226562, 346.5226135253906, 239.5338592529297)
    rl = page.search_for(needle, clip=clip)
    assert len(rl) == 2
    for r in rl:
        assert r in clip
