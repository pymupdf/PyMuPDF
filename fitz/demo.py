#!/usr/bin/env python
#This is a demo which saves a certain page as PNG file
#It also contains misc feature like displaying document outline
#usage: demo.py <filename> <page> <zoom> <degree> <output filename>

import fitz
import sys

if len(sys.argv) != 6:
    print('Usage: %s <filename> <page> <zoom> <degree> <output filename>' % sys.argv[0])
    exit(0)

#create a document object from the file path
doc = fitz.Document(sys.argv[1])

#here we print out the outline of the document(if any)
#first, we define a function for traversal
def olTraversal(root):
    nodes = [root]
    while nodes:
        node = nodes.pop()
        print('- %s ==> %d' % (node.title, node.dest.page))
        next = node.next
        if next:
            nodes.append(next)
        else:
            print('<')
        down = node.down
        if down:
            print('>')
            nodes.append(down)
#and now let's do this
ol=doc.loadOutline()
if ol:
    print('Outline of the document')
    olTraversal(ol)
else:
    print('No outline available')

#get the page number, which should start from 0
pn = int(sys.argv[2])-1
if pn >= doc.pageCount or pn < 0:
    print('%s has %d pages only' % (sys.argv[1], doc.pageCount))
    exit(1)

#we create a transformation matrix here
zoom = int(sys.argv[3])
rotate = int(sys.argv[4])
trans = fitz.Matrix(zoom/100.0, zoom/100.0).preRotate(rotate)

#get the page
page = doc.loadPage(pn)

#get the page size
#then apply the transformation
#and finally round it to irect whose coordinates are integers
irect = page.bound().transform(trans).round()
print('coordinates: (%d, %d), (%d, %d)' % (irect.x0, irect.y0, irect.x1, irect.y1))

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

