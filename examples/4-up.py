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
A file 4up-input.pdf with 1 output page for every 4 input pages.

Notes
-----
(1) Output file is chosen to have A4 portrait pages. Input pages are scaled
    maintaining side proportions. Both can be changed, e.g. based on input
    page size. However, note that not all pages need to have the same size, etc.

(2) Easily adapt the example to combine just 2 pages (like for a booklet)
    or any other number.

(3) This should run very fast: needed less than 25 sec on a Python 3.6 64bit,
    Windows 10, AMD 4.0 GHz for the 1'310 pages of the Adobe manual.
    Without save-options "garbage" and "deflate" this goes below 4 seconds.
'''
from __future__ import print_function
import fitz, time, sys
doc = fitz.open()
infile = sys.argv[1]
src = fitz.open(infile)

r = fitz.Rect(0, 0, 595, 842)          # A4 portrait output page format

# define the 4 rectangles per page
r1 = fitz.Rect(0, 0, r.width/2, r.height/2)
r2 = r1 + (r1.width, 0, r1.width, 0)
r3 = r1 + (0, r1.height, 0, r1.height)
r4 = fitz.Rect(r1.br, r.br)

# put them in an array
r_tab = (r1, r2, r3, r4)

t0 = time.clock()

# copy input pages to output
for spage in src:
    if spage.number % 4 == 0:           # create new output page
        page = doc.newPage(-1, width = r.width, height = r.height)
    page.showPDFpage(r_tab[spage.number % 4],    # select output rect
                     src,               # input document
                     spage.number,      # input page number
                     keep_proportions = True,    # keep side proportions
                     overlay = True)    # put to foreground in output

t1 = time.clock()

# by all means, save new file using garbage collection and compression
doc.save("4up-" + infile, garbage = 4, deflate = True)

# log output
t2 = time.clock()
print("processed %i pages of file '%s'" % (len(src), src.name))
print("showPDFpage time: %g" % (t1-t0))
print("save time: %g" % (t2-t1))