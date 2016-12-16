#!/usr/bin/python
# -*- coding: utf-8 -*-
import fitz
import sys
from PIL import Image

'''
Given any pixmap, use Pil / Pillow to save it in a different format
Example: take a RGBA pixmap and output as JPEG
The unwieldy parameters afte "raw" onwards suppress warnings from PIL ...
'''

assert len(sys.argv) == 2, 'Usage: %s <input file>' % sys.argv[0]
print('Reading %s' % sys.argv[1])
pix = fitz.Pixmap(sys.argv[1])
img = Image.frombuffer("RGBA", [pix.width, pix.height], pix.samples,
                       "raw", "RGBA", 0, 1)
outputFileName = '%s-from-fitz.jpg' % sys.argv[1]
print('Writing %s' % outputFileName)
img.save(outputFileName, "jpeg")
