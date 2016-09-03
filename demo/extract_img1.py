#! python
'''
This demo extracts all images of a PDF as PNG files that are referenced
by pages.
Runtime is determined by number of pages and volume of stored images.
Usage:
extract_img1.py input.pdf
'''
from __future__ import print_function
import fitz
import sys, time

if len(sys.argv) != 2:
    print('Usage: %s <input file>' % sys.argv[0])
    exit(0)
    
t0 = time.clock()
doc = fitz.open(sys.argv[1])
imgcount = 0
lenXREF = doc._getXrefLength()

# display some file info
print("file: %s, pages: %s, objects: %s" % (sys.argv[1], len(doc), lenXREF-1))

for i in range(len(doc)):
    imglist = doc.getPageImageList(i)
    for img in imglist:
        xref = img[0]                  # xref number
        pix = fitz.Pixmap(doc, xref)   # make pixmap from image
        imgcount += 1
        if pix.n < 5:                  # can be saved as PNG
            pix.writePNG("p%s-%s.png" % (i, xref))
        else:                          # must convert CMYK first
            pix0 = fitz.Pixmap(fitz.csRGB, pix)
            pix0.writePNG("p%s-%s.png" % (i, xref))
            pix0 = None                # free Pixmap resources
        pix = None                     # free Pixmap resources

t1 = time.clock()
print("run time", round(t1-t0, 2))
print("extracted images", imgcount)