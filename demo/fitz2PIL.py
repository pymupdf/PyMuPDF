#!/usr/bin/python
# -*- coding: utf-8 -*-
import fitz
from PIL import Image

'''
Given any pixmap, use Pil / Pillow to save it in a different format
Example: JPEG
The unwieldy parameters afte "raw" onwards suppress warnings from PIL ...
'''
pix = fitz.Pixmap(...)
img = Image.frombuffer("RGBA", [pix.width, pix.height], pix.samples,
                       "raw", "RGBA", 0, 1)
img.save("filename.jpg", "jpeg")
