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
highlight), Circle, Square, Line, PolyLine, Polygon, FileAttachment and Stamp.

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
text = "text in line\ntext in line\ntext in line\ntext in line"
red    = (1, 0, 0)
blue   = (0, 0, 1)
gold   = (1, 1, 0)
colors = {"stroke": blue, "fill": gold}
border = {"width": 0.3, "dashes": [2]}
displ = fitz.Rect(0, 50, 0, 50)
r = fitz.Rect(50, 100, 220, 135)
t1 = u"têxt üsès Lätiñ charß,\nEUR: €, mu: µ, super scripts: ²³!"

def print_descr(rect, annot):
    """Print a short description to the right of an annot rect."""
    annot.parent.insertText(rect.br + (10, 0),
                    "'%s' annotation" % annot.type[1], color = red)

doc = fitz.open()
page = doc.newPage()
annot = page.addFreetextAnnot(r, t1, rotate = 90)
annot.setBorder(border)
annot.update(fontsize = 10, border_color=red, fill_color=gold, text_color=blue)

print_descr(annot.rect, annot)
r = annot.rect + displ
print("added 'FreeText'")

annot = page.addTextAnnot(r.tl, t1)
print_descr(annot.rect, annot)
print("added 'Sticky Note'")

pos = annot.rect.tl + displ.tl

# first insert 4 rotated text lines
page.insertText(pos, text, fontsize=11, morph = (pos, fitz.Matrix(-15)))
# now search text to get the quads
rl = page.searchFor("text in line", quads = True)
r0 = rl[0]
r1 = rl[1]
r2 = rl[2]
r3 = rl[3]
annot = page.addHighlightAnnot(r0)
# need to convert quad to rect for descriptive text ...
print_descr(r0.rect, annot)
print("added 'HighLight'")

annot = page.addStrikeoutAnnot(r1)
print_descr(r1.rect, annot)
print("added 'StrikeOut'")

annot = page.addUnderlineAnnot(r2)
print_descr(r2.rect, annot)
print("added 'Underline'")

annot = page.addSquigglyAnnot(r3)
print_descr(r3.rect, annot)
print("added 'Squiggly'")

r = r3.rect + displ
annot = page.addPolylineAnnot([r.bl, r.tr, r.br, r.tl])
annot.setBorder(border)
annot.setColors(colors)
annot.setLineEnds(fitz.ANNOT_LE_ClosedArrow, fitz.ANNOT_LE_RClosedArrow)
annot.update()
print_descr(annot.rect, annot)
print("added 'PolyLine'")

r+= displ
annot = page.addPolygonAnnot([r.bl, r.tr, r.br, r.tl])
annot.setBorder(border)
annot.setColors(colors)
annot.setLineEnds(fitz.ANNOT_LE_Diamond, fitz.ANNOT_LE_Circle)
annot.update()
print_descr(annot.rect, annot)
print("added 'Polygon'")

r+= displ
annot = page.addLineAnnot(r.tr, r.bl)
annot.setBorder(border)
annot.setColors(colors)
annot.setLineEnds(fitz.ANNOT_LE_Diamond, fitz.ANNOT_LE_Circle)
annot.update()
print_descr(annot.rect, annot)
print("added 'Line'")

r+= displ
annot = page.addRectAnnot(r)
annot.setBorder(border)
annot.setColors(colors)
annot.update()
print_descr(annot.rect, annot)
print("added 'Square'")

r+= displ
annot = page.addCircleAnnot(r)
annot.setBorder(border)
annot.setColors(colors)
annot.update()
print_descr(annot.rect, annot)
print("added 'Circle'")

r+= displ
annot = page.addFileAnnot(r.tl, b"just anything for testing", "testdata.txt")
print_descr(annot.rect, annot)
print("added 'FileAttachment'")

r+= displ
annot = page.addStampAnnot(r, stamp = 10)
annot.setColors(colors)
annot.setOpacity(0.5)
annot.update()
print_descr(annot.rect, annot)
print("added 'Stamp'")

doc.save("new-annots.pdf", expand=255)
