"""
Created on 2017-09-06

@author: (c) 2017, Jorj X. McKie

License: GNU GPL V3

PyMuPDF Demo Program
---------------------
Draw an arbitrary regular polygon, but use wavy / squiggly lines instead of
straight ones.
Visible page size will be adjusted to the generated drawing.
Two output files are generated: a PDF and a SVG image file.

It also demonstrates how draw commands can be used to calculate points without
actually drawing them.

Dependencies
------------
PyMuPDF v1.12.2+

"""

import fitz
fname1 = "curly-polygon"
doc     = fitz.open()
page    = doc.newPage()
img     = page.newShape()
nedge   = 5                            # number of polygon edges
breadth = 2                            # wave amplitude
beta    = -1.0 * 360 / nedge           # our angle, drawn clockwise
center = fitz.Point(300,300)           # center of circle
p0     = fitz.Point(300,200)           # start here (1st edge = north)
p1     = +p0                           # save as last edge to add
points = [p0]                          # to store the polygon edges

# we only use this to calculate the polygon edges
# we will delete the resp. draw commands
for i in range(nedge - 1):
    p0 = img.drawSector(center, p0, beta)
    points.append(p0)

# erase previous draw commands in contents buffer
img.contents = ""

points.append(p1)                      # add starting point to edges list
# now draw the lines along stored edges
for i in range(nedge):
    img.drawSquiggle(points[i], points[i+1], breadth = breadth)

img.finish(color = (0,0,1), fill = (1,1,0), closePath = False)

# adjust visible page to dimensions of the drawing
page.setCropBox(img.rect)
img.commit()
doc.save(fname1 + ".pdf")
fout = open(fname1 + ".svg", "w")
fout.write(page.getSVGimage())
fout.close()
doc.close()
