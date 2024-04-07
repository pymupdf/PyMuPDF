import os
import fitz

scriptdir = os.path.dirname(__file__)


def test_cluster1():
    """Confirm correct identification of known examples."""
    if not hasattr(fitz, "mupdf"):
        print("Not executing 'test_cluster1' in classic")
        return
    filename = os.path.join(scriptdir, "resources", "symbol-list.pdf")
    doc = fitz.open(filename)
    page = doc[0]
    assert len(page.cluster_drawings()) == 10
    filename = os.path.join(scriptdir, "resources", "chinese-tables.pdf")
    doc = fitz.open(filename)
    page = doc[0]
    assert len(page.cluster_drawings()) == 2


def test_cluster2():
    """Join disjoint but neighbored drawings."""
    if not hasattr(fitz, "mupdf"):
        print("Not executing 'test_cluster2' in classic")
        return
    doc = fitz.open()
    page = doc.new_page()
    r1 = fitz.Rect(100, 100, 200, 200)
    r2 = fitz.Rect(203, 203, 400, 400)
    page.draw_rect(r1)
    page.draw_rect(r2)
    assert page.cluster_drawings() == [r1 | r2]


def test_cluster3():
    """Confirm as separate if neighborhood threshold exceeded."""
    if not hasattr(fitz, "mupdf"):
        print("Not executing 'test_cluster3' in classic")
        return
    doc = fitz.open()
    page = doc.new_page()
    r1 = fitz.Rect(100, 100, 200, 200)
    r2 = fitz.Rect(204, 200, 400, 400)
    page.draw_rect(r1)
    page.draw_rect(r2)
    assert page.cluster_drawings() == [r1, r2]
