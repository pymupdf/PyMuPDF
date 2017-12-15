#! /usr/bin/python
"""
Created on Sun Jul 30 08:21:13 2017

@author: (c) 2017, Jorj X. McKie
License: GNU GPL V3

PyMuPDF demo program to print the the database of stored RGB colors as a PDF
----------------------------------------------------------------------------
The colors are sorted down by the color tuple. Each color is drawn in a
rectangle together with its name (in back and in white).

The colors are sorted depending on color tuple. Each color is drawn in a
rectangle together with its name (in back and in white to ensure readability).
A PDF page has dimensions 800 x 600 pixels.
"""
from __future__ import print_function
import fitz, sys, os
from fitz.utils import getColor, getColorInfoList
print(sys.version)
print(fitz.__doc__)
print("Running:", __file__)

def sortkey(x):
    """Return '001002003' for (colorname, 1, 2, 3)"""
    k = str(x[1]).zfill(3) + str(x[2]).zfill(3) + str(x[3]).zfill(3)
    return k

# create color list sorted down RGB values
mylist = sorted(getColorInfoList(), reverse = True, key=lambda x: sortkey(x))

w = 800            # page width
h = 600            # page height
rw = 80            # width of color rect
rh = 60            # height of color rect

num_colors = len(mylist)     # number of color triples
black = getColor("black")    # text color
white = getColor("white")    # text color
fsize = 8                    # fontsize
lheight = fsize *1.2         # line height
idx = 0                      # index in color database
doc = fitz.open()            # empty PDF
while idx < num_colors:
    page=doc.newPage(-1, width = w, height = h)  # new empty page
    for i in range(10):                          # row index
        if idx >= num_colors:
            break
        for j in range(10):                      # column index
            rect = fitz.Rect(rw*j, rh*i, rw*j + rw, rh*i + rh)  # color rect
            cname = mylist[idx][0].lower()       # color name
            col = mylist[idx][1:]                # color tuple -> to floats
            col = (col[0] / 255., col[1] / 255., col[2] / 255.)
            page.drawRect(rect, color = col, fill = col)   # draw color rect
            pnt1 = rect.top_left + (0, rh*0.3)   # pos of color name in white
            pnt2 = pnt1 + (0, lheight)           # pos of color name in black
            page.insertText(pnt1, cname, fontsize = fsize, color = white)
            page.insertText(pnt2, cname, fontsize = fsize, color = black)
            idx += 1
            if idx >= num_colors:
                break

m = {"author": "Jorj X. McKie", "producer": "PyMuPDF", "creator": "colordb.py",
     "creationDate": fitz.getPDFnow(), "modDate": fitz.getPDFnow(),
   "title": "PyMuPDF Color Database", "subject": "Sorted down by RGB values"}

doc.setMetadata(m)
path = os.path.dirname(os.path.abspath(__file__))
ofn = os.path.join(path, "colordbRGB.pdf")
print("Writing:", ofn)
doc.save(ofn, garbage = 4, deflate = True, clean=True)
