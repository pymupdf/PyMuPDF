#!/usr/bin/env python
import fitz
import sys

assert len(sys.argv) == 3, 'Usage: %s <input file> <page num>' % sys.argv[0]

#get the page
d = fitz.Document(sys.argv[1])
pg = d.loadPage(int(sys.argv[2]))

#setup the display list
dl = fitz.DisplayList(pg.rect)
dv = fitz.Device(dl)
pg.run(dv, fitz.Identity)

#setup the text page
ts = fitz.TextSheet()
tp = fitz.TextPage(pg.rect)
dl.run(fitz.Device(ts, tp), fitz.Identity, pg.rect)

#get the text content
text = tp.extractText()
print('%s' % text)
