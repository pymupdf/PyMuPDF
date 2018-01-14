from __future__ import print_function
import math
import fitz
from fitz.utils import getColor
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

coffee = getColor("coffee")                      # color: latte macchiato?
yellow = getColor("yellow")                      # color of sun rays
blue   = getColor("blue")                        # color cup border
doc = fitz.open()                                # new empty PDF 
page = doc.newPage(-1, width = 800, height = 800)# create page
center = fitz.Point(page.rect.width / 2,         # center of circle on page
                    page.rect.height / 2)

radius = page.rect.width / 2 - 20                # leave a border of 20 pixels

img = page.newShape()
img.drawCircle(center, radius)
img.finish(color = coffee, fill = coffee)        # fill coffee into the cup

count = 200                                      # how many sun rays we paint
interval = math.pi / count                       # angle fraction
for i in range(1, count):
    a = -math.pi / 2 + i * interval              # go from -90 to +90 degrees
    von = fitz.Point(pvon(a)) * radius + center  # start point adjusted
    bis = fitz.Point(pbis(a)) * radius + center  # end point adjusted
    img.drawLine(von, bis)
    
img.finish(width = 1, color = yellow, closePath = False) # a ray is a fine yellow line

img.drawCircle(center, radius)
img.finish(color = blue)                         # cup border is blue
img.commit()
doc.save("catacaustic.pdf", garbage = 4)

# create a PNG image
pix = doc.getPagePixmap(0)
pix.writePNG("catacaustic.png")

# create an SVG image
t = page.getSVGimage()
fout = open("catacaustic.svg", "w")
fout.write(t)
fout.close()