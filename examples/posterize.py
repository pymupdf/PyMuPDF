'''
Create a PDF copy with split-up pages (posterize)
---------------------------------------------------
License: GNU GPL V3
(c) 2018 Jorj X. McKie

Usage
------
python posterize.py input.pdf

Result
-------
A file "poster-input.pdf" with 4 output pages for every input page.

Notes
-----
(1) Output file is chosen to have page dimensions of 1/4 of input.

(2) Easily adapt the example to make n pages per input, or decide per each
    input page or whatever.

Dependencies
------------
PyMuPDF 1.12.2 or later
'''
from __future__ import print_function
import fitz, sys
infile = sys.argv[1]                        # input file name
src = fitz.open(infile)
doc = fitz.open()                           # empty output PDF

for spage in src:                           # for each page in input
    xref = 0                                # force initial page copy to output
    r = spage.rect                          # input page rectangle
    d = fitz.Rect(spage.CropBoxPosition,    # CropBox displacement if not
                  spage.CropBoxPosition)    # starting at (0, 0)
    #--------------------------------------------------------------------------                  
    # example: cut input page into 2 x 2 parts
    #--------------------------------------------------------------------------
    r1 = r * 0.5                            # top left rect
    r2 = r1 + (r1.width, 0, r1.width, 0)    # top right rect
    r3 = r1 + (0, r1.height, 0, r1.height)  # bottom left rect
    r4 = fitz.Rect(r1.br, r.br)             # bottom right rect
    rect_list = [r1, r2, r3, r4]            # put them in a list
    
    for rx in rect_list:                    # run thru rect list
        rx += d                             # add the CropBox displacement
        page = doc.newPage(-1,              # new output page with rx dimensions
                           width = rx.width,
                           height = rx.height)
        xref = page.showPDFpage(page.rect,  # fill all new page with the image
                                src,        # input document
                                spage.number, # input page number
                                subrect = rx, # which part to use of input page
                                reuse_xref = xref) # copy input page once only
                                
# that's it, save output file
doc.save("poster-" + src.name,
         garbage = 4,                       # eliminate duplicate objects
         deflate = True)                    # compress stuff where possible
