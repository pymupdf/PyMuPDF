#!/usr/bin/python
# -*- coding: utf-8 -*-
import fitz
from PIL import Image
import sys
from __future__ import print_function
'''
Create a Pixmap from any PIL / Pillow supported filetype
'''
if len(sys.argv) == 2:
    pic_fn = sys.argv[1]
else:
    pic_fn = None

if pic_fn:
    print(pic_fn)
    pic_f = open(pic_fn, "rb")
    img = Image.open(pic_f).convert("RGBA")
    samples = img.tobytes()
    pix = fitz.Pixmap(fitz.csRGB, img.size[0], img.size[1], samples, 1)
    pix.writePNG(pic_fn + ".png")
    pic_f.close()
