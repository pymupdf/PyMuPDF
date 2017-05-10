%pythoncode %{
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
def getPDFstr(s):
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

%}