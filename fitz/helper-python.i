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
    def __init__(self, obj):
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
        if obj.isExternal:
            self.page = -1
            self.kind = LINK_URI
        if not self.uri:
            self.page = -1
            self.kind = LINK_NONE
        if not obj.isExternal and self.uri:
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
                    self.kind = LINK_GOTOR
                    self.fileSpec = ftab[0]
                    if ftab[1].startswith("page="):
                        self.page = int(ftab[1][5:]) - 1    
                    else:
                        self.page = -1
                        self.dest = ftab[1]
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
# Returns a PDF string depending on its coding.
# If only ascii then "(original)" is returned,
# else if only 8 bit chars then "(original)" with interspersed octal strings
# \nnn is returned,
# else a string "<FEFF[hexstring]>" is returned, where [hexstring] is the
# UTF-16BE encoding of the original.
#-------------------------------------------------------------------------------
def getPDFstr(s, brackets = True):
    try:
        x = s.decode("utf-8")
    except:
        x = s
    if x is None:
        return "()" if brackets else ""
    if type(x) in (str, bytes) or sys.version_info[0] < 3 and type(x) in (str, unicode):
        pass
    else:
        raise ValueError("non-string passed to getPDFstr")

    utf16 = False
    # following returns ascii original string with mixed-in 
    # octal numbers \nnn if <= chr(255)
    r = ""
    for i in range(len(x)):
        if ord(x[i]) > 255:
            utf16 = True
            break
        if not brackets:
            r += x[i]
            continue
        if ord(x[i]) > 127:
            r += "\\" + oct(ord(x[i]))[-3:]
        else:
            r += x[i]

    if not utf16:
        return "(" + r + ")" if brackets else r

    # require full unicode: make a UTF-16BE hex string prefixed with "feff"
    r = hexlify(bytearray([254, 255]) + bytearray(x, "UTF-16BE"))
    t = r.decode("utf-8")                        # make str in Python 3
    return "<" + t + ">"                         # brackets indicate hex

'''
www.din-formate.de
www.din-formate.info/amerikanische-formate.html
www.directtools.de/wissen/normen/iso.htm
'''
paperSizes = {                     # known paper formats @ 72 dpi
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

%}