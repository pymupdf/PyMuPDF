"""
Created on 2017-09-06

@author: (c) 2017, Jorj X. McKie

License: GNU GPL V3

PyMuPDF Demo Program
---------------------
Draw an arbitrary regular polygon, but use wavy / squiggly lines instead of
straight ones.

It also demonstrates how drawSector can be used to calculate points without
actually drawing them.

"""

import fitz
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

# we only use this to calculate the polygon edges - will delete draw commands
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
img.commit()
doc.save("wavy-polygon.pdf", garbage = 4)