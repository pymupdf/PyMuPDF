#! python
'''
This demo extracts all images of a PDF as PNG files that are referenced
by pages.
Runtime is determined by number of pages and volume of stored images.
Usage:
------
extract_img1.py input.pdf
Changes:
--------
Do not use pix.colorspace when checking for CMYK images, because it may be None
if the image is a stencil mask. Instead, we now check pix.n - pix.alpha < 4
to confirm that an image is not CMYK.
IAW: the repr() of a stencil mask pixmap looks like
"Pixmap(None, fitz.IRect(0, 0, width, height), 1)", and we have
width * height == len(pix.samples).
'''
from __future__ import print_function
import fitz
import sys, time

def recoverpix(doc, item):
    x = item[0]  # xref of PDF image
    s = item[1]  # xref of its /SMask
    pix1 = fitz.Pixmap(doc, x)
    if s == 0:                    # has no /SMask
        return pix1               # no special handling
    pix2 = fitz.Pixmap(doc, s)    # create pixmap of /SMask entry
    # check that we are safe
    if not (pix1.irect == pix2.irect and \
            pix1.alpha == pix2.alpha == 0 and \
            pix2.n == 1):
        print("pix1", pix1, "pix2", pix2)
        raise ValueError("unexpected situation")
    pix = fitz.Pixmap(pix1)       # copy of pix1, alpha channel added
    pix.setAlpha(pix2.samples)    # treat pix2.samples as alpha value
    pix1 = pix2 = None            # free temp pixmaps
    return pix


assert len(sys.argv) == 2, 'Usage: %s <input file>' % sys.argv[0]
    
t0 = time.clock()
doc = fitz.open(sys.argv[1])
imgcount = 0
lenXREF = doc._getXrefLength()

# display some file info
print("file: %s, pages: %s, objects: %s" % (sys.argv[1], len(doc), lenXREF-1))

for i in range(len(doc)):
    imglist = doc.getPageImageList(i)
    for img in imglist:
        pix = recoverpix(doc, img)     # make pixmap from image
        imgcount += 1
        if pix.n - pix.alpha < 4:      # can be saved as PNG
            pass
        else:                          # must convert CMYK first
            pix0 = fitz.Pixmap(fitz.csRGB, pix)
            pix = pix0
        pix.writePNG("p%i-%s.png" % (i, img[7]))
        pix = None                     # free Pixmap resources

t1 = time.clock()
print("run time", round(t1-t0, 2))
print("extracted images", imgcount)