#!/usr/bin/python
# -*- coding: utf-8 -*-
import fitz
from PIL import Image
import sys
from __future__ import print_function
'''
Given any pixmap, use Pil / Pillow to save it in a different format
Example: JPEG
'''
pix = fitz.Pixmap(...)
img = Image.frombytes("RGBA",[pix.width, pix.height], str(pix.samples))
img.save("filename.jpg", "jpeg")
