#! /usr/bin/python
# -*- coding: utf-8 -*-
import numpy as np
import fitz

#==============================================================================
# Create any height*width*4 RGBA pixel area using numpy and then use fitz
# to save it as a PNG image.
# This is usually more than 10 times faster than pure python solutions
# like pypng and more than 2 times faster than PIL.
#==============================================================================
height = 108            # choose whatever
width  = 192            # you want here 
image  = np.ndarray((height, width, 4), dtype=np.uint8)

for i in range(height):
    for j in range(width):
        # choose color components as you like them
        image[i, j] = np.array([i%256, j%256, 200, 255], dtype=np.uint8)

# create a string from the array and output the picture
samples = image.tostring()
pix=fitz.Pixmap(fitz.Colorspace(fitz.CS_RGB), width, height, samples)
pix.writePNG("test.png")
