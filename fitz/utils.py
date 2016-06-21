#!/usr/bin/python
# -*- coding: utf-8 -*-
from . import fitz
import math
'''
The following is a collection of commodity functions to simplify the use of PyMupdf.
'''
#==============================================================================
# A function to select certain document pages
#==============================================================================
#def select([list]):
def select(*arg):
    '''select([list of page numbers])\nSelect document pages.
Parameters:\nlist: list of page numbers to retain.\n
Pages not in the list will be deleted. Pages can occur multiple times and in any order.
    '''
    if len(arg) != 2:
        raise ValueError("list of pages is required")
    doc = arg[0]
    if not repr(doc).startswith("fitz.Document"):
        raise ValueError("invalid fitz.Document provided to select")
    if doc.isClosed or doc.isEncrypted:
        raise ValueError("operation on closed or encrypted document")
    liste = arg[1]
    if not doc.name.lower().endswith(("/pdf", ".pdf")):
        raise ValueError("only PDF documents supported")
    r = doc._select(liste)
    if r == 0:
        doc.initData()
    return r

#==============================================================================
# A function for searching string occurrences on a page.
#==============================================================================
#def searchFor(page, text, hit_max = 16):
def searchFor(*arg, **kw):
    '''searchFor(text, hit_max=16)\nSearch for a string on a page.
Parameters:\ntext: string to be searched for\nhit_max: maximum hits.\n
Returns a list of rectangles, each of which surrounds a found occurrence.
    '''
    page = arg[0]
    text = arg[1]
    if "hit_max" in kw:
        hit_max = kw["hit_max"]
    else:
        hit_max = 16
        if kw:
            raise ValueError("invalid keyword parameter specified")

    if not repr(page.parent).startswith("fitz.Document"):
        raise ValueError("invalid page object provided to searchFor")
    if page.parent.isClosed or self.parent.isEncrypted:
        raise ValueError("page operation on closed or encrpted document")

    dl = fitz.DisplayList()                  # create DisplayList
    page.run(fitz.Device(dl), fitz.Identity) # run page through it
    ts = fitz.TextSheet()                    # create TextSheet
    tp = fitz.TextPage()                     # create TextPage
    rect = page.bound()                      # the page's rectangle
    dl.run(fitz.Device(ts, tp), fitz.Identity, rect)   # run the page

    # return list of hitting reactangles
    return tp.search(text, hit_max = hit_max)

#==============================================================================
# A function for extracting a page's text.
#==============================================================================
#def getText(page, output = "text"):
def getText(*arg, **kw):
    '''getText(output='text')\nExtracts a PDF page's text.
Parameters:\noutput option: text, html, json or xml.\n
Returns strings like the TextPage extraction methods extractText, extractHTML,
extractJSON, or etractXML respectively.
Default and misspelling choice is "text".
    '''
    # determine parameters. Using generalized arguments, so we can become a
    # method of the Page class
    if len(arg) != 1:
        raise ValueError("requiring 1 pos. argument, %s given" % (len(arg),))
    page = arg[0]                                # arg[0] = self when Page method
    if not repr(page.parent).startswith("fitz.Document"):
        raise ValueError("invalid page object provided to getText")
    if page.parent.isClosed or page.parent.isEncrypted:
        raise ValueError("page operation on closed or encrypted document")

    if "output" in kw:
        output = kw["output"]
    else:
        output = "text"
        if kw:
            raise ValueError("getText invalid keyword specified")

    # return requested text format
    if output.lower() == "json":
        return page._readPageText(output = 2)
    elif output.lower() == "html":
        return page._readPageText(output = 1)
    elif output.lower() == "xml":
        return page._readPageText(output = 3)
    return page._readPageText(output = 0)

#==============================================================================
# A function for extracting a page's text.
#==============================================================================
#def getPageText(pno, output = "text"):
def getPageText(*arg, **kw):
    '''getPageText(pno, output='text')
Extracts a PDF page's text by page number.
Parameters:\npno: page number\noutput option: text, html, json or xml.\n
Returns strings like the TextPage extraction methods extractText, extractHTML,
extractJSON, or etractXML respectively.
Default and misspelling choice is "text".
    '''
    # determine parameters. Using generics, so we can become a
    # method of the Document class
    if len(arg) != 2:
        raise ValueError("requiring 2 pos. arguments, %s given" % (len(arg),))
    doc = arg[0]                       # arg[0] = self when Document method
    if not repr(doc).startswith("fitz.Document"):
        raise ValueError("invalid fitz.Document object specified")
    if doc.isClosed or doc.isEncrypted:
        raise ValueError("operation on closed or encrypted document")

    pno = int(arg[1])                  # page number
    if pno < 0 or pno >= doc.pageCount:
        raise ValueError("page number not in range 0 to %s" % (doc.pageCount - 1,))

    if "output" in kw:
        output = kw["output"]
    else:
        output = "text"
        if kw:
            raise ValueError("invalid keyword specified to getPageText")

    # return requested text format
    if output.lower() == "json":
        return doc._readPageText(pno, output = 2)
    elif output.lower() == "html":
        return doc._readPageText(pno, output = 1)
    elif output.lower() == "xml":
        return doc._readPageText(pno, output = 3)
    return doc._readPageText(pno, output = 0)

#==============================================================================
# A function for rendering a page's image.
# Requires a page object.
#==============================================================================
#def getPixmap(matrix = fitz.Identity, colorspace = "RGB", clip = None):
def getPixmap(*arg, **kw):
    '''getPixmap(matrix=fitz.Identity, colorspace='rgb', clip = None)
Creates a fitz.Pixmap of a PDF page.
Parameters:\nmatrix: a fitz.Matrix instance to specify required transformations.
Defaults to fitz.Identity (no transformation).
colorspace: text string to specify required colour space (rgb, rgb, gray - case ignored).
Default and misspelling choice is "rgb".
clip: a fitz.IRect to restrict rendering to this area.
    '''
    # get parameters
    if len(arg) != 1:
        raise ValueError("requiring 1 pos. argument, %s given" % (len(arg),))
    page = arg[0]
    if not repr(page.parent).startswith("fitz.Document"):
        raise ValueError("invalid page object provided to getPixmap")
    if page.parent.isClosed or page.parent.isEncrypted:
        raise ValueError("page operation on closed or encrypted document")

    for k in kw.keys():
        if k not in ["matrix", "colorspace", "clip"]:
            raise ValueError("invalid keyword in getPixmap")
    # set default values
    matrix = fitz.Identity
    colorspace = "rgb"
    clip = None

    if "matrix" in kw:
        matrix = kw["matrix"]
    if "colorspace" in kw:
        colorspace = kw["colorspace"]
    if "clip" in kw:
        clip = kw["clip"]

    # determine required colorspace
    if colorspace.upper() == "GRAY":
        cs = fitz.csGRAY
    elif colorspace.upper() == "CMYK":
        cs = fitz.csCMYK
    else:
        cs = fitz.csRGB

    dl = fitz.DisplayList()                  # create DisplayList
    page.run(fitz.Device(dl), fitz.Identity) # run page through it
    r = page.bound()                         # get page boundaries

    if clip:
        r.intersect(clip.getRect())          # only the part within clip
        r.transform(matrix)                  # transform it
        clip = r.round()                     # make IRect copy of it
        ir = clip
    else:                                    # take full page
        r.transform(matrix)                  # transform it
        ir = r.round()                       # make IRect copy of it

    pix = fitz.Pixmap(cs, ir)                # create an empty pixmap
    pix.clearWith(255)                       # clear it with color "white"
    dv = fitz.Device(pix, clip)              # create a "draw" device
    dl.run(dv, matrix, r)                    # render the page
    dv = None
    dl = None
    pix.x = 0
    pix.y = 0
    return pix

#==============================================================================
# A function for rendering a page by its number
#==============================================================================
# getPagePixmap(doc, pno, matrix = fitz.Identity, colorspace = "RGB", clip = None):
def getPagePixmap(*arg, **kw):
    '''getPagePixmap(pno, matrix=fitz.Identity, colorspace="rgb", clip = None)
Creates a fitz.Pixmap object for a document page number.
Parameters:\npno: page number (int)
matrix: a fitz.Matrix instance to specify required transformations.
Defaults to fitz.Identity (no transformation).
colorspace: text string to specify the required colour space (rgb, cmyk, gray - case ignored).
Default and misspelling choice is "rgb".
clip: a fitz.IRect to restrict rendering to this area
    '''
    # get parameters
    if len(arg) != 2:
        raise ValueError("need 2 positional arguments, got %s" % (len(arg),))
    doc = arg[0]
    # check if called with a valid document
    if not repr(doc).startswith("fitz.Document"):
        raise ValueError("invalid fitz.Document provided to getPagePixmap")
    if doc.isClosed or doc.isEncrypted:
        raise ValueError("operation on closed or encrypted document")
    # check if called with a valid page number
    pno = int(arg[1])
    if pno < 0 or pno >= doc.pageCount:
        raise ValueError("page number not in range 0 to %s" % (doc.pageCount - 1,))

    for k in kw.keys():
        if k not in ["matrix", "colorspace", "clip"]:
            raise ValueError("invalid keyword specified to getPagePixmap")
    # default values
    matrix = fitz.Identity
    colorspace = "rgb"
    clip = None

    if "matrix" in kw.keys():
        matrix = kw["matrix"]
    if "colorspace" in kw.keys():
        colorspace = kw["colorspace"]
    if "clip" in kw.keys():
        clip = kw["clip"]

    page = doc.loadPage(pno)

    # determine required colorspace
    if colorspace.upper() == "GRAY":
        cs = fitz.csGRAY
    elif colorspace.upper() == "CMYK":
        cs = fitz.csCMYK
    else:
        cs = fitz.csRGB

    dl = fitz.DisplayList()                  # create DisplayList
    page.run(fitz.Device(dl), fitz.Identity) # run page through it
    r = page.bound()                         # get page boundaries

    if clip:
        r.intersect(clip.getRect())          # only the part within clip
        r.transform(matrix)                  # transform it
        clip = r.round()                     # make IRect copy of it
        ir = clip
    else:                                    # take full page
        r.transform(matrix)                  # transform it
        ir = r.round()                       # make IRect copy of it

    pix = fitz.Pixmap(cs, ir)                # create an empty pixmap
    pix.clearWith(255)                       # clear it with color "white"
    dv = fitz.Device(pix, clip)              # create a "draw" device
    dl.run(dv, matrix, r)                    # render the page
    dv = None
    dl = None
    page = None
    pix.x = 0
    pix.y = 0
    return pix

#==============================================================================
# A function to collect all links of a PDF page.
# Required is a page object previously created by the
# loadPage() method of a document.
#==============================================================================
#def getLinks(page):
def getLinks(*arg, **kw):
    '''getLinks()
Creates a list of all links contained in a PDF page.
Parameters: none\nThe returned list contains a Python dictionary for every link item found.
Every dictionary contains the keys "type" and "kind" to specify the link type / kind.
The presence of other keys depends on this kind - see PyMuPDF's ducmentation for details.'''
    # get parameters
    page = arg[0]

    # check whether called with a valid page
    if not repr(page.parent).startswith("fitz.Document"):
        raise ValueError("invalid page object provided to getLinks")
    if page.parent.isClosed or page.parent.isEncrypted:
        raise ValueError("page operation on closed or encrypted document")
    ln = page.loadLinks()
    links = []
    while ln:
        nl = {"kind":ln.dest.kind, "from": ln.rect}
        flags = bin(ln.dest.flags)[2:].rjust(8, "0")
        if flags[6:] == "11":
            nl["to"] = fitz.Point(ln.dest.lt.x, ln.dest.lt.y)

        if ln.dest.kind == fitz.LINK_URI:
            nl["type"] = "uri"
            nl["uri"] =  ln.dest.uri

        elif ln.dest.kind == fitz.LINK_GOTO:
            nl["type"] = "goto"
            nl["page"] = ln.dest.page

        elif ln.dest.kind == fitz.LINK_GOTOR:
            nl["type"] = "gotor"
            nl["file"] = ln.dest.fileSpec
            nl["page"] = ln.dest.page

        elif ln.dest.kind == fitz.LINK_LAUNCH:
            nl["type"] = "launch"
            nl["file"] = ln.dest.fileSpec

        elif ln.dest.kind == fitz.LINK_NAMED:
            nl["type"] = "named"
            nl["name"] = ln.dest.named

        elif ln.dest.kind == fitz.LINK_NONE:
            nl["type"] = "none"
            nl["page"] = ln.dest.page

        else:
            pass
        links.append(nl)
        ln = ln.next
    return links

#==============================================================================
# A function to collect all bookmarks of a PDF document in the form of a table
# of contents.
#==============================================================================
#def GetToC(doc, simple = True):
def getToC(*arg, **kw):
    '''getToC(simple=True)
Creates a table of contents for a given PDF document.
Parameters:\nsimple: a boolean indicator to control the output
Returns a Python list, where each entry consists of outline level, title, page number
and link destination (if simple = False). For details see PyMuPDF's documentation.'''
    # get parameters
    doc = arg[0]
    if "simple" in kw:
        simple = kw["simple"]
    else:
        simple = True
        if kw:
            raise ValueError("invalid keyword provided to getToc")

    def recurse(olItem, liste, lvl):
        '''Recursively follow the outline item chain and record item information in a list.'''
        while olItem:
            if olItem.title:
                title = olItem.title
            else:
                title = " "
            page = olItem.dest.page + 1
            if not simple:
                link = {"kind": olItem.dest.kind}
                flags = bin(olItem.dest.flags)[2:].rjust(8, "0")
                if flags[6:] == "11":       # valid target top-left coordinate
                    link["to"] = [round(olItem.dest.lt.x, 4), round(olItem.dest.lt.y, 4)]
                page = olItem.dest.page + 1
                if olItem.dest.kind == fitz.LINK_GOTO:
                    link["type"] = "goto"
                    link["page"] = olItem.dest.page

                elif olItem.dest.kind == fitz.LINK_GOTOR:
                    link["type"] = "gotor"
                    link["file"] = olItem.dest.fileSpec
                    link["page"] = olItem.dest.page

                elif olItem.dest.kind == fitz.LINK_LAUNCH:
                    link["type"] = "launch"
                    link["file"] = olItem.dest.fileSpec

                elif olItem.dest.kind == fitz.LINK_URI:
                    link["type"] = "uri"
                    link["uri"] = olItem.dest.uri

                elif olItem.dest.kind == fitz.LINK_NAMED:
                    link["type"] = "named"
                    link["name"] = olItem.dest.named

                elif olItem.dest.kind == fitz.LINK_NONE:
                    link["type"] = "none"
                    link["page"] = olItem.dest.page

                liste.append([lvl, title, page, link])
            else:
                liste.append([lvl, title, olItem.dest.page + 1])
            if olItem.down:
                liste = recurse(olItem.down, liste, lvl+1)
            olItem = olItem.next
        return liste

    # check if we are being called legally
    if not repr(doc).startswith("fitz.Document"):
        raise ValueError("invalid document object provided to getToC")

    # check if document is open and not encrypted
    if doc.isClosed or doc.isEncrypted:
        raise ValueError("operation on closed or encrypted document")

    olItem = doc.outline

    if not olItem: return []
    lvl = 1
    liste = []
    return recurse(olItem, liste, lvl)

#==============================================================================
# A function to determine a pixmap's IRect
#==============================================================================
#def getIRect(pixmap):
def getIRect(*arg, **kw):
    '''getIRect()\nReturns the IRect of a given Pixmap.'''
    # get parameters
    p = arg[0]
    if not repr(p).startswith("fitz.Pixmap"):
        raise ValueError("no valid fitz.Pixmap provided")
    return fitz.IRect(p.x, p.y, p.x + p.width, p.y + p.height)

#==============================================================================
# A function to determine a pixmap's Colorspace
#==============================================================================
#def getColorspace(pixmap):
def getColorspace(*arg, **kw):
    '''Returns the fitz.Colorspace of a given fitz.Pixmap.'''
    # get parameters
    p = arg[0]
    if not repr(p).startswith("fitz.Pixmap"):
        raise ValueError("no valid fitz.Pixmap provided")

    if p.n == 2:
        return fitz.csGRAY
    elif p.n == 4:
        return fitz.csRGB
    elif p.n == 5:
        return fitz.csCMYK
    else:
        raise ValueError("unsupported colorspace in pixmap")

def getRectArea(rect, unit = "pt"):
    '''Calculates the area of a rectangle in square points or millimeters.
Parameters:\nrect: a fitz.IRect or fitz.Rect\nunit: a string, 'pt' means points (default),
"mm" means millimeters.
Returns a float containing the area.
Infinite rectangles (MuPDF definition) have an area of zero.
    '''
    if rect.x1 <= rect.x0 or rect.y1 <= rect.y0:
        return 0.0
    width = float(rect.x1 - rect.x0)
    height = float(rect.y1 - rect.y0)
    area = width * height
    if unit == "pt":
        return area
    else:
        # square mm = pt * (25.4/72)**2
        return area * 0.1244521605

def getPointDistance(p1, p2, unit = "pt"):
    '''Calculates the distance between two points in points or millimeters.
Parameters:\np1, p2: two fitz.Point objects\nunit: a string, 'pt' means points,
"mm" means millimeters.
Returns a float containing the distance.
    '''
    a = float(p2.x - p1.x)
    b = float(p2.y - p1.y)
    c = math.sqrt(a * a + b * b)
    if unit == "pt":
        return c
    else:
        return c * 25.4 / 72.0

#def writeImage(filename, output = "png", savealpha = False):
def writeImage(*arg, **kw):
    '''writeImage(filename, output="png", savealpha=False)
Saves a pixmap to an image.
Parameters:\nfilename: image filename\noutput: requested output format
(one of png, pam, pnm, tga)
savealpha: whether to save the alpha channel
    '''
    pix = arg[0]
    filename = arg[1]
    if "output" in kw:
        output = kw["output"]
    else:
        output = "png"

    if "savealpha" in kw:
        savealpha = kw["savealpha"]
    else:
        savealpha = False
    c_output = 0
    if output == "png":
        c_output = 1
        if not filename.lower().endswith(".png"):
            raise ValueError("output=png requires .png extension")
        if pix.n > 4:
            raise ValueError("colorspace not supported for png")
    elif output == "tga":
        c_output = 4
        if not filename.lower().endswith(".tga"):
            raise ValueError("output=tga requires .tga extension")
        if pix.n > 4:
            raise ValueError("colorspace not supported for tga")
    elif output == "pam":
        c_output = 3
        if not filename.lower().endswith(".pam"):
            raise ValueError("output=pam requires .pam extension")
    elif output == "pnm":
        c_output = 2
        if pix.n > 4:
            raise ValueError("colorspace not supported for pnm")
        if pix.n == 2:
            if not filename.lower().endswith((".pnm", ".pgm")):
                raise ValueError("colorspace requires pnm or pgm extensions")
        elif not filename.lower().endswith((".pnm", "ppm")):
            raise ValueError("colorspace requires pnm or ppm extensions")
    else:
        raise ValueError("invalid output parameter")

    rc = pix._writeIMG(filename, c_output, savealpha)

    return rc

class Pages():
    ''' Creates an iterator over a document's set of pages'''
    def __init__(self, doc):
        if not repr(doc).startswith("fitz.Document"):
            raise ValueError("'%s' is not a valid fitz.Document" %(doc,))
        self.pno      = -1
        self.max      = doc.pageCount - 1
        self.file     = doc.name
        self.isStream = doc.streamlen > 0
        self.doc      = repr(doc)
        self.parent   = doc
        self.page     = None

    def __getitem__(self, i):
        self.page = None
        if i > self.max or i < 0:
            raise StopIteration("page number not in range 0 to %s" % (self.max,))
        self.pno = i
        self.page = self.parent.loadPage(i)
        return self.page

    def __len__(self):
        return self.parent.pageCount

    def __del__(self):
        self.page = None

    def next(self):
        self.page = None
        self.pno += 1
        if self.pno > self.max:
            self.page = None
            raise StopIteration
        self.page = self.parent.loadPage(self.pno)
        return self.page

#==============================================================================
# arithmetic methods for fitz.Matrix
#==============================================================================
def mat_mult(m1, m2):     # __mul__
    if not repr(m2).startswith(("fitz.Matrix", "fitz.Identity")):
        raise NotImplementedError
    m = fitz.Matrix()
    m.concat(m1, m2)
    return m

def mat_invert(m1):       # __invert__
    m = fitz.Matrix()
    r = m.invert(m1)
    return m

def mat_add(m1, m2):      # __add__
    if not repr(m2).startswith(("fitz.Matrix", "fitz.Identity")):
        raise NotImplementedError
    m = fitz.Matrix()
    m.a = m1.a + m2.a
    m.b = m1.b + m2.b
    m.c = m1.c + m2.c
    m.d = m1.d + m2.d
    m.e = m1.e + m2.e
    m.f = m1.f + m2.f
    return m

def mat_sub(m1, m2):      # __sub__
    if not repr(m2).startswith(("fitz.Matrix", "fitz.Identity")):
        raise NotImplementedError
    m = fitz.Matrix()
    m.a = m1.a - m2.a
    m.b = m1.b - m2.b
    m.c = m1.c - m2.c
    m.d = m1.d - m2.d
    m.e = m1.e - m2.e
    m.f = m1.f - m2.f
    return m

def mat_neg(m1):          # __neg__
    m = fitz.Matrix()
    m.a = -m1.a
    m.b = -m1.b
    m.c = -m1.c
    m.d = -m1.d
    m.e = -m1.e
    m.f = -m1.f
    return m

def mat_abs(m):           # __abs__
    a = m.a**2 + m.b**2 + m.c**2 + m.d**2 + m.e**2 + m.f**2
    return math.sqrt(a)

def mat_true(m):          # __nonzero__
    a = m.a**2 + m.b**2 + m.c**2 + m.d**2 + m.e**2 + m.f**2
    return a > 0.0

#==============================================================================
# arithmetic methods for fitz.Rect
#==============================================================================
def rect_neg(r):             # __neg__: (-1)*r, also for irect
    if repr(r).startswith("fitz.Rect"):
        nr = fitz.Rect(r)
    else:
        nr = fitz.IRect(r)
    nr.x0 *= -1
    nr.y0 *= -1
    nr.x1 *= -1
    nr.y1 *= -1
    return nr

def rect_or(r1, r2):         # __or__: include point, rect or irect
    if not repr(r1).startswith("fitz.Rect"):
        raise NotImplementedError
    if not repr(r2).startswith(("fitz.Rect", "fitz.IRect", "fitz.Point")):
        raise NotImplementedError
    r = fitz.Rect(r1)
    if repr(r2).startswith("fitz.Rect"):
        return r.includeRect(r2)
    elif repr(r2).startswith("fitz.IRect"):
        return r.includeRect(r2.getRect())
    return r.includePoint(r2)

def rect_and(r1, r2):        # __and__: intersection with rect or irect
    if not repr(r1).startswith("fitz.Rect"):
        raise NotImplementedError
    if not repr(r2).startswith(("fitz.Rect", "fitz.IRect")):
        raise NotImplementedError
    r = fitz.Rect(r1)
    if repr(r2).startswith("fitz.Rect"):
        return r.intersect(r2)
    if repr(r2).startswith("fitz.IRect"):
        return r.intersect(r2.getRect())
    raise NotImplementedError

def rect_add(r1, r2):        # __add__: add number, rect or irect to rect
    if not repr(r1).startswith("fitz.Rect"):
        raise NotImplementedError
    r = fitz.Rect(r1)
    if repr(r2).startswith(("fitz.Rect", "fitz.IRect")):
        a = r2
    elif type(r2) is int or type(r2) is float:
        a = fitz.Rect(r2, r2, r2, r2)
    else:
        raise NotImplementedError
    r.x0 += a.x0
    r.y0 += a.y0
    r.x1 += a.x1
    r.y1 += a.y1
    return r

def rect_sub(r1, r2):        # __sub__: subtract number, rect or irect from rect
    if not repr(r1).startswith("fitz.Rect"):
        raise NotImplementedError
    r = fitz.Rect(r1)
    if repr(r2).startswith(("fitz.Rect", "fitz.IRect")):
        a = r2
    elif type(r2) is int or type(r2) is float:
        a = fitz.Rect(r2, r2, r2, r2)
    else:
        raise NotImplementedError
    r.x0 -= a.x0
    r.y0 -= a.y0
    r.x1 -= a.x1
    r.y1 -= a.y1
    return r

def rect_mul(r, m):          # __mul__: transform with matrix
    if not repr(r).startswith("fitz.Rect"):
        raise NotImplementedError
    if not repr(m).startswith(("fitz.Matrix", "fitz.Identity")):
        raise NotImplementedError
    r1 = fitz.Rect(r)
    return r1.transform(m)

#==============================================================================
# arithmetic methods for fitz.IRect
#==============================================================================
def irect_or(r1, r2):        # __or__: include a point, rect or irect
    if not repr(r1).startswith("fitz.IRect"):
        raise NotImplementedError
    if not repr(r2).startswith(("fitz.Rect", "fitz.IRect", "fitz.Point")):
        raise NotImplementedError
    r = r1.getRect()
    if repr(r2).startswith("fitz.Rect"):
        return r.includeRect(r2).round()
    elif repr(r2).startswith("fitz.IRect"):
        return r.includeRect(r2.getRect()).round()
    return r.includePoint(r2).round()

def irect_and(r1, r2):       # __and__: intersection with a rect or irect
    if not repr(r1).startswith("fitz.IRect"):
        raise NotImplementedError
    if not repr(r2).startswith(("fitz.Rect", "fitz.IRect")):
        raise NotImplementedError
    r = fitz.IRect(r1)
    if repr(r2).startswith("fitz.Rect"):
        return r.intersect(r2).round()
    if repr(r2).startswith("fitz.IRect"):
        return r.intersect(r2)
    raise NotImplementedError

def irect_add(r1, r2):       # __add__: add a number, rect or irect
    if not repr(r1).startswith("fitz.IRect"):
        raise NotImplementedError
    r = r1.getRect()
    if repr(r2).startswith(("fitz.Rect", "fitz.IRect")):
        a = r2
    elif type(r2) is int or type(r2) is float:
        a = fitz.Rect(r2, r2, r2, r2)
    else:
        raise NotImplementedError
    r.x0 += a.x0
    r.y0 += a.y0
    r.x1 += a.x1
    r.y1 += a.y1
    return r.round()

def irect_sub(r1, r2):       # __sub__: subtract number, rect or irect
    if not repr(r1).startswith("fitz.IRect"):
        raise NotImplementedError
    r = r1.getRect()
    if repr(r2).startswith(("fitz.Rect", "fitz.IRect")):
        a = r2
    elif type(r2) is int or type(r2) is float:
        a = fitz.Rect(r2, r2, r2, r2)
    else:
        raise NotImplementedError
    r.x0 -= a.x0
    r.y0 -= a.y0
    r.x1 -= a.x1
    r.y1 -= a.y1
    return r.round()

def irect_mul(r, m):         # __mul__: transform with matrix
    if not repr(r).startswith("fitz.IRect"):
        raise NotImplementedError
    if not repr(m).startswith(("fitz.Matrix", "fitz.Identity")):
        raise NotImplementedError
    r1 = r.getRect()
    return r1.transform(m).round()

#==============================================================================
# arithmetic methods for fitz.Point
#==============================================================================
def point_neg(p):            # __neg__: point with negated coordinates
    return fitz.Point(-p.x, -p.y)

def point_add(p1, p2):
    if not repr(p1).startswith("fitz.Point"):
        raise NotImplementedError
    if repr(p2).startswith("fitz.Point"):
        p = p2
    elif type(p2) is int or type(p2) is float:
        p = fitz.Point(p2, p2)
    else:
        raise NotImplementedError
    return fitz.Point(p1.x + p.x, p1.y + p.y)

def point_sub(p1, p2):
    if not repr(p1).startswith("fitz.Point"):
        raise NotImplementedError
    if repr(p2).startswith("fitz.Point"):
        p = p2
    elif type(p2) is int or type(p2) is float:
        p = fitz.Point(p2, p2)
    else:
        raise NotImplementedError
    return fitz.Point(p1.x - p.x, p1.y - p.y)

def point_mul(p, m):
    if not repr(p).startswith("fitz.Point"):
        raise NotImplementedError
    if not repr(m).startswith(("fitz.Matrix", "fitz.Identity")):
        raise NotImplementedError
    p1 = fitz.Point(p)
    return p1.transform(m)

def point_abs(p):
    return math.sqrt(p.x**2 + p.y**2)

#==============================================================================
# Document method Set Metadata
#==============================================================================
def setMetadata(doc, m):
    '''Set a PDF document's metadata (/Info dictionary)\nParameters:\nm: a dictionary with valid metadata keys.\nAfter execution, the metadata property will be updated.
    '''
    if not repr(doc).startswith("fitz.Document") or not doc.name.lower().endswith(("/pdf", ".pdf")):
        raise ValueError("argument 1 must be a PDF document")
    if doc.isClosed or doc.isEncrypted:
        raise ValueError("operation on closed or encrypted document")
    if type(m) is not dict:
        raise ValueError("argument 2 must be a dictionary")
    for k in m.keys():
        if not k in ["author", "producer", "creator", "title", "format", "encryption",
                     "creationDate", "modDate", "subject", "keywords"]:
            raise ValueError("invalid dictionary key: " + k)

    d = "<</Author("
    d += "none" if not m.get("author") else m["author"]
    d += ")/CreationDate("
    d += "none" if not m.get("creationDate") else m["creationDate"]
    d += ")/Creator("
    d += "none" if not m.get("creator") else m["creator"]
    d += ")/Keywords("
    d += "none" if not m.get("keywords") else m["keywords"]
    d += ")/ModDate("
    d += "none" if not m.get("modDate") else m["modDate"]
    d += ")/Producer("
    d += "none" if not m.get("producer") else m["producer"]
    d += ")/Subject("
    d += "none" if not m.get("subject") else m["subject"]
    d += ")/Title("
    d += "none" if not m.get("title") else m["title"]
    d += ")>>"
    r = doc._setMetadata(d)
    if r == 0:
        doc.initData()
    return r

#==============================================================================
# Document method set Table of Contents
#==============================================================================
def setToC(doc, toc):
    '''Creates a new outline tree (table of contents) for a PDF document.\nParameters:
    doc: a PDF document opened with PyMuPDF
    toc: a Python list of lists. Each entry must contain level, title, page and optionally top margin on the page.
    Returns zero (int) on success.
    '''
    if not repr(doc).startswith("fitz.Document"):
        raise ValueError("arg1 not a document")
    if not doc.name.lower().endswith(("/pdf", ".pdf")):
        raise ValueError("not a PDF document")
    if doc.isClosed or doc.isEncrypted:
        raise ValueError("operation on closed or encrypted document")

    toclen = len(toc)
    # check toc validity
    if type(toc) is not list:
        raise ValueError("arg2 must be a list")
    t0 = toc[0]
    if type(t0) is not list:
        raise ValueError("arg2 must be a list of lists of 3 or 4 items")
    if t0[0] != 1:
        raise ValueError("item 0 must have hierarchy level 1")
    for i in list(range(toclen-1)):
        t1 = toc[i]
        t2 = toc[i+1]
        if (type(t2) is not list) or len(t2) < 3 or len(t2) > 4:
            raise ValueError("arg2 must be a list of lists of 3 or 4 items")
        if (type(t2[0]) is not int) or t2[0] < 1:
            raise ValueError("hierarchy levels must be int > 0")
        if t2[0] > t1[0] + 1:
            raise ValueError("hierarchy steps must not be > 1")

    doc._delToC()                      # delete existing outlines

    xref = [0] * (1+toclen)            # prepare table of new xref entries
    xref[0] = doc._getOLRootNumber()   # entry zero is outline root xref#

    for i in list(range(toclen)):
        xref[i+1] = doc._getNewXref()  # allocate new xref entries

    lvltab = {0:0}                     # stores last entry per hierarchy level

    # contains new outline objects as strings
    olitems = [{"count":0, "first":-1, "last":-1, "xref":xref[0]}]

    for i in list(range(toclen)):
        o = toc[i]
        lvl = o[0] # level
        title = o[1] # titel
        pno = o[2] - 1 # page number
        p = doc.loadPage(pno)
        top = int(round(p.bound().y1) - 36)   # default top location on page
        p = None                              # free page resources
        top1 = top + 0                        # accept provided top parameter
        if len(o) > 3:
            if type(o[3]) is int or type(o[3]) is float:
                top1 = int(round(o[3]))
            else:
                try:
                    top1 = int(round(o[3]["to"][1])) # top
                except: pass
        if top1 >= 0 and top1 <= top:
            top = top1
        d = {}
        d["first"] = -1
        d["count"] = 0
        d["last"]  = -1
        d["prev"]  = -1
        d["next"]  = -1
        d["page"]  = doc._getPageObjNumber(pno)
        d["top"]   = top
        d["title"] = title
        d["parent"] = lvltab[lvl-1]
        d["xref"] = xref[i + 1]
        lvltab[lvl] = i+1
        parent = olitems[lvltab[lvl-1]]
        parent["count"] += 1

        if parent["first"] == -1:
            parent["first"] = i+1
            parent["last"] = i+1
        else:
            d["prev"] = parent["last"]
            prev = olitems[parent["last"]]
            prev["next"]   = i+1
            parent["last"] = i+1
        olitems.append(d)

    for i, ol in enumerate(olitems):
        txt = "<<"
        if ol["count"] > 0:
            txt += "/Count " + str(ol["count"])
        try:
            txt += "/Dest[" + str(ol["page"][0]) + " " + str(ol["page"][1]) + " R/XYZ 0 " + str(ol["top"]) + " 0]"
        except: pass
        try:
            if ol["first"] > -1:
                txt += "/First " + str(xref[ol["first"]]) + " 0 R"
        except: pass
        try:
            if ol["last"] > -1:
                txt += "/Last " + str(xref[ol["last"]]) + " 0 R"
        except: pass
        try:
            if ol["next"] > -1:
                txt += "/Next " + str(xref[ol["next"]]) + " 0 R"
        except: pass
        try:
            if ol["parent"] > -1:
                txt += "/Parent " + str(xref[ol["parent"]]) + " 0 R"
        except: pass
        try:
            if ol["prev"] > -1:
                txt += "/Prev " + str(xref[ol["prev"]]) + " 0 R"
        except: pass
        try:
            txt += "/Title(" + str(ol["title"]) + ")"
        except: pass
        if i == 0:
            txt += "/Type/Outlines"
        txt += ">>"
        rc = doc._updateObject(xref[i], txt)
        if rc != 0:
            raise ValueError("outline insert error:\n" + txt)

    doc.initData()
    return 0