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
    paths = page.get_cdrawings()
    out = io.StringIO()  # pprint output goes here
    pprint(paths, stream=out)
    assert symbols_text == out.getvalue()


def test_drawings2():
    delta = (0, 20, 0, 20)
    doc = fitz.open()
    page = doc.new_page()

    r = fitz.Rect(100, 100, 200, 200)
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
        assert fitz.Rect(r) in fitz.Rect(bboxes[i])
