# -----------------------------------------------------------------------------
# Copyright 2020-2022, Harald Lieder, mailto:harald.lieder@outlook.com
# License: GNU AFFERO GPL 3.0, https://www.gnu.org/licenses/agpl-3.0.html
# Part of "PyMuPDF", Python bindings for "MuPDF" (http://mupdf.com), a
# lightweight PDF, XPS, and E-book viewer, renderer and toolkit which is
# maintained and developed by Artifex Software, Inc. https://artifex.com.
# -----------------------------------------------------------------------------
import argparse
import bisect
import os
import sys
import statistics
from typing import Dict, List, Set, Tuple

import fitz
from fitz.fitz import (
    TEXT_INHIBIT_SPACES,
    TEXT_PRESERVE_LIGATURES,
    TEXT_PRESERVE_WHITESPACE,
)

mycenter = lambda x: (" %s " % x).center(75, "-")


def recoverpix(doc, item):
    """Return image for a given XREF."""
    x = item[0]  # xref of PDF image
    s = item[1]  # xref of its /SMask
    if s == 0:  # no smask: use direct image output
        return doc.extract_image(x)

    def getimage(pix):
        if pix.colorspace.n != 4:
            return pix
        tpix = fitz.Pixmap(fitz.csRGB, pix)
        return tpix

    # we need to reconstruct the alpha channel with the smask
    pix1 = fitz.Pixmap(doc, x)
    pix2 = fitz.Pixmap(doc, s)  # create pixmap of the /SMask entry

    """Sanity check:
    - both pixmaps must have the same rectangle
    - both pixmaps must have alpha=0
    - pix2 must consist of 1 byte per pixel
    """
    if not (pix1.irect == pix2.irect and pix1.alpha == pix2.alpha == 0 and pix2.n == 1):
        fitz.message("Warning: unsupported /SMask %i for %i:" % (s, x))
        fitz.message(pix2)
        pix2 = None
        return getimage(pix1)  # return the pixmap as is

    pix = fitz.Pixmap(pix1)  # copy of pix1, with an alpha channel added
    pix.set_alpha(pix2.samples)  # treat pix2.samples as the alpha values
    pix1 = pix2 = None  # free temp pixmaps

    # we may need to adjust something for CMYK pixmaps here:
    return getimage(pix)


def open_file(filename, password, show=False, pdf=True):
    """Open and authenticate a document."""
    doc = fitz.open(filename)
    if not doc.is_pdf and pdf is True:
        sys.exit("this command supports PDF files only")
    rc = -1
    if not doc.needs_pass:
        return doc
    if password:
        rc = doc.authenticate(password)
        if not rc:
            sys.exit("authentication unsuccessful")
        if show is True:
            fitz.message("authenticated as %s" % "owner" if rc > 2 else "user")
    else:
        sys.exit("'%s' requires a password" % doc.name)
    return doc


def print_dict(item):
    """Print a Python dictionary."""
    l = max([len(k) for k in item.keys()]) + 1
    for k, v in item.items():
        msg = "%s: %s" % (k.rjust(l), v)
        fitz.message(msg)
    return


def print_xref(doc, xref):
    """Print an object given by XREF number.

    Simulate the PDF source in "pretty" format.
    For a stream also print its size.
    """
    fitz.message("%i 0 obj" % xref)
    xref_str = doc.xref_object(xref)
    fitz.message(xref_str)
    if doc.xref_is_stream(xref):
        temp = xref_str.split()
        try:
            idx = temp.index("/Length") + 1
            size = temp[idx]
            if size.endswith("0 R"):
                size = "unknown"
        except:
            size = "unknown"
        fitz.message("stream\n...%s bytes" % size)
        fitz.message("endstream")
    fitz.message("endobj")


def get_list(rlist, limit, what="page"):
    """Transform a page / xref specification into a list of integers.

    Args
    ----
        rlist: (str) the specification
        limit: maximum number, i.e. number of pages, number of objects
        what: a string to be used in error messages
    Returns
    -------
        A list of integers representing the specification.
    """
    N = str(limit - 1)
    rlist = rlist.replace("N", N).replace(" ", "")
    rlist_arr = rlist.split(",")
    out_list = []
    for seq, item in enumerate(rlist_arr):
        n = seq + 1
        if item.isdecimal():  # a single integer
            i = int(item)
            if 1 <= i < limit:
                out_list.append(int(item))
            else:
                sys.exit("bad %s specification at item %i" % (what, n))
            continue
        try:  # this must be a range now, and all of the following must work:
            i1, i2 = item.split("-")  # will fail if not 2 items produced
            i1 = int(i1)  # will fail on non-integers
            i2 = int(i2)
        except:
            sys.exit("bad %s range specification at item %i" % (what, n))

        if not (1 <= i1 < limit and 1 <= i2 < limit):
            sys.exit("bad %s range specification at item %i" % (what, n))

        if i1 == i2:  # just in case: a range of equal numbers
            out_list.append(i1)
            continue

        if i1 < i2:  # first less than second
            out_list += list(range(i1, i2 + 1))
        else:  # first larger than second
            out_list += list(range(i1, i2 - 1, -1))

    return out_list


def show(args):
    doc = open_file(args.input, args.password, True)
    size = os.path.getsize(args.input) / 1024
    flag = "KB"
    if size > 1000:
        size /= 1024
        flag = "MB"
    size = round(size, 1)
    meta = doc.metadata
    fitz.message(
        "'%s', pages: %i, objects: %i, %g %s, %s, encryption: %s"
        % (
            args.input,
            doc.page_count,
            doc.xref_length() - 1,
            size,
            flag,
            meta["format"],
            meta["encryption"],
        )
    )
    n = doc.is_form_pdf
    if n > 0:
        s = doc.get_sigflags()
        fitz.message(
            "document contains %i root form fields and is %ssigned"
            % (n, "not " if s != 3 else "")
        )
    n = doc.embfile_count()
    if n > 0:
        fitz.message("document contains %i embedded files" % n)
    fitz.message()
    if args.catalog:
        fitz.message(mycenter("PDF catalog"))
        xref = doc.pdf_catalog()
        print_xref(doc, xref)
        fitz.message()
    if args.metadata:
        fitz.message(mycenter("PDF metadata"))
        print_dict(doc.metadata)
        fitz.message()
    if args.xrefs:
        fitz.message(mycenter("object information"))
        xrefl = get_list(args.xrefs, doc.xref_length(), what="xref")
        for xref in xrefl:
            print_xref(doc, xref)
            fitz.message()
    if args.pages:
        fitz.message(mycenter("page information"))
        pagel = get_list(args.pages, doc.page_count + 1)
        for pno in pagel:
            n = pno - 1
            xref = doc.page_xref(n)
            fitz.message("Page %i:" % pno)
            print_xref(doc, xref)
            fitz.message()
    if args.trailer:
        fitz.message(mycenter("PDF trailer"))
        fitz.message(doc.pdf_trailer())
        fitz.message()
    doc.close()


def clean(args):
    doc = open_file(args.input, args.password, pdf=True)
    encryption = args.encryption
    encrypt = ("keep", "none", "rc4-40", "rc4-128", "aes-128", "aes-256").index(
        encryption
    )

    if not args.pages:  # simple cleaning
        doc.save(
            args.output,
            garbage=args.garbage,
            deflate=args.compress,
            pretty=args.pretty,
            clean=args.sanitize,
            ascii=args.ascii,
            linear=args.linear,
            encryption=encrypt,
            owner_pw=args.owner,
            user_pw=args.user,
            permissions=args.permission,
        )
        return

    # create sub document from page numbers
    pages = get_list(args.pages, doc.page_count + 1)
    outdoc = fitz.open()
    for pno in pages:
        n = pno - 1
        outdoc.insert_pdf(doc, from_page=n, to_page=n)
    outdoc.save(
        args.output,
        garbage=args.garbage,
        deflate=args.compress,
        pretty=args.pretty,
        clean=args.sanitize,
        ascii=args.ascii,
        linear=args.linear,
        encryption=encrypt,
        owner_pw=args.owner,
        user_pw=args.user,
        permissions=args.permission,
    )
    doc.close()
    outdoc.close()
    return


def doc_join(args):
    """Join pages from several PDF documents."""
    doc_list = args.input  # a list of input PDFs
    doc = fitz.open()  # output PDF
    for src_item in doc_list:  # process one input PDF
        src_list = src_item.split(",")
        password = src_list[1] if len(src_list) > 1 else None
        src = open_file(src_list[0], password, pdf=True)
        pages = ",".join(src_list[2:])  # get 'pages' specifications
        if pages:  # if anything there, retrieve a list of desired pages
            page_list = get_list(",".join(src_list[2:]), src.page_count + 1)
        else:  # take all pages
            page_list = range(1, src.page_count + 1)
        for i in page_list:
            doc.insert_pdf(src, from_page=i - 1, to_page=i - 1)  # copy each source page
        src.close()

    doc.save(args.output, garbage=4, deflate=True)
    doc.close()


def embedded_copy(args):
    """Copy embedded files between PDFs."""
    doc = open_file(args.input, args.password, pdf=True)
    if not doc.can_save_incrementally() and (
        not args.output or args.output == args.input
    ):
        sys.exit("cannot save PDF incrementally")
    src = open_file(args.source, args.pwdsource)
    names = set(args.name) if args.name else set()
    src_names = set(src.embfile_names())
    if names:
        if not names <= src_names:
            sys.exit("not all names are contained in source")
    else:
        names = src_names
    if not names:
        sys.exit("nothing to copy")
    intersect = names & set(doc.embfile_names())  # any equal name already in target?
    if intersect:
        sys.exit("following names already exist in receiving PDF: %s" % str(intersect))

    for item in names:
        info = src.embfile_info(item)
        buff = src.embfile_get(item)
        doc.embfile_add(
            item,
            buff,
            filename=info["filename"],
            ufilename=info["ufilename"],
            desc=info["desc"],
        )
        fitz.message("copied entry '%s' from '%s'" % (item, src.name))
    src.close()
    if args.output and args.output != args.input:
        doc.save(args.output, garbage=3)
    else:
        doc.saveIncr()
    doc.close()


def embedded_del(args):
    """Delete an embedded file entry."""
    doc = open_file(args.input, args.password, pdf=True)
    if not doc.can_save_incrementally() and (
        not args.output or args.output == args.input
    ):
        sys.exit("cannot save PDF incrementally")

    exception_types = (ValueError, mupdf.FzErrorBase)
    if mupdf_version_tuple < (1, 24):
        exception_types = ValueError
    try:
        doc.embfile_del(args.name)
    except exception_types as e:
        sys.exit(f'no such embedded file {args.name!r}: {e}')
    if not args.output or args.output == args.input:
        doc.save_incr()
    else:
        doc.save(args.output, garbage=1)
    doc.close()


def embedded_get(args):
    """Retrieve contents of an embedded file."""
    doc = open_file(args.input, args.password, pdf=True)
    exception_types = (ValueError, mupdf.FzErrorBase)
    if mupdf_version_tuple < (1, 24):
        exception_types = ValueError
    try:
        stream = doc.embfile_get(args.name)
        d = doc.embfile_info(args.name)
    except exception_types as e:
        sys.exit(f'no such embedded file {args.name!r}: {e}')
    filename = args.output if args.output else d["filename"]
    output = open(filename, "wb")
    output.write(stream)
    output.close()
    fitz.message("saved entry '%s' as '%s'" % (args.name, filename))
    doc.close()


def embedded_add(args):
    """Insert a new embedded file."""
    doc = open_file(args.input, args.password, pdf=True)
    if not doc.can_save_incrementally() and (
        args.output is None or args.output == args.input
    ):
        sys.exit("cannot save PDF incrementally")

    try:
        doc.embfile_del(args.name)
        sys.exit("entry '%s' already exists" % args.name)
    except:
        pass

    if not os.path.exists(args.path) or not os.path.isfile(args.path):
        sys.exit("no such file '%s'" % args.path)
    stream = open(args.path, "rb").read()
    filename = args.path
    ufilename = filename
    if not args.desc:
        desc = filename
    else:
        desc = args.desc
    doc.embfile_add(
        args.name, stream, filename=filename, ufilename=ufilename, desc=desc
    )
    if not args.output or args.output == args.input:
        doc.saveIncr()
    else:
        doc.save(args.output, garbage=3)
    doc.close()


def embedded_upd(args):
    """Update contents or metadata of an embedded file."""
    doc = open_file(args.input, args.password, pdf=True)
    if not doc.can_save_incrementally() and (
        args.output is None or args.output == args.input
    ):
        sys.exit("cannot save PDF incrementally")

    try:
        doc.embfile_info(args.name)
    except:
        sys.exit("no such embedded file '%s'" % args.name)

    if (
        args.path is not None
        and os.path.exists(args.path)
        and os.path.isfile(args.path)
    ):
        stream = open(args.path, "rb").read()
    else:
        stream = None

    if args.filename:
        filename = args.filename
    else:
        filename = None

    if args.ufilename:
        ufilename = args.ufilename
    elif args.filename:
        ufilename = args.filename
    else:
        ufilename = None

    if args.desc:
        desc = args.desc
    else:
        desc = None

    doc.embfile_upd(
        args.name, stream, filename=filename, ufilename=ufilename, desc=desc
    )
    if args.output is None or args.output == args.input:
        doc.saveIncr()
    else:
        doc.save(args.output, garbage=3)
    doc.close()


def embedded_list(args):
    """List embedded files."""
    doc = open_file(args.input, args.password, pdf=True)
    names = doc.embfile_names()
    if args.name is not None:
        if args.name not in names:
            sys.exit("no such embedded file '%s'" % args.name)
        else:
            fitz.message()
            fitz.message(
                "printing 1 of %i embedded file%s:"
                % (len(names), "s" if len(names) > 1 else "")
            )
            fitz.message()
            print_dict(doc.embfile_info(args.name))
            fitz.message()
            return
    if not names:
        fitz.message("'%s' contains no embedded files" % doc.name)
        return
    if len(names) > 1:
        msg = "'%s' contains the following %i embedded files" % (doc.name, len(names))
    else:
        msg = "'%s' contains the following embedded file" % doc.name
    fitz.message(msg)
    fitz.message()
    for name in names:
        if not args.detail:
            fitz.message(name)
            continue
        _ = doc.embfile_info(name)
        print_dict(doc.embfile_info(name))
        fitz.message()
    doc.close()


def extract_objects(args):
    """Extract images and / or fonts from a PDF."""
    if not args.fonts and not args.images:
        sys.exit("neither fonts nor images requested")
    doc = open_file(args.input, args.password, pdf=True)

    if args.pages:
        pages = get_list(args.pages, doc.page_count + 1)
    else:
        pages = range(1, doc.page_count + 1)

    if not args.output:
        out_dir = os.path.abspath(os.curdir)
    else:
        out_dir = args.output
        if not (os.path.exists(out_dir) and os.path.isdir(out_dir)):
            sys.exit("output directory %s does not exist" % out_dir)

    font_xrefs = set()  # already saved fonts
    image_xrefs = set()  # already saved images

    for pno in pages:
        if args.fonts:
            itemlist = doc.get_page_fonts(pno - 1)
            for item in itemlist:
                xref = item[0]
                if xref not in font_xrefs:
                    font_xrefs.add(xref)
                    fontname, ext, _, buffer = doc.extract_font(xref)
                    if ext == "n/a" or not buffer:
                        continue
                    outname = os.path.join(
                        out_dir, f"{fontname.replace(' ', '-')}-{xref}.{ext}"
                    )
                    outfile = open(outname, "wb")
                    outfile.write(buffer)
                    outfile.close()
                    buffer = None
        if args.images:
            itemlist = doc.get_page_images(pno - 1)
            for item in itemlist:
                xref = item[0]
                if xref not in image_xrefs:
                    image_xrefs.add(xref)
                    pix = recoverpix(doc, item)
                    if type(pix) is dict:
                        ext = pix["ext"]
                        imgdata = pix["image"]
                        outname = os.path.join(out_dir, "img-%i.%s" % (xref, ext))
                        outfile = open(outname, "wb")
                        outfile.write(imgdata)
                        outfile.close()
                    else:
                        outname = os.path.join(out_dir, "img-%i.png" % xref)
                        pix2 = (
                            pix
                            if pix.colorspace.n < 4
                            else fitz.Pixmap(fitz.csRGB, pix)
                        )
                        pix2.save(outname)

    if args.fonts:
        fitz.message("saved %i fonts to '%s'" % (len(font_xrefs), out_dir))
    if args.images:
        fitz.message("saved %i images to '%s'" % (len(image_xrefs), out_dir))
    doc.close()


def page_simple(page, textout, GRID, fontsize, noformfeed, skip_empty, flags):
    eop = b"\n" if noformfeed else bytes([12])
    text = page.get_text("text", flags=flags)
    if not text:
        if not skip_empty:
            textout.write(eop)  # write formfeed
        return
    textout.write(text.encode("utf8", errors="surrogatepass"))
    textout.write(eop)
    return


def page_blocksort(page, textout, GRID, fontsize, noformfeed, skip_empty, flags):
    eop = b"\n" if noformfeed else bytes([12])
    blocks = page.get_text("blocks", flags=flags)
    if blocks == []:
        if not skip_empty:
            textout.write(eop)  # write formfeed
        return
    blocks.sort(key=lambda b: (b[3], b[0]))
    for b in blocks:
        textout.write(b[4].encode("utf8", errors="surrogatepass"))
    textout.write(eop)
    return


def page_layout(page, textout, GRID, fontsize, noformfeed, skip_empty, flags):
    eop = b"\n" if noformfeed else bytes([12])

    # --------------------------------------------------------------------
    def find_line_index(values: List[int], value: int) -> int:
        """Find the right row coordinate.

        Args:
            values: (list) y-coordinates of rows.
            value: (int) lookup for this value (y-origin of char).
        Returns:
            y-ccordinate of appropriate line for value.
        """
        i = bisect.bisect_right(values, value)
        if i:
            return values[i - 1]
        raise RuntimeError("Line for %g not found in %s" % (value, values))

    # --------------------------------------------------------------------
    def curate_rows(rows: Set[int], GRID) -> List:
        rows = list(rows)
        rows.sort()  # sort ascending
        nrows = [rows[0]]
        for h in rows[1:]:
            if h >= nrows[-1] + GRID:  # only keep significant differences
                nrows.append(h)
        return nrows  # curated list of line bottom coordinates

    def process_blocks(blocks: List[Dict], page: fitz.Page):
        rows = set()
        page_width = page.rect.width
        page_height = page.rect.height
        rowheight = page_height
        left = page_width
        right = 0
        chars = []
        for block in blocks:
            for line in block["lines"]:
                if line["dir"] != (1, 0):  # ignore non-horizontal text
                    continue
                x0, y0, x1, y1 = line["bbox"]
                if y1 < 0 or y0 > page.rect.height:  # ignore if outside CropBox
                    continue
                # upd row height
                height = y1 - y0

                if rowheight > height:
                    rowheight = height
                for span in line["spans"]:
                    if span["size"] <= fontsize:
                        continue
                    for c in span["chars"]:
                        x0, _, x1, _ = c["bbox"]
                        cwidth = x1 - x0
                        ox, oy = c["origin"]
                        oy = int(round(oy))
                        rows.add(oy)
                        ch = c["c"]
                        if left > ox and ch != " ":
                            left = ox  # update left coordinate
                        if right < x1:
                            right = x1  # update right coordinate
                        # handle ligatures:
                        if cwidth == 0 and chars != []:  # potential ligature
                            old_ch, old_ox, old_oy, old_cwidth = chars[-1]
                            if old_oy == oy:  # ligature
                                if old_ch != chr(0xFB00):  # previous "ff" char lig?
                                    lig = joinligature(old_ch + ch)  # no
                                # convert to one of the 3-char ligatures:
                                elif ch == "i":
                                    lig = chr(0xFB03)  # "ffi"
                                elif ch == "l":
                                    lig = chr(0xFB04)  # "ffl"
                                else:  # something wrong, leave old char in place
                                    lig = old_ch
                                chars[-1] = (lig, old_ox, old_oy, old_cwidth)
                                continue
                        chars.append((ch, ox, oy, cwidth))  # all chars on page
        return chars, rows, left, right, rowheight

    def joinligature(lig: str) -> str:
        """Return ligature character for a given pair / triple of characters.

        Args:
            lig: (str) 2/3 characters, e.g. "ff"
        Returns:
            Ligature, e.g. "ff" -> chr(0xFB00)
        """

        if lig == "ff":
            return chr(0xFB00)
        elif lig == "fi":
            return chr(0xFB01)
        elif lig == "fl":
            return chr(0xFB02)
        elif lig == "ffi":
            return chr(0xFB03)
        elif lig == "ffl":
            return chr(0xFB04)
        elif lig == "ft":
            return chr(0xFB05)
        elif lig == "st":
            return chr(0xFB06)
        return lig

    # --------------------------------------------------------------------
    def make_textline(left, slot, minslot, lchars):
        """Produce the text of one output line.

        Args:
            left: (float) left most coordinate used on page
            slot: (float) avg width of one character in any font in use.
            minslot: (float) min width for the characters in this line.
            chars: (list[tuple]) characters of this line.
        Returns:
            text: (str) text string for this line
        """
        text = ""  # we output this
        old_char = ""
        old_x1 = 0  # end coordinate of last char
        old_ox = 0  # x-origin of last char
        if minslot <= fitz.EPSILON:
            raise RuntimeError("program error: minslot too small = %g" % minslot)

        for c in lchars:  # loop over characters
            char, ox, _, cwidth = c
            ox = ox - left  # its (relative) start coordinate
            x1 = ox + cwidth  # ending coordinate

            # eliminate overprint effect
            if old_char == char and ox - old_ox <= cwidth * 0.2:
                continue

            # omit spaces overlapping previous char
            if char == " " and (old_x1 - ox) / cwidth > 0.8:
                continue

            old_char = char
            # close enough to previous?
            if ox < old_x1 + minslot:  # assume char adjacent to previous
                text += char  # append to output
                old_x1 = x1  # new end coord
                old_ox = ox  # new origin.x
                continue

            # else next char starts after some gap:
            # fill in right number of spaces, so char is positioned
            # in the right slot of the line
            if char == " ":  # rest relevant for non-space only
                continue
            delta = int(ox / slot) - len(text)
            if ox > old_x1 and delta > 1:
                text += " " * delta
            # now append char
            text += char
            old_x1 = x1  # new end coordinate
            old_ox = ox  # new origin
        return text.rstrip()

    # extract page text by single characters ("rawdict")
    blocks = page.get_text("rawdict", flags=flags)["blocks"]
    chars, rows, left, right, rowheight = process_blocks(blocks, page)

    if chars == []:
        if not skip_empty:
            textout.write(eop)  # write formfeed
        return
    # compute list of line coordinates - ignoring small (GRID) differences
    rows = curate_rows(rows, GRID)

    # sort all chars by x-coordinates, so every line will receive char info,
    # sorted from left to right.
    chars.sort(key=lambda c: c[1])

    # populate the lines with their char info
    lines = {}  # key: y1-ccordinate, value: char list
    for c in chars:
        _, _, oy, _ = c
        y = find_line_index(rows, oy)  # y-coord of the right line
        lchars = lines.get(y, [])  # read line chars so far
        lchars.append(c)  # append this char
        lines[y] = lchars  # write back to line

    # ensure line coordinates are ascending
    keys = list(lines.keys())
    keys.sort()

    # -------------------------------------------------------------------------
    # Compute "char resolution" for the page: the char width corresponding to
    # 1 text char position on output - call it 'slot'.
    # For each line, compute median of its char widths. The minimum across all
    # lines is 'slot'.
    # The minimum char width of each line is used to determine if spaces must
    # be inserted in between two characters.
    # -------------------------------------------------------------------------
    slot = right - left
    minslots = {}
    for k in keys:
        lchars = lines[k]
        ccount = len(lchars)
        if ccount < 2:
            minslots[k] = 1
            continue
        widths = [c[3] for c in lchars]
        widths.sort()
        this_slot = statistics.median(widths)  # take median value
        if this_slot < slot:
            slot = this_slot
        minslots[k] = widths[0]

    # compute line advance in text output
    rowheight = rowheight * (rows[-1] - rows[0]) / (rowheight * len(rows)) * 1.2
    rowpos = rows[0]  # first line positioned here
    textout.write(b"\n")
    for k in keys:  # walk through the lines
        while rowpos < k:  # honor distance between lines
            textout.write(b"\n")
            rowpos += rowheight
        text = make_textline(left, slot, minslots[k], lines[k])
        textout.write((text + "\n").encode("utf8", errors="surrogatepass"))
        rowpos = k + rowheight

    textout.write(eop)  # write formfeed


def gettext(args):
    doc = open_file(args.input, args.password, pdf=False)
    pagel = get_list(args.pages, doc.page_count + 1)
    output = args.output
    if output == None:
        filename, _ = os.path.splitext(doc.name)
        output = filename + ".txt"
    textout = open(output, "wb")
    flags = TEXT_PRESERVE_LIGATURES | TEXT_PRESERVE_WHITESPACE
    if args.convert_white:
        flags ^= TEXT_PRESERVE_WHITESPACE
    if args.noligatures:
        flags ^= TEXT_PRESERVE_LIGATURES
    if args.extra_spaces:
        flags ^= TEXT_INHIBIT_SPACES
    func = {
        "simple": page_simple,
        "blocks": page_blocksort,
        "layout": page_layout,
    }
    for pno in pagel:
        page = doc[pno - 1]
        func[args.mode](
            page,
            textout,
            args.grid,
            args.fontsize,
            args.noformfeed,
            args.skip_empty,
            flags=flags,
        )

    textout.close()


def _internal(args):
    fitz.message('This is from fitz.message().')
    fitz.log('This is from fitz.log().')

def main():
    """Define command configurations."""
    parser = argparse.ArgumentParser(
        prog="fitz",
        description=mycenter("Basic PyMuPDF Functions"),
    )
    subps = parser.add_subparsers(
        title="Subcommands", help="Enter 'command -h' for subcommand specific help"
    )

    # -------------------------------------------------------------------------
    # 'show' command
    # -------------------------------------------------------------------------
    ps_show = subps.add_parser("show", description=mycenter("display PDF information"))
    ps_show.add_argument("input", type=str, help="PDF filename")
    ps_show.add_argument("-password", help="password")
    ps_show.add_argument("-catalog", action="store_true", help="show PDF catalog")
    ps_show.add_argument("-trailer", action="store_true", help="show PDF trailer")
    ps_show.add_argument("-metadata", action="store_true", help="show PDF metadata")
    ps_show.add_argument(
        "-xrefs", type=str, help="show selected objects, format: 1,5-7,N"
    )
    ps_show.add_argument(
        "-pages", type=str, help="show selected pages, format: 1,5-7,50-N"
    )
    ps_show.set_defaults(func=show)

    # -------------------------------------------------------------------------
    # 'clean' command
    # -------------------------------------------------------------------------
    ps_clean = subps.add_parser(
        "clean", description=mycenter("optimize PDF, or create sub-PDF if pages given")
    )
    ps_clean.add_argument("input", type=str, help="PDF filename")
    ps_clean.add_argument("output", type=str, help="output PDF filename")
    ps_clean.add_argument("-password", help="password")

    ps_clean.add_argument(
        "-encryption",
        help="encryption method",
        choices=("keep", "none", "rc4-40", "rc4-128", "aes-128", "aes-256"),
        default="none",
    )

    ps_clean.add_argument("-owner", type=str, help="owner password")
    ps_clean.add_argument("-user", type=str, help="user password")

    ps_clean.add_argument(
        "-garbage",
        type=int,
        help="garbage collection level",
        choices=range(5),
        default=0,
    )

    ps_clean.add_argument(
        "-compress",
        action="store_true",
        default=False,
        help="compress (deflate) output",
    )

    ps_clean.add_argument(
        "-ascii", action="store_true", default=False, help="ASCII encode binary data"
    )

    ps_clean.add_argument(
        "-linear",
        action="store_true",
        default=False,
        help="format for fast web display",
    )

    ps_clean.add_argument(
        "-permission", type=int, default=-1, help="integer with permission levels"
    )

    ps_clean.add_argument(
        "-sanitize",
        action="store_true",
        default=False,
        help="sanitize / clean contents",
    )
    ps_clean.add_argument(
        "-pretty", action="store_true", default=False, help="prettify PDF structure"
    )
    ps_clean.add_argument(
        "-pages", help="output selected pages pages, format: 1,5-7,50-N"
    )
    ps_clean.set_defaults(func=clean)

    # -------------------------------------------------------------------------
    # 'join' command
    # -------------------------------------------------------------------------
    ps_join = subps.add_parser(
        "join",
        description=mycenter("join PDF documents"),
        epilog="specify each input as 'filename[,password[,pages]]'",
    )
    ps_join.add_argument("input", nargs="*", help="input filenames")
    ps_join.add_argument("-output", required=True, help="output filename")
    ps_join.set_defaults(func=doc_join)

    # -------------------------------------------------------------------------
    # 'extract' command
    # -------------------------------------------------------------------------
    ps_extract = subps.add_parser(
        "extract", description=mycenter("extract images and fonts to disk")
    )
    ps_extract.add_argument("input", type=str, help="PDF filename")
    ps_extract.add_argument("-images", action="store_true", help="extract images")
    ps_extract.add_argument("-fonts", action="store_true", help="extract fonts")
    ps_extract.add_argument(
        "-output", help="folder to receive output, defaults to current"
    )
    ps_extract.add_argument("-password", help="password")
    ps_extract.add_argument(
        "-pages", type=str, help="consider these pages only, format: 1,5-7,50-N"
    )
    ps_extract.set_defaults(func=extract_objects)

    # -------------------------------------------------------------------------
    # 'embed-info'
    # -------------------------------------------------------------------------
    ps_show = subps.add_parser(
        "embed-info", description=mycenter("list embedded files")
    )
    ps_show.add_argument("input", help="PDF filename")
    ps_show.add_argument("-name", help="if given, report only this one")
    ps_show.add_argument("-detail", action="store_true", help="detail information")
    ps_show.add_argument("-password", help="password")
    ps_show.set_defaults(func=embedded_list)

    # -------------------------------------------------------------------------
    # 'embed-add' command
    # -------------------------------------------------------------------------
    ps_embed_add = subps.add_parser(
        "embed-add", description=mycenter("add embedded file")
    )
    ps_embed_add.add_argument("input", help="PDF filename")
    ps_embed_add.add_argument("-password", help="password")
    ps_embed_add.add_argument(
        "-output", help="output PDF filename, incremental save if none"
    )
    ps_embed_add.add_argument("-name", required=True, help="name of new entry")
    ps_embed_add.add_argument("-path", required=True, help="path to data for new entry")
    ps_embed_add.add_argument("-desc", help="description of new entry")
    ps_embed_add.set_defaults(func=embedded_add)

    # -------------------------------------------------------------------------
    # 'embed-del' command
    # -------------------------------------------------------------------------
    ps_embed_del = subps.add_parser(
        "embed-del", description=mycenter("delete embedded file")
    )
    ps_embed_del.add_argument("input", help="PDF filename")
    ps_embed_del.add_argument("-password", help="password")
    ps_embed_del.add_argument(
        "-output", help="output PDF filename, incremental save if none"
    )
    ps_embed_del.add_argument("-name", required=True, help="name of entry to delete")
    ps_embed_del.set_defaults(func=embedded_del)

    # -------------------------------------------------------------------------
    # 'embed-upd' command
    # -------------------------------------------------------------------------
    ps_embed_upd = subps.add_parser(
        "embed-upd",
        description=mycenter("update embedded file"),
        epilog="except '-name' all parameters are optional",
    )
    ps_embed_upd.add_argument("input", help="PDF filename")
    ps_embed_upd.add_argument("-name", required=True, help="name of entry")
    ps_embed_upd.add_argument("-password", help="password")
    ps_embed_upd.add_argument(
        "-output", help="Output PDF filename, incremental save if none"
    )
    ps_embed_upd.add_argument("-path", help="path to new data for entry")
    ps_embed_upd.add_argument("-filename", help="new filename to store in entry")
    ps_embed_upd.add_argument(
        "-ufilename", help="new unicode filename to store in entry"
    )
    ps_embed_upd.add_argument("-desc", help="new description to store in entry")
    ps_embed_upd.set_defaults(func=embedded_upd)

    # -------------------------------------------------------------------------
    # 'embed-extract' command
    # -------------------------------------------------------------------------
    ps_embed_extract = subps.add_parser(
        "embed-extract", description=mycenter("extract embedded file to disk")
    )
    ps_embed_extract.add_argument("input", type=str, help="PDF filename")
    ps_embed_extract.add_argument("-name", required=True, help="name of entry")
    ps_embed_extract.add_argument("-password", help="password")
    ps_embed_extract.add_argument(
        "-output", help="output filename, default is stored name"
    )
    ps_embed_extract.set_defaults(func=embedded_get)

    # -------------------------------------------------------------------------
    # 'embed-copy' command
    # -------------------------------------------------------------------------
    ps_embed_copy = subps.add_parser(
        "embed-copy", description=mycenter("copy embedded files between PDFs")
    )
    ps_embed_copy.add_argument("input", type=str, help="PDF to receive embedded files")
    ps_embed_copy.add_argument("-password", help="password of input")
    ps_embed_copy.add_argument(
        "-output", help="output PDF, incremental save to 'input' if omitted"
    )
    ps_embed_copy.add_argument(
        "-source", required=True, help="copy embedded files from here"
    )
    ps_embed_copy.add_argument("-pwdsource", help="password of 'source' PDF")
    ps_embed_copy.add_argument(
        "-name", nargs="*", help="restrict copy to these entries"
    )
    ps_embed_copy.set_defaults(func=embedded_copy)

    # -------------------------------------------------------------------------
    # 'textlayout' command
    # -------------------------------------------------------------------------
    ps_gettext = subps.add_parser(
        "gettext", description=mycenter("extract text in various formatting modes")
    )
    ps_gettext.add_argument("input", type=str, help="input document filename")
    ps_gettext.add_argument("-password", help="password for input document")
    ps_gettext.add_argument(
        "-mode",
        type=str,
        help="mode: simple, block sort, or layout (default)",
        choices=("simple", "blocks", "layout"),
        default="layout",
    )
    ps_gettext.add_argument(
        "-pages",
        type=str,
        help="select pages, format: 1,5-7,50-N",
        default="1-N",
    )
    ps_gettext.add_argument(
        "-noligatures",
        action="store_true",
        help="expand ligature characters (default False)",
        default=False,
    )
    ps_gettext.add_argument(
        "-convert-white",
        action="store_true",
        help="convert whitespace characters to white (default False)",
        default=False,
    )
    ps_gettext.add_argument(
        "-extra-spaces",
        action="store_true",
        help="fill gaps with spaces (default False)",
        default=False,
    )
    ps_gettext.add_argument(
        "-noformfeed",
        action="store_true",
        help="write linefeeds, no formfeeds (default False)",
        default=False,
    )
    ps_gettext.add_argument(
        "-skip-empty",
        action="store_true",
        help="suppress pages with no text (default False)",
        default=False,
    )
    ps_gettext.add_argument(
        "-output",
        help="store text in this file (default inputfilename.txt)",
    )
    ps_gettext.add_argument(
        "-grid",
        type=float,
        help="merge lines if closer than this (default 2)",
        default=2,
    )
    ps_gettext.add_argument(
        "-fontsize",
        type=float,
        help="only include text with a larger fontsize (default 3)",
        default=3,
    )
    ps_gettext.set_defaults(func=gettext)

    # -------------------------------------------------------------------------
    # '_internal' command
    # -------------------------------------------------------------------------
    ps_internal = subps.add_parser(
        "internal", description=mycenter("internal testing")
    )
    ps_internal.set_defaults(func=_internal)

    # -------------------------------------------------------------------------
    # start program
    # -------------------------------------------------------------------------
    args = parser.parse_args()  # create parameter arguments class
    if not hasattr(args, "func"):  # no function selected
        parser.print_help()  # so print top level help
    else:
        args.func(args)  # execute requested command


if __name__ == "__main__":
    main()
