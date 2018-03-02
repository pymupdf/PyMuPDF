'''
Copy an input PDF to output with an SVG-based logo
---------------------------------------------------
License: GNU GPL V3
(c) 2018 Jorj X. McKie

Usage
------
python svg-logo.py input.pdf logo.svg(z)

Result
-------
A file "logo-input.pdf" with the logo on each page.

Notes
-----
(1) Output file is chosen to have A4 portrait pages. Input pages are scaled
    maintaining side proportions. Both can be changed, e.g. based on input
    page size. However, note that not all pages need to have the same size, etc.

(2) Easily adapt the example to combine just 2 pages (like for a booklet) or
    make the output page dimension dependent on input, or whatever.
    
Dependencies
-------------
PyMuPDF 1.12.2 or later
svglib, reportlab
'''
from __future__ import print_function
import fitz
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF
import sys
doc_fn = sys.argv[1]                        # name of PDF file
svg_fn = sys.argv[2]                        # name of SVG image file

drawing = svg2rlg(svg_fn)                   # open the SVG
pdfbytes = renderPDF.drawToString(drawing)  # turn SVG to PDF image
src = fitz.open("pdf", pdfbytes)            # open SVG as a PDF
rect = src[0].rect                          # rectangle of the image
factor = 25 / rect.height                   # logo height will be fixed 25
rect *= factor                              # adjust width accordingly
doc = fitz.open(doc_fn)                     # open PDF to be modified
xref = -1
for page in doc:                            # scan through PDF pages
    xref = page.showPDFpage(rect, src, 0,
                            reuse_xref = xref,
                            overlay = False)
  
doc.save("logo-" + doc_fn)
