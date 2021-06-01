from __future__ import division, print_function

import os
import sys

import fitz

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
        print("Warning: unsupported /SMask %i for %i:" % (s, x))
        print(pix2)
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
            print("authenticated as %s" % "owner" if rc > 2 else "user")
    else:
        sys.exit("'%s' requires a password" % doc.name)
    return doc


def print_dict(item):
    """Print a Python dictionary."""
    l = max([len(k) for k in item.keys()]) + 1
    for k, v in item.items():
        msg = "%s: %s" % (k.rjust(l), v)
        print(msg)
    return


def print_xref(doc, xref):
    """Print an object given by XREF number.

    Simulate the PDF source in "pretty" format.
    For a stream also print its size.
    """
    print("%i 0 obj" % xref)
    xref_str = doc.xref_object(xref)
    print(xref_str)
    if doc.is_stream(xref):
        temp = xref_str.split()
        try:
            idx = temp.index("/Length") + 1
            size = temp[idx]
            if size.endswith("0 R"):
                size = "unknown"
        except:
            size = "unknown"
        print("stream\n...%s bytes" % size)
        print("endstream")
    print("endobj")


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
    print(
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
        print(
            "document contains %i root form fields and is %ssigned"
            % (n, "not " if s != 3 else "")
        )
    n = doc.embfile_count()
    if n > 0:
        print("document contains %i embedded files" % n)
    print()
    if args.catalog:
        print(mycenter("PDF catalog"))
        xref = doc.pdf_catalog()
        print_xref(doc, xref)
        print()
    if args.metadata:
        print(mycenter("PDF metadata"))
        print_dict(doc.metadata)
        print()
    if args.xrefs:
        print(mycenter("object information"))
        xrefl = get_list(args.xrefs, doc.xref_length(), what="xref")
        for xref in xrefl:
            print_xref(doc, xref)
            print()
    if args.pages:
        print(mycenter("page information"))
        pagel = get_list(args.pages, doc.page_count + 1)
        for pno in pagel:
            n = pno - 1
            xref = doc.page_xref(n)
            print("Page %i:" % pno)
            print_xref(doc, xref)
            print()
    if args.trailer:
        print(mycenter("PDF trailer"))
        print(doc.pdf_trailer())
        print()
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
        print("copied entry '%s' from '%s'" % (item, src.name))
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

    try:
        doc.embfile_del(args.name)
    except ValueError:
        sys.exit("no such embedded file '%s'" % args.name)
    if not args.output or args.output == args.input:
        doc.save_incr()
    else:
        doc.save(args.output, garbage=1)
    doc.close()


def embedded_get(args):
    """Retrieve contents of an embedded file."""
    doc = open_file(args.input, args.password, pdf=True)
    try:
        stream = doc.embfile_get(args.name)
        d = doc.embfile_info(args.name)
    except ValueError:
        sys.exit("no such embedded file '%s'" % args.name)
    filename = args.output if args.output else d["filename"]
    output = open(filename, "wb")
    output.write(stream)
    output.close()
    print("saved entry '%s' as '%s'" % (args.name, filename))
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
            print()
            print(
                "printing 1 of %i embedded file%s:"
                % (len(names), "s" if len(names) > 1 else "")
            )
            print()
            print_dict(doc.embfile_info(args.name))
            print()
            return
    if not names:
        print("'%s' contains no embedded files" % doc.name)
        return
    if len(names) > 1:
        msg = "'%s' contains the following %i embedded files" % (doc.name, len(names))
    else:
        msg = "'%s' contains the following embedded file" % doc.name
    print(msg)
    print()
    for name in names:
        if not args.detail:
            print(name)
            continue
        _ = doc.embfile_info(name)
        print_dict(doc.embfile_info(name))
        print()
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
                        out_dir, fontname.replace(" ", "-") + "." + ext
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
        print("saved %i fonts to '%s'" % (len(font_xrefs), out_dir))
    if args.images:
        print("saved %i images to '%s'" % (len(image_xrefs), out_dir))
    doc.close()


def main():
    """Define command configurations."""
    import argparse

    parser = argparse.ArgumentParser(
        description=mycenter("Basic PyMuPDF Functions"), prog="fitz"
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
    # start program
    # -------------------------------------------------------------------------
    args = parser.parse_args()  # create parameter arguments class
    if not hasattr(args, "func"):  # no function selected
        parser.print_help()  # so print top level help
    else:
        args.func(args)  # execute requested command


if __name__ == "__main__":
    main()
