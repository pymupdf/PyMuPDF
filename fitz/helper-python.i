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
TEXT_INHIBIT_SPACES      = 8

#------------------------------------------------------------------------------
# Simple text encoding options
#------------------------------------------------------------------------------
TEXT_ENCODING_LATIN    = 0
TEXT_ENCODING_GREEK    = 1
TEXT_ENCODING_CYRILLIC = 2
#------------------------------------------------------------------------------
# Stamp annotation icon numbers
#------------------------------------------------------------------------------
STAMP_Approved            = 0
STAMP_AsIs                = 1
STAMP_Confidential        = 2
STAMP_Departmental        = 3
STAMP_Experimental        = 4
STAMP_Expired             = 5
STAMP_Final               = 6
STAMP_ForComment          = 7
STAMP_ForPublicRelease    = 8
STAMP_NotApproved         = 9
STAMP_NotForPublicRelease = 10
STAMP_Sold                = 11
STAMP_TopSecret           = 12
STAMP_Draft               = 13

#------------------------------------------------------------------------------
# Base 14 font names and dictionary
#------------------------------------------------------------------------------
Base14_fontnames = ("Courier", "Courier-Oblique", "Courier-Bold",
    "Courier-BoldOblique", "Helvetica", "Helvetica-Oblique",
    "Helvetica-Bold", "Helvetica-BoldOblique",
    "Times-Roman", "Times-Italic", "Times-Bold",
    "Times-BoldItalic", "Symbol", "ZapfDingbats")

Base14_fontdict = {}
for f in Base14_fontnames:
    Base14_fontdict[f.lower()] = f
Base14_fontdict["helv"] = "Helvetica"
Base14_fontdict["heit"] = "Helvetica-Oblique"
Base14_fontdict["hebo"] = "Helvetica-Bold"
Base14_fontdict["hebi"] = "Helvetica-BoldOblique"
Base14_fontdict["cour"] = "Courier"
Base14_fontdict["coit"] = "Courier-Oblique"
Base14_fontdict["cobo"] = "Courier-Bold"
Base14_fontdict["cobi"] = "Courier-BoldOblique"
Base14_fontdict["tiro"] = "Times-Roman"
Base14_fontdict["tibo"] = "Times-Bold"
Base14_fontdict["tiit"] = "Times-Italic"
Base14_fontdict["tibi"] = "Times-BoldItalic"
Base14_fontdict["symb"] = "Symbol"
Base14_fontdict["zadb"] = "ZapfDingbats"

annot_skel = {
    "goto1": "<</A<</S/GoTo/D[%i 0 R/XYZ %g %g 0]>>/Rect[%s]/BS<</W 0>>/Subtype/Link>>",
    "goto2": "<</A<</S/GoTo/D%s>>/Rect[%s]/BS<</W 0>>/Subtype/Link>>",
    "gotor1": "<</A<</S/GoToR/D[%i /XYZ %g %g 0]/F<</F(%s)/UF(%s)/Type/Filespec>>>>/Rect[%s]/BS<</W 0>>/Subtype/Link>>",
    "gotor2": "<</A<</S/GoToR/D%s/F(%s)>>/Rect[%s]/BS<</W 0>>/Subtype/Link>>",
    "launch": "<</A<</S/Launch/F<</F(%s)/UF(%s)/Type/Filespec>>>>/Rect[%s]/BS<</W 0>>/Subtype/Link>>",
    "uri": "<</A<</S/URI/URI(%s)>>/Rect[%s]/BS<</W 0>>/Subtype/Link>>",
    "named": "<</A<</S/Named/N/%s/Type/Action>>/Rect[%s]/BS<</W 0>>/Subtype/Link>>",
}

def _toc_remove_page(toc, first, last):
    """ Remove all ToC entries pointing to certain pages.

    Args:
        toc: old table of contents generated with getToC(False).
        first: (int) number of first page to remove.
        last: (int) number of last page to remove.
    Returns:
        Modified table of contents, which should be used by PDF
        document method setToC.
    """
    toc2 = []  # intermediate new toc
    count = last - first + 1  # number of pages to remove
    # step 1: remove numbers from toc
    for t in toc:
        if first <= t[2] <= last:  # skip entries between first and last
            continue
        if t[2] < first:  # keep smaller page numbers
            toc2.append(t)
            continue
        # larger page numbers
        t[2] -= count  # decrease page number
        d = t[3]
        if d["kind"] == LINK_GOTO:
            d["page"] -= count
            t[3] = d
        toc2.append(t)

    toc3 = []  # final new toc
    old_lvl = 0

    # step 2: deal with hierarchy lvl gaps > 1
    for t in toc2:
        while t[0] - old_lvl > 1:  # lvl gap too large
            old_lvl += 1  # increase previous lvl
            toc3.append([old_lvl] + t[1:])  # insert a filler item
        old_lvl = t[0]
        toc3.append(t)

    return toc3


def getTextlength(text, fontname="helv", fontsize=11, encoding=0):
    """Calculate length of a string for a given built-in font.

    Args:
        fontname: name of the font.
        fontsize: size of font in points.
        encoding: encoding to use (0=Latin, 1=Greek, 2=Cyrillic).
    Returns:
        (float) length of text.
    """
    fontname = fontname.lower()
    basename = Base14_fontdict.get(fontname, None)

    glyphs = None
    if basename == "Symbol":
        glyphs = symbol_glyphs
    if basename == "ZapfDingbats":
        glyphs = zapf_glyphs
    if glyphs is not None:
        w = sum([glyphs[ord(c)][1] if ord(c) < 256 else glyphs[183][1] for c in text])
        return w * fontsize

    if fontname in Base14_fontdict.keys():
        return TOOLS.measure_string(text, Base14_fontdict[fontname], fontsize, encoding)

    if fontname in ("china-t", "china-s",
                    "china-ts", "china-ss",
                    "japan", "japan-s",
                    "korea", "korea-s"):
        return len(text) * fontsize

    raise ValueError("Font '%s' is unsupported" % fontname)


#------------------------------------------------------------------------------
# Glyph list for the built-in font 'ZapfDingbats'
#------------------------------------------------------------------------------
zapf_glyphs = (
 (183, 0.788), (183, 0.788), (183, 0.788), (183, 0.788), (183, 0.788), (183, 0.788),
 (183, 0.788), (183, 0.788), (183, 0.788), (183, 0.788), (183, 0.788), (183, 0.788),
 (183, 0.788), (183, 0.788), (183, 0.788), (183, 0.788), (183, 0.788), (183, 0.788),
 (183, 0.788), (183, 0.788), (183, 0.788), (183, 0.788), (183, 0.788), (183, 0.788),
 (183, 0.788), (183, 0.788), (183, 0.788), (183, 0.788), (183, 0.788), (183, 0.788),
 (183, 0.788), (183, 0.788), (32, 0.278), (33, 0.974), (34, 0.961), (35, 0.974),
 (36, 0.98), (37, 0.719), (38, 0.789), (39, 0.79), (40, 0.791), (41, 0.69),
 (42, 0.96), (43, 0.939), (44, 0.549), (45, 0.855), (46, 0.911), (47, 0.933),
 (48, 0.911), (49, 0.945), (50, 0.974), (51, 0.755), (52, 0.846), (53, 0.762),
 (54, 0.761), (55, 0.571), (56, 0.677), (57, 0.763), (58, 0.76), (59, 0.759),
 (60, 0.754), (61, 0.494), (62, 0.552), (63, 0.537), (64, 0.577), (65, 0.692),
 (66, 0.786), (67, 0.788), (68, 0.788), (69, 0.79), (70, 0.793), (71, 0.794),
 (72, 0.816), (73, 0.823), (74, 0.789), (75, 0.841), (76, 0.823), (77, 0.833),
 (78, 0.816), (79, 0.831), (80, 0.923), (81, 0.744), (82, 0.723), (83, 0.749),
 (84, 0.79), (85, 0.792), (86, 0.695), (87, 0.776), (88, 0.768), (89, 0.792),
 (90, 0.759), (91, 0.707), (92, 0.708), (93, 0.682), (94, 0.701), (95, 0.826),
 (96, 0.815), (97, 0.789), (98, 0.789), (99, 0.707), (100, 0.687), (101, 0.696),
 (102, 0.689), (103, 0.786), (104, 0.787), (105, 0.713), (106, 0.791),
 (107, 0.785), (108, 0.791), (109, 0.873), (110, 0.761), (111, 0.762),
 (112, 0.762), (113, 0.759), (114, 0.759), (115, 0.892), (116, 0.892),
 (117, 0.788), (118, 0.784), (119, 0.438), (120, 0.138), (121, 0.277),
 (122, 0.415), (123, 0.392), (124, 0.392), (125, 0.668), (126, 0.668),
 (183, 0.788), (183, 0.788), (183, 0.788), (183, 0.788), (183, 0.788), (183, 0.788),
 (183, 0.788), (183, 0.788), (183, 0.788), (183, 0.788), (183, 0.788), (183, 0.788),
 (183, 0.788), (183, 0.788), (183, 0.788), (183, 0.788), (183, 0.788), (183, 0.788),
 (183, 0.788), (183, 0.788), (183, 0.788), (183, 0.788), (183, 0.788), (183, 0.788),
 (183, 0.788), (183, 0.788), (183, 0.788), (183, 0.788), (183, 0.788), (183, 0.788),
 (183, 0.788), (183, 0.788), (183, 0.788), (183, 0.788), (161, 0.732), (162, 0.544),
 (163, 0.544), (164, 0.91), (165, 0.667), (166, 0.76), (167, 0.76),
 (168, 0.776), (169, 0.595), (170, 0.694), (171, 0.626), (172, 0.788),
 (173, 0.788), (174, 0.788), (175, 0.788), (176, 0.788), (177, 0.788),
 (178, 0.788), (179, 0.788), (180, 0.788), (181, 0.788), (182, 0.788),
 (183, 0.788), (184, 0.788), (185, 0.788), (186, 0.788), (187, 0.788),
 (188, 0.788), (189, 0.788), (190, 0.788), (191, 0.788), (192, 0.788),
 (193, 0.788), (194, 0.788), (195, 0.788), (196, 0.788), (197, 0.788),
 (198, 0.788), (199, 0.788), (200, 0.788), (201, 0.788), (202, 0.788),
 (203, 0.788), (204, 0.788), (205, 0.788), (206, 0.788), (207, 0.788),
 (208, 0.788), (209, 0.788), (210, 0.788), (211, 0.788), (212, 0.894),
 (213, 0.838), (214, 1.016), (215, 0.458), (216, 0.748), (217, 0.924),
 (218, 0.748), (219, 0.918), (220, 0.927), (221, 0.928), (222, 0.928),
 (223, 0.834), (224, 0.873), (225, 0.828), (226, 0.924), (227, 0.924),
 (228, 0.917), (229, 0.93), (230, 0.931), (231, 0.463), (232, 0.883),
 (233, 0.836), (234, 0.836), (235, 0.867), (236, 0.867), (237, 0.696),
 (238, 0.696), (239, 0.874), (183, 0.788), (241, 0.874), (242, 0.76),
 (243, 0.946), (244, 0.771), (245, 0.865), (246, 0.771), (247, 0.888),
 (248, 0.967), (249, 0.888), (250, 0.831), (251, 0.873), (252, 0.927),
 (253, 0.97), (183, 0.788), (183, 0.788)
 )

#------------------------------------------------------------------------------
# Glyph list for the built-in font 'Symbol'
#------------------------------------------------------------------------------
symbol_glyphs = (
 (183, 0.46), (183, 0.46), (183, 0.46), (183, 0.46), (183, 0.46),
 (183, 0.46), (183, 0.46), (183, 0.46), (183, 0.46), (183, 0.46),
 (183, 0.46), (183, 0.46), (183, 0.46), (183, 0.46), (183, 0.46),
 (183, 0.46), (183, 0.46), (183, 0.46), (183, 0.46), (183, 0.46),
 (183, 0.46), (183, 0.46), (183, 0.46), (183, 0.46), (183, 0.46),
 (183, 0.46), (183, 0.46), (183, 0.46), (183, 0.46), (183, 0.46),
 (183, 0.46), (183, 0.46), (32, 0.25), (33, 0.333), (34, 0.713),
 (35, 0.5), (36, 0.549), (37, 0.833), (38, 0.778), (39, 0.439),
 (40, 0.333), (41, 0.333), (42, 0.5), (43, 0.549), (44, 0.25), (45, 0.549),
 (46, 0.25), (47, 0.278), (48, 0.5), (49, 0.5), (50, 0.5), (51, 0.5),
 (52, 0.5), (53, 0.5), (54, 0.5), (55, 0.5), (56, 0.5), (57, 0.5),
 (58, 0.278), (59, 0.278), (60, 0.549), (61, 0.549), (62, 0.549),
 (63, 0.444), (64, 0.549), (65, 0.722), (66, 0.667), (67, 0.722),
 (68, 0.612), (69, 0.611), (70, 0.763), (71, 0.603), (72, 0.722),
 (73, 0.333), (74, 0.631), (75, 0.722), (76, 0.686), (77, 0.889),
 (78, 0.722), (79, 0.722), (80, 0.768), (81, 0.741), (82, 0.556),
 (83, 0.592), (84, 0.611), (85, 0.69), (86, 0.439), (87, 0.768),
 (88, 0.645), (89, 0.795), (90, 0.611), (91, 0.333), (92, 0.863),
 (93, 0.333), (94, 0.658), (95, 0.5), (96, 0.5), (97, 0.631), (98, 0.549),
 (99, 0.549), (100, 0.494), (101, 0.439), (102, 0.521), (103, 0.411),
 (104, 0.603), (105, 0.329), (106, 0.603), (107, 0.549), (108, 0.549),
 (109, 0.576), (110, 0.521), (111, 0.549), (112, 0.549), (113, 0.521),
 (114, 0.549), (115, 0.603), (116, 0.439), (117, 0.576), (118, 0.713),
 (119, 0.686), (120, 0.493), (121, 0.686), (122, 0.494), (123, 0.48),
 (124, 0.2), (125, 0.48), (126, 0.549), (183, 0.46), (183, 0.46),
 (183, 0.46), (183, 0.46), (183, 0.46), (183, 0.46), (183, 0.46),
 (183, 0.46), (183, 0.46), (183, 0.46), (183, 0.46), (183, 0.46),
 (183, 0.46), (183, 0.46), (183, 0.46), (183, 0.46), (183, 0.46),
 (183, 0.46), (183, 0.46), (183, 0.46), (183, 0.46), (183, 0.46),
 (183, 0.46), (183, 0.46), (183, 0.46), (183, 0.46), (183, 0.46),
 (183, 0.46), (183, 0.46), (183, 0.46), (183, 0.46), (183, 0.46),
 (183, 0.46), (160, 0.25), (161, 0.62), (162, 0.247), (163, 0.549),
 (164, 0.167), (165, 0.713), (166, 0.5), (167, 0.753), (168, 0.753),
 (169, 0.753), (170, 0.753), (171, 1.042), (172, 0.713), (173, 0.603),
 (174, 0.987), (175, 0.603), (176, 0.4), (177, 0.549), (178, 0.411),
 (179, 0.549), (180, 0.549), (181, 0.576), (182, 0.494), (183, 0.46),
 (184, 0.549), (185, 0.549), (186, 0.549), (187, 0.549), (188, 1),
 (189, 0.603), (190, 1), (191, 0.658), (192, 0.823), (193, 0.686),
 (194, 0.795), (195, 0.987), (196, 0.768), (197, 0.768), (198, 0.823),
 (199, 0.768), (200, 0.768), (201, 0.713), (202, 0.713), (203, 0.713),
 (204, 0.713), (205, 0.713), (206, 0.713), (207, 0.713), (208, 0.768),
 (209, 0.713), (210, 0.79), (211, 0.79), (212, 0.89), (213, 0.823),
 (214, 0.549), (215, 0.549), (216, 0.713), (217, 0.603), (218, 0.603),
 (219, 1.042), (220, 0.987), (221, 0.603), (222, 0.987), (223, 0.603),
 (224, 0.494), (225, 0.329), (226, 0.79), (227, 0.79), (228, 0.786),
 (229, 0.713), (230, 0.384), (231, 0.384), (232, 0.384), (233, 0.384),
 (234, 0.384), (235, 0.384), (236, 0.494), (237, 0.494), (238, 0.494),
 (239, 0.494), (183, 0.46), (241, 0.329), (242, 0.274), (243, 0.686),
 (244, 0.686), (245, 0.686), (246, 0.384), (247, 0.549), (248, 0.384),
 (249, 0.384), (250, 0.384), (251, 0.384), (252, 0.494), (253, 0.494),
 (254, 0.494), (183, 0.46)
 )

class linkDest(object):
    """link or outline destination details"""
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


def getPDFstr(s):
    """ Return a PDF string depending on its coding.

    Notes:
        If only ascii then "(original)" is returned, else if only 8 bit chars
        then "(original)" with interspersed octal strings \nnn is returned,
        else a string "<FEFF[hexstring]>" is returned, where [hexstring] is the
        UTF-16BE encoding of the original.
    """
    if not bool(s):
        return "()"

    def make_utf16be(s):
        r = hexlify(bytearray([254, 255]) + bytearray(s, "UTF-16BE"))
        t = r if fitz_py2 else r.decode()
        return "<" + t + ">"  # brackets indicate hex


    # following either returns original string with mixed-in
    # octal numbers \nnn for chars outside ASCII range, or:
    # exits with utf-16be BOM version of the string
    r = ""
    for c in s:
        oc = ord(c)
        if oc > 255:  # shortcut if beyond 8-bit code range
            return make_utf16be(s)

        if oc > 31 and oc < 127:  # in ASCII range
            if c in ("(", ")", "\\"):  # these need to be escaped
                r += "\\"
            r += c
            continue

        if oc > 127:  # beyond ASCII
            r += "\\%03o" % oc
            continue

        # now the white spaces
        if oc == 8:  # backspace
            r += "\\b"
        elif oc == 9:  # tab
            r += "\\t"
        elif oc == 10:  # line feed
            r += "\\n"
        elif oc == 12:  # form feed
            r += "\\f"
        elif oc == 13:  # carriage return
            r += "\\r"
        else:
            r += "\\267"  # unsupported: replace by 0xB7

    return "(" + r + ")"


def getTJstr(text, glyphs, simple, ordering):
    """ Return a PDF string enclosed in [] brackets, suitable for the PDF TJ
    operator.

    Notes:
        The input string is converted to either 2 or 4 hex digits per character.
    Args:
        simple: no glyphs: 2-chars, use char codes as the glyph
                glyphs: 2-chars, use glyphs instead of char codes (Symbol,
                ZapfDingbats)
        not simple: ordering < 0: 4-chars, use glyphs not char codes
                    ordering >=0: a CJK font! 4 chars, use char codes as glyphs
    """
    if text.startswith("[<") and text.endswith(">]"): # already done
        return text

    if not bool(text):
        return "[<>]"

    if simple:  # each char or its glyph is coded as a 2-byte hex
        if glyphs is None:  # not Symbol, not ZapfDingbats: use char code
            otxt = "".join(["%02x" % ord(c) if ord(c) < 256 else "b7" for c in text])
        else:  # Symbol or ZapfDingbats: use glyphs
            otxt = "".join(["%02x" % glyphs[ord(c)][0] if ord(c) < 256 else "b7" for c in text])
        return "[<" + otxt + ">]"

    # non-simple fonts: each char or its glyph is coded as 4-byte hex
    if ordering < 0:  # not a CJK font: use the glyphs
        otxt = "".join(["%04x" % glyphs[ord(c)][0] for c in text])
    else:  # CJK: use the char codes
        otxt = "".join(["%04x" % ord(c) for c in text])

    return "[<" + otxt + ">]"

"""
Information taken from the following web sites:
www.din-formate.de
www.din-formate.info/amerikanische-formate.html
www.directtools.de/wissen/normen/iso.htm
"""
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
    """Return a tuple (width, height) for a given paper format string.
    
    Notes:
        'A4-L' will return (842, 595), the values for A4 landscape.
        Suffix '-P' and no suffix return the portrait tuple.
    """
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
        if (
            type(c) not in (list, tuple)
            or len(c) not in (1, 3, 4)
            or min(c) < 0
            or max(c) > 1
        ):
            raise ValueError("need 1, 3 or 4 color components in range 0 to 1")


def ColorCode(c, f):
    if c is None:
        return ""
    if hasattr(c, "__float__"):
        c = (c,)
    CheckColor(c)
    if len(c) == 1:
        s = "%g " % c[0]
        return s + "G " if f == "c" else s + "g "

    if len(c) == 3:
        s = "%g %g %g " % tuple(c)
        return s + "RG " if f == "c" else s + "rg "

    s = "%g %g %g %g " % tuple(c)
    return s + "K " if f == "c" else s + "k "


def JM_TUPLE(o):
    return tuple(map(lambda x: round(x, 8), o))


def CheckMorph(o):
    if not bool(o): return False
    if not (type(o) in (list, tuple) and len(o) == 2):
        raise ValueError("morph must be a sequence of length 2")
    if not (len(o[0]) == 2 and len(o[1]) == 6):
        raise ValueError("invalid morph parm 0")
    if not o[1][4] == o[1][5] == 0:
        raise ValueError("invalid morph parm 1")
    return True


def CheckFont(page, fontname):
    """Return an entry in the page's font list if reference name matches.
    """
    for f in page.getFontList():
        if f[4] == fontname:
            return f
        if f[3].lower() == fontname.lower():
            return f


def CheckFontInfo(doc, xref):
    """Return a font info if present in the document.
    """
    for f in doc.FontInfos:
        if xref == f[0]:
            return f


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


def planishLine(p1, p2):
    """Return matrix which flattens out the line from p1 to p2.

    Args:
        p1, p2: point_like
    Returns:
        Matrix which maps p1 to Point(0,0) and p2 to a point on the x axis at
        the same distance to Point(0,0). Will always combine a rotation and a
        transformation.
    """ 
    p1 = Point(p1)
    p2 = Point(p2)
    return TOOLS._hor_matrix(p1, p2)


def ImageProperties(img):
    """ Return basic properties of an image.

    Args:
        img: bytes, bytearray, io.BytesIO object or an opened image file.
    Returns:
        A dictionary with keys width, height, colorspace.n, bpc, type, ext and size,
        where 'type' is the MuPDF image type (0 to 14) and 'ext' the suitable
        file extension.
    """
    if type(img) is io.BytesIO:
        stream = img.getvalue()
    elif hasattr(img, "read"):
        stream = img.read()
    elif type(img) in (bytes, bytearray):
        stream = img
    else:
        raise ValueError("bad argument 'img'")

    return TOOLS.image_profile(stream)


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

%}
