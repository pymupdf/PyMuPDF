#! python
'''
This demo extracts all images of a PDF to separate files that are referenced
by pages. Runtime is hence determined by number of pages and volume of stored
images. Typical data: less than 1.5 seconds for the 1310-page Adobe manual
(180 images, 4 MB), 3.5 seconds for 100 pages of an illustration-oriented
science magazine (Spektrum, 790 images, 18 MB).
If an image has no /SMask entry, it is stored using the raw image buffer -
i.e. not necessarily as a PNG file.
If the image has an /SMask entry, it is processed using PyMuPDF pixmaps.
Image files are stored in the PDF's directory and named "p<i>-<j>.ext",
where i is the page number, j the xref number and ext the appropriate extension.

Usage:
------
extract_img3.py input.pdf

'''
from __future__ import print_function
import fitz
import sys, time

def recoverpix(doc, item):
    x = item[0]  # xref of PDF image
    s = item[1]  # xref of its /SMask
    if s == 0:                    # no /SMask: use raw image
        return doc.extractImage(x)

    pix1 = fitz.Pixmap(doc, x)
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
doc = fitz.open(sys.argv[1])           # the PDF
assert doc.isPDF, "This script can only process PDF documents."
imgcount = 0                           # counts extracted images
xreflist = []                          # records images already extracted
lenXREF = doc._getXrefLength()         # only used for information

# display some file info
print("file: %s, pages: %s, objects: %s" % (sys.argv[1], len(doc), lenXREF-1))

for i in range(len(doc)):              # scan through all pages
    imglist = doc.getPageImageList(i)  # list of images used by the page
    for img in imglist:
        if img[0] in xreflist:         # image already processed
            continue 
        xreflist.append(img[0])        # take note of the xref
        imgcount += 1
        pix = recoverpix(doc, img[:2]) # make pixmap from image
        imgfile = "p%i-%i" % (i, img[0])
        if type(pix) is not fitz.Pixmap:    # a raw image buffer
            fout = open(imgfile + "." + pix["ext"], "wb")
            fout.write(pix["image"])
            fout.close()
            continue

        if pix.n - pix.alpha < 4:      # can be saved as PNG
            pass
        else:                          # must convert CMYK first
            pix0 = fitz.Pixmap(fitz.csRGB, pix)
            pix = pix0
        pix.writePNG(imgfile + ".png")
        pix = None                     # free Pixmap resources

t1 = time.clock()
print("run time", round(t1-t0, 2))
print("extracted images", imgcount)