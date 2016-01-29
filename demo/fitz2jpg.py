#!/usr/bin/python
# -*- coding: utf-8 -*-
import fitz
from PIL import Image
import sys
'''
demonstrates how to output a JPEG image from PyMuPDF using PIL / Pillow
'''
if len(sys.argv) == 2:
    pic_fn = sys.argv[1]
else:
    pic_fn = None

if pic_fn:
    print pic_fn
    pic = open(pic_fn, "rb").read()

    pix = fitz.Pixmap(pic, len(pic))
    img = Image.frombytes("RGBA",[pix.width, pix.height], str(pix.samples))
    img.save(pic_fn + ".jpg", "jpeg")