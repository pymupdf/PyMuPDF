#!/usr/bin/python
# -*- coding: utf-8 -*-
import fitz
import sys
from PIL import Image

'''
Given any pixmap, use Pil / Pillow to save it in a different format
Example: take a RGB(A) pixmap and output as JPEG
The unwieldy parameters after "raw" onwards suppress warnings from PIL ...

Changes
--------
- [v1.10.0] adjust image format depending on presence of alpha in image
- [v1.13.0] convert to non-alpha pixmap for JPEG output
'''

assert len(sys.argv) == 2, 'Usage: %s <input file>' % sys.argv[0]

pix = fitz.Pixmap(sys.argv[1])    # read image file
rgb = "RGB"                       # set PIL parameter
if pix.alpha:                     # JPEG cannot have alpha!
    pix0 = fitz.Pixmap(pix, 0)    # drop alpha channel
    pix = pix0                    # rename pixmap

img = Image.frombuffer(rgb, [pix.width, pix.height], pix.samples,
                       "raw", rgb, 0, 1)

outputFileName = '%s-from-fitz.jpg' % sys.argv[1]
print('Writing %s' % outputFileName)
img.save(outputFileName)
