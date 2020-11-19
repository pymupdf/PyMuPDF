from __future__ import division

import io
import math
import os
import warnings
import json
from fitz import *


"""
This is a collection of functions to extend PyMupdf.
"""


def writeText(
    page,
    rect=None,
    writers=None,
    opacity=None,
    color=None,
    overlay=True,
    keep_proportion=True,
    rotate=0,
    oc=0,
):
    """Write the text of one or TextWriter objects.

    Args:
        rect: target rectangle. If None, the union of the text writers is used.
        writers: one or more TextWriter objects.
        overlay: put in foreground or background.
        keep_proportion: maintain aspect ratio of rectangle sides.
        rotate: arbitrary rotation angle.
        oc: the xref of an optional content object
    """
    if not writers:
        raise ValueError("need at least one TextWriter")
    if type(writers) is TextWriter:
        if rotate == 0 and rect is None:
            writers.writeText(page, opacity=opacity, color=color, overlay=overlay)
            return None
        else:
            writers = (writers,)
    clip = writers[0].textRect
    textdoc = Document()
    tpage = textdoc.newPage(width=page.rect.width, height=page.rect.height)
    for writer in writers:
        clip |= writer.textRect
        writer.writeText(tpage, opacity=opacity, color=color)
    if rect is None:
        rect = clip
    page.showPDFpage(
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


def showPDFpage(
    page,
    rect,
    src,
    pno=0,
    overlay=True,
    keep_proportion=True,
    rotate=0,
    oc=0,
    reuse_xref=0,
    clip=None,
):
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

    if not doc.isPDF or not src.isPDF:
        raise ValueError("not a PDF")

    rect = page.rect & rect  # intersect with page rectangle
    if rect.isEmpty or rect.isInfinite:
        raise ValueError("rect must be finite and not empty")

    if reuse_xref > 0:
        warnings.warn("ignoring 'reuse_xref'", DeprecationWarning)

    while pno < 0:  # support negative page numbers
        pno += len(src)
    src_page = src[pno]  # load ource page
    if len(src_page._getContents()) == 0:
        raise ValueError("nothing to show - source page empty")

    tar_rect = rect * ~page.transformationMatrix  # target rect in PDF coordinates

    src_rect = src_page.rect if not clip else src_page.rect & clip  # source rect
    if src_rect.isEmpty or src_rect.isInfinite:
        raise ValueError("clip must be finite and not empty")
    src_rect = src_rect * ~src_page.transformationMatrix  # ... in PDF coord

    matrix = calc_matrix(src_rect, tar_rect, keep=keep_proportion, rotate=rotate)

    # list of existing /Form /XObjects
    ilst = [i[1] for i in doc._getPageInfo(page.number, 3)]

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

    xref = page._showPDFpage(
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


def insertImage(
    page,
    rect,
    filename=None,
    pixmap=None,
    stream=None,
    mask=None,
    rotate=0,
    oc=0,
    keep_proportion=True,
    overlay=True,
):
    """Insert an image in a rectangle on the current page.

    Notes:
        Exactly one of filename, pixmap or stream must be provided.
    Args:
        rect: (rect-like) where to place the source image
        filename: (str) name of an image file
        pixmap: (obj) a Pixmap object
        stream: (bytes) an image in memory
        mask: (bytes) enforce this image mask
        rotate: (int) degrees (int multiple of 90)
        oc: (int) xref of an optional content object
        keep_proportion: (bool) whether to maintain aspect ratio
        overlay: (bool) put in foreground
    """

    def calc_hash(stream):
        m = hashlib.sha1()
        m.update(stream)
        return m.digest()

    def calc_matrix(fw, fh, tr, rotate=0):
        """Calculate transformation matrix for image insertion.

        Notes:
            The result is basically a multiplication of four matrices in this
            sequence: number one moves the image rectangle (always a unit rect!) to (0,0), number two rotates as desired, number three
            scales using the width-height-ratio, and number four moves to the
            target rect.
        Args:
            fw, fh: width / height ratio factors 0 < f <= 1.
                    The longer one must be 1.
            tr: target rect in PDF (!) coordinates
            rotate: (degrees) rotation angle.
        Returns:
            Transformation matrix.
        """
        # compute scale matrix parameters
        small = min(fw, fh)  # factor of the smaller side

        if rotate not in (0, 180):
            fw, fh = fh, fw  # width / height exchange their roles

        if fw < 1:  # portrait
            if tr.width / fw > tr.height / fh:
                w = tr.height * small
                h = tr.height
            else:
                w = tr.width
                h = tr.width / small

        elif fw != fh:  # landscape
            if tr.width / fw > tr.height / fh:
                w = tr.height / small
                h = tr.height
            else:
                w = tr.width
                h = tr.width * small

        else:
            w = tr.width
            h = tr.height

        # center point of target rectangle
        tmp = (tr.tl + tr.br) / 2.0

        # move image center to (0, 0), then rotate
        m = Matrix(1, 0, 0, 1, -0.5, -0.5) * Matrix(rotate)
        m *= Matrix(w, h)  # concat scale matrix
        m *= Matrix(1, 0, 0, 1, tmp.x, tmp.y)  # concat move to target center
        return m

    # ------------------------------------------------------------------------

    CheckParent(page)
    doc = page.parent
    if not doc.isPDF:
        raise ValueError("not a PDF")
    if bool(filename) + bool(stream) + bool(pixmap) != 1:
        raise ValueError("need exactly one of filename, pixmap, stream")

    if filename and not os.path.exists(filename):
        raise FileNotFoundError("No such file: '%s'" % filename)
    elif stream and type(stream) not in (bytes, bytearray, io.BytesIO):
        raise ValueError("stream must be bytes-like or BytesIO")
    elif pixmap and type(pixmap) is not Pixmap:
        raise ValueError("pixmap must be a Pixmap")
    if mask and not stream:
        raise ValueError("mask requires stream")
    if mask is not None and type(mask) not in (bytes, bytearray, io.BytesIO):
        raise ValueError("mask must be bytes-like or BytesIO")
    while rotate < 0:
        rotate += 360
    while rotate >= 360:
        rotate -= 360
    if rotate not in (0, 90, 180, 270):
        raise ValueError("bad rotate value")

    r = Rect(rect)
    if r.isEmpty or r.isInfinite:
        raise ValueError("rect must be finite and not empty")

    _imgpointer = None

    # -------------------------------------------------------------------------
    # Calculate the matrix for image insertion.
    # -------------------------------------------------------------------------
    # If aspect ratio must be kept, we need to know image width and height.
    # Easy for pixmaps. For file and stream cases, we make an fz_image and
    # take those values from it. In this case, we also hand the fz_image over
    # to the actual C-level function (_imgpointer), and set all other
    # parameters to None.
    # -------------------------------------------------------------------------
    if keep_proportion is True:  # for this we need the image dimension
        if pixmap:  # this is the easy case
            w = pixmap.width
            h = pixmap.height
            digest = calc_hash(pixmap.samples)

        elif stream:  # use tool to access the information
            # we also pass through the generated fz_image address
            if type(stream) is io.BytesIO:
                stream = stream.getvalue()
            img_prof = TOOLS.image_profile(stream, keep_image=True)
            w, h = img_prof["width"], img_prof["height"]
            digest = calc_hash(stream)
            stream = None  # make sure this arg is NOT used
            _imgpointer = img_prof["image"]  # pointer to fz_image

        else:  # worst case: must read the file
            stream = open(filename, "rb").read()
            digest = calc_hash(stream)
            img_prof = TOOLS.image_profile(stream, keep_image=True)
            w, h = img_prof["width"], img_prof["height"]
            stream = None  # make sure this arg is NOT used
            filename = None  # make sure this arg is NOT used
            _imgpointer = img_prof["image"]  # pointer to fz_image

        maxf = max(w, h)
        fw = w / maxf
        fh = h / maxf
    else:
        fw = fh = 1.0

    clip = r * ~page.transformationMatrix  # target rect in PDF coordinates

    matrix = calc_matrix(fw, fh, clip, rotate=rotate)  # calculate matrix

    # Create a unique image reference name.
    ilst = [i[7] for i in doc.getPageImageList(page.number)]
    n = "Im"  # 'fitz image'
    i = 0
    _imgname = n + "0"  # first name candidate
    while _imgname in ilst:
        i += 1
        _imgname = n + str(i)  # try new name

    xref = doc.InsertedImages.get(digest, 0)  # reuse any previously inserted image

    xref = page._insertImage(
        filename=filename,  # image in file
        pixmap=pixmap,  # image in pixmap
        stream=stream,  # image in memory
        imask=mask,
        matrix=matrix,  # generated matrix
        overlay=overlay,
        oc=oc,  # optional content object
        xref=xref,
        _imgname=_imgname,  # generated PDF resource name
        _imgpointer=_imgpointer,  # address of fz_image
    )
    if xref > 0:
        doc.InsertedImages[digest] = xref


def searchFor(page, text, hit_max=16, quads=False, clip=None, flags=None):
    """Search for a string on a page.

    Args:
        text: string to be searched for
        clip: restrict search to this rectangle
        quads: (bool) return quads instead of rectangles
        flags: bit switches, default: join hyphened words
    Returns:
        a list of rectangles or quads, each containing one occurrence.
    """
    CheckParent(page)
    if flags is None:
        flags = TEXT_DEHYPHENATE
    tp = page.getTextPage(clip=clip, flags=flags)  # create TextPage
    rlist = tp.search(text, quads=quads)
    tp = None
    return rlist


def searchPageFor(doc, pno, text, hit_max=16, quads=False, clip=None, flags=None):
    """Search for a string on a page.

    Args:
        pno: page number
        text: string to be searched for
        clip: restrict search to this rectangle
        quads: (bool) return quads instead of rectangles
        flags: bit switches, default: join hyphened words
    Returns:
        a list of rectangles or quads, each containing an occurrence.
    """

    return doc[pno].searchFor(text, quads=quads, clip=clip, flags=flags)


def getTextBlocks(page, clip=None, flags=None):
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
        flags = TEXT_PRESERVE_WHITESPACE + TEXT_PRESERVE_IMAGES
    tp = page.getTextPage(clip=clip, flags=flags)
    blocks = tp.extractBLOCKS()
    del tp
    return blocks


def getTextWords(page, clip=None, flags=None):
    """Return the text words as a list with the bbox for each word.

    Args:
        flags: (int) control the amount of data parsed into the textpage.
    """
    CheckParent(page)
    if flags is None:
        flags = TEXT_PRESERVE_WHITESPACE
    tp = page.getTextPage(clip=clip, flags=flags)
    words = tp.extractWORDS()
    del tp
    return words


def getTextbox(page, rect):
    rc = page.getText("text", clip=rect, flags=0)
    if rc.endswith("\n"):
        rc = rc[:-1]
    return rc


def getTextSelection(page, p1, p2, clip=None):
    CheckParent(page)
    flags = TEXT_PRESERVE_LIGATURES | TEXT_PRESERVE_WHITESPACE
    tp = page.getTextPage(clip=clip, flags=flags)
    rc = tp.extractSelection(p1, p2)
    del tp
    return rc


def getText(page, option="text", clip=None, flags=None):
    """Extract text from a page or an annotation.

    This is a unifying wrapper for various methods of the TextPage class.

    Args:
        option: (str) text, words, blocks, html, dict, json, rawdict, xhtml or xml.
        clip: (rect-like) restrict output to this area.
        flags: bitfield to e.g. exclude images.

    Returns:
        the output of methods getTextWords / getTextBlocks or TextPage
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
        flags = TEXT_PRESERVE_WHITESPACE
        if formats[option] == 1:
            flags += TEXT_PRESERVE_IMAGES

    if option == "words":
        return getTextWords(page, clip=clip, flags=flags)
    if option == "blocks":
        return getTextBlocks(page, clip=clip, flags=flags)
    CheckParent(page)

    tp = page.getTextPage(clip=clip, flags=flags)  # TextPage with or without images

    if option == "json":
        t = tp.extractJSON()
    elif option == "rawjson":
        t = tp.extractRAWJSON()
    elif option == "dict":
        t = tp.extractDICT()
    elif option == "rawdict":
        t = tp.extractRAWDICT()
    elif option == "html":
        t = tp.extractHTML()
    elif option == "xml":
        t = tp.extractXML()
    elif option == "xhtml":
        t = tp.extractXHTML()
    else:
        t = tp.extractText()

    del tp
    return t


def getPageText(doc, pno, option="text", clip=None, flags=None):
    """Extract a document page's text by page number.

    Notes:
        Convenience function calling page.getText().
    Args:
        pno: page number
        option: (str) text, words, blocks, html, dict, json, rawdict, xhtml or xml.
    Returns:
        output from page.TextPage().
    """
    return doc[pno].getText(option, clip=clip, flags=flags)


def getPixmap(page, matrix=None, colorspace=csRGB, clip=None, alpha=False, annots=True):
    """Create pixmap of page.

    Args:
        matrix: Matrix for transformation (default: Identity).
        colorspace: (str/Colorspace) cmyk, rgb, gray - case ignored, default csRGB.
        clip: (irect-like) restrict rendering to this area.
        alpha: (bool) whether to include alpha channel
        annots: (bool) whether to also render annotations
    """
    CheckParent(page)
    if type(colorspace) is str:
        if colorspace.upper() == "GRAY":
            colorspace = csGRAY
        elif colorspace.upper() == "CMYK":
            colorspace = csCMYK
        else:
            colorspace = csRGB
    if colorspace.n not in (1, 3, 4):
        raise ValueError("unsupported colorspace")

    dl = page.getDisplayList(annots=annots)
    pix = dl.getPixmap(matrix=matrix, colorspace=colorspace, alpha=alpha, clip=clip)
    dl = None
    return pix
    # doc = page.parent
    # return page._makePixmap(doc, matrix, colorspace, alpha, annots, clip)


def getPagePixmap(
    doc, pno, matrix=None, colorspace=csRGB, clip=None, alpha=False, annots=True
):
    """Create pixmap of document page by page number.

    Notes:
        Convenience function calling page.getPixmap.
    Args:
        pno: (int) page number
        matrix: Matrix for transformation (default: Identity).
        colorspace: (str,Colorspace) rgb, rgb, gray - case ignored, default csRGB.
        clip: (irect-like) restrict rendering to this area.
        alpha: (bool) include alpha channel
        annots: (bool) also render annotations
    """
    return doc[pno].getPixmap(
        matrix=matrix, colorspace=colorspace, clip=clip, alpha=alpha, annots=annots
    )


def getLinkDict(ln):
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


def getLinks(page):
    """Create a list of all links contained in a PDF page.

    Notes:
        see PyMuPDF ducmentation for details.
    """

    CheckParent(page)
    ln = page.firstLink
    links = []
    while ln:
        nl = getLinkDict(ln)
        # if nl["kind"] == LINK_GOTO:
        #    if type(nl["to"]) is Point and nl["page"] >= 0:
        #        doc = page.parent
        #        target_page = doc[nl["page"]]
        #        ctm = target_page.transformationMatrix
        #        point = nl["to"] * ctm
        #        nl["to"] = point
        links.append(nl)
        ln = ln.next
    if len(links) > 0:
        linkxrefs = page._getLinkXrefs()
        if len(linkxrefs) == len(links):
            for i in range(len(linkxrefs)):
                links[i]["xref"] = linkxrefs[i]
    return links


def getToC(doc, simple=True):
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

            if not olItem.isExternal:
                if olItem.uri:
                    if olItem.page == -1:
                        resolve = doc.resolveLink(olItem.uri)
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

    # check if document is open and not encrypted
    if doc.isClosed:
        raise ValueError("document closed")
    doc.initData()
    olItem = doc.outline

    if not olItem:
        return []
    lvl = 1
    liste = []
    return recurse(olItem, liste, lvl)


def delTOC_item(doc, idx):
    """Delete TOC / bookmark item by index."""
    toc = doc.getTOC()
    xref = doc.outlineXref(idx)
    if xref == 0:
        raise ValueError("bad TOC item number")
    doc._remove_toc_item(xref)


def setTOC_item(
    doc,
    idx,
    dest_dict=None,
    kind=None,
    pno=None,
    uri=None,
    title=None,
    to=None,
    filename=None,
    zoom=0,
):
    """Update TOC item by index.

    It allows changing the item's title and link destination.

    Args:
        idx: (int) desired index of the TOC list, as created by getTOC.
        dest_dict: (dict) destination dictionary as created by getTOC(False).
            Outrules all other parameters. If None, the remaining parameters
            are used to make a dest dictionary.
        kind: (int) kind of link (LINK_GOTO, etc.). If None, then only the
            title will be updated. If LINK_NONE, the TOC item will be deleted.
        pno: (int) page number (1-based like in getTOC). Required if LINK_GOTO.
        uri: (str) the URL, required if LINK_URI.
        title: (str) the new title. No change if None.
        to: (point-like) destination on the target page. If omitted, (72, 36)
            will be used as taget coordinates.
        filename: (str) destination filename, required for LINK_GOTOR and
            LINK_LAUNCH.
        name: (str) a destination name for LINK_NAMED.
        zoom: (float) a zoom factor for the target location (LINK_GOTO).
    """
    xref = doc.outlineXref(idx)
    if xref == 0:
        raise ValueError("bad TOC item number")
    page_xref = 0
    if type(dest_dict) is dict:
        if dest_dict["kind"] == LINK_GOTO:
            pno = dest_dict["page"]
            page_xref = doc.pageXref(pno)
            page_height = doc.pageCropBox(pno).height
            to = dest_dict.get(to, Point(72, 36))
            to.y = page_height - to.y
            dest_dict["to"] = to
        action = getDestStr(page_xref, dest_dict)
        if not action.startswith("/A"):
            raise ValueError("bad bookmark dest")
        return doc._update_toc_item(xref, action=action[2:], title=title)

    if kind == LINK_NONE:  # delete bookmark item
        return doc.delTOC_item(idx)
    if kind is None and title is None:  # treat as no-op
        return None
    if kind is None:  # only update title text
        return doc._update_toc_item(xref, action=None, title=title)

    if kind == LINK_GOTO:
        if pno is None or pno not in range(1, doc.pageCount + 1):
            raise ValueError("bad page number")
        page_xref = doc.pageXref(pno - 1)
        page_height = doc.pageCropBox(pno - 1).height
        if to is None:
            to = Point(72, page_height - 38)
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


def getRectArea(*args):
    """Calculate area of rectangle.\nparameter is one of 'px' (default), 'in', 'cm', or 'mm'."""
    rect = args[0]
    if len(args) > 1:
        unit = args[1]
    else:
        unit = "px"
    u = {"px": (1, 1), "in": (1.0, 72.0), "cm": (2.54, 72.0), "mm": (25.4, 72.0)}
    f = (u[unit][0] / u[unit][1]) ** 2
    return f * rect.width * rect.height


def setMetadata(doc, m):
    """Set PDF /Info object.

    Args:
        m: a dictionary like doc.metadata.
    """
    if doc.isClosed or doc.isEncrypted:
        raise ValueError("document closed or encrypted")
    if type(m) is not dict:
        raise ValueError("bad metadata argument")
    keymap = {
        "author": "/Author",
        "producer": "/Producer",
        "creator": "/Creator",
        "title": "/Title",
        "format": None,
        "encryption": None,
        "creationDate": "/CreationDate",
        "modDate": "/ModDate",
        "subject": "/Subject",
        "keywords": "/Keywords",
        "trapped": "/Trapped",
    }
    valid_keys = set(keymap.keys())
    diff_set = set(m.keys()).difference(valid_keys)
    if diff_set != set():
        msg = "bad dict key(s): %s" % diff_set
        raise ValueError(msg)

    d = "<<"
    for k in m.keys():
        if m[k] and keymap[k] and m[k] != "none":
            x = m[k] if m[k].startswith("/") else getPDFstr(m[k])
            d += keymap[k] + x
    d += ">>"
    doc._setMetadata(d)
    doc.initData()
    return


def getDestStr(xref, ddict):
    """Calculate the PDF action string.

    Notes:
        Supports Link annotations and outline items (bookmarks).
    """
    if not ddict:
        return ""
    str_goto = "/A<</S/GoTo/D[%i 0 R/XYZ %g %g %i]>>"
    str_gotor1 = "/A<</S/GoToR/D[%s /XYZ %s %s %s]/F<</F%s/UF%s/Type/Filespec>>>>"
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
        dest = str_uri % (getPDFstr(ddict["uri"]),)
        return dest

    if ddict["kind"] == LINK_LAUNCH:
        fspec = getPDFstr(ddict["file"])
        dest = str_launch % (fspec, fspec)
        return dest

    if ddict["kind"] == LINK_GOTOR and ddict["page"] < 0:
        fspec = getPDFstr(ddict["file"])
        dest = str_gotor2 % (getPDFstr(ddict["to"]), fspec, fspec)
        return dest

    if ddict["kind"] == LINK_GOTOR and ddict["page"] >= 0:
        fspec = getPDFstr(ddict["file"])
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


def setToC(doc, toc, collapse=1):
    """Create new outline tree (table of contents, TOC).

    Args:
        toc: (list, tuple) each entry must contain level, title, page and
            optionally top margin on the page. None or '()' remove the TOC.
        collapse: (int) collapses entries beyond this level. Zero or None
            shows all entries unfolded.
    Returns:
        the number of inserted items, or the number of removed items respectively.
    """
    if doc.isClosed or doc.isEncrypted:
        raise ValueError("document closed or encrypted")
    if not doc.isPDF:
        raise ValueError("not a PDF")
    if not toc:  # remove all entries
        return len(doc._delToC())

    # validity checks --------------------------------------------------------
    if type(toc) not in (list, tuple):
        raise ValueError("'toc' must be list or tuple")
    toclen = len(toc)
    pageCount = doc.pageCount
    t0 = toc[0]
    if type(t0) not in (list, tuple):
        raise ValueError("items must be sequences of 3 or 4 items")
    if t0[0] != 1:
        raise ValueError("hierarchy level of item 0 must be 1")
    for i in list(range(toclen - 1)):
        t1 = toc[i]
        t2 = toc[i + 1]
        if not -1 <= t1[2] <= pageCount:
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
    old_xrefs = []  # TODO do not reuse them currently
    # prepare table of xrefs for new bookmarks
    xref = [0] + old_xrefs
    xref[0] = doc._getOLRootNumber()  # entry zero is outline root xref#
    if toclen > len(old_xrefs):  # too few old xrefs?
        for i in range((toclen - len(old_xrefs))):
            xref.append(doc._getNewXref())  # acquire new ones

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
        title = getPDFstr(o[1])  # title
        pno = min(doc.pageCount - 1, max(0, o[2] - 1))  # page number
        page_xref = doc.pageXref(pno)
        page_height = doc.pageCropBox(pno).height
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
        lvltab[lvl] = i + 1
        parent = olitems[lvltab[lvl - 1]]  # the parent entry

        if collapse and lvl > collapse:  # suppress expansion
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
        if i == 0:  # special: this is the outline root
            txt += "/Type/Outlines"  # so add the /Type entry
        txt += ">>"
        doc._updateObject(xref[i], txt)  # insert the PDF object

    doc.initData()
    return toclen


def do_links(doc1, doc2, from_page=-1, to_page=-1, start_at=-1):
    """Insert links contained in copied page range into destination PDF.

    Parameter values **must** equal those of method insertPDF(), which must
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
            annot = txt % (xref_dst[idx], p.x, p.y, rect)

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
                    lnk["file"],
                    lnk["file"],
                    rect,
                )
            else:
                txt = annot_skel["gotor2"]  # annot_gotor_n
                to = getPDFstr(lnk["to"])
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
    elif from_page >= doc2.pageCount:
        fp = doc2.pageCount - 1
    else:
        fp = from_page

    if to_page < 0 or to_page >= doc2.pageCount:
        tp = doc2.pageCount - 1
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
        old_xref = doc2.pageXref(p_src)
        new_xref = doc1.pageXref(p_dst)
        xref_src.append(old_xref)
        xref_dst.append(new_xref)

    # create the links for each copied page in destination PDF
    for i in range(len(xref_src)):
        page_src = doc2[pno_src[i]]  # load source page
        links = page_src.getLinks()  # get all its links
        if len(links) == 0:  # no links there
            page_src = None
            continue
        ctm = ~page_src.transformationMatrix  # calc page transformation matrix
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
            page_dst._addAnnot_FromString(link_tab)
        page_dst = None
        page_src = None
    return


def getLinkText(page, lnk):
    # --------------------------------------------------------------------------
    # define skeletons for /Annots object texts
    # --------------------------------------------------------------------------
    ctm = page.transformationMatrix
    ictm = ~ctm
    r = lnk["from"]
    height = page.rect.height
    rect = "%g %g %g %g" % tuple(r * ictm)

    annot = ""
    if lnk["kind"] == LINK_GOTO:
        if lnk["page"] >= 0:
            txt = annot_skel["goto1"]  # annot_goto
            pno = lnk["page"]
            xref = page.parent._getPageXref(pno)[0]
            pnt = lnk.get("to", Point(0, 0))  # destination point
            ipnt = pnt * ictm
            annot = txt % (xref, ipnt.x, ipnt.y, rect)
        else:
            txt = annot_skel["goto2"]  # annot_goto_n
            annot = txt % (getPDFstr(lnk["to"]), rect)

    elif lnk["kind"] == LINK_GOTOR:
        if lnk["page"] >= 0:
            txt = annot_skel["gotor1"]  # annot_gotor
            pnt = lnk.get("to", Point(0, 0))  # destination point
            if type(pnt) is not Point:
                pnt = Point(0, 0)
            annot = txt % (lnk["page"], pnt.x, pnt.y, lnk["file"], lnk["file"], rect)
        else:
            txt = annot_skel["gotor2"]  # annot_gotor_n
            annot = txt % (getPDFstr(lnk["to"]), lnk["file"], rect)

    elif lnk["kind"] == LINK_LAUNCH:
        txt = annot_skel["launch"]  # annot_launch
        annot = txt % (lnk["file"], lnk["file"], rect)

    elif lnk["kind"] == LINK_URI:
        txt = annot_skel["uri"]  # txt = annot_uri
        annot = txt % (lnk["uri"], rect)

    elif lnk["kind"] == LINK_NAMED:
        txt = annot_skel["named"]  # annot_named
        annot = txt % (lnk["name"], rect)

    return annot


def deleteWidget(page, widget):
    """Delete widget from page and return the next one."""
    CheckParent(page)
    annot = getattr(widget, "_annot", None)
    if annot is None:
        raise ValueError("bad type: widget")
    nextwidget = widget.next
    page.deleteAnnot(annot)
    widget._annot.__del__()
    widget._annot.parent = None
    keylist = list(widget.__dict__.keys())
    for key in keylist:
        del widget.__dict__[key]
    return nextwidget


def updateLink(page, lnk):
    """ Update a link on the current page. """
    CheckParent(page)
    annot = getLinkText(page, lnk)
    if annot == "":
        raise ValueError("link kind not supported")

    page.parent._updateObject(lnk["xref"], annot, page=page)
    return


def insertLink(page, lnk, mark=True):
    """ Insert a new link for the current page. """
    CheckParent(page)
    annot = getLinkText(page, lnk)
    if annot == "":
        raise ValueError("link kind not supported")

    page._addAnnot_FromString([annot])
    return


def insertTextbox(
    page,
    rect,
    buffer,
    fontname="helv",
    fontfile=None,
    set_simple=0,
    encoding=0,
    fontsize=11,
    color=None,
    fill=None,
    expandtabs=1,
    align=0,
    rotate=0,
    render_mode=0,
    border_width=1,
    morph=None,
    overlay=True,
    stroke_opacity=1,
    fill_opacity=1,
    oc=0,
):
    """Insert text into a given rectangle.

    Notes:
        Creates a Shape object, uses its same-named method and commits it.
    Parameters:
        rect: (rect-like) area to use for text.
        buffer: text to be inserted
        fontname: a Base-14 font, font name or '/name'
        fontfile: name of a font file
        fontsize: font size
        color: RGB color triple
        expandtabs: handles tabulators with string function
        align: left, center, right, justified
        rotate: 0, 90, 180, or 270 degrees
        morph: morph box with a matrix and a fixpoint
        overlay: put text in foreground or background
    Returns:
        unused or deficit rectangle area (float)
    """
    img = page.newShape()
    rc = img.insertTextbox(
        rect,
        buffer,
        fontsize=fontsize,
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


def insertText(
    page,
    point,
    text,
    fontsize=11,
    fontname="helv",
    fontfile=None,
    set_simple=0,
    encoding=0,
    color=None,
    fill=None,
    border_width=1,
    render_mode=0,
    rotate=0,
    morph=None,
    overlay=True,
    stroke_opacity=1,
    fill_opacity=1,
    oc=0,
):

    img = page.newShape()
    rc = img.insertText(
        point,
        text,
        fontsize=fontsize,
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


def newPage(doc, pno=-1, width=595, height=842):
    """Create and return a new page object."""
    doc._newPage(pno, width=width, height=height)
    return doc[pno]


def insertPage(
    doc,
    pno,
    text=None,
    fontsize=11,
    width=595,
    height=842,
    fontname="helv",
    fontfile=None,
    color=None,
):
    """Create a new PDF page and insert some text.

    Notes:
        Function combining Document.newPage() and Page.insertText().
        For parameter details see these methods.
    """
    page = doc.newPage(pno=pno, width=width, height=height)
    if not bool(text):
        return 0
    rc = page.insertText(
        (50, 72),
        text,
        fontsize=fontsize,
        fontname=fontname,
        fontfile=fontfile,
        color=color,
    )
    return rc


def drawLine(
    page,
    p1,
    p2,
    color=None,
    dashes=None,
    width=1,
    lineCap=0,
    lineJoin=0,
    overlay=True,
    morph=None,
    stroke_opacity=1,
    fill_opacity=1,
    oc=0,
):
    """Draw a line from point p1 to point p2."""
    img = page.newShape()
    p = img.drawLine(Point(p1), Point(p2))
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


def drawSquiggle(
    page,
    p1,
    p2,
    breadth=2,
    color=None,
    dashes=None,
    width=1,
    lineCap=0,
    lineJoin=0,
    overlay=True,
    morph=None,
    stroke_opacity=1,
    fill_opacity=1,
    oc=0,
):
    """Draw a squiggly line from point p1 to point p2."""
    img = page.newShape()
    p = img.drawSquiggle(Point(p1), Point(p2), breadth=breadth)
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


def drawZigzag(
    page,
    p1,
    p2,
    breadth=2,
    color=None,
    dashes=None,
    width=1,
    lineCap=0,
    lineJoin=0,
    overlay=True,
    morph=None,
    stroke_opacity=1,
    fill_opacity=1,
    oc=0,
):
    """Draw a zigzag line from point p1 to point p2."""
    img = page.newShape()
    p = img.drawZigzag(Point(p1), Point(p2), breadth=breadth)
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


def drawRect(
    page,
    rect,
    color=None,
    fill=None,
    dashes=None,
    width=1,
    lineCap=0,
    lineJoin=0,
    morph=None,
    overlay=True,
    stroke_opacity=1,
    fill_opacity=1,
    oc=0,
):
    """Draw a rectangle."""
    img = page.newShape()
    Q = img.drawRect(Rect(rect))
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


def drawQuad(
    page,
    quad,
    color=None,
    fill=None,
    dashes=None,
    width=1,
    lineCap=0,
    lineJoin=0,
    morph=None,
    overlay=True,
    stroke_opacity=1,
    fill_opacity=1,
    oc=0,
):
    """Draw a quadrilateral."""
    img = page.newShape()
    Q = img.drawQuad(Quad(quad))
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


def drawPolyline(
    page,
    points,
    color=None,
    fill=None,
    dashes=None,
    width=1,
    morph=None,
    lineCap=0,
    lineJoin=0,
    overlay=True,
    closePath=False,
    stroke_opacity=1,
    fill_opacity=1,
    oc=0,
):
    """Draw multiple connected line segments."""
    img = page.newShape()
    Q = img.drawPolyline(points)
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


def drawCircle(
    page,
    center,
    radius,
    color=None,
    fill=None,
    morph=None,
    dashes=None,
    width=1,
    lineCap=0,
    lineJoin=0,
    overlay=True,
    stroke_opacity=1,
    fill_opacity=1,
    oc=0,
):
    """Draw a circle given its center and radius."""
    img = page.newShape()
    Q = img.drawCircle(Point(center), radius)
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


def drawOval(
    page,
    rect,
    color=None,
    fill=None,
    dashes=None,
    morph=None,
    width=1,
    lineCap=0,
    lineJoin=0,
    overlay=True,
    stroke_opacity=1,
    fill_opacity=1,
    oc=0,
):
    """Draw an oval given its containing rectangle or quad."""
    img = page.newShape()
    Q = img.drawOval(rect)
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


def drawCurve(
    page,
    p1,
    p2,
    p3,
    color=None,
    fill=None,
    dashes=None,
    width=1,
    morph=None,
    closePath=False,
    lineCap=0,
    lineJoin=0,
    overlay=True,
    stroke_opacity=1,
    fill_opacity=1,
    oc=0,
):
    """Draw a special Bezier curve from p1 to p3, generating control points on lines p1 to p2 and p2 to p3."""
    img = page.newShape()
    Q = img.drawCurve(Point(p1), Point(p2), Point(p3))
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


def drawBezier(
    page,
    p1,
    p2,
    p3,
    p4,
    color=None,
    fill=None,
    dashes=None,
    width=1,
    morph=None,
    closePath=False,
    lineCap=0,
    lineJoin=0,
    overlay=True,
    stroke_opacity=1,
    fill_opacity=1,
    oc=0,
):
    """Draw a general cubic Bezier curve from p1 to p4 using control points p2 and p3."""
    img = page.newShape()
    Q = img.drawBezier(Point(p1), Point(p2), Point(p3), Point(p4))
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


def drawSector(
    page,
    center,
    point,
    beta,
    color=None,
    fill=None,
    dashes=None,
    fullSector=True,
    morph=None,
    width=1,
    closePath=False,
    lineCap=0,
    lineJoin=0,
    overlay=True,
    stroke_opacity=1,
    fill_opacity=1,
    oc=0,
):
    """Draw a circle sector given circle center, one arc end point and the angle of the arc.

    Parameters:
        center -- center of circle
        point -- arc end point
        beta -- angle of arc (degrees)
        fullSector -- connect arc ends with center
    """
    img = page.newShape()
    Q = img.drawSector(Point(center), Point(point), beta, fullSector=fullSector)
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


def getColorList():
    """
    Returns a list of just the colour names used by this module.
    :rtype: list of strings
    """

    return [x[0] for x in getColorInfoList()]


def getColorInfoList():
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


def getColorInfoDict():
    d = {}
    for item in getColorInfoList():
        d[item[0].lower()] = item[1:]
    return d


def getColor(name):
    """Retrieve RGB color in PDF format by name.

    Returns:
        a triple of floats in range 0 to 1. In case of name-not-found, "white" is returned.
    """
    try:
        c = getColorInfoList()[getColorList().index(name.upper())]
        return (c[1] / 255.0, c[2] / 255.0, c[3] / 255.0)
    except:
        return (1, 1, 1)


def getColorHSV(name):
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


def getCharWidths(doc, xref, limit=256, idx=0):
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
        name, ext, stype, _ = doc.extractFont(xref, info_only=True)
        fontdict = {"name": name, "type": stype, "ext": ext}

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
        glyphs = doc._getCharWidths(
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

    def __init__(self, page):
        CheckParent(page)
        self.page = page
        self.doc = page.parent
        if not self.doc.isPDF:
            raise ValueError("not a PDF")
        self.height = page.MediaBoxSize.y
        self.width = page.MediaBoxSize.x
        self.x = page.CropBoxPosition.x
        self.y = page.CropBoxPosition.y

        self.pctm = page.transformationMatrix  # page transf. matrix
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

    def drawLine(self, p1, p2):
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

    def drawPolyline(self, points):
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

    def drawBezier(self, p1, p2, p3, p4):
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

    def drawOval(self, tetra):
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
        self.drawCurve(ml, q.ll, mb)
        self.drawCurve(mb, q.lr, mr)
        self.drawCurve(mr, q.ur, mt)
        self.drawCurve(mt, q.ul, ml)
        self.updateRect(q.rect)
        self.lastPoint = ml
        return self.lastPoint

    def drawCircle(self, center, radius):
        """Draw a circle given its center and radius."""
        if not radius > EPSILON:
            raise ValueError("radius must be postive")
        center = Point(center)
        p1 = center - (radius, 0)
        return self.drawSector(center, p1, 360, fullSector=False)

    def drawCurve(self, p1, p2, p3):
        """Draw a curve between points using one control point."""
        kappa = 0.55228474983
        p1 = Point(p1)
        p2 = Point(p2)
        p3 = Point(p3)
        k1 = p1 + (p2 - p1) * kappa
        k2 = p3 + (p2 - p3) * kappa
        return self.drawBezier(p1, k1, k2, p3)

    def drawSector(self, center, point, beta, fullSector=True):
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

    def drawRect(self, rect):
        """Draw a rectangle."""
        r = Rect(rect)
        self.draw_cont += "%g %g %g %g re\n" % JM_TUPLE(
            list(r.bl * self.ipctm) + [r.width, r.height]
        )
        self.updateRect(r)
        self.lastPoint = r.tl
        return self.lastPoint

    def drawQuad(self, quad):
        """Draw a Quad."""
        q = Quad(quad)
        return self.drawPolyline([q.ul, q.ll, q.lr, q.ur, q.ul])

    def drawZigzag(self, p1, p2, breadth=2):
        """Draw a zig-zagged line from p1 to p2."""
        p1 = Point(p1)
        p2 = Point(p2)
        S = p2 - p1  # vector start - end
        rad = abs(S)  # distance of points
        cnt = 4 * int(round(rad / (4 * breadth), 0))  # always take full phases
        if cnt < 4:
            raise ValueError("points too close")
        mb = rad / cnt  # revised breadth
        matrix = TOOLS._hor_matrix(p1, p2)  # normalize line to x-axis
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
        self.drawPolyline([p1] + points + [p2])  # add start and end points
        return p2

    def drawSquiggle(self, p1, p2, breadth=2):
        """Draw a squiggly line from p1 to p2."""
        p1 = Point(p1)
        p2 = Point(p2)
        S = p2 - p1  # vector start - end
        rad = abs(S)  # distance of points
        cnt = 4 * int(round(rad / (4 * breadth), 0))  # always take full phases
        if cnt < 4:
            raise ValueError("points too close")
        mb = rad / cnt  # revised breadth
        matrix = Matrix(TOOLS._hor_matrix(p1, p2))  # normalize line to x-axis
        i_mat = ~matrix  # get original position
        k = 2.4142135623765633  # y of drawCurve helper point

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
            self.drawCurve(points[i], points[i + 1], points[i + 2])
            i += 2
        return p2

    # ==============================================================================
    # Shape.insertText
    # ==============================================================================
    def insertText(
        self,
        point,
        buffer,
        fontsize=11,
        fontname="helv",
        fontfile=None,
        set_simple=0,
        encoding=0,
        color=None,
        fill=None,
        render_mode=0,
        border_width=1,
        rotate=0,
        morph=None,
        stroke_opacity=1,
        fill_opacity=1,
        oc=0,
    ):

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

        xref = self.page.insertFont(
            fontname=fname, fontfile=fontfile, encoding=encoding, set_simple=set_simple
        )
        fontinfo = CheckFontInfo(self.doc, xref)

        fontdict = fontinfo[1]
        ordering = fontdict["ordering"]
        simple = fontdict["simple"]
        bfname = fontdict["name"]
        if maxcode > 255:
            glyphs = self.doc.getCharWidths(xref, maxcode + 1)
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
            raise ValueError("rotate not multiple of 90")

        while rot < 0:
            rot += 360
        rot = rot % 360  # text rotate = 0, 90, 270, 180

        templ1 = "\nq\n%s%sBT\n%s1 0 0 1 %g %g Tm /%s %g Tf "
        templ2 = "TJ\n0 -%g TD\n"
        cmp90 = "0 1 -1 0 0 0 cm\n"  # rotates 90 deg counter-clockwise
        cmm90 = "0 -1 1 0 0 0 cm\n"  # rotates 90 deg clockwise
        cm180 = "-1 0 0 -1 0 0 cm\n"  # rotates by 180 deg.
        height = self.height
        width = self.width
        lheight = fontsize * 1.2  # line height
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
        nres += templ2 % lheight  # line 1
        for i in range(1, len(text)):
            if space < lheight:
                break  # no space left on page
            if i > 1:
                nres += "\nT* "
            nres += text[i] + templ2[:2]
            space -= lheight
            nlines += 1

        nres += " ET\n%sQ\n" % emc

        # =========================================================================
        #   end of text insertion
        # =========================================================================
        # update the /Contents object
        self.text_cont += nres
        return nlines

    # ==============================================================================
    # Shape.insertTextbox
    # ==============================================================================
    def insertTextbox(
        self,
        rect,
        buffer,
        fontname="helv",
        fontfile=None,
        fontsize=11,
        set_simple=0,
        encoding=0,
        color=None,
        fill=None,
        expandtabs=1,
        border_width=1,
        align=0,
        render_mode=0,
        rotate=0,
        morph=None,
        stroke_opacity=1,
        fill_opacity=1,
        oc=0,
    ):
        """Insert text into a given rectangle.

        Args:
            rect -- the textbox to fill
            buffer -- text to be inserted
            fontname -- a Base-14 font, font name or '/name'
            fontfile -- name of a font file
            fontsize -- font size
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
        if rect.isEmpty or rect.isInfinite:
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

        xref = self.page.insertFont(
            fontname=fname, fontfile=fontfile, encoding=encoding, set_simple=set_simple
        )
        fontinfo = CheckFontInfo(self.doc, xref)

        fontdict = fontinfo[1]
        ordering = fontdict["ordering"]
        simple = fontdict["simple"]
        glyphs = fontdict["glyphs"]
        bfname = fontdict["name"]

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

        glyphs = self.doc.getCharWidths(xref, maxcode + 1)
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
        lheight = fontsize * 1.2  # line height
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
        c_pnt = Point(0, fontsize)  # used for line progress
        if rot == 0:  # normal orientation
            point = rect.tl + c_pnt  # line 1 is 'lheight' below top
            pos = point.y + self.y  # y of first line
            maxwidth = rect.width  # pixels available in one line
            maxpos = rect.y1 + self.y  # lines must not be below this

        elif rot == 90:  # rotate counter clockwise
            c_pnt = Point(fontsize, 0)  # progress in x-direction
            point = rect.bl + c_pnt  # line 1 'lheight' away from left
            pos = point.x + self.x  # position of first line
            maxwidth = rect.height  # pixels available in one line
            maxpos = rect.x1 + self.x  # lines must not be right of this
            cm += cmp90

        elif rot == 180:  # text upside down
            c_pnt = -Point(0, fontsize)  # progress upwards in y direction
            point = rect.br + c_pnt  # line 1 'lheight' above bottom
            pos = point.y + self.y  # position of first line
            maxwidth = rect.width  # pixels available in one line
            progr = -1  # subtract lheight for next line
            maxpos = rect.y0 + self.y  # lines must not be above this
            cm += cm180

        else:  # rotate clockwise (270 or -90)
            c_pnt = -Point(fontsize, 0)  # progress from right to left
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
        spacing = 0
        text_t = text.splitlines()  # split text in lines again
        for i, t in enumerate(text_t):
            pl = maxwidth - pixlen(t)  # length of empty line part
            pnt = point + c_pnt * (i * 1.2)  # text start of line
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
            if spacing != 0:
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
        width=1,
        color=None,
        fill=None,
        lineCap=0,
        lineJoin=0,
        dashes=None,
        even_odd=False,
        morph=None,
        closePath=True,
        fill_opacity=1,
        stroke_opacity=1,
        oc=0,
    ):
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

        if width != 1:
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

    def commit(self, overlay=True):
        """Update the page's /Contents object with Shape data. The argument controls whether data appear in foreground (default) or background."""
        CheckParent(self.page)  # doc may have died meanwhile
        self.totalcont += self.text_cont

        if not fitz_py2:  # need bytes if Python > 2
            self.totalcont = bytes(self.totalcont, "utf-8")

        if self.totalcont != b"":
            # make /Contents object with dummy stream
            xref = TOOLS._insert_contents(self.page, b" ", overlay)
            # update it with potential compression
            self.doc.updateStream(xref, self.totalcont)

        self.lastPoint = None  # clean up ...
        self.rect = None  #
        self.draw_cont = ""  # for possible ...
        self.text_cont = ""  # ...
        self.totalcont = ""  # re-use
        return


def apply_redactions(page, images=2):
    """Apply the redaction annotations of the page."""

    def center_rect(annot_rect, text, font, fsize):
        """Calculate minimal sub-rectangle for the overlay text.

        Notes:
            Because 'insertTextbox' supports no vertical text centering,
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
            text_width = getTextlength(text, font, fsize)
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
    if doc.isEncrypted or doc.isClosed:
        raise ValueError("document closed or encrypted")
    if not doc.isPDF:
        raise ValueError("not a PDF")

    redact_annots = []  # storage of annot values
    for annot in page.annots(types=(PDF_ANNOT_REDACT,)):  # loop redactions
        redact_annots.append(annot._get_redact_values())  # save annot values

    if redact_annots == []:  # any redactions on this page?
        return False  # no redactions

    rc = page._apply_redactions(images)  # call MuPDF redaction process step
    if not rc:  # should not happen really
        raise ValueError("Error applying redactions.")

    # now write replacement text in old redact rectangles
    shape = page.newShape()
    for redact in redact_annots:
        annot_rect = redact["rect"]
        fill = redact["fill"]
        if fill:
            shape.drawRect(annot_rect)  # colorize the rect background
            shape.finish(fill=fill, color=fill)
        if "text" in redact.keys():  # if we also have text
            trect = center_rect(  # try finding vertical centered sub-rect
                annot_rect, redact["text"], redact["fontname"], redact["fontsize"]
            )
            fsize = redact["fontsize"]  # start with stored fontsize
            rc = -1
            while rc < 0 and fsize >= 4:  # while not enough room
                rc = shape.insertTextbox(  # (re-) try insertion
                    trect,
                    redact["text"],
                    fontname=redact["fontname"],
                    fontsize=fsize,
                    color=redact["text_color"],
                    align=redact["align"],
                )
                fsize -= 0.5  # reduce font if unsuccessful
    shape.commit()  # append new contents object
    return True


# ------------------------------------------------------------------------------
# Remove potentially sensitive data from a PDF. Corresponds to the Adobe
# Acrobat 'sanitize' function
# ------------------------------------------------------------------------------
def scrub(
    doc,
    attached_files=True,
    clean_pages=True,
    embedded_files=True,
    hidden_text=True,
    javascript=True,
    metadata=True,
    redactions=True,
    redact_images=0,
    remove_links=True,
    reset_fields=True,
    reset_responses=True,
    xml_metadata=True,
):
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

    if not doc.isPDF:  # only works for PDF
        raise ValueError("not a PDF")
    if doc.isEncrypted or doc.isClosed:
        raise ValueError("closed or encrypted doc")

    if clean_pages is False:
        hidden_text = False
        redactions = False

    if metadata:
        doc.setMetadata({})  # remove standard metadata

    if not (xml_metadata or javascript):
        xref_limit = 0
    else:
        xref_limit = doc.xrefLength()
    for xref in range(1, xref_limit):
        obj = doc.xrefObject(xref)  # get object definition source
        # note: this string is formatted in a fixed, standard way by MuPDF.

        if javascript and "/S /JavaScript" in obj:  # a /JavaScript action object?
            obj = "<</S/JavaScript/JS()>>"  # replace with a null JavaScript
            doc.updateObject(xref, obj)  # update this object
            continue  # no further handling

        if not xml_metadata or "/Metadata" not in obj:
            continue

        if "/Type /Metadata" in obj:  # delete any metadata object directly
            doc._deleteObject(xref)
            continue

        obj_lines = obj.splitlines()
        new_lines = []  # will receive remaining obj definition lines
        found = False  # assume /Metadata  not found
        for line in obj_lines:
            line = line.strip()
            if not line.startswith("/Metadata "):
                new_lines.append(line)  # keep this line
            else:  # drop this line
                found = True
        if found:  # if removed /Metadata key, update object definition
            doc.updateObject(xref, "\n".join(new_lines))

    # remove embedded files
    if embedded_files:
        for name in doc.embeddedFileNames():
            doc.embeddedFileDel(name)

    for page in doc:
        if reset_fields:
            # reset form fields (widgets)
            for widget in page.widgets():
                widget.reset()
                widget.update()

        if remove_links:
            links = page.getLinks()  # list of all links on page
            for link in links:  # remove all links
                page.deleteLink(link)

        found_redacts = False
        for annot in page.annots():
            if annot.type[0] == PDF_ANNOT_FILE_ATTACHMENT and attached_files:
                annot.fileUpd(buffer=b"")  # set file content to empty
            if reset_responses:
                annot.delete_responses()
            if annot.type[0] == PDF_ANNOT_REDACT:
                found_redacts = True

        if redactions and found_redacts:
            page.apply_redactions(images=redact_images)

        if not page.getContents():  # safeguard against empty /Contents
            continue

        if not (clean_pages or hidden_text):
            continue  # done with the page

        page.cleanContents(sanitize=True)

        if hidden_text:
            xref = page.getContents()[0]  # only one b/o cleaning!
            cont = doc.xrefStream(xref)
            cont_lines = remove_hidden(cont.splitlines())  # remove hidden text
            if cont_lines:  # something was actually removed
                cont = b"\n".join(cont_lines)
                doc.updateStream(xref, cont)  # rewrite the page /Contents


def fillTextbox(
    writer, rect, text, pos=None, font=None, fontsize=11, align=0, warn=True
):
    """Fill a rectangle with text.

    Args:
        writer: TextWriter object (= "self")
        text: string or list/tuple of strings.
        rect: rect-like to receive the text.
        pos: point-like start position of first word.
        font: Font object (default Font('helv')).
        fontsize: the fontsize.
        align: (int) 0 = left, 1 = center, 2 = right, 3 = justify
        warn: (bool) just warn on text overflow, else raise exception.
    """
    textlen = lambda x: font.text_length(x, fontsize)  # just for abbreviation

    rect = fitz.Rect(rect)
    if rect.isEmpty or rect.isInfinite:
        raise ValueError("fill rect must be finite and not empty.")

    if type(font) is not Font:
        font = Font("helv")

    tolerance = fontsize * 0.25
    width = rect.width - tolerance  # available horizontal space

    len_space = textlen(" ")  # width of space character

    # starting point of the text
    if pos is not None:
        pos = Point(pos)
        if not pos in rect:
            raise ValueError("'pos' must be inside 'rect'")
    else:  # default is just below rect top-left
        pos = rect.tl + (tolerance, fontsize * 1.3)

    # calculate displacement factor for alignment
    if align == fitz.TEXT_ALIGN_CENTER:
        factor = 0.5
    elif align == fitz.TEXT_ALIGN_RIGHT:
        factor = 1.0
    else:
        factor = 0

    # split in lines if just a string was given
    if type(text) not in (tuple, list):
        text = text.splitlines()

    text = " \n".join(text).split(" ")  # split in words, preserve line breaks

    # compute lists of words and word lengths
    words = []  # recomputed list of words
    len_words = []  # corresponding lengths

    for word in text:
        # fill the lists of words and their lengths
        # this splits words longer than width into chunks, which each are
        # treated as words themselves.
        if word.startswith("\n"):
            len_word = textlen(word[1:])
        else:
            len_word = textlen(word)
        if len_word <= width:  # simple case: word not longer than a line
            words.append(word)
            len_words.append(len_word)
            continue
        # deal with an extra long word
        w = word[0]  # start with 1st char
        l = textlen(w)  # and its length
        for i in range(1, len(word)):
            nl = textlen(word[i])  # next char length
            if l + nl > width:  # if too long
                words.append(w)  # append what we have so far
                len_words.append(l)
                w = word[i]  # start over with new char
                l = nl  # and its length
            else:  # if still fitting
                w += word[i]  # just append char
                l += nl  # and add its length
        words.append(w)  # output tail of long word
        len_words.append(l)  # output length of long word tail

    idx = 0  # index of current word processed
    line_ctr = 0  # counter for output lines
    end_idx = len(words)  # number of words

    # -------------------------------------------------------------------------
    # each loop outputs one line
    # -------------------------------------------------------------------------
    while True:
        if idx >= end_idx:  # all words processed
            break

        # compute the new insertion point
        if line_ctr == 0 and len_words[0] >= rect.x1 - pos.x and idx == 0:
            line_ctr = 1  # first word wont fit in first line: take next one

        if line_ctr == 0:  # first line in rect
            start = pos
            width = rect.x1 - pos.x
        else:
            start = Point(rect.x0 + tolerance, pos.y + fontsize * 1.3 * line_ctr)
            width = rect.width - tolerance

        if start.y > rect.y1:  # landed below rectangle area
            if warn:
                print("Warning: only fitting %i of %i total words." % (idx, end_idx))
                break
            else:
                raise ValueError("only fitting %i of %i total words." % (idx, end_idx))

        word = words[idx]  # get first word for the line
        if word.startswith("\n"):  # remove any leading line breaks
            word = word[1:]

        line = [word]  # list of words fitting in this line
        len_line = [len_words[idx]]  # list of word lengths

        exhausted = False  # switch indicating we are done
        justify = True  # enable text justify as default
        next_words = range(idx + 1, end_idx)  # remaining words in text

        for i in next_words:  # try adding more words to the line
            nw = words[i]  # next word
            if nw.startswith("\n"):  # forced line break
                justify = False  # do not justify this current line
                break
            tl = len_space + len_words[i]
            if tl + sum(len_line) + (len(line) - 1) * len_space > width:  # won't fit
                break
            line.append(nw)  # append new word
            len_line.append(len_words[i])  # add its length
            if i >= end_idx - 1:  # if we exhausted the words
                justify = False  # do not justify current line
                exhausted = True  # and turn on switch

        # finished preparing a line
        if align != fitz.TEXT_ALIGN_JUSTIFY:  # trivial alignments
            fin_len = sum(len_line) + (len(line) - 1) * len_space
            d = (width - fin_len) * factor  # takes care of alignment
            start.x += d
            writer.append(start, " ".join(line), font, fontsize)
        else:  # take care of justified alignment
            writer.append(start, line[0], font, fontsize)  # always 1st word
            if len(line) > 1:  # more than one word in the line
                if justify is False:  # if no justify use space as gap
                    gap = len_space
                else:
                    gap = (width - sum(len_line)) / (len(line) - 1)
                this_gap = len_line[0] + gap  # gap for 2nd word
                for j in range(1, len(line)):
                    writer.append(start + (this_gap, 0), line[j], font, fontsize)
                    this_gap += len_line[j] + gap  # gap for next word

        if len(next_words) == 0 or exhausted is True:  # no words left
            break

        idx = i  # number of next word to read
        line_ctr += 1  # line counter

    return (idx, end_idx)  # return count of processed words, total words


# ------------------------------------------------------------------------
# Optional Content functions
# ------------------------------------------------------------------------
def set_ocmd(doc, xref=0, ocgs=None, policy=None, ve=None):
    """Create or update an OCMD object in a PDF document.

    Args:
        xref: (int) 0 for creating a new object, otherwise update existing one.
        ocgs: (list) OCG xref numbers, which shall be subject to 'policy'.
        policy: one of 'AllOn', 'AllOff', 'AnyOn', 'AnyOff' (any casing).
        ve: (list) visibility expression. Use instead of 'ocgs' with 'policy'.

    Returns:
        Xref of the created or updated OCMD.
    """

    all_ocgs = doc.getOCGs().keys()

    def ve_maker(ve):
        if len(ve) < 2:
            raise ValueError("bad format: less than two items, %s" % ve)
        if ve[0].lower() not in ("and", "or", "not"):
            raise ValueError("bad operand: %s" % ve[0])
        if ve[0].lower() == "not" and len(ve) != 2:
            raise ValueError("bad format: require one operand, %s" % ve)
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
    if ocgs and type(ocgs) in (list, tuple):
        ocgs_str = "/OCGs["
        for item in ocgs:
            if item not in all_ocgs:
                raise ValueError("bad OCG %i" % item)
            ocgs_str += "%i 0 R " % item
        ocgs_str[-1] = "]"
        text += ocgs_str
    if not policy:
        policy = "/P/AnyOn"
    else:
        policy = policy.lower()
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
    if xref == 0:
        xref = doc._getNewXref()
    else:
        check = doc.xrefObject(xref, compressed=True)
        if "/Type/OCMD" not in check:
            raise ValueError("bad xref or not an OCMD")
    doc.updateObject(xref, text)
    return xref


def get_ocmd(doc, xref):
    """Return the definition of an OCMD (optional content membership dictionary).

    Recognizes PDF dict keys /OCGs (array of OCGs), /P (policy string) and /VE
    (visibility expression, PDF array). Via string manipulytion, this
    information is converted to a Python dictionary with the keys "ocgs",
    "policy" and "ve".
    """

    if xref not in range(doc.xrefLength()):
        raise ValueError("bad xref")
    text = doc.xrefObject(xref, compressed=True)
    if "/Type/OCMD" not in text:
        raise ValueError("bad object type")
    textlen = len(text)
    p0 = text.find("/OCGs[")
    p1 = text.find("]", p0)
    if p0 < 0 or p1 < 0:  # no OCGs found
        ocgs = None
    else:
        ocgs = text[p0 + 6 : p1].replace("0 R", " ").split()
        ocgs = list(map(int, ocgs))
    p0 = text.find("/P/")
    p1 = text.find("ff", p0)
    if p1 < 0:
        p1 = text.find("on", p0)
    if p0 < 0 or p1 < 0:  # no policy found
        policy = None
    else:
        policy = text[p0 + 3 : p1 + 2]
    p0 = text.find("/VE[")
    if p0 < 0:  # no visibility expression found
        ve = None
    else:
        lp = rp = 0  # find end of /VE by finding last ']'.
        p1 = p0
        while lp < 1 or lp != rp:
            p1 += 1
            if not p1 < textlen:
                raise ValueError("bad object at xref")
            if text[p1] == "[":
                lp += 1
            if text[p1] == "]":
                rp += 1
        ve = text[p0 + 3 : p1 + 1]  # the PDF /VE array
        ve = (
            ve.replace("/And", '"and",')
            .replace("/Not", '"not",')
            .replace("/Or", '"or",')
        )
        ve = ve.replace(" 0 R]", "]").replace(" 0 R", ",").replace("][", "],[")
        ve = json.loads(ve)
    return {"xref": xref, "ocgs": ocgs, "policy": policy, "ve": ve}
