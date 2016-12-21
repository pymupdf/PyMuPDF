# -*- coding: utf-8 -*-
"""
@created: 2016-01-15 08:40:00

@author: Jorj X. McKie

Create Sierpinki's carpet using PyMuPDF.

Dependencies:
PyMuPDF

License:
 GNU GPL 3.x
 
On a machine with 4.0 GHz, run time should be well below 0.5 sec for d = 729 (= 3**6).
For each additional power of 3, runtime grows by a factor of 8, i.e. about 4 seconds for d = 3**7, etc. in our case.
"""
import fitz
import time


def punch(pm, x00, y00, x03, y03):
    step = x03 - x00
    if step < 3:                       # stop recursion if square < 3 x 3
        return
    step = step // 3
    # define short names for square corner coordinates
    x01 = x00 + step
    x02 = x01 + step
    y01 = y00 + step
    y02 = y01 + step
    # we clear the middle square and recurse for the other 8
    ir = fitz.IRect(x01, y01, x02, y02)  # rectangle of middle square
    punch(pm, x00, y00, x01, y01)      # top left
    punch(pm, x01, y00, x02, y01)      # top middle
    punch(pm, x02, y00, x03, y01)      # top right
    punch(pm, x00, y01, x01, y02)      # middle left
    pm.clearWith(255, ir)              # clear center to white
    punch(pm, x02, y01, x03, y02)      # middle right
    punch(pm, x00, y02, x01, y02)      # bottom left
    punch(pm, x01, y02, x02, y03)      # bottom middle
    punch(pm, x02, y02, x03, y03)      # bottom right
    return

#==============================================================================
# main program
#==============================================================================
d = 3 ** 6                               # 729
# create a quadratic pixmap with origin (0,0), where width = height = d should
# be a power of 3
t0 = time.clock()
ir = fitz.IRect(0, 0, d, d)
pm = fitz.Pixmap(fitz.csGRAY, ir)
# fill image area with "black" and then optionally tint and gamma it
pm.clearWith(0)
# pm.tintWith(10, 20, 100)            # tint it with some sort of blue
# pm.gammaWith(0.5)                   # lighten it up
# now punch holes into it, down to 1 pixel granularity
punch(pm, 0, 0, d, d)
t1 = time.clock()
pm.writePNG("sierpinski-fitz.png")
t2 = time.clock()
print("%f sec to create fitz img" % (t1 - t0))
print("%f sec to save fitz img" % (t2 - t1))
