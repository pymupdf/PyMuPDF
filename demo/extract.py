#!/usr/bin/env python
import fitz
import sys

if len(sys.argv) != 3:
    print('Usage: %s <input file> <page num>' % sys.argv[0])
    exit(0)

#get the page
d = fitz.Document(sys.argv[1])
pg = d.loadPage(int(sys.argv[2]))

#setup the display list
dl = fitz.DisplayList()
dv = fitz.Device(dl)
pg.run(dv, fitz.Identity)

#setup the text page
ts = fitz.TextSheet()
tp = fitz.TextPage()
rect = pg.bound()
dl.run(fitz.Device(ts, tp), fitz.Identity, rect)

#get the text content
text = tp.extractText()
print('%s' % text)

#TODO: extract images from a page
