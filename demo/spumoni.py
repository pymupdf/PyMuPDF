import fitz
from fitz.utils import getColor
"""
@created: 2017-07-03 14:00:00

@author: (c) Jorj X. McKie

Demo for creating the "SPUMONI" drawing contained in ReportLab's Users Guide
on pp. 25 - 26

Dependencies:
PyMuPDF

License:
 GNU GPL 3+

The only purpose of this ugly picture is to show, that creating it with PyMuPDF
is definitely at least as easy and straightforward ...

"""

green, pink, brown = getColor("green"), getColor("pink"), getColor("brown")
clist = (pink, green, brown)       # make a list of these colors
top  = 72                          # some convenience constants
left = right = top / 2
nrects = 14
fname = "Helvetica-Bold"           # fontname
doc = fitz.open()                  # empty new document
cw = doc._getCharWidths(fname)     # get glyph widths of the font
text = "SPUMONI"                   # the ominous text
textl = sum([cw[ord(c)] for c in text])     # get total glyph width of text
width, height = fitz.PaperSize("letter")
page = doc.newPage(-1, width = width, height = height)     # insert new page
rwidth = (width - 2*left) / nrects # rect width, leaves borders of 36 px
fsize = (width - 2*left) / textl   # optimum fontsize
rheight = 400                      # rect height
for i in range(nrects-2):          # draw colored rectangles (last 2 stay white)
    r = fitz.Rect(left + i*rwidth, top, left + (i+1)*rwidth, top + rheight)
    page.drawRect(r, color = clist[i % 3], fill = clist[i % 3])
# draw outer black border
page.drawRect(fitz.Rect(left, top, width - right, top + rheight))
# insert the big text in white letters, a little above rectangle's middle line
page.insertText(fitz.Point(left, top + (rheight + fsize*0.7)/2), text,
                fontsize=fsize, fontname = fname, color = getColor("white"))

# now the wafer cone with its 3 defining points
points = (fitz.Point(width/2, top + rheight),        # center of bottom line
          fitz.Point(width*0.4, top + rheight*0.5),  # upper corner left
          fitz.Point(width*0.6, top + rheight*0.5))  # upper corner right
page.drawPolyline(points, fill = brown, closePath = True)  # draw and fill it

# now the three ice scoops, their centers are above each other
page.drawCircle(fitz.Point(width*0.5, top + rheight*0.5), width*0.1, fill = pink)
page.drawCircle(fitz.Point(width*0.5, top + rheight*0.35), width*0.1, fill = green)
page.drawCircle(fitz.Point(width*0.5, top + rheight*0.2), width*0.1, fill = brown)
# done!
doc.save("spumoni.pdf")
