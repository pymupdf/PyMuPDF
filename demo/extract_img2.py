#! python
'''
This demo will extract all images of a PDF as PNG files, whether they are
referenced by pages or not.
It scans through all objects and selects /Type/XObject with /Subtype/Image.
Runtime is therefore determined by XREF length and volume of stored images.
Usage:
extract_img2.py <input file>
'''
from __future__ import print_function
import fitz
import sys, time, re

checkXO = r"/Type(?= */XObject)"   # finds "/Type/XObject"   
checkIM = r"/Subtype(?= */Image)"  # finds "/Subtype/Image"

if len(sys.argv) != 2:
    print('Usage: %s <input file>' % sys.argv[0])
    exit(0)
    
t0 = time.clock()
doc = fitz.open(sys.argv[1])
imgcount = 0
lenXREF = doc._getXrefLength()
print("file: %s, pages: %s, objects: %s" % (sys.argv[1], len(doc), lenXREF-1))
for i in range(1, lenXREF):
    text = doc._getObjectString(i)
    isXObject = re.search(checkXO, text)
    isImage   = re.search(checkIM, text)
    if not isXObject or not isImage:   # not an image
        continue
    imgcount += 1
    pix = fitz.Pixmap(doc, i)     # make pixmap from image
    if pix.n < 5:                 # can be saved as PNG
        pix.writePNG("img-%s.png" % (i,))
    else:                         # must convert CMYK first
        pix0 = fitz.Pixmap(fitz.csRGB, pix)
        pix0.writePNG("img-%s.png" % (i,))
        pix0 = None               # free Pixmap resources
    pix = None                    # free Pixmap resources
        
t1 = time.clock()
print("run time", round(t1-t0, 2))
print("extracted images", imgcount)