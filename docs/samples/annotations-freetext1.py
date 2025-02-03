# -*- coding: utf-8 -*-
import pymupdf

# some colors
blue = (0, 0, 1)
green = (0, 1, 0)
red = (1, 0, 0)
gold = (1, 1, 0)

# a new PDF with 1 page
doc = pymupdf.open()
page = doc.new_page()

# 3 rectangles, same size, above each other
r1 = pymupdf.Rect(100, 100, 200, 150)
r2 = r1 + (0, 75, 0, 75)
r3 = r2 + (0, 75, 0, 75)

# the text, Latin alphabet
t = "¡Un pequeño texto para practicar!"

# add 3 annots, modify the last one somewhat
a1 = page.add_freetext_annot(r1, t, text_color=red, border_color=red)
a2 = page.add_freetext_annot(r2, t, fontname="Ti", text_color=blue, border_color=blue)
a3 = page.add_freetext_annot(r3, t, fontname="Co", text_color=blue, rotate=90)
a3.set_border(width=0)
a3.update(fontsize=8, fill_color=gold)

# save the PDF
doc.save("a-freetext.pdf")
