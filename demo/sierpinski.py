# -*- coding: utf-8 -*-
"""
@created: 2016-01-15 08:40:00

@author: Jorj X. McKie

Create a Sierpinks carpet using PyMuPDF.

Dependencies:
PyMuPDF

License:
 GNU GPL 3.x
 
On a machine with 4.0 GHz, run time should be well below 0.5 sec for d = 729.
"""

import fitz, time
def punch(pm, x0, y0, x1, y1):         # pixmap and square coordinates 
    if (x1-x0) < 3:                    # no handling if quare is < 3*3
        return False
    step = (x1 - x0) / 3
    # define short names for small square coordinates
    x00 = x0
    x01 = x00 + step
    x02 = x01 + step
    x03 = x02 + step
    y00 = y0
    y01 = y00 + step
    y02 = y01 + step
    y03 = y02 + step
    # we clear the middle square and invoke us again for the other 8
    punch(pm, x00, y00, x01, y01)      # top left
    punch(pm, x01, y00, x02, y01)      # top middle
    punch(pm, x02, y00, x03, y01)      # top right
    punch(pm, x00, y01, x01, y02)      # middle left
    pm.clearWith(0, fitz.IRect(x01, y01, x02, y02))   # clear center square
    punch(pm, x02, y01, x03, y02)      # middle right
    punch(pm, x00, y02, x01, y02)      # bottom left
    punch(pm, x01, y02, x02, y03)      # bottom middle
    punch(pm, x02, y02, x03, y03)      # bottom right
    return True

#==============================================================================
# main program
#==============================================================================
d = 729                                # 729 = 3**6, stick to powers of 3 here
# create a quadratic pixmap with origin (0,0), where width = height = d should
# be a power of 3
t0 = time.clock()
pm = fitz.Pixmap(fitz.Colorspace(fitz.CS_RGB), fitz.IRect(0, 0, d, d))
# fill image area with "white" and then tint and gamma it
pm.clearWith(255)
pm.tintWith(0, 50, 255)            # tint it with some sort of blue

# now punch holes into it, down to 1 pixel granularity
punch(pm, 0, 0, d, d)
t1 = time.clock()
pm.writePNG("sierpinski.png")
t2 = time.clock()
print t1-t0, "sec to create fitz img"
print t2-t1, "sec to save fitz img"