"""
Extract drawings of a PDF page and compare with stored expected result.
"""

import io
import os
import sys
import pprint

import pymupdf

scriptdir = os.path.abspath(os.path.dirname(__file__))
filename = os.path.join(scriptdir, "resources", "symbol-list.pdf")
symbols = os.path.join(scriptdir, "resources", "symbols.txt")


def test_drawings1():
    symbols_text = open(symbols).read()  # expected result
    doc = pymupdf.open(filename)
    page = doc[0]
    paths = page.get_cdrawings()
    out = io.StringIO()  # pprint output goes here
    pprint.pprint(paths, stream=out)
    assert symbols_text == out.getvalue()


def test_drawings2():
    delta = (0, 20, 0, 20)
    doc = pymupdf.open()
    page = doc.new_page()

    r = pymupdf.Rect(100, 100, 200, 200)
    page.draw_circle(r.br, 2, color=0)
    r += delta

    page.draw_line(r.tl, r.br, color=0)
    r += delta

    page.draw_oval(r, color=0)
    r += delta

    page.draw_rect(r, color=0)
    r += delta

    page.draw_quad(r.quad, color=0)
    r += delta

    page.draw_polyline((r.tl, r.tr, r.br), color=0)
    r += delta

    page.draw_bezier(r.tl, r.tr, r.br, r.bl, color=0)
    r += delta

    page.draw_curve(r.tl, r.tr, r.br, color=0)
    r += delta

    page.draw_squiggle(r.tl, r.br, color=0)
    r += delta

    rects = [p["rect"] for p in page.get_cdrawings()]
    bboxes = [b[1] for b in page.get_bboxlog()]
    for i, r in enumerate(rects):
        assert pymupdf.Rect(r) in pymupdf.Rect(bboxes[i])


def _dict_difference(a, b):
    """
    Verifies that dictionaries "a", "b"
    * have the same keys and values, except for key "items":
    * the items list of "a" must be one shorter but otherwise equal the "b" items

    Returns last item of b["items"].
    """
    assert a.keys() == b.keys()
    for k in a.keys():
        v1 = a[k]
        v2 = b[k]
        if k != "items":
            assert v1 == v2
        else:
            assert v1 == v2[:-1]
            rc = v2[-1]
    return rc


def test_drawings3():
    doc = pymupdf.open()
    page1 = doc.new_page()
    shape1 = page1.new_shape()
    shape1.draw_line((10, 10), (10, 50))
    shape1.draw_line((10, 50), (100, 100))
    shape1.finish(closePath=False)
    shape1.commit()
    drawings1 = page1.get_drawings()[0]

    page2 = doc.new_page()
    shape2 = page2.new_shape()
    shape2.draw_line((10, 10), (10, 50))
    shape2.draw_line((10, 50), (100, 100))
    shape2.finish(closePath=True)
    shape2.commit()
    drawings2 = page2.get_drawings()[0]

    assert _dict_difference(drawings1, drawings2) == ("l", (100, 100), (10, 10))

    page3 = doc.new_page()
    shape3 = page3.new_shape()
    shape3.draw_line((10, 10), (10, 50))
    shape3.draw_line((10, 50), (100, 100))
    shape3.draw_line((100, 100), (50, 70))
    shape3.finish(closePath=False)
    shape3.commit()
    drawings3 = page3.get_drawings()[0]

    page4 = doc.new_page()
    shape4 = page4.new_shape()
    shape4.draw_line((10, 10), (10, 50))
    shape4.draw_line((10, 50), (100, 100))
    shape4.draw_line((100, 100), (50, 70))
    shape4.finish(closePath=True)
    shape4.commit()
    drawings4 = page4.get_drawings()[0]

    assert _dict_difference(drawings3, drawings4) == ("l", (50, 70), (10, 10))


def test_2365():
    """Draw a filled rectangle on a new page.

    Then extract the page's vector graphics and confirm that only one path
    was generated which has all the right properties."""
    doc = pymupdf.open()
    page = doc.new_page()
    rect = pymupdf.Rect(100, 100, 200, 200)
    page.draw_rect(
        rect, color=pymupdf.pdfcolor["black"], fill=pymupdf.pdfcolor["yellow"], width=3
    )
    paths = page.get_drawings()
    assert len(paths) == 1
    path = paths[0]
    assert path["type"] == "fs"
    assert path["fill"] == pymupdf.pdfcolor["yellow"]
    assert path["fill_opacity"] == 1
    assert path["color"] == pymupdf.pdfcolor["black"]
    assert path["stroke_opacity"] == 1
    assert path["width"] == 3
    assert path["rect"] == rect


def test_2462():
    """
    Assertion happens, if this code does NOT bring down the interpreter.

    Background:
    We previously ignored clips for non-vector-graphics. However, ending
    a clip does not refer back the object(s) that have been clipped.
    In order to correctly compute the "scissor" rectangle, we now keep track
    of the clipped object type.
    """
    doc = pymupdf.open(f"{scriptdir}/resources/test-2462.pdf")
    page = doc[0]
    vg = page.get_drawings(extended=True)


def test_2556():
    """Ensure that incomplete clip paths will be properly ignored."""
    doc = pymupdf.open()  # new empty PDF
    page = doc.new_page()  # new page
    # following contains an incomplete clip
    c = b"q 50 697.6 400 100.0 re W n q 0 0 m W n Q "
    xref = doc.get_new_xref()  # prepare /Contents object for page
    doc.update_object(xref, "<<>>")  # new xref now is a dictionary
    doc.update_stream(xref, c)  # store drawing commands
    page.set_contents(xref)  # give the page this xref as /Contents
    # following will bring down interpreter if fix not installed
    assert page.get_drawings(extended=True)


def test_3207():
    """Example graphics with multiple "close path" commands within same path.

    The fix translates a close-path commands into an additional line
    which connects the current point with a preceeding "move" target.
    The example page has 2 paths which each contain 2 close-path
    commands after 2 normal "line" commands, i.e. 2 command sequences
    "move-to, line-to, line-to, close-path".
    This is converted into 3 connected lines, where the last end point
    is connect to the start point of the first line.
    So, in the sequence of lines / points

    (p0, p1), (p2, p3), (p4, p5), (p6, p7), (p8, p9), (p10, p11)

    point p5 must equal p0, and p11 must equal p6 (for each of the
    two paths in the example).
    """
    filename = os.path.join(scriptdir, "resources", "test-3207.pdf")
    doc = pymupdf.open(filename)
    page = doc[0]
    paths = page.get_drawings()
    assert len(paths) == 2

    path0 = paths[0]
    items = path0["items"]
    assert len(items) == 6
    p0 = items[0][1]
    p5 = items[2][2]
    p6 = items[3][1]
    p11 = items[5][2]
    assert p0 == p5
    assert p6 == p11

    path1 = paths[1]
    items = path1["items"]
    assert len(items) == 6
    p0 = items[0][1]
    p5 = items[2][2]
    p6 = items[3][1]
    p11 = items[5][2]
    assert p0 == p5
    assert p6 == p11


def test_3591():
    """Confirm correct scaling factor for rotation matrices."""
    filename = os.path.join(scriptdir, "resources", "test-3591.pdf")
    doc = pymupdf.open(filename)
    page = doc[0]
    paths = page.get_drawings()
    for p in paths:
        assert p["width"] == 15
