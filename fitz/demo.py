#!/usr/bin/env python2
#This is a demo which prints number of pages

import fitz
import sys

fitz.initContext()
doc = fitz.Document(sys.argv[1])
print '%d pages' % doc.pageCount

page = doc.loadPage(0)
rect = page.bound()
irect = rect.round()
print '(%d, %d), (%d, %d)' % (irect.x0, irect.y0, irect.x1, irect.y1)

cs = fitz.Colorspace(fitz.CS_RGB)
pm = fitz.Pixmap(cs, irect)
pm.clearWith(0xff)

dev = fitz.Device(pm)
