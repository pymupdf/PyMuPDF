#!/usr/bin/python
# -*- coding: utf-8 -*-
import fitz

'''
Created on Fri Jan 08 17:00:00 2016

@author: Jorj X. McKie

===============================================================================
PyMuPDF demo program
--------------------
Demonstrates some of MuPDF's non-PDF graphic capabilities.

Read a PNG image and create a new one consisting of 3 * 4 tiles of it.
===============================================================================
'''
# read in picture image as a pixmap
pic = open("editra.png", "rb").read()
pix0 = fitz.Pixmap(pic, len(pic))

# calculate target pixmap dimensions and then create it
tar_width  = pix0.width * 3
tar_height = pix0.height * 4
tar_irect  = fitz.IRect(0, 0, tar_width, tar_height)
tar_pix    = fitz.Pixmap(fitz.Colorspace(fitz.CS_RGB), tar_irect)
tar_pix.clearWith(90)        # clear target with a lively gray :-)

# now fill target with 3 * 4 tiles of input picture
for i in list(range(4)):
    pix0.y = i * pix0.height                          # modify input's y coord
    for j in list(range(3)):
        pix0.x = j * pix0.width                       # modify input's x coord
        tar_pix.copyPixmap(pix0, pix0.getIRect())     # copy input to new loc
        # save intermediate image to show what is happening
        fn = "target-" + str(i) + str(j) + ".png"
        tar_pix.writePNG(fn)
