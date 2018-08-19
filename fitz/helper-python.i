%pythoncode %{
#------------------------------------------------------------------------------
# link kinds and link flags
#------------------------------------------------------------------------------
LINK_NONE   = 0
LINK_GOTO   = 1
LINK_URI    = 2
LINK_LAUNCH = 3
LINK_NAMED  = 4
LINK_GOTOR  = 5
LINK_FLAG_L_VALID = 1
LINK_FLAG_T_VALID = 2
LINK_FLAG_R_VALID = 4
LINK_FLAG_B_VALID = 8
LINK_FLAG_FIT_H = 16
LINK_FLAG_FIT_V = 32
LINK_FLAG_R_IS_ZOOM = 64

#------------------------------------------------------------------------------
# Text handling flags
#------------------------------------------------------------------------------
TEXT_ALIGN_LEFT     = 0
TEXT_ALIGN_CENTER   = 1
TEXT_ALIGN_RIGHT    = 2
TEXT_ALIGN_JUSTIFY  = 3

TEXT_OUTPUT_TEXT    = 0
TEXT_OUTPUT_HTML    = 1
TEXT_OUTPUT_JSON    = 2
TEXT_OUTPUT_XML     = 3
TEXT_OUTPUT_XHTML   = 4

TEXT_PRESERVE_LIGATURES  = 1
TEXT_PRESERVE_WHITESPACE = 2
TEXT_PRESERVE_IMAGES     = 4

#------------------------------------------------------------------------------
# Base 14 font names
#------------------------------------------------------------------------------

Base14_fontnames = ("Courier", "Courier-Oblique", "Courier-Bold",
    "Courier-BoldOblique", "Helvetica", "Helvetica-Oblique",
    "Helvetica-Bold", "Helvetica-BoldOblique",
    "Times-Roman", "Times-Italic", "Times-Bold",
    "Times-BoldItalic", "Symbol", "ZapfDingbats")

#------------------------------------------------------------------------------
# Emulate old linkDest class
#------------------------------------------------------------------------------
class linkDest():
    '''link or outline destination details'''
    def __init__(self, obj, rlink):
        isExt = obj.isExternal
        isInt = not isExt
        self.dest = ""
        self.fileSpec = ""
        self.flags = 0
        self.isMap = False
        self.isUri = False
        self.kind = LINK_NONE
        self.lt = Point(0, 0)
        self.named = ""
        self.newWindow = ""
        self.page = obj.page
        self.rb = Point(0, 0)
        self.uri = obj.uri
        if rlink and not self.uri.startswith("#"):
            self.uri = "#%i,%g,%g" % (rlink[0]+1, rlink[1], rlink[2])
        if obj.isExternal:
            self.page = -1
            self.kind = LINK_URI
        if not self.uri:
            self.page = -1
            self.kind = LINK_NONE
        if isInt and self.uri:
            if self.uri.startswith("#"):
                self.named = ""
                self.kind = LINK_GOTO
                ftab = self.uri[1:].split(",")
                if len(ftab) == 3:
                    self.page = int(ftab[0]) - 1
                    self.lt = Point(float(ftab[1]), float(ftab[2]))
                    self.flags = self.flags | LINK_FLAG_L_VALID | LINK_FLAG_T_VALID
                else:
                    try:
                        self.page = int(ftab[0]) - 1
                    except:
                        self.kind = LINK_NAMED
                        self.named = self.uri[1:]
            else:
                self.kind = LINK_NAMED
                self.named = self.uri
        if obj.isExternal:
            if self.uri.startswith(("http://", "https://", "mailto:", "ftp://")):
                self.isUri = True
                self.kind = LINK_URI
            elif self.uri.startswith("file://"):
                self.fileSpec = self.uri[7:]
                self.isUri = False
                self.uri = ""
                self.kind = LINK_LAUNCH
                ftab = self.fileSpec.split("#")
                if len(ftab) == 2:
                    if ftab[1].startswith("page="):
                        self.kind = LINK_GOTOR
                        self.fileSpec = ftab[0]
                        self.page = int(ftab[1][5:]) - 1
            else:
                self.isUri = True
                self.kind = LINK_LAUNCH

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

#-------------------------------------------------------------------------------
# Return a PDF string depending on its coding.
# If only ascii then "(original)" is returned,
# else if only 8 bit chars then "(original)" with interspersed octal strings
# \nnn is returned,
# else a string "<FEFF[hexstring]>" is returned, where [hexstring] is the
# UTF-16BE encoding of the original.
#-------------------------------------------------------------------------------
def getPDFstr(x):
    if x is None or x == "":
        return "()"

    utf16 = max(ord(c) for c in x) > 255
    if utf16:
        # require full unicode: make a UTF-16BE hex string with BOM "feff"
        r = hexlify(bytearray([254, 255]) + bytearray(x, "UTF-16BE"))
        # r is 'bytes', so convert to 'str' if Python 3
        t = r if str is bytes else r.decode()
        return "<" + t + ">"                         # brackets indicate hex
    
    s = x.replace("\x00", " ")
    if str is bytes:
        if type(s) is str:
            s = unicode(s, "utf-8", "replace")

    # following returns ascii original string with mixed-in 
    # octal numbers \nnn if <= chr(255)
    r = ""
    for c in s:
        oc = ord(c)
        if oc > 127:
            r += "\\" + oct(oc)[-3:]
        else:
            if c in ("(", ")", "\\"):
                r += "\\"
            r += c

    return "(" + r + ")"

#------------------------------------------------------------------------------
# Return a PDF string suitable for the TJ operator enclosed in "[]" brackets.
# The input string is converted to either 2 or 4 hex digits per character.
# If no glyphs are supplied, then a simple font is assumed and each character
# taken directly.
# Otherwise a char's glyph is taken and 4 hex digits per char are put out.
#------------------------------------------------------------------------------
def getTJstr(text, glyphs):
    if text.startswith("[<") and text.endswith(">]"): # already done
        return text
    if not bool(text):
        return "[<>]"
    if glyphs is None:            # this is a simple font
        otxt = "".join([hex(ord(c))[2:].rjust(2, "0") if ord(c)<256 else "3f" for c in text])
        return "[<" + otxt + ">]"
    # this is not a simple font -> take the glyphs of a character
    otxt = "".join([hex(glyphs[ord(c)][0])[2:].rjust(4, "0") for c in text])
    return "[<" + otxt + ">]"

'''
Information taken from the following web sites:
www.din-formate.de
www.din-formate.info/amerikanische-formate.html
www.directtools.de/wissen/normen/iso.htm
'''
paperSizes = { # known paper formats @ 72 dpi
        'a0': (2384, 3370),
        'a1': (1684, 2384),
        'a10': (74, 105),
        'a2': (1191, 1684),
        'a3': (842, 1191),
        'a4': (595, 842),
        'a5': (420, 595),
        'a6': (298, 420),
        'a7': (210, 298),
        'a8': (147, 210),
        'a9': (105, 147),
        'b0': (2835, 4008),
        'b1': (2004, 2835),
        'b10': (88, 125),
        'b2': (1417, 2004),
        'b3': (1001, 1417),
        'b4': (709, 1001),
        'b5': (499, 709),
        'b6': (354, 499),
        'b7': (249, 354),
        'b8': (176, 249),
        'b9': (125, 176),
        'c0': (2599, 3677),
        'c1': (1837, 2599),
        'c10': (79, 113),
        'c2': (1298, 1837),
        'c3': (918, 1298),
        'c4': (649, 918),
        'c5': (459, 649),
        'c6': (323, 459),
        'c7': (230, 323),
        'c8': (162, 230),
        'c9': (113, 162),
        'card-4x6': (288, 432),
        'card-5x7': (360, 504),
        'commercial': (297, 684),
        'executive': (522, 756),
        'invoice': (396, 612),
        'ledger': (792, 1224),
        'legal': (612, 1008),
        'legal-13': (612, 936),
        'letter': (612, 792),
        'monarch': (279, 540),
        'tabloid-extra': (864, 1296),
        }
def PaperSize(s):
    """Return a tuple (width, height) for a given paper format string. 'A4-L' will
    return (842, 595), the values for A4 landscape. Suffix '-P' and no suffix
    returns portrait."""
    size = s.lower()
    f = "p"
    if size.endswith("-l"):
        f = "l"
        size = size[:-2]
    if size.endswith("-p"):
        size = size[:-2]
    rc = paperSizes.get(size, (-1, -1))
    if f == "p":
        return rc
    return (rc[1], rc[0])

def PaperRect(s):
    """Return a fitz.Rect for the paper size indicated in string 's'. Must conform to the argument of method 'PaperSize', which will be invoked.
    """
    width, height = PaperSize(s)
    return Rect(0.0, 0.0, width, height)

def CheckParent(o):
    if not hasattr(o, "parent") or o.parent is None:
        raise ValueError("orphaned object: parent is None") 

def CheckColor(c):
    if c is not None:
        if type(c) not in (list, tuple) or len(c) != 3 or \
            min(c) < 0 or max(c) > 1:
            raise ValueError("need 3 color components in range 0 to 1")

def CheckMorph(o):
    if not bool(o): return False
    if not (type(o) in (list, tuple) and len(o) == 2):
        raise ValueError("morph must be a sequence of length 2")
    if not (type(o[0]) == Point and issubclass(type(o[1]), Matrix)):
        raise ValueError("invalid morph parameter")
    if not o[1].e == o[1].f == 0:
        raise ValueError("invalid morph parameter")
    return True
    
def CheckFont(page, fontname):
    """Return an entry in the page's font list if reference name matches.
    """
    fl = page.getFontList()
    refname = None
    for f in fl:
        if f[4] == fontname:
            refname = f
            break
    return refname

def CheckFontInfo(doc, xref):
    """Return a font info if present in the document.
    """
    fi = None
    for f in doc.FontInfos:
        if xref == f[0]:
            fi = f
            break
    return fi

def UpdateFontInfo(doc, info):
    xref = info[0]
    found = False
    for i, fi in enumerate(doc.FontInfos):
        if fi[0] == xref:
            found = True
            break
    if found:
        doc.FontInfos[i] = info
    else:
        doc.FontInfos.append(info)

def DUMMY(*args, **kw):
    return
    
def ConversionHeader(i, filename = "unknown"):
    t = i.lower()
    html = """<!DOCTYPE html>
<html>
<head>
<style>
body{background-color:gray}
div{position:relative;background-color:white;margin:1em auto}
p{position:absolute;margin:0}
img{position:absolute}
</style>
</head>
<body>\n"""
    
    xml = """<?xml version="1.0"?>
<document name="%s">\n""" % filename

    xhtml = """<?xml version="1.0"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<style>
body{background-color:gray}
div{background-color:white;margin:1em;padding:1em}
p{white-space:pre-wrap}
</style>
</head>
<body>\n"""

    text = ""
    json = '{"document": "%s", "pages": [\n' % filename
    if t == "html":
        r = html
    elif t == "json":
        r = json
    elif t == "xml":
        r = xml
    elif t == "xhtml":
        r = xhtml
    else:
        r = text
    
    return r

def ConversionTrailer(i):
    t = i.lower()
    text = ""
    json = "]\n}"
    html = "</body>\n</html>\n"
    xml = "</document>\n"
    xhtml = html
    if t == "html":
        r = html
    elif t == "json":
        r = json
    elif t == "xml":
        r = xml
    elif t == "xhtml":
        r = xhtml
    else:
        r = text
    
    return r

def _make_line_AP(annot, nv = None, r0 = None):
    """ Create the /AP stream for 'Line', 'PolyLine' and 'Polygon' annotations.
    """
    w = annot.border["width"]          # get line width
    sc = annot.colors["stroke"]        # get stroke color
    fc = annot.colors["fill"]          # get fill color
    ca = annot.opacity                 # get opacity value
    Alp0 = "/Alp0 gs\n" if ca >= 0 else ""
    vert = nv if nv else annot.vertices # get list of points
    rn = r0 if r0 else annot.rect
    h = rn.height                      # annot rectangle height
    r = Rect(0, 0, rn.width, h)        # this is the /BBox of the /AP
    x0 = rn.x0                         # annot rect origin x
    y0 = rn.y0                         # annot rect origin y
    scol = "%g %g %g RG\n" % (sc[0], sc[1], sc[2]) if sc else "0 0 0 RG\n"
    fcol = "%g %g %g rg\n" % (fc[0], fc[1], fc[2]) if fc else ""

    dt = annot.border.get("dashes")
    dtab = []
    if dt:
        dtab = ["[", "]0 d\n"]
        for n in dt:
            dtab[0] += "%i " % n
    dtab = "".join(dtab)

    # start /AP string with a goto command
    ap = "q\n%s%g %g m\n" % (Alp0, vert[0][0] - x0, h - (vert[0][1] - y0))

    # add line commands for all subsequent points
    for v in vert[1:]:
        ap += "%g %g l\n" % (v[0] - x0, h - (v[1] - y0))

    # add color triples and other stuff commands
    ap += scol + fcol + dtab + "%g w 1 J 1 j\n" % w

    # add stroke / fill & stroke command depending on type
    if fcol and annot.type[0] == ANNOT_POLYGON:
        ap += "b"
    else:
        ap += "S"
    ap += "\nQ\n"

    le_left = annot.lineEnds[0]
    le_right = annot.lineEnds[1]
    if max(le_left, le_right) < 1:          # leave if there is no line end
        return ap

    _le_func = (None, _le_square, _le_circle, _le_diamond, _le_openarrow,
                _le_closedarrow, _le_butt, _le_ropenarrow,
                _le_rclosedarrow, _le_slash)
    
    if le_left:
        ap += _le_func[le_left](annot, Point(vert[0]), Point(vert[1]), False)

    if le_right:
        ap += _le_func[le_right](annot, Point(vert[-2]), Point(vert[-1]), True)
    return ap

def _hor_matrix(C, P):
    S = P - C                               # vector 'C' -> 'P'
    try:
        alfa = math.asin(abs(S.y) / abs(S)) # absolute angle from horizontal
    except ZeroDivisionError:
        print("points are too close:")
        return Matrix()
    if S.x < 0:                             # make arcsin result unique
        if S.y <= 0:                        # bottom-left
            alfa = -(math.pi - alfa)
        else:                               # top-left
            alfa = math.pi - alfa
    else:
        if S.y >= 0:                        # top-right
            pass
        else:                               # bottom-right
            alfa = - alfa
    ca = math.cos(alfa)
    sa = math.sin(alfa)
    m = Matrix(ca, -sa, sa, ca, -C.x, -C.y)
    return m

def _make_rect_AP(annot):
    """ Create /AP stream for rectangle annotation.
    """
    w = annot.border["width"]          # get line width
    sc = annot.colors["stroke"]        # get stroke color
    fc = annot.colors["fill"]          # get fill color
    ca = annot.opacity                 # get opacity value
    Alp0 = "/Alp0 gs\n" if ca >= 0 else ""
    scol = "%g %g %g RG " % (sc[0], sc[1], sc[2]) if sc else "0 0 0 RG "
    fcol = "%g %g %g rg " % (fc[0], fc[1], fc[2]) if fc else ""
    dt = annot.border.get("dashes")
    dtab = []
    if dt:
        dtab = ["[", "]0 d"]
        for n in dt:
            dtab[0] += "%i " % n
    dtab = "".join(dtab)
    r = annot.rect                     # annot rectangle
    r1 = r2 = w/2.                     # rect starts bottom-left here
    r3 = r.width - w                   # rect width reduced by line width
    r4 = r.height - w                  # rect height reduced by line with
    ap = "q\n%s%g %g %g %g re %g w 1 J 1 j\n" % (Alp0, r1, r2, r3, r4, w)
    ap += scol + fcol + dtab
    if fcol:
        ap += "\nb\nQ\n"
    else:
        ap += "\ns\nQ\n"
    return ap

def _le_annot_parms(annot, p1, p2):
    w = annot.border["width"]
    sc = annot.colors["stroke"]
    scol = "%g %g %g RG\n" % (sc[0], sc[1], sc[2]) if sc else "0 0 0 RG\n"
    fc = annot.colors["fill"]
    fcol = "%g %g %g rg\n" % (fc[0], fc[1], fc[2]) if fc else "1 1 1 rg\n"
    delta = Point(annot.rect.x0, annot.rect.y0)
    nr = annot.rect - Rect(delta, delta)
    h = nr.height
    np1 = p1 - delta         # point coord relative to annot rect
    np2 = p2 - delta         # point coord relative to annot rect
    m = _hor_matrix(np1, np2)   # matrix makes the line horizontal
    if m == Matrix():
        print(tuple(p1), tuple(p2))
    im = ~m                  # inverted matrix
    L = np1 * m              # converted start (left) point
    R = np2 * m              # converted end (right) point
    return m, im, L, R, w, h, scol, fcol

def _make_circle_AP(annot):
    sc = annot.colors["stroke"]
    scol = "%g %g %g RG " % (sc[0], sc[1], sc[2]) if sc else "0 0 0 RG "
    fc = annot.colors["fill"]
    ca = annot.opacity                 # get opacity value
    Alp0 = "/Alp0 gs\n" if ca >= 0 else ""
    fcol = "%g %g %g rg " % (fc[0], fc[1], fc[2]) if fc else ""
    dt = annot.border.get("dashes")
    dtab = []
    if dt:
        dtab = ["[", "]0 d\n"]
        for n in dt:
            dtab[0] += "%i " % n
    dtab = "".join(dtab)
    lw = annot.border["width"]
    lw2 = lw / 2.
    h = annot.rect.height
    r = Rect(lw2, lw2, annot.rect.width - lw2, h - lw2)

    ap = "q\n" + Alp0 + _oval_string(h, r.tl, r.tr, r.br, r.bl)
    ap += "%g w 1 J 1 j\n" % lw
    ap += scol + fcol + dtab
    if fcol:
        ap += "\nb\nQ\n"
    else:
        ap += "\ns\nQ\n"
    return ap

def _oval_string(h, p1, p2, p3, p4):
    """Return string defining an oval within a 4-polygon
    """
    def bezier(p, q, r):
        f = "%g %g %g %g %g %g c\n"
        return f % (p.x, h - p.y, q.x, h - q.y, r.x, h - r.y)

    kappa = 0.55228474983
    ml = p1 + (p4 - p1) * 0.5    # Mitte links
    mo = p1 + (p2 - p1) * 0.5    # Mitte oben
    mr = p2 + (p3 - p2) * 0.5    # Mitte rechts
    mu = p4 + (p3 - p4) * 0.5    # Mitte unten
    ol1 = ml + (p1 - ml) * kappa
    ol2 = mo + (p1 - mo) * kappa
    or1 = mo + (p2 - mo) * kappa
    or2 = mr + (p2 - mr) * kappa
    ur1 = mr + (p3 - mr) * kappa
    ur2 = mu + (p3 - mu) * kappa
    ul1 = mu + (p4 - mu) * kappa
    ul2 = ml + (p4 - ml) * kappa

    ap = "%g %g m\n" % (ml.x, h - ml.y)
    ap += bezier(ol1, ol2, mo)
    ap += bezier(or1, or2, mr)
    ap += bezier(ur1, ur2, mu)
    ap += bezier(ul1, ul2, ml)
    return ap

def _le_diamond(annot, p1, p2, lr):
    m, im, L, R, w, h, scol, fcol = _le_annot_parms(annot, p1, p2)
    shift = 1.75             # 2*shift*width = length of square edge
    d = w * shift
    M = R - (w, 0) if lr else L + (w, 0)
    r = Rect(M, M) + (-d, -d, d, d)         # the square
    # the square makes line longer by (2*shift - 1)*width
    p = (r.tl + (r.bl - r.tl) * 0.5) * im
    ap = "q\n%g %g m\n" % (p.x, h - p.y)
    p = (r.tl + (r.tr - r.tl) * 0.5) * im
    ap += "%g %g l\n"   % (p.x, h - p.y)
    p = (r.tr + (r.br - r.tr) * 0.5) * im
    ap += "%g %g l\n"   % (p.x, h - p.y)
    p = (r.br + (r.bl - r.br) * 0.5) * im
    ap += "%g %g l\n"   % (p.x, h - p.y)
    ap += "%g w\n" % w
    ap += scol + fcol + "b\nQ\n"
    return ap

def _le_square(annot, p1, p2, lr):
    m, im, L, R, w, h, scol, fcol = _le_annot_parms(annot, p1, p2)
    shift = 1.25             # 2*shift*width = length of square edge
    d = w * shift
    M = R - (w, 0) if lr else L + (w, 0)
    r = Rect(M, M) + (-d, -d, d, d)         # the square
    # the square makes line longer by (2*shift - 1)*width
    p = r.tl * im
    ap = "q\n%g %g m\n" % (p.x, h - p.y)
    p = r.tr * im
    ap += "%g %g l\n"   % (p.x, h - p.y)
    p = r.br * im
    ap += "%g %g l\n"   % (p.x, h - p.y)
    p = r.bl * im
    ap += "%g %g l\n"   % (p.x, h - p.y)
    ap += "%g w\n" % w
    ap += scol + fcol + "b\nQ\n"
    return ap

def _le_circle(annot, p1, p2, lr):
    m, im, L, R, w, h, scol, fcol = _le_annot_parms(annot, p1, p2)
    shift = 1.50             # 2*shift*width = length of square edge
    d = w * shift
    M = R - (w, 0) if lr else L + (w, 0)
    r = Rect(M, M) + (-d, -d, d, d)         # the square
    ap = "q\n" + _oval_string(h, r.tl * im, r.tr * im, r.br * im, r.bl * im)
    ap += "%g w\n" % w
    ap += scol + fcol + "b\nQ\n"
    return ap
    
def _le_butt(annot, p1, p2, lr):
    m, im, L, R, w, h, scol, fcol = _le_annot_parms(annot, p1, p2)
    M = R if lr else L
    top = (M + (0, -2 * w)) * im
    bot = (M + (0, 2 * w)) * im
    ap = "\nq\n%g %g m\n" % (top.x, h - top.y)
    ap += "%g %g l\n" % (bot.x, h - bot.y)
    ap += "%g w\n" % w
    ap += scol + "s\nQ\n"
    return ap
    
def _le_slash(annot, p1, p2, lr):
    m, im, L, R, w, h, scol, fcol = _le_annot_parms(annot, p1, p2)
    rw = 1.1547 * w * 0.5         # makes rect diagonal a 30 deg inclination
    M = R if lr else L
    r = Rect(M.x - rw, M.y - 2 * w, M.x + rw, M.y + 2 * w)
    top = r.tl * im
    bot = r.br * im
    ap = "\nq\n%g %g m\n" % (top.x, h - top.y)
    ap += "%g %g l\n" % (bot.x, h - bot.y)
    ap += "%g w\n" % w
    ap += scol + "s\nQ\n"
    return ap

def _le_openarrow(annot, p1, p2, lr):
    m, im, L, R, w, h, scol, fcol = _le_annot_parms(annot, p1, p2)
    p2 = R + (1.5 * w, 0) if lr else L - (1.5 * w, 0)
    p1 = p2 + (-3 * w, -1.5 * w) if lr else p2 + (3 * w, -1.5 * w)
    p3 = p2 + (-3 * w, 1.5 * w) if lr else p2 + (3 * w, 1.5 * w)
    p1 *= im
    p2 *= im
    p3 *= im
    ap = "\nq\n%g %g m\n" % (p1.x, h - p1.y)
    ap += "%g %g l\n" % (p2.x, h - p2.y)
    ap += "%g %g l\n" % (p3.x, h - p3.y)
    ap += "%g w\n" % w
    ap += scol + "S\nQ\n"
    return ap
    
def _le_closedarrow(annot, p1, p2, lr):
    m, im, L, R, w, h, scol, fcol = _le_annot_parms(annot, p1, p2)
    p2 = R + (1.5 * w, 0) if lr else L - (1.5 * w, 0)
    p1 = p2 + (-3 * w, -1.5 * w) if lr else p2 + (3 * w, -1.5 * w)
    p3 = p2 + (-3 * w, 1.5 * w) if lr else p2 + (3 * w, 1.5 * w)
    p1 *= im
    p2 *= im
    p3 *= im
    ap = "\nq\n%g %g m\n" % (p1.x, h - p1.y)
    ap += "%g %g l\n" % (p2.x, h - p2.y)
    ap += "%g %g l\n" % (p3.x, h - p3.y)
    ap += "%g w\n" % w
    ap += scol + fcol + "b\nQ\n"
    return ap
    
def _le_ropenarrow(annot, p1, p2, lr):
    m, im, L, R, w, h, scol, fcol = _le_annot_parms(annot, p1, p2)
    p2 = R - (0.5 * w, 0) if lr else L + (0.5 * w, 0)
    p1 = p2 + (3 * w, -1.5 * w) if lr else p2 + (-3 * w, -1.5 * w)
    p3 = p2 + (3 * w, 1.5 * w) if lr else p2 + (-3 * w, 1.5 * w)
    p1 *= im
    p2 *= im
    p3 *= im
    ap = "\nq\n%g %g m\n" % (p1.x, h - p1.y)
    ap += "%g %g l\n" % (p2.x, h - p2.y)
    ap += "%g %g l\n" % (p3.x, h - p3.y)
    ap += "%g w\n" % w
    ap += scol + fcol + "S\nQ\n"
    return ap
    
def _le_rclosedarrow(annot, p1, p2, lr):
    m, im, L, R, w, h, scol, fcol = _le_annot_parms(annot, p1, p2)
    p2 = R - (3.0 * w, 0) if lr else L + (3.0 * w, 0)
    p1 = p2 + (3 * w, -1.5 * w) if lr else p2 + (-3 * w, -1.5 * w)
    p3 = p2 + (3 * w, 1.5 * w) if lr else p2 + (-3 * w, 1.5 * w)
    p1 *= im
    p2 *= im
    p3 *= im
    ap = "\nq\n%g %g m\n" % (p1.x, h - p1.y)
    ap += "%g %g l\n" % (p2.x, h - p2.y)
    ap += "%g %g l\n" % (p3.x, h - p3.y)
    ap += "%g w\n" % w
    ap += scol + fcol + "b\nQ\n"
    return ap

def _upd_my_AP(annot):
    if annot.type[0] not in range(2, 8):
        return
    r = Rect(0, 0, annot.rect.width, annot.rect.height)

    if annot.type[0] == ANNOT_CIRCLE:
        ap = _make_circle_AP(annot)
        annot._checkAP(r, ap)
        return

    if annot.type[0] == ANNOT_SQUARE:
        ap = _make_rect_AP(annot)
        annot._checkAP(r, ap)
        return

    ov = annot.vertices
    rect = Rect(Point(ov[0]), Point(ov[0]))
    for v in ov[1:]:
        rect |= v
    w = 3 * annot.border["width"]
    rect += (-w, -w, w, w)
    annot._setRect(rect)
    r = Rect(0, 0, rect.width, rect.height)
    ap = _make_line_AP(annot)
    annot._checkAP(r, ap)
    return
%}