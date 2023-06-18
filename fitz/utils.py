# ------------------------------------------------------------------------
# Copyright 2020-2022, Harald Lieder, mailto:harald.lieder@outlook.com
# License: GNU AFFERO GPL 3.0, https://www.gnu.org/licenses/agpl-3.0.html
#
# Part of "PyMuPDF", a Python binding for "MuPDF" (http://mupdf.com), a
# lightweight PDF, XPS, and E-book viewer, renderer and toolkit which is
# maintained and developed by Artifex Software, Inc. https://artifex.com.
# ------------------------------------------------------------------------
import io
import json
import math
import os
import random
import string
import tempfile
import typing
import warnings

from fitz import *

TESSDATA_PREFIX = os.getenv("TESSDATA_PREFIX")
point_like = "point_like"
rect_like = "rect_like"
matrix_like = "matrix_like"
quad_like = "quad_like"
AnyType = typing.Any
OptInt = typing.Union[int, None]
OptFloat = typing.Optional[float]
OptStr = typing.Optional[str]
OptDict = typing.Optional[dict]
OptBytes = typing.Optional[typing.ByteString]
OptSeq = typing.Optional[typing.Sequence]

"""
This is a collection of functions to extend PyMupdf.
"""


def write_text(page: Page, **kwargs) -> None:
    """Write the text of one or more TextWriter objects.

    Args:
        rect: target rectangle. If None, the union of the text writers is used.
        writers: one or more TextWriter objects.
        overlay: put in foreground or background.
        keep_proportion: maintain aspect ratio of rectangle sides.
        rotate: arbitrary rotation angle.
        oc: the xref of an optional content object
    """
    if type(page) is not Page:
        raise ValueError("bad page parameter")
    s = {
        k
        for k in kwargs.keys()
        if k
        not in {
            "rect",
            "writers",
            "opacity",
            "color",
            "overlay",
            "keep_proportion",
            "rotate",
            "oc",
        }
    }
    if s != set():
        raise ValueError("bad keywords: " + str(s))

    rect = kwargs.get("rect")
    writers = kwargs.get("writers")
    opacity = kwargs.get("opacity")
    color = kwargs.get("color")
    overlay = bool(kwargs.get("overlay", True))
    keep_proportion = bool(kwargs.get("keep_proportion", True))
    rotate = int(kwargs.get("rotate", 0))
    oc = int(kwargs.get("oc", 0))

    if not writers:
        raise ValueError("need at least one TextWriter")
    if type(writers) is TextWriter:
        if rotate == 0 and rect is None:
            writers.write_text(page, opacity=opacity, color=color, overlay=overlay)
            return None
        else:
            writers = (writers,)
    clip = writers[0].text_rect
    textdoc = Document()
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


def show_pdf_page(*args, **kwargs) -> int:
    """Show page number 'pno' of PDF 'src' in rectangle 'rect'.

    Args:
        rect: (rect-like) where to place the source image
        src: (document) source PDF
        pno: (int) source page number
        overlay: (bool) put in foreground
        keep_proportion: (bool) do not change width-height-ratio
        rotate: (int) degrees (multiple of 90)
        clip: (rect-like) part of source page rectangle
    Returns:
        xref of inserted object (for reuse)
    """
    if len(args) not in (3, 4):
        raise ValueError("bad number of positional parameters")
    pno = None
    if len(args) == 3:
        page, rect, src = args
    else:
        page, rect, src, pno = args
    if pno == None:
        pno = int(kwargs.get("pno", 0))
    overlay = bool(kwargs.get("overlay", True))
    keep_proportion = bool(kwargs.get("keep_proportion", True))
    rotate = float(kwargs.get("rotate", 0))
    oc = int(kwargs.get("oc", 0))
    clip = kwargs.get("clip")

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
        m = Matrix(1, 0, 0, 1, -smp.x, -smp.y) * Matrix(rotate)

        sr1 = sr * m  # resulting source rect to calculate scale factors

        fw = tr.width / sr1.width  # scale the width
        fh = tr.height / sr1.height  # scale the height
        if keep:
            fw = fh = min(fw, fh)  # take min if keeping aspect ratio

        m *= Matrix(fw, fh)  # concat scale matrix
        m *= Matrix(1, 0, 0, 1, tmp.x, tmp.y)  # concat move to target center
        return JM_TUPLE(m)

    CheckParent(page)
    doc = page.parent

    if not doc.is_pdf or not src.is_pdf:
        raise ValueError("is no PDF")

    if rect.is_empty or rect.is_infinite:
        raise ValueError("rect must be finite and not empty")

    while pno < 0:  # support negative page numbers
        pno += src.page_count
    src_page = src[pno]  # load source page
    if src_page.get_contents() == []:
        raise ValueError("nothing to show - source page empty")

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

    isrc = src._graft_id  # used as key for graftmaps
    if doc._graft_id == isrc:
        raise ValueError("source document must not equal target")

    # retrieve / make Graftmap for source PDF
    gmap = doc.Graftmaps.get(isrc, None)
    if gmap is None:
        gmap = Graftmap(doc)
        doc.Graftmaps[isrc] = gmap

    # take note of generated xref for automatic reuse
    pno_id = (isrc, pno)  # id of src[pno]
    xref = doc.ShownPages.get(pno_id, 0)

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


def replace_image(page: Page, xref: int, *, filename=None, pixmap=None, stream=None):
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


def delete_image(page: Page, xref: int):
    """Delete the image referred to by xef.

    Actually replaces by a small transparent Pixmap using method Page.replace_image.

    Args:
        xref: xref of the image to delete.
    """
    # make a small 100% transparent pixmap (of just any dimension)
    pix = fitz.Pixmap(fitz.csGRAY, (0, 0, 1, 1), 1)
    pix.clear_with()  # clear all samples bytes to 0x00
    page.replace_image(xref, pixmap=pix)


def insert_image(page, rect, **kwargs):
    """Insert an image for display in a rectangle.

    Args:
        rect: (rect_like) position of image on the page.
        alpha: (int, optional) set to 0 if image has no transparency.
        filename: (str, Path, file object) image filename.
        keep_proportion: (bool) keep width / height ratio (default).
        mask: (bytes, optional) image consisting of alpha values to use.
        oc: (int) xref of OCG or OCMD to declare as Optional Content.
        overlay: (bool) put in foreground (default) or background.
        pixmap: (Pixmap) use this as image.
        rotate: (int) rotate by 0, 90, 180 or 270 degrees.
        stream: (bytes) use this as image.
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
    CheckParent(page)
    doc = page.parent
    if not doc.is_pdf:
        raise ValueError("is no PDF")

    valid_keys = {
        "alpha",
        "filename",
        "height",
        "keep_proportion",
        "mask",
        "oc",
        "overlay",
        "pixmap",
        "rotate",
        "stream",
        "width",
        "xref",
    }
    s = set(kwargs.keys()).difference(valid_keys)
    if s != set():
        raise ValueError(f"bad key argument(s): {s}.")
    filename = kwargs.get("filename")
    pixmap = kwargs.get("pixmap")
    stream = kwargs.get("stream")
    mask = kwargs.get("mask")
    rotate = int(kwargs.get("rotate", 0))
    width = int(kwargs.get("width", 0))
    height = int(kwargs.get("height", 0))
    alpha = int(kwargs.get("alpha", -1))
    oc = int(kwargs.get("oc", 0))
    xref = int(kwargs.get("xref", 0))
    keep_proportion = bool(kwargs.get("keep_proportion", True))
    overlay = bool(kwargs.get("overlay", True))

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
    elif pixmap and type(pixmap) is not Pixmap:
        raise ValueError("pixmap must be a Pixmap")
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

    r = Rect(rect)
    if r.is_empty or r.is_infinite:
        raise ValueError("rect must be finite and not empty")
    clip = r * ~page.transformation_matrix

    # Create a unique image reference name.
    ilst = [i[7] for i in doc.get_page_images(page.number)]
    ilst += [i[1] for i in doc.get_page_xobjects(page.number)]
    ilst += [i[4] for i in doc.get_page_fonts(page.number)]
    n = "fzImg"  # 'fitz image'
    i = 0
    _imgname = n + "0"  # first name candidate
    while _imgname in ilst:
        i += 1
        _imgname = n + str(i)  # try new name

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

    if digests != None:
        doc.InsertedImages = digests

    return xref


def search_for(*args, **kwargs) -> list:
    """Search for a string on a page.

    Args:
        text: string to be searched for
        clip: restrict search to this rectangle
        quads: (bool) return quads instead of rectangles
        flags: bit switches, default: join hyphened words
        textpage: a pre-created TextPage
    Returns:
        a list of rectangles or quads, each containing one occurrence.
    """
    if len(args) != 2:
        raise ValueError("bad number of positional parameters")
    page, text = args
    quads = kwargs.get("quads", 0)
    clip = kwargs.get("clip")
    textpage = kwargs.get("textpage")
    if clip != None:
        clip = Rect(clip)
    flags = kwargs.get(
        "flags",
        TEXT_DEHYPHENATE
        | TEXT_PRESERVE_WHITESPACE
        | TEXT_PRESERVE_LIGATURES
        | TEXT_MEDIABOX_CLIP,
    )

    CheckParent(page)
    tp = textpage
    if tp is None:
        tp = page.get_textpage(clip=clip, flags=flags)  # create TextPage
    elif getattr(tp, "parent") != page:
        raise ValueError("not a textpage of this page")
    rlist = tp.search(text, quads=quads)
    if textpage is None:
        del tp
    return rlist


def search_page_for(
    doc: Document,
    pno: int,
    text: str,
    quads: bool = False,
    clip: rect_like = None,
    flags: int = TEXT_DEHYPHENATE
    | TEXT_PRESERVE_LIGATURES
    | TEXT_PRESERVE_WHITESPACE
    | TEXT_MEDIABOX_CLIP,
    textpage: TextPage = None,
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
    page: Page,
    clip: rect_like = None,
    flags: OptInt = None,
    textpage: TextPage = None,
    sort: bool = False,
) -> list:
    """Return the text blocks on a page.

    Notes:
        Lines in a block are concatenated with line breaks.
    Args:
        flags: (int) control the amount of data parsed into the textpage.
    Returns:
        A list of the blocks. Each item contains the containing rectangle
        coordinates, text lines, block type and running block number.
    """
    CheckParent(page)
    if flags is None:
        flags = (
            TEXT_PRESERVE_WHITESPACE
            | TEXT_PRESERVE_IMAGES
            | TEXT_PRESERVE_LIGATURES
            | TEXT_MEDIABOX_CLIP
        )
    tp = textpage
    if tp is None:
        tp = page.get_textpage(clip=clip, flags=flags)
    elif getattr(tp, "parent") != page:
        raise ValueError("not a textpage of this page")

    blocks = tp.extractBLOCKS()
    if textpage is None:
        del tp
    if sort is True:
        blocks.sort(key=lambda b: (b[3], b[0]))
    return blocks


def get_text_words(
    page: Page,
    clip: rect_like = None,
    flags: OptInt = None,
    textpage: TextPage = None,
    sort: bool = False,
) -> list:
    """Return the text words as a list with the bbox for each word.

    Args:
        flags: (int) control the amount of data parsed into the textpage.
    """
    CheckParent(page)
    if flags is None:
        flags = TEXT_PRESERVE_WHITESPACE | TEXT_PRESERVE_LIGATURES | TEXT_MEDIABOX_CLIP
    tp = textpage
    if tp is None:
        tp = page.get_textpage(clip=clip, flags=flags)
    elif getattr(tp, "parent") != page:
        raise ValueError("not a textpage of this page")
    words = tp.extractWORDS()
    if textpage is None:
        del tp
    if sort is True:
        words.sort(key=lambda w: (w[3], w[0]))
    return words


def get_textbox(
    page: Page,
    rect: rect_like,
    textpage: TextPage = None,
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
    page: Page,
    p1: point_like,
    p2: point_like,
    clip: rect_like = None,
    textpage: TextPage = None,
):
    CheckParent(page)
    tp = textpage
    if tp is None:
        tp = page.get_textpage(clip=clip, flags=TEXT_DEHYPHENATE)
    elif getattr(tp, "parent") != page:
        raise ValueError("not a textpage of this page")
    rc = tp.extractSelection(p1, p2)
    if textpage is None:
        del tp
    return rc


def get_textpage_ocr(
    page: Page,
    flags: int = 0,
    language: str = "eng",
    dpi: int = 72,
    full: bool = False,
    tessdata: str = None,
) -> TextPage:
    """Create a Textpage from combined results of normal and OCR text parsing.

    Args:
        flags: (int) control content becoming part of the result.
        language: (str) specify expected language(s). Deafault is "eng" (English).
        dpi: (int) resolution in dpi, default 72.
        full: (bool) whether to OCR the full page image, or only its images (default)
    """
    CheckParent(page)
    if not os.getenv("TESSDATA_PREFIX") and not tessdata:
        raise RuntimeError("No OCR support: TESSDATA_PREFIX not set")

    def full_ocr(page, dpi, language, flags):
        zoom = dpi / 72
        mat = Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        ocr_pdf = Document(
            "pdf",
            pix.pdfocr_tobytes(compress=False, language=language, tessdata=tessdata),
        )
        ocr_page = ocr_pdf.load_page(0)
        unzoom = page.rect.width / ocr_page.rect.width
        ctm = Matrix(unzoom, unzoom) * page.derotation_matrix
        tpage = ocr_page.get_textpage(flags=flags, matrix=ctm)
        ocr_pdf.close()
        pix = None
        tpage.parent = weakref.proxy(page)
        return tpage

    # if OCR for the full page, OCR its pixmap @ desired dpi
    if full is True:
        return full_ocr(page, dpi, language, flags)

    # For partial OCR, make a normal textpage, then extend it with text that
    # is OCRed from each image.
    # Because of this, we need the images flag bit set ON.
    tpage = page.get_textpage(flags=flags)
    for block in page.get_text("dict", flags=TEXT_PRESERVE_IMAGES)["blocks"]:
        if block["type"] != 1:  # only look at images
            continue
        bbox = Rect(block["bbox"])
        if bbox.width <= 3 or bbox.height <= 3:  # ignore tiny stuff
            continue
        try:
            pix = Pixmap(block["image"])  # get image pixmap
            if pix.n - pix.alpha != 3:  # we need to convert this to RGB!
                pix = Pixmap(csRGB, pix)
            if pix.alpha:  # must remove alpha channel
                pix = Pixmap(pix, 0)
            imgdoc = Document(
                "pdf", pix.pdfocr_tobytes(language=language, tessdata=tessdata)
            )  # pdf with OCRed page
            imgpage = imgdoc.load_page(0)  # read image as a page
            pix = None
            # compute matrix to transform coordinates back to that of 'page'
            imgrect = imgpage.rect  # page size of image PDF
            shrink = Matrix(1 / imgrect.width, 1 / imgrect.height)
            mat = shrink * block["transform"]
            imgpage.extend_textpage(tpage, flags=0, matrix=mat)
            imgdoc.close()
        except RuntimeError:
            tpage = None
            print("Falling back to full page OCR")
            return full_ocr(page, dpi, language, flags)

    return tpage


def get_image_info(page: Page, hashes: bool = False, xrefs: bool = False) -> list:
    """Extract image information only from a TextPage.

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
        tp = page.get_textpage(flags=TEXT_PRESERVE_IMAGES)
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
        pix = Pixmap(doc, xref)
        digests[pix.digest] = xref
        del pix
    for i in range(len(imginfo)):
        item = imginfo[i]
        xref = digests.get(item["digest"], 0)
        item["xref"] = xref
        imginfo[i] = item
    return imginfo


def get_image_rects(page: Page, name, transform=False) -> list:
    """Return list of image positions on a page.

    Args:
        name: (str, list, int) image identification. May be reference name, an
              item of the page's image list or an xref.
        transform: (bool) whether to also return the transformation matrix.
    Returns:
        A list of Rect objects or tuples of (Rect, Matrix) for all image
        locations on the page.
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
    pix = Pixmap(page.parent, xref)  # make pixmap of the image to compute MD5
    digest = pix.digest
    del pix
    infos = page.get_image_info(hashes=True)
    if not transform:
        bboxes = [Rect(im["bbox"]) for im in infos if im["digest"] == digest]
    else:
        bboxes = [
            (Rect(im["bbox"]), Matrix(im["transform"]))
            for im in infos
            if im["digest"] == digest
        ]
    return bboxes


def get_text(
    page: Page,
    option: str = "text",
    clip: rect_like = None,
    flags: OptInt = None,
    textpage: TextPage = None,
    sort: bool = False,
):
    """Extract text from a page or an annotation.

    This is a unifying wrapper for various methods of the TextPage class.

    Args:
        option: (str) text, words, blocks, html, dict, json, rawdict, xhtml or xml.
        clip: (rect-like) restrict output to this area.
        flags: bit switches to e.g. exclude images or decompose ligatures.
        textpage: reuse this TextPage and make no new one. If specified,
            'flags' and 'clip' are ignored.

    Returns:
        the output of methods get_text_words / get_text_blocks or TextPage
        methods extractText, extractHTML, extractDICT, extractJSON, extractRAWDICT,
        extractXHTML or etractXML respectively.
        Default and misspelling choice is "text".
    """
    formats = {
        "text": 0,
        "html": 1,
        "json": 1,
        "rawjson": 1,
        "xml": 0,
        "xhtml": 1,
        "dict": 1,
        "rawdict": 1,
        "words": 0,
        "blocks": 1,
    }
    option = option.lower()
    if option not in formats:
        option = "text"
    if flags is None:
        flags = TEXT_PRESERVE_WHITESPACE | TEXT_PRESERVE_LIGATURES | TEXT_MEDIABOX_CLIP
        if formats[option] == 1:
            flags |= TEXT_PRESERVE_IMAGES

    if option == "words":
        return get_text_words(
            page, clip=clip, flags=flags, textpage=textpage, sort=sort
        )
    if option == "blocks":
        return get_text_blocks(
            page, clip=clip, flags=flags, textpage=textpage, sort=sort
        )
    CheckParent(page)
    cb = None
    if option in ("html", "xml", "xhtml"):  # no clipping for MuPDF functions
        clip = page.cropbox
    if clip != None:
        clip = Rect(clip)
        cb = None
    elif type(page) is Page:
        cb = page.cropbox
    # TextPage with or without images
    tp = textpage
    if tp is None:
        tp = page.get_textpage(clip=clip, flags=flags)
    elif getattr(tp, "parent") != page:
        raise ValueError("not a textpage of this page")

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
    doc: Document,
    pno: int,
    option: str = "text",
    clip: rect_like = None,
    flags: OptInt = None,
    textpage: TextPage = None,
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
    page: Page,
    *,
    matrix: matrix_like = Identity,
    dpi=None,
    colorspace: Colorspace = csRGB,
    clip: rect_like = None,
    alpha: bool = False,
    annots: bool = True,
) -> Pixmap:
    """Create pixmap of page.

    Keyword args:
        matrix: Matrix for transformation (default: Identity).
        dpi: desired dots per inch. If given, matrix is ignored.
        colorspace: (str/Colorspace) cmyk, rgb, gray - case ignored, default csRGB.
        clip: (irect-like) restrict rendering to this area.
        alpha: (bool) whether to include alpha channel
        annots: (bool) whether to also render annotations
    """
    CheckParent(page)
    if dpi:
        zoom = dpi / 72
        matrix = Matrix(zoom, zoom)

    if type(colorspace) is str:
        if colorspace.upper() == "GRAY":
            colorspace = csGRAY
        elif colorspace.upper() == "CMYK":
            colorspace = csCMYK
        else:
            colorspace = csRGB
    if colorspace.n not in (1, 3, 4):
        raise ValueError("unsupported colorspace")

    dl = page.get_displaylist(annots=annots)
    pix = dl.get_pixmap(matrix=matrix, colorspace=colorspace, alpha=alpha, clip=clip)
    dl = None
    if dpi:
        pix.set_dpi(dpi, dpi)
    return pix


def get_page_pixmap(
    doc: Document,
    pno: int,
    *,
    matrix: matrix_like = Identity,
    dpi=None,
    colorspace: Colorspace = csRGB,
    clip: rect_like = None,
    alpha: bool = False,
    annots: bool = True,
) -> Pixmap:
    """Create pixmap of document page by page number.

    Notes:
        Convenience function calling page.get_pixmap.
    Args:
        pno: (int) page number
        matrix: Matrix for transformation (default: Identity).
        colorspace: (str,Colorspace) rgb, rgb, gray - case ignored, default csRGB.
        clip: (irect-like) restrict rendering to this area.
        alpha: (bool) include alpha channel
        annots: (bool) also render annotations
    """
    return doc[pno].get_pixmap(
        matrix=matrix,
        dpi=dpi,
        colorspace=colorspace,
        clip=clip,
        alpha=alpha,
        annots=annots,
    )


def getLinkDict(ln) -> dict:
    nl = {"kind": ln.dest.kind, "xref": 0}
    try:
        nl["from"] = ln.rect
    except:
        pass
    pnt = Point(0, 0)
    if ln.dest.flags & LINK_FLAG_L_VALID:
        pnt.x = ln.dest.lt.x
    if ln.dest.flags & LINK_FLAG_T_VALID:
        pnt.y = ln.dest.lt.y

    if ln.dest.kind == LINK_URI:
        nl["uri"] = ln.dest.uri

    elif ln.dest.kind == LINK_GOTO:
        nl["page"] = ln.dest.page
        nl["to"] = pnt
        if ln.dest.flags & LINK_FLAG_R_IS_ZOOM:
            nl["zoom"] = ln.dest.rb.x
        else:
            nl["zoom"] = 0.0

    elif ln.dest.kind == LINK_GOTOR:
        nl["file"] = ln.dest.fileSpec.replace("\\", "/")
        nl["page"] = ln.dest.page
        if ln.dest.page < 0:
            nl["to"] = ln.dest.dest
        else:
            nl["to"] = pnt
            if ln.dest.flags & LINK_FLAG_R_IS_ZOOM:
                nl["zoom"] = ln.dest.rb.x
            else:
                nl["zoom"] = 0.0

    elif ln.dest.kind == LINK_LAUNCH:
        nl["file"] = ln.dest.fileSpec.replace("\\", "/")

    elif ln.dest.kind == LINK_NAMED:
        nl["name"] = ln.dest.named

    else:
        nl["page"] = ln.dest.page

    return nl


def get_links(page: Page) -> list:
    """Create a list of all links contained in a PDF page.

    Notes:
        see PyMuPDF ducmentation for details.
    """

    CheckParent(page)
    ln = page.first_link
    links = []
    while ln:
        nl = getLinkDict(ln)
        links.append(nl)
        ln = ln.next
    if links != [] and page.parent.is_pdf:
        linkxrefs = [x for x in page.annot_xrefs() if x[1] == PDF_ANNOT_LINK]
        if len(linkxrefs) == len(links):
            for i in range(len(linkxrefs)):
                links[i]["xref"] = linkxrefs[i][0]
                links[i]["id"] = linkxrefs[i][2]
    return links


def get_toc(
    doc: Document,
    simple: bool = True,
) -> list:
    """Create a table of contents.

    Args:
        simple: a bool to control output. Returns a list, where each entry consists of outline level, title, page number and link destination (if simple = False). For details see PyMuPDF's documentation.
    """

    def recurse(olItem, liste, lvl):
        """Recursively follow the outline item chain and record item information in a list."""
        while olItem:
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
                link = getLinkDict(olItem)
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
    if doc.is_pdf and simple is False:
        doc._extend_toc_items(toc)
    return toc


def del_toc_item(
    doc: Document,
    idx: int,
) -> None:
    """Delete TOC / bookmark item by index."""
    xref = doc.get_outline_xrefs()[idx]
    doc._remove_toc_item(xref)


def set_toc_item(
    doc: Document,
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
        idx: (int) desired index of the TOC list, as created by get_toc.
        dest_dict: (dict) destination dictionary as created by get_toc(False).
            Outrules all other parameters. If None, the remaining parameters
            are used to make a dest dictionary.
        kind: (int) kind of link (LINK_GOTO, etc.). If None, then only the
            title will be updated. If LINK_NONE, the TOC item will be deleted.
        pno: (int) page number (1-based like in get_toc). Required if LINK_GOTO.
        uri: (str) the URL, required if LINK_URI.
        title: (str) the new title. No change if None.
        to: (point-like) destination on the target page. If omitted, (72, 36)
            will be used as taget coordinates.
        filename: (str) destination filename, required for LINK_GOTOR and
            LINK_LAUNCH.
        name: (str) a destination name for LINK_NAMED.
        zoom: (float) a zoom factor for the target location (LINK_GOTO).
    """
    xref = doc.get_outline_xrefs()[idx]
    page_xref = 0
    if type(dest_dict) is dict:
        if dest_dict["kind"] == LINK_GOTO:
            pno = dest_dict["page"]
            page_xref = doc.page_xref(pno)
            page_height = doc.page_cropbox(pno).height
            to = dest_dict.get("to", Point(72, 36))
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

    if kind == LINK_NONE:  # delete bookmark item
        return doc.del_toc_item(idx)
    if kind is None and title is None:  # treat as no-op
        return None
    if kind is None:  # only update title text
        return doc._update_toc_item(xref, action=None, title=title)

    if kind == LINK_GOTO:
        if pno is None or pno not in range(1, doc.page_count + 1):
            raise ValueError("bad page number")
        page_xref = doc.page_xref(pno - 1)
        page_height = doc.page_cropbox(pno - 1).height
        if to is None:
            to = Point(72, page_height - 36)
        else:
            to = Point(to)
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


def set_metadata(doc: Document, m: dict) -> None:
    """Update the PDF /Info object.

    Args:
        m: a dictionary like doc.metadata.
    """
    if not doc.is_pdf:
        raise ValueError("is no PDF")
    if doc.is_closed or doc.is_encrypted:
        raise ValueError("document closed or encrypted")
    if type(m) is not dict:
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
        return

    for key, val in [(k, v) for k, v in m.items() if keymap[k] != None]:
        pdf_key = keymap[key]
        if not bool(val) or val in ("none", "null"):
            val = "null"
        else:
            val = get_pdf_str(val)
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
    str_goto = "/A<</S/GoTo/D[%i 0 R/XYZ %g %g %g]>>"
    str_gotor1 = "/A<</S/GoToR/D[%s /XYZ %g %g %g]/F<</F%s/UF%s/Type/Filespec>>>>"
    str_gotor2 = "/A<</S/GoToR/D%s/F<</F%s/UF%s/Type/Filespec>>>>"
    str_launch = "/A<</S/Launch/F<</F%s/UF%s/Type/Filespec>>>>"
    str_uri = "/A<</S/URI/URI%s>>"

    if type(ddict) in (int, float):
        dest = str_goto % (xref, 0, ddict, 0)
        return dest
    d_kind = ddict.get("kind", LINK_NONE)

    if d_kind == LINK_NONE:
        return ""

    if ddict["kind"] == LINK_GOTO:
        d_zoom = ddict.get("zoom", 0)
        to = ddict.get("to", Point(0, 0))
        d_left, d_top = to
        dest = str_goto % (xref, d_left, d_top, d_zoom)
        return dest

    if ddict["kind"] == LINK_URI:
        dest = str_uri % (get_pdf_str(ddict["uri"]),)
        return dest

    if ddict["kind"] == LINK_LAUNCH:
        fspec = get_pdf_str(ddict["file"])
        dest = str_launch % (fspec, fspec)
        return dest

    if ddict["kind"] == LINK_GOTOR and ddict["page"] < 0:
        fspec = get_pdf_str(ddict["file"])
        dest = str_gotor2 % (get_pdf_str(ddict["to"]), fspec, fspec)
        return dest

    if ddict["kind"] == LINK_GOTOR and ddict["page"] >= 0:
        fspec = get_pdf_str(ddict["file"])
        dest = str_gotor1 % (
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
    doc: Document,
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
    # build olitems as a list of PDF-like connnected dictionaries
    # ------------------------------------------------------------------------------
    for i in range(toclen):
        o = toc[i]
        lvl = o[0]  # level
        title = get_pdf_str(o[1])  # title
        pno = min(doc.page_count - 1, max(0, o[2] - 1))  # page number
        page_xref = doc.page_xref(pno)
        page_height = doc.page_cropbox(pno).height
        top = Point(72, page_height - 36)
        dest_dict = {"to": top, "kind": LINK_GOTO}  # fall back target
        if o[2] < 0:
            dest_dict["kind"] = LINK_NONE
        if len(o) > 3:  # some target is specified
            if type(o[3]) in (int, float):  # convert a number to a point
                dest_dict["to"] = Point(72, page_height - o[3])
            else:  # if something else, make sure we have a dict
                dest_dict = o[3] if type(o[3]) is dict else dest_dict
                if "to" not in dest_dict:  # target point not in dict?
                    dest_dict["to"] = top  # put default in
                else:  # transform target to PDF coordinates
                    point = +dest_dict["to"]
                    point.y = page_height - point.y
                    dest_dict["to"] = point
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
        except:
            pass
        try:
            if ol["first"] > -1:
                txt += "/First %i 0 R" % xref[ol["first"]]
        except:
            pass
        try:
            if ol["last"] > -1:
                txt += "/Last %i 0 R" % xref[ol["last"]]
        except:
            pass
        try:
            if ol["next"] > -1:
                txt += "/Next %i 0 R" % xref[ol["next"]]
        except:
            pass
        try:
            if ol["parent"] > -1:
                txt += "/Parent %i 0 R" % xref[ol["parent"]]
        except:
            pass
        try:
            if ol["prev"] > -1:
                txt += "/Prev %i 0 R" % xref[ol["prev"]]
        except:
            pass
        try:
            txt += "/Title" + ol["title"]
        except:
            pass

        if ol.get("color") and len(ol["color"]) == 3:
            txt += "/C[ %g %g %g]" % tuple(ol["color"])
        if ol.get("flags", 0) > 0:
            txt += "/F %i" % ol["flags"]

        if i == 0:  # special: this is the outline root
            txt += "/Type/Outlines"  # so add the /Type entry
        txt += ">>"
        doc.update_object(xref[i], txt)  # insert the PDF object

    doc.init_doc()
    return toclen


def do_links(
    doc1: Document,
    doc2: Document,
    from_page: int = -1,
    to_page: int = -1,
    start_at: int = -1,
) -> None:
    """Insert links contained in copied page range into destination PDF.

    Parameter values **must** equal those of method insert_pdf(), which must
    have been previously executed.
    """

    # --------------------------------------------------------------------------
    # internal function to create the actual "/Annots" object string
    # --------------------------------------------------------------------------
    def cre_annot(lnk, xref_dst, pno_src, ctm):
        """Create annotation object string for a passed-in link."""

        r = lnk["from"] * ctm  # rect in PDF coordinates
        rect = "%g %g %g %g" % tuple(r)
        if lnk["kind"] == LINK_GOTO:
            txt = annot_skel["goto1"]  # annot_goto
            idx = pno_src.index(lnk["page"])
            p = lnk["to"] * ctm  # target point in PDF coordinates
            annot = txt % (xref_dst[idx], p.x, p.y, lnk["zoom"], rect)

        elif lnk["kind"] == LINK_GOTOR:
            if lnk["page"] >= 0:
                txt = annot_skel["gotor1"]  # annot_gotor
                pnt = lnk.get("to", Point(0, 0))  # destination point
                if type(pnt) is not Point:
                    pnt = Point(0, 0)
                annot = txt % (
                    lnk["page"],
                    pnt.x,
                    pnt.y,
                    lnk["zoom"],
                    lnk["file"],
                    lnk["file"],
                    rect,
                )
            else:
                txt = annot_skel["gotor2"]  # annot_gotor_n
                to = get_pdf_str(lnk["to"])
                to = to[1:-1]
                f = lnk["file"]
                annot = txt % (to, f, rect)

        elif lnk["kind"] == LINK_LAUNCH:
            txt = annot_skel["launch"]  # annot_launch
            annot = txt % (lnk["file"], lnk["file"], rect)

        elif lnk["kind"] == LINK_URI:
            txt = annot_skel["uri"]  # annot_uri
            annot = txt % (lnk["uri"], rect)

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
        if len(links) == 0:  # no links there
            page_src = None
            continue
        ctm = ~page_src.transformation_matrix  # calc page transformation matrix
        page_dst = doc1[pno_dst[i]]  # load destination page
        link_tab = []  # store all link definitions here
        for l in links:
            if l["kind"] == LINK_GOTO and (l["page"] not in pno_src):
                continue  # GOTO link target not in copied pages
            annot_text = cre_annot(l, xref_dst, pno_src, ctm)
            if not annot_text:
                print("cannot create /Annot for kind: " + str(l["kind"]))
            else:
                link_tab.append(annot_text)
        if link_tab != []:
            page_dst._addAnnot_FromString(tuple(link_tab))

    return


def getLinkText(page: Page, lnk: dict) -> str:
    # --------------------------------------------------------------------------
    # define skeletons for /Annots object texts
    # --------------------------------------------------------------------------
    ctm = page.transformation_matrix
    ictm = ~ctm
    r = lnk["from"]
    rect = "%g %g %g %g" % tuple(r * ictm)

    annot = ""
    if lnk["kind"] == LINK_GOTO:
        if lnk["page"] >= 0:
            txt = annot_skel["goto1"]  # annot_goto
            pno = lnk["page"]
            xref = page.parent.page_xref(pno)
            pnt = lnk.get("to", Point(0, 0))  # destination point
            ipnt = pnt * ictm
            annot = txt % (xref, ipnt.x, ipnt.y, lnk.get("zoom", 0), rect)
        else:
            txt = annot_skel["goto2"]  # annot_goto_n
            annot = txt % (get_pdf_str(lnk["to"]), rect)

    elif lnk["kind"] == LINK_GOTOR:
        if lnk["page"] >= 0:
            txt = annot_skel["gotor1"]  # annot_gotor
            pnt = lnk.get("to", Point(0, 0))  # destination point
            if type(pnt) is not Point:
                pnt = Point(0, 0)
            annot = txt % (
                lnk["page"],
                pnt.x,
                pnt.y,
                lnk.get("zoom", 0),
                lnk["file"],
                lnk["file"],
                rect,
            )
        else:
            txt = annot_skel["gotor2"]  # annot_gotor_n
            annot = txt % (get_pdf_str(lnk["to"]), lnk["file"], rect)

    elif lnk["kind"] == LINK_LAUNCH:
        txt = annot_skel["launch"]  # annot_launch
        annot = txt % (lnk["file"], lnk["file"], rect)

    elif lnk["kind"] == LINK_URI:
        txt = annot_skel["uri"]  # txt = annot_uri
        annot = txt % (lnk["uri"], rect)

    elif lnk["kind"] == LINK_NAMED:
        txt = annot_skel["named"]  # annot_named
        annot = txt % (lnk["name"], rect)
    if not annot:
        return annot

    # add a /NM PDF key to the object definition
    link_names = dict(  # existing ids and their xref
        [(x[0], x[2]) for x in page.annot_xrefs() if x[1] == PDF_ANNOT_LINK]
    )

    old_name = lnk.get("id", "")  # id value in the argument

    if old_name and (lnk["xref"], old_name) in link_names.items():
        name = old_name  # no new name if this is an update only
    else:
        i = 0
        stem = TOOLS.set_annot_stem() + "-L%i"
        while True:
            name = stem % i
            if name not in link_names.values():
                break
            i += 1
    # add /NM key to object definition
    annot = annot.replace("/Link", "/Link/NM(%s)" % name)

    return annot


def delete_widget(page: Page, widget: Widget) -> Widget:
    """Delete widget from page and return the next one."""
    CheckParent(page)
    annot = getattr(widget, "_annot", None)
    if annot is None:
        raise ValueError("bad type: widget")
    nextwidget = widget.next
    page.delete_annot(annot)
    widget._annot.__del__()
    widget._annot.parent = None
    keylist = list(widget.__dict__.keys())
    for key in keylist:
        del widget.__dict__[key]
    return nextwidget


def update_link(page: Page, lnk: dict) -> None:
    """Update a link on the current page."""
    CheckParent(page)
    annot = getLinkText(page, lnk)
    if annot == "":
        raise ValueError("link kind not supported")

    page.parent.update_object(lnk["xref"], annot, page=page)
    return


def insert_link(page: Page, lnk: dict, mark: bool = True) -> None:
    """Insert a new link for the current page."""
    CheckParent(page)
    annot = getLinkText(page, lnk)
    if annot == "":
        raise ValueError("link kind not supported")
    page._addAnnot_FromString((annot,))
    return


def insert_textbox(
    page: Page,
    rect: rect_like,
    buffer: typing.Union[str, list],
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
    border_width: float = 1,
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
    page: Page,
    point: point_like,
    text: typing.Union[str, list],
    fontsize: float = 11,
    lineheight: OptFloat = None,
    fontname: str = "helv",
    fontfile: OptStr = None,
    set_simple: int = 0,
    encoding: int = 0,
    color: OptSeq = None,
    fill: OptSeq = None,
    border_width: float = 1,
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
        rotate=rotate,
        morph=morph,
        stroke_opacity=stroke_opacity,
        fill_opacity=fill_opacity,
        oc=oc,
    )
    if rc >= 0:
        img.commit(overlay)
    return rc


def new_page(
    doc: Document,
    pno: int = -1,
    width: float = 595,
    height: float = 842,
) -> Page:
    """Create and return a new page object.

    Args:
        pno: (int) insert before this page. Default: after last page.
        width: (float) page width in points. Default: 595 (ISO A4 width).
        height: (float) page height in points. Default 842 (ISO A4 height).
    Returns:
        A Page object.
    """
    doc._newPage(pno, width=width, height=height)
    return doc[pno]


def insert_page(
    doc: Document,
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
        Function combining Document.new_page() and Page.insert_text().
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
    page: Page,
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
) -> Point:
    """Draw a line from point p1 to point p2."""
    img = page.new_shape()
    p = img.draw_line(Point(p1), Point(p2))
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
    page: Page,
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
) -> Point:
    """Draw a squiggly line from point p1 to point p2."""
    img = page.new_shape()
    p = img.draw_squiggle(Point(p1), Point(p2), breadth=breadth)
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
    page: Page,
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
) -> Point:
    """Draw a zigzag line from point p1 to point p2."""
    img = page.new_shape()
    p = img.draw_zigzag(Point(p1), Point(p2), breadth=breadth)
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
    page: Page,
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
) -> Point:
    """Draw a rectangle. See Shape class method for details."""
    img = page.new_shape()
    Q = img.draw_rect(Rect(rect), radius=radius)
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
    page: Page,
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
) -> Point:
    """Draw a quadrilateral."""
    img = page.new_shape()
    Q = img.draw_quad(Quad(quad))
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
    page: Page,
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
) -> Point:
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
    page: Page,
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
) -> Point:
    """Draw a circle given its center and radius."""
    img = page.new_shape()
    Q = img.draw_circle(Point(center), radius)
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
    page: Page,
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
) -> Point:
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
    page: Page,
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
) -> Point:
    """Draw a special Bezier curve from p1 to p3, generating control points on lines p1 to p2 and p2 to p3."""
    img = page.new_shape()
    Q = img.draw_curve(Point(p1), Point(p2), Point(p3))
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
    page: Page,
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
) -> Point:
    """Draw a general cubic Bezier curve from p1 to p4 using control points p2 and p3."""
    img = page.new_shape()
    Q = img.draw_bezier(Point(p1), Point(p2), Point(p3), Point(p4))
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
    page: Page,
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
) -> Point:
    """Draw a circle sector given circle center, one arc end point and the angle of the arc.

    Parameters:
        center -- center of circle
        point -- arc end point
        beta -- angle of arc (degrees)
        fullSector -- connect arc ends with center
    """
    img = page.new_shape()
    Q = img.draw_sector(Point(center), Point(point), beta, fullSector=fullSector)
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
    Returns a list of just the colour names used by this module.
    :rtype: list of strings
    """

    return [x[0] for x in getColorInfoList()]


def getColorInfoList() -> list:
    """
    Returns the list of colour name/value tuples used by this module.
    :rtype: list of tuples
    """

    return [
        ("ALICEBLUE", 240, 248, 255),
        ("ANTIQUEWHITE", 250, 235, 215),
        ("ANTIQUEWHITE1", 255, 239, 219),
        ("ANTIQUEWHITE2", 238, 223, 204),
        ("ANTIQUEWHITE3", 205, 192, 176),
        ("ANTIQUEWHITE4", 139, 131, 120),
        ("AQUAMARINE", 127, 255, 212),
        ("AQUAMARINE1", 127, 255, 212),
        ("AQUAMARINE2", 118, 238, 198),
        ("AQUAMARINE3", 102, 205, 170),
        ("AQUAMARINE4", 69, 139, 116),
        ("AZURE", 240, 255, 255),
        ("AZURE1", 240, 255, 255),
        ("AZURE2", 224, 238, 238),
        ("AZURE3", 193, 205, 205),
        ("AZURE4", 131, 139, 139),
        ("BEIGE", 245, 245, 220),
        ("BISQUE", 255, 228, 196),
        ("BISQUE1", 255, 228, 196),
        ("BISQUE2", 238, 213, 183),
        ("BISQUE3", 205, 183, 158),
        ("BISQUE4", 139, 125, 107),
        ("BLACK", 0, 0, 0),
        ("BLANCHEDALMOND", 255, 235, 205),
        ("BLUE", 0, 0, 255),
        ("BLUE1", 0, 0, 255),
        ("BLUE2", 0, 0, 238),
        ("BLUE3", 0, 0, 205),
        ("BLUE4", 0, 0, 139),
        ("BLUEVIOLET", 138, 43, 226),
        ("BROWN", 165, 42, 42),
        ("BROWN1", 255, 64, 64),
        ("BROWN2", 238, 59, 59),
        ("BROWN3", 205, 51, 51),
        ("BROWN4", 139, 35, 35),
        ("BURLYWOOD", 222, 184, 135),
        ("BURLYWOOD1", 255, 211, 155),
        ("BURLYWOOD2", 238, 197, 145),
        ("BURLYWOOD3", 205, 170, 125),
        ("BURLYWOOD4", 139, 115, 85),
        ("CADETBLUE", 95, 158, 160),
        ("CADETBLUE1", 152, 245, 255),
        ("CADETBLUE2", 142, 229, 238),
        ("CADETBLUE3", 122, 197, 205),
        ("CADETBLUE4", 83, 134, 139),
        ("CHARTREUSE", 127, 255, 0),
        ("CHARTREUSE1", 127, 255, 0),
        ("CHARTREUSE2", 118, 238, 0),
        ("CHARTREUSE3", 102, 205, 0),
        ("CHARTREUSE4", 69, 139, 0),
        ("CHOCOLATE", 210, 105, 30),
        ("CHOCOLATE1", 255, 127, 36),
        ("CHOCOLATE2", 238, 118, 33),
        ("CHOCOLATE3", 205, 102, 29),
        ("CHOCOLATE4", 139, 69, 19),
        ("COFFEE", 156, 79, 0),
        ("CORAL", 255, 127, 80),
        ("CORAL1", 255, 114, 86),
        ("CORAL2", 238, 106, 80),
        ("CORAL3", 205, 91, 69),
        ("CORAL4", 139, 62, 47),
        ("CORNFLOWERBLUE", 100, 149, 237),
        ("CORNSILK", 255, 248, 220),
        ("CORNSILK1", 255, 248, 220),
        ("CORNSILK2", 238, 232, 205),
        ("CORNSILK3", 205, 200, 177),
        ("CORNSILK4", 139, 136, 120),
        ("CYAN", 0, 255, 255),
        ("CYAN1", 0, 255, 255),
        ("CYAN2", 0, 238, 238),
        ("CYAN3", 0, 205, 205),
        ("CYAN4", 0, 139, 139),
        ("DARKBLUE", 0, 0, 139),
        ("DARKCYAN", 0, 139, 139),
        ("DARKGOLDENROD", 184, 134, 11),
        ("DARKGOLDENROD1", 255, 185, 15),
        ("DARKGOLDENROD2", 238, 173, 14),
        ("DARKGOLDENROD3", 205, 149, 12),
        ("DARKGOLDENROD4", 139, 101, 8),
        ("DARKGREEN", 0, 100, 0),
        ("DARKGRAY", 169, 169, 169),
        ("DARKKHAKI", 189, 183, 107),
        ("DARKMAGENTA", 139, 0, 139),
        ("DARKOLIVEGREEN", 85, 107, 47),
        ("DARKOLIVEGREEN1", 202, 255, 112),
        ("DARKOLIVEGREEN2", 188, 238, 104),
        ("DARKOLIVEGREEN3", 162, 205, 90),
        ("DARKOLIVEGREEN4", 110, 139, 61),
        ("DARKORANGE", 255, 140, 0),
        ("DARKORANGE1", 255, 127, 0),
        ("DARKORANGE2", 238, 118, 0),
        ("DARKORANGE3", 205, 102, 0),
        ("DARKORANGE4", 139, 69, 0),
        ("DARKORCHID", 153, 50, 204),
        ("DARKORCHID1", 191, 62, 255),
        ("DARKORCHID2", 178, 58, 238),
        ("DARKORCHID3", 154, 50, 205),
        ("DARKORCHID4", 104, 34, 139),
        ("DARKRED", 139, 0, 0),
        ("DARKSALMON", 233, 150, 122),
        ("DARKSEAGREEN", 143, 188, 143),
        ("DARKSEAGREEN1", 193, 255, 193),
        ("DARKSEAGREEN2", 180, 238, 180),
        ("DARKSEAGREEN3", 155, 205, 155),
        ("DARKSEAGREEN4", 105, 139, 105),
        ("DARKSLATEBLUE", 72, 61, 139),
        ("DARKSLATEGRAY", 47, 79, 79),
        ("DARKTURQUOISE", 0, 206, 209),
        ("DARKVIOLET", 148, 0, 211),
        ("DEEPPINK", 255, 20, 147),
        ("DEEPPINK1", 255, 20, 147),
        ("DEEPPINK2", 238, 18, 137),
        ("DEEPPINK3", 205, 16, 118),
        ("DEEPPINK4", 139, 10, 80),
        ("DEEPSKYBLUE", 0, 191, 255),
        ("DEEPSKYBLUE1", 0, 191, 255),
        ("DEEPSKYBLUE2", 0, 178, 238),
        ("DEEPSKYBLUE3", 0, 154, 205),
        ("DEEPSKYBLUE4", 0, 104, 139),
        ("DIMGRAY", 105, 105, 105),
        ("DODGERBLUE", 30, 144, 255),
        ("DODGERBLUE1", 30, 144, 255),
        ("DODGERBLUE2", 28, 134, 238),
        ("DODGERBLUE3", 24, 116, 205),
        ("DODGERBLUE4", 16, 78, 139),
        ("FIREBRICK", 178, 34, 34),
        ("FIREBRICK1", 255, 48, 48),
        ("FIREBRICK2", 238, 44, 44),
        ("FIREBRICK3", 205, 38, 38),
        ("FIREBRICK4", 139, 26, 26),
        ("FLORALWHITE", 255, 250, 240),
        ("FORESTGREEN", 34, 139, 34),
        ("GAINSBORO", 220, 220, 220),
        ("GHOSTWHITE", 248, 248, 255),
        ("GOLD", 255, 215, 0),
        ("GOLD1", 255, 215, 0),
        ("GOLD2", 238, 201, 0),
        ("GOLD3", 205, 173, 0),
        ("GOLD4", 139, 117, 0),
        ("GOLDENROD", 218, 165, 32),
        ("GOLDENROD1", 255, 193, 37),
        ("GOLDENROD2", 238, 180, 34),
        ("GOLDENROD3", 205, 155, 29),
        ("GOLDENROD4", 139, 105, 20),
        ("GREEN YELLOW", 173, 255, 47),
        ("GREEN", 0, 255, 0),
        ("GREEN1", 0, 255, 0),
        ("GREEN2", 0, 238, 0),
        ("GREEN3", 0, 205, 0),
        ("GREEN4", 0, 139, 0),
        ("GREENYELLOW", 173, 255, 47),
        ("GRAY", 190, 190, 190),
        ("GRAY0", 0, 0, 0),
        ("GRAY1", 3, 3, 3),
        ("GRAY10", 26, 26, 26),
        ("GRAY100", 255, 255, 255),
        ("GRAY11", 28, 28, 28),
        ("GRAY12", 31, 31, 31),
        ("GRAY13", 33, 33, 33),
        ("GRAY14", 36, 36, 36),
        ("GRAY15", 38, 38, 38),
        ("GRAY16", 41, 41, 41),
        ("GRAY17", 43, 43, 43),
        ("GRAY18", 46, 46, 46),
        ("GRAY19", 48, 48, 48),
        ("GRAY2", 5, 5, 5),
        ("GRAY20", 51, 51, 51),
        ("GRAY21", 54, 54, 54),
        ("GRAY22", 56, 56, 56),
        ("GRAY23", 59, 59, 59),
        ("GRAY24", 61, 61, 61),
        ("GRAY25", 64, 64, 64),
        ("GRAY26", 66, 66, 66),
        ("GRAY27", 69, 69, 69),
        ("GRAY28", 71, 71, 71),
        ("GRAY29", 74, 74, 74),
        ("GRAY3", 8, 8, 8),
        ("GRAY30", 77, 77, 77),
        ("GRAY31", 79, 79, 79),
        ("GRAY32", 82, 82, 82),
        ("GRAY33", 84, 84, 84),
        ("GRAY34", 87, 87, 87),
        ("GRAY35", 89, 89, 89),
        ("GRAY36", 92, 92, 92),
        ("GRAY37", 94, 94, 94),
        ("GRAY38", 97, 97, 97),
        ("GRAY39", 99, 99, 99),
        ("GRAY4", 10, 10, 10),
        ("GRAY40", 102, 102, 102),
        ("GRAY41", 105, 105, 105),
        ("GRAY42", 107, 107, 107),
        ("GRAY43", 110, 110, 110),
        ("GRAY44", 112, 112, 112),
        ("GRAY45", 115, 115, 115),
        ("GRAY46", 117, 117, 117),
        ("GRAY47", 120, 120, 120),
        ("GRAY48", 122, 122, 122),
        ("GRAY49", 125, 125, 125),
        ("GRAY5", 13, 13, 13),
        ("GRAY50", 127, 127, 127),
        ("GRAY51", 130, 130, 130),
        ("GRAY52", 133, 133, 133),
        ("GRAY53", 135, 135, 135),
        ("GRAY54", 138, 138, 138),
        ("GRAY55", 140, 140, 140),
        ("GRAY56", 143, 143, 143),
        ("GRAY57", 145, 145, 145),
        ("GRAY58", 148, 148, 148),
        ("GRAY59", 150, 150, 150),
        ("GRAY6", 15, 15, 15),
        ("GRAY60", 153, 153, 153),
        ("GRAY61", 156, 156, 156),
        ("GRAY62", 158, 158, 158),
        ("GRAY63", 161, 161, 161),
        ("GRAY64", 163, 163, 163),
        ("GRAY65", 166, 166, 166),
        ("GRAY66", 168, 168, 168),
        ("GRAY67", 171, 171, 171),
        ("GRAY68", 173, 173, 173),
        ("GRAY69", 176, 176, 176),
        ("GRAY7", 18, 18, 18),
        ("GRAY70", 179, 179, 179),
        ("GRAY71", 181, 181, 181),
        ("GRAY72", 184, 184, 184),
        ("GRAY73", 186, 186, 186),
        ("GRAY74", 189, 189, 189),
        ("GRAY75", 191, 191, 191),
        ("GRAY76", 194, 194, 194),
        ("GRAY77", 196, 196, 196),
        ("GRAY78", 199, 199, 199),
        ("GRAY79", 201, 201, 201),
        ("GRAY8", 20, 20, 20),
        ("GRAY80", 204, 204, 204),
        ("GRAY81", 207, 207, 207),
        ("GRAY82", 209, 209, 209),
        ("GRAY83", 212, 212, 212),
        ("GRAY84", 214, 214, 214),
        ("GRAY85", 217, 217, 217),
        ("GRAY86", 219, 219, 219),
        ("GRAY87", 222, 222, 222),
        ("GRAY88", 224, 224, 224),
        ("GRAY89", 227, 227, 227),
        ("GRAY9", 23, 23, 23),
        ("GRAY90", 229, 229, 229),
        ("GRAY91", 232, 232, 232),
        ("GRAY92", 235, 235, 235),
        ("GRAY93", 237, 237, 237),
        ("GRAY94", 240, 240, 240),
        ("GRAY95", 242, 242, 242),
        ("GRAY96", 245, 245, 245),
        ("GRAY97", 247, 247, 247),
        ("GRAY98", 250, 250, 250),
        ("GRAY99", 252, 252, 252),
        ("HONEYDEW", 240, 255, 240),
        ("HONEYDEW1", 240, 255, 240),
        ("HONEYDEW2", 224, 238, 224),
        ("HONEYDEW3", 193, 205, 193),
        ("HONEYDEW4", 131, 139, 131),
        ("HOTPINK", 255, 105, 180),
        ("HOTPINK1", 255, 110, 180),
        ("HOTPINK2", 238, 106, 167),
        ("HOTPINK3", 205, 96, 144),
        ("HOTPINK4", 139, 58, 98),
        ("INDIANRED", 205, 92, 92),
        ("INDIANRED1", 255, 106, 106),
        ("INDIANRED2", 238, 99, 99),
        ("INDIANRED3", 205, 85, 85),
        ("INDIANRED4", 139, 58, 58),
        ("IVORY", 255, 255, 240),
        ("IVORY1", 255, 255, 240),
        ("IVORY2", 238, 238, 224),
        ("IVORY3", 205, 205, 193),
        ("IVORY4", 139, 139, 131),
        ("KHAKI", 240, 230, 140),
        ("KHAKI1", 255, 246, 143),
        ("KHAKI2", 238, 230, 133),
        ("KHAKI3", 205, 198, 115),
        ("KHAKI4", 139, 134, 78),
        ("LAVENDER", 230, 230, 250),
        ("LAVENDERBLUSH", 255, 240, 245),
        ("LAVENDERBLUSH1", 255, 240, 245),
        ("LAVENDERBLUSH2", 238, 224, 229),
        ("LAVENDERBLUSH3", 205, 193, 197),
        ("LAVENDERBLUSH4", 139, 131, 134),
        ("LAWNGREEN", 124, 252, 0),
        ("LEMONCHIFFON", 255, 250, 205),
        ("LEMONCHIFFON1", 255, 250, 205),
        ("LEMONCHIFFON2", 238, 233, 191),
        ("LEMONCHIFFON3", 205, 201, 165),
        ("LEMONCHIFFON4", 139, 137, 112),
        ("LIGHTBLUE", 173, 216, 230),
        ("LIGHTBLUE1", 191, 239, 255),
        ("LIGHTBLUE2", 178, 223, 238),
        ("LIGHTBLUE3", 154, 192, 205),
        ("LIGHTBLUE4", 104, 131, 139),
        ("LIGHTCORAL", 240, 128, 128),
        ("LIGHTCYAN", 224, 255, 255),
        ("LIGHTCYAN1", 224, 255, 255),
        ("LIGHTCYAN2", 209, 238, 238),
        ("LIGHTCYAN3", 180, 205, 205),
        ("LIGHTCYAN4", 122, 139, 139),
        ("LIGHTGOLDENROD", 238, 221, 130),
        ("LIGHTGOLDENROD1", 255, 236, 139),
        ("LIGHTGOLDENROD2", 238, 220, 130),
        ("LIGHTGOLDENROD3", 205, 190, 112),
        ("LIGHTGOLDENROD4", 139, 129, 76),
        ("LIGHTGOLDENRODYELLOW", 250, 250, 210),
        ("LIGHTGREEN", 144, 238, 144),
        ("LIGHTGRAY", 211, 211, 211),
        ("LIGHTPINK", 255, 182, 193),
        ("LIGHTPINK1", 255, 174, 185),
        ("LIGHTPINK2", 238, 162, 173),
        ("LIGHTPINK3", 205, 140, 149),
        ("LIGHTPINK4", 139, 95, 101),
        ("LIGHTSALMON", 255, 160, 122),
        ("LIGHTSALMON1", 255, 160, 122),
        ("LIGHTSALMON2", 238, 149, 114),
        ("LIGHTSALMON3", 205, 129, 98),
        ("LIGHTSALMON4", 139, 87, 66),
        ("LIGHTSEAGREEN", 32, 178, 170),
        ("LIGHTSKYBLUE", 135, 206, 250),
        ("LIGHTSKYBLUE1", 176, 226, 255),
        ("LIGHTSKYBLUE2", 164, 211, 238),
        ("LIGHTSKYBLUE3", 141, 182, 205),
        ("LIGHTSKYBLUE4", 96, 123, 139),
        ("LIGHTSLATEBLUE", 132, 112, 255),
        ("LIGHTSLATEGRAY", 119, 136, 153),
        ("LIGHTSTEELBLUE", 176, 196, 222),
        ("LIGHTSTEELBLUE1", 202, 225, 255),
        ("LIGHTSTEELBLUE2", 188, 210, 238),
        ("LIGHTSTEELBLUE3", 162, 181, 205),
        ("LIGHTSTEELBLUE4", 110, 123, 139),
        ("LIGHTYELLOW", 255, 255, 224),
        ("LIGHTYELLOW1", 255, 255, 224),
        ("LIGHTYELLOW2", 238, 238, 209),
        ("LIGHTYELLOW3", 205, 205, 180),
        ("LIGHTYELLOW4", 139, 139, 122),
        ("LIMEGREEN", 50, 205, 50),
        ("LINEN", 250, 240, 230),
        ("MAGENTA", 255, 0, 255),
        ("MAGENTA1", 255, 0, 255),
        ("MAGENTA2", 238, 0, 238),
        ("MAGENTA3", 205, 0, 205),
        ("MAGENTA4", 139, 0, 139),
        ("MAROON", 176, 48, 96),
        ("MAROON1", 255, 52, 179),
        ("MAROON2", 238, 48, 167),
        ("MAROON3", 205, 41, 144),
        ("MAROON4", 139, 28, 98),
        ("MEDIUMAQUAMARINE", 102, 205, 170),
        ("MEDIUMBLUE", 0, 0, 205),
        ("MEDIUMORCHID", 186, 85, 211),
        ("MEDIUMORCHID1", 224, 102, 255),
        ("MEDIUMORCHID2", 209, 95, 238),
        ("MEDIUMORCHID3", 180, 82, 205),
        ("MEDIUMORCHID4", 122, 55, 139),
        ("MEDIUMPURPLE", 147, 112, 219),
        ("MEDIUMPURPLE1", 171, 130, 255),
        ("MEDIUMPURPLE2", 159, 121, 238),
        ("MEDIUMPURPLE3", 137, 104, 205),
        ("MEDIUMPURPLE4", 93, 71, 139),
        ("MEDIUMSEAGREEN", 60, 179, 113),
        ("MEDIUMSLATEBLUE", 123, 104, 238),
        ("MEDIUMSPRINGGREEN", 0, 250, 154),
        ("MEDIUMTURQUOISE", 72, 209, 204),
        ("MEDIUMVIOLETRED", 199, 21, 133),
        ("MIDNIGHTBLUE", 25, 25, 112),
        ("MINTCREAM", 245, 255, 250),
        ("MISTYROSE", 255, 228, 225),
        ("MISTYROSE1", 255, 228, 225),
        ("MISTYROSE2", 238, 213, 210),
        ("MISTYROSE3", 205, 183, 181),
        ("MISTYROSE4", 139, 125, 123),
        ("MOCCASIN", 255, 228, 181),
        ("MUPDFBLUE", 37, 114, 172),
        ("NAVAJOWHITE", 255, 222, 173),
        ("NAVAJOWHITE1", 255, 222, 173),
        ("NAVAJOWHITE2", 238, 207, 161),
        ("NAVAJOWHITE3", 205, 179, 139),
        ("NAVAJOWHITE4", 139, 121, 94),
        ("NAVY", 0, 0, 128),
        ("NAVYBLUE", 0, 0, 128),
        ("OLDLACE", 253, 245, 230),
        ("OLIVEDRAB", 107, 142, 35),
        ("OLIVEDRAB1", 192, 255, 62),
        ("OLIVEDRAB2", 179, 238, 58),
        ("OLIVEDRAB3", 154, 205, 50),
        ("OLIVEDRAB4", 105, 139, 34),
        ("ORANGE", 255, 165, 0),
        ("ORANGE1", 255, 165, 0),
        ("ORANGE2", 238, 154, 0),
        ("ORANGE3", 205, 133, 0),
        ("ORANGE4", 139, 90, 0),
        ("ORANGERED", 255, 69, 0),
        ("ORANGERED1", 255, 69, 0),
        ("ORANGERED2", 238, 64, 0),
        ("ORANGERED3", 205, 55, 0),
        ("ORANGERED4", 139, 37, 0),
        ("ORCHID", 218, 112, 214),
        ("ORCHID1", 255, 131, 250),
        ("ORCHID2", 238, 122, 233),
        ("ORCHID3", 205, 105, 201),
        ("ORCHID4", 139, 71, 137),
        ("PALEGOLDENROD", 238, 232, 170),
        ("PALEGREEN", 152, 251, 152),
        ("PALEGREEN1", 154, 255, 154),
        ("PALEGREEN2", 144, 238, 144),
        ("PALEGREEN3", 124, 205, 124),
        ("PALEGREEN4", 84, 139, 84),
        ("PALETURQUOISE", 175, 238, 238),
        ("PALETURQUOISE1", 187, 255, 255),
        ("PALETURQUOISE2", 174, 238, 238),
        ("PALETURQUOISE3", 150, 205, 205),
        ("PALETURQUOISE4", 102, 139, 139),
        ("PALEVIOLETRED", 219, 112, 147),
        ("PALEVIOLETRED1", 255, 130, 171),
        ("PALEVIOLETRED2", 238, 121, 159),
        ("PALEVIOLETRED3", 205, 104, 137),
        ("PALEVIOLETRED4", 139, 71, 93),
        ("PAPAYAWHIP", 255, 239, 213),
        ("PEACHPUFF", 255, 218, 185),
        ("PEACHPUFF1", 255, 218, 185),
        ("PEACHPUFF2", 238, 203, 173),
        ("PEACHPUFF3", 205, 175, 149),
        ("PEACHPUFF4", 139, 119, 101),
        ("PERU", 205, 133, 63),
        ("PINK", 255, 192, 203),
        ("PINK1", 255, 181, 197),
        ("PINK2", 238, 169, 184),
        ("PINK3", 205, 145, 158),
        ("PINK4", 139, 99, 108),
        ("PLUM", 221, 160, 221),
        ("PLUM1", 255, 187, 255),
        ("PLUM2", 238, 174, 238),
        ("PLUM3", 205, 150, 205),
        ("PLUM4", 139, 102, 139),
        ("POWDERBLUE", 176, 224, 230),
        ("PURPLE", 160, 32, 240),
        ("PURPLE1", 155, 48, 255),
        ("PURPLE2", 145, 44, 238),
        ("PURPLE3", 125, 38, 205),
        ("PURPLE4", 85, 26, 139),
        ("PY_COLOR", 240, 255, 210),
        ("RED", 255, 0, 0),
        ("RED1", 255, 0, 0),
        ("RED2", 238, 0, 0),
        ("RED3", 205, 0, 0),
        ("RED4", 139, 0, 0),
        ("ROSYBROWN", 188, 143, 143),
        ("ROSYBROWN1", 255, 193, 193),
        ("ROSYBROWN2", 238, 180, 180),
        ("ROSYBROWN3", 205, 155, 155),
        ("ROSYBROWN4", 139, 105, 105),
        ("ROYALBLUE", 65, 105, 225),
        ("ROYALBLUE1", 72, 118, 255),
        ("ROYALBLUE2", 67, 110, 238),
        ("ROYALBLUE3", 58, 95, 205),
        ("ROYALBLUE4", 39, 64, 139),
        ("SADDLEBROWN", 139, 69, 19),
        ("SALMON", 250, 128, 114),
        ("SALMON1", 255, 140, 105),
        ("SALMON2", 238, 130, 98),
        ("SALMON3", 205, 112, 84),
        ("SALMON4", 139, 76, 57),
        ("SANDYBROWN", 244, 164, 96),
        ("SEAGREEN", 46, 139, 87),
        ("SEAGREEN1", 84, 255, 159),
        ("SEAGREEN2", 78, 238, 148),
        ("SEAGREEN3", 67, 205, 128),
        ("SEAGREEN4", 46, 139, 87),
        ("SEASHELL", 255, 245, 238),
        ("SEASHELL1", 255, 245, 238),
        ("SEASHELL2", 238, 229, 222),
        ("SEASHELL3", 205, 197, 191),
        ("SEASHELL4", 139, 134, 130),
        ("SIENNA", 160, 82, 45),
        ("SIENNA1", 255, 130, 71),
        ("SIENNA2", 238, 121, 66),
        ("SIENNA3", 205, 104, 57),
        ("SIENNA4", 139, 71, 38),
        ("SKYBLUE", 135, 206, 235),
        ("SKYBLUE1", 135, 206, 255),
        ("SKYBLUE2", 126, 192, 238),
        ("SKYBLUE3", 108, 166, 205),
        ("SKYBLUE4", 74, 112, 139),
        ("SLATEBLUE", 106, 90, 205),
        ("SLATEBLUE1", 131, 111, 255),
        ("SLATEBLUE2", 122, 103, 238),
        ("SLATEBLUE3", 105, 89, 205),
        ("SLATEBLUE4", 71, 60, 139),
        ("SLATEGRAY", 112, 128, 144),
        ("SNOW", 255, 250, 250),
        ("SNOW1", 255, 250, 250),
        ("SNOW2", 238, 233, 233),
        ("SNOW3", 205, 201, 201),
        ("SNOW4", 139, 137, 137),
        ("SPRINGGREEN", 0, 255, 127),
        ("SPRINGGREEN1", 0, 255, 127),
        ("SPRINGGREEN2", 0, 238, 118),
        ("SPRINGGREEN3", 0, 205, 102),
        ("SPRINGGREEN4", 0, 139, 69),
        ("STEELBLUE", 70, 130, 180),
        ("STEELBLUE1", 99, 184, 255),
        ("STEELBLUE2", 92, 172, 238),
        ("STEELBLUE3", 79, 148, 205),
        ("STEELBLUE4", 54, 100, 139),
        ("TAN", 210, 180, 140),
        ("TAN1", 255, 165, 79),
        ("TAN2", 238, 154, 73),
        ("TAN3", 205, 133, 63),
        ("TAN4", 139, 90, 43),
        ("THISTLE", 216, 191, 216),
        ("THISTLE1", 255, 225, 255),
        ("THISTLE2", 238, 210, 238),
        ("THISTLE3", 205, 181, 205),
        ("THISTLE4", 139, 123, 139),
        ("TOMATO", 255, 99, 71),
        ("TOMATO1", 255, 99, 71),
        ("TOMATO2", 238, 92, 66),
        ("TOMATO3", 205, 79, 57),
        ("TOMATO4", 139, 54, 38),
        ("TURQUOISE", 64, 224, 208),
        ("TURQUOISE1", 0, 245, 255),
        ("TURQUOISE2", 0, 229, 238),
        ("TURQUOISE3", 0, 197, 205),
        ("TURQUOISE4", 0, 134, 139),
        ("VIOLET", 238, 130, 238),
        ("VIOLETRED", 208, 32, 144),
        ("VIOLETRED1", 255, 62, 150),
        ("VIOLETRED2", 238, 58, 140),
        ("VIOLETRED3", 205, 50, 120),
        ("VIOLETRED4", 139, 34, 82),
        ("WHEAT", 245, 222, 179),
        ("WHEAT1", 255, 231, 186),
        ("WHEAT2", 238, 216, 174),
        ("WHEAT3", 205, 186, 150),
        ("WHEAT4", 139, 126, 102),
        ("WHITE", 255, 255, 255),
        ("WHITESMOKE", 245, 245, 245),
        ("YELLOW", 255, 255, 0),
        ("YELLOW1", 255, 255, 0),
        ("YELLOW2", 238, 238, 0),
        ("YELLOW3", 205, 205, 0),
        ("YELLOW4", 139, 139, 0),
        ("YELLOWGREEN", 154, 205, 50),
    ]


def getColorInfoDict() -> dict:
    d = {}
    for item in getColorInfoList():
        d[item[0].lower()] = item[1:]
    return d


def getColor(name: str) -> tuple:
    """Retrieve RGB color in PDF format by name.

    Returns:
        a triple of floats in range 0 to 1. In case of name-not-found, "white" is returned.
    """
    try:
        c = getColorInfoList()[getColorList().index(name.upper())]
        return (c[1] / 255.0, c[2] / 255.0, c[3] / 255.0)
    except:
        return (1, 1, 1)


def getColorHSV(name: str) -> tuple:
    """Retrieve the hue, saturation, value triple of a color name.

    Returns:
        a triple (degree, percent, percent). If not found (-1, -1, -1) is returned.
    """
    try:
        x = getColorInfoList()[getColorList().index(name.upper())]
    except:
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


def _get_font_properties(doc: Document, xref: int) -> tuple:
    fontname, ext, stype, buffer = doc.extract_font(xref)
    asc = 0.8
    dsc = -0.2
    if ext == "":
        return fontname, ext, stype, asc, dsc

    if buffer:
        try:
            font = Font(fontbuffer=buffer)
            asc = font.ascender
            dsc = font.descender
            bbox = font.bbox
            if asc - dsc < 1:
                if bbox.y0 < dsc:
                    dsc = bbox.y0
                asc = 1 - dsc
        except:
            asc *= 1.2
            dsc *= 1.2
        return fontname, ext, stype, asc, dsc
    if ext != "n/a":
        try:
            font = Font(fontname)
            asc = font.ascender
            dsc = font.descender
        except:
            asc *= 1.2
            dsc *= 1.2
    else:
        asc *= 1.2
        dsc *= 1.2
    return fontname, ext, stype, asc, dsc


def get_char_widths(
    doc: Document, xref: int, limit: int = 256, idx: int = 0, fontdict: OptDict = None
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
    fontinfo = CheckFontInfo(doc, xref)
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
            glyphs = zapf_glyphs
        elif name == "Symbol":
            glyphs = symbol_glyphs
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
    UpdateFontInfo(doc, fontinfo)

    return glyphs


class Shape(object):
    """Create a new shape."""

    @staticmethod
    def horizontal_angle(C, P):
        """Return the angle to the horizontal for the connection from C to P.
        This uses the arcus sine function and resolves its inherent ambiguity by
        looking up in which quadrant vector S = P - C is located.
        """
        S = Point(P - C).unit  # unit vector 'C' -> 'P'
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

    def __init__(self, page: Page):
        CheckParent(page)
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
        self.lastPoint = None
        self.rect = None

    def updateRect(self, x):
        if self.rect is None:
            if len(x) == 2:
                self.rect = Rect(x, x)
            else:
                self.rect = Rect(x)

        else:
            if len(x) == 2:
                x = Point(x)
                self.rect.x0 = min(self.rect.x0, x.x)
                self.rect.y0 = min(self.rect.y0, x.y)
                self.rect.x1 = max(self.rect.x1, x.x)
                self.rect.y1 = max(self.rect.y1, x.y)
            else:
                x = Rect(x)
                self.rect.x0 = min(self.rect.x0, x.x0)
                self.rect.y0 = min(self.rect.y0, x.y0)
                self.rect.x1 = max(self.rect.x1, x.x1)
                self.rect.y1 = max(self.rect.y1, x.y1)

    def draw_line(self, p1: point_like, p2: point_like) -> Point:
        """Draw a line between two points."""
        p1 = Point(p1)
        p2 = Point(p2)
        if not (self.lastPoint == p1):
            self.draw_cont += "%g %g m\n" % JM_TUPLE(p1 * self.ipctm)
            self.lastPoint = p1
            self.updateRect(p1)

        self.draw_cont += "%g %g l\n" % JM_TUPLE(p2 * self.ipctm)
        self.updateRect(p2)
        self.lastPoint = p2
        return self.lastPoint

    def draw_polyline(self, points: list) -> Point:
        """Draw several connected line segments."""
        for i, p in enumerate(points):
            if i == 0:
                if not (self.lastPoint == Point(p)):
                    self.draw_cont += "%g %g m\n" % JM_TUPLE(Point(p) * self.ipctm)
                    self.lastPoint = Point(p)
            else:
                self.draw_cont += "%g %g l\n" % JM_TUPLE(Point(p) * self.ipctm)
            self.updateRect(p)

        self.lastPoint = Point(points[-1])
        return self.lastPoint

    def draw_bezier(
        self,
        p1: point_like,
        p2: point_like,
        p3: point_like,
        p4: point_like,
    ) -> Point:
        """Draw a standard cubic Bezier curve."""
        p1 = Point(p1)
        p2 = Point(p2)
        p3 = Point(p3)
        p4 = Point(p4)
        if not (self.lastPoint == p1):
            self.draw_cont += "%g %g m\n" % JM_TUPLE(p1 * self.ipctm)
        self.draw_cont += "%g %g %g %g %g %g c\n" % JM_TUPLE(
            list(p2 * self.ipctm) + list(p3 * self.ipctm) + list(p4 * self.ipctm)
        )
        self.updateRect(p1)
        self.updateRect(p2)
        self.updateRect(p3)
        self.updateRect(p4)
        self.lastPoint = p4
        return self.lastPoint

    def draw_oval(self, tetra: typing.Union[quad_like, rect_like]) -> Point:
        """Draw an ellipse inside a tetrapod."""
        if len(tetra) != 4:
            raise ValueError("invalid arg length")
        if hasattr(tetra[0], "__float__"):
            q = Rect(tetra).quad
        else:
            q = Quad(tetra)

        mt = q.ul + (q.ur - q.ul) * 0.5
        mr = q.ur + (q.lr - q.ur) * 0.5
        mb = q.ll + (q.lr - q.ll) * 0.5
        ml = q.ul + (q.ll - q.ul) * 0.5
        if not (self.lastPoint == ml):
            self.draw_cont += "%g %g m\n" % JM_TUPLE(ml * self.ipctm)
            self.lastPoint = ml
        self.draw_curve(ml, q.ll, mb)
        self.draw_curve(mb, q.lr, mr)
        self.draw_curve(mr, q.ur, mt)
        self.draw_curve(mt, q.ul, ml)
        self.updateRect(q.rect)
        self.lastPoint = ml
        return self.lastPoint

    def draw_circle(self, center: point_like, radius: float) -> Point:
        """Draw a circle given its center and radius."""
        if not radius > EPSILON:
            raise ValueError("radius must be positive")
        center = Point(center)
        p1 = center - (radius, 0)
        return self.draw_sector(center, p1, 360, fullSector=False)

    def draw_curve(
        self,
        p1: point_like,
        p2: point_like,
        p3: point_like,
    ) -> Point:
        """Draw a curve between points using one control point."""
        kappa = 0.55228474983
        p1 = Point(p1)
        p2 = Point(p2)
        p3 = Point(p3)
        k1 = p1 + (p2 - p1) * kappa
        k2 = p3 + (p2 - p3) * kappa
        return self.draw_bezier(p1, k1, k2, p3)

    def draw_sector(
        self,
        center: point_like,
        point: point_like,
        beta: float,
        fullSector: bool = True,
    ) -> Point:
        """Draw a circle sector."""
        center = Point(center)
        point = Point(point)
        l3 = "%g %g m\n"
        l4 = "%g %g %g %g %g %g c\n"
        l5 = "%g %g l\n"
        betar = math.radians(-beta)
        w360 = math.radians(math.copysign(360, betar)) * (-1)
        w90 = math.radians(math.copysign(90, betar))
        w45 = w90 / 2
        while abs(betar) > 2 * math.pi:
            betar += w360  # bring angle below 360 degrees
        if not (self.lastPoint == point):
            self.draw_cont += l3 % JM_TUPLE(point * self.ipctm)
            self.lastPoint = point
        Q = Point(0, 0)  # just make sure it exists
        C = center
        P = point
        S = P - C  # vector 'center' -> 'point'
        rad = abs(S)  # circle radius

        if not rad > EPSILON:
            raise ValueError("radius must be positive")

        alfa = self.horizontal_angle(center, point)
        while abs(betar) > abs(w90):  # draw 90 degree arcs
            q1 = C.x + math.cos(alfa + w90) * rad
            q2 = C.y + math.sin(alfa + w90) * rad
            Q = Point(q1, q2)  # the arc's end point
            r1 = C.x + math.cos(alfa + w45) * rad / math.cos(w45)
            r2 = C.y + math.sin(alfa + w45) * rad / math.cos(w45)
            R = Point(r1, r2)  # crossing point of tangents
            kappah = (1 - math.cos(w45)) * 4 / 3 / abs(R - Q)
            kappa = kappah * abs(P - Q)
            cp1 = P + (R - P) * kappa  # control point 1
            cp2 = Q + (R - Q) * kappa  # control point 2
            self.draw_cont += l4 % JM_TUPLE(
                list(cp1 * self.ipctm) + list(cp2 * self.ipctm) + list(Q * self.ipctm)
            )

            betar -= w90  # reduce parm angle by 90 deg
            alfa += w90  # advance start angle by 90 deg
            P = Q  # advance to arc end point
        # draw (remaining) arc
        if abs(betar) > 1e-3:  # significant degrees left?
            beta2 = betar / 2
            q1 = C.x + math.cos(alfa + betar) * rad
            q2 = C.y + math.sin(alfa + betar) * rad
            Q = Point(q1, q2)  # the arc's end point
            r1 = C.x + math.cos(alfa + beta2) * rad / math.cos(beta2)
            r2 = C.y + math.sin(alfa + beta2) * rad / math.cos(beta2)
            R = Point(r1, r2)  # crossing point of tangents
            # kappa height is 4/3 of segment height
            kappah = (1 - math.cos(beta2)) * 4 / 3 / abs(R - Q)  # kappa height
            kappa = kappah * abs(P - Q) / (1 - math.cos(betar))
            cp1 = P + (R - P) * kappa  # control point 1
            cp2 = Q + (R - Q) * kappa  # control point 2
            self.draw_cont += l4 % JM_TUPLE(
                list(cp1 * self.ipctm) + list(cp2 * self.ipctm) + list(Q * self.ipctm)
            )
        if fullSector:
            self.draw_cont += l3 % JM_TUPLE(point * self.ipctm)
            self.draw_cont += l5 % JM_TUPLE(center * self.ipctm)
            self.draw_cont += l5 % JM_TUPLE(Q * self.ipctm)
        self.lastPoint = Q
        return self.lastPoint

    def draw_rect(self, rect: rect_like, *, radius=None) -> Point:
        """Draw a rectangle.

        Args:
            radius: if not None, the rectangle will have rounded corners.
                This is the radius of the curvature, given as percentage of
                the rectangle width or height. Valid are values 0 < v <= 0.5.
                For a sequence of two values, the corners will have different
                radii. Otherwise, the percentage will be computed from the
                shorter side. A value of (0.5, 0.5) will draw an ellipse.
        """
        r = Rect(rect)
        if radius == None:  # standard rectangle
            self.draw_cont += "%g %g %g %g re\n" % JM_TUPLE(
                list(r.bl * self.ipctm) + [r.width, r.height]
            )
            self.updateRect(r)
            self.lastPoint = r.tl
            return self.lastPoint
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
        self.lastPoint = self.draw_curve(lp, r.tl, r.tl + py)

        self.updateRect(r)
        return self.lastPoint

    def draw_quad(self, quad: quad_like) -> Point:
        """Draw a Quad."""
        q = Quad(quad)
        return self.draw_polyline([q.ul, q.ll, q.lr, q.ur, q.ul])

    def draw_zigzag(
        self,
        p1: point_like,
        p2: point_like,
        breadth: float = 2,
    ) -> Point:
        """Draw a zig-zagged line from p1 to p2."""
        p1 = Point(p1)
        p2 = Point(p2)
        S = p2 - p1  # vector start - end
        rad = abs(S)  # distance of points
        cnt = 4 * int(round(rad / (4 * breadth), 0))  # always take full phases
        if cnt < 4:
            raise ValueError("points too close")
        mb = rad / cnt  # revised breadth
        matrix = Matrix(util_hor_matrix(p1, p2))  # normalize line to x-axis
        i_mat = ~matrix  # get original position
        points = []  # stores edges
        for i in range(1, cnt):
            if i % 4 == 1:  # point "above" connection
                p = Point(i, -1) * mb
            elif i % 4 == 3:  # point "below" connection
                p = Point(i, 1) * mb
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
    ) -> Point:
        """Draw a squiggly line from p1 to p2."""
        p1 = Point(p1)
        p2 = Point(p2)
        S = p2 - p1  # vector start - end
        rad = abs(S)  # distance of points
        cnt = 4 * int(round(rad / (4 * breadth), 0))  # always take full phases
        if cnt < 4:
            raise ValueError("points too close")
        mb = rad / cnt  # revised breadth
        matrix = Matrix(util_hor_matrix(p1, p2))  # normalize line to x-axis
        i_mat = ~matrix  # get original position
        k = 2.4142135623765633  # y of draw_curve helper point

        points = []  # stores edges
        for i in range(1, cnt):
            if i % 4 == 1:  # point "above" connection
                p = Point(i, -k) * mb
            elif i % 4 == 3:  # point "below" connection
                p = Point(i, k) * mb
            else:  # else on connection line
                p = Point(i, 0) * mb
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
        fontsize: float = 11,
        lineheight: OptFloat = None,
        fontname: str = "helv",
        fontfile: OptStr = None,
        set_simple: bool = 0,
        encoding: int = 0,
        color: OptSeq = None,
        fill: OptSeq = None,
        render_mode: int = 0,
        border_width: float = 1,
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

        point = Point(point)
        try:
            maxcode = max([ord(c) for c in " ".join(text)])
        except:
            return 0

        # ensure valid 'fontname'
        fname = fontname
        if fname.startswith("/"):
            fname = fname[1:]

        xref = self.page.insert_font(
            fontname=fname, fontfile=fontfile, encoding=encoding, set_simple=set_simple
        )
        fontinfo = CheckFontInfo(self.doc, xref)

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
            tab.append(getTJstr(t, g, simple, ordering))
        text = tab

        color_str = ColorCode(color, "c")
        fill_str = ColorCode(fill, "f")
        if not fill and render_mode == 0:  # ensure fill color when 0 Tr
            fill = color
            fill_str = ColorCode(color, "f")

        morphing = CheckMorph(morph)
        rot = rotate
        if rot % 90 != 0:
            raise ValueError("bad rotate value")

        while rot < 0:
            rot += 360
        rot = rot % 360  # text rotate = 0, 90, 270, 180

        templ1 = "\nq\n%s%sBT\n%s1 0 0 1 %g %g Tm\n/%s %g Tf "
        templ2 = "TJ\n0 -%g TD\n"
        cmp90 = "0 1 -1 0 0 0 cm\n"  # rotates 90 deg counter-clockwise
        cmm90 = "0 -1 1 0 0 0 cm\n"  # rotates 90 deg clockwise
        cm180 = "-1 0 0 -1 0 0 cm\n"  # rotates by 180 deg.
        height = self.height
        width = self.width

        # setting up for standard rotation directions
        # case rotate = 0
        if morphing:
            m1 = Matrix(1, 0, 0, 1, morph[0].x + self.x, height - morph[0].y - self.y)
            mat = ~m1 * morph[1] * m1
            cm = "%g %g %g %g %g %g cm\n" % JM_TUPLE(mat)
        else:
            cm = ""
        top = height - point.y - self.y  # start of 1st char
        left = point.x + self.x  # start of 1. char
        space = top  # space available
        headroom = point.y + self.y  # distance to page border
        if rot == 90:
            left = height - point.y - self.y
            top = -point.x - self.x
            cm += cmp90
            space = width - abs(top)
            headroom = point.x + self.x

        elif rot == 270:
            left = -height + point.y + self.y
            top = point.x + self.x
            cm += cmm90
            space = abs(top)
            headroom = width - point.x - self.x

        elif rot == 180:
            left = -point.x - self.x
            top = -height + point.y + self.y
            cm += cm180
            space = abs(point.y + self.y)
            headroom = height - point.y - self.y

        optcont = self.page._get_optional_content(oc)
        if optcont != None:
            bdc = "/OC /%s BDC\n" % optcont
            emc = "EMC\n"
        else:
            bdc = emc = ""

        alpha = self.page._set_opacity(CA=stroke_opacity, ca=fill_opacity)
        if alpha == None:
            alpha = ""
        else:
            alpha = "/%s gs\n" % alpha
        nres = templ1 % (bdc, alpha, cm, left, top, fname, fontsize)
        if render_mode > 0:
            nres += "%i Tr " % render_mode
        if border_width != 1:
            nres += "%g w " % border_width
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
            nres += templ2 % lheight  # line 1
        else:
            nres += templ2[:2]
        for i in range(1, len(text)):
            if space < lheight:
                break  # no space left on page
            if i > 1:
                nres += "\nT* "
            nres += text[i] + templ2[:2]
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
        fontname: OptStr = "helv",
        fontfile: OptStr = None,
        fontsize: float = 11,
        lineheight: OptFloat = None,
        set_simple: bool = 0,
        encoding: int = 0,
        color: OptSeq = None,
        fill: OptSeq = None,
        expandtabs: int = 1,
        border_width: float = 1,
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
            border_width -- thickness of glyph borders
            expandtabs -- handles tabulators with string function
            align -- left, center, right, justified
            rotate -- 0, 90, 180, or 270 degrees
            morph -- morph box with a matrix and a fixpoint
        Returns:
            unused or deficit rectangle area (float)
        """
        rect = Rect(rect)
        if rect.is_empty or rect.is_infinite:
            raise ValueError("text box must be finite and not empty")

        color_str = ColorCode(color, "c")
        fill_str = ColorCode(fill, "f")
        if fill is None and render_mode == 0:  # ensure fill color for 0 Tr
            fill = color
            fill_str = ColorCode(color, "f")

        optcont = self.page._get_optional_content(oc)
        if optcont != None:
            bdc = "/OC /%s BDC\n" % optcont
            emc = "EMC\n"
        else:
            bdc = emc = ""

        # determine opacity / transparency
        alpha = self.page._set_opacity(CA=stroke_opacity, ca=fill_opacity)
        if alpha == None:
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
        fontinfo = CheckFontInfo(self.doc, xref)

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

        # ----------------------------------------------------------------------

        if ordering < 0:
            blen = glyphs[32][1] * fontsize  # pixel size of space character
        else:
            blen = fontsize

        text = ""  # output buffer

        if CheckMorph(morph):
            m1 = Matrix(
                1, 0, 0, 1, morph[0].x + self.x, self.height - morph[0].y - self.y
            )
            mat = ~m1 * morph[1] * m1
            cm = "%g %g %g %g %g %g cm\n" % JM_TUPLE(mat)
        else:
            cm = ""

        # ---------------------------------------------------------------------------
        # adjust for text orientation / rotation
        # ---------------------------------------------------------------------------
        progr = 1  # direction of line progress
        c_pnt = Point(0, fontsize * ascender)  # used for line progress
        if rot == 0:  # normal orientation
            point = rect.tl + c_pnt  # line 1 is 'lheight' below top
            pos = point.y + self.y  # y of first line
            maxwidth = rect.width  # pixels available in one line
            maxpos = rect.y1 + self.y  # lines must not be below this

        elif rot == 90:  # rotate counter clockwise
            c_pnt = Point(fontsize * ascender, 0)  # progress in x-direction
            point = rect.bl + c_pnt  # line 1 'lheight' away from left
            pos = point.x + self.x  # position of first line
            maxwidth = rect.height  # pixels available in one line
            maxpos = rect.x1 + self.x  # lines must not be right of this
            cm += cmp90

        elif rot == 180:  # text upside down
            # progress upwards in y direction
            c_pnt = -Point(0, fontsize * ascender)
            point = rect.br + c_pnt  # line 1 'lheight' above bottom
            pos = point.y + self.y  # position of first line
            maxwidth = rect.width  # pixels available in one line
            progr = -1  # subtract lheight for next line
            maxpos = rect.y0 + self.y  # lines must not be above this
            cm += cm180

        else:  # rotate clockwise (270 or -90)
            # progress from right to left
            c_pnt = -Point(fontsize * ascender, 0)
            point = rect.tr + c_pnt  # line 1 'lheight' left of right
            pos = point.x + self.x  # position of first line
            maxwidth = rect.height  # pixels available in one line
            progr = -1  # subtract lheight for next line
            maxpos = rect.x0 + self.x  # lines must not left of this
            cm += cmm90

        # =======================================================================
        # line loop
        # =======================================================================
        just_tab = []  # 'justify' indicators per line

        for i, line in enumerate(t0):
            line_t = line.expandtabs(expandtabs).split(" ")  # split into words
            lbuff = ""  # init line buffer
            rest = maxwidth  # available line pixels
            # ===================================================================
            # word loop
            # ===================================================================
            for word in line_t:
                pl_w = pixlen(word)  # pixel len of word
                if rest >= pl_w:  # will it fit on the line?
                    lbuff += word + " "  # yes, and append word
                    rest -= pl_w + blen  # update available line space
                    continue
                # word won't fit - output line (if not empty)
                if len(lbuff) > 0:
                    lbuff = lbuff.rstrip() + "\n"  # line full, append line break
                    text += lbuff  # append to total text
                    pos += lheight * progr  # increase line position
                    just_tab.append(True)  # line is justify candidate
                    lbuff = ""  # re-init line buffer
                rest = maxwidth  # re-init avail. space
                if pl_w <= maxwidth:  # word shorter than 1 line?
                    lbuff = word + " "  # start the line with it
                    rest = maxwidth - pl_w - blen  # update free space
                    continue
                # long word: split across multiple lines - char by char ...
                if len(just_tab) > 0:
                    just_tab[-1] = False  # reset justify indicator
                for c in word:
                    if pixlen(lbuff) <= maxwidth - pixlen(c):
                        lbuff += c
                    else:  # line full
                        lbuff += "\n"  # close line
                        text += lbuff  # append to text
                        pos += lheight * progr  # increase line position
                        just_tab.append(False)  # do not justify line
                        lbuff = c  # start new line with this char
                lbuff += " "  # finish long word
                rest = maxwidth - pixlen(lbuff)  # long word stored

            if lbuff != "":  # unprocessed line content?
                text += lbuff.rstrip()  # append to text
                just_tab.append(False)  # do not justify line
            if i < len(t0) - 1:  # not the last line?
                text += "\n"  # insert line break
                pos += lheight * progr  # increase line position

        more = (pos - maxpos) * progr  # difference to rect size limit

        if more > EPSILON:  # landed too much outside rect
            return (-1) * more  # return deficit, don't output

        more = abs(more)
        if more < EPSILON:
            more = 0  # don't bother with epsilons
        nres = "\nq\n%s%sBT\n" % (bdc, alpha) + cm  # initialize output buffer
        templ = "1 0 0 1 %g %g Tm /%s %g Tf "
        # center, right, justify: output each line with its own specifics
        text_t = text.splitlines()  # split text in lines again
        just_tab[-1] = False  # never justify last line
        for i, t in enumerate(text_t):
            pl = maxwidth - pixlen(t)  # length of empty line part
            pnt = point + c_pnt * (i * lheight_factor)  # text start of line
            if align == 1:  # center: right shift by half width
                if rot in (0, 180):
                    pnt = pnt + Point(pl / 2, 0) * progr
                else:
                    pnt = pnt - Point(0, pl / 2) * progr
            elif align == 2:  # right: right shift by full width
                if rot in (0, 180):
                    pnt = pnt + Point(pl, 0) * progr
                else:
                    pnt = pnt - Point(0, pl) * progr
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

            nres += templ % (left, top, fname, fontsize)
            if render_mode > 0:
                nres += "%i Tr " % render_mode
            if align == 3:
                nres += "%g Tw " % spacing

            if color is not None:
                nres += color_str
            if fill is not None:
                nres += fill_str
            if border_width != 1:
                nres += "%g w " % border_width
            nres += "%sTJ\n" % getTJstr(t, tj_glyphs, simple, ordering)

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
        elif color == None:  # vice versa
            width = 0
        # if color == None and fill == None:
        #     raise ValueError("at least one of 'color' or 'fill' must be given")
        color_str = ColorCode(color, "c")  # ensure proper color string
        fill_str = ColorCode(fill, "f")  # ensure proper fill string

        optcont = self.page._get_optional_content(oc)
        if optcont is not None:
            self.draw_cont = "/OC /%s BDC\n" % optcont + self.draw_cont
            emc = "EMC\n"
        else:
            emc = ""

        alpha = self.page._set_opacity(CA=stroke_opacity, ca=fill_opacity)
        if alpha != None:
            self.draw_cont = "/%s gs\n" % alpha + self.draw_cont

        if width != 1 and width != 0:
            self.draw_cont += "%g w\n" % width

        if lineCap != 0:
            self.draw_cont = "%i J\n" % lineCap + self.draw_cont
        if lineJoin != 0:
            self.draw_cont = "%i j\n" % lineJoin + self.draw_cont

        if dashes not in (None, "", "[] 0"):
            self.draw_cont = "%s d\n" % dashes + self.draw_cont

        if closePath:
            self.draw_cont += "h\n"
            self.lastPoint = None

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
        if CheckMorph(morph):
            m1 = Matrix(
                1, 0, 0, 1, morph[0].x + self.x, self.height - morph[0].y - self.y
            )
            mat = ~m1 * morph[1] * m1
            self.draw_cont = "%g %g %g %g %g %g cm\n" % JM_TUPLE(mat) + self.draw_cont

        self.totalcont += "\nq\n" + self.draw_cont + "Q\n"
        self.draw_cont = ""
        self.lastPoint = None
        return

    def commit(self, overlay: bool = True) -> None:
        """Update the page's /Contents object with Shape data. The argument controls whether data appear in foreground (default) or background."""
        CheckParent(self.page)  # doc may have died meanwhile
        self.totalcont += self.text_cont

        self.totalcont = self.totalcont.encode()

        if self.totalcont != b"":
            # make /Contents object with dummy stream
            xref = TOOLS._insert_contents(self.page, b" ", overlay)
            # update it with potential compression
            self.doc.update_stream(xref, self.totalcont)

        self.lastPoint = None  # clean up ...
        self.rect = None  #
        self.draw_cont = ""  # for potential ...
        self.text_cont = ""  # ...
        self.totalcont = ""  # re-use
        return

    # define deprecated aliases ------------------------------------------
    drawBezier = draw_bezier
    drawCircle = draw_circle
    drawCurve = draw_curve
    drawLine = draw_line
    drawOval = draw_oval
    drawPolyline = draw_polyline
    drawQuad = draw_quad
    drawRect = draw_rect
    drawSector = draw_sector
    drawSquiggle = draw_squiggle
    drawZigzag = draw_zigzag
    insertText = insert_text
    insertTextbox = insert_textbox


def apply_redactions(page: Page, images: int = 2) -> bool:
    """Apply the redaction annotations of the page.

    Args:
        page: the PDF page.
        images: 0 - ignore images, 1 - remove complete overlapping image,
                2 - blank out overlapping image parts.
    """

    def center_rect(annot_rect, text, font, fsize):
        """Calculate minimal sub-rectangle for the overlay text.

        Notes:
            Because 'insert_textbox' supports no vertical text centering,
            we calculate an approximate number of lines here and return a
            sub-rect with smaller height, which should still be sufficient.
        Args:
            annot_rect: the annotation rectangle
            text: the text to insert.
            font: the fontname. Must be one of the CJK or Base-14 set, else
                the rectangle is returned unchanged.
            fsize: the fontsize
        Returns:
            A rectangle to use instead of the annot rectangle.
        """
        if not text:
            return annot_rect
        try:
            text_width = get_text_length(text, font, fsize)
        except ValueError:  # unsupported font
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

    CheckParent(page)
    doc = page.parent
    if doc.is_encrypted or doc.is_closed:
        raise ValueError("document closed or encrypted")
    if not doc.is_pdf:
        raise ValueError("is no PDF")

    redact_annots = []  # storage of annot values
    for annot in page.annots(types=(PDF_ANNOT_REDACT,)):  # loop redactions
        redact_annots.append(annot._get_redact_values())  # save annot values

    if redact_annots == []:  # any redactions on this page?
        return False  # no redactions

    rc = page._apply_redactions(images)  # call MuPDF redaction process step
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
            text = redact["text"]
            align = redact.get("align", 0)
            fname = redact["fontname"]
            fsize = redact["fontsize"]
            color = redact["text_color"]
            # try finding vertical centered sub-rect
            trect = center_rect(annot_rect, text, fname, fsize)

            rc = -1
            while rc < 0 and fsize >= 4:  # while not enough room
                # (re-) try insertion
                rc = shape.insert_textbox(
                    trect,
                    text,
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
    doc: Document,
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

    if clean_pages is False:
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
            if annot.type[0] == PDF_ANNOT_FILE_ATTACHMENT and attached_files:
                annot.fileUpd(buffer=b" ")  # set file content to empty
            if reset_responses:
                annot.delete_responses()
            if annot.type[0] == PDF_ANNOT_REDACT:
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


def fill_textbox(
    writer: TextWriter,
    rect: rect_like,
    text: typing.Union[str, list],
    pos: point_like = None,
    font: typing.Optional[Font] = None,
    fontsize: float = 11,
    lineheight: OptFloat = None,
    align: int = 0,
    warn: bool = None,
    right_to_left: bool = False,
    small_caps: bool = False,
) -> tuple:
    """Fill a rectangle with text.

    Args:
        writer: TextWriter object (= "self")
        rect: rect-like to receive the text.
        text: string or list/tuple of strings.
        pos: point-like start position of first word.
        font: Font object (default Font('helv')).
        fontsize: the fontsize.
        lineheight: overwrite the font property
        align: (int) 0 = left, 1 = center, 2 = right, 3 = justify
        warn: (bool) text overflow action: none, warn, or exception
        right_to_left: (bool) indicate right-to-left language.
    """
    rect = Rect(rect)
    if rect.is_empty:
        raise ValueError("fill rect must not empty.")
    if type(font) is not Font:
        font = Font("helv")

    def textlen(x):
        """Return length of a string."""
        return font.text_length(
            x, fontsize=fontsize, small_caps=small_caps
        )  # abbreviation

    def char_lengths(x):
        """Return list of single character lengths for a string."""
        return font.char_lengths(x, fontsize=fontsize, small_caps=small_caps)

    def append_this(pos, text):
        return writer.append(
            pos, text, font=font, fontsize=fontsize, small_caps=small_caps
        )

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
                    nwords.append(w[: n + 1])
                    word_lengths.append(wl)
                    w = w[n + 1 :]
                    wl_lst = wl_lst[n + 1 :]
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
        pos = Point(pos)
    else:  # default is just below rect top-left
        pos = rect.tl + (tolerance, fontsize * asc)
    if not pos in rect:
        raise ValueError("Text must start in rectangle.")

    # calculate displacement factor for alignment
    if align == TEXT_ALIGN_CENTER:
        factor = 0.5
    elif align == TEXT_ALIGN_RIGHT:
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
        words, word_lengths = norm_words(std_width, words)

        n = len(words)
        while True:
            line0 = " ".join(words[:n])
            wl = sum(word_lengths[:n]) + space_len * (len(word_lengths[:n]) - 1)
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

    # -------------------------------------------------------------------------
    # List of lines created. Each item is (text, tl), where 'tl' is the PDF
    # output length (float) and 'text' is the text. Except for justified text,
    # this is output-ready.
    # -------------------------------------------------------------------------
    nlines = len(new_lines)
    if nlines > max_lines:
        msg = "Only fitting %i of %i lines." % (max_lines, nlines)
        if warn == True:
            print("Warning: " + msg)
        elif warn == False:
            raise ValueError(msg)

    start = Point()
    no_justify += [len(new_lines) - 1]  # no justifying of last line
    for i in range(max_lines):
        try:
            line, tl = new_lines.pop(0)
        except IndexError:
            break

        if right_to_left:  # Arabic, Hebrew
            line = "".join(reversed(line))

        if i == 0:  # may have different start for first line
            start = pos

        if align == TEXT_ALIGN_JUSTIFY and i not in no_justify and tl < std_width:
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
def get_oc(doc: Document, xref: int) -> int:
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


def set_oc(doc: Document, xref: int, oc: int) -> None:
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
    doc: Document,
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


def get_ocmd(doc: Document, xref: int) -> dict:
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
        try:
            ve = json.loads(ve)
        except:
            print("bad /VE key: ", ve)
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
    for i, item in enumerate(rule):
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
    pagenumber = pgNo - rule["startpage"] + rule["firstpagenum"]
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
        """Convert Python label dict to correspnding PDF rule string.

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


def has_links(doc: Document) -> bool:
    """Check whether there are links on any page."""
    if doc.is_closed:
        raise ValueError("document closed")
    if not doc.is_pdf:
        raise ValueError("is no PDF")
    for i in range(doc.page_count):
        for item in doc.page_annot_xrefs(i):
            if item[1] == PDF_ANNOT_LINK:
                return True
    return False


def has_annots(doc: Document) -> bool:
    """Check whether there are annotations on any page."""
    if doc.is_closed:
        raise ValueError("document closed")
    if not doc.is_pdf:
        raise ValueError("is no PDF")
    for i in range(doc.page_count):
        for item in doc.page_annot_xrefs(i):
            if not (item[1] == PDF_ANNOT_LINK or item[1] == PDF_ANNOT_WIDGET):
                return True
    return False


# -------------------------------------------------------------------
# Functions to recover the quad contained in a text extraction bbox
# -------------------------------------------------------------------
def recover_bbox_quad(line_dir: tuple, span: dict, bbox: tuple) -> Quad:
    """Compute the quad located inside the bbox.

    The bbox may be any of the resp. tuples occurring inside the given span.

    Args:
        line_dir: (tuple) 'line["dir"]' of the owning line or None.
        span: (dict) the span. May be from get_texttrace() method.
        bbox: (tuple) the bbox of the span or any of its characters.
    Returns:
        The quad which is wrapped by the bbox.
    """
    if line_dir == None:
        line_dir = span["dir"]
    cos, sin = line_dir
    bbox = Rect(bbox)  # make it a rect
    if TOOLS.set_small_glyph_heights():  # ==> just fontsize as height
        d = 1
    else:
        d = span["ascender"] - span["descender"]

    height = d * span["size"]  # the quad's rectangle height
    # The following are distances from the bbox corners, at wich we find the
    # respective quad points. The computation depends on in which quadrant
    # the text writing angle is located.
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
    return Quad(ul, ur, ll, lr)


def recover_quad(line_dir: tuple, span: dict) -> Quad:
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


def recover_line_quad(line: dict, spans: list = None) -> Quad:
    """Calculate the line quad for 'dict' / 'rawdict' text extractions.

    The lower quad points are those of the first, resp. last span quad.
    The upper points are determined by the maximum span quad height.
    From this, compute a rect with bottom-left in (0, 0), convert this to a
    quad and rotate and shift back to cover the text of the spans.

    Args:
        spans: (list, optional) sub-list of spans to consider.
    Returns:
        Quad covering selected spans.
    """
    if spans == None:  # no sub-selection
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

    mat0 = planish_line(line_ll, line_lr)

    # map base line to x-axis such that line_ll goes to (0, 0)
    x_lr = line_lr * mat0

    small = TOOLS.set_small_glyph_heights()  # small glyph heights?

    h = max(
        [s["size"] * (1 if small else (s["ascender"] - s["descender"])) for s in spans]
    )

    line_rect = Rect(0, -h, x_lr.x, 0)  # line rectangle
    line_quad = line_rect.quad  # make it a quad and:
    line_quad *= ~mat0
    return line_quad


def recover_span_quad(line_dir: tuple, span: dict, chars: list = None) -> Quad:
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
        Quad covering selected characters.
    """
    if line_dir == None:  # must be a span from get_texttrace()
        line_dir = span["dir"]
    if chars == None:  # no sub-selection
        return recover_quad(line_dir, span)
    if not "chars" in span.keys():
        raise ValueError("need 'rawdict' option to sub-select chars")

    q0 = recover_char_quad(line_dir, span, chars[0])  # quad of first char
    if len(chars) > 1:  # get quad of last char
        q1 = recover_char_quad(line_dir, span, chars[-1])
    else:
        q1 = q0  # last = first

    span_ll = q0.ll  # lower-left of span quad
    span_lr = q1.lr  # lower-right of span quad
    mat0 = planish_line(span_ll, span_lr)
    # map base line to x-axis such that span_ll goes to (0, 0)
    x_lr = span_lr * mat0

    small = TOOLS.set_small_glyph_heights()  # small glyph heights?
    h = span["size"] * (1 if small else (span["ascender"] - span["descender"]))

    span_rect = Rect(0, -h, x_lr.x, 0)  # line rectangle
    span_quad = span_rect.quad  # make it a quad and:
    span_quad *= ~mat0  # rotate back and shift back
    return span_quad


def recover_char_quad(line_dir: tuple, span: dict, char: dict) -> Quad:
    """Recover the quadrilateral of a text character.

    This requires the "rawdict" option of text extraction.

    Args:
        line_dir: (tuple) 'line["dir"]' of the span's line.
        span: (dict) the span dict.
        char: (dict) the character dict.
    Returns:
        The quadrilateral enveloping the character.
    """
    if line_dir == None:
        line_dir = span["dir"]
    if type(line_dir) is not tuple or len(line_dir) != 2:
        raise ValueError("bad line dir argument")
    if type(span) is not dict:
        raise ValueError("bad span argument")
    if type(char) is dict:
        bbox = Rect(char["bbox"])
    elif type(char) is tuple:
        bbox = Rect(char[3])
    else:
        raise ValueError("bad span argument")

    return recover_bbox_quad(line_dir, span, bbox)


# -------------------------------------------------------------------
# Building font subsets using fontTools
# -------------------------------------------------------------------
def subset_fonts(doc: Document, verbose: bool = False) -> None:
    """Build font subsets of a PDF. Requires package 'fontTools'.

    Eligible fonts are potentially replaced by smaller versions. Page text is
    NOT rewritten and thus should retain properties like being hidden or
    controlled by optional content.
    """
    # Font binaries: -  "buffer" -> (names, xrefs, (unicodes, glyphs))
    # An embedded font is uniquely defined by its fontbuffer only. It may have
    # multiple names and xrefs.
    # Once the sets of used unicodes and glyphs are known, we compute a
    # smaller version of the buffer user package fontTools.
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
        return None

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
            print("This method requires fontTools to be installed.")
            raise
        tmp_dir = tempfile.gettempdir()
        oldfont_path = f"{tmp_dir}/oldfont.ttf"
        newfont_path = f"{tmp_dir}/newfont.ttf"
        uncfile_path = f"{tmp_dir}/uncfile.txt"
        args = [
            oldfont_path,
            "--retain-gids",
            f"--output-file={newfont_path}",
            "--layout-features='*'",
            "--passthrough-tables",
            "--ignore-missing-glyphs",
            "--ignore-missing-unicodes",
            "--symbol-cmap",
        ]

        unc_file = open(
            f"{tmp_dir}/uncfile.txt", "w"
        )  # store glyph ids or unicodes as file
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

        unc_file.close()
        fontfile = open(oldfont_path, "wb")  # store fontbuffer as a file
        fontfile.write(buffer)
        fontfile.close()
        try:
            os.remove(newfont_path)  # remove old file
        except:
            pass
        try:  # invoke fontTools subsetter
            fts.main(args)
            font = Font(fontfile=newfont_path)
            new_buffer = font.buffer
            if len(font.valid_codepoints()) == 0:
                new_buffer = None
        except:
            new_buffer = None
        try:
            os.remove(uncfile_path)
        except:
            pass
        try:
            os.remove(oldfont_path)
        except:
            pass
        try:
            os.remove(newfont_path)
        except:
            pass
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
                font = Font(fontbuffer=fontbuffer)
                name_set.add(font.name)
                del font
                font_buffers[fontbuffer] = (name_set, xref_set, subsets)
        return None

    def find_buffer_by_name(name):
        for buffer in font_buffers.keys():
            name_set, _, _ = font_buffers[buffer]
            if name in name_set:
                return buffer
        return None

    # -----------------
    # main function
    # -----------------
    repl_fontnames(doc)  # populate font information
    if not font_buffers:  # nothing found to do
        if verbose:
            print("No fonts to subset.")
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
    for old_buffer in font_buffers.keys():
        name_set, xref_set, subsets = font_buffers[old_buffer]
        new_buffer = build_subset(old_buffer, subsets[0], subsets[1])
        fontname = list(name_set)[0]
        if new_buffer == None or len(new_buffer) >= len(old_buffer):
            # subset was not created or did not get smaller
            if verbose:
                print(f"Cannot subset '{fontname}'.")
            continue
        if verbose:
            print(f"Built subset of font '{fontname}'.")
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
def xref_copy(doc: Document, source: int, target: int, *, keep: list = None) -> None:
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
    return None
