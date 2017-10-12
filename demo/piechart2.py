from __future__ import print_function
import fitz
import sys

#==============================================================================
# Pie Chart program - semi circle version
#==============================================================================
from fitz.utils import getColor        # for getting RGB colors by name
doc = fitz.open()                      # new empty PDF
doc.insertPage()                       # creates an ISO-A4 page
page = doc[-1]                         # this is the page
img = page.newShape()
# title of the page
title = "Sitzverteilung nach der Bundestagswahl 2013"
# pie chart center and point of 1st data pie
center = fitz.Point(200, 250)
point  = fitz.Point(100, 250)          # will cycle through table data
# this is the radius
radius = abs(point - center)

blue = getColor("blue")                # we need some colors
white = getColor("white")

lineheight = 20                        # legend line height
ts_v  = 150                            # vertical start of legend block
ts_h  = center.x + radius + 50         # horizontal coord of legend block

# these are the data to visualize:
# number of seats of political parties in German parliament since 2013
table  = (       # seats, party color & name 
          (64, "violetred", "Die Linke"),
          (193, "red", "SPD"),
          (63, "green", "Die Grünen"),
          (253, "black", "CDU"),
          (56, "dodgerblue", "CSU"),
          (1, "gray", "fraktionslos"),
         )

seats = float(sum([c[0] for c in table]))   # total seats
stitle = "Bundestagssitze insgesamt: %i" % (seats,)

img.insertText(fitz.Point(72, 72),title, fontsize = 14, color = blue)
img.insertText(fitz.Point(ts_h - 30, ts_v - 30), stitle, 
                fontsize = 13, color = blue)

img.drawLine(fitz.Point(72, 80), fitz.Point(550, 80))
img.finish(color = blue)

# draw the table data
for i, c in enumerate(table):
    beta = -c[0] / seats * 180          # express seats as angle in semi circle
    color = getColor(c[1])             # avoid multiple color lookups
    # the method delivers point of other end of the constructed arc
    # we will use it as input for next round
    point = img.drawSector(center, point, beta, fullSector = True)
    img.finish(color = white, fill = color, closePath = False)
    
    text = "%s, %i %s" % (c[2], c[0], "Sitze" if c[0] > 1 else "Sitz")
    pos  = fitz.Point(ts_h, ts_v + i*lineheight)
    img.insertText(pos, text, color = blue)
    tl = fitz.Point(pos.x - 30, ts_v - 10 + i*lineheight)
    br = fitz.Point(pos.x - 10, ts_v + i*lineheight)
    rect = fitz.Rect(tl, br)                # legend color bar
    img.drawRect(rect)
    img.finish(fill = color, color = color)

# overlay center of circle with white
img.drawCircle(center, radius - 70)
img.finish(color = white, fill = white)
img.commit()
doc.save("piechart2.pdf")

















