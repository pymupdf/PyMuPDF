#!/usr/bin/env python2
#This is a demo which saves a certain page as PNG file
#usage: demo.py <filename> <page> <zoom> <degree> <output filename>

import fitz
import sys

#init the context, this needs to be carried out in the beginning
fitz.initContext()

#create a document object from the file path
doc = fitz.Document(sys.argv[1])

#pages start from 0
pn = int(sys.argv[2])-1
if pn >= doc.pageCount:
	print '%s has %d pages only' % (sys.argv[1], doc.pageCount)
	exit(1)

#we create a transformation matrix here
zoom = int(sys.argv[3])
rotate = int(sys.argv[4])
trans = fitz.Matrix.scale(zoom/100.0, zoom/100.0).preRotate(rotate)

#get a page
page = doc.loadPage(pn)

#get the page size
#then apply the transformation
#and finally round it to irect whose coordinates are integers
irect = page.bound().transform(trans).round()
print 'coordinates: (%d, %d), (%d, %d)' % (irect.x0, irect.y0, irect.x1, irect.y1)

#create a pixmap with RGB as colorspace and bounded by irect
pm = fitz.Pixmap(fitz.Colorspace(fitz.CS_RGB), irect)
#clear it with 0xff white
pm.clearWith(0xff)

#fitz.Device(pm) is a device for drawing
#we run that drawing device on the page
#with transformation applied
page.run(fitz.Device(pm), trans)

#the drawing device save the result int the pixmap
#and we save the pixmap as a PNG file
pm.writePNG(sys.argv[5], 0)

#DO NOT run fitz.dropContext() here
#since it will deallocate the fitz context
#which is still needed destructor of other resources