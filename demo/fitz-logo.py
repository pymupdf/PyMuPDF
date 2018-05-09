'''
Copy an input PDF to output with a logo in topleft corner
----------------------------------------------------------
License: GNU GPL V3
(c) 2018 Jorj X. McKie

Usage
------
python fitz-logo.py input.pdf logo.file

Result
-------
A file "fitzlogo-input.pdf" with the logo on each page. If the output page
rectangle is taken as page.rect, then a watermark effect will occur.

Notes
-----
(1) Any PyMuPDF-supported document can be used as the logo / watermark.
    This includes PDF, XPS, EPUB, CBZ, FB2 and any image type.

(2) SVG-based logos are not always shown correctly. Use a different
    PDF converter like svglib if that occurs.

(3) Logos / watermarks are transparent for non-image document types.
    If you need transparency for images, you must convert it to a PDF
    "manually" like so:

    pix = fitz.Pixmap(logo_fn)
    src = fitz.open()
    src_page = src.newPage(-1, width = pix.width, height = pix.height)
    src_page.insertImage(src_page.rect, pixmap = pix)

Dependencies
-------------
PyMuPDF 1.13.3 or later
'''
from __future__ import print_function
import fitz
import sys
doc_fn = sys.argv[1]                        # name of PDF file
logo_fn = sys.argv[2]                       # name of logo file

src = fitz.open(logo_fn)                    # open logo document
if not src.isPDF:                           # convert if not PDF
    pdfbytes = src.convertToPDF             # convert to PDF
    src.close()
    src = fitz.open("pdf", pdfbytes)        # open logo as a PDF
rect = src[0].rect                          # rectangle of the logo
factor = 25 / rect.height                   # logo height is fixed to 25
rect *= factor                              # adjust width accordingly
doc = fitz.open(doc_fn)                     # open the PDF to be modified
xref = 0
for page in doc:                            # scan through PDF pages
    xref = page.showPDFpage(rect, src, 0,
                            reuse_xref = xref,
                            overlay = False)

doc.save("fitzlogo-" + doc_fn, garbage = 4)
