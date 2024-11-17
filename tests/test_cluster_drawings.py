import os
import pymupdf

scriptdir = os.path.dirname(__file__)


def test_cluster1():
    """Confirm correct identification of known examples."""
    if not hasattr(pymupdf, "mupdf"):
        print("Not executing 'test_cluster1' in classic")
        return
    filename = os.path.join(scriptdir, "resources", "symbol-list.pdf")
    doc = pymupdf.open(filename)
    page = doc[0]
    assert len(page.cluster_drawings()) == 10
    filename = os.path.join(scriptdir, "resources", "chinese-tables.pdf")
    doc = pymupdf.open(filename)
    page = doc[0]
    assert len(page.cluster_drawings()) == 2


def test_cluster2():
    """Join disjoint but neighbored drawings."""
    if not hasattr(pymupdf, "mupdf"):
        print("Not executing 'test_cluster2' in classic")
        return
    doc = pymupdf.open()
    page = doc.new_page()
    r1 = pymupdf.Rect(100, 100, 200, 200)
    r2 = pymupdf.Rect(203, 203, 400, 400)
    page.draw_rect(r1)
    page.draw_rect(r2)
    assert page.cluster_drawings() == [r1 | r2]


def test_cluster3():
    """Confirm as separate if neighborhood threshold exceeded."""
    if not hasattr(pymupdf, "mupdf"):
        print("Not executing 'test_cluster3' in classic")
        return
    doc = pymupdf.open()
    page = doc.new_page()
    r1 = pymupdf.Rect(100, 100, 200, 200)
    r2 = pymupdf.Rect(204, 200, 400, 400)
    page.draw_rect(r1)
    page.draw_rect(r2)
    assert page.cluster_drawings() == [r1, r2]
