# -*- coding: utf-8 -*-
from __future__ import print_function
import sys
print("Python", sys.version, "on", sys.platform, "\n")
import fitz
print(fitz.__doc__, "\n")
"""
-------------------------------------------------------------------------------
Demo script to show how annotations can be added to a PDF using PyMuPDF.

It contains the following annotation types:
Text ("sticky note"), FreeText, text markers (underline, strike-out,
highlight), Circle, Square, Line, PolyLine, Polygon and FileAttachment.

Notes
-----
1. PyMuPDF (in contrast to MuPDF) adds appearance objects to all supported
   annotations. This ensures they get properly rendered in PyMuPDF pixmaps
   and by viewers like "mupdf" and "SumatraPDF".
2. PyMuPDF does not (yet, v1.13.13) support line ending styles. This is
   relevant for 'Line' and 'PolyLine' annotations.
3. PyMuPDF supports FileAttachment annotations.
4. 'FreeText' annotations currently only support ASCII text. Other char
   codes are displayed as "?". CallOut arrows are currently not supprted.

Dependencies
------------
PyMuPDF v1.13.13
-------------------------------------------------------------------------------
"""
text = "text in line\ntext in line\ntext in line"
red    = (1, 0, 0)
blue   = (0, 0, 1)
yellow = (1, 1, 0)
colors = {"stroke": red, "fill": yellow}
border = {"width": 1}
displ = fitz.Rect(0, 50, 0, 50)
pos = fitz.Point(50, 100)
t1 = u"têxt üsès Lätiñ charß,\nEuro: €, mu: µ, superscripts: ²³!"

def print_descr(rect, annot):
    """Print a short description to the right of an annotation."""
    page = annot.parent
    page.insertText(rect.br + (10, -3),
                    "'%s' annotation" % annot.type[1], color = red)

doc = fitz.open()
page = doc.newPage()
annot = page.addFreetextAnnot(pos, t1, color = blue)
print_descr(annot.rect, annot)
r = annot.rect + displ
print("added 'FreeText'")

annot = page.addTextAnnot(r.tl, t1)
print_descr(annot.rect, annot)
pos = annot.rect.tl + displ.tl * 2
print("added 'Sticky Note'")

page.insertText(pos, text, fontsize=11)
rl = page.searchFor("text in line")
r0 = rl[0]
r1 = rl[1]
r2 = rl[2]
annot = page.addHighlightAnnot(r0)
print_descr(r0, annot)
print("added 'HighLight'")

annot = page.addStrikeoutAnnot(r1)
print_descr(r1, annot)
print("added 'StrikeOut'")

annot = page.addUnderlineAnnot(r2)
print_descr(r2, annot)
print("added 'Underline'")

r = r2 + displ
annot = page.addPolylineAnnot([r.bl, r.tr, r.br, r.tl])
annot.setLineEnds(fitz.ANNOT_LE_Circle, fitz.ANNOT_LE_Diamond)
annot.setColors(colors)
annot.updateImage()
print_descr(annot.rect, annot)
print("added 'PolyLine'")

r+= displ
annot = page.addPolygonAnnot([r.bl, r.tr, r.br, r.tl])
annot.setColors(colors)
annot.updateImage()
print_descr(annot.rect, annot)
print("added 'Polygon'")

r+= displ
annot = page.addLineAnnot(r.tr, r.bl)
annot.setLineEnds(fitz.ANNOT_LE_Circle, fitz.ANNOT_LE_Diamond)
annot.setColors(colors)
annot.updateImage()
print_descr(annot.rect, annot)
print("added 'Line'")

r+= displ
annot = page.addRectAnnot(r)
annot.setColors(colors)
annot.updateImage()
print_descr(annot.rect, annot)
print("added 'Square'")


r+= displ
annot = page.addCircleAnnot(r)
annot.setColors(colors)
annot.updateImage()
print_descr(annot.rect, annot)
print("added 'Circle'")

r+= displ
annot = page.addFileAnnot(r.tl, b"just anything for testing", "testdata.txt")
print_descr(annot.rect, annot)
print("added 'FileAttachment'")

doc.save("new-annots.pdf", clean=True)
doc.close()