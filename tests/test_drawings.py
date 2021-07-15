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
    r = fitz.Rect(100, 100, 200, 200)
    page.draw_circle(r.br, 2)
    page.draw_line(r.tl, r.br)
    page.draw_oval(r)
    page.draw_rect(r)
    page.draw_quad(r.quad)
    page.draw_polyline((r.tl, r.tr, r.br))
    page.draw_bezier(r.tl, r.tr, r.br, r.bl)
    page.draw_curve(r.tl, r.tr, r.br)
    # page.draw_zigzag(r.tl, r.br)
    page.draw_squiggle(r.tl, r.br)
