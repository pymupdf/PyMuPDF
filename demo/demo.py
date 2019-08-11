from __future__ import print_function

"""
Copyright 2016-2019, Jorj McKie, mailto:<jorj.x.mckie@outlook.de>

This demonstrates important features of PyMuPDF:

* print a document's metadata
* print the table of contents
* store a raster image (PNG) of a given page
* search for a given string on that page and store another image where
  found text is shown with inverted colors
* print a list of links of the page

Usage:
------
demo.py <filename> <page> <zoom> <degree> <output filename> <needle>

Remarks
--------
This demo version uses the normal user interface of PyMuPDF. If you are
interested in more low level information, have a look at "demo-lowlevel.py" in
the same directory.

"""
import fitz
import sys

print(fitz.__doc__)
assert len(sys.argv) == 7, (
    "Usage: %s <filename> <page> <zoom> <degree> <output filename> <needle>"
    % sys.argv[0]
)

# open a document object from the file path
doc = fitz.open(sys.argv[1])

"""
The metadata is a python dict, whose keys are:
# format, encryption, title, author, subject, keywords, creator, producer,
creationDate, modDate.
The values will be None if the info is not available
"""
print("")
print("Document '%s' has %i pages." % (doc.name, len(doc)))

print("")
print("Metadata Information:")
print("---------------------")
for key in doc.metadata:
    if doc.metadata[key]:
        print(" %s: %s" % (key.title(), doc.metadata[key]))
print("")

# here we print out the outline of the document(if any)
toc = doc.getToC()
if len(toc) == 0:
    print("No Table of Contents available")
else:
    print("Table of Contents:")
    print("------------------")
    for t in toc:
        print("  " * (t[0] - 1), t[0], t[1], "page", t[2])

print("")

# get the page number, which should start from 0
pn = int(sys.argv[2]) - 1
if pn > doc.pageCount:
    raise SystemExit("%s has %d pages only" % (sys.argv[1], doc.pageCount))

# get the page
page = doc[pn]

# we can also get all the links in the current page
links = page.getLinks()
if len(links) == 0:
    print("No links on page", (pn + 1))
else:
    print("Links on page %i:" % (pn + 1))
    print("------------------")
    for ln in links:
        if ln["kind"] == fitz.LINK_GOTO:
            print("Jump to page", ln["page"] + 1)
        elif ln["kind"] in (fitz.LINK_GOTOR, fitz.LINK_LAUNCH):
            print("Open or launch file", ln["file"])
        elif ln["kind"] == fitz.LINK_URI:
            print("Open URI", ln["uri"])

# we create a transformation matrix here
zoom = int(sys.argv[3])
rotate = int(sys.argv[4])
trans = fitz.Matrix(zoom / 100.0, zoom / 100.0).preRotate(rotate)

# create raster image of page (non-transparent)
pm = page.getPixmap(matrix=trans, alpha=False)

# write a PNG image of the page
pm.writePNG(sys.argv[5])

# now we are ready for search, with max hit count limited to 16
# the return result is a list of hit box rectangles
res = page.searchFor(sys.argv[6], hit_max=16)
print("search text '%s' found %i on the page" % (sys.argv[6], len(res)))
for r in res:
    # we invert the pixmap at the hit irect to highlight the search result
    pm.invertIRect(r.round())

# and finally write to another PNG
pm.writePNG("dl-" + sys.argv[5])
