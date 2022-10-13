"""
* Check EPUB document is no PDF
* Check page access using (chapter, page) notation
* Re-layout EPUB ensuring a previous location is memorized
"""
import os

import fitz

scriptdir = os.path.abspath(os.path.dirname(__file__))
filename = os.path.join(scriptdir, "resources", "Bezier.epub")
doc = fitz.open(filename)


def test_isnopdf():
    assert not doc.is_pdf


def test_pageids():
    assert doc.chapter_count == 7
    assert doc.last_location == (6, 1)
    assert doc.prev_location((6, 0)) == (5, 11)
    assert doc.next_location((5, 11)) == (6, 0)
    # Check page numbers have no gaps:
    i = 0
    for chapter in range(doc.chapter_count):
        for cpno in range(doc.chapter_page_count(chapter)):
            assert doc.page_number_from_location((chapter, cpno)) == i
            i += 1

def test_layout():
    """Memorize a page location, re-layout with ISO-A4, assert pre-determined location."""
    loc = doc.make_bookmark((5, 11))
    doc.layout(fitz.Rect(fitz.paper_rect("a4")))
    assert doc.find_bookmark(loc) == (5, 6)
