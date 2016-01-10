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
    '''pm: pixmap with width = height (a square) and start at (0, 0). Should be a power of 3.
    lvl: level of square subdivision
    function: subdivide pm's square into 3**(lvl-1) * 3**(lvl-1) smaller ones and for each small square, punch out its center.'''
    if lvl < 1:                        # punch level must be > 0
        return False
    d = pm.width                       # pixel length of pm's square side
    step = d / (3**(lvl - 1))          # width of small squares lvl=2 -> step=d/3
    if step < 3:                       # cannot handle sub-pixel sizes
        return False
    iter_cnt = 3**(lvl-1)              # how many small squares
    step3 = step/3                     # top-left coord of punch hole
    step4 = 2*step/3                   # bottom-right coord of punch hole
    for i in list(range(iter_cnt)):
        x = i * step
        for j in list(range(iter_cnt)):
            y = j * step
            pm.clearWith(0, fitz.IRect(x + step3,
                                       y + step3,
                                       x + step4,
                                       y + step4))
    return True

#==============================================================================
# main program
#==============================================================================
d = 729                      # 729 = 3**6, stick with powers of 3 here
# create a quadratic pixmap with origin (0,0), where width = height should be
# a power of 3
pm = fitz.Pixmap(fitz.Colorspace(fitz.CS_RGB), fitz.IRect(0, 0, d, d))
# fill image area with "white" and then tint and gamma it
pm.clearWith(255)
pm.tintWith(0, 50, 255)            # tint it with some sort of blue
pm.gammaWith(0.2)                  # lighten it up

# now punch holes into it, down to 1 pixel granularity
i = 1
while punch(pm, i):
    i += 1

pm.writePNG("sierpinski.png")
