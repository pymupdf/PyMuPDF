from __future__ import print_function
import math
import fitz
from fitz.utils import getColor
import gzip
"""
@created: 2017-06-18 10:00:00

@author: (c) Jorj X. McKie

Demo for creating simple graphics with method 'drawLine()', 'drawCircle()'
and friends.

Dependencies:
PyMuPDF v1.12.0+, math

License:
 GNU GPL 3+

Sketching a caustic. That's the shape the early morning sun paints onto
your desperately needed cup of coffee, when shining from a low angle
through the window on your left side ...

We draw each sun ray after it has been reflected by the cup.

The resulting picture is save in three image formats: PDF, PNG and SVG / SVGZ

"""
def pvon(a):
    """Starting point of a reflected sun ray, given an angle a."""
    return(math.cos(a), math.sin(a))

def pbis(a):
    """End point of a reflected sun ray, given an angle a."""
    return(math.cos(3*a - math.pi), (math.sin(3*a - math.pi)))

fileprfx = "catacaustic"                         # filename prefix
coffee = getColor("coffee")                      # color: latte macchiato?
yellow = getColor("yellow")                      # color of sun rays
blue   = getColor("blue")                        # color cup border
doc = fitz.open()                                # new empty PDF 
page = doc.newPage(-1, width = 800, height = 800)# create square sized page
center = fitz.Point(page.rect.width / 2,         # center of circle on page
                    page.rect.height / 2)

radius = page.rect.width / 2 - 20                # leave a border of 20 pixels

img = page.newShape()
img.drawCircle(center, radius)
img.finish(color = coffee, fill = coffee)        # fill coffee into the cup

count = 200                                      # how many sun rays we draw
interval = math.pi / count                       # angle fraction
for i in range(1, count):
    a = -math.pi / 2 + i * interval              # go from -90 to +90 degrees
    von = fitz.Point(pvon(a)) * radius + center  # start point adjusted
    bis = fitz.Point(pbis(a)) * radius + center  # end point adjusted
    img.drawLine(von, bis)
    
img.finish(width = 1, color = yellow, closePath = False) # a ray is a fine yellow line

img.drawCircle(center, radius)
img.finish(color = blue)                         # cup border is blue
page.setCropBox(img.rect)                        # adjust visible page
img.commit()
doc.save(fileprfx + ".pdf")

# create a PNG image
doc.getPagePixmap(0).writePNG(fileprfx + ".png")

# save as SVG / SVGZ images
svg = page.getSVGimage()
svgz = gzip.compress(svg.encode("utf-8"))
fout = open(fileprfx + ".svg", "w")
fout.write(svg)
fout.close()
fout = open(fileprfx + ".svgz", "wb")
fout.write(svgz)
fout.close()