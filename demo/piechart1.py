from __future__ import print_function
import fitz
from fitz.utils import getColor 
import sys

#==============================================================================
# Pie Chart program
#==============================================================================
doc = fitz.open()                 # new empty PDF
page = doc.newPage()              # without parms, this is an ISO-A4 format page
img = page.newShape()
# title line
title = "Sitzverteilung nach der Bundestagswahl 2013"
# pie chart center and point of 1st data pie
center = fitz.Point(200, 250)
point  = fitz.Point(200, 150)          # this will cycle through table data
# this is the radius
radius = abs(point - center)

blue = getColor("blue")                # we need some colors
white = getColor("white")

lineheight = 20                        # legend line height
ts_v  = 200                            # vertical start of legend block
ts_h  = center.x + radius + 50         # horizontal coord of legend block

# these are the data to visualize:
# number of seats of political parties in German parliament since 2013
table  = (
          (253, "black", "CDU"),       # seats, party color & party name 
          (56, "dodgerblue", "CSU"),
          (193, "red", "SPD"),
          (64, "violetred", "Die Linke"),
          (63, "green", "Die Grünen"),
          (1, "gray", "fraktionslos"),
         )

seats = float(sum([c[0] for c in table]))   # total seats
stitle = "Bundestagssitze insgesamt: %i" % (seats,)

img.insertText(fitz.Point(72, 72),title, fontsize = 14, color = blue)
img.insertText(fitz.Point(ts_h - 30, ts_v - 30), stitle, 
                fontsize = 13, color = blue)
img.drawLine(fitz.Point(72, 80), fitz.Point(550, 80))
img.finish(color = blue)


for i, c in enumerate(table):
    beta = -c[0] / seats * 360         # express no. of seats as angle
    color = getColor(c[1])             # avoid multiple color lookups
    
    # the method delivers point of other end of the constructed arc
    # we will use it as input for next round
    point = img.drawSector(center, point, beta, fullSector = True)
    img.finish(color = white, fill = color, closePath=False)
    
    # legend text (takes care of German plural of "Sitz", too)
    text = "%s, %i %s" % (c[2], c[0], "Sitze" if c[0] > 1 else "Sitz")
    pos  = fitz.Point(ts_h, ts_v + i*lineheight)
    img.insertText(pos, text, color = blue)     # legend text
    tl = fitz.Point(pos.x - 30, ts_v - 10 + i*lineheight)
    br = fitz.Point(pos.x - 10, ts_v + i*lineheight)
    rect = fitz.Rect(tl, br)                     # legend color bar
    img.drawRect(rect)
    img.finish(fill = color, color = color)

img.commit()
doc.save("piechart1.pdf")

















