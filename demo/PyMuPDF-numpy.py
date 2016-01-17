#!/usr/bin/python
# -*- coding: utf-8 -*-
import numpy as np
import fitz

#==============================================================================
# create a width*height PNG using fitz and numpy
#==============================================================================
height = 108
width = 192
bild=np.empty((height, width, 4), dtype=np.uint8)

for i in range(height):
    for j in range(width):
        bild[i][j] = [i%256, j%256, 200, 255]   # color distribution as u like

samples = bild.tostring()
pix=fitz.Pixmap(fitz.Colorspace(fitz.CS_RGB), width, height, samples)
pix.writePNG("test.png")
