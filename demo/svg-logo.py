"""
Copy an input PDF to output with an SVG-based logo
---------------------------------------------------
License: GNU GPL V3
(c) 2018-2019 Jorj X. McKie

Usage
------
python svg-logo.py input.pdf logo.svg(z)

Result
-------
A file "logo-input.pdf" with the logo on each page.

Dependencies
-------------
PyMuPDF 1.12.2 or later
svglib, reportlab
"""
from __future__ import print_function
import sys
import fitz
from svglib.svglib import svg2rlg

doc_fn = sys.argv[1]  # name of PDF file
svg_fn = sys.argv[2]  # name of SVG image file

drawing = svg2rlg(svg_fn)  # open the SVG logo file
pdfbytes = drawing.asString("pdf")  # turn logo to PDF image bytes
src = fitz.open("pdf", pdfbytes)  # open as PDF from memory
rect = src[0].rect  # rectangle of the image
factor = 25 / rect.height  # logo height is fixed to 25
rect *= factor  # adjust width accordingly
doc = fitz.open(doc_fn)  # open PDF to be modified
for page in doc:  # scan through PDF pages
    xref = page.showPDFpage(
        rect, src, 0, overlay=True  # put page src[0] in rect
    )  # put in forground
doc.save("logo-" + doc_fn, garbage=4)

