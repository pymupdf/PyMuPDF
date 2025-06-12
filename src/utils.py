# ------------------------------------------------------------------------
# Copyright 2020-2022, Harald Lieder, mailto:harald.lieder@outlook.com
# License: GNU AFFERO GPL 3.0, https://www.gnu.org/licenses/agpl-3.0.html
#
# Part of "PyMuPDF", a Python binding for "MuPDF" (http://mupdf.com), a
# lightweight PDF, XPS, and E-book viewer, renderer and toolkit which is
# maintained and developed by Artifex Software, Inc. https://artifex.com.
# ------------------------------------------------------------------------
import io
import math
import os
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


def write_text(
        page: pymupdf.Page,
        rect=None,
        writers=None,
        overlay=True,
        color=None,
        opacity=None,
        keep_proportion=True,
        rotate=0,
        oc=0,
        ) -> None:
    """Write the text of one or more pymupdf.TextWriter objects.

    Args:
        rect: target rectangle. If None, the union of the text writers is used.
        writers: one or more pymupdf.TextWriter objects.
        overlay: put in foreground or background.
        keep_proportion: maintain aspect ratio of rectangle sides.
        rotate: arbitrary rotation angle.
        oc: the xref of an optional content object
    """
    assert isinstance(page, pymupdf.Page)
    if not writers:
        raise ValueError("need at least one pymupdf.TextWriter")
    if type(writers) is pymupdf.TextWriter:
        if rotate == 0 and rect is None:
            writers.write_text(page, opacity=opacity, color=color, overlay=overlay)
            return None
        else:
            writers = (writers,)
    clip = writers[0].text_rect
    textdoc = pymupdf.Document()
    tpage = textdoc.new_page(width=page.rect.width, height=page.rect.height)
    for writer in writers:
        clip |= writer.text_rect
        writer.write_text(tpage, opacity=opacity, color=color)
    if rect is None:
        rect = clip
    page.show_pdf_page(
        rect,
        textdoc,
        0,
        overlay=overlay,
        keep_proportion=keep_proportion,
        rotate=rotate,
        clip=clip,
        oc=oc,
    )
    textdoc = None
    tpage = None


def show_pdf_page(
        page,
        rect,
        docsrc,
        pno=0,
        keep_proportion=True,
        overlay=True,
        oc=0,
        rotate=0,
        clip=None,
        ) -> int:
    """Show page number 'pno' of PDF 'docsrc' in rectangle 'rect'.

    Args:
        rect: (rect-like) where to place the source image
        docsrc: (document) source PDF
        pno: (int) source page number
        keep_proportion: (bool) do not change width-height-ratio
        overlay: (bool) put in foreground
        oc: (xref) make visibility dependent on this OCG / OCMD (which must be defined in the target PDF)
        rotate: (int) degrees (multiple of 90)
        clip: (rect-like) part of source page rectangle
    Returns:
        xref of inserted object (for reuse)
    """
    def calc_matrix(sr, tr, keep=True, rotate=0):
        """Calculate transformation matrix from source to target rect.

        Notes:
            The product of four matrices in this sequence: (1) translate correct
            source corner to origin, (2) rotate, (3) scale, (4) translate to
            target's top-left corner.
        Args:
            sr: source rect in PDF (!) coordinate system
            tr: target rect in PDF coordinate system
            keep: whether to keep source ratio of width to height
            rotate: rotation angle in degrees
        Returns:
            Transformation matrix.
        """
        # calc center point of source rect
        smp = (sr.tl + sr.br) / 2.0
        # calc center point of target rect
        tmp = (tr.tl + tr.br) / 2.0

        # m moves to (0, 0), then rotates
        m = pymupdf.Matrix(1, 0, 0, 1, -smp.x, -smp.y) * pymupdf.Matrix(rotate)

        sr1 = sr * m  # resulting source rect to calculate scale factors

        fw = tr.width / sr1.width  # scale the width
        fh = tr.height / sr1.height  # scale the height
        if keep:
            fw = fh = min(fw, fh)  # take min if keeping aspect ratio

        m *= pymupdf.Matrix(fw, fh)  # concat scale matrix
        m *= pymupdf.Matrix(1, 0, 0, 1, tmp.x, tmp.y)  # concat move to target center
        return pymupdf.JM_TUPLE(m)

    pymupdf.CheckParent(page)
    doc = page.parent

    if not doc.is_pdf or not docsrc.is_pdf:
        raise ValueError("is no PDF")

    if rect.is_empty or rect.is_infinite:
        raise ValueError("rect must be finite and not empty")

    while pno < 0:  # support negative page numbers
        pno += docsrc.page_count
    src_page = docsrc[pno]  # load source page

    tar_rect = rect * ~page.transformation_matrix  # target rect in PDF coordinates

    src_rect = src_page.rect if not clip else src_page.rect & clip  # source rect
    if src_rect.is_empty or src_rect.is_infinite:
        raise ValueError("clip must be finite and not empty")
    src_rect = src_rect * ~src_page.transformation_matrix  # ... in PDF coord

    matrix = calc_matrix(src_rect, tar_rect, keep=keep_proportion, rotate=rotate)

    # list of existing /Form /XObjects
    ilst = [i[1] for i in doc.get_page_xobjects(page.number)]
    ilst += [i[7] for i in doc.get_page_images(page.number)]
    ilst += [i[4] for i in doc.get_page_fonts(page.number)]

    # create a name not in that list
    n = "fzFrm"
    i = 0
    _imgname = n + "0"
    while _imgname in ilst:
        i += 1
        _imgname = n + str(i)

    isrc = docsrc._graft_id  # used as key for graftmaps
    if doc._graft_id == isrc:
        raise ValueError("source document must not equal target")

    # retrieve / make pymupdf.Graftmap for source PDF
    gmap = doc.Graftmaps.get(isrc, None)
    if gmap is None:
        gmap = pymupdf.Graftmap(doc)
        doc.Graftmaps[isrc] = gmap

    # take note of generated xref for automatic reuse
    pno_id = (isrc, pno)  # id of docsrc[pno]
    xref = doc.ShownPages.get(pno_id, 0)

    if overlay:
        page.wrap_contents()  # ensure a balanced graphics state
    xref = page._show_pdf_page(
        src_page,
        overlay=overlay,
        matrix=matrix,
        xref=xref,
        oc=oc,
        clip=src_rect,
        graftmap=gmap,
        _imgname=_imgname,
    )
    doc.ShownPages[pno_id] = xref

    return xref


def replace_image(page: pymupdf.Page, xref: int, *, filename=None, pixmap=None, stream=None):
    """Replace the image referred to by xref.

    Replace the image by changing the object definition stored under xref. This
    will leave the pages appearance instructions intact, so the new image is
    being displayed with the same bbox, rotation etc.
    By providing a small fully transparent image, an effect as if the image had
    been deleted can be achieved.
    A typical use may include replacing large images by a smaller version,
    e.g. with a lower resolution or graylevel instead of colored.

    Args:
        xref: the xref of the image to replace.
        filename, pixmap, stream: exactly one of these must be provided. The
            meaning being the same as in Page.insert_image.
    """
    doc = page.parent  # the owning document
    if not doc.xref_is_image(xref):
        raise ValueError("xref not an image")  # insert new image anywhere in page
    if bool(filename) + bool(stream) + bool(pixmap) != 1:
        raise ValueError("Exactly one of filename/stream/pixmap must be given")
    new_xref = page.insert_image(
        page.rect, filename=filename, stream=stream, pixmap=pixmap
    )
    doc.xref_copy(new_xref, xref)  # copy over new to old
    last_contents_xref = page.get_contents()[-1]
    # new image insertion has created a new /Contents source,
    # which we will set to spaces now
    doc.update_stream(last_contents_xref, b" ")
    page._image_info = None  # clear cache of extracted image information


def delete_image(page: pymupdf.Page, xref: int):
    """Delete the image referred to by xef.

    Actually replaces by a small transparent Pixmap using method Page.replace_image.

    Args:
        xref: xref of the image to delete.
    """
    # make a small 100% transparent pixmap (of just any dimension)
    pix = pymupdf.Pixmap(pymupdf.csGRAY, (0, 0, 1, 1), 1)
    pix.clear_with()  # clear all samples bytes to 0x00
    page.replace_image(xref, pixmap=pix)


def insert_image(
        page,
        rect,
        *,
        alpha=-1,
        filename=None,
        height=0,
        keep_proportion=True,
        mask=None,
        oc=0,
        overlay=True,
        pixmap=None,
        rotate=0,
        stream=None,
        width=0,
        xref=0,
        ):
    """Insert an image for display in a rectangle.

    Args:
        rect: (rect_like) position of image on the page.
        alpha: (int, optional) set to 0 if image has no transparency.
        filename: (str, Path, file object) image filename.
        height: (int)
        keep_proportion: (bool) keep width / height ratio (default).
        mask: (bytes, optional) image consisting of alpha values to use.
        oc: (int) xref of OCG or OCMD to declare as Optional Content.
        overlay: (bool) put in foreground (default) or background.
        pixmap: (pymupdf.Pixmap) use this as image.
        rotate: (int) rotate by 0, 90, 180 or 270 degrees.
        stream: (bytes) use this as image.
        width: (int)
        xref: (int) use this as image.

    'page' and 'rect' are positional, all other parameters are keywords.

    If 'xref' is given, that image is used. Other input options are ignored.
    Else, exactly one of pixmap, stream or filename must be given.

    'alpha=0' for non-transparent images improves performance significantly.
    Affects stream and filename only.

    Optimum transparent insertions are possible by using filename / stream in
    conjunction with a 'mask' image of alpha values.

    Returns:
        xref (int) of inserted image. Re-use as argument for multiple insertions.
    """
    pymupdf.CheckParent(page)
    doc = page.parent
    if not doc.is_pdf:
        raise ValueError("is no PDF")

    if xref == 0 and (bool(filename) + bool(stream) + bool(pixmap) != 1):
        raise ValueError("xref=0 needs exactly one of filename, pixmap, stream")

    if filename:
        if type(filename) is str:
            pass
        elif hasattr(filename, "absolute"):
            filename = str(filename)
        elif hasattr(filename, "name"):
            filename = filename.name
        else:
            raise ValueError("bad filename")

    if filename and not os.path.exists(filename):
        raise FileNotFoundError("No such file: '%s'" % filename)
    elif stream and type(stream) not in (bytes, bytearray, io.BytesIO):
        raise ValueError("stream must be bytes-like / BytesIO")
    elif pixmap and type(pixmap) is not pymupdf.Pixmap:
        raise ValueError("pixmap must be a pymupdf.Pixmap")
    if mask and not (stream or filename):
        raise ValueError("mask requires stream or filename")
    if mask and type(mask) not in (bytes, bytearray, io.BytesIO):
        raise ValueError("mask must be bytes-like / BytesIO")
    while rotate < 0:
        rotate += 360
    while rotate >= 360:
        rotate -= 360
    if rotate not in (0, 90, 180, 270):
        raise ValueError("bad rotate value")

    r = pymupdf.Rect(rect)
    if r.is_empty or r.is_infinite:
        raise ValueError("rect must be finite and not empty")
    clip = r * ~page.transformation_matrix

    # Create a unique image reference name.
    ilst = [i[7] for i in doc.get_page_images(page.number)]
    ilst += [i[1] for i in doc.get_page_xobjects(page.number)]
    ilst += [i[4] for i in doc.get_page_fonts(page.number)]
    n = "fzImg"  # 'pymupdf image'
    i = 0
    _imgname = n + "0"  # first name candidate
    while _imgname in ilst:
        i += 1
        _imgname = n + str(i)  # try new name

    if overlay:
        page.wrap_contents()  # ensure a balanced graphics state
    digests = doc.InsertedImages
    xref, digests = page._insert_image(
        filename=filename,
        pixmap=pixmap,
        stream=stream,
        imask=mask,
        clip=clip,
        overlay=overlay,
        oc=oc,
        xref=xref,
        rotate=rotate,
        keep_proportion=keep_proportion,
        width=width,
        height=height,
        alpha=alpha,
        _imgname=_imgname,
        digests=digests,
    )
    if digests is not None:
        doc.InsertedImages = digests

    return xref


def search_for(
        page,
        text,
        *,
        clip=None,
        quads=False,
        flags=pymupdf.TEXT_DEHYPHENATE
            | pymupdf.TEXT_PRESERVE_WHITESPACE
            | pymupdf.TEXT_PRESERVE_LIGATURES
            | pymupdf.TEXT_MEDIABOX_CLIP
            ,
        textpage=None,
        ) -> list:
    """Search for a string on a page.

    Args:
        text: string to be searched for
        clip: restrict search to this rectangle
        quads: (bool) return quads instead of rectangles
        flags: bit switches, default: join hyphened words
        textpage: a pre-created pymupdf.TextPage
    Returns:
        a list of rectangles or quads, each containing one occurrence.
    """
    if clip is not None:
        clip = pymupdf.Rect(clip)

    pymupdf.CheckParent(page)
    tp = textpage
    if tp is None:
        tp = page.get_textpage(clip=clip, flags=flags)  # create pymupdf.TextPage
    elif getattr(tp, "parent") != page:
        raise ValueError("not a textpage of this page")
    rlist = tp.search(text, quads=quads)
    if textpage is None:
        del tp
    return rlist


def search_page_for(
    doc: pymupdf.Document,
    pno: int,
    text: str,
    quads: bool = False,
    clip: rect_like = None,
    flags: int = pymupdf.TEXT_DEHYPHENATE
            | pymupdf.TEXT_PRESERVE_LIGATURES
            | pymupdf.TEXT_PRESERVE_WHITESPACE
            | pymupdf.TEXT_MEDIABOX_CLIP
            ,
    textpage: pymupdf.TextPage = None,
) -> list:
    """Search for a string on a page.

    Args:
        pno: page number
        text: string to be searched for
        clip: restrict search to this rectangle
        quads: (bool) return quads instead of rectangles
        flags: bit switches, default: join hyphened words
        textpage: reuse a prepared textpage
    Returns:
        a list of rectangles or quads, each containing an occurrence.
    """

    return doc[pno].search_for(
        text,
        quads=quads,
        clip=clip,
        flags=flags,
        textpage=textpage,
    )


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


def get_image_info(page: pymupdf.Page, hashes: bool = False, xrefs: bool = False) -> list:
    """Extract image information only from a pymupdf.TextPage.

    Args:
        hashes: (bool) include MD5 hash for each image.
        xrefs: (bool) try to find the xref for each image. Sets hashes to true.
    """
    doc = page.parent
    if xrefs and doc.is_pdf:
        hashes = True
    if not doc.is_pdf:
        xrefs = False
    imginfo = getattr(page, "_image_info", None)
    if imginfo and not xrefs:
        return imginfo
    if not imginfo:
        tp = page.get_textpage(flags=pymupdf.TEXT_PRESERVE_IMAGES)
        imginfo = tp.extractIMGINFO(hashes=hashes)
        del tp
        if hashes:
            page._image_info = imginfo
    if not xrefs or not doc.is_pdf:
        return imginfo
    imglist = page.get_images()
    digests = {}
    for item in imglist:
        xref = item[0]
        pix = pymupdf.Pixmap(doc, xref)
        digests[pix.digest] = xref
        del pix
    for i in range(len(imginfo)):
        item = imginfo[i]
        xref = digests.get(item["digest"], 0)
        item["xref"] = xref
        imginfo[i] = item
    return imginfo


def get_image_rects(page: pymupdf.Page, name, transform=False) -> list:
    """Return list of image positions on a page.

    Args:
        name: (str, list, int) image identification. May be reference name, an
              item of the page's image list or an xref.
        transform: (bool) whether to also return the transformation matrix.
    Returns:
        A list of pymupdf.Rect objects or tuples of (pymupdf.Rect, pymupdf.Matrix)
        for all image locations on the page.
    """
    if type(name) in (list, tuple):
        xref = name[0]
    elif type(name) is int:
        xref = name
    else:
        imglist = [i for i in page.get_images() if i[7] == name]
        if imglist == []:
            raise ValueError("bad image name")
        elif len(imglist) != 1:
            raise ValueError("multiple image names found")
        xref = imglist[0][0]
    pix = pymupdf.Pixmap(page.parent, xref)  # make pixmap of the image to compute MD5
    digest = pix.digest
    del pix
    infos = page.get_image_info(hashes=True)
    if not transform:
        bboxes = [pymupdf.Rect(im["bbox"]) for im in infos if im["digest"] == digest]
    else:
        bboxes = [
            (pymupdf.Rect(im["bbox"]), pymupdf.Matrix(im["transform"]))
            for im in infos
            if im["digest"] == digest
        ]
    return bboxes


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


def get_page_text(
    doc: pymupdf.Document,
    pno: int,
    option: str = "text",
    clip: rect_like = None,
    flags: OptInt = None,
    textpage: pymupdf.TextPage = None,
    sort: bool = False,
) -> typing.Any:
    """Extract a document page's text by page number.

    Notes:
        Convenience function calling page.get_text().
    Args:
        pno: page number
        option: (str) text, words, blocks, html, dict, json, rawdict, xhtml or xml.
    Returns:
        output from page.TextPage().
    """
    return doc[pno].get_text(option, clip=clip, flags=flags, sort=sort)

def get_pixmap(
        page: pymupdf.Page,
        *,
        matrix: matrix_like=pymupdf.Identity,
        dpi=None,
        colorspace: pymupdf.Colorspace=pymupdf.csRGB,
        clip: rect_like=None,
        alpha: bool=False,
        annots: bool=True,
        ) -> pymupdf.Pixmap:
    """Create pixmap of page.

    Keyword args:
        matrix: Matrix for transformation (default: Identity).
        dpi: desired dots per inch. If given, matrix is ignored.
        colorspace: (str/Colorspace) cmyk, rgb, gray - case ignored, default csRGB.
        clip: (irect-like) restrict rendering to this area.
        alpha: (bool) whether to include alpha channel
        annots: (bool) whether to also render annotations
    """
    if dpi:
        zoom = dpi / 72
        matrix = pymupdf.Matrix(zoom, zoom)

    if type(colorspace) is str:
        if colorspace.upper() == "GRAY":
            colorspace = pymupdf.csGRAY
        elif colorspace.upper() == "CMYK":
            colorspace = pymupdf.csCMYK
        else:
            colorspace = pymupdf.csRGB
    if colorspace.n not in (1, 3, 4):
        raise ValueError("unsupported colorspace")

    dl = page.get_displaylist(annots=annots)
    pix = dl.get_pixmap(matrix=matrix, colorspace=colorspace, alpha=alpha, clip=clip)
    dl = None
    if dpi:
        pix.set_dpi(dpi, dpi)
    return pix


def get_page_pixmap(
    doc: pymupdf.Document,
    pno: int,
    *,
    matrix: matrix_like = pymupdf.Identity,
    dpi=None,
    colorspace: pymupdf.Colorspace = pymupdf.csRGB,
    clip: rect_like = None,
    alpha: bool = False,
    annots: bool = True,
) -> pymupdf.Pixmap:
    """Create pixmap of document page by page number.

    Notes:
        Convenience function calling page.get_pixmap.
    Args:
        pno: (int) page number
        matrix: pymupdf.Matrix for transformation (default: pymupdf.Identity).
        colorspace: (str,pymupdf.Colorspace) rgb, rgb, gray - case ignored, default csRGB.
        clip: (irect-like) restrict rendering to this area.
        alpha: (bool) include alpha channel
        annots: (bool) also render annotations
    """
    return doc[pno].get_pixmap(
            matrix=matrix,
            dpi=dpi, colorspace=colorspace,
            clip=clip,
            alpha=alpha,
            annots=annots
            )


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


def get_links(page: pymupdf.Page) -> list:
    """Create a list of all links contained in a PDF page.

    Notes:
        see PyMuPDF ducmentation for details.
    """

    pymupdf.CheckParent(page)
    ln = page.first_link
    links = []
    while ln:
        nl = getLinkDict(ln, page.parent)
        links.append(nl)
        ln = ln.next
    if links != [] and page.parent.is_pdf:
        linkxrefs = [x for x in
                #page.annot_xrefs()
                pymupdf.JM_get_annot_xref_list2(page)
                if x[1] == pymupdf.PDF_ANNOT_LINK  # pylint: disable=no-member
                ]
        if len(linkxrefs) == len(links):
            for i in range(len(linkxrefs)):
                links[i]["xref"] = linkxrefs[i][0]
                links[i]["id"] = linkxrefs[i][2]
    return links


def get_toc(
    doc: pymupdf.Document,
    simple: bool = True,
) -> list:
    """Create a table of contents.

    Args:
        simple: a bool to control output. Returns a list, where each entry consists of outline level, title, page number and link destination (if simple = False). For details see PyMuPDF's documentation.
    """
    def recurse(olItem, liste, lvl):
        """Recursively follow the outline item chain and record item information in a list."""
        while olItem and olItem.this.m_internal:
            if olItem.title:
                title = olItem.title
            else:
                title = " "

            if not olItem.is_external:
                if olItem.uri:
                    if olItem.page == -1:
                        resolve = doc.resolve_link(olItem.uri)
                        page = resolve[0] + 1
                    else:
                        page = olItem.page + 1
                else:
                    page = -1
            else:
                page = -1

            if not simple:
                link = getLinkDict(olItem, doc)
                liste.append([lvl, title, page, link])
            else:
                liste.append([lvl, title, page])

            if olItem.down:
                liste = recurse(olItem.down, liste, lvl + 1)
            olItem = olItem.next
        return liste

    # ensure document is open
    if doc.is_closed:
        raise ValueError("document closed")
    doc.init_doc()
    olItem = doc.outline
    if not olItem:
        return []
    lvl = 1
    liste = []
    toc = recurse(olItem, liste, lvl)
    if doc.is_pdf and not simple:
        doc._extend_toc_items(toc)
    return toc


def del_toc_item(
    doc: pymupdf.Document,
    idx: int,
) -> None:
    """Delete TOC / bookmark item by index."""
    xref = doc.get_outline_xrefs()[idx]
    doc._remove_toc_item(xref)


def set_toc_item(
    doc: pymupdf.Document,
    idx: int,
    dest_dict: OptDict = None,
    kind: OptInt = None,
    pno: OptInt = None,
    uri: OptStr = None,
    title: OptStr = None,
    to: point_like = None,
    filename: OptStr = None,
    zoom: float = 0,
) -> None:
    """Update TOC item by index.

    It allows changing the item's title and link destination.

    Args:
        idx:
            (int) desired index of the TOC list, as created by get_toc.
        dest_dict:
            (dict) destination dictionary as created by get_toc(False).
            Outrules all other parameters. If None, the remaining parameters
            are used to make a dest dictionary.
        kind:
            (int) kind of link (pymupdf.LINK_GOTO, etc.). If None, then only
            the title will be updated. If pymupdf.LINK_NONE, the TOC item will
            be deleted.
        pno:
            (int) page number (1-based like in get_toc). Required if
            pymupdf.LINK_GOTO.
        uri:
            (str) the URL, required if pymupdf.LINK_URI.
        title:
            (str) the new title. No change if None.
        to:
            (point-like) destination on the target page. If omitted, (72, 36)
            will be used as target coordinates.
        filename:
            (str) destination filename, required for pymupdf.LINK_GOTOR and
            pymupdf.LINK_LAUNCH.
        name:
            (str) a destination name for pymupdf.LINK_NAMED.
        zoom:
            (float) a zoom factor for the target location (pymupdf.LINK_GOTO).
    """
    xref = doc.get_outline_xrefs()[idx]
    page_xref = 0
    if type(dest_dict) is dict:
        if dest_dict["kind"] == pymupdf.LINK_GOTO:
            pno = dest_dict["page"]
            page_xref = doc.page_xref(pno)
            page_height = doc.page_cropbox(pno).height
            to = dest_dict.get('to', pymupdf.Point(72, 36))
            to.y = page_height - to.y
            dest_dict["to"] = to
        action = getDestStr(page_xref, dest_dict)
        if not action.startswith("/A"):
            raise ValueError("bad bookmark dest")
        color = dest_dict.get("color")
        if color:
            color = list(map(float, color))
            if len(color) != 3 or min(color) < 0 or max(color) > 1:
                raise ValueError("bad color value")
        bold = dest_dict.get("bold", False)
        italic = dest_dict.get("italic", False)
        flags = italic + 2 * bold
        collapse = dest_dict.get("collapse")
        return doc._update_toc_item(
            xref,
            action=action[2:],
            title=title,
            color=color,
            flags=flags,
            collapse=collapse,
        )

    if kind == pymupdf.LINK_NONE:  # delete bookmark item
        return doc.del_toc_item(idx)
    if kind is None and title is None:  # treat as no-op
        return None
    if kind is None:  # only update title text
        return doc._update_toc_item(xref, action=None, title=title)

    if kind == pymupdf.LINK_GOTO:
        if pno is None or pno not in range(1, doc.page_count + 1):
            raise ValueError("bad page number")
        page_xref = doc.page_xref(pno - 1)
        page_height = doc.page_cropbox(pno - 1).height
        if to is None:
            to = pymupdf.Point(72, page_height - 36)
        else:
            to = pymupdf.Point(to)
            to.y = page_height - to.y

    ddict = {
        "kind": kind,
        "to": to,
        "uri": uri,
        "page": pno,
        "file": filename,
        "zoom": zoom,
    }
    action = getDestStr(page_xref, ddict)
    if action == "" or not action.startswith("/A"):
        raise ValueError("bad bookmark dest")

    return doc._update_toc_item(xref, action=action[2:], title=title)


def get_area(*args) -> float:
    """Calculate area of rectangle.\nparameter is one of 'px' (default), 'in', 'cm', or 'mm'."""
    rect = args[0]
    if len(args) > 1:
        unit = args[1]
    else:
        unit = "px"
    u = {"px": (1, 1), "in": (1.0, 72.0), "cm": (2.54, 72.0), "mm": (25.4, 72.0)}
    f = (u[unit][0] / u[unit][1]) ** 2
    return f * rect.width * rect.height


def set_metadata(doc: pymupdf.Document, m: dict = None) -> None:
    """Update the PDF /Info object.

    Args:
        m: a dictionary like doc.metadata.
    """
    if not doc.is_pdf:
        raise ValueError("is no PDF")
    if doc.is_closed or doc.is_encrypted:
        raise ValueError("document closed or encrypted")
    if m is None:
        m = {}
    elif type(m) is not dict:
        raise ValueError("bad metadata")
    keymap = {
        "author": "Author",
        "producer": "Producer",
        "creator": "Creator",
        "title": "Title",
        "format": None,
        "encryption": None,
        "creationDate": "CreationDate",
        "modDate": "ModDate",
        "subject": "Subject",
        "keywords": "Keywords",
        "trapped": "Trapped",
    }
    valid_keys = set(keymap.keys())
    diff_set = set(m.keys()).difference(valid_keys)
    if diff_set != set():
        msg = "bad dict key(s): %s" % diff_set
        raise ValueError(msg)

    t, temp = doc.xref_get_key(-1, "Info")
    if t != "xref":
        info_xref = 0
    else:
        info_xref = int(temp.replace("0 R", ""))

    if m == {} and info_xref == 0:  # nothing to do
        return

    if info_xref == 0:  # no prev metadata: get new xref
        info_xref = doc.get_new_xref()
        doc.update_object(info_xref, "<<>>")  # fill it with empty object
        doc.xref_set_key(-1, "Info", "%i 0 R" % info_xref)
    elif m == {}:  # remove existing metadata
        doc.xref_set_key(-1, "Info", "null")
        doc.init_doc()
        return

    for key, val in [(k, v) for k, v in m.items() if keymap[k] is not None]:
        pdf_key = keymap[key]
        if not bool(val) or val in ("none", "null"):
            val = "null"
        else:
            val = pymupdf.get_pdf_str(val)
        doc.xref_set_key(info_xref, pdf_key, val)
    doc.init_doc()
    return


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


def set_toc(
    doc: pymupdf.Document,
    toc: list,
    collapse: int = 1,
) -> int:
    """Create new outline tree (table of contents, TOC).

    Args:
        toc: (list, tuple) each entry must contain level, title, page and
            optionally top margin on the page. None or '()' remove the TOC.
        collapse: (int) collapses entries beyond this level. Zero or None
            shows all entries unfolded.
    Returns:
        the number of inserted items, or the number of removed items respectively.
    """
    if doc.is_closed or doc.is_encrypted:
        raise ValueError("document closed or encrypted")
    if not doc.is_pdf:
        raise ValueError("is no PDF")
    if not toc:  # remove all entries
        return len(doc._delToC())

    # validity checks --------------------------------------------------------
    if type(toc) not in (list, tuple):
        raise ValueError("'toc' must be list or tuple")
    toclen = len(toc)
    page_count = doc.page_count
    t0 = toc[0]
    if type(t0) not in (list, tuple):
        raise ValueError("items must be sequences of 3 or 4 items")
    if t0[0] != 1:
        raise ValueError("hierarchy level of item 0 must be 1")
    for i in list(range(toclen - 1)):
        t1 = toc[i]
        t2 = toc[i + 1]
        if not -1 <= t1[2] <= page_count:
            raise ValueError("row %i: page number out of range" % i)
        if (type(t2) not in (list, tuple)) or len(t2) not in (3, 4):
            raise ValueError("bad row %i" % (i + 1))
        if (type(t2[0]) is not int) or t2[0] < 1:
            raise ValueError("bad hierarchy level in row %i" % (i + 1))
        if t2[0] > t1[0] + 1:
            raise ValueError("bad hierarchy level in row %i" % (i + 1))
    # no formal errors in toc --------------------------------------------------

    # --------------------------------------------------------------------------
    # make a list of xref numbers, which we can use for our TOC entries
    # --------------------------------------------------------------------------
    old_xrefs = doc._delToC()  # del old outlines, get their xref numbers

    # prepare table of xrefs for new bookmarks
    old_xrefs = []
    xref = [0] + old_xrefs
    xref[0] = doc._getOLRootNumber()  # entry zero is outline root xref number
    if toclen > len(old_xrefs):  # too few old xrefs?
        for i in range((toclen - len(old_xrefs))):
            xref.append(doc.get_new_xref())  # acquire new ones

    lvltab = {0: 0}  # to store last entry per hierarchy level

    # ------------------------------------------------------------------------------
    # contains new outline objects as strings - first one is the outline root
    # ------------------------------------------------------------------------------
    olitems = [{"count": 0, "first": -1, "last": -1, "xref": xref[0]}]
    # ------------------------------------------------------------------------------
    # build olitems as a list of PDF-like connected dictionaries
    # ------------------------------------------------------------------------------
    for i in range(toclen):
        o = toc[i]
        lvl = o[0]  # level
        title = pymupdf.get_pdf_str(o[1])  # title
        pno = min(doc.page_count - 1, max(0, o[2] - 1))  # page number
        page_xref = doc.page_xref(pno)
        page_height = doc.page_cropbox(pno).height
        top = pymupdf.Point(72, page_height - 36)
        dest_dict = {"to": top, "kind": pymupdf.LINK_GOTO}  # fall back target
        if o[2] < 0:
            dest_dict["kind"] = pymupdf.LINK_NONE
        if len(o) > 3:  # some target is specified
            if type(o[3]) in (int, float):  # convert a number to a point
                dest_dict["to"] = pymupdf.Point(72, page_height - o[3])
            else:  # if something else, make sure we have a dict
                # We make a copy of o[3] to avoid modifying our caller's data.
                dest_dict = o[3].copy() if type(o[3]) is dict else dest_dict
                if "to" not in dest_dict:  # target point not in dict?
                    dest_dict["to"] = top  # put default in
                else:  # transform target to PDF coordinates
                    page = doc[pno]
                    point = pymupdf.Point(dest_dict["to"])
                    point.y = page.cropbox.height - point.y
                    point = point * page.rotation_matrix
                    dest_dict["to"] = (point.x, point.y)
        d = {}
        d["first"] = -1
        d["count"] = 0
        d["last"] = -1
        d["prev"] = -1
        d["next"] = -1
        d["dest"] = getDestStr(page_xref, dest_dict)
        d["top"] = dest_dict["to"]
        d["title"] = title
        d["parent"] = lvltab[lvl - 1]
        d["xref"] = xref[i + 1]
        d["color"] = dest_dict.get("color")
        d["flags"] = dest_dict.get("italic", 0) + 2 * dest_dict.get("bold", 0)
        lvltab[lvl] = i + 1
        parent = olitems[lvltab[lvl - 1]]  # the parent entry

        if (
            dest_dict.get("collapse") or collapse and lvl > collapse
        ):  # suppress expansion
            parent["count"] -= 1  # make /Count negative
        else:
            parent["count"] += 1  # positive /Count

        if parent["first"] == -1:
            parent["first"] = i + 1
            parent["last"] = i + 1
        else:
            d["prev"] = parent["last"]
            prev = olitems[parent["last"]]
            prev["next"] = i + 1
            parent["last"] = i + 1
        olitems.append(d)

    # ------------------------------------------------------------------------------
    # now create each outline item as a string and insert it in the PDF
    # ------------------------------------------------------------------------------
    for i, ol in enumerate(olitems):
        txt = "<<"
        if ol["count"] != 0:
            txt += "/Count %i" % ol["count"]
        try:
            txt += ol["dest"]
        except Exception:
            # Verbose in PyMuPDF/tests.
            if g_exceptions_verbose >= 2:   pymupdf.exception_info()
            pass
        try:
            if ol["first"] > -1:
                txt += "/First %i 0 R" % xref[ol["first"]]
        except Exception:
            if g_exceptions_verbose >= 2:   pymupdf.exception_info()
            pass
        try:
            if ol["last"] > -1:
                txt += "/Last %i 0 R" % xref[ol["last"]]
        except Exception:
            if g_exceptions_verbose >= 2:   pymupdf.exception_info()
            pass
        try:
            if ol["next"] > -1:
                txt += "/Next %i 0 R" % xref[ol["next"]]
        except Exception:
            # Verbose in PyMuPDF/tests.
            if g_exceptions_verbose >= 2:   pymupdf.exception_info()
            pass
        try:
            if ol["parent"] > -1:
                txt += "/Parent %i 0 R" % xref[ol["parent"]]
        except Exception:
            # Verbose in PyMuPDF/tests.
            if g_exceptions_verbose >= 2:   pymupdf.exception_info()
            pass
        try:
            if ol["prev"] > -1:
                txt += "/Prev %i 0 R" % xref[ol["prev"]]
        except Exception:
            # Verbose in PyMuPDF/tests.
            if g_exceptions_verbose >= 2:   pymupdf.exception_info()
            pass
        try:
            txt += "/Title" + ol["title"]
        except Exception:
            # Verbose in PyMuPDF/tests.
            if g_exceptions_verbose >= 2:   pymupdf.exception_info()
            pass

        if ol.get("color") and len(ol["color"]) == 3:
            txt += f"/C[ {_format_g(tuple(ol['color']))}]"
        if ol.get("flags", 0) > 0:
            txt += "/F %i" % ol["flags"]

        if i == 0:  # special: this is the outline root
            txt += "/Type/Outlines"  # so add the /Type entry
        txt += ">>"
        doc.update_object(xref[i], txt)  # insert the PDF object

    doc.init_doc()
    return toclen


def do_widgets(
    tar: pymupdf.Document,
    src: pymupdf.Document,
    graftmap,
    from_page: int = -1,
    to_page: int = -1,
    start_at: int = -1,
    join_duplicates=0,
) -> None:
    """Insert widgets of copied page range into target PDF.

    Parameter values **must** equal those of method insert_pdf() which
    must have been previously executed.
    """
    if not src.is_form_pdf:  # nothing to do: source PDF has no fields
        return

    def clean_kid_parents(acro_fields):
        """ Make sure all kids have correct "Parent" pointers."""
        for i in range(acro_fields.pdf_array_len()):
            parent = acro_fields.pdf_array_get(i)
            kids = parent.pdf_dict_get(pymupdf.PDF_NAME("Kids"))
            for j in range(kids.pdf_array_len()):
                kid = kids.pdf_array_get(j)
                kid.pdf_dict_put(pymupdf.PDF_NAME("Parent"), parent)

    def join_widgets(pdf, acro_fields, xref1, xref2, name):
        """Called for each pair of widgets having the same name.

        Args:
            pdf: target MuPDF document
            acro_fields: object Root/AcroForm/Fields
            xref1, xref2: widget xrefs having same names
            name: (str) the name

        Result:
            Defined or updated widget parent that points to both widgets.
        """

        def re_target(pdf, acro_fields, xref1, kids1, xref2, kids2):
            """Merge widget in xref2 into "Kids" list of widget xref1.

            Args:
                xref1, kids1: target widget and its "Kids" array.
                xref2, kids2: source wwidget and its "Kids" array (may be empty).
            """
            # make indirect objects from widgets
            w1_ind = mupdf.pdf_new_indirect(pdf, xref1, 0)
            w2_ind = mupdf.pdf_new_indirect(pdf, xref2, 0)
            # find source widget in "Fields" array
            idx = acro_fields.pdf_array_find(w2_ind)
            acro_fields.pdf_array_delete(idx)

            if not kids2.pdf_is_array():  # source widget has no kids
                widget = mupdf.pdf_load_object(pdf, xref2)

                # delete name from widget and insert target as parent
                widget.pdf_dict_del(pymupdf.PDF_NAME("T"))
                widget.pdf_dict_put(pymupdf.PDF_NAME("Parent"), w1_ind)

                # put in target Kids
                kids1.pdf_array_push(w2_ind)
            else:  # copy source kids to target kids
                for i in range(kids2.pdf_array_len()):
                    kid = kids2.pdf_array_get(i)
                    kid.pdf_dict_put(pymupdf.PDF_NAME("Parent"), w1_ind)
                    kid_ind = mupdf.pdf_new_indirect(pdf, kid.pdf_to_num(), 0)
                    kids1.pdf_array_push(kid_ind)

        def new_target(pdf, acro_fields, xref1, w1, xref2, w2, name):
            """Make new "Parent" for two widgets with same name.

            Args:
                xref1, w1: first widget
                xref2, w2: second widget
                name: field name

            Result:
                Both widgets have no "Kids". We create a new object with the
                name and a "Kids" array containing the widgets.
                Original widgets must be removed from AcroForm/Fields.
            """
            # make new "Parent" object
            new = mupdf.pdf_new_dict(pdf, 5)
            new.pdf_dict_put_text_string(pymupdf.PDF_NAME("T"), name)
            kids = new.pdf_dict_put_array(pymupdf.PDF_NAME("Kids"), 2)
            new_obj = mupdf.pdf_add_object(pdf, new)
            new_obj_xref = new_obj.pdf_to_num()
            new_ind = mupdf.pdf_new_indirect(pdf, new_obj_xref, 0)

            # copy over some required source widget properties
            ft = w1.pdf_dict_get(pymupdf.PDF_NAME("FT"))
            w1.pdf_dict_del(pymupdf.PDF_NAME("FT"))
            new_obj.pdf_dict_put(pymupdf.PDF_NAME("FT"), ft)

            aa = w1.pdf_dict_get(pymupdf.PDF_NAME("AA"))
            w1.pdf_dict_del(pymupdf.PDF_NAME("AA"))
            new_obj.pdf_dict_put(pymupdf.PDF_NAME("AA"), aa)

            # remove name field, insert "Parent" field in source widgets
            w1.pdf_dict_del(pymupdf.PDF_NAME("T"))
            w1.pdf_dict_put(pymupdf.PDF_NAME("Parent"), new_ind)
            w2.pdf_dict_del(pymupdf.PDF_NAME("T"))
            w2.pdf_dict_put(pymupdf.PDF_NAME("Parent"), new_ind)

            # put source widgets in "kids" array
            ind1 = mupdf.pdf_new_indirect(pdf, xref1, 0)
            ind2 = mupdf.pdf_new_indirect(pdf, xref2, 0)
            kids.pdf_array_push(ind1)
            kids.pdf_array_push(ind2)

            # remove source widgets from "AcroForm/Fields"
            idx = acro_fields.pdf_array_find(ind1)
            acro_fields.pdf_array_delete(idx)
            idx = acro_fields.pdf_array_find(ind2)
            acro_fields.pdf_array_delete(idx)

            acro_fields.pdf_array_push(new_ind)

        w1 = mupdf.pdf_load_object(pdf, xref1)
        w2 = mupdf.pdf_load_object(pdf, xref2)
        kids1 = w1.pdf_dict_get(pymupdf.PDF_NAME("Kids"))
        kids2 = w2.pdf_dict_get(pymupdf.PDF_NAME("Kids"))

        # check which widget has a suitable "Kids" array
        if kids1.pdf_is_array():
            re_target(pdf, acro_fields, xref1, kids1, xref2, kids2)  # pylint: disable=arguments-out-of-order
        elif kids2.pdf_is_array():
            re_target(pdf, acro_fields, xref2, kids2, xref1, kids1)  # pylint: disable=arguments-out-of-order
        else:
            new_target(pdf, acro_fields, xref1, w1, xref2, w2, name)  # pylint: disable=arguments-out-of-order

    def get_kids(parent, kids_list):
        """Return xref list of leaf kids for a parent.

        Call with an empty list.
        """
        kids = mupdf.pdf_dict_get(parent, pymupdf.PDF_NAME("Kids"))
        if not kids.pdf_is_array():
            return kids_list
        for i in range(kids.pdf_array_len()):
            kid = kids.pdf_array_get(i)
            if mupdf.pdf_is_dict(mupdf.pdf_dict_get(kid, pymupdf.PDF_NAME("Kids"))):
                kids_list = get_kids(kid, kids_list)
            else:
                kids_list.append(kid.pdf_to_num())
        return kids_list

    def kids_xrefs(widget):
        """Get the xref of top "Parent" and the list of leaf widgets."""
        kids_list = []
        parent = mupdf.pdf_dict_get(widget, pymupdf.PDF_NAME("Parent"))
        parent_xref = parent.pdf_to_num()
        if parent_xref == 0:
            return parent_xref, kids_list
        kids_list = get_kids(parent, kids_list)
        return parent_xref, kids_list

    def deduplicate_names(pdf, acro_fields, join_duplicates=False):
        """Handle any widget name duplicates caused by the merge."""
        names = {}  # key is a widget name, value a list of widgets having it.

        # extract all names and widgets in "AcroForm/Fields"
        for i in range(mupdf.pdf_array_len(acro_fields)):
            wobject = mupdf.pdf_array_get(acro_fields, i)
            xref = wobject.pdf_to_num()

            # extract widget name and collect widget(s) using it
            T = mupdf.pdf_dict_get_text_string(wobject, pymupdf.PDF_NAME("T"))
            xrefs = names.get(T, [])
            xrefs.append(xref)
            names[T] = xrefs

        for name, xrefs in names.items():
            if len(xrefs) < 2:
                continue
            xref0, xref1 = xrefs[:2]  # only exactly 2 should occur!
            if join_duplicates:  # combine fields with equal names
                join_widgets(pdf, acro_fields, xref0, xref1, name)
            else:  # make field names unique
                newname = name + f" [{xref1}]"  # append this to the name
                wobject = mupdf.pdf_load_object(pdf, xref1)
                wobject.pdf_dict_put_text_string(pymupdf.PDF_NAME("T"), newname)

        clean_kid_parents(acro_fields)

    def get_acroform(doc):
        """Retrieve the AcroForm dictionary form a PDF."""
        pdf = mupdf.pdf_document_from_fz_document(doc)
        # AcroForm (= central form field info)
        return mupdf.pdf_dict_getp(mupdf.pdf_trailer(pdf), "Root/AcroForm")

    tarpdf = mupdf.pdf_document_from_fz_document(tar)
    srcpdf = mupdf.pdf_document_from_fz_document(src)

    if tar.is_form_pdf:
        # target is a Form PDF, so use it to include source fields
        acro = get_acroform(tar)
        # Important arrays in AcroForm
        acro_fields = acro.pdf_dict_get(pymupdf.PDF_NAME("Fields"))
        tar_co = acro.pdf_dict_get(pymupdf.PDF_NAME("CO"))
        if not tar_co.pdf_is_array():
            tar_co = acro.pdf_dict_put_array(pymupdf.PDF_NAME("CO"), 5)
    else:
        # target is no Form PDF, so copy over source AcroForm
        acro = mupdf.pdf_deep_copy_obj(get_acroform(src))  # make a copy

        # Clear "Fields" and "CO" arrays: will be populated by page fields.
        # This is required to avoid copying unneeded objects.
        acro.pdf_dict_del(pymupdf.PDF_NAME("Fields"))
        acro.pdf_dict_put_array(pymupdf.PDF_NAME("Fields"), 5)
        acro.pdf_dict_del(pymupdf.PDF_NAME("CO"))
        acro.pdf_dict_put_array(pymupdf.PDF_NAME("CO"), 5)

        # Enrich AcroForm for copying to target
        acro_graft = mupdf.pdf_graft_mapped_object(graftmap, acro)

        # Insert AcroForm into target PDF
        acro_tar = mupdf.pdf_add_object(tarpdf, acro_graft)
        acro_fields = acro_tar.pdf_dict_get(pymupdf.PDF_NAME("Fields"))
        tar_co = acro_tar.pdf_dict_get(pymupdf.PDF_NAME("CO"))

        # get its xref and insert it into target catalog
        tar_xref = acro_tar.pdf_to_num()
        acro_tar_ind = mupdf.pdf_new_indirect(tarpdf, tar_xref, 0)
        root = mupdf.pdf_dict_get(mupdf.pdf_trailer(tarpdf), pymupdf.PDF_NAME("Root"))
        root.pdf_dict_put(pymupdf.PDF_NAME("AcroForm"), acro_tar_ind)

    if from_page <= to_page:
        src_range = range(from_page, to_page + 1)
    else:
        src_range = range(from_page, to_page - 1, -1)

    parents = {}  # information about widget parents

    # remove "P" owning page reference from all widgets of all source pages
    for i in src_range:
        src_page = src[i]
        for xref in [
            xref
            for xref, wtype, _ in src_page.annot_xrefs()
            if wtype == pymupdf.PDF_ANNOT_WIDGET  # pylint: disable=no-member
        ]:
            w_obj = mupdf.pdf_load_object(srcpdf, xref)
            w_obj.pdf_dict_del(pymupdf.PDF_NAME("P"))

            # get the widget's parent structure
            parent_xref, old_kids = kids_xrefs(w_obj)
            if parent_xref:
                parents[parent_xref] = {
                    "new_xref": 0,
                    "old_kids": old_kids,
                    "new_kids": [],
                }
    # Copy over Parent widgets first - they are not page-dependent
    for xref in parents.keys():  # pylint: disable=consider-using-dict-items
        parent = mupdf.pdf_load_object(srcpdf, xref)
        parent_graft = mupdf.pdf_graft_mapped_object(graftmap, parent)
        parent_tar = mupdf.pdf_add_object(tarpdf, parent_graft)
        kids_xrefs_new = get_kids(parent_tar, [])
        parent_xref_new = parent_tar.pdf_to_num()
        parent_ind = mupdf.pdf_new_indirect(tarpdf, parent_xref_new, 0)
        acro_fields.pdf_array_push(parent_ind)
        parents[xref]["new_xref"] = parent_xref_new
        parents[xref]["new_kids"] = kids_xrefs_new

    for i in range(len(src_range)):
        # read first copied over page in target
        tar_page = tar[start_at + i]

        # read the original page in the source PDF
        src_page = src[src_range[i]]

        # now walk through source page widgets and copy over
        w_xrefs = [  # widget xrefs of the source page
            xref
            for xref, wtype, _ in src_page.annot_xrefs()
            if wtype == pymupdf.PDF_ANNOT_WIDGET  # pylint: disable=no-member
        ]
        if not w_xrefs:  # no widgets on this source page
            continue

        # convert to formal PDF page
        tar_page_pdf = mupdf.pdf_page_from_fz_page(tar_page)

        # extract annotations array
        tar_annots = mupdf.pdf_dict_get(tar_page_pdf.obj(), pymupdf.PDF_NAME("Annots"))
        if not mupdf.pdf_is_array(tar_annots):
            tar_annots = mupdf.pdf_dict_put_array(
                tar_page_pdf.obj(), pymupdf.PDF_NAME("Annots"), 5
            )

        for xref in w_xrefs:
            w_obj = mupdf.pdf_load_object(srcpdf, xref)

            # check if field takes part in inter-field validations
            is_aac = mupdf.pdf_is_dict(mupdf.pdf_dict_getp(w_obj, "AA/C"))

            # check if parent of widget already in target
            parent_xref = mupdf.pdf_to_num(
                w_obj.pdf_dict_get(pymupdf.PDF_NAME("Parent"))
            )
            if parent_xref == 0:  # parent not in target yet
                w_obj_graft = mupdf.pdf_graft_mapped_object(graftmap, w_obj)
                w_obj_tar = mupdf.pdf_add_object(tarpdf, w_obj_graft)
                tar_xref = w_obj_tar.pdf_to_num()
                w_obj_tar_ind = mupdf.pdf_new_indirect(tarpdf, tar_xref, 0)
                mupdf.pdf_array_push(tar_annots, w_obj_tar_ind)
                mupdf.pdf_array_push(acro_fields, w_obj_tar_ind)
            else:
                parent = parents[parent_xref]
                idx = parent["old_kids"].index(xref)  # search for xref in parent
                tar_xref = parent["new_kids"][idx]
                w_obj_tar_ind = mupdf.pdf_new_indirect(tarpdf, tar_xref, 0)
                mupdf.pdf_array_push(tar_annots, w_obj_tar_ind)

            # Into "AcroForm/CO" if a computation field.
            if is_aac:
                mupdf.pdf_array_push(tar_co, w_obj_tar_ind)

    deduplicate_names(tarpdf, acro_fields, join_duplicates=join_duplicates)

def do_links(
    doc1: pymupdf.Document,
    doc2: pymupdf.Document,
    from_page: int = -1,
    to_page: int = -1,
    start_at: int = -1,
) -> None:
    """Insert links contained in copied page range into destination PDF.

    Parameter values **must** equal those of method insert_pdf(), which must
    have been previously executed.
    """
    #pymupdf.log( 'utils.do_links()')
    # --------------------------------------------------------------------------
    # internal function to create the actual "/Annots" object string
    # --------------------------------------------------------------------------
    def cre_annot(lnk, xref_dst, pno_src, ctm):
        """Create annotation object string for a passed-in link."""

        r = lnk["from"] * ctm  # rect in PDF coordinates
        rect = _format_g(tuple(r))
        if lnk["kind"] == pymupdf.LINK_GOTO:
            txt = pymupdf.annot_skel["goto1"]  # annot_goto
            idx = pno_src.index(lnk["page"])
            p = lnk["to"] * ctm  # target point in PDF coordinates
            annot = txt(xref_dst[idx], p.x, p.y, lnk["zoom"], rect)

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
                    lnk["zoom"],
                    lnk["file"],
                    lnk["file"],
                    rect,
                )
            else:
                txt = pymupdf.annot_skel["gotor2"]  # annot_gotor_n
                to = pymupdf.get_pdf_str(lnk["to"])
                to = to[1:-1]
                f = lnk["file"]
                annot = txt(to, f, rect)

        elif lnk["kind"] == pymupdf.LINK_LAUNCH:
            txt = pymupdf.annot_skel["launch"]  # annot_launch
            annot = txt(lnk["file"], lnk["file"], rect)

        elif lnk["kind"] == pymupdf.LINK_URI:
            txt = pymupdf.annot_skel["uri"]  # annot_uri
            annot = txt(lnk["uri"], rect)

        else:
            annot = ""

        return annot

    # --------------------------------------------------------------------------

    # validate & normalize parameters
    if from_page < 0:
        fp = 0
    elif from_page >= doc2.page_count:
        fp = doc2.page_count - 1
    else:
        fp = from_page

    if to_page < 0 or to_page >= doc2.page_count:
        tp = doc2.page_count - 1
    else:
        tp = to_page

    if start_at < 0:
        raise ValueError("'start_at' must be >= 0")
    sa = start_at

    incr = 1 if fp <= tp else -1  # page range could be reversed

    # lists of source / destination page numbers
    pno_src = list(range(fp, tp + incr, incr))
    pno_dst = [sa + i for i in range(len(pno_src))]

    # lists of source / destination page xrefs
    xref_src = []
    xref_dst = []
    for i in range(len(pno_src)):
        p_src = pno_src[i]
        p_dst = pno_dst[i]
        old_xref = doc2.page_xref(p_src)
        new_xref = doc1.page_xref(p_dst)
        xref_src.append(old_xref)
        xref_dst.append(new_xref)

    # create the links for each copied page in destination PDF
    for i in range(len(xref_src)):
        page_src = doc2[pno_src[i]]  # load source page
        links = page_src.get_links()  # get all its links
        #pymupdf.log( '{pno_src=}')
        #pymupdf.log( '{type(page_src)=}')
        #pymupdf.log( '{page_src=}')
        #pymupdf.log( '{=i len(links)}')
        if len(links) == 0:  # no links there
            page_src = None
            continue
        ctm = ~page_src.transformation_matrix  # calc page transformation matrix
        page_dst = doc1[pno_dst[i]]  # load destination page
        link_tab = []  # store all link definitions here
        for l in links:
            if l["kind"] == pymupdf.LINK_GOTO and (l["page"] not in pno_src):
                continue  # GOTO link target not in copied pages
            annot_text = cre_annot(l, xref_dst, pno_src, ctm)
            if annot_text:
                link_tab.append(annot_text)
        if link_tab != []:
            page_dst._addAnnot_FromString( tuple(link_tab))
    #pymupdf.log( 'utils.do_links() returning.')


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


def delete_widget(page: pymupdf.Page, widget: pymupdf.Widget) -> pymupdf.Widget:
    """Delete widget from page and return the next one."""
    pymupdf.CheckParent(page)
    annot = getattr(widget, "_annot", None)
    if annot is None:
        raise ValueError("bad type: widget")
    nextwidget = widget.next
    page.delete_annot(annot)
    widget._annot.parent = None
    keylist = list(widget.__dict__.keys())
    for key in keylist:
        del widget.__dict__[key]
    return nextwidget


def update_link(page: pymupdf.Page, lnk: dict) -> None:
    """Update a link on the current page."""
    pymupdf.CheckParent(page)
    annot = getLinkText(page, lnk)
    if annot == "":
        raise ValueError("link kind not supported")

    page.parent.update_object(lnk["xref"], annot, page=page)


def insert_link(page: pymupdf.Page, lnk: dict, mark: bool = True) -> None:
    """Insert a new link for the current page."""
    pymupdf.CheckParent(page)
    annot = getLinkText(page, lnk)
    if annot == "":
        raise ValueError("link kind not supported")
    page._addAnnot_FromString((annot,))


def insert_textbox(
    page: pymupdf.Page,
    rect: rect_like,
    buffer: typing.Union[str, list],
    *,
    fontname: str = "helv",
    fontfile: OptStr = None,
    set_simple: int = 0,
    encoding: int = 0,
    fontsize: float = 11,
    lineheight: OptFloat = None,
    color: OptSeq = None,
    fill: OptSeq = None,
    expandtabs: int = 1,
    align: int = 0,
    rotate: int = 0,
    render_mode: int = 0,
    miter_limit: float = 1,
    border_width: float = 0.05,
    morph: OptSeq = None,
    overlay: bool = True,
    stroke_opacity: float = 1,
    fill_opacity: float = 1,
    oc: int = 0,
) -> float:
    """Insert text into a given rectangle.

    Notes:
        Creates a Shape object, uses its same-named method and commits it.
    Parameters:
        rect: (rect-like) area to use for text.
        buffer: text to be inserted
        fontname: a Base-14 font, font name or '/name'
        fontfile: name of a font file
        fontsize: font size
        lineheight: overwrite the font property
        color: RGB color triple
        expandtabs: handles tabulators with string function
        align: left, center, right, justified
        rotate: 0, 90, 180, or 270 degrees
        morph: morph box with a matrix and a fixpoint
        overlay: put text in foreground or background
    Returns:
        unused or deficit rectangle area (float)
    """
    img = page.new_shape()
    rc = img.insert_textbox(
        rect,
        buffer,
        fontsize=fontsize,
        lineheight=lineheight,
        fontname=fontname,
        fontfile=fontfile,
        set_simple=set_simple,
        encoding=encoding,
        color=color,
        fill=fill,
        expandtabs=expandtabs,
        render_mode=render_mode,
        miter_limit=miter_limit,
        border_width=border_width,
        align=align,
        rotate=rotate,
        morph=morph,
        stroke_opacity=stroke_opacity,
        fill_opacity=fill_opacity,
        oc=oc,
    )
    if rc >= 0:
        img.commit(overlay)
    return rc


def insert_text(
    page: pymupdf.Page,
    point: point_like,
    text: typing.Union[str, list],
    *,
    fontsize: float = 11,
    lineheight: OptFloat = None,
    fontname: str = "helv",
    fontfile: OptStr = None,
    set_simple: int = 0,
    encoding: int = 0,
    color: OptSeq = None,
    fill: OptSeq = None,
    border_width: float = 0.05,
    miter_limit: float = 1,
    render_mode: int = 0,
    rotate: int = 0,
    morph: OptSeq = None,
    overlay: bool = True,
    stroke_opacity: float = 1,
    fill_opacity: float = 1,
    oc: int = 0,
):

    img = page.new_shape()
    rc = img.insert_text(
        point,
        text,
        fontsize=fontsize,
        lineheight=lineheight,
        fontname=fontname,
        fontfile=fontfile,
        set_simple=set_simple,
        encoding=encoding,
        color=color,
        fill=fill,
        border_width=border_width,
        render_mode=render_mode,
        miter_limit=miter_limit,
        rotate=rotate,
        morph=morph,
        stroke_opacity=stroke_opacity,
        fill_opacity=fill_opacity,
        oc=oc,
    )
    if rc >= 0:
        img.commit(overlay)
    return rc


def insert_htmlbox(
    page,
    rect,
    text,
    *,
    css=None,
    scale_low=0,
    archive=None,
    rotate=0,
    oc=0,
    opacity=1,
    overlay=True,
) -> float:
    """Insert text with optional HTML tags and stylings into a rectangle.

    Args:
        rect: (rect-like) rectangle into which the text should be placed.
        text: (str) text with optional HTML tags and stylings.
        css: (str) CSS styling commands.
        scale_low: (float) force-fit content by scaling it down. Must be in
            range [0, 1]. If 1, no scaling will take place. If 0, arbitrary
            down-scaling is acceptable. A value of 0.1 would mean that content
            may be scaled down by at most 90%.
        archive: Archive object pointing to locations of used fonts or images
        rotate: (int) rotate the text in the box by a multiple of 90 degrees.
        oc: (int) the xref of an OCG / OCMD (Optional Content).
        opacity: (float) set opacity of inserted content.
        overlay: (bool) put text on top of page content.
    Returns:
        A tuple of floats (spare_height, scale).
        spare_height: -1 if content did not fit, else >= 0. It is the height of the
               unused (still available) rectangle stripe. Positive only if
               scale_min = 1 (no down scaling).
        scale: downscaling factor, 0 < scale <= 1. Set to 0 if spare_height = -1 (no fit).
    """

    # normalize rotation angle
    if not rotate % 90 == 0:
        raise ValueError("bad rotation angle")
    while rotate < 0:
        rotate += 360
    while rotate >= 360:
        rotate -= 360

    if not 0 <= scale_low <= 1:
        raise ValueError("'scale_low' must be in [0, 1]")

    if css is None:
        css = ""

    rect = pymupdf.Rect(rect)
    if rotate in (90, 270):
        temp_rect = pymupdf.Rect(0, 0, rect.height, rect.width)
    else:
        temp_rect = pymupdf.Rect(0, 0, rect.width, rect.height)

    # use a small border by default
    mycss = "body {margin:1px;}" + css  # append user CSS

    # either make a story, or accept a given one
    if isinstance(text, str):  # if a string, convert to a Story
        story = pymupdf.Story(html=text, user_css=mycss, archive=archive)
    elif isinstance(text, pymupdf.Story):
        story = text
    else:
        raise ValueError("'text' must be a string or a Story")
    # ----------------------------------------------------------------
    # Find a scaling factor that lets our story fit in
    # ----------------------------------------------------------------
    scale_max = None if scale_low == 0 else 1 / scale_low

    fit = story.fit_scale(temp_rect, scale_min=1, scale_max=scale_max)
    if not fit.big_enough:  # there was no fit
        return (-1, scale_low)

    filled = fit.filled
    scale = 1 / fit.parameter  # shrink factor

    spare_height = fit.rect.y1 - filled[3]  # unused room at rectangle bottom
    # Note: due to MuPDF's logic this may be negative even for successful fits.
    if scale != 1 or spare_height < 0:  # if scaling occurred, set spare_height to 0
        spare_height = 0

    def rect_function(*args):
        return fit.rect, fit.rect, pymupdf.Identity

    # draw story on temp PDF page
    doc = story.write_with_links(rect_function)

    # Insert opacity if requested.
    # For this, we prepend a command to the /Contents.
    if 0 <= opacity < 1:
        tpage = doc[0]  # load page
        # generate /ExtGstate for the page
        alp0 = tpage._set_opacity(CA=opacity, ca=opacity)
        s = f"/{alp0} gs\n"  # generate graphic state command
        pymupdf.TOOLS._insert_contents(tpage, s.encode(), 0)

    # put result in target page
    page.show_pdf_page(rect, doc, 0, rotate=rotate, oc=oc, overlay=overlay)

    # -------------------------------------------------------------------------
    # re-insert links in target rect (show_pdf_page cannot copy annotations)
    # -------------------------------------------------------------------------
    # scaled center point of fit.rect
    mp1 = (fit.rect.tl + fit.rect.br) / 2 * scale

    # center point of target rect
    mp2 = (rect.tl + rect.br) / 2

    # compute link positioning matrix:
    # - move center of scaled-down fit.rect to (0,0)
    # - rotate
    # - move (0,0) to center of target rect
    mat = (
        pymupdf.Matrix(scale, 0, 0, scale, -mp1.x, -mp1.y)
        * pymupdf.Matrix(-rotate)
        * pymupdf.Matrix(1, 0, 0, 1, mp2.x, mp2.y)
    )

    # copy over links
    for link in doc[0].get_links():
        link["from"] *= mat
        page.insert_link(link)

    return spare_height, scale


def new_page(
    doc: pymupdf.Document,
    pno: int = -1,
    width: float = 595,
    height: float = 842,
) -> pymupdf.Page:
    """Create and return a new page object.

    Args:
        pno: (int) insert before this page. Default: after last page.
        width: (float) page width in points. Default: 595 (ISO A4 width).
        height: (float) page height in points. Default 842 (ISO A4 height).
    Returns:
        A pymupdf.Page object.
    """
    doc._newPage(pno, width=width, height=height)
    return doc[pno]


def insert_page(
    doc: pymupdf.Document,
    pno: int,
    text: typing.Union[str, list, None] = None,
    fontsize: float = 11,
    width: float = 595,
    height: float = 842,
    fontname: str = "helv",
    fontfile: OptStr = None,
    color: OptSeq = (0,),
) -> int:
    """Create a new PDF page and insert some text.

    Notes:
        Function combining pymupdf.Document.new_page() and pymupdf.Page.insert_text().
        For parameter details see these methods.
    """
    page = doc.new_page(pno=pno, width=width, height=height)
    if not bool(text):
        return 0
    rc = page.insert_text(
        (50, 72),
        text,
        fontsize=fontsize,
        fontname=fontname,
        fontfile=fontfile,
        color=color,
    )
    return rc


def draw_line(
    page: pymupdf.Page,
    p1: point_like,
    p2: point_like,
    color: OptSeq = (0,),
    dashes: OptStr = None,
    width: float = 1,
    lineCap: int = 0,
    lineJoin: int = 0,
    overlay: bool = True,
    morph: OptSeq = None,
    stroke_opacity: float = 1,
    fill_opacity: float = 1,
    oc=0,
) -> pymupdf.Point:
    """Draw a line from point p1 to point p2."""
    img = page.new_shape()
    p = img.draw_line(pymupdf.Point(p1), pymupdf.Point(p2))
    img.finish(
        color=color,
        dashes=dashes,
        width=width,
        closePath=False,
        lineCap=lineCap,
        lineJoin=lineJoin,
        morph=morph,
        stroke_opacity=stroke_opacity,
        fill_opacity=fill_opacity,
        oc=oc,
    )
    img.commit(overlay)

    return p


def draw_squiggle(
    page: pymupdf.Page,
    p1: point_like,
    p2: point_like,
    breadth: float = 2,
    color: OptSeq = (0,),
    dashes: OptStr = None,
    width: float = 1,
    lineCap: int = 0,
    lineJoin: int = 0,
    overlay: bool = True,
    morph: OptSeq = None,
    stroke_opacity: float = 1,
    fill_opacity: float = 1,
    oc: int = 0,
) -> pymupdf.Point:
    """Draw a squiggly line from point p1 to point p2."""
    img = page.new_shape()
    p = img.draw_squiggle(pymupdf.Point(p1), pymupdf.Point(p2), breadth=breadth)
    img.finish(
        color=color,
        dashes=dashes,
        width=width,
        closePath=False,
        lineCap=lineCap,
        lineJoin=lineJoin,
        morph=morph,
        stroke_opacity=stroke_opacity,
        fill_opacity=fill_opacity,
        oc=oc,
    )
    img.commit(overlay)

    return p


def draw_zigzag(
    page: pymupdf.Page,
    p1: point_like,
    p2: point_like,
    breadth: float = 2,
    color: OptSeq = (0,),
    dashes: OptStr = None,
    width: float = 1,
    lineCap: int = 0,
    lineJoin: int = 0,
    overlay: bool = True,
    morph: OptSeq = None,
    stroke_opacity: float = 1,
    fill_opacity: float = 1,
    oc: int = 0,
) -> pymupdf.Point:
    """Draw a zigzag line from point p1 to point p2."""
    img = page.new_shape()
    p = img.draw_zigzag(pymupdf.Point(p1), pymupdf.Point(p2), breadth=breadth)
    img.finish(
        color=color,
        dashes=dashes,
        width=width,
        closePath=False,
        lineCap=lineCap,
        lineJoin=lineJoin,
        morph=morph,
        stroke_opacity=stroke_opacity,
        fill_opacity=fill_opacity,
        oc=oc,
    )
    img.commit(overlay)

    return p


def draw_rect(
        page: pymupdf.Page,
        rect: rect_like,
        color: OptSeq = (0,),
        fill: OptSeq = None,
        dashes: OptStr = None,
        width: float = 1,
        lineCap: int = 0,
        lineJoin: int = 0,
        morph: OptSeq = None,
        overlay: bool = True,
        stroke_opacity: float = 1,
        fill_opacity: float = 1,
        oc: int = 0,
        radius=None,
        ) -> pymupdf.Point:
    '''
    Draw a rectangle. See Shape class method for details.
    '''
    img = page.new_shape()
    Q = img.draw_rect(pymupdf.Rect(rect), radius=radius)
    img.finish(
        color=color,
        fill=fill,
        dashes=dashes,
        width=width,
        lineCap=lineCap,
        lineJoin=lineJoin,
        morph=morph,
        stroke_opacity=stroke_opacity,
        fill_opacity=fill_opacity,
        oc=oc,
    )
    img.commit(overlay)

    return Q


def draw_quad(
    page: pymupdf.Page,
    quad: quad_like,
    color: OptSeq = (0,),
    fill: OptSeq = None,
    dashes: OptStr = None,
    width: float = 1,
    lineCap: int = 0,
    lineJoin: int = 0,
    morph: OptSeq = None,
    overlay: bool = True,
    stroke_opacity: float = 1,
    fill_opacity: float = 1,
    oc: int = 0,
) -> pymupdf.Point:
    """Draw a quadrilateral."""
    img = page.new_shape()
    Q = img.draw_quad(pymupdf.Quad(quad))
    img.finish(
        color=color,
        fill=fill,
        dashes=dashes,
        width=width,
        lineCap=lineCap,
        lineJoin=lineJoin,
        morph=morph,
        stroke_opacity=stroke_opacity,
        fill_opacity=fill_opacity,
        oc=oc,
    )
    img.commit(overlay)

    return Q


def draw_polyline(
    page: pymupdf.Page,
    points: list,
    color: OptSeq = (0,),
    fill: OptSeq = None,
    dashes: OptStr = None,
    width: float = 1,
    morph: OptSeq = None,
    lineCap: int = 0,
    lineJoin: int = 0,
    overlay: bool = True,
    closePath: bool = False,
    stroke_opacity: float = 1,
    fill_opacity: float = 1,
    oc: int = 0,
) -> pymupdf.Point:
    """Draw multiple connected line segments."""
    img = page.new_shape()
    Q = img.draw_polyline(points)
    img.finish(
        color=color,
        fill=fill,
        dashes=dashes,
        width=width,
        lineCap=lineCap,
        lineJoin=lineJoin,
        morph=morph,
        closePath=closePath,
        stroke_opacity=stroke_opacity,
        fill_opacity=fill_opacity,
        oc=oc,
    )
    img.commit(overlay)

    return Q


def draw_circle(
    page: pymupdf.Page,
    center: point_like,
    radius: float,
    color: OptSeq = (0,),
    fill: OptSeq = None,
    morph: OptSeq = None,
    dashes: OptStr = None,
    width: float = 1,
    lineCap: int = 0,
    lineJoin: int = 0,
    overlay: bool = True,
    stroke_opacity: float = 1,
    fill_opacity: float = 1,
    oc: int = 0,
) -> pymupdf.Point:
    """Draw a circle given its center and radius."""
    img = page.new_shape()
    Q = img.draw_circle(pymupdf.Point(center), radius)
    img.finish(
        color=color,
        fill=fill,
        dashes=dashes,
        width=width,
        lineCap=lineCap,
        lineJoin=lineJoin,
        morph=morph,
        stroke_opacity=stroke_opacity,
        fill_opacity=fill_opacity,
        oc=oc,
    )
    img.commit(overlay)
    return Q


def draw_oval(
    page: pymupdf.Page,
    rect: typing.Union[rect_like, quad_like],
    color: OptSeq = (0,),
    fill: OptSeq = None,
    dashes: OptStr = None,
    morph: OptSeq = None,
    width: float = 1,
    lineCap: int = 0,
    lineJoin: int = 0,
    overlay: bool = True,
    stroke_opacity: float = 1,
    fill_opacity: float = 1,
    oc: int = 0,
) -> pymupdf.Point:
    """Draw an oval given its containing rectangle or quad."""
    img = page.new_shape()
    Q = img.draw_oval(rect)
    img.finish(
        color=color,
        fill=fill,
        dashes=dashes,
        width=width,
        lineCap=lineCap,
        lineJoin=lineJoin,
        morph=morph,
        stroke_opacity=stroke_opacity,
        fill_opacity=fill_opacity,
        oc=oc,
    )
    img.commit(overlay)

    return Q


def draw_curve(
    page: pymupdf.Page,
    p1: point_like,
    p2: point_like,
    p3: point_like,
    color: OptSeq = (0,),
    fill: OptSeq = None,
    dashes: OptStr = None,
    width: float = 1,
    morph: OptSeq = None,
    closePath: bool = False,
    lineCap: int = 0,
    lineJoin: int = 0,
    overlay: bool = True,
    stroke_opacity: float = 1,
    fill_opacity: float = 1,
    oc: int = 0,
) -> pymupdf.Point:
    """Draw a special Bezier curve from p1 to p3, generating control points on lines p1 to p2 and p2 to p3."""
    img = page.new_shape()
    Q = img.draw_curve(pymupdf.Point(p1), pymupdf.Point(p2), pymupdf.Point(p3))
    img.finish(
        color=color,
        fill=fill,
        dashes=dashes,
        width=width,
        lineCap=lineCap,
        lineJoin=lineJoin,
        morph=morph,
        closePath=closePath,
        stroke_opacity=stroke_opacity,
        fill_opacity=fill_opacity,
        oc=oc,
    )
    img.commit(overlay)

    return Q


def draw_bezier(
    page: pymupdf.Page,
    p1: point_like,
    p2: point_like,
    p3: point_like,
    p4: point_like,
    color: OptSeq = (0,),
    fill: OptSeq = None,
    dashes: OptStr = None,
    width: float = 1,
    morph: OptStr = None,
    closePath: bool = False,
    lineCap: int = 0,
    lineJoin: int = 0,
    overlay: bool = True,
    stroke_opacity: float = 1,
    fill_opacity: float = 1,
    oc: int = 0,
) -> pymupdf.Point:
    """Draw a general cubic Bezier curve from p1 to p4 using control points p2 and p3."""
    img = page.new_shape()
    Q = img.draw_bezier(pymupdf.Point(p1), pymupdf.Point(p2), pymupdf.Point(p3), pymupdf.Point(p4))
    img.finish(
        color=color,
        fill=fill,
        dashes=dashes,
        width=width,
        lineCap=lineCap,
        lineJoin=lineJoin,
        morph=morph,
        closePath=closePath,
        stroke_opacity=stroke_opacity,
        fill_opacity=fill_opacity,
        oc=oc,
    )
    img.commit(overlay)

    return Q


def draw_sector(
    page: pymupdf.Page,
    center: point_like,
    point: point_like,
    beta: float,
    color: OptSeq = (0,),
    fill: OptSeq = None,
    dashes: OptStr = None,
    fullSector: bool = True,
    morph: OptSeq = None,
    width: float = 1,
    closePath: bool = False,
    lineCap: int = 0,
    lineJoin: int = 0,
    overlay: bool = True,
    stroke_opacity: float = 1,
    fill_opacity: float = 1,
    oc: int = 0,
) -> pymupdf.Point:
    """Draw a circle sector given circle center, one arc end point and the angle of the arc.

    Parameters:
        center -- center of circle
        point -- arc end point
        beta -- angle of arc (degrees)
        fullSector -- connect arc ends with center
    """
    img = page.new_shape()
    Q = img.draw_sector(pymupdf.Point(center), pymupdf.Point(point), beta, fullSector=fullSector)
    img.finish(
        color=color,
        fill=fill,
        dashes=dashes,
        width=width,
        lineCap=lineCap,
        lineJoin=lineJoin,
        morph=morph,
        closePath=closePath,
        stroke_opacity=stroke_opacity,
        fill_opacity=fill_opacity,
        oc=oc,
    )
    img.commit(overlay)

    return Q


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


def get_char_widths(
    doc: pymupdf.Document, xref: int, limit: int = 256, idx: int = 0, fontdict: OptDict = None
) -> list:
    """Get list of glyph information of a font.

    Notes:
        Must be provided by its XREF number. If we already dealt with the
        font, it will be recorded in doc.FontInfos. Otherwise we insert an
        entry there.
        Finally we return the glyphs for the font. This is a list of
        (glyph, width) where glyph is an integer controlling the char
        appearance, and width is a float controlling the char's spacing:
        width * fontsize is the actual space.
        For 'simple' fonts, glyph == ord(char) will usually be true.
        Exceptions are 'Symbol' and 'ZapfDingbats'. We are providing data for these directly here.
    """
    fontinfo = pymupdf.CheckFontInfo(doc, xref)
    if fontinfo is None:  # not recorded yet: create it
        if fontdict is None:
            name, ext, stype, asc, dsc = _get_font_properties(doc, xref)
            fontdict = {
                "name": name,
                "type": stype,
                "ext": ext,
                "ascender": asc,
                "descender": dsc,
            }
        else:
            name = fontdict["name"]
            ext = fontdict["ext"]
            stype = fontdict["type"]
            ordering = fontdict["ordering"]
            simple = fontdict["simple"]

        if ext == "":
            raise ValueError("xref is not a font")

        # check for 'simple' fonts
        if stype in ("Type1", "MMType1", "TrueType"):
            simple = True
        else:
            simple = False

        # check for CJK fonts
        if name in ("Fangti", "Ming"):
            ordering = 0
        elif name in ("Heiti", "Song"):
            ordering = 1
        elif name in ("Gothic", "Mincho"):
            ordering = 2
        elif name in ("Dotum", "Batang"):
            ordering = 3
        else:
            ordering = -1

        fontdict["simple"] = simple

        if name == "ZapfDingbats":
            glyphs = pymupdf.zapf_glyphs
        elif name == "Symbol":
            glyphs = pymupdf.symbol_glyphs
        else:
            glyphs = None

        fontdict["glyphs"] = glyphs
        fontdict["ordering"] = ordering
        fontinfo = [xref, fontdict]
        doc.FontInfos.append(fontinfo)
    else:
        fontdict = fontinfo[1]
        glyphs = fontdict["glyphs"]
        simple = fontdict["simple"]
        ordering = fontdict["ordering"]

    if glyphs is None:
        oldlimit = 0
    else:
        oldlimit = len(glyphs)

    mylimit = max(256, limit)

    if mylimit <= oldlimit:
        return glyphs

    if ordering < 0:  # not a CJK font
        glyphs = doc._get_char_widths(
            xref, fontdict["name"], fontdict["ext"], fontdict["ordering"], mylimit, idx
        )
    else:  # CJK fonts use char codes and width = 1
        glyphs = None

    fontdict["glyphs"] = glyphs
    fontinfo[1] = fontdict
    pymupdf.UpdateFontInfo(doc, fontinfo)

    return glyphs


class Shape:
    """Create a new shape."""

    @staticmethod
    def horizontal_angle(C, P):
        """Return the angle to the horizontal for the connection from C to P.
        This uses the arcus sine function and resolves its inherent ambiguity by
        looking up in which quadrant vector S = P - C is located.
        """
        S = pymupdf.Point(P - C).unit  # unit vector 'C' -> 'P'
        alfa = math.asin(abs(S.y))  # absolute angle from horizontal
        if S.x < 0:  # make arcsin result unique
            if S.y <= 0:  # bottom-left
                alfa = -(math.pi - alfa)
            else:  # top-left
                alfa = math.pi - alfa
        else:
            if S.y >= 0:  # top-right
                pass
            else:  # bottom-right
                alfa = -alfa
        return alfa

    def __init__(self, page: pymupdf.Page):
        pymupdf.CheckParent(page)
        self.page = page
        self.doc = page.parent
        if not self.doc.is_pdf:
            raise ValueError("is no PDF")
        self.height = page.mediabox_size.y
        self.width = page.mediabox_size.x
        self.x = page.cropbox_position.x
        self.y = page.cropbox_position.y

        self.pctm = page.transformation_matrix  # page transf. matrix
        self.ipctm = ~self.pctm  # inverted transf. matrix

        self.draw_cont = ""
        self.text_cont = ""
        self.totalcont = ""
        self.last_point = None
        self.rect = None

    def updateRect(self, x):
        if self.rect is None:
            if len(x) == 2:
                self.rect = pymupdf.Rect(x, x)
            else:
                self.rect = pymupdf.Rect(x)

        else:
            if len(x) == 2:
                x = pymupdf.Point(x)
                self.rect.x0 = min(self.rect.x0, x.x)
                self.rect.y0 = min(self.rect.y0, x.y)
                self.rect.x1 = max(self.rect.x1, x.x)
                self.rect.y1 = max(self.rect.y1, x.y)
            else:
                x = pymupdf.Rect(x)
                self.rect.x0 = min(self.rect.x0, x.x0)
                self.rect.y0 = min(self.rect.y0, x.y0)
                self.rect.x1 = max(self.rect.x1, x.x1)
                self.rect.y1 = max(self.rect.y1, x.y1)

    def draw_line(self, p1: point_like, p2: point_like) -> pymupdf.Point:
        """Draw a line between two points."""
        p1 = pymupdf.Point(p1)
        p2 = pymupdf.Point(p2)
        if not (self.last_point == p1):
            self.draw_cont += _format_g(pymupdf.JM_TUPLE(p1 * self.ipctm)) + " m\n"
            self.last_point = p1
            self.updateRect(p1)

        self.draw_cont += _format_g(pymupdf.JM_TUPLE(p2 * self.ipctm)) + " l\n"
        self.updateRect(p2)
        self.last_point = p2
        return self.last_point

    def draw_polyline(self, points: list) -> pymupdf.Point:
        """Draw several connected line segments."""
        for i, p in enumerate(points):
            if i == 0:
                if not (self.last_point == pymupdf.Point(p)):
                    self.draw_cont += _format_g(pymupdf.JM_TUPLE(pymupdf.Point(p) * self.ipctm)) + " m\n"
                    self.last_point = pymupdf.Point(p)
            else:
                self.draw_cont += _format_g(pymupdf.JM_TUPLE(pymupdf.Point(p) * self.ipctm)) + " l\n"
            self.updateRect(p)

        self.last_point = pymupdf.Point(points[-1])
        return self.last_point

    def draw_bezier(
        self,
        p1: point_like,
        p2: point_like,
        p3: point_like,
        p4: point_like,
    ) -> pymupdf.Point:
        """Draw a standard cubic Bezier curve."""
        p1 = pymupdf.Point(p1)
        p2 = pymupdf.Point(p2)
        p3 = pymupdf.Point(p3)
        p4 = pymupdf.Point(p4)
        if not (self.last_point == p1):
            self.draw_cont += _format_g(pymupdf.JM_TUPLE(p1 * self.ipctm)) + " m\n"
        args = pymupdf.JM_TUPLE(list(p2 * self.ipctm) + list(p3 * self.ipctm) + list(p4 * self.ipctm))
        self.draw_cont += _format_g(args) + " c\n"
        self.updateRect(p1)
        self.updateRect(p2)
        self.updateRect(p3)
        self.updateRect(p4)
        self.last_point = p4
        return self.last_point

    def draw_oval(self, tetra: typing.Union[quad_like, rect_like]) -> pymupdf.Point:
        """Draw an ellipse inside a tetrapod."""
        if len(tetra) != 4:
            raise ValueError("invalid arg length")
        if hasattr(tetra[0], "__float__"):
            q = pymupdf.Rect(tetra).quad
        else:
            q = pymupdf.Quad(tetra)

        mt = q.ul + (q.ur - q.ul) * 0.5
        mr = q.ur + (q.lr - q.ur) * 0.5
        mb = q.ll + (q.lr - q.ll) * 0.5
        ml = q.ul + (q.ll - q.ul) * 0.5
        if not (self.last_point == ml):
            self.draw_cont += _format_g(pymupdf.JM_TUPLE(ml * self.ipctm)) + " m\n"
            self.last_point = ml
        self.draw_curve(ml, q.ll, mb)
        self.draw_curve(mb, q.lr, mr)
        self.draw_curve(mr, q.ur, mt)
        self.draw_curve(mt, q.ul, ml)
        self.updateRect(q.rect)
        self.last_point = ml
        return self.last_point

    def draw_circle(self, center: point_like, radius: float) -> pymupdf.Point:
        """Draw a circle given its center and radius."""
        if not radius > pymupdf.EPSILON:
            raise ValueError("radius must be positive")
        center = pymupdf.Point(center)
        p1 = center - (radius, 0)
        return self.draw_sector(center, p1, 360, fullSector=False)

    def draw_curve(
        self,
        p1: point_like,
        p2: point_like,
        p3: point_like,
    ) -> pymupdf.Point:
        """Draw a curve between points using one control point."""
        kappa = 0.55228474983
        p1 = pymupdf.Point(p1)
        p2 = pymupdf.Point(p2)
        p3 = pymupdf.Point(p3)
        k1 = p1 + (p2 - p1) * kappa
        k2 = p3 + (p2 - p3) * kappa
        return self.draw_bezier(p1, k1, k2, p3)

    def draw_sector(
        self,
        center: point_like,
        point: point_like,
        beta: float,
        fullSector: bool = True,
    ) -> pymupdf.Point:
        """Draw a circle sector."""
        center = pymupdf.Point(center)
        point = pymupdf.Point(point)
        l3 = lambda a, b: _format_g((a, b)) + " m\n"
        l4 = lambda a, b, c, d, e, f: _format_g((a, b, c, d, e, f)) + " c\n"
        l5 = lambda a, b: _format_g((a, b)) + " l\n"
        betar = math.radians(-beta)
        w360 = math.radians(math.copysign(360, betar)) * (-1)
        w90 = math.radians(math.copysign(90, betar))
        w45 = w90 / 2
        while abs(betar) > 2 * math.pi:
            betar += w360  # bring angle below 360 degrees
        if not (self.last_point == point):
            self.draw_cont += l3(*pymupdf.JM_TUPLE(point * self.ipctm))
            self.last_point = point
        Q = pymupdf.Point(0, 0)  # just make sure it exists
        C = center
        P = point
        S = P - C  # vector 'center' -> 'point'
        rad = abs(S)  # circle radius

        if not rad > pymupdf.EPSILON:
            raise ValueError("radius must be positive")

        alfa = self.horizontal_angle(center, point)
        while abs(betar) > abs(w90):  # draw 90 degree arcs
            q1 = C.x + math.cos(alfa + w90) * rad
            q2 = C.y + math.sin(alfa + w90) * rad
            Q = pymupdf.Point(q1, q2)  # the arc's end point
            r1 = C.x + math.cos(alfa + w45) * rad / math.cos(w45)
            r2 = C.y + math.sin(alfa + w45) * rad / math.cos(w45)
            R = pymupdf.Point(r1, r2)  # crossing point of tangents
            kappah = (1 - math.cos(w45)) * 4 / 3 / abs(R - Q)
            kappa = kappah * abs(P - Q)
            cp1 = P + (R - P) * kappa  # control point 1
            cp2 = Q + (R - Q) * kappa  # control point 2
            self.draw_cont += l4(*pymupdf.JM_TUPLE(
                list(cp1 * self.ipctm) + list(cp2 * self.ipctm) + list(Q * self.ipctm)
            ))

            betar -= w90  # reduce param angle by 90 deg
            alfa += w90  # advance start angle by 90 deg
            P = Q  # advance to arc end point
        # draw (remaining) arc
        if abs(betar) > 1e-3:  # significant degrees left?
            beta2 = betar / 2
            q1 = C.x + math.cos(alfa + betar) * rad
            q2 = C.y + math.sin(alfa + betar) * rad
            Q = pymupdf.Point(q1, q2)  # the arc's end point
            r1 = C.x + math.cos(alfa + beta2) * rad / math.cos(beta2)
            r2 = C.y + math.sin(alfa + beta2) * rad / math.cos(beta2)
            R = pymupdf.Point(r1, r2)  # crossing point of tangents
            # kappa height is 4/3 of segment height
            kappah = (1 - math.cos(beta2)) * 4 / 3 / abs(R - Q)  # kappa height
            kappa = kappah * abs(P - Q) / (1 - math.cos(betar))
            cp1 = P + (R - P) * kappa  # control point 1
            cp2 = Q + (R - Q) * kappa  # control point 2
            self.draw_cont += l4(*pymupdf.JM_TUPLE(
                list(cp1 * self.ipctm) + list(cp2 * self.ipctm) + list(Q * self.ipctm)
            ))
        if fullSector:
            self.draw_cont += l3(*pymupdf.JM_TUPLE(point * self.ipctm))
            self.draw_cont += l5(*pymupdf.JM_TUPLE(center * self.ipctm))
            self.draw_cont += l5(*pymupdf.JM_TUPLE(Q * self.ipctm))
        self.last_point = Q
        return self.last_point

    def draw_rect(self, rect: rect_like, *, radius=None) -> pymupdf.Point:
        """Draw a rectangle.

        Args:
            radius: if not None, the rectangle will have rounded corners.
                This is the radius of the curvature, given as percentage of
                the rectangle width or height. Valid are values 0 < v <= 0.5.
                For a sequence of two values, the corners will have different
                radii. Otherwise, the percentage will be computed from the
                shorter side. A value of (0.5, 0.5) will draw an ellipse.
        """
        r = pymupdf.Rect(rect)
        if radius is None:  # standard rectangle
            self.draw_cont += _format_g(pymupdf.JM_TUPLE(
                list(r.bl * self.ipctm) + [r.width, r.height]
            )) + " re\n"
            self.updateRect(r)
            self.last_point = r.tl
            return self.last_point
        # rounded corners requested. This requires 1 or 2 values, each
        # with 0 < value <= 0.5
        if hasattr(radius, "__float__"):
            if radius <= 0 or radius > 0.5:
                raise ValueError(f"bad radius value {radius}.")
            d = min(r.width, r.height) * radius
            px = (d, 0)
            py = (0, d)
        elif hasattr(radius, "__len__") and len(radius) == 2:
            rx, ry = radius
            px = (rx * r.width, 0)
            py = (0, ry * r.height)
            if min(rx, ry) <= 0 or max(rx, ry) > 0.5:
                raise ValueError(f"bad radius value {radius}.")
        else:
            raise ValueError(f"bad radius value {radius}.")

        lp = self.draw_line(r.tl + py, r.bl - py)
        lp = self.draw_curve(lp, r.bl, r.bl + px)

        lp = self.draw_line(lp, r.br - px)
        lp = self.draw_curve(lp, r.br, r.br - py)

        lp = self.draw_line(lp, r.tr + py)
        lp = self.draw_curve(lp, r.tr, r.tr - px)

        lp = self.draw_line(lp, r.tl + px)
        self.last_point = self.draw_curve(lp, r.tl, r.tl + py)

        self.updateRect(r)
        return self.last_point

    def draw_quad(self, quad: quad_like) -> pymupdf.Point:
        """Draw a Quad."""
        q = pymupdf.Quad(quad)
        return self.draw_polyline([q.ul, q.ll, q.lr, q.ur, q.ul])

    def draw_zigzag(
        self,
        p1: point_like,
        p2: point_like,
        breadth: float = 2,
    ) -> pymupdf.Point:
        """Draw a zig-zagged line from p1 to p2."""
        p1 = pymupdf.Point(p1)
        p2 = pymupdf.Point(p2)
        S = p2 - p1  # vector start - end
        rad = abs(S)  # distance of points
        cnt = 4 * int(round(rad / (4 * breadth), 0))  # always take full phases
        if cnt < 4:
            raise ValueError("points too close")
        mb = rad / cnt  # revised breadth
        matrix = pymupdf.Matrix(pymupdf.util_hor_matrix(p1, p2))  # normalize line to x-axis
        i_mat = ~matrix  # get original position
        points = []  # stores edges
        for i in range(1, cnt):
            if i % 4 == 1:  # point "above" connection
                p = pymupdf.Point(i, -1) * mb
            elif i % 4 == 3:  # point "below" connection
                p = pymupdf.Point(i, 1) * mb
            else:  # ignore others
                continue
            points.append(p * i_mat)
        self.draw_polyline([p1] + points + [p2])  # add start and end points
        return p2

    def draw_squiggle(
        self,
        p1: point_like,
        p2: point_like,
        breadth=2,
    ) -> pymupdf.Point:
        """Draw a squiggly line from p1 to p2."""
        p1 = pymupdf.Point(p1)
        p2 = pymupdf.Point(p2)
        S = p2 - p1  # vector start - end
        rad = abs(S)  # distance of points
        cnt = 4 * int(round(rad / (4 * breadth), 0))  # always take full phases
        if cnt < 4:
            raise ValueError("points too close")
        mb = rad / cnt  # revised breadth
        matrix = pymupdf.Matrix(pymupdf.util_hor_matrix(p1, p2))  # normalize line to x-axis
        i_mat = ~matrix  # get original position
        k = 2.4142135623765633  # y of draw_curve helper point

        points = []  # stores edges
        for i in range(1, cnt):
            if i % 4 == 1:  # point "above" connection
                p = pymupdf.Point(i, -k) * mb
            elif i % 4 == 3:  # point "below" connection
                p = pymupdf.Point(i, k) * mb
            else:  # else on connection line
                p = pymupdf.Point(i, 0) * mb
            points.append(p * i_mat)

        points = [p1] + points + [p2]
        cnt = len(points)
        i = 0
        while i + 2 < cnt:
            self.draw_curve(points[i], points[i + 1], points[i + 2])
            i += 2
        return p2

    # ==============================================================================
    # Shape.insert_text
    # ==============================================================================
    def insert_text(
        self,
        point: point_like,
        buffer: typing.Union[str, list],
        *,
        fontsize: float = 11,
        lineheight: OptFloat = None,
        fontname: str = "helv",
        fontfile: OptStr = None,
        set_simple: bool = 0,
        encoding: int = 0,
        color: OptSeq = None,
        fill: OptSeq = None,
        render_mode: int = 0,
        border_width: float = 0.05,
        miter_limit: float = 1,
        rotate: int = 0,
        morph: OptSeq = None,
        stroke_opacity: float = 1,
        fill_opacity: float = 1,
        oc: int = 0,
    ) -> int:

        # ensure 'text' is a list of strings, worth dealing with
        if not bool(buffer):
            return 0

        if type(buffer) not in (list, tuple):
            text = buffer.splitlines()
        else:
            text = buffer

        if not len(text) > 0:
            return 0

        point = pymupdf.Point(point)
        try:
            maxcode = max([ord(c) for c in " ".join(text)])
        except Exception:
            pymupdf.exception_info()
            return 0

        # ensure valid 'fontname'
        fname = fontname
        if fname.startswith("/"):
            fname = fname[1:]

        xref = self.page.insert_font(
            fontname=fname, fontfile=fontfile, encoding=encoding, set_simple=set_simple
        )
        fontinfo = pymupdf.CheckFontInfo(self.doc, xref)

        fontdict = fontinfo[1]
        ordering = fontdict["ordering"]
        simple = fontdict["simple"]
        bfname = fontdict["name"]
        ascender = fontdict["ascender"]
        descender = fontdict["descender"]
        if lineheight:
            lheight = fontsize * lineheight
        elif ascender - descender <= 1:
            lheight = fontsize * 1.2
        else:
            lheight = fontsize * (ascender - descender)

        if maxcode > 255:
            glyphs = self.doc.get_char_widths(xref, maxcode + 1)
        else:
            glyphs = fontdict["glyphs"]

        tab = []
        for t in text:
            if simple and bfname not in ("Symbol", "ZapfDingbats"):
                g = None
            else:
                g = glyphs
            tab.append(pymupdf.getTJstr(t, g, simple, ordering))
        text = tab

        color_str = pymupdf.ColorCode(color, "c")
        fill_str = pymupdf.ColorCode(fill, "f")
        if not fill and render_mode == 0:  # ensure fill color when 0 Tr
            fill = color
            fill_str = pymupdf.ColorCode(color, "f")

        morphing = pymupdf.CheckMorph(morph)
        rot = rotate
        if rot % 90 != 0:
            raise ValueError("bad rotate value")

        while rot < 0:
            rot += 360
        rot = rot % 360  # text rotate = 0, 90, 270, 180

        templ1 = lambda a, b, c, d, e, f, g: f"\nq\n{a}{b}BT\n{c}1 0 0 1 {_format_g((d, e))} Tm\n/{f} {_format_g(g)} Tf "
        templ2 = lambda a: f"TJ\n0 -{_format_g(a)} TD\n"
        cmp90 = "0 1 -1 0 0 0 cm\n"  # rotates 90 deg counter-clockwise
        cmm90 = "0 -1 1 0 0 0 cm\n"  # rotates 90 deg clockwise
        cm180 = "-1 0 0 -1 0 0 cm\n"  # rotates by 180 deg.
        height = self.height
        width = self.width

        # setting up for standard rotation directions
        # case rotate = 0
        if morphing:
            m1 = pymupdf.Matrix(1, 0, 0, 1, morph[0].x + self.x, height - morph[0].y - self.y)
            mat = ~m1 * morph[1] * m1
            cm = _format_g(pymupdf.JM_TUPLE(mat)) + " cm\n"
        else:
            cm = ""
        top = height - point.y - self.y  # start of 1st char
        left = point.x + self.x  # start of 1. char
        space = top  # space available
        #headroom = point.y + self.y  # distance to page border
        if rot == 90:
            left = height - point.y - self.y
            top = -point.x - self.x
            cm += cmp90
            space = width - abs(top)
            #headroom = point.x + self.x

        elif rot == 270:
            left = -height + point.y + self.y
            top = point.x + self.x
            cm += cmm90
            space = abs(top)
            #headroom = width - point.x - self.x

        elif rot == 180:
            left = -point.x - self.x
            top = -height + point.y + self.y
            cm += cm180
            space = abs(point.y + self.y)
            #headroom = height - point.y - self.y

        optcont = self.page._get_optional_content(oc)
        if optcont is not None:
            bdc = "/OC /%s BDC\n" % optcont
            emc = "EMC\n"
        else:
            bdc = emc = ""

        alpha = self.page._set_opacity(CA=stroke_opacity, ca=fill_opacity)
        if alpha is None:
            alpha = ""
        else:
            alpha = "/%s gs\n" % alpha
        nres = templ1(bdc, alpha, cm, left, top, fname, fontsize)

        if render_mode > 0:
            nres += "%i Tr " % render_mode
            nres += _format_g(border_width * fontsize) + " w "
            if miter_limit is not None:
                nres += _format_g(miter_limit) + " M "
        if color is not None:
            nres += color_str
        if fill is not None:
            nres += fill_str

        # =========================================================================
        #   start text insertion
        # =========================================================================
        nres += text[0]
        nlines = 1  # set output line counter
        if len(text) > 1:
            nres += templ2(lheight)  # line 1
        else:
            nres += 'TJ'
        for i in range(1, len(text)):
            if space < lheight:
                break  # no space left on page
            if i > 1:
                nres += "\nT* "
            nres += text[i] + 'TJ'
            space -= lheight
            nlines += 1

        nres += "\nET\n%sQ\n" % emc

        # =========================================================================
        #   end of text insertion
        # =========================================================================
        # update the /Contents object
        self.text_cont += nres
        return nlines

    # ==============================================================================
    # Shape.insert_textbox
    # ==============================================================================
    def insert_textbox(
        self,
        rect: rect_like,
        buffer: typing.Union[str, list],
        *,
        fontname: OptStr = "helv",
        fontfile: OptStr = None,
        fontsize: float = 11,
        lineheight: OptFloat = None,
        set_simple: bool = 0,
        encoding: int = 0,
        color: OptSeq = None,
        fill: OptSeq = None,
        expandtabs: int = 1,
        border_width: float = 0.05,
        miter_limit: float = 1,
        align: int = 0,
        render_mode: int = 0,
        rotate: int = 0,
        morph: OptSeq = None,
        stroke_opacity: float = 1,
        fill_opacity: float = 1,
        oc: int = 0,
    ) -> float:
        """Insert text into a given rectangle.

        Args:
            rect -- the textbox to fill
            buffer -- text to be inserted
            fontname -- a Base-14 font, font name or '/name'
            fontfile -- name of a font file
            fontsize -- font size
            lineheight -- overwrite the font property
            color -- RGB stroke color triple
            fill -- RGB fill color triple
            render_mode -- text rendering control
            border_width -- thickness of glyph borders as percentage of fontsize
            expandtabs -- handles tabulators with string function
            align -- left, center, right, justified
            rotate -- 0, 90, 180, or 270 degrees
            morph -- morph box with a matrix and a fixpoint
        Returns:
            unused or deficit rectangle area (float)
        """
        rect = pymupdf.Rect(rect)
        if rect.is_empty or rect.is_infinite:
            raise ValueError("text box must be finite and not empty")

        color_str = pymupdf.ColorCode(color, "c")
        fill_str = pymupdf.ColorCode(fill, "f")
        if fill is None and render_mode == 0:  # ensure fill color for 0 Tr
            fill = color
            fill_str = pymupdf.ColorCode(color, "f")

        optcont = self.page._get_optional_content(oc)
        if optcont is not None:
            bdc = "/OC /%s BDC\n" % optcont
            emc = "EMC\n"
        else:
            bdc = emc = ""

        # determine opacity / transparency
        alpha = self.page._set_opacity(CA=stroke_opacity, ca=fill_opacity)
        if alpha is None:
            alpha = ""
        else:
            alpha = "/%s gs\n" % alpha

        if rotate % 90 != 0:
            raise ValueError("rotate must be multiple of 90")

        rot = rotate
        while rot < 0:
            rot += 360
        rot = rot % 360

        # is buffer worth of dealing with?
        if not bool(buffer):
            return rect.height if rot in (0, 180) else rect.width

        cmp90 = "0 1 -1 0 0 0 cm\n"  # rotates counter-clockwise
        cmm90 = "0 -1 1 0 0 0 cm\n"  # rotates clockwise
        cm180 = "-1 0 0 -1 0 0 cm\n"  # rotates by 180 deg.
        height = self.height

        fname = fontname
        if fname.startswith("/"):
            fname = fname[1:]

        xref = self.page.insert_font(
            fontname=fname, fontfile=fontfile, encoding=encoding, set_simple=set_simple
        )
        fontinfo = pymupdf.CheckFontInfo(self.doc, xref)

        fontdict = fontinfo[1]
        ordering = fontdict["ordering"]
        simple = fontdict["simple"]
        glyphs = fontdict["glyphs"]
        bfname = fontdict["name"]
        ascender = fontdict["ascender"]
        descender = fontdict["descender"]

        if lineheight:
            lheight_factor = lineheight
        elif ascender - descender <= 1:
            lheight_factor = 1.2
        else:
            lheight_factor = ascender - descender
        lheight = fontsize * lheight_factor

        # create a list from buffer, split into its lines
        if type(buffer) in (list, tuple):
            t0 = "\n".join(buffer)
        else:
            t0 = buffer

        maxcode = max([ord(c) for c in t0])
        # replace invalid char codes for simple fonts
        if simple and maxcode > 255:
            t0 = "".join([c if ord(c) < 256 else "?" for c in t0])

        t0 = t0.splitlines()

        glyphs = self.doc.get_char_widths(xref, maxcode + 1)
        if simple and bfname not in ("Symbol", "ZapfDingbats"):
            tj_glyphs = None
        else:
            tj_glyphs = glyphs

        # ----------------------------------------------------------------------
        # calculate pixel length of a string
        # ----------------------------------------------------------------------
        def pixlen(x):
            """Calculate pixel length of x."""
            if ordering < 0:
                return sum([glyphs[ord(c)][1] for c in x]) * fontsize
            else:
                return len(x) * fontsize

        # ---------------------------------------------------------------------

        if ordering < 0:
            blen = glyphs[32][1] * fontsize  # pixel size of space character
        else:
            blen = fontsize

        text = ""  # output buffer

        if pymupdf.CheckMorph(morph):
            m1 = pymupdf.Matrix(
                1, 0, 0, 1, morph[0].x + self.x, self.height - morph[0].y - self.y
            )
            mat = ~m1 * morph[1] * m1
            cm = _format_g(pymupdf.JM_TUPLE(mat)) + " cm\n"
        else:
            cm = ""

        # ---------------------------------------------------------------------
        # adjust for text orientation / rotation
        # ---------------------------------------------------------------------
        progr = 1  # direction of line progress
        c_pnt = pymupdf.Point(0, fontsize * ascender)  # used for line progress
        if rot == 0:  # normal orientation
            point = rect.tl + c_pnt  # line 1 is 'lheight' below top
            maxwidth = rect.width  # pixels available in one line
            maxheight = rect.height  # available text height

        elif rot == 90:  # rotate counter clockwise
            c_pnt = pymupdf.Point(fontsize * ascender, 0)  # progress in x-direction
            point = rect.bl + c_pnt  # line 1 'lheight' away from left
            maxwidth = rect.height  # pixels available in one line
            maxheight = rect.width  # available text height
            cm += cmp90

        elif rot == 180:  # text upside down
            # progress upwards in y direction
            c_pnt = -pymupdf.Point(0, fontsize * ascender)
            point = rect.br + c_pnt  # line 1 'lheight' above bottom
            maxwidth = rect.width  # pixels available in one line
            progr = -1  # subtract lheight for next line
            maxheight =rect.height  # available text height
            cm += cm180

        else:  # rotate clockwise (270 or -90)
            # progress from right to left
            c_pnt = -pymupdf.Point(fontsize * ascender, 0)
            point = rect.tr + c_pnt  # line 1 'lheight' left of right
            maxwidth = rect.height  # pixels available in one line
            progr = -1  # subtract lheight for next line
            maxheight = rect.width  # available text height
            cm += cmm90

        # =====================================================================
        # line loop
        # =====================================================================
        just_tab = []  # 'justify' indicators per line

        for i, line in enumerate(t0):
            line_t = line.expandtabs(expandtabs).split(" ")  # split into words
            num_words = len(line_t)
            lbuff = ""  # init line buffer
            rest = maxwidth  # available line pixels
            # =================================================================
            # word loop
            # =================================================================
            for j in range(num_words):
                word = line_t[j]
                pl_w = pixlen(word)  # pixel len of word
                if rest >= pl_w:  # does it fit on the line?
                    lbuff += word + " "  # yes, append word
                    rest -= pl_w + blen  # update available line space
                    continue  # next word

                # word doesn't fit - output line (if not empty)
                if lbuff:
                    lbuff = lbuff.rstrip() + "\n"  # line full, append line break
                    text += lbuff  # append to total text
                    just_tab.append(True)  # can align-justify

                lbuff = ""  # re-init line buffer
                rest = maxwidth  # re-init avail. space

                if pl_w <= maxwidth:  # word shorter than 1 line?
                    lbuff = word + " "  # start the line with it
                    rest = maxwidth - pl_w - blen  # update free space
                    continue

                # long word: split across multiple lines - char by char ...
                if len(just_tab) > 0:
                    just_tab[-1] = False  # cannot align-justify
                for c in word:
                    if pixlen(lbuff) <= maxwidth - pixlen(c):
                        lbuff += c
                    else:  # line full
                        lbuff += "\n"  # close line
                        text += lbuff  # append to text
                        just_tab.append(False)  # cannot align-justify
                        lbuff = c  # start new line with this char

                lbuff += " "  # finish long word
                rest = maxwidth - pixlen(lbuff)  # long word stored

            if lbuff:  # unprocessed line content?
                text += lbuff.rstrip()  # append to text
                just_tab.append(False)  # cannot align-justify

            if i < len(t0) - 1:  # not the last line?
                text += "\n"  # insert line break

        # compute used part of the textbox
        if text.endswith("\n"):
            text = text[:-1]
        lb_count = text.count("\n") + 1  # number of lines written

        # text height = line count * line height plus one descender value
        text_height = lheight * lb_count - descender * fontsize

        more = text_height - maxheight  # difference to height limit
        if more > pymupdf.EPSILON:  # landed too much outside rect
            return (-1) * more  # return deficit, don't output

        more = abs(more)
        if more < pymupdf.EPSILON:
            more = 0  # don't bother with epsilons
        nres = "\nq\n%s%sBT\n" % (bdc, alpha) + cm  # initialize output buffer
        templ = lambda a, b, c, d: f"1 0 0 1 {_format_g((a, b))} Tm /{c} {_format_g(d)} Tf "
        # center, right, justify: output each line with its own specifics
        text_t = text.splitlines()  # split text in lines again
        just_tab[-1] = False  # never justify last line
        for i, t in enumerate(text_t):
            spacing = 0
            pl = maxwidth - pixlen(t)  # length of empty line part
            pnt = point + c_pnt * (i * lheight_factor)  # text start of line
            if align == 1:  # center: right shift by half width
                if rot in (0, 180):
                    pnt = pnt + pymupdf.Point(pl / 2, 0) * progr
                else:
                    pnt = pnt - pymupdf.Point(0, pl / 2) * progr
            elif align == 2:  # right: right shift by full width
                if rot in (0, 180):
                    pnt = pnt + pymupdf.Point(pl, 0) * progr
                else:
                    pnt = pnt - pymupdf.Point(0, pl) * progr
            elif align == 3:  # justify
                spaces = t.count(" ")  # number of spaces in line
                if spaces > 0 and just_tab[i]:  # if any, and we may justify
                    spacing = pl / spaces  # make every space this much larger
                else:
                    spacing = 0  # keep normal space length
            top = height - pnt.y - self.y
            left = pnt.x + self.x
            if rot == 90:
                left = height - pnt.y - self.y
                top = -pnt.x - self.x
            elif rot == 270:
                left = -height + pnt.y + self.y
                top = pnt.x + self.x
            elif rot == 180:
                left = -pnt.x - self.x
                top = -height + pnt.y + self.y

            nres += templ(left, top, fname, fontsize)

            if render_mode > 0:
                nres += "%i Tr " % render_mode
                nres += _format_g(border_width * fontsize) + " w "
                if miter_limit is not None:
                    nres += _format_g(miter_limit) + " M "

            if align == 3:
                nres += _format_g(spacing) + " Tw "

            if color is not None:
                nres += color_str
            if fill is not None:
                nres += fill_str
            nres += "%sTJ\n" % pymupdf.getTJstr(t, tj_glyphs, simple, ordering)

        nres += "ET\n%sQ\n" % emc

        self.text_cont += nres
        self.updateRect(rect)
        return more

    def finish(
        self,
        width: float = 1,
        color: OptSeq = (0,),
        fill: OptSeq = None,
        lineCap: int = 0,
        lineJoin: int = 0,
        dashes: OptStr = None,
        even_odd: bool = False,
        morph: OptSeq = None,
        closePath: bool = True,
        fill_opacity: float = 1,
        stroke_opacity: float = 1,
        oc: int = 0,
    ) -> None:
        """Finish the current drawing segment.

        Notes:
            Apply colors, opacity, dashes, line style and width, or
            morphing. Also whether to close the path
            by connecting last to first point.
        """
        if self.draw_cont == "":  # treat empty contents as no-op
            return

        if width == 0:  # border color makes no sense then
            color = None
        elif color is None:  # vice versa
            width = 0
        # if color == None and fill == None:
        #     raise ValueError("at least one of 'color' or 'fill' must be given")
        color_str = pymupdf.ColorCode(color, "c")  # ensure proper color string
        fill_str = pymupdf.ColorCode(fill, "f")  # ensure proper fill string

        optcont = self.page._get_optional_content(oc)
        if optcont is not None:
            self.draw_cont = "/OC /%s BDC\n" % optcont + self.draw_cont
            emc = "EMC\n"
        else:
            emc = ""

        alpha = self.page._set_opacity(CA=stroke_opacity, ca=fill_opacity)
        if alpha is not None:
            self.draw_cont = "/%s gs\n" % alpha + self.draw_cont

        if width != 1 and width != 0:
            self.draw_cont += _format_g(width) + " w\n"

        if lineCap != 0:
            self.draw_cont = "%i J\n" % lineCap + self.draw_cont
        if lineJoin != 0:
            self.draw_cont = "%i j\n" % lineJoin + self.draw_cont

        if dashes not in (None, "", "[] 0"):
            self.draw_cont = "%s d\n" % dashes + self.draw_cont

        if closePath:
            self.draw_cont += "h\n"
            self.last_point = None

        if color is not None:
            self.draw_cont += color_str

        if fill is not None:
            self.draw_cont += fill_str
            if color is not None:
                if not even_odd:
                    self.draw_cont += "B\n"
                else:
                    self.draw_cont += "B*\n"
            else:
                if not even_odd:
                    self.draw_cont += "f\n"
                else:
                    self.draw_cont += "f*\n"
        else:
            self.draw_cont += "S\n"

        self.draw_cont += emc
        if pymupdf.CheckMorph(morph):
            m1 = pymupdf.Matrix(
                1, 0, 0, 1, morph[0].x + self.x, self.height - morph[0].y - self.y
            )
            mat = ~m1 * morph[1] * m1
            self.draw_cont = _format_g(pymupdf.JM_TUPLE(mat)) + " cm\n" + self.draw_cont

        self.totalcont += "\nq\n" + self.draw_cont + "Q\n"
        self.draw_cont = ""
        self.last_point = None
        return

    def commit(self, overlay: bool = True) -> None:
        """Update the page's /Contents object with Shape data.

        The argument controls whether data appear in foreground (default)
        or background.
        """
        pymupdf.CheckParent(self.page)  # doc may have died meanwhile
        self.totalcont += self.text_cont
        self.totalcont = self.totalcont.encode()

        if self.totalcont:
            if overlay:
                self.page.wrap_contents()  # ensure a balanced graphics state
            # make /Contents object with dummy stream
            xref = pymupdf.TOOLS._insert_contents(self.page, b" ", overlay)
            # update it with potential compression
            self.doc.update_stream(xref, self.totalcont)

        self.last_point = None  # clean up ...
        self.rect = None  #
        self.draw_cont = ""  # for potential ...
        self.text_cont = ""  # ...
        self.totalcont = ""  # re-use


def apply_redactions(
    page: pymupdf.Page, images: int = 2, graphics: int = 1, text: int = 0
) -> bool:
    """Apply the redaction annotations of the page.

    Args:
        page: the PDF page.
        images:
              0 - ignore images
              1 - remove all overlapping images
              2 - blank out overlapping image parts
              3 - remove image unless invisible
        graphics:
              0 - ignore graphics
              1 - remove graphics if contained in rectangle
              2 - remove all overlapping graphics
        text:
              0 - remove text
              1 - ignore text
    """

    def center_rect(annot_rect, new_text, font, fsize):
        """Calculate minimal sub-rectangle for the overlay text.

        Notes:
            Because 'insert_textbox' supports no vertical text centering,
            we calculate an approximate number of lines here and return a
            sub-rect with smaller height, which should still be sufficient.
        Args:
            annot_rect: the annotation rectangle
            new_text: the text to insert.
            font: the fontname. Must be one of the CJK or Base-14 set, else
                the rectangle is returned unchanged.
            fsize: the fontsize
        Returns:
            A rectangle to use instead of the annot rectangle.
        """
        if not new_text or annot_rect.width <= pymupdf.EPSILON:
            return annot_rect
        try:
            text_width = pymupdf.get_text_length(new_text, font, fsize)
        except (ValueError, mupdf.FzErrorBase):  # unsupported font
            if g_exceptions_verbose:
                pymupdf.exception_info()
            return annot_rect
        line_height = fsize * 1.2
        limit = annot_rect.width
        h = math.ceil(text_width / limit) * line_height  # estimate rect height
        if h >= annot_rect.height:
            return annot_rect
        r = annot_rect
        y = (annot_rect.tl.y + annot_rect.bl.y - h) * 0.5
        r.y0 = y
        return r

    pymupdf.CheckParent(page)
    doc = page.parent
    if doc.is_encrypted or doc.is_closed:
        raise ValueError("document closed or encrypted")
    if not doc.is_pdf:
        raise ValueError("is no PDF")

    redact_annots = []  # storage of annot values
    for annot in page.annots(
        types=(pymupdf.PDF_ANNOT_REDACT,)  # pylint: disable=no-member
    ):
        # loop redactions
        redact_annots.append(annot._get_redact_values())  # save annot values

    if redact_annots == []:  # any redactions on this page?
        return False  # no redactions

    rc = page._apply_redactions(text, images, graphics)  # call MuPDF
    if not rc:  # should not happen really
        raise ValueError("Error applying redactions.")

    # now write replacement text in old redact rectangles
    shape = page.new_shape()
    for redact in redact_annots:
        annot_rect = redact["rect"]
        fill = redact["fill"]
        if fill:
            shape.draw_rect(annot_rect)  # colorize the rect background
            shape.finish(fill=fill, color=fill)
        if "text" in redact.keys():  # if we also have text
            new_text = redact["text"]
            align = redact.get("align", 0)
            fname = redact["fontname"]
            fsize = redact["fontsize"]
            color = redact["text_color"]
            # try finding vertical centered sub-rect
            trect = center_rect(annot_rect, new_text, fname, fsize)

            rc = -1
            while rc < 0 and fsize >= 4:  # while not enough room
                # (re-) try insertion
                rc = shape.insert_textbox(
                    trect,
                    new_text,
                    fontname=fname,
                    fontsize=fsize,
                    color=color,
                    align=align,
                )
                fsize -= 0.5  # reduce font if unsuccessful
    shape.commit()  # append new contents object
    return True


# ------------------------------------------------------------------------------
# Remove potentially sensitive data from a PDF. Similar to the Adobe
# Acrobat 'sanitize' function
# ------------------------------------------------------------------------------
def scrub(
    doc: pymupdf.Document,
    attached_files: bool = True,
    clean_pages: bool = True,
    embedded_files: bool = True,
    hidden_text: bool = True,
    javascript: bool = True,
    metadata: bool = True,
    redactions: bool = True,
    redact_images: int = 0,
    remove_links: bool = True,
    reset_fields: bool = True,
    reset_responses: bool = True,
    thumbnails: bool = True,
    xml_metadata: bool = True,
) -> None:
    def remove_hidden(cont_lines):
        """Remove hidden text from a PDF page.

        Args:
            cont_lines: list of lines with /Contents content. Should have status
                from after page.cleanContents().

        Returns:
            List of /Contents lines from which hidden text has been removed.

        Notes:
            The input must have been created after the page's /Contents object(s)
            have been cleaned with page.cleanContents(). This ensures a standard
            formatting: one command per line, single spaces between operators.
            This allows for drastic simplification of this code.
        """
        out_lines = []  # will return this
        in_text = False  # indicate if within BT/ET object
        suppress = False  # indicate text suppression active
        make_return = False
        for line in cont_lines:
            if line == b"BT":  # start of text object
                in_text = True  # switch on
                out_lines.append(line)  # output it
                continue
            if line == b"ET":  # end of text object
                in_text = False  # switch off
                out_lines.append(line)  # output it
                continue
            if line == b"3 Tr":  # text suppression operator
                suppress = True  # switch on
                make_return = True
                continue
            if line[-2:] == b"Tr" and line[0] != b"3":
                suppress = False  # text rendering changed
                out_lines.append(line)
                continue
            if line == b"Q":  # unstack command also switches off
                suppress = False
                out_lines.append(line)
                continue
            if suppress and in_text:  # suppress hidden lines
                continue
            out_lines.append(line)
        if make_return:
            return out_lines
        else:
            return None

    if not doc.is_pdf:  # only works for PDF
        raise ValueError("is no PDF")
    if doc.is_encrypted or doc.is_closed:
        raise ValueError("closed or encrypted doc")

    if not clean_pages:
        hidden_text = False
        redactions = False

    if metadata:
        doc.set_metadata({})  # remove standard metadata

    for page in doc:
        if reset_fields:
            # reset form fields (widgets)
            for widget in page.widgets():
                widget.reset()

        if remove_links:
            links = page.get_links()  # list of all links on page
            for link in links:  # remove all links
                page.delete_link(link)

        found_redacts = False
        for annot in page.annots():
            if annot.type[0] == mupdf.PDF_ANNOT_FILE_ATTACHMENT and attached_files:
                annot.update_file(buffer=b" ")  # set file content to empty
            if reset_responses:
                annot.delete_responses()
            if annot.type[0] == pymupdf.PDF_ANNOT_REDACT:  # pylint: disable=no-member
                found_redacts = True

        if redactions and found_redacts:
            page.apply_redactions(images=redact_images)

        if not (clean_pages or hidden_text):
            continue  # done with the page

        page.clean_contents()
        if not page.get_contents():
            continue
        if hidden_text:
            xref = page.get_contents()[0]  # only one b/o cleaning!
            cont = doc.xref_stream(xref)
            cont_lines = remove_hidden(cont.splitlines())  # remove hidden text
            if cont_lines:  # something was actually removed
                cont = b"\n".join(cont_lines)
                doc.update_stream(xref, cont)  # rewrite the page /Contents

        if thumbnails:  # remove page thumbnails?
            if doc.xref_get_key(page.xref, "Thumb")[0] != "null":
                doc.xref_set_key(page.xref, "Thumb", "null")

    # pages are scrubbed, now perform document-wide scrubbing
    # remove embedded files
    if embedded_files:
        for name in doc.embfile_names():
            doc.embfile_del(name)

    if xml_metadata:
        doc.del_xml_metadata()
    if not (xml_metadata or javascript):
        xref_limit = 0
    else:
        xref_limit = doc.xref_length()
    for xref in range(1, xref_limit):
        if not doc.xref_object(xref):
            msg = "bad xref %i - clean PDF before scrubbing" % xref
            raise ValueError(msg)
        if javascript and doc.xref_get_key(xref, "S")[1] == "/JavaScript":
            # a /JavaScript action object
            obj = "<</S/JavaScript/JS()>>"  # replace with a null JavaScript
            doc.update_object(xref, obj)  # update this object
            continue  # no further handling

        if not xml_metadata:
            continue

        if doc.xref_get_key(xref, "Type")[1] == "/Metadata":
            # delete any metadata object directly
            doc.update_object(xref, "<<>>")
            doc.update_stream(xref, b"deleted", new=True)
            continue

        if doc.xref_get_key(xref, "Metadata")[0] != "null":
            doc.xref_set_key(xref, "Metadata", "null")


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

def fill_textbox(
    writer: pymupdf.TextWriter,
    rect: rect_like,
    text: typing.Union[str, list],
    pos: point_like = None,
    font: typing.Optional[pymupdf.Font] = None,
    fontsize: float = 11,
    lineheight: OptFloat = None,
    align: int = 0,
    warn: bool = None,
    right_to_left: bool = False,
    small_caps: bool = False,
) -> tuple:
    """Fill a rectangle with text.

    Args:
        writer: pymupdf.TextWriter object (= "self")
        rect: rect-like to receive the text.
        text: string or list/tuple of strings.
        pos: point-like start position of first word.
        font: pymupdf.Font object (default pymupdf.Font('helv')).
        fontsize: the fontsize.
        lineheight: overwrite the font property
        align: (int) 0 = left, 1 = center, 2 = right, 3 = justify
        warn: (bool) text overflow action: none, warn, or exception
        right_to_left: (bool) indicate right-to-left language.
    """
    rect = pymupdf.Rect(rect)
    if rect.is_empty:
        raise ValueError("fill rect must not empty.")
    if type(font) is not pymupdf.Font:
        font = pymupdf.Font("helv")

    def textlen(x):
        """Return length of a string."""
        return font.text_length(
            x, fontsize=fontsize, small_caps=small_caps
        )  # abbreviation

    def char_lengths(x):
        """Return list of single character lengths for a string."""
        return font.char_lengths(x, fontsize=fontsize, small_caps=small_caps)

    def append_this(pos, text):
        ret = writer.append(
                pos, text, font=font, fontsize=fontsize, small_caps=small_caps
                )
        return ret

    tolerance = fontsize * 0.2  # extra distance to left border
    space_len = textlen(" ")
    std_width = rect.width - tolerance
    std_start = rect.x0 + tolerance

    def norm_words(width, words):
        """Cut any word in pieces no longer than 'width'."""
        nwords = []
        word_lengths = []
        for w in words:
            wl_lst = char_lengths(w)
            wl = sum(wl_lst)
            if wl <= width:  # nothing to do - copy over
                nwords.append(w)
                word_lengths.append(wl)
                continue

            # word longer than rect width - split it in parts
            n = len(wl_lst)
            while n > 0:
                wl = sum(wl_lst[:n])
                if wl <= width:
                    nwords.append(w[:n])
                    word_lengths.append(wl)
                    w = w[n:]
                    wl_lst = wl_lst[n:]
                    n = len(wl_lst)
                else:
                    n -= 1
        return nwords, word_lengths

    def output_justify(start, line):
        """Justified output of a line."""
        # ignore leading / trailing / multiple spaces
        words = [w for w in line.split(" ") if w != ""]
        nwords = len(words)
        if nwords == 0:
            return
        if nwords == 1:  # single word cannot be justified
            append_this(start, words[0])
            return
        tl = sum([textlen(w) for w in words])  # total word lengths
        gaps = nwords - 1  # number of word gaps
        gapl = (std_width - tl) / gaps  # width of each gap
        for w in words:
            _, lp = append_this(start, w)  # output one word
            start.x = lp.x + gapl  # next start at word end plus gap
        return

    asc = font.ascender
    dsc = font.descender
    if not lineheight:
        if asc - dsc <= 1:
            lheight = 1.2
        else:
            lheight = asc - dsc
    else:
        lheight = lineheight

    LINEHEIGHT = fontsize * lheight  # effective line height
    width = std_width  # available horizontal space

    # starting point of text
    if pos is not None:
        pos = pymupdf.Point(pos)
    else:  # default is just below rect top-left
        pos = rect.tl + (tolerance, fontsize * asc)
    if pos not in rect:
        raise ValueError("Text must start in rectangle.")

    # calculate displacement factor for alignment
    if align == pymupdf.TEXT_ALIGN_CENTER:
        factor = 0.5
    elif align == pymupdf.TEXT_ALIGN_RIGHT:
        factor = 1.0
    else:
        factor = 0

    # split in lines if just a string was given
    if type(text) is str:
        textlines = text.splitlines()
    else:
        textlines = []
        for line in text:
            textlines.extend(line.splitlines())

    max_lines = int((rect.y1 - pos.y) / LINEHEIGHT) + 1

    new_lines = []  # the final list of textbox lines
    no_justify = []  # no justify for these line numbers
    for i, line in enumerate(textlines):
        if line in ("", " "):
            new_lines.append((line, space_len))
            width = rect.width - tolerance
            no_justify.append((len(new_lines) - 1))
            continue
        if i == 0:
            width = rect.x1 - pos.x
        else:
            width = rect.width - tolerance

        if right_to_left:  # reverses Arabic / Hebrew text front to back
            line = writer.clean_rtl(line)
        tl = textlen(line)
        if tl <= width:  # line short enough
            new_lines.append((line, tl))
            no_justify.append((len(new_lines) - 1))
            continue

        # we need to split the line in fitting parts
        words = line.split(" ")  # the words in the line

        # cut in parts any words that are longer than rect width
        words, word_lengths = norm_words(width, words)

        n = len(words)
        while True:
            line0 = " ".join(words[:n])
            wl = sum(word_lengths[:n]) + space_len * (n - 1)
            if wl <= width:
                new_lines.append((line0, wl))
                words = words[n:]
                word_lengths = word_lengths[n:]
                n = len(words)
                line0 = None
            else:
                n -= 1

            if len(words) == 0:
                break
            assert n

    # -------------------------------------------------------------------------
    # List of lines created. Each item is (text, tl), where 'tl' is the PDF
    # output length (float) and 'text' is the text. Except for justified text,
    # this is output-ready.
    # -------------------------------------------------------------------------
    nlines = len(new_lines)
    if nlines > max_lines:
        msg = "Only fitting %i of %i lines." % (max_lines, nlines)
        if warn is None:
            pass
        elif warn:
            pymupdf.message("Warning: " + msg)
        else:
            raise ValueError(msg)

    start = pymupdf.Point()
    no_justify += [len(new_lines) - 1]  # no justifying of last line
    for i in range(max_lines):
        try:
            line, tl = new_lines.pop(0)
        except IndexError:
            if g_exceptions_verbose >= 2:   pymupdf.exception_info()
            break

        if right_to_left:  # Arabic, Hebrew
            line = "".join(reversed(line))

        if i == 0:  # may have different start for first line
            start = pos

        if align == pymupdf.TEXT_ALIGN_JUSTIFY and i not in no_justify and tl < std_width:
            output_justify(start, line)
            start.x = std_start
            start.y += LINEHEIGHT
            continue

        if i > 0 or pos.x == std_start:  # left, center, right alignments
            start.x += (width - tl) * factor

        append_this(start, line)
        start.x = std_start
        start.y += LINEHEIGHT

    return new_lines  # return non-written lines


# ------------------------------------------------------------------------
# Optional Content functions
# ------------------------------------------------------------------------
def get_oc(doc: pymupdf.Document, xref: int) -> int:
    """Return optional content object xref for an image or form xobject.

    Args:
        xref: (int) xref number of an image or form xobject.
    """
    if doc.is_closed or doc.is_encrypted:
        raise ValueError("document close or encrypted")
    t, name = doc.xref_get_key(xref, "Subtype")
    if t != "name" or name not in ("/Image", "/Form"):
        raise ValueError("bad object type at xref %i" % xref)
    t, oc = doc.xref_get_key(xref, "OC")
    if t != "xref":
        return 0
    rc = int(oc.replace("0 R", ""))
    return rc


def set_oc(doc: pymupdf.Document, xref: int, oc: int) -> None:
    """Attach optional content object to image or form xobject.

    Args:
        xref: (int) xref number of an image or form xobject
        oc: (int) xref number of an OCG or OCMD
    """
    if doc.is_closed or doc.is_encrypted:
        raise ValueError("document close or encrypted")
    t, name = doc.xref_get_key(xref, "Subtype")
    if t != "name" or name not in ("/Image", "/Form"):
        raise ValueError("bad object type at xref %i" % xref)
    if oc > 0:
        t, name = doc.xref_get_key(oc, "Type")
        if t != "name" or name not in ("/OCG", "/OCMD"):
            raise ValueError("bad object type at xref %i" % oc)
    if oc == 0 and "OC" in doc.xref_get_keys(xref):
        doc.xref_set_key(xref, "OC", "null")
        return None
    doc.xref_set_key(xref, "OC", "%i 0 R" % oc)
    return None


def set_ocmd(
    doc: pymupdf.Document,
    xref: int = 0,
    ocgs: typing.Union[list, None] = None,
    policy: OptStr = None,
    ve: typing.Union[list, None] = None,
) -> int:
    """Create or update an OCMD object in a PDF document.

    Args:
        xref: (int) 0 for creating a new object, otherwise update existing one.
        ocgs: (list) OCG xref numbers, which shall be subject to 'policy'.
        policy: one of 'AllOn', 'AllOff', 'AnyOn', 'AnyOff' (any casing).
        ve: (list) visibility expression. Use instead of 'ocgs' with 'policy'.

    Returns:
        Xref of the created or updated OCMD.
    """

    all_ocgs = set(doc.get_ocgs().keys())

    def ve_maker(ve):
        if type(ve) not in (list, tuple) or len(ve) < 2:
            raise ValueError("bad 've' format: %s" % ve)
        if ve[0].lower() not in ("and", "or", "not"):
            raise ValueError("bad operand: %s" % ve[0])
        if ve[0].lower() == "not" and len(ve) != 2:
            raise ValueError("bad 've' format: %s" % ve)
        item = "[/%s" % ve[0].title()
        for x in ve[1:]:
            if type(x) is int:
                if x not in all_ocgs:
                    raise ValueError("bad OCG %i" % x)
                item += " %i 0 R" % x
            else:
                item += " %s" % ve_maker(x)
        item += "]"
        return item

    text = "<</Type/OCMD"

    if ocgs and type(ocgs) in (list, tuple):  # some OCGs are provided
        s = set(ocgs).difference(all_ocgs)  # contains illegal xrefs
        if s != set():
            msg = "bad OCGs: %s" % s
            raise ValueError(msg)
        text += "/OCGs[" + " ".join(map(lambda x: "%i 0 R" % x, ocgs)) + "]"

    if policy:
        policy = str(policy).lower()
        pols = {
            "anyon": "AnyOn",
            "allon": "AllOn",
            "anyoff": "AnyOff",
            "alloff": "AllOff",
        }
        if policy not in ("anyon", "allon", "anyoff", "alloff"):
            raise ValueError("bad policy: %s" % policy)
        text += "/P/%s" % pols[policy]

    if ve:
        text += "/VE%s" % ve_maker(ve)

    text += ">>"

    # make new object or replace old OCMD (check type first)
    if xref == 0:
        xref = doc.get_new_xref()
    elif "/Type/OCMD" not in doc.xref_object(xref, compressed=True):
        raise ValueError("bad xref or not an OCMD")
    doc.update_object(xref, text)
    return xref


def get_ocmd(doc: pymupdf.Document, xref: int) -> dict:
    """Return the definition of an OCMD (optional content membership dictionary).

    Recognizes PDF dict keys /OCGs (PDF array of OCGs), /P (policy string) and
    /VE (visibility expression, PDF array). Via string manipulation, this
    info is converted to a Python dictionary with keys "xref", "ocgs", "policy"
    and "ve" - ready to recycle as input for 'set_ocmd()'.
    """

    if xref not in range(doc.xref_length()):
        raise ValueError("bad xref")
    text = doc.xref_object(xref, compressed=True)
    if "/Type/OCMD" not in text:
        raise ValueError("bad object type")
    textlen = len(text)

    p0 = text.find("/OCGs[")  # look for /OCGs key
    p1 = text.find("]", p0)
    if p0 < 0 or p1 < 0:  # no OCGs found
        ocgs = None
    else:
        ocgs = text[p0 + 6 : p1].replace("0 R", " ").split()
        ocgs = list(map(int, ocgs))

    p0 = text.find("/P/")  # look for /P policy key
    if p0 < 0:
        policy = None
    else:
        p1 = text.find("ff", p0)
        if p1 < 0:
            p1 = text.find("on", p0)
        if p1 < 0:  # some irregular syntax
            raise ValueError("bad object at xref")
        else:
            policy = text[p0 + 3 : p1 + 2]

    p0 = text.find("/VE[")  # look for /VE visibility expression key
    if p0 < 0:  # no visibility expression found
        ve = None
    else:
        lp = rp = 0  # find end of /VE by finding last ']'.
        p1 = p0
        while lp < 1 or lp != rp:
            p1 += 1
            if not p1 < textlen:  # some irregular syntax
                raise ValueError("bad object at xref")
            if text[p1] == "[":
                lp += 1
            if text[p1] == "]":
                rp += 1
        # p1 now positioned at the last "]"
        ve = text[p0 + 3 : p1 + 1]  # the PDF /VE array
        ve = (
            ve.replace("/And", '"and",')
            .replace("/Not", '"not",')
            .replace("/Or", '"or",')
        )
        ve = ve.replace(" 0 R]", "]").replace(" 0 R", ",").replace("][", "],[")
        import json
        try:
            ve = json.loads(ve)
        except Exception:
            pymupdf.exception_info()
            pymupdf.message(f"bad /VE key: {ve!r}")
            raise
    return {"xref": xref, "ocgs": ocgs, "policy": policy, "ve": ve}


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


def get_label(page):
    """Return the label for this PDF page.

    Args:
        page: page object.
    Returns:
        The label (str) of the page. Errors return an empty string.
    """
    # Jorj McKie, 2021-01-06

    labels = page.parent._get_page_labels()
    if not labels:
        return ""
    labels.sort()
    return get_label_pno(page.number, labels)


def get_page_numbers(doc, label, only_one=False):
    """Return a list of page numbers with the given label.

    Args:
        doc: PDF document object (resp. 'self').
        label: (str) label.
        only_one: (bool) stop searching after first hit.
    Returns:
        List of page numbers having this label.
    """
    # Jorj McKie, 2021-01-06

    numbers = []
    if not label:
        return numbers
    labels = doc._get_page_labels()
    if labels == []:
        return numbers
    for i in range(doc.page_count):
        plabel = get_label_pno(i, labels)
        if plabel == label:
            numbers.append(i)
            if only_one:
                break
    return numbers


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


def get_page_labels(doc):
    """Return page label definitions in PDF document.

    Args:
        doc: PDF document (resp. 'self').
    Returns:
        A list of dictionaries with the following format:
        {'startpage': int, 'prefix': str, 'style': str, 'firstpagenum': int}.
    """
    # Jorj McKie, 2021-01-10
    return [rule_dict(item) for item in doc._get_page_labels()]


def set_page_labels(doc, labels):
    """Add / replace page label definitions in PDF document.

    Args:
        doc: PDF document (resp. 'self').
        labels: list of label dictionaries like:
        {'startpage': int, 'prefix': str, 'style': str, 'firstpagenum': int},
        as returned by get_page_labels().
    """
    # William Chapman, 2021-01-06

    def create_label_str(label):
        """Convert Python label dict to corresponding PDF rule string.

        Args:
            label: (dict) build rule for the label.
        Returns:
            PDF label rule string wrapped in "<<", ">>".
        """
        s = "%i<<" % label["startpage"]
        if label.get("prefix", "") != "":
            s += "/P(%s)" % label["prefix"]
        if label.get("style", "") != "":
            s += "/S/%s" % label["style"]
        if label.get("firstpagenum", 1) > 1:
            s += "/St %i" % label["firstpagenum"]
        s += ">>"
        return s

    def create_nums(labels):
        """Return concatenated string of all labels rules.

        Args:
            labels: (list) dictionaries as created by function 'rule_dict'.
        Returns:
            PDF compatible string for page label definitions, ready to be
            enclosed in PDF array 'Nums[...]'.
        """
        labels.sort(key=lambda x: x["startpage"])
        s = "".join([create_label_str(label) for label in labels])
        return s

    doc._set_page_labels(create_nums(labels))


# End of Page Label Code -------------------------------------------------


def has_links(doc: pymupdf.Document) -> bool:
    """Check whether there are links on any page."""
    if doc.is_closed:
        raise ValueError("document closed")
    if not doc.is_pdf:
        raise ValueError("is no PDF")
    for i in range(doc.page_count):
        for item in doc.page_annot_xrefs(i):
            if item[1] == pymupdf.PDF_ANNOT_LINK:  # pylint: disable=no-member
                return True
    return False


def has_annots(doc: pymupdf.Document) -> bool:
    """Check whether there are annotations on any page."""
    if doc.is_closed:
        raise ValueError("document closed")
    if not doc.is_pdf:
        raise ValueError("is no PDF")
    for i in range(doc.page_count):
        for item in doc.page_annot_xrefs(i):
            # pylint: disable=no-member
            if not (item[1] == pymupdf.PDF_ANNOT_LINK or item[1] == pymupdf.PDF_ANNOT_WIDGET):  # pylint: disable=no-member
                return True
    return False


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


# -------------------------------------------------------------------
# Building font subsets using fontTools
# -------------------------------------------------------------------
def subset_fonts(doc: pymupdf.Document, verbose: bool = False, fallback: bool = False) -> OptInt:
    """Build font subsets in a PDF.

    Eligible fonts are potentially replaced by smaller versions. Page text is
    NOT rewritten and thus should retain properties like being hidden or
    controlled by optional content.

    This method by default uses MuPDF's own internal feature to create subset
    fonts. As this is a new function, errors may still occur. In this case,
    please fall back to using the previous version by using "fallback=True".
    Fallback mode requires the external package 'fontTools'.

    Args:
        fallback: use the older deprecated implementation.
        verbose: only used by fallback mode.

    Returns:
        The new MuPDF-based code returns None.  The deprecated fallback
        mode returns 0 if there are no fonts to subset.  Otherwise, it
        returns the decrease in fontsize (the difference in fontsize),
        measured in bytes.
    """
    # Font binaries: -  "buffer" -> (names, xrefs, (unicodes, glyphs))
    # An embedded font is uniquely defined by its fontbuffer only. It may have
    # multiple names and xrefs.
    # Once the sets of used unicodes and glyphs are known, we compute a
    # smaller version of the buffer user package fontTools.

    if not fallback:  # by default use MuPDF function
        pdf = mupdf.pdf_document_from_fz_document(doc)
        mupdf.pdf_subset_fonts2(pdf, list(range(doc.page_count)))
        return

    font_buffers = {}

    def get_old_widths(xref):
        """Retrieve old font '/W' and '/DW' values."""
        df = doc.xref_get_key(xref, "DescendantFonts")
        if df[0] != "array":  # only handle xref specifications
            return None, None
        df_xref = int(df[1][1:-1].replace("0 R", ""))
        widths = doc.xref_get_key(df_xref, "W")
        if widths[0] != "array":  # no widths key found
            widths = None
        else:
            widths = widths[1]
        dwidths = doc.xref_get_key(df_xref, "DW")
        if dwidths[0] != "int":
            dwidths = None
        else:
            dwidths = dwidths[1]
        return widths, dwidths

    def set_old_widths(xref, widths, dwidths):
        """Restore the old '/W' and '/DW' in subsetted font.

        If either parameter is None or evaluates to False, the corresponding
        dictionary key will be set to null.
        """
        df = doc.xref_get_key(xref, "DescendantFonts")
        if df[0] != "array":  # only handle xref specs
            return None
        df_xref = int(df[1][1:-1].replace("0 R", ""))
        if (type(widths) is not str or not widths) and doc.xref_get_key(df_xref, "W")[
            0
        ] != "null":
            doc.xref_set_key(df_xref, "W", "null")
        else:
            doc.xref_set_key(df_xref, "W", widths)
        if (type(dwidths) is not str or not dwidths) and doc.xref_get_key(
            df_xref, "DW"
        )[0] != "null":
            doc.xref_set_key(df_xref, "DW", "null")
        else:
            doc.xref_set_key(df_xref, "DW", dwidths)
        return None

    def set_subset_fontname(new_xref):
        """Generate a name prefix to tag a font as subset.

        We use a random generator to select 6 upper case ASCII characters.
        The prefixed name must be put in the font xref as the "/BaseFont" value
        and in the FontDescriptor object as the '/FontName' value.
        """
        # The following generates a prefix like 'ABCDEF+'
        import random
        import string
        prefix = "".join(random.choices(tuple(string.ascii_uppercase), k=6)) + "+"
        font_str = doc.xref_object(new_xref, compressed=True)
        font_str = font_str.replace("/BaseFont/", "/BaseFont/" + prefix)
        df = doc.xref_get_key(new_xref, "DescendantFonts")
        if df[0] == "array":
            df_xref = int(df[1][1:-1].replace("0 R", ""))
            fd = doc.xref_get_key(df_xref, "FontDescriptor")
            if fd[0] == "xref":
                fd_xref = int(fd[1].replace("0 R", ""))
                fd_str = doc.xref_object(fd_xref, compressed=True)
                fd_str = fd_str.replace("/FontName/", "/FontName/" + prefix)
                doc.update_object(fd_xref, fd_str)
        doc.update_object(new_xref, font_str)

    def build_subset(buffer, unc_set, gid_set):
        """Build font subset using fontTools.

        Args:
            buffer: (bytes) the font given as a binary buffer.
            unc_set: (set) required glyph ids.
        Returns:
            Either None if subsetting is unsuccessful or the subset font buffer.
        """
        try:
            import fontTools.subset as fts
        except ImportError:
            if g_exceptions_verbose:    pymupdf.exception_info()
            pymupdf.message("This method requires fontTools to be installed.")
            raise
        import tempfile
        with tempfile.TemporaryDirectory() as tmp_dir:
            oldfont_path = f"{tmp_dir}/oldfont.ttf"
            newfont_path = f"{tmp_dir}/newfont.ttf"
            uncfile_path = f"{tmp_dir}/uncfile.txt"
            args = [
                oldfont_path,
                "--retain-gids",
                f"--output-file={newfont_path}",
                "--layout-features=*",
                "--passthrough-tables",
                "--ignore-missing-glyphs",
                "--ignore-missing-unicodes",
                "--symbol-cmap",
            ]

            # store glyph ids or unicodes as file
            with open(f"{tmp_dir}/uncfile.txt", "w", encoding='utf8') as unc_file:
                if 0xFFFD in unc_set:  # error unicode exists -> use glyphs
                    args.append(f"--gids-file={uncfile_path}")
                    gid_set.add(189)
                    unc_list = list(gid_set)
                    for unc in unc_list:
                        unc_file.write("%i\n" % unc)
                else:
                    args.append(f"--unicodes-file={uncfile_path}")
                    unc_set.add(255)
                    unc_list = list(unc_set)
                    for unc in unc_list:
                        unc_file.write("%04x\n" % unc)

            # store fontbuffer as a file
            with open(oldfont_path, "wb") as fontfile:
                fontfile.write(buffer)
            try:
                os.remove(newfont_path)  # remove old file
            except Exception:
                pass
            try:  # invoke fontTools subsetter
                fts.main(args)
                font = pymupdf.Font(fontfile=newfont_path)
                new_buffer = font.buffer  # subset font binary
                if font.glyph_count == 0:  # intercept empty font
                    new_buffer = None
            except Exception:
                pymupdf.exception_info()
                new_buffer = None
        return new_buffer

    def repl_fontnames(doc):
        """Populate 'font_buffers'.

        For each font candidate, store its xref and the list of names
        by which PDF text may refer to it (there may be multiple).
        """

        def norm_name(name):
            """Recreate font name that contains PDF hex codes.

            E.g. #20 -> space, chr(32)
            """
            while "#" in name:
                p = name.find("#")
                c = int(name[p + 1 : p + 3], 16)
                name = name.replace(name[p : p + 3], chr(c))
            return name

        def get_fontnames(doc, item):
            """Return a list of fontnames for an item of page.get_fonts().

            There may be multiple names e.g. for Type0 fonts.
            """
            fontname = item[3]
            names = [fontname]
            fontname = doc.xref_get_key(item[0], "BaseFont")[1][1:]
            fontname = norm_name(fontname)
            if fontname not in names:
                names.append(fontname)
            descendents = doc.xref_get_key(item[0], "DescendantFonts")
            if descendents[0] != "array":
                return names
            descendents = descendents[1][1:-1]
            if descendents.endswith(" 0 R"):
                xref = int(descendents[:-4])
                descendents = doc.xref_object(xref, compressed=True)
            p1 = descendents.find("/BaseFont")
            if p1 >= 0:
                p2 = descendents.find("/", p1 + 1)
                p1 = min(descendents.find("/", p2 + 1), descendents.find(">>", p2 + 1))
                fontname = descendents[p2 + 1 : p1]
                fontname = norm_name(fontname)
                if fontname not in names:
                    names.append(fontname)
            return names

        for i in range(doc.page_count):
            for f in doc.get_page_fonts(i, full=True):
                font_xref = f[0]  # font xref
                font_ext = f[1]  # font file extension
                basename = f[3]  # font basename

                if font_ext not in (  # skip if not supported by fontTools
                    "otf",
                    "ttf",
                    "woff",
                    "woff2",
                ):
                    continue
                # skip fonts which already are subsets
                if len(basename) > 6 and basename[6] == "+":
                    continue

                extr = doc.extract_font(font_xref)
                fontbuffer = extr[-1]
                names = get_fontnames(doc, f)
                name_set, xref_set, subsets = font_buffers.get(
                    fontbuffer, (set(), set(), (set(), set()))
                )
                xref_set.add(font_xref)
                for name in names:
                    name_set.add(name)
                font = pymupdf.Font(fontbuffer=fontbuffer)
                name_set.add(font.name)
                del font
                font_buffers[fontbuffer] = (name_set, xref_set, subsets)

    def find_buffer_by_name(name):
        for buffer, (name_set, _, _) in font_buffers.items():
            if name in name_set:
                return buffer
        return None

    # -----------------
    # main function
    # -----------------
    repl_fontnames(doc)  # populate font information
    if not font_buffers:  # nothing found to do
        if verbose:
            pymupdf.message(f'No fonts to subset.')
        return 0

    old_fontsize = 0
    new_fontsize = 0
    for fontbuffer in font_buffers.keys():
        old_fontsize += len(fontbuffer)

    # Scan page text for usage of subsettable fonts
    for page in doc:
        # go through the text and extend set of used glyphs by font
        # we use a modified MuPDF trace device, which delivers us glyph ids.
        for span in page.get_texttrace():
            if type(span) is not dict:  # skip useless information
                continue
            fontname = span["font"][:33]  # fontname for the span
            buffer = find_buffer_by_name(fontname)
            if buffer is None:
                continue
            name_set, xref_set, (set_ucs, set_gid) = font_buffers[buffer]
            for c in span["chars"]:
                set_ucs.add(c[0])  # unicode
                set_gid.add(c[1])  # glyph id
            font_buffers[buffer] = (name_set, xref_set, (set_ucs, set_gid))

    # build the font subsets
    for old_buffer, (name_set, xref_set, subsets) in font_buffers.items():
        new_buffer = build_subset(old_buffer, subsets[0], subsets[1])
        fontname = list(name_set)[0]
        if new_buffer is None or len(new_buffer) >= len(old_buffer):
            # subset was not created or did not get smaller
            if verbose:
                pymupdf.message(f'Cannot subset {fontname!r}.')
            continue
        if verbose:
            pymupdf.message(f"Built subset of font {fontname!r}.")
        val = doc._insert_font(fontbuffer=new_buffer)  # store subset font in PDF
        new_xref = val[0]  # get its xref
        set_subset_fontname(new_xref)  # tag fontname as subset font
        font_str = doc.xref_object(  # get its object definition
            new_xref,
            compressed=True,
        )
        # walk through the original font xrefs and replace each by the subset def
        for font_xref in xref_set:
            # we need the original '/W' and '/DW' width values
            width_table, def_width = get_old_widths(font_xref)
            # ... and replace original font definition at xref with it
            doc.update_object(font_xref, font_str)
            # now copy over old '/W' and '/DW' values
            if width_table or def_width:
                set_old_widths(font_xref, width_table, def_width)
        # 'new_xref' remains unused in the PDF and must be removed
        # by garbage collection.
        new_fontsize += len(new_buffer)

    return old_fontsize - new_fontsize


# -------------------------------------------------------------------
# Copy XREF object to another XREF
# -------------------------------------------------------------------
def xref_copy(doc: pymupdf.Document, source: int, target: int, *, keep: list = None) -> None:
    """Copy a PDF dictionary object to another one given their xref numbers.

    Args:
        doc: PDF document object
        source: source xref number
        target: target xref number, the xref must already exist
        keep: an optional list of 1st level keys in target that should not be
              removed before copying.
    Notes:
        This works similar to the copy() method of dictionaries in Python. The
        source may be a stream object.
    """
    if doc.xref_is_stream(source):
        # read new xref stream, maintaining compression
        stream = doc.xref_stream_raw(source)
        doc.update_stream(
            target,
            stream,
            compress=False,  # keeps source compression
            new=True,  # in case target is no stream
        )

    # empty the target completely, observe exceptions
    if keep is None:
        keep = []
    for key in doc.xref_get_keys(target):
        if key in keep:
            continue
        doc.xref_set_key(target, key, "null")
    # copy over all source dict items
    for key in doc.xref_get_keys(source):
        item = doc.xref_get_key(source, key)
        doc.xref_set_key(target, key, item[1])
