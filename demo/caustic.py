from __future__ import print_function
import math
import fitz
"""
@created: 2017-06-18 10:00:00

@author: (c) Jorj X. McKie

Demo for creating simple graphics with method 'Page.drawLine()', 'drawCircle()'
and friends.

Dependencies:
PyMuPDF, math

License:
 GNU GPL 3+

Sketching a caustic. That's the figure the early morning sun paints onto
your desperately needed cup of coffee, from an angle on your left side ...

We paint each sun ray after is has been reflected by the cup.

"""
def pvon(a):
    """Starting point of a reflected sun ray, given an angle a."""
    return(math.cos(a), math.sin(a))

def pbis(a):
    """End point of a reflected sun ray, given an angle a."""
    return(math.cos(3*a - math.pi), (math.sin(3*a - math.pi)))

doc = fitz.open()                                # new empty PDF 
doc.insertPage(-1, width = 800, height = 800)    # new square page in it
page = doc[0]                                    # get the page just created

center = fitz.Point(page.rect.width / 2,         # center of circle on page
                    page.rect.height / 2)

radius = page.rect.width / 2 - 20                # leave a border of 20 pixels

coffee = (156.0/255, 79.0/255, 0)                # color: latte macchiato?
page.drawCircle(center, radius, color = coffee,  # fill the cup with coffee
                fill = coffee)

count = 400                                      # how many sun rays we paint
yellow = (1, 1, 0)                               # yellow = color of sun rays
interval = math.pi / count                       # angle fraction
for i in range(1, count):
    a = -math.pi / 2 + i * interval              # go from -90 to +90 degrees
    von = fitz.Point(pvon(a)) * radius + center  # start point adjusted
    bis = fitz.Point(pbis(a)) * radius + center  # end point adjusted
    page.drawLine(von, bis, width = 0.3,         # a ray is a fine yellow line
                  color = yellow)

page.drawCircle(center, radius, color = (0, 0, 1)) # cup border is blue
doc.save("caustic.pdf", garbage = 4, deflate = True)
