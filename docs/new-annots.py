# -*- coding: utf-8 -*-
from __future__ import print_function
import sys

import fitz

print(fitz.__doc__)
if fitz.VersionBind.split(".") < ["1", "16", "0"]:
    sys.exit("PyMuPDF v1.16.0+ is needed.")
"""
-------------------------------------------------------------------------------
Demo script showing how annotations can be added to a PDF using PyMuPDF.

It contains the following annotation types:
Text ("sticky note"), FreeText, text markers (underline, strike-out,
highlight), Circle, Square, Line, PolyLine, Polygon, FileAttachment and Stamp.


Dependencies
------------
PyMuPDF v1.16.0
-------------------------------------------------------------------------------
"""
text = "text in line\ntext in line\ntext in line\ntext in line"
red = (1, 0, 0)
blue = (0, 0, 1)
gold = (1, 1, 0)
green = (0, 1, 0)

displ = fitz.Rect(0, 50, 0, 50)
r = fitz.Rect(72, 100, 220, 135)
t1 = u"têxt üsès Lätiñ charß,\nEUR: €, mu: µ, super scripts: ²³!"


def print_descr(rect, annot):
    """Print a short description to the right of an annot rect."""
    annot.parent.insertText(
        rect.br + (10, -5), "'%s' annotation" % annot.type[1], color=red
    )


doc = fitz.open()
page = doc.newPage()

annot = page.addCaretAnnot(r.tl)  # 'Caret'
print_descr(annot.rect, annot)

r = r + displ
annot = page.addFreetextAnnot(  # 'FreeText'
    r, t1, fontsize=10, rotate=90, text_color=blue, fill_color=gold
)
annot.setBorder(width=0.3, dashes=[2])
annot.update()

print_descr(annot.rect, annot)
r = annot.rect + displ

annot = page.addTextAnnot(r.tl, t1)
print_descr(annot.rect, annot)

#------------------------------------------------------------------------------
# prepare insertion of 4 text highlight annotations
#------------------------------------------------------------------------------
pos = annot.rect.tl + displ.tl
# 1. insert 4 rotated text lines
page.insertText(pos, text, fontsize=11, morph=(pos, fitz.Matrix(-15)))
# 2. search text to get the quads
rl = page.searchFor("text in line", quads=True)
r0 = rl[0]  # these are the 4 quads
r1 = rl[1]
r2 = rl[2]
r3 = rl[3]
annot = page.addHighlightAnnot(r0)
# need to convert quad to rect for descriptive text ...
print_descr(r0.rect, annot)

annot = page.addStrikeoutAnnot(r1)
print_descr(r1.rect, annot)

annot = page.addUnderlineAnnot(r2)
print_descr(r2.rect, annot)

annot = page.addSquigglyAnnot(r3)
print_descr(r3.rect, annot)
# end of text highlight annot code
#------------------------------------------------------------------------------

r = r3.rect + displ
annot = page.addPolylineAnnot([r.bl, r.tr, r.br, r.tl])  # 'Polyline'
annot.setBorder(width=0.3, dashes=[2])
annot.setColors(stroke=blue, fill=gold)
annot.setLineEnds(fitz.PDF_ANNOT_LE_CLOSED_ARROW,
                  fitz.PDF_ANNOT_LE_R_CLOSED_ARROW)
annot.update()
print_descr(annot.rect, annot)

r += displ
annot = page.addPolygonAnnot([r.bl, r.tr, r.br, r.tl])  # 'Polygon'
annot.setBorder(width=0.3, dashes=[2])
annot.setColors(stroke=blue, fill=gold)
annot.setLineEnds(fitz.PDF_ANNOT_LE_DIAMOND,
                  fitz.PDF_ANNOT_LE_CIRCLE)
annot.update()
print_descr(annot.rect, annot)

r += displ
annot = page.addLineAnnot(r.tr, r.bl)  # 'Line'
annot.setBorder(width=0.3, dashes=[2])
annot.setColors(stroke=blue, fill=gold)
annot.setLineEnds(fitz.PDF_ANNOT_LE_DIAMOND,
                  fitz.PDF_ANNOT_LE_CIRCLE)
annot.update()
print_descr(annot.rect, annot)

r += displ
annot = page.addRectAnnot(r)  # 'Square'
annot.setBorder(width=1, dashes=[1, 2])
annot.setColors(stroke=blue, fill=gold)
annot.setOpacity(0.5)
annot.update()
print_descr(annot.rect, annot)

r += displ
annot = page.addCircleAnnot(r)  # 'Circle'
annot.setBorder(width=0.3, dashes=[2])
annot.setColors(stroke=blue, fill=gold)
annot.update()
print_descr(annot.rect, annot)

r += displ
annot = page.addFileAnnot(r.tl,  # 'FileAttachment'
                          b"just anything for testing",
                          "testdata.txt")
print_descr(annot.rect, annot)

r += displ
annot = page.addStampAnnot(r, stamp=10)  # 'Stamp'
annot.setColors(stroke=green)
annot.update()
print_descr(annot.rect, annot)


doc.save("new-annots.pdf")
