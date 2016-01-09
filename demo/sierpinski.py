# -*- coding: utf-8 -*-
"""
@created: 2015-10-23 13:40:00

@author: Jorj X. McKie

A PyMuPDF demo program: Create a Sierpinski carpet

Remark for our optimization friends:

Yes, I know, that
(1) a recursive implementation would have been more adequate, consequently,
(2) I am blackening some areas that are already black.

I was just too lazy to invest more brainware ... :-)
"""
import fitz

def punch(pm, lvl):
    # pm: pixmap with width = height (a square) and start at (0, 0)
    # lvl: level of square subdivision
    # function: subdivide big square in 3**lvl * 3**lvl smaller ones and
    # make the middle one black (punch it out)
    assert pm.width == pm.height
    assert pm.x == pm.y == 0
    d = pm.width
    step = d / (3**(lvl - 1))
    for i in list(range(3**lvl)):
        x = i * step
        for j in list(range(3**lvl)):
            y = j * step
            pm.clearIRectWith(0, fitz.IRect(x + step / 3,
                                            y + step / 3,
                                            x + 2 * step / 3,
                                            y + 2 * step / 3))
    return

#==============================================================================
# main program
#==============================================================================
d = 729                      # 729 = 3**6
# create a quadratic pixmap with origin (0,0) and width / height should be
# a power of 3
pm = fitz.Pixmap(fitz.Colorspace(fitz.CS_RGB), fitz.IRect(0, 0, d, d))
# fill image area with "white"
pm.clearWith(255)
# now punch black holes into it with increasing refinement levels
punch(pm, 1)
punch(pm, 2)
punch(pm, 3)
punch(pm, 4)
punch(pm, 5)
punch(pm, 6)  # max level for image dimension 729 * 729 (resolution = 1 pixel)
pm.writePNG("sierpinski.png")