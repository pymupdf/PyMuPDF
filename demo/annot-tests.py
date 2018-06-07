# -*- coding: utf-8 -*-
import fitz
print(fitz.__doc__)
"""
Demo script to show how annotations can be added to PDF pages.
It contains the following 10 annotation types:
Text ("sticky note"), FreeText, text markers (underline, strike-out, highlight),
Circle, Square, Line, PolyLine, Polygon.
"""
text = "text in line\ntext in line\ntext in line"
red = (1,0,0)
yellow = (1,1,0)
colors = {"stroke": red, "fill": yellow}
displ = fitz.Rect(0, 50, 0, 50)
pos = fitz.Point(50, 100)
t1 = u"têxt éxplöits Lätiñ chars,\nEuro: €, mu: µ, superscripts: ²³!"

def print_descr(rect, annot):
    """Print a short description to the right of an annotation."""
    page = annot.parent
    page.insertText(rect.br + (10, -3), "'%s' annotation" % annot.type[1], color = red)

doc = fitz.open()
page = doc.newPage()
annot = page.addFreetextAnnot(pos, t1)
print_descr(annot.rect, annot)

r = annot.rect + displ
annot = page.addTextAnnot(r.tl, t1)
print_descr(annot.rect, annot)

pos = annot.rect.tl + displ.tl * 2
page.insertText(pos, text, fontsize=11)
rl = page.searchFor("text in line")
r0 = rl[0]
r1 = rl[1]
r2 = rl[2]
annot = page.addHighlightAnnot(r0)
print_descr(r0, annot)
annot = page.addStrikeoutAnnot(r1)
print_descr(r1, annot)
annot = page.addUnderlineAnnot(r2)
print_descr(r2, annot)

r = r2 + displ
annot = page.addPolylineAnnot([r.tr, r.br, r.bl])
annot.setLineEnds(fitz.ANNOT_LE_Circle, fitz.ANNOT_LE_Diamond)
annot.setColors(colors)
print_descr(annot.rect, annot)

r+= displ
annot = page.addPolygonAnnot([r.tr, r.br, r.bl])
annot.setColors(colors)
print_descr(annot.rect, annot)

r+= displ
annot = page.addLineAnnot(r.tr, r.bl)
annot.setLineEnds(fitz.ANNOT_LE_Circle, fitz.ANNOT_LE_Diamond)
annot.setColors(colors)
print_descr(annot.rect, annot)

r+= displ
annot = page.addRectAnnot(r)
annot.setColors(colors)
print_descr(annot.rect, annot)

r+= displ
annot = page.addCircleAnnot(r)
annot.setColors(colors)
print_descr(annot.rect, annot)

doc.save("annot-tests.pdf", clean=True,expand=True)
