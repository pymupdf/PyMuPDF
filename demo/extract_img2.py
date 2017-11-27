#! python
'''
This demo extracts all images of a PDF as PNG files, whether they are
referenced by pages or not.
It scans through all objects and selects /Type/XObject with /Subtype/Image.
So runtime is determined by number of objects and image volume.
Usage:
extract_img2.py input.pdf
'''
from __future__ import print_function
import fitz
import sys, time, re

def recoverpix(doc, item):
    x = item[0]  # xref of PDF image
    s = item[1]  # xref of its /SMask
    
    try:
        pix1 = fitz.Pixmap(doc, x)     # make pixmap from image
    except:
        print("xref %i " % x + doc._getGCTXerrmsg())
        return None                    # skip if error

    if s == 0:                    # has no /SMask
        return pix1               # no special handling
    
    try:
        pix2 = fitz.Pixmap(doc, s)    # create pixmap of /SMask entry
    except:
        print("cannot create mask %i for image xref %i" % (s,x))
        return pix1
        
    # check that we are safe
    if not (pix1.irect == pix2.irect and \
            pix1.alpha == pix2.alpha == 0 and \
            pix2.n == 1):
        print("unexpected /SMask situation: pix1", pix1, "pix2", pix2)
        return pix1
    pix = fitz.Pixmap(pix1)       # copy of pix1, alpha channel added
    pix.setAlpha(pix2.samples)    # treat pix2.samples as alpha value
    pix1 = pix2 = None            # free temp pixmaps
    return pix

checkXO = r"/Type(?= */XObject)"       # finds "/Type/XObject"   
checkIM = r"/Subtype(?= */Image)"      # finds "/Subtype/Image"

assert len(sys.argv) == 2, 'Usage: %s <input file>' % sys.argv[0]
    
t0 = time.clock()
doc = fitz.open(sys.argv[1])
imgcount = 0
lenXREF = doc._getXrefLength()         # number of objects - do not use entry 0!

# display some file info
print(__file__, "PDF: %s, pages: %s, objects: %s" % (sys.argv[1], len(doc), lenXREF-1))

for i in range(1, lenXREF):            # scan through all objects
    try:
        text = doc._getObjectString(i) # PDF object definition string
    except:
        print("xref %i " % i + doc._getGCTXerrmsg())
        continue                       # skip if error
        
    isXObject = re.search(checkXO, text)    # tests for XObject
    isImage   = re.search(checkIM, text)    # tests for Image
    if not isXObject or not isImage:   # not an image object if not both True
        continue
        
    txt = text.split("/SMask")
    if len(txt) > 1:
        y = txt[1].split()
        mxref = int(y[0])
    else:
        mxref = 0
    
    pix = recoverpix(doc, (i, mxref))
        
    if not pix:
        continue
    if not pix.colorspace:             # an error a just a mask!
        continue

    imgcount += 1
    if pix.colorspace.n < 4:           # can be saved as PNG
        pix.writePNG("img-%s.png" % (i,))
    else:                              # CMYK: must convert it
        pix0 = fitz.Pixmap(fitz.csRGB, pix)
        pix0.writePNG("img-%s.png" % (i,))
        pix0 = None                    # free Pixmap resources
    pix = None                         # free Pixmap resources
        
t1 = time.clock()
print("run time", round(t1-t0, 2))
print("extracted images", imgcount)