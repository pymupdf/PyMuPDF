# ------------------------------------------------------------------------
# Copyright 2020-2022, Harald Lieder, mailto:harald.lieder@outlook.com
# License: GNU AFFERO GPL 3.0, https://www.gnu.org/licenses/agpl-3.0.html
#
# Part of "PyMuPDF", a Python binding for "MuPDF" (http://mupdf.com), a
# lightweight PDF, XPS, and E-book viewer, renderer and toolkit which is
# maintained and developed by Artifex Software, Inc. https://artifex.com.
# ------------------------------------------------------------------------
import math
import typing
import weakref

try:
    from . import pymupdf
except Exception:
    import pymupdf
try:
    from . import mupdf
except Exception:
    import mupdf

_format_g = pymupdf.format_g

g_exceptions_verbose = pymupdf.g_exceptions_verbose

point_like = "point_like"
rect_like = "rect_like"
matrix_like = "matrix_like"
quad_like = "quad_like"

# ByteString is gone from typing in 3.14.
# collections.abc.Buffer available from 3.12 only
try:
    ByteString = typing.ByteString
except AttributeError:
    # pylint: disable=unsupported-binary-operation
    ByteString = bytes | bytearray | memoryview

AnyType = typing.Any
OptInt = typing.Union[int, None]
OptFloat = typing.Optional[float]
OptStr = typing.Optional[str]
OptDict = typing.Optional[dict]
OptBytes = typing.Optional[ByteString]
OptSeq = typing.Optional[typing.Sequence]

"""
This is a collection of functions to extend PyMupdf.
"""


def get_text_blocks(
    page: pymupdf.Page,
    clip: rect_like = None,
    flags: OptInt = None,
    textpage: pymupdf.TextPage = None,
    sort: bool = False,
) -> list:
    """Return the text blocks on a page.

    Notes:
        Lines in a block are concatenated with line breaks.
    Args:
        flags: (int) control the amount of data parsed into the textpage.
    Returns:
        A list of the blocks. Each item contains the containing rectangle
        coordinates, text lines, running block number and block type.
    """
    pymupdf.CheckParent(page)
    if flags is None:
        flags = pymupdf.TEXTFLAGS_BLOCKS
    tp = textpage
    if tp is None:
        tp = page.get_textpage(clip=clip, flags=flags)
    elif getattr(tp, "parent") != page:
        raise ValueError("not a textpage of this page")

    blocks = tp.extractBLOCKS()
    if textpage is None:
        del tp
    if sort:
        blocks.sort(key=lambda b: (b[3], b[0]))
    return blocks


def get_text_words(
    page: pymupdf.Page,
    clip: rect_like = None,
    flags: OptInt = None,
    textpage: pymupdf.TextPage = None,
    sort: bool = False,
    delimiters=None,
    tolerance=3,
) -> list:
    """Return the text words as a list with the bbox for each word.

    Args:
        page: pymupdf.Page
        clip: (rect-like) area on page to consider
        flags: (int) control the amount of data parsed into the textpage.
        textpage: (pymupdf.TextPage) either passed-in or None.
        sort: (bool) sort the words in reading sequence.
        delimiters: (str,list) characters to use as word delimiters.
        tolerance: (float) consider words to be part of the same line if
            top or bottom coordinate are not larger than this. Relevant
            only if sort=True.

    Returns:
        Word tuples (x0, y0, x1, y1, "word", bno, lno, wno).
    """

    def sort_words(words):
        """Sort words line-wise, forgiving small deviations."""
        words.sort(key=lambda w: (w[3], w[0]))
        nwords = []  # final word list
        line = [words[0]]  # collects words roughly in same line
        lrect = pymupdf.Rect(words[0][:4])  # start the line rectangle
        for w in words[1:]:
            wrect = pymupdf.Rect(w[:4])
            if (
                abs(wrect.y0 - lrect.y0) <= tolerance
                or abs(wrect.y1 - lrect.y1) <= tolerance
            ):
                line.append(w)
                lrect |= wrect
            else:
                line.sort(key=lambda w: w[0])  # sort words in line l-t-r
                nwords.extend(line)  # append to final words list
                line = [w]  # start next line
                lrect = wrect  # start next line rect

        line.sort(key=lambda w: w[0])  # sort words in line l-t-r
        nwords.extend(line)  # append to final words list

        return nwords

    pymupdf.CheckParent(page)
    if flags is None:
        flags = pymupdf.TEXTFLAGS_WORDS
    tp = textpage
    if tp is None:
        tp = page.get_textpage(clip=clip, flags=flags)
    elif getattr(tp, "parent") != page:
        raise ValueError("not a textpage of this page")

    words = tp.extractWORDS(delimiters)

    # if textpage was given, we subselect the words in clip
    if textpage is not None and clip is not None:
        # sub-select words contained in clip
        clip = pymupdf.Rect(clip)
        words = [
            w for w in words if abs(clip & w[:4]) >= 0.5 * abs(pymupdf.Rect(w[:4]))
        ]

    if textpage is None:
        del tp
    if words and sort:
        # advanced sort if any words found
        words = sort_words(words)

    return words


def get_sorted_text(
    page: pymupdf.Page,
    clip: rect_like = None,
    flags: OptInt = None,
    textpage: pymupdf.TextPage = None,
    tolerance=3,
) -> str:
    """Extract plain text avoiding unacceptable line breaks.

    Text contained in clip will be sorted in reading sequence. Some effort
    is also spent to simulate layout vertically and horizontally.

    Args:
        page: pymupdf.Page
        clip: (rect-like) only consider text inside
        flags: (int) text extraction flags
        textpage: pymupdf.TextPage
        tolerance: (float) consider words to be on the same line if their top
            or bottom coordinates do not differ more than this.

    Notes:
        If a TextPage is provided, all text is checked for being inside clip
        with at least 50% of its bbox.
        This allows to use some "global" TextPage in conjunction with sub-
        selecting words in parts of the defined TextPage rectangle.

    Returns:
        A text string in reading sequence. Left indentation of each line,
        inter-line and inter-word distances strive to reflect the layout.
    """

    def line_text(clip, line):
        """Create the string of one text line.

        We are trying to simulate some horizontal layout here, too.

        Args:
            clip: (pymupdf.Rect) the area from which all text is being read.
            line: (list) word tuples (rect, text) contained in the line
        Returns:
            Text in this line. Generated from words in 'line'. Distance from
            predecessor is translated to multiple spaces, thus simulating
            text indentations and large horizontal distances.
        """
        line.sort(key=lambda w: w[0].x0)
        ltext = ""  # text in the line
        x1 = clip.x0  # end coordinate of ltext
        lrect = pymupdf.EMPTY_RECT()  # bbox of this line
        for r, t in line:
            lrect |= r  # update line bbox
            # convert distance to previous word to multiple spaces
            dist = max(
                int(round((r.x0 - x1) / r.width * len(t))),
                0 if (x1 == clip.x0 or r.x0 <= x1) else 1,
            )  # number of space characters

            ltext += " " * dist + t  # append word string
            x1 = r.x1  # update new end position
        return ltext

    # Extract words in correct sequence first.
    words = [
        (pymupdf.Rect(w[:4]), w[4])
        for w in get_text_words(
            page,
            clip=clip,
            flags=flags,
            textpage=textpage,
            sort=True,
            tolerance=tolerance,
        )
    ]

    if not words:  # no text present
        return ""
    totalbox = pymupdf.EMPTY_RECT()  # area covering all text
    for wr, text in words:
        totalbox |= wr

    lines = []  # list of reconstituted lines
    line = [words[0]]  # current line
    lrect = words[0][0]  # the line's rectangle

    # walk through the words
    for wr, text in words[1:]:  # start with second word
        w0r, _ = line[-1]  # read previous word in current line

        # if this word matches top or bottom of the line, append it
        if abs(lrect.y0 - wr.y0) <= tolerance or abs(lrect.y1 - wr.y1) <= tolerance:
            line.append((wr, text))
            lrect |= wr
        else:
            # output current line and re-initialize
            ltext = line_text(totalbox, line)
            lines.append((lrect, ltext))
            line = [(wr, text)]
            lrect = wr

    # also append unfinished last line
    ltext = line_text(totalbox, line)
    lines.append((lrect, ltext))

    # sort all lines vertically
    lines.sort(key=lambda l: (l[0].y1))

    text = lines[0][1]  # text of first line
    y1 = lines[0][0].y1  # its bottom coordinate
    for lrect, ltext in lines[1:]:
        distance = min(int(round((lrect.y0 - y1) / lrect.height)), 5)
        breaks = "\n" * (distance + 1)
        text += breaks + ltext
        y1 = lrect.y1

    # return text in clip
    return text


def get_textbox(
    page: pymupdf.Page,
    rect: rect_like,
    textpage: pymupdf.TextPage = None,
) -> str:
    tp = textpage
    if tp is None:
        tp = page.get_textpage()
    elif getattr(tp, "parent") != page:
        raise ValueError("not a textpage of this page")
    rc = tp.extractTextbox(rect)
    if textpage is None:
        del tp
    return rc


def get_text_selection(
    page: pymupdf.Page,
    p1: point_like,
    p2: point_like,
    clip: rect_like = None,
    textpage: pymupdf.TextPage = None,
):
    pymupdf.CheckParent(page)
    tp = textpage
    if tp is None:
        tp = page.get_textpage(clip=clip, flags=pymupdf.TEXT_DEHYPHENATE)
    elif getattr(tp, "parent") != page:
        raise ValueError("not a textpage of this page")
    rc = tp.extractSelection(p1, p2)
    if textpage is None:
        del tp
    return rc


def get_textpage_ocr(
    page: pymupdf.Page,
    flags: int = 0,
    language: str = "eng",
    dpi: int = 72,
    full: bool = False,
    tessdata: str = None,
) -> pymupdf.TextPage:
    """Create a Textpage from combined results of normal and OCR text parsing.

    Args:
        flags: (int) control content becoming part of the result.
        language: (str) specify expected language(s). Default is "eng" (English).
        dpi: (int) resolution in dpi, default 72.
        full: (bool) whether to OCR the full page image, or only its images (default)
    """
    pymupdf.CheckParent(page)
    tessdata = pymupdf.get_tessdata(tessdata)

    def full_ocr(page, dpi, language, flags):
        zoom = dpi / 72
        mat = pymupdf.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        ocr_pdf = pymupdf.Document(
                "pdf",
                pix.pdfocr_tobytes(
                    compress=False,
                    language=language,
                    tessdata=tessdata,
                    ),
                )
        ocr_page = ocr_pdf.load_page(0)
        unzoom = page.rect.width / ocr_page.rect.width
        ctm = pymupdf.Matrix(unzoom, unzoom) * page.derotation_matrix
        tpage = ocr_page.get_textpage(flags=flags, matrix=ctm)
        ocr_pdf.close()
        pix = None
        tpage.parent = weakref.proxy(page)
        return tpage

    # if OCR for the full page, OCR its pixmap @ desired dpi
    if full:
        return full_ocr(page, dpi, language, flags)

    # For partial OCR, make a normal textpage, then extend it with text that
    # is OCRed from each image.
    # Because of this, we need the images flag bit set ON.
    tpage = page.get_textpage(flags=flags)
    for block in page.get_text("dict", flags=pymupdf.TEXT_PRESERVE_IMAGES)["blocks"]:
        if block["type"] != 1:  # only look at images
            continue
        bbox = pymupdf.Rect(block["bbox"])
        if bbox.width <= 3 or bbox.height <= 3:  # ignore tiny stuff
            continue
        try:
            pix = pymupdf.Pixmap(block["image"])  # get image pixmap
            if pix.n - pix.alpha != 3:  # we need to convert this to RGB!
                pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
            if pix.alpha:  # must remove alpha channel
                pix = pymupdf.Pixmap(pix, 0)
            imgdoc = pymupdf.Document(
                    "pdf",
                    pix.pdfocr_tobytes(language=language, tessdata=tessdata),
                    )  # pdf with OCRed page
            imgpage = imgdoc.load_page(0)  # read image as a page
            pix = None
            # compute matrix to transform coordinates back to that of 'page'
            imgrect = imgpage.rect  # page size of image PDF
            shrink = pymupdf.Matrix(1 / imgrect.width, 1 / imgrect.height)
            mat = shrink * block["transform"]
            imgpage.extend_textpage(tpage, flags=0, matrix=mat)
            imgdoc.close()
        except (RuntimeError, mupdf.FzErrorBase):
            if 0 and g_exceptions_verbose:
                # Don't show exception info here because it can happen in
                # normal operation (see test_3842b).
                pymupdf.exception_info()
            tpage = None
            pymupdf.message("Falling back to full page OCR")
            return full_ocr(page, dpi, language, flags)

    return tpage


def get_text(
    page: pymupdf.Page,
    option: str = "text",
    *,
    clip: rect_like = None,
    flags: OptInt = None,
    textpage: pymupdf.TextPage = None,
    sort: bool = False,
    delimiters=None,
    tolerance=3,
):
    """Extract text from a page or an annotation.

    This is a unifying wrapper for various methods of the pymupdf.TextPage class.

    Args:
        option: (str) text, words, blocks, html, dict, json, rawdict, xhtml or xml.
        clip: (rect-like) restrict output to this area.
        flags: bit switches to e.g. exclude images or decompose ligatures.
        textpage: reuse this pymupdf.TextPage and make no new one. If specified,
            'flags' and 'clip' are ignored.

    Returns:
        the output of methods get_text_words / get_text_blocks or pymupdf.TextPage
        methods extractText, extractHTML, extractDICT, extractJSON, extractRAWDICT,
        extractXHTML or etractXML respectively.
        Default and misspelling choice is "text".
    """
    formats = {
        "text": pymupdf.TEXTFLAGS_TEXT,
        "html": pymupdf.TEXTFLAGS_HTML,
        "json": pymupdf.TEXTFLAGS_DICT,
        "rawjson": pymupdf.TEXTFLAGS_RAWDICT,
        "xml": pymupdf.TEXTFLAGS_XML,
        "xhtml": pymupdf.TEXTFLAGS_XHTML,
        "dict": pymupdf.TEXTFLAGS_DICT,
        "rawdict": pymupdf.TEXTFLAGS_RAWDICT,
        "words": pymupdf.TEXTFLAGS_WORDS,
        "blocks": pymupdf.TEXTFLAGS_BLOCKS,
    }
    option = option.lower()
    assert option in formats
    if option not in formats:
        option = "text"
    if flags is None:
        flags = formats[option]

    if option == "words":
        return get_text_words(
            page,
            clip=clip,
            flags=flags,
            textpage=textpage,
            sort=sort,
            delimiters=delimiters,
        )
    if option == "blocks":
        return get_text_blocks(
            page, clip=clip, flags=flags, textpage=textpage, sort=sort
        )

    if option == "text" and sort:
        return get_sorted_text(
            page,
            clip=clip,
            flags=flags,
            textpage=textpage,
            tolerance=tolerance,
        )

    pymupdf.CheckParent(page)
    cb = None
    if option in ("html", "xml", "xhtml"):  # no clipping for MuPDF functions
        clip = page.cropbox
    if clip is not None:
        clip = pymupdf.Rect(clip)
        cb = None
    elif type(page) is pymupdf.Page:
        cb = page.cropbox
    # pymupdf.TextPage with or without images
    tp = textpage
    #pymupdf.exception_info()
    if tp is None:
        tp = page.get_textpage(clip=clip, flags=flags)
    elif getattr(tp, "parent") != page:
        raise ValueError("not a textpage of this page")
    #pymupdf.log( '{option=}')
    if option == "json":
        t = tp.extractJSON(cb=cb, sort=sort)
    elif option == "rawjson":
        t = tp.extractRAWJSON(cb=cb, sort=sort)
    elif option == "dict":
        t = tp.extractDICT(cb=cb, sort=sort)
    elif option == "rawdict":
        t = tp.extractRAWDICT(cb=cb, sort=sort)
    elif option == "html":
        t = tp.extractHTML()
    elif option == "xml":
        t = tp.extractXML()
    elif option == "xhtml":
        t = tp.extractXHTML()
    else:
        t = tp.extractText(sort=sort)

    if textpage is None:
        del tp
    return t


def getLinkDict(ln, document=None) -> dict:
    if isinstance(ln, pymupdf.Outline):
        dest = ln.destination(document)
    elif isinstance(ln, pymupdf.Link):
        dest = ln.dest
    else:
        assert 0, f'Unexpected {type(ln)=}.'
    nl = {"kind": dest.kind, "xref": 0}
    try:
        if hasattr(ln, 'rect'):
            nl["from"] = ln.rect
    except Exception:
        # This seems to happen quite often in PyMuPDF/tests.
        if g_exceptions_verbose >= 2:   pymupdf.exception_info()
        pass
    pnt = pymupdf.Point(0, 0)
    if dest.flags & pymupdf.LINK_FLAG_L_VALID:
        pnt.x = dest.lt.x
    if dest.flags & pymupdf.LINK_FLAG_T_VALID:
        pnt.y = dest.lt.y

    if dest.kind == pymupdf.LINK_URI:
        nl["uri"] = dest.uri

    elif dest.kind == pymupdf.LINK_GOTO:
        nl["page"] = dest.page
        nl["to"] = pnt
        if dest.flags & pymupdf.LINK_FLAG_R_IS_ZOOM:
            nl["zoom"] = dest.rb.x
        else:
            nl["zoom"] = 0.0

    elif dest.kind == pymupdf.LINK_GOTOR:
        nl["file"] = dest.file_spec.replace("\\", "/")
        nl["page"] = dest.page
        if dest.page < 0:
            nl["to"] = dest.dest
        else:
            nl["to"] = pnt
            if dest.flags & pymupdf.LINK_FLAG_R_IS_ZOOM:
                nl["zoom"] = dest.rb.x
            else:
                nl["zoom"] = 0.0

    elif dest.kind == pymupdf.LINK_LAUNCH:
        nl["file"] = dest.file_spec.replace("\\", "/")

    elif dest.kind == pymupdf.LINK_NAMED:
        # The dicts should not have same key(s).
        assert not (dest.named.keys() & nl.keys())
        nl.update(dest.named)
        if 'to' in nl:
            nl['to'] = pymupdf.Point(nl['to'])

    else:
        nl["page"] = dest.page
    return nl


def getDestStr(xref: int, ddict: dict) -> str:
    """Calculate the PDF action string.

    Notes:
        Supports Link annotations and outline items (bookmarks).
    """
    if not ddict:
        return ""
    str_goto = lambda a, b, c, d: f"/A<</S/GoTo/D[{a} 0 R/XYZ {_format_g((b, c, d))}]>>"
    str_gotor1 = lambda a, b, c, d, e, f: f"/A<</S/GoToR/D[{a} /XYZ {_format_g((b, c, d))}]/F<</F{e}/UF{f}/Type/Filespec>>>>"
    str_gotor2 = lambda a, b, c: f"/A<</S/GoToR/D{a}/F<</F{b}/UF{c}/Type/Filespec>>>>"
    str_launch = lambda a, b: f"/A<</S/Launch/F<</F{a}/UF{b}/Type/Filespec>>>>"
    str_uri = lambda a: f"/A<</S/URI/URI{a}>>"

    if type(ddict) in (int, float):
        dest = str_goto(xref, 0, ddict, 0)
        return dest
    d_kind = ddict.get("kind", pymupdf.LINK_NONE)

    if d_kind == pymupdf.LINK_NONE:
        return ""

    if ddict["kind"] == pymupdf.LINK_GOTO:
        d_zoom = ddict.get("zoom", 0)
        to = ddict.get("to", pymupdf.Point(0, 0))
        d_left, d_top = to
        dest = str_goto(xref, d_left, d_top, d_zoom)
        return dest

    if ddict["kind"] == pymupdf.LINK_URI:
        dest = str_uri(pymupdf.get_pdf_str(ddict["uri"]),)
        return dest

    if ddict["kind"] == pymupdf.LINK_LAUNCH:
        fspec = pymupdf.get_pdf_str(ddict["file"])
        dest = str_launch(fspec, fspec)
        return dest

    if ddict["kind"] == pymupdf.LINK_GOTOR and ddict["page"] < 0:
        fspec = pymupdf.get_pdf_str(ddict["file"])
        dest = str_gotor2(pymupdf.get_pdf_str(ddict["to"]), fspec, fspec)
        return dest

    if ddict["kind"] == pymupdf.LINK_GOTOR and ddict["page"] >= 0:
        fspec = pymupdf.get_pdf_str(ddict["file"])
        dest = str_gotor1(
            ddict["page"],
            ddict["to"].x,
            ddict["to"].y,
            ddict["zoom"],
            fspec,
            fspec,
        )
        return dest

    return ""


def getLinkText(page: pymupdf.Page, lnk: dict) -> str:
    # --------------------------------------------------------------------------
    # define skeletons for /Annots object texts
    # --------------------------------------------------------------------------
    ctm = page.transformation_matrix
    ictm = ~ctm
    r = lnk["from"]
    rect = _format_g(tuple(r * ictm))

    annot = ""
    if lnk["kind"] == pymupdf.LINK_GOTO:
        if lnk["page"] >= 0:
            txt = pymupdf.annot_skel["goto1"]  # annot_goto
            pno = lnk["page"]
            xref = page.parent.page_xref(pno)
            pnt = lnk.get("to", pymupdf.Point(0, 0))  # destination point
            dest_page = page.parent[pno]
            dest_ctm = dest_page.transformation_matrix
            dest_ictm = ~dest_ctm
            ipnt = pnt * dest_ictm
            annot = txt(xref, ipnt.x, ipnt.y, lnk.get("zoom", 0), rect)
        else:
            txt = pymupdf.annot_skel["goto2"]  # annot_goto_n
            annot = txt(pymupdf.get_pdf_str(lnk["to"]), rect)

    elif lnk["kind"] == pymupdf.LINK_GOTOR:
        if lnk["page"] >= 0:
            txt = pymupdf.annot_skel["gotor1"]  # annot_gotor
            pnt = lnk.get("to", pymupdf.Point(0, 0))  # destination point
            if type(pnt) is not pymupdf.Point:
                pnt = pymupdf.Point(0, 0)
            annot = txt(
                lnk["page"],
                pnt.x,
                pnt.y,
                lnk.get("zoom", 0),
                lnk["file"],
                lnk["file"],
                rect,
            )
        else:
            txt = pymupdf.annot_skel["gotor2"]  # annot_gotor_n
            annot = txt(pymupdf.get_pdf_str(lnk["to"]), lnk["file"], rect)

    elif lnk["kind"] == pymupdf.LINK_LAUNCH:
        txt = pymupdf.annot_skel["launch"]  # annot_launch
        annot = txt(lnk["file"], lnk["file"], rect)

    elif lnk["kind"] == pymupdf.LINK_URI:
        txt = pymupdf.annot_skel["uri"]  # txt = annot_uri
        annot = txt(lnk["uri"], rect)

    elif lnk["kind"] == pymupdf.LINK_NAMED:
        txt = pymupdf.annot_skel["named"]  # annot_named
        lname = lnk.get("name")  # check presence of key
        if lname is None:  # if missing, fall back to alternative
            lname = lnk["nameddest"]
        annot = txt(lname, rect)
    if not annot:
        return annot

    # add a /NM PDF key to the object definition
    link_names = dict(  # existing ids and their xref
        [(x[0], x[2]) for x in page.annot_xrefs() if x[1] == pymupdf.PDF_ANNOT_LINK]   # pylint: disable=no-member
    )

    old_name = lnk.get("id", "")  # id value in the argument

    if old_name and (lnk["xref"], old_name) in link_names.items():
        name = old_name  # no new name if this is an update only
    else:
        i = 0
        stem = pymupdf.TOOLS.set_annot_stem() + "-L%i"
        while True:
            name = stem % i
            if name not in link_names.values():
                break
            i += 1
    # add /NM key to object definition
    annot = annot.replace("/Link", "/Link/NM(%s)" % name)
    return annot


# ----------------------------------------------------------------------
# Name:        wx.lib.colourdb.py
# Purpose:     Adds a bunch of colour names and RGB values to the
#              colour database so they can be found by name
#
# Author:      Robin Dunn
#
# Created:     13-March-2001
# Copyright:   (c) 2001-2017 by Total Control Software
# Licence:     wxWindows license
# Tags:        phoenix-port, unittest, documented
# ----------------------------------------------------------------------


def getColorList() -> list:
    """
    Returns a list of upper-case colour names.
    :rtype: list of strings
    """
    return [name for name, r, g, b in pymupdf.colors_wx_list()]


def getColorInfoList() -> list:
    """
    Returns list of (name, red, gree, blue) tuples, where:
        name: upper-case color name.
        read, green, blue: integers in range 0..255.
    :rtype: list of tuples
    """
    return pymupdf.colors_wx_list()


def getColor(name: str) -> tuple:
    """Retrieve RGB color in PDF format by name.

    Returns:
        a triple of floats in range 0 to 1. In case of name-not-found, "white" is returned.
    """
    return pymupdf.colors_pdf_dict().get(name.lower(), (1, 1, 1))


def getColorHSV(name: str) -> tuple:
    """Retrieve the hue, saturation, value triple of a color name.

    Returns:
        a triple (degree, percent, percent). If not found (-1, -1, -1) is returned.
    """
    try:
        x = getColorInfoList()[getColorList().index(name.upper())]
    except Exception:
        if g_exceptions_verbose:    pymupdf.exception_info()
        return (-1, -1, -1)

    r = x[1] / 255.0
    g = x[2] / 255.0
    b = x[3] / 255.0
    cmax = max(r, g, b)
    V = round(cmax * 100, 1)
    cmin = min(r, g, b)
    delta = cmax - cmin
    if delta == 0:
        hue = 0
    elif cmax == r:
        hue = 60.0 * (((g - b) / delta) % 6)
    elif cmax == g:
        hue = 60.0 * (((b - r) / delta) + 2)
    else:
        hue = 60.0 * (((r - g) / delta) + 4)

    H = int(round(hue))

    if cmax == 0:
        sat = 0
    else:
        sat = delta / cmax
    S = int(round(sat * 100))

    return (H, S, V)


def _get_font_properties(doc: pymupdf.Document, xref: int) -> tuple:
    fontname, ext, stype, buffer = doc.extract_font(xref)
    asc = 0.8
    dsc = -0.2
    if ext == "":
        return fontname, ext, stype, asc, dsc

    if buffer:
        try:
            font = pymupdf.Font(fontbuffer=buffer)
            asc = font.ascender
            dsc = font.descender
            bbox = font.bbox
            if asc - dsc < 1:
                if bbox.y0 < dsc:
                    dsc = bbox.y0
                asc = 1 - dsc
        except Exception:
            pymupdf.exception_info()
            asc *= 1.2
            dsc *= 1.2
        return fontname, ext, stype, asc, dsc
    if ext != "n/a":
        try:
            font = pymupdf.Font(fontname)
            asc = font.ascender
            dsc = font.descender
        except Exception:
            pymupdf.exception_info()
            asc *= 1.2
            dsc *= 1.2
    else:
        asc *= 1.2
        dsc *= 1.2
    return fontname, ext, stype, asc, dsc


def _show_fz_text( text):
    #if mupdf_cppyy:
    #    assert isinstance( text, cppyy.gbl.mupdf.Text)
    #else:
    #    assert isinstance( text, mupdf.Text)
    num_spans = 0
    num_chars = 0
    span = text.m_internal.head
    while 1:
        if not span:
            break
        num_spans += 1
        num_chars += span.len
        span = span.next
    return f'num_spans={num_spans} num_chars={num_chars}'


"""
Handle page labels for PDF documents.

Reading
-------
* compute the label of a page
* find page number(s) having the given label.

Writing
-------
Supports setting (defining) page labels for PDF documents.

A big Thank You goes to WILLIAM CHAPMAN who contributed the idea and
significant parts of the following code during late December 2020
through early January 2021.
"""


def rule_dict(item):
    """Make a Python dict from a PDF page label rule.

    Args:
        item -- a tuple (pno, rule) with the start page number and the rule
                string like <</S/D...>>.
    Returns:
        A dict like
        {'startpage': int, 'prefix': str, 'style': str, 'firstpagenum': int}.
    """
    # Jorj McKie, 2021-01-06

    pno, rule = item
    rule = rule[2:-2].split("/")[1:]  # strip "<<" and ">>"
    d = {"startpage": pno, "prefix": "", "firstpagenum": 1}
    skip = False
    for i, item in enumerate(rule): # pylint: disable=redefined-argument-from-local
        if skip:  # this item has already been processed
            skip = False  # deactivate skipping again
            continue
        if item == "S":  # style specification
            d["style"] = rule[i + 1]  # next item has the style
            skip = True  # do not process next item again
            continue
        if item.startswith("P"):  # prefix specification: extract the string
            x = item[1:].replace("(", "").replace(")", "")
            d["prefix"] = x
            continue
        if item.startswith("St"):  # start page number specification
            x = int(item[2:])
            d["firstpagenum"] = x
    return d


def get_label_pno(pgNo, labels):
    """Return the label for this page number.

    Args:
        pgNo: page number, 0-based.
        labels: result of doc._get_page_labels().
    Returns:
        The label (str) of the page number. Errors return an empty string.
    """
    # Jorj McKie, 2021-01-06

    item = [x for x in labels if x[0] <= pgNo][-1]
    rule = rule_dict(item)
    prefix = rule.get("prefix", "")
    style = rule.get("style", "")
    # make sure we start at 0 when enumerating the alphabet
    delta = -1 if style in ("a", "A") else 0
    pagenumber = pgNo - rule["startpage"] + rule["firstpagenum"] + delta
    return construct_label(style, prefix, pagenumber)


def construct_label(style, prefix, pno) -> str:
    """Construct a label based on style, prefix and page number."""
    # William Chapman, 2021-01-06

    n_str = ""
    if style == "D":
        n_str = str(pno)
    elif style == "r":
        n_str = integerToRoman(pno).lower()
    elif style == "R":
        n_str = integerToRoman(pno).upper()
    elif style == "a":
        n_str = integerToLetter(pno).lower()
    elif style == "A":
        n_str = integerToLetter(pno).upper()
    result = prefix + n_str
    return result


def integerToLetter(i) -> str:
    """Returns letter sequence string for integer i."""
    # William Chapman, Jorj McKie, 2021-01-06
    import string
    ls = string.ascii_uppercase
    n, a = 1, i
    while pow(26, n) <= a:
        a -= int(math.pow(26, n))
        n += 1

    str_t = ""
    for j in reversed(range(n)):
        f, g = divmod(a, int(math.pow(26, j)))
        str_t += ls[f]
        a = g
    return str_t


def integerToRoman(num: int) -> str:
    """Return roman numeral for an integer."""
    # William Chapman, Jorj McKie, 2021-01-06

    roman = (
        (1000, "M"),
        (900, "CM"),
        (500, "D"),
        (400, "CD"),
        (100, "C"),
        (90, "XC"),
        (50, "L"),
        (40, "XL"),
        (10, "X"),
        (9, "IX"),
        (5, "V"),
        (4, "IV"),
        (1, "I"),
    )

    def roman_num(num):
        for r, ltr in roman:
            x, _ = divmod(num, r)
            yield ltr * x
            num -= r * x
            if num <= 0:
                break

    return "".join([a for a in roman_num(num)])


# -------------------------------------------------------------------
# Functions to recover the quad contained in a text extraction bbox
# -------------------------------------------------------------------
def recover_bbox_quad(line_dir: tuple, span: dict, bbox: tuple) -> pymupdf.Quad:
    """Compute the quad located inside the bbox.

    The bbox may be any of the resp. tuples occurring inside the given span.

    Args:
        line_dir: (tuple) 'line["dir"]' of the owning line or None.
        span: (dict) the span. May be from get_texttrace() method.
        bbox: (tuple) the bbox of the span or any of its characters.
    Returns:
        The quad which is wrapped by the bbox.
    """
    if line_dir is None:
        line_dir = span["dir"]
    cos, sin = line_dir
    bbox = pymupdf.Rect(bbox)  # make it a rect
    if pymupdf.TOOLS.set_small_glyph_heights():  # ==> just fontsize as height
        d = 1
    else:
        d = span["ascender"] - span["descender"]

    height = d * span["size"]  # the quad's rectangle height
    # The following are distances from the bbox corners, at which we find the
    # respective quad points. The computation depends on in which quadrant the
    # text writing angle is located.
    hs = height * sin
    hc = height * cos
    if hc >= 0 and hs <= 0:  # quadrant 1
        ul = bbox.bl - (0, hc)
        ur = bbox.tr + (hs, 0)
        ll = bbox.bl - (hs, 0)
        lr = bbox.tr + (0, hc)
    elif hc <= 0 and hs <= 0:  # quadrant 2
        ul = bbox.br + (hs, 0)
        ur = bbox.tl - (0, hc)
        ll = bbox.br + (0, hc)
        lr = bbox.tl - (hs, 0)
    elif hc <= 0 and hs >= 0:  # quadrant 3
        ul = bbox.tr - (0, hc)
        ur = bbox.bl + (hs, 0)
        ll = bbox.tr - (hs, 0)
        lr = bbox.bl + (0, hc)
    else:  # quadrant 4
        ul = bbox.tl + (hs, 0)
        ur = bbox.br - (0, hc)
        ll = bbox.tl + (0, hc)
        lr = bbox.br - (hs, 0)
    return pymupdf.Quad(ul, ur, ll, lr)


def recover_quad(line_dir: tuple, span: dict) -> pymupdf.Quad:
    """Recover the quadrilateral of a text span.

    Args:
        line_dir: (tuple) 'line["dir"]' of the owning line.
        span: the span.
    Returns:
        The quadrilateral enveloping the span's text.
    """
    if type(line_dir) is not tuple or len(line_dir) != 2:
        raise ValueError("bad line dir argument")
    if type(span) is not dict:
        raise ValueError("bad span argument")
    return recover_bbox_quad(line_dir, span, span["bbox"])


def recover_line_quad(line: dict, spans: list = None) -> pymupdf.Quad:
    """Calculate the line quad for 'dict' / 'rawdict' text extractions.

    The lower quad points are those of the first, resp. last span quad.
    The upper points are determined by the maximum span quad height.
    From this, compute a rect with bottom-left in (0, 0), convert this to a
    quad and rotate and shift back to cover the text of the spans.

    Args:
        spans: (list, optional) sub-list of spans to consider.
    Returns:
        pymupdf.Quad covering selected spans.
    """
    if spans is None:  # no sub-selection
        spans = line["spans"]  # all spans
    if len(spans) == 0:
        raise ValueError("bad span list")
    line_dir = line["dir"]  # text direction
    cos, sin = line_dir
    q0 = recover_quad(line_dir, spans[0])  # quad of first span
    if len(spans) > 1:  # get quad of last span
        q1 = recover_quad(line_dir, spans[-1])
    else:
        q1 = q0  # last = first

    line_ll = q0.ll  # lower-left of line quad
    line_lr = q1.lr  # lower-right of line quad

    mat0 = pymupdf.planish_line(line_ll, line_lr)

    # map base line to x-axis such that line_ll goes to (0, 0)
    x_lr = line_lr * mat0

    small = pymupdf.TOOLS.set_small_glyph_heights()  # small glyph heights?

    h = max(
        [s["size"] * (1 if small else (s["ascender"] - s["descender"])) for s in spans]
    )

    line_rect = pymupdf.Rect(0, -h, x_lr.x, 0)  # line rectangle
    line_quad = line_rect.quad  # make it a quad and:
    line_quad *= ~mat0
    return line_quad


def recover_span_quad(line_dir: tuple, span: dict, chars: list = None) -> pymupdf.Quad:
    """Calculate the span quad for 'dict' / 'rawdict' text extractions.

    Notes:
        There are two execution paths:
        1. For the full span quad, the result of 'recover_quad' is returned.
        2. For the quad of a sub-list of characters, the char quads are
           computed and joined. This is only supported for the "rawdict"
           extraction option.

    Args:
        line_dir: (tuple) 'line["dir"]' of the owning line.
        span: (dict) the span.
        chars: (list, optional) sub-list of characters to consider.
    Returns:
        pymupdf.Quad covering selected characters.
    """
    if line_dir is None:  # must be a span from get_texttrace()
        line_dir = span["dir"]
    if chars is None:  # no sub-selection
        return recover_quad(line_dir, span)
    if "chars" not in span.keys():
        raise ValueError("need 'rawdict' option to sub-select chars")

    q0 = recover_char_quad(line_dir, span, chars[0])  # quad of first char
    if len(chars) > 1:  # get quad of last char
        q1 = recover_char_quad(line_dir, span, chars[-1])
    else:
        q1 = q0  # last = first

    span_ll = q0.ll  # lower-left of span quad
    span_lr = q1.lr  # lower-right of span quad
    mat0 = pymupdf.planish_line(span_ll, span_lr)
    # map base line to x-axis such that span_ll goes to (0, 0)
    x_lr = span_lr * mat0

    small = pymupdf.TOOLS.set_small_glyph_heights()  # small glyph heights?
    h = span["size"] * (1 if small else (span["ascender"] - span["descender"]))

    span_rect = pymupdf.Rect(0, -h, x_lr.x, 0)  # line rectangle
    span_quad = span_rect.quad  # make it a quad and:
    span_quad *= ~mat0  # rotate back and shift back
    return span_quad


def recover_char_quad(line_dir: tuple, span: dict, char: dict) -> pymupdf.Quad:
    """Recover the quadrilateral of a text character.

    This requires the "rawdict" option of text extraction.

    Args:
        line_dir: (tuple) 'line["dir"]' of the span's line.
        span: (dict) the span dict.
        char: (dict) the character dict.
    Returns:
        The quadrilateral enveloping the character.
    """
    if line_dir is None:
        line_dir = span["dir"]
    if type(line_dir) is not tuple or len(line_dir) != 2:
        raise ValueError("bad line dir argument")
    if type(span) is not dict:
        raise ValueError("bad span argument")
    if type(char) is dict:
        bbox = pymupdf.Rect(char["bbox"])
    elif type(char) is tuple:
        bbox = pymupdf.Rect(char[3])
    else:
        raise ValueError("bad span argument")

    return recover_bbox_quad(line_dir, span, bbox)
