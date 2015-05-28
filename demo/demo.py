#!/usr/bin/env python
#This is a demo which saves a certain page as PNG file
#It also contains misc feature like displaying document outline
#usage: demo.py <filename> <page> <zoom> <degree> <output filename> <needle>

import fitz
import sys

if len(sys.argv) != 7:
    print('Usage: %s <filename> <page> <zoom> <degree> <output filename> <needle>' % sys.argv[0])
    exit(0)

#create a document object from the file path
doc = fitz.Document(sys.argv[1])
#SWIG returns high level python proxy class and .this points to the underlying C object
if not doc.this:
    print('cannot open document')
    exit(1)

#the metadata is a python dict, whose keys are:
#format, encryption, title, author, subject, keywords, creator, producer, creationDate, modDate
#the value will be None if the info is N/A
for key in doc.metadata:
    if doc.metadata[key]:
        print('%s: %s' % (key, doc.metadata[key]))

#here we print out the outline of the document(if any)
#first, we define a function for traversal
def olTraversal(root):
    nodes = [root]
    while nodes:
        node = nodes.pop()
        print('[OUTLINE]- %s ==> %d' % (node.title, node.dest.page))
        next = node.next
        if next:
            nodes.append(next)
        else:
            print('[OUTLINE]<')
        down = node.down
        if down:
            print('[OUTLINE]>')
            nodes.append(down)
#and now let's do this
ol=doc.outline
if ol:
    print('Outline of the document')
    olTraversal(ol)
#we can also save outline into XML or TXT file
    ol.saveXML(sys.argv[1]+'.xml')
    ol.saveText(sys.argv[1]+'.txt')
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

#we can also get all the links in the current page
ln = page.loadLinks()
#links are saved as a single linked list
#and we need to first check the kind of the link to determine what info we can get
while ln:
    if ln.dest.kind == fitz.LINK_URI:
        print('[LINK]URI: %s' % ln.dest.uri)
    elif ln.dest.kind == fitz.LINK_GOTO:
        print('[LINK]jump to page %d' % ln.dest.page)
    else:
        pass
    ln = ln.next


#here we introduce the display list, which provides caching-mechanism to reduce parsing of a page
#first, we need to create a display list
#hand it over to a list device
#and then populate the display list by running the page through that device, with transformation applied
dl = fitz.DisplayList()
dv = fitz.Device(dl)
page.run(dv, trans)

#get the page size, and then apply the transformation
rect = page.bound().transform(trans)

#create a pixmap with RGB as colorspace and bounded by irect
pm = fitz.Pixmap(fitz.Colorspace(fitz.CS_RGB), rect.round())
#clear it with 0xff white
pm.clearWith(0xff)

#fitz.Device(pm) is a device for drawing
#we run the display list above through this drawing device
#with area provided
dl.run(fitz.Device(pm), fitz.Identity, rect)

#the drawing device save the result int the pixmap
#and we save the pixmap as a PNG file
pm.writePNG(sys.argv[5])

#and the page is no longer needed for drawing pixmap now
#we can drop those resources
page = None
dv = None
pm = None

#to re-draw the pixmap, we just need to run the display list again
#first, setup the pixmap and its drawing device
pm1 = fitz.Pixmap(fitz.Colorspace(fitz.CS_RGB), rect.round())
pm1.clearWith(0xff)
#then, run the display list, which already contains drawing commands
dl.run(fitz.Device(pm1), fitz.Identity, rect)

#now let's do text search
#first, we need text sheet and text page
ts = fitz.TextSheet()
tp = fitz.TextPage()
#and run the display list throught a text device which is created from text page and text sheet
dl.run(fitz.Device(ts, tp), fitz.Identity, rect)

#now we are ready for search, with max hit count limited to 4
#the return result is a list of hit box rect
res = tp.search(sys.argv[6], 4)
for r in res:
    #we invert the pixmap at the hit irect to highlight the search resuilt
    pm1.invertIRect(r.round())

#and finally write to another PNG
pm1.writePNG('dl-' + sys.argv[5])
