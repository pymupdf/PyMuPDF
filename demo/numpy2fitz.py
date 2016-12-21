#! /usr/bin/python
# -*- coding: utf-8 -*-
import numpy as np
import fitz

'''
==============================================================================
Create any height*width*3 RGB pixel area using numpy and then use fitz to
save it as a PNG image.
This is 10+ times faster than saving with pure python solutions like
pypng and 2+ times faster than saving with PIL.
==============================================================================
Changes in v1.20.0
-------------------
- do not use alpha channel to save 25% image memory
'''
height = 108            # choose whatever
width = 192            # you want here

image = np.ndarray((height, width, 3), dtype=np.uint8)

for i in range(height):
    for j in range(width):
        # colorize the 3 components as you like it
        image[i, j] = np.array([i % 256, j % 256, 200], dtype=np.uint8)

# create string / bytes object from the array and output the picture
samples = image.tostring()
pix = fitz.Pixmap(fitz.csRGB, width, height, samples)
pix.writePNG("test.png")
