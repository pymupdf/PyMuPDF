# -*- coding: utf-8 -*-
"""
-------------------------------------------------------------------------------
Demo script showing how annotations can be added to a PDF using PyMuPDF.

It contains the following annotation types:
Caret, Text, FreeText, text markers (underline, strike-out, highlight,
squiggle), Circle, Square, Line, PolyLine, Polygon, FileAttachment, Stamp
and Redaction.
There is some effort to vary appearances by adding colors, line ends,
opacity, rotation, dashed lines, etc.

Dependencies
------------
PyMuPDF v1.17.0
-------------------------------------------------------------------------------
"""
from __future__ import print_function

import gc
import os
import sys

import fitz

print(fitz.__doc__)
if fitz.VersionBind.split(".") < ["1", "17", "0"]:
    sys.exit("PyMuPDF v1.17.0+ is needed.")

gc.set_debug(gc.DEBUG_UNCOLLECTABLE)

highlight = "this text is highlighted"
underline = "this text is underlined"
strikeout = "this text is striked out"
squiggled = "this text is zigzag-underlined"
red = (1, 0, 0)
blue = (0, 0, 1)
gold = (1, 1, 0)
green = (0, 1, 0)

displ = fitz.Rect(0, 50, 0, 50)
r = fitz.Rect(72, 72, 220, 100)
t1 = u"têxt üsès Lätiñ charß,\nEUR: €, mu: µ, super scripts: ²³!"


def print_descr(annot):
    """Print a short description to the right of each annot rect."""
    annot.parent.insertText(
        annot.rect.br + (10, -5), "%s annotation" % annot.type[1], color=red
    )


doc = fitz.open()
page = doc.newPage()

page.setRotation(0)

annot = page.addCaretAnnot(r.tl)
print_descr(annot)

r = r + displ
annot = page.addFreetextAnnot(
    r,
    t1,
    fontsize=10,
    rotate=90,
    text_color=blue,
    fill_color=gold,
    align=fitz.TEXT_ALIGN_CENTER,
)
annot.setBorder(width=0.3, dashes=[2])
annot.update(text_color=blue, fill_color=gold)

print_descr(annot)
r = annot.rect + displ

annot = page.addTextAnnot(r.tl, t1)
print_descr(annot)

# Adding text marker annotations:
# first insert a unique text, then search for it, then mark it
pos = annot.rect.tl + displ.tl
page.insertText(
    pos,  # insertion point
    highlight,  # inserted text
    morph=(pos, fitz.Matrix(-5)),  # rotate around insertion point
)
rl = page.searchFor(highlight, quads=True)  # need a quad b/o tilted text
annot = page.addHighlightAnnot(rl[0])
print_descr(annot)
pos = annot.rect.bl  # next insertion point

page.insertText(pos, underline, morph=(pos, fitz.Matrix(-10)))
rl = page.searchFor(underline, quads=True)
annot = page.addUnderlineAnnot(rl[0])
print_descr(annot)
pos = annot.rect.bl

page.insertText(pos, strikeout, morph=(pos, fitz.Matrix(-15)))
rl = page.searchFor(strikeout, quads=True)
annot = page.addStrikeoutAnnot(rl[0])
print_descr(annot)
pos = annot.rect.bl

page.insertText(pos, squiggled, morph=(pos, fitz.Matrix(-20)))
rl = page.searchFor(squiggled, quads=True)
annot = page.addSquigglyAnnot(rl[0])
print_descr(annot)
pos = annot.rect.bl

r = fitz.Rect(pos, pos.x + 75, pos.y + 35) + (0, 20, 0, 20)
annot = page.addPolylineAnnot([r.bl, r.tr, r.br, r.tl])  # 'Polyline'
annot.setBorder(width=0.3, dashes=[2])
annot.setColors(stroke=blue, fill=green)
annot.setLineEnds(fitz.PDF_ANNOT_LE_CLOSED_ARROW, fitz.PDF_ANNOT_LE_R_CLOSED_ARROW)
annot.update(fill_color=(1, 1, 0))
print_descr(annot)

r += displ
annot = page.addPolygonAnnot([r.bl, r.tr, r.br, r.tl])  # 'Polygon'
annot.setBorder(width=0.3, dashes=[2])
annot.setColors(stroke=blue, fill=gold)
annot.setLineEnds(fitz.PDF_ANNOT_LE_DIAMOND, fitz.PDF_ANNOT_LE_CIRCLE)
annot.update()
print_descr(annot)

r += displ
annot = page.addLineAnnot(r.tr, r.bl)  # 'Line'
annot.setBorder(width=0.3, dashes=[2])
annot.setColors(stroke=blue, fill=gold)
annot.setLineEnds(fitz.PDF_ANNOT_LE_DIAMOND, fitz.PDF_ANNOT_LE_CIRCLE)
annot.update()
print_descr(annot)

r += displ
annot = page.addRectAnnot(r)  # 'Square'
annot.setBorder(width=1, dashes=[1, 2])
annot.setColors(stroke=blue, fill=gold)
annot.update(opacity=0.5)
print_descr(annot)

r += displ
annot = page.addCircleAnnot(r)  # 'Circle'
annot.setBorder(width=0.3, dashes=[2])
annot.setColors(stroke=blue, fill=gold)
annot.update()
print_descr(annot)

r += displ
annot = page.addFileAnnot(
    r.tl, b"just anything for testing", "testdata.txt"  # 'FileAttachment'
)
print_descr(annot)  # annot.rect

r += displ
annot = page.addStampAnnot(r, stamp=10)  # 'Stamp'
annot.setColors(stroke=green)
annot.update()
print_descr(annot)

r += displ + (0, 0, 50, 10)
rc = page.insertTextbox(
    r,
    "This content will be removed upon applying the redaction.",
    color=blue,
    align=fitz.TEXT_ALIGN_CENTER,
)
annot = page.addRedactAnnot(r)
print_descr(annot)

outfile = os.path.abspath(__file__).replace(".py", "-%i.pdf" % page.rotation)
doc.save(outfile, deflate=True)
