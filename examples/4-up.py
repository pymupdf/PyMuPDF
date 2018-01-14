'''
Copy an input PDF to output combining every 4 pages
---------------------------------------------------
License: GNU GPL V3
(c) 2018 Jorj X. McKie

Usage
------
python 4up.py input.pdf

Result
-------
A file "4up-input.pdf" with 1 output page for every 4 input pages.

Notes
-----
(1) Output file is chosen to have A4 portrait pages. Input pages are scaled
    maintaining side proportions. Both can be changed, e.g. based on input
    page size. However, note that not all pages need to have the same size, etc.

(2) Easily adapt the example to combine just 2 pages (like for a booklet) or
    make the output page dimension dependent on input, or whatever.

(3) This should run very fast: needed less than 25 sec on a Python 3.6 64bit,
    Windows 10, AMD 4.0 GHz for the 1'310 pages of the Adobe manual.
    Without save-options "garbage" and "deflate" this goes below 4 seconds, but
    results in a bigger file.
    
Dependencies
-------------
PyMuPDF 1.12.1 or later
'''
from __future__ import print_function
import fitz, sys
infile = sys.argv[1]
src = fitz.open(infile)
doc = fitz.open()                      # empty output PDF

width, height = fitz.PaperSize("a4")   # A4 portrait output page format
r = fitz.Rect(0, 0, width, height)

# define the 4 rectangles per page
r1 = r * 0.5                           # top left rect
r2 = r1 + (r1.width, 0, r1.width, 0)   # top right
r3 = r1 + (0, r1.height, 0, r1.height) # bottom left
r4 = fitz.Rect(r1.br, r.br)            # bottom right

# put them in a list
r_tab = [r1, r2, r3, r4]

# now copy input pages to output
for spage in src:
    if spage.number % 4 == 0:           # create new output page
        page = doc.newPage(-1,
                      width = width,
                      height = height)
    # insert input page into the correct rectangle
    page.showPDFpage(r_tab[spage.number % 4],    # select output rect
                     src,               # input document
                     spage.number)      # input page number

# by all means, save new file using garbage collection and compression
doc.save("4up-" + infile, garbage = 4, deflate = True)
