#!/usr/bin/python
# -*- coding: utf-8 -*-
import fitz
from PIL import Image
import sys
'''
Create a Pixmap from any PIL / Pillow supported filetype
Changes in v1.10.0
-------------------
- omit alpha to save image memor<
'''
if len(sys.argv) == 2:
    pic_fn = sys.argv[1]
else:
    pic_fn = None

if pic_fn:
    print('Reading %s' % pic_fn)
    pic_f = open(pic_fn, "rb")
    img = Image.open(pic_f).convert("RGB")
    samples = img.tobytes()
    pix = fitz.Pixmap(fitz.csRGB, img.size[0], img.size[1], samples, 0)
    outputFileName = pic_fn + '-from-PIL.png'
    print('Writing %s' % outputFileName)
    pix.writePNG(outputFileName)
    pic_f.close()
