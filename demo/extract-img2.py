from __future__ import print_function
import fitz
import os, sys, time, re
"""
This demo extracts all images of a PDF as PNG files, whether they are
referenced by pages or not.
It scans through all objects and selects /Type/XObject with /Subtype/Image.
So runtime is determined by number of objects and image volume.

Technically, images with a specified /SMask are correctly recovered and
should appear as originally stored.

Usage:
-------
python extract_img.py input.pdf img-prefix

The focus of this script is to be as fault-tolerant as possible:
-----------------------------------------------------------------
* It can cope with invalid PDF page trees, invalid PDF objects and more
* It ignores images with very small dimensions (< 100 pixels side length)
* It ignores very small image file sizes (< 2 KB)
* It ignores well-compressible images - assuming these are insignificant,
  like unicolor images

Adjust / omit these limits as required.

Found images are stored in a directory one level below the input PDF, called
"images" (created if not existing). Adjust this as appropriate.

"""
assert len(sys.argv) == 3, "usage: extract_img.py input.pdf img-prefix"
dimlimit = 100      # each image side must be greater than this
relsize  = 0.05     # PNG:pixmap size ratio must be larger than this (5%)
abssize  = 2048     # absolute PNG size limit: ignore if smaller
imgdir   = "images" # found images are stored here
if not os.path.exists(imgdir):
    os.mkdir(imgdir)

def recoverpix(doc, item):
    """Return pixmap for item, which is a list of 2 xref numbers. Second xref
    is that of an smask if > 0.
    Return None for any error.
    """
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
        return pix1               # return w/ failed transparency
        
    # check that we are safe
    if not (pix1.irect == pix2.irect and \
            pix1.alpha == pix2.alpha == 0 and \
            pix2.n == 1):
        print("unexpected /SMask situation: pix1", pix1, "pix2", pix2)
        return pix1
    pix = fitz.Pixmap(pix1)       # copy of pix1, alpha channel added
    pix.setAlpha(pix2.samples)    # treat pix2.samples as alpha values
    pix1 = pix2 = None            # free temp pixmaps
    return pix

checkXO = r"/Type(?= */XObject)"       # finds "/Type/XObject"   
checkIM = r"/Subtype(?= */Image)"      # finds "/Subtype/Image"

t0 = time.clock()

fname = sys.argv[1] # file name
fpref = sys.argv[2] # image file prefix
doc = fitz.open(sys.argv[1])
imgcount = 0
lenXREF = doc._getXrefLength()         # object count - do not use entry 0!

# display some file info
print("")
print(__file__, "PDF: %s, pages: %s, objects: %s" % (sys.argv[1], len(doc), lenXREF-1))

smasks = [] # stores xrefs of /SMask objects
#------------------------------------------------------------------------------
# loop through PDF images
#------------------------------------------------------------------------------
for i in range(1, lenXREF):            # scan through all objects
    try:
        text = doc._getXrefString(i) # PDF object definition string
    except:
        print("xref %i " % i + doc._getGCTXerrmsg())
        continue                       # skip the error
        
    isXObject = re.search(checkXO, text)    # tests for XObject
    isImage   = re.search(checkIM, text)    # tests for Image
    is_an_image = isXObject and isImage     # both must be True for an image
    if not is_an_image:
        continue

    # check if just an /SMask
    txt = text.split("/SMask")
    if len(txt) > 1:                        # this is an smask
        y = txt[1].split()
        mxref = int(y[0])                   # its xref
        if mxref not in smasks:             # store xref
            smasks.append(mxref)
    else:
        mxref = 0
    
    pix = recoverpix(doc, (i, mxref))  # get the pixmap
        
    if not pix:                        # skip if error
        continue
    if not pix.colorspace:             # an error or just a mask!
        continue
    if min(pix.w, pix.h) <= dimlimit:  # rectangle edges too small
        continue

    if pix.colorspace.n >= 4:          # CMYK: must be converted first
        pix0 = fitz.Pixmap(fitz.csRGB, pix)
        pix = pix0
    
    imgdata = pix.getPNGData()         # content of to-be-created image file
    
    if (len(imgdata) / len(pix.samples)) < relsize: # image is probably empty!
        continue
    
    if len(imgdata) <= abssize:        # image too small to be relevant
        continue

    # now we have an image worthwhile dealing with
    imgcount += 1
    imgn1 = fpref + "-%i.png" % i
    imgname = os.path.join(imgdir, imgn1)
    ofile = open(imgname, "wb")
    ofile.write(imgdata)
    ofile.close()

# now delete any /SMask files not filtered out before
removed = 0
for xref in smasks:
    imgn1 = fpref + "-%i.png" % xref
    imgname = os.path.join(imgdir, imgn1)
    if os.path.exists(imgname):
        os.remove(imgname)
        removed += 1
        
t1 = time.clock()

print("run time %g" % (t1-t0))
print("extracted images:", (imgcount - removed))
print("skipped smasks:", len(smasks))
print("removed smasks:", removed)