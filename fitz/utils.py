#!/usr/bin/python
# -*- coding: utf-8 -*-
from . import fitz
import math, sys
from binascii import hexlify
'''
The following is a collection of commodity functions to simplify the use of PyMupdf.
'''
#==============================================================================
# A function for searching string occurrences on a page.
#==============================================================================
#def searchFor(page, text, hit_max = 16):
def searchFor(page, text, hit_max = 16):
    '''Search for a string on a page. Parameters:\ntext: string to be searched for\nhit_max: maximum hits.\nReturns a list of rectangles, each of which surrounds a found occurrence.'''
    if page.parent is None:
        raise RuntimeError("orphaned object: parent is None")

    rect = page.rect
    dl = fitz.DisplayList(rect)         # create DisplayList
    page.run(fitz.Device(dl), fitz.Identity) # run page through it
    ts = fitz.TextSheet()                    # create TextSheet
    tp = fitz.TextPage(rect)            # create TextPage
    dl.run(fitz.Device(ts, tp), fitz.Identity, rect)   # run the page
    # return list of hitting reactangles
    return tp.search(text, hit_max = hit_max)

#==============================================================================
# A function for searching string occurrences on a page.
#==============================================================================
def searchPageFor(doc, pno, text, hit_max=16):
    """Search for a string on a page. Parameters:\npno: integer page number\ntext: string to be searched for\nhit_max: maximum hits.\nReturns a list of rectangles, each of which surrounds a found occurrence."""
    return searchFor(doc[pno], text, hit_max = hit_max)
    
#==============================================================================
# A function for extracting a page's text.
#==============================================================================
#def getText(page, output = "text"):
def getText(page, output = "text"):
    '''Extract a PDF page's text. Parameters:\noutput option: text, html, json or xml.\nReturns strings like the TextPage extraction methods extractText, extractHTML, extractJSON, or etractXML respectively. Default and misspelling choice is "text".'''
    if page.parent is None:
        raise RuntimeError("orphaned object: parent is None")

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
def getPageText(doc, pno, output = "text"):
    '''Extract a PDF page's text by page number. Parameters:\npno: page number\noutput option: text, html, json or xml.\nReturns strings like the TextPage extraction methods extractText, extractHTML, extractJSON, or etractXML respectively. Default and misspelling choice is "text".'''
    return doc[pno].getText(output = output)

#==============================================================================
# A function for rendering a page's image.
# Requires a page object.
#==============================================================================

def getPixmap(page, matrix = fitz.Identity, colorspace = "rgb", clip = None,
              alpha = True):
    '''Create pixmap of page.\nmatrix: fitz.Matrix for transformation (default: fitz.Identity).\ncolorspace: text string / fitz.Colorspace (rgb, rgb, gray - case ignored), default fitz.csRGB.\nclip: a fitz.IRect to restrict rendering to this area.'''
    if page.parent is None:
        raise RuntimeError("orphaned object: parent is None")

    # determine required colorspace
    cs = colorspace
    if type(colorspace) is str:
        if colorspace.upper() == "GRAY":
            cs = fitz.csGRAY
        elif colorspace.upper() == "CMYK":
            cs = fitz.csCMYK
        else:
            cs = fitz.csRGB
    assert cs.n in (1,3,4), "unsupported colorspace"    

    r = page.rect                            # get page boundaries
    dl = fitz.DisplayList(r)                 # create DisplayList
    page.run(fitz.Device(dl), fitz.Identity) # run page through it

    if clip:
        r.intersect(clip.getRect())          # only the part within clip
        r.transform(matrix)                  # transform it
        clip = r.irect                       # make IRect copy of it
        ir = clip
    else:                                    # take full page
        r.transform(matrix)                  # transform it
        ir = r.irect                         # make IRect copy of it

    pix = fitz.Pixmap(cs, ir, alpha)         # create an empty pixmap
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
# getPagePixmap(doc, pno, matrix = fitz.Identity, colorspace = "RGB", clip = None, alpha = False):
def getPagePixmap(doc, pno, matrix = fitz.Identity, colorspace = "rgb",
                  clip = None, alpha = True):
    '''Create pixmap of page number.\nmatrix: fitz.Matrix for transformation (default: fitz.Identity).\ncolorspace: text string / fitz.Colorspace (rgb, rgb, gray - case ignored), default fitz.csRGB.\nclip: a fitz.IRect to restrict rendering to this area.'''
    return doc[pno].getPixmap(matrix = matrix, colorspace = colorspace,
                          clip = clip, alpha = alpha)

#==============================================================================
# An internal function to create a link info dictionary for getToC and getLinks
#==============================================================================
def getLinkDict(ln):
    nl = {"kind": ln.dest.kind, "xref": 0, "id": id(ln)}
    try:
        nl["from"] = ln.rect
    except:
        pass
    pnt = fitz.Point(0, 0)
    if ln.dest.flags & fitz.LINK_FLAG_L_VALID:
        pnt.x = ln.dest.lt.x
    if ln.dest.flags & fitz.LINK_FLAG_T_VALID:
        pnt.y = ln.dest.lt.y

    if ln.dest.kind == fitz.LINK_URI:
        nl["uri"] = ln.dest.uri

    elif ln.dest.kind == fitz.LINK_GOTO:
        nl["page"] = ln.dest.page
        nl["to"] = pnt
        if ln.dest.flags & fitz.LINK_FLAG_R_IS_ZOOM:
            nl["zoom"] = ln.dest.rb.x
        else:
            nl["zoom"] = 0.0

    elif ln.dest.kind == fitz.LINK_GOTOR:
        nl["file"] = ln.dest.fileSpec.replace("\\", "/")
        nl["page"] = ln.dest.page
        if ln.dest.page < 0:
            nl["to"] = ln.dest.dest
        else:
            nl["to"] = pnt
            if ln.dest.flags & fitz.LINK_FLAG_R_IS_ZOOM:
                nl["zoom"] = ln.dest.rb.x
            else:
                nl["zoom"] = 0.0

    elif ln.dest.kind == fitz.LINK_LAUNCH:
        nl["file"] = ln.dest.fileSpec.replace("\\", "/")

    elif ln.dest.kind == fitz.LINK_NAMED:
        nl["name"] = ln.dest.named

    else:
        nl["page"] = ln.dest.page

    return nl

#==============================================================================
# A function to collect all links of a PDF page.
# Required is a page object previously created by the
# loadPage() method of a document.
#==============================================================================
def getLinks(page):
    '''Create a list of all links contained in a PDF page as dictionaries - see PyMuPDF ducmentation for details.'''

    if page.parent is None:
        raise RuntimeError("orphaned object: parent is None")
    ln = page.firstLink
    links = []
    while ln:
        nl = getLinkDict(ln)
        links.append(nl)
        ln = ln.next
    if len(links) > 0:
        linkxrefs = page._getLinkXrefs()
        if len(linkxrefs) == len(links):
            for i in range(len(linkxrefs)):
                links[i]["xref"] = linkxrefs[i]
    return links

#==============================================================================
# A function to collect all bookmarks of a PDF document in the form of a table
# of contents.
#==============================================================================
def getToC(doc, simple = True):
    '''Create a table of contents.\nsimple: a bool to control output. Returns a list, where each entry consists of outline level, title, page number and link destination (if simple = False). For details see PyMuPDF's documentation.'''

    def recurse(olItem, liste, lvl):
        '''Recursively follow the outline item chain and record item information in a list.'''
        while olItem:
            if olItem.title:
                title = olItem.title
            else:
                title = " "

            if not olItem.isExternal:
                if olItem.uri:
                    page = olItem.page + 1
                else:
                    page = -1
            else:
                page = -1

            if not simple:
                link = getLinkDict(olItem)
                liste.append([lvl, title, page, link])
            else:
                liste.append([lvl, title, page])

            if olItem.down:
                liste = recurse(olItem.down, liste, lvl+1)
            olItem = olItem.next
        return liste

    # check if document is open and not encrypted
    if doc.isClosed:
        raise RuntimeError("illegal operation on closed document")

    olItem = doc.outline

    if not olItem: return []
    lvl = 1
    liste = []
    return recurse(olItem, liste, lvl)

def getRectArea(*args):
    """Calculate area of rectangle.\nparameter is one of 'px' (default), 'in', 'cm', or 'mm'."""
    rect = args[0]
    if len(args) > 1:
        unit = args[1]
    else:
        unit = "px"    
    if rect.isInfinite or rect.isEmpty:
        return 0.0
    u = {"px": (1,1), "in": (1.,72.), "cm": (2.54, 72.), "mm": (25.4, 72.)}
    f = (u[unit][0] / u[unit][1])**2
    return f * rect.width * rect.height

#def writeImage(filename, output = "png"):
def writeImage(*arg, **kw):
    '''Save pixmap to file.\nfilename: image filename\noutput: requested output format (png, pam, pnm or tga).'''
    pix = arg[0]
    filename = arg[1]
    if "output" in kw:
        output = kw["output"]
    else:
        output = "png"

    c_output = 0
    if output == "png":
        c_output = 1
        if not filename.lower().endswith(".png"):
            raise ValueError("require .png extension")
        if pix.colorspace.n > 3:
            raise ValueError(pix.colorspace.name + " not supported for png")
    elif output == "tga":
        c_output = 4
        if not filename.lower().endswith(".tga"):
            raise ValueError("require .tga extension")
        if pix.colorspace.n > 3:
            raise ValueError(pix.colorspace.name + " not supported for tga")
    elif output == "pam":
        c_output = 3
        if not filename.lower().endswith(".pam"):
            raise ValueError("require .pam extension")
    elif output == "pnm":
        c_output = 2
        if pix.colorspace.n > 3:
            raise ValueError(pix.colorspace.name + " not supported for pnm")
        if pix.n <= 2:
            if not filename.lower().endswith((".pnm", ".pgm")):
                raise ValueError("colorspace requires pnm or pgm extensions")
        elif not filename.lower().endswith((".pnm", "ppm")):
            raise ValueError("colorspace requires pnm or ppm extensions")
    else:
        raise ValueError("invalid output parameter")

    rc = pix._writeIMG(filename, c_output)

    return rc

#==============================================================================
# arithmetic methods for fitz.Matrix
#==============================================================================
def mat_mult(m1, m2):     # __mul__
    if type(m2) in (int, float):
        return fitz.Matrix(m1.a * m2, m1.b * m2, m1.c * m2,
                           m1.d * m2, m1.e * m2, m1.f * m2)
    m = fitz.Matrix()
    try:
        m.concat(m1, m2)
    except:
        raise NotImplementedError("op2 must be 'Matrix' or number")
    return m

def mat_invert(me):       # __invert__
    m = fitz.Matrix()
    m.invert(me)
    return m

def mat_add(m1, m2):      # __add__
    if type(m2) in (int, float):
        return fitz.Matrix(m1.a + m2, m1.b + m2, m1.c + m2,
                           m1.d + m2, m1.e + m2, m1.f + m2)
    try:
        return fitz.Matrix(m1.a + m2.a, m1.b + m2.b, m1.c + m2.c,
                           m1.d + m2.d, m1.e + m2.e, m1.f + m2.f)
    except:
        raise NotImplementedError("op2 must be 'Matrix' or number")

def mat_sub(m1, m2):      # __sub__
    if type(m2) in (int, float):
        return fitz.Matrix(m1.a - m2, m1.b - m2, m1.c - m2,
                           m1.d - m2, m1.e - m2, m1.f - m2)
    try:
        return fitz.Matrix(m1.a - m2.a, m1.b - m2.b, m1.c - m2.c,
                           m1.d - m2.d, m1.e - m2.e, m1.f - m2.f)
    except:
        raise NotImplementedError("op2 must be 'Matrix' or number")

def mat_abs(m):           # __abs__
    a = m.a**2 + m.b**2 + m.c**2 + m.d**2 + m.e**2 + m.f**2
    return math.sqrt(a)

def mat_true(m):          # __nonzero__
    return (abs(m.a) + abs(m.b) + abs(m.c) + abs(m.d) + abs(m.e) + abs(m.f)) > 0

def mat_equ(m, m2):       # __equ__
    return len(m) == len(m2) and mat_true(m - m2) == 0

def mat_contains(m, x):
    if type(x) not in (int, float):
        return False
    else:
        return x in tuple(m)

#==============================================================================
# arithmetic methods for fitz.Rect
#==============================================================================
def rect_or(r1, r2):         # __or__: include point, rect or irect
    if type(r2) not in (fitz.Rect, fitz.IRect, fitz.Point):
        raise NotImplementedError("op2 must be 'Rect', 'IRect' or 'Point'")
    if type(r1) is fitz.Rect:
        r = fitz.Rect(r1)
    else:
        r = r1.rect
    if type(r2) is fitz.Rect:
        r.includeRect(r2)
    elif type(r2) is fitz.IRect:
        r.includeRect(r2.rect)
    else:
        r.includePoint(r2)
    if type(r1) is fitz.Rect:
        return r
    else:
        return r.irect

def rect_and(r1, r2):        # __and__: intersection with rect or irect
    if type(r2) not in (fitz.Rect, fitz.IRect):
        raise NotImplementedError("op2 must be 'Rect' or 'IRect'")
    if type(r1) is fitz.Rect:
        r = fitz.Rect(r1)
    else:
        r = r1.rect
    if type(r2) is fitz.Rect:
        r.intersect(r2)
    else:
        r.intersect(r2.rect)
    if type(r1) is fitz.Rect:
        return r
    else:
        return r.irect

def rect_add(r1, r2):        # __add__: add number, rect or irect to rect
    if type(r1) is fitz.Rect:
        r = fitz.Rect(r1)
    else:
        r = r1.rect
    if type(r2) in (fitz.Rect, fitz.IRect):
        a = r2
    elif type(r2) in (int, float):
        a = fitz.Rect(r2, r2, r2, r2)
    else:
        raise NotImplementedError("op2 must be 'Rect', 'Irect' or number")
    r.x0 += a.x0
    r.y0 += a.y0
    r.x1 += a.x1
    r.y1 += a.y1
    if type(r1) is fitz.Rect:
        return r
    else:
        return r.irect

def rect_sub(r1, r2):        # __sub__: subtract number, rect or irect from rect
    if type(r1) is fitz.Rect:
        r = fitz.Rect(r1)
    else:
        r = r1.rect

    if type(r2) in (fitz.Rect, fitz.IRect):
        a = r2
    elif type(r2) in (int, float):
        a = fitz.Rect(r2, r2, r2, r2)
    else:
        raise NotImplementedError("op2 must be 'Rect', 'Irect' or number")
    r.x0 -= a.x0
    r.y0 -= a.y0
    r.x1 -= a.x1
    r.y1 -= a.y1
    if type(r1) is fitz.Rect:
        return r
    else:
        return r.irect

def rect_mul(r, m):          # __mul__: transform with matrix
    if type(r) is fitz.Rect:
        r1 = fitz.Rect(r)
    else:
        r1 = r.rect
    if type(m) in (int, float):
        r1 = fitz.Rect(r1.x0 * m, r1.y0 * m, r1.x1 * m, r1.y1 * m)
    else:
        try:
            r1.transform(m)
        except:
            raise NotImplementedError("op2 must be number or 'Matrix'")
    if type(r) is fitz.Rect:
        return r1
    else:
        return r1.irect

def rect_equ(r, r2):       # __equ__
    return type(r) == type(r2) and rect_true(r - r2) == 0

def rect_true(r):
    return (abs(r.x0) + abs(r.y0) + abs(r.x1) + abs(r.y1)) > 0
    
#==============================================================================
# arithmetic methods for fitz.Point
#==============================================================================
def point_add(p1, p2):
    if type(p2) is fitz.Point:
        p = p2
    elif type(p2) in (int, float):
        p = fitz.Point(p2, p2)
    else:
        raise NotImplementedError("op2 must be 'Point' or number")
    return fitz.Point(p1.x + p.x, p1.y + p.y)

def point_sub(p1, p2):
    if type(p2) is fitz.Point:
        p = p2
    elif type(p2) in (int, float):
        p = fitz.Point(p2, p2)
    else:
        raise NotImplementedError("op2 must be 'Point' or number")
    return fitz.Point(p1.x - p.x, p1.y - p.y)

def point_mul(p, m):
    if type(m) in (int, float):
        return fitz.Point(p.x*m, p.y*m)
    p1 = fitz.Point(p)
    try:
        return p1.transform(m)
    except:
        raise NotImplementedError("op2 must be 'Matrix' or number")

def point_abs(p):
    return math.sqrt(p.x**2 + p.y**2)

def point_true(p):
    return (abs(p.x) + abs(p.y)) > 0

def point_equ(p, p2):       # __equ__
    return type(p) == type(p2) and point_true(p - p2) == 0

def point_contains(p, x):
    if type(x) not in (int, float):
        return False
    else:
        return x in tuple(p)

#==============================================================================
# Returns a PDF string depending on its coding.
# If only ascii then "(original)" is returned,
# else if only 8 bit chars then "(original)" with interspersed octal strings
# \nnn is returned,
# else a string "<FEFF[hexstring]>" is returned, where [hexstring] is the
# UTF-16BE encoding of the original.
#==============================================================================
def PDFstr(s):
    try:
        x = s.decode("utf-8")
    except:
        x = s
    if x is None: x = ""
    if isinstance(x, str) or sys.version_info[0] < 3 and isinstance(x, unicode):
        pass
    else:
        raise ValueError("non-string provided to PDFstr function")

    utf16 = False
    # following returns ascii original string with mixed-in octal numbers \nnn
    # for chr(128) - chr(255)
    r = ""
    for i in range(len(x)):
        if ord(x[i]) <= 127:
            r += x[i]                            # copy over ascii chars
        elif ord(x[i]) <= 255:
            r += "\\" + oct(ord(x[i]))[-3:]      # octal number with backslash
        else:                                    # skip to UTF16_BE case
            utf16 = True
            break
    if not utf16:
        return "(" + r + ")"                     # result in brackets

    # require full unicode: make a UTF-16BE hex string prefixed with "feff"
    r = hexlify(bytearray([254, 255]) + bytearray(x, "UTF-16BE"))
    t = r.decode("utf-8")                        # make str in Python 3
    return "<" + t + ">"                         # brackets indicate hex

#==============================================================================
# Document method Set Metadata
#==============================================================================
def setMetadata(doc, m):
    """Set a PDF's metadata (/Info dictionary)\nm: dictionary like doc.metadata'."""
    if doc.isClosed or doc.isEncrypted:
        raise ValueError("operation on closed or encrypted document")
    if type(m) is not dict:
        raise ValueError("arg2 must be a dictionary")
    for k in m.keys():
        if not k in ("author", "producer", "creator", "title", "format",
                     "encryption", "creationDate", "modDate", "subject",
                     "keywords"):
            raise ValueError("invalid dictionary key: " + k)

    d = "<</Author"
    d += PDFstr(m.get("author", "none"))
    d += "/CreationDate"
    d += PDFstr(m.get("creationDate", "none"))
    d += "/Creator"
    d += PDFstr(m.get("creator", "none"))
    d += "/Keywords"
    d += PDFstr(m.get("keywords", "none"))
    d += "/ModDate"
    d += PDFstr(m.get("modDate", "none"))
    d += "/Producer"
    d += PDFstr(m.get("producer", "none"))
    d += "/Subject"
    d += PDFstr(m.get("subject", "none"))
    d += "/Title"
    d += PDFstr(m.get("title", "none"))
    d += ">>"
    r = doc._setMetadata(d)
    if r == 0:
        doc.initData()
    return r

def getDestStr(xref, ddict):
    if not ddict:
        return ""
    str_goto = "/Dest[%s %s R/XYZ %s %s %s]"

    if type(ddict) in (int, float):
        dest = str_goto % (xref[0], xref[1], 0, str(ddict), 0)
        return dest
    d_kind = ddict["kind"]

    if d_kind == fitz.LINK_NONE:
        return ""

    if ddict["kind"] == fitz.LINK_GOTO:
        d_zoom = ddict["zoom"]
        d_left = ddict["to"].x
        d_top  = ddict["to"].y
        dest = str_goto % (xref[0], xref[1], str(d_left), str(d_top),
                           str(d_zoom))
        return dest

    str_gotor1 = "/A<</D[%s /XYZ %s %s %s]/F<</F%s/UF%s/Type/Filespec>>" \
                 "/S/GoToR>>"
    str_gotor2 = "/A<</D%s/F<</F%s/UF%s/Type/Filespec>>/S/GoToR>>"
    str_launch = "/A<</F<</F%s/UF%s/Type/Filespec>>/S/Launch>>"
    str_uri    = "/A<</S/URI/URI%s/Type/Action>>"

    if ddict["kind"] == fitz.LINK_URI:
        dest = str_uri % (PDFstr(ddict["uri"]),)
        return dest

    if ddict["kind"] == fitz.LINK_LAUNCH:
        fspec = PDFstr(ddict["file"])
        dest = str_launch % (fspec, fspec)
        return dest

    if ddict["kind"] == fitz.LINK_GOTOR and ddict["page"] < 0:
        fspec = PDFstr(ddict["file"])
        dest = str_gotor2 % (PDFstr(ddict["to"]), fspec, fspec)
        return dest

    if ddict["kind"] == fitz.LINK_GOTOR and ddict["page"] >= 0:
        fspec = PDFstr(ddict["file"])
        dest = str_gotor1 % (ddict["page"], ddict["to"].x, ddict["to"].y,
                                   ddict["zoom"], fspec, fspec)
        return dest

    return ""

#==============================================================================
# Document method set Table of Contents
#==============================================================================
def setToC(doc, toc):
    '''Create new outline tree (table of contents)\ntoc: a Python list of lists. Each entry must contain level, title, page and optionally top margin on the page.'''
    if not doc.name.lower().endswith(("/pdf", ".pdf")) and len(doc.name) > 0:
        raise ValueError("not a PDF document")
    if doc.isClosed or doc.isEncrypted:
        raise ValueError("operation on closed or encrypted document")

    toclen = len(toc)
    # check toc validity ------------------------------------------------------
    if type(toc) is not list:
        raise ValueError("arg2 must be a list")
    if toclen == 0:
        return len(doc._delToC())
    pageCount = len(doc)
    t0 = toc[0]
    if type(t0) is not list:
        raise ValueError("arg2 must contain lists of 3 or 4 items")
    if t0[0] != 1:
        raise ValueError("hierarchy level of item 0 must be 1")
    for i in list(range(toclen-1)):
        t1 = toc[i]
        t2 = toc[i+1]
        if not -1 <= t1[2] <= pageCount:
            raise ValueError("row %s:page number out of range" % (str(i),))
        if (type(t2) is not list) or len(t2) < 3 or len(t2) > 4:
            raise ValueError("arg2 must contain lists of 3 or 4 items")
        if (type(t2[0]) is not int) or t2[0] < 1:
            raise ValueError("hierarchy levels must be int > 0")
        if t2[0] > t1[0] + 1:
            raise ValueError("row %s: hierarchy steps must not be > 1" + (str(i),))
    # no formal errors in toc --------------------------------------------------

    old_xrefs = doc._delToC()          # del old outlines, get xref numbers
    # prepare table of xrefs for new bookmarks
    xref = [0] + old_xrefs
    xref[0] = doc._getOLRootNumber()        # entry zero is outline root xref#
    if toclen > len(old_xrefs):             # too few old xrefs?
        for i in range((toclen - len(old_xrefs))):
            xref.append(doc._getNewXref())  # acquire new ones

    lvltab = {0:0}                     # to store last entry per hierarchy level

#==============================================================================
# contains new outline objects as strings - first one is outline root
#==============================================================================
    olitems = [{"count":0, "first":-1, "last":-1, "xref":xref[0]}]
#==============================================================================
# build olitems as a list of PDF-like connnected dictionaries
#==============================================================================
    for i in range(toclen):
        o = toc[i]
        lvl = o[0] # level
        title = PDFstr(o[1]) # titel
        pno = min(doc.pageCount - 1, max(0, o[2] - 1)) # page number
        top = 0
        if len(o) < 4:
            p = doc.loadPage(pno)
            top = int(round(p.bound().y1) - 36)  # default top location on page
            p = None                             # free page resources
        top1 = top + 0                        # accept provided top parameter
        dest_dict = {}
        if len(o) > 3:
            if type(o[3]) is int or type(o[3]) is float:
                top1 = int(round(o[3]))
                dest_dict = o[3]
            else:
                dest_dict = o[3] if type(o[3]) is dict else {}
                try:
                    top1 = int(round(o[3]["to"].y)) # top
                except: pass
        else:
            dest_dict = top
        if  0 <= top1 <= top + 36:
            top = top1
        d = {}
        d["first"] = -1
        d["count"] = 0
        d["last"]  = -1
        d["prev"]  = -1
        d["next"]  = -1
        d["dest"]  = getDestStr(doc._getPageObjNumber(pno), dest_dict)
        d["top"]   = top
        d["title"] = title
        d["parent"] = lvltab[lvl-1]
        d["xref"] = xref[i+1]
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

#==============================================================================
# now create each ol item as a string and insert it in the PDF
#==============================================================================
    for i, ol in enumerate(olitems):
        txt = "<<"
        if ol["count"] > 0:
            txt += "/Count " + str(ol["count"])
        try:
            txt += ol["dest"]
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
            txt += "/Title" + ol["title"]
        except: pass
        if i == 0:           # special: this is the outline root
            txt += "/Type/Outlines"
        txt += ">>"
        rc = doc._updateObject(xref[i], txt)     # insert the PDF object
        if rc != 0:
            raise ValueError("outline insert error:\n" + txt)

    doc.initData()
    return toclen

def do_links(doc1, doc2, from_page = -1, to_page = -1, start_at = -1):
    '''Insert links contained in copied page range into destination PDF.
    Parameter values **must** equal those of method insertPDF() - which must have been previously executed.'''
    #--------------------------------------------------------------------------
    # define skeletons for /Annots object texts
    #--------------------------------------------------------------------------
    annot_goto ='''<</Dest[%s 0 R /XYZ %s %s 0]/Rect[%s]/Subtype/Link>>'''

    annot_gotor = '''<</A<</D[%s /XYZ %s %s 0]/F<</F(%s)/UF(%s)/Type/Filespec
    >>/S/GoToR>>/Rect[%s]/Subtype/Link>>'''

    annot_launch = '''<</A<</F<</F(%s)/UF(%s)/Type/Filespec>>/S/Launch
    >>/Rect[%s]/Subtype/Link>>'''

    annot_uri = '''<</A<</S/URI/URI(%s)/Type/Action>>/Rect[%s]/Subtype/Link>>'''

    #--------------------------------------------------------------------------
    # internal function to create the actual "/Annots" object string
    #--------------------------------------------------------------------------
    def cre_annot(lnk, xref_dst, list_src, height):
        '''Create annotation object string for a passed-in link.'''

        # "from" rectangle is always there. Note: y-coords are from bottom!
        r = lnk["from"]
        rect = "%s %s %s %s" % (str(r.x0), str(height - r.y0),   # correct y0
                                str(r.x1), str(height - r.y1))   # correct y1
        if lnk["kind"] == fitz.LINK_GOTO:
            txt = annot_goto
            idx = list_src.index(lnk["page"])
            annot = txt % (str(xref_dst[idx]), str(lnk["to"].x),
                           str(lnk["to"].y), rect)
        elif lnk["kind"] == fitz.LINK_GOTOR:
            txt = annot_gotor
            annot = txt % (str(lnk["page"]), str(lnk["to"].x),
                           str(lnk["to"].y),
                           lnk["file"], lnk["file"],
                           rect)
        elif lnk["kind"] == fitz.LINK_LAUNCH:
            txt = annot_launch
            annot = txt % (lnk["file"], lnk["file"], rect)
        elif lnk["kind"] == fitz.LINK_URI:
            txt = annot_uri
            annot = txt % (lnk["uri"], rect)
        else:
            annot = ""

        return annot
    #--------------------------------------------------------------------------

    # validate & normalize parameters
    if from_page < 0:
        fp = 0
    elif from_page >= doc2.pageCount:
        from_page = doc2.page_count - 1
    else:
        fp = from_page

    if to_page < 0 or to_page >= doc2.pageCount:
        tp = doc2.pageCount - 1
    else:
        tp = to_page

    if start_at < 0:
        raise ValueError("do_links: 'start_at' arg must be >= 0")
    sa = start_at

    incr = 1 if fp <= tp else -1            # page range could be reversed
    # lists of source / destination page numbers
    list_src = list(range(fp, tp + incr, incr))
    list_dst = [sa + i for i in range(len(list_src))]
    # lists of source / destination page xref numbers
    xref_src = []
    xref_dst = []
    for i in range(len(list_src)):
        p_src = list_src[i]
        p_dst = list_dst[i]
        old_xref = doc2._getPageObjNumber(p_src)[0]
        new_xref = doc1._getPageObjNumber(p_dst)[0]
        xref_src.append(old_xref)
        xref_dst.append(new_xref)

    # create /Annots per copied page in destination PDF
    for i in range(len(xref_src)):
        page_src = doc2[list_src[i]]
        links = page_src.getLinks()
        if len(links) == 0:
            page_src = None
            continue
        height = page_src.bound().y1
        p_annots = ""
        page_dst = doc1[list_dst[i]]
        link_tab = []
        for l in links:
            if l["kind"] == fitz.LINK_GOTO and (l["page"] not in list_src):
                continue          # target not in copied pages
            annot_text = cre_annot(l, xref_dst, list_src, height)
            if not annot_text:
                raise ValueError("cannot create /Annot for kind: " + str(l["kind"]))
            link_tab.append(annot_text)
        if len(link_tab) > 0:
            page_dst._addAnnot_FromString(link_tab)
        page_dst = None
        page_src = None
    return

def getLinkText(page, lnk):
    #--------------------------------------------------------------------------
    # define skeletons for /Annots object texts
    #--------------------------------------------------------------------------
    annot_goto = "<</Dest[%s 0 R/XYZ %s %s 0]/Rect[%s]/Subtype/Link>>"

    annot_goto_n = "<</A<</D%s/S/GoTo>>/Rect[%s]/Subtype/Link>>"

    annot_gotor = '''<</A<</D[%s /XYZ %s %s 0]/F<</F(%s)/UF(%s)/Type/Filespec
    >>/S/GoToR>>/Rect[%s]/Subtype/Link>>'''

    annot_gotor_n = "<</A<</D%s/F(%s)/S/GoToR>>/Rect[%s]/Subtype/Link>>"

    annot_launch = '''<</A<</F<</F(%s)/UF(%s)/Type/Filespec>>/S/Launch
    >>/Rect[%s]/Subtype/Link>>'''

    annot_uri = "<</A<</S/URI/URI(%s)>>/Rect[%s]/Subtype/Link>>"

    annot_named = "<</A<</S/Named/N/%s/Type/Action>>/Rect[%s]/Subtype/Link>>"

    r = lnk["from"]
    height = page.rect.height
    rect = "%s %s %s %s" % (str(r.x0), str(height - r.y0),   # correct y0
                            str(r.x1), str(height - r.y1))   # correct y1

    annot = ""
    if lnk["kind"] == fitz.LINK_GOTO:
        if lnk["page"] >= 0:
            txt = annot_goto
            pno = lnk["page"]
            xref = page.parent._getPageXref(pno)[0]
            pnt = lnk.get("to", fitz.Point(0, 0))          # destination point
            annot = txt % (xref, str(pnt.x),
                           str(pnt.y), rect)
        else:
            txt = annot_goto_n
            annot = txt % (PDFstr(lnk["to"]), rect)
        
    elif lnk["kind"] == fitz.LINK_GOTOR:
        if lnk["page"] >= 0:
            txt = annot_gotor
            pnt = lnk.get("to", fitz.Point(0, 0))          # destination point
            if type(pnt) is not fitz.Point:
                pnt = fitz.Point(0, 0)
            annot = txt % (str(lnk["page"]), str(pnt.x), str(pnt.y),
                           lnk["file"], lnk["file"], rect)
        else:
            txt = annot_gotor_n
            annot = txt % (PDFstr(lnk["to"]), lnk["file"], rect)

    elif lnk["kind"] == fitz.LINK_LAUNCH:
        txt = annot_launch
        annot = txt % (lnk["file"], lnk["file"], rect)

    elif lnk["kind"] == fitz.LINK_URI:
        txt = annot_uri
        annot = txt % (lnk["uri"], rect)

    elif lnk["kind"] == fitz.LINK_NAMED:
        txt = annot_named
        annot = txt % (lnk["name"], rect)

    return annot    
    
def updateLink(page, lnk):
    """ Update a link on the current page. """
    annot = getLinkText(page, lnk)
    assert annot != "", "link kind not supported"
    page.parent._updateObject(lnk["xref"], annot, page = page) 
    return

def insertLink(page, lnk, mark = True):
    """ Insert a new link for the current page. """
    annot = getLinkText(page, lnk)
    assert annot != "", "link kind not supported"
    page._addAnnot_FromString([annot])
    return

def intersects(me, rect):
    """ Checks whether this rectangle and 'rect' have a rectangle with a positive area in common."""
    if type(rect) not in (fitz.Rect, fitz.IRect):
        return False
    if me.isEmpty or me.isInfinite or rect.isEmpty or rect.isInfinite:
        return False
    r = me & rect
    if r.isEmpty or r.isInfinite:
        return False
    return True

#-------------------------------------------------------------------------------
# Annot method
#-------------------------------------------------------------------------------
def updateImage(annot):
    '''Update border and color information in the appearance dictionary /AP.'''
    if annot.parent is None:
        raise RuntimeError("orphaned object: parent is None")
    if annot.parent.parent.isClosed:
        raise RuntimeError("illegal operation on closed document")
    
    def modAP(tab, ctab, ftab, wtab, dtab):
        '''replace all occurrences of colors, width and dashes by provided values.'''
        ntab = []
        in_text_block = False          # if True do nothing
        for i in range(len(tab)):
            if tab[i] == b"Do":        # another XObject invoked
                raise ValueError("nested XObject calls not supported")
            ntab.append(tab[i])        # store in output
            if tab[i] == b"BT":        # begin of text block
                in_text_block = True   # switch on
                continue
            if tab[i] == b"ET":        # end of text block
                in_text_block = False  # switch off
                continue
            if in_text_block:          # skip if in text block
                continue
            if ftab[4] and (tab[i] == b"s"):     # fill color provided
                ntab[-1] = b"b"        # make sure it is used
                continue
            if ctab[4]:                # stroke color provided
                if tab[i] == b"G":     # it is a gray
                    del ntab[-2:]
                    ntab.extend(ctab)
                    continue
                elif tab[i] == b"RG":  # it is RGB
                    del ntab[len(ntab)-4:]
                    ntab.extend(ctab)
                    continue
                elif tab[i] == b"K":   # it is CMYK
                    del ntab[len(ntab)-5:]
                    ntab.extend(ctab)
                    continue
            if ftab[4]:                # fill color provided
                if tab[i] == b"g":     # it is a gray
                    del ntab[-2:]
                    ntab.extend(ftab)
                    continue
                elif tab[i] == b"rg":  # it is RGB
                    del ntab[len(ntab)-4:]
                    ntab.extend(ftab)
                    continue
                elif tab[i] == b"k":   # it is CMYK
                    del ntab[len(ntab)-5:]
                    ntab.extend(ftab)
                    continue
            if wtab[1]:                # width value provided
                if tab[i] == b"w":
                    ntab[-2] = wtab[0]
                    continue
            if dtab[1]:                # dashes provided
                if tab[i] == b"d":
                    j = len(ntab) - 1
                    x = b"d"
                    while not x.startswith(b"["):     # search start of array
                        j -= 1
                        x = ntab[j]
                    del ntab[j:]
                    ntab.extend(dtab)
        return ntab
        
    ap = annot._getAP() # get appearance text
    aptab = ap.split() # decompose into a list
        
    # prepare width, colors and dashes lists
    # fill color
    c = annot.colors.get("fill")
    ftab = [b""]*5
    if c and len(c) > 0:
        l = len(c)
        if l == 4:
            ftab[4] = b"k"
            for i in range(4):
                ftab[i] = str(round(c[i],4)).encode("utf-8")
        elif l == 3:
            ftab[4] = b"rg"
            for i in range(1, 4):
                ftab[i] = str(round(c[i-1],4)).encode("utf-8")
        elif l == 1:
            ftab[4] = b"g"
            ftab[3] = str(round(c[0],4)).encode("utf-8")

    # stroke color
    c = annot.colors.get("common")
    ctab = [b""]*5
    if c and len(c) > 0:
        l = len(c)
        if l == 4:
            ctab[4] = b"K"
            for i in range(4):
                ctab[i] = str(round(c[i], 4)).encode("utf-8")
        elif l == 3:
            ctab[4] = b"RG"
            for i in range(1, 4):
                ctab[i] = str(round(c[i-1], 4)).encode("utf-8")
        elif l == 1:
            ctab[4] = b"G"
            ctab[3] = str(round(c[0], 4)).encode("utf-8")

    # border width
    c = annot.border.get("width")
    wtab = [b"", b""]
    if c:
        wtab[0] = str(round(c, 4)).encode("utf-8")
        wtab[1] = b"w"

    # dash pattern
    c = annot.border.get("dashes")
    dtab = [b""]*2
    if not c is None:
        dtab[1] = b"0 d"
        dtab[0] = b"["
        for n in c:
            if n > 0:
                dtab[0] += str(n).encode("utf-8") + b" "
        dtab[0] += b"]"

    outlist = []
    outlist += ftab if ftab[4] else []
    outlist += ctab if ctab[4] else []
    outlist += wtab if wtab[1] else []
    outlist += dtab if dtab[1] else []
    if not outlist:
        return
    # make sure we insert behind a leading "save graphics state"
    if aptab[0] == b"q":
        outlist = [b"q"] + outlist
        aptab = aptab[1:]
    # now change every color, width and dashes spec
    aptab = modAP(aptab, ctab, ftab, wtab, dtab)
    aptab = outlist + aptab
    ap = b" ".join(aptab)
    annot._setAP(ap)
    return

#-------------------------------------------------------------------------------
# "Now" timestamp in PDF Format
#-------------------------------------------------------------------------------
def getPDFnow():
    import time
    tz = "%s'%s'" % (str(time.timezone // 3600).rjust(2, "0"),
                 str((time.timezone // 60)%60).rjust(2, "0"))
    tstamp = time.strftime("D:%Y%m%d%H%M%S", time.localtime())
    if time.timezone > 0:
        tstamp += "-" + tz
    elif time.timezone < 0:
        tstamp = "+" + tz
    else:
        pass
    return tstamp
