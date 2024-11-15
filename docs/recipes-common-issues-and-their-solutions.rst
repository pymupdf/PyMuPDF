.. include:: header.rst

.. _RecipesCommonIssuesAndTheirSolutions:

==========================================
Common Issues and their Solutions
==========================================

How To Dynamically Clean Up Corrupt :title:`PDFs`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This shows a potential use of |PyMuPDF| with another Python PDF library (the excellent pure Python package `pdfrw <https://pypi.python.org/pypi/pdfrw>`_ is used here as an example).

If a clean, non-corrupt / decompressed PDF is needed, one could dynamically invoke PyMuPDF to recover from many problems like so::

 import sys
 from io import BytesIO
 from pdfrw import PdfReader
 import pymupdf

 #---------------------------------------
 # 'Tolerant' PDF reader
 #---------------------------------------
 def reader(fname, password = None):
     idata = open(fname, "rb").read()  # read the PDF into memory and
     ibuffer = BytesIO(idata)  # convert to stream
     if password is None:
         try:
             return PdfReader(ibuffer)  # if this works: fine!
         except:
             pass

     # either we need a password or it is a problem-PDF
     # create a repaired / decompressed / decrypted version
     doc = pymupdf.open("pdf", ibuffer)
     if password is not None:  # decrypt if password provided
         rc = doc.authenticate(password)
         if not rc > 0:
             raise ValueError("wrong password")
     c = doc.tobytes(garbage=3, deflate=True)
     del doc  # close & delete doc
     return PdfReader(BytesIO(c))  # let pdfrw retry
 #---------------------------------------
 # Main program
 #---------------------------------------
 pdf = reader("pymupdf.pdf", password = None) # include a password if necessary
 print pdf.Info
 # do further processing

With the command line utility *pdftk* (`available <https://www.pdflabs.com/tools/pdftk-the-pdf-toolkit/>`_ for Windows only, but reported to also run under `Wine <https://www.winehq.org/>`_) a similar result can be achieved, see `here <http://www.overthere.co.uk/2013/07/22/improving-pypdf2-with-pdftk/>`_. However, you must invoke it as a separate process via *subprocess.Popen*, using stdin and stdout as communication vehicles.



How to Convert Any Document to |PDF|
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here is a script that converts any |PyMuPDF| :ref:`supported document<Supported_File_Types>` to a |PDF|. These include XPS, EPUB, FB2, CBZ and image formats, including multi-page TIFF images.

It features maintaining any metadata, table of contents and links contained in the source document::

    """
    Demo script: Convert input file to a PDF
    -----------------------------------------
    Intended for multi-page input files like XPS, EPUB etc.

    Features:
    ---------
    Recovery of table of contents and links of input file.
    While this works well for bookmarks (outlines, table of contents),
    links will only work if they are not of type "LINK_NAMED".
    This link type is skipped by the script.

    For XPS and EPUB input, internal links however **are** of type "LINK_NAMED".
    Base library MuPDF does not resolve them to page numbers.

    So, for anyone expert enough to know the internal structure of these
    document types, can further interpret and resolve these link types.

    Dependencies
    --------------
    PyMuPDF v1.14.0+
    """
    import sys
    import pymupdf
    if not (list(map(int, pymupdf.VersionBind.split("."))) >= [1,14,0]):
        raise SystemExit("need PyMuPDF v1.14.0+")
    fn = sys.argv[1]

    print("Converting '%s' to '%s.pdf'" % (fn, fn))

    doc = pymupdf.open(fn)

    b = doc.convert_to_pdf()  # convert to pdf
    pdf = pymupdf.open("pdf", b)  # open as pdf

    toc= doc.get_toc()  # table of contents of input
    pdf.set_toc(toc)  # simply set it for output
    meta = doc.metadata  # read and set metadata
    if not meta["producer"]:
        meta["producer"] = "PyMuPDF v" + pymupdf.VersionBind

    if not meta["creator"]:
        meta["creator"] = "PyMuPDF PDF converter"
    meta["modDate"] = pymupdf.get_pdf_now()
    meta["creationDate"] = meta["modDate"]
    pdf.set_metadata(meta)

    # now process the links
    link_cnti = 0
    link_skip = 0
    for pinput in doc:  # iterate through input pages
        links = pinput.get_links()  # get list of links
        link_cnti += len(links)  # count how many
        pout = pdf[pinput.number]  # read corresp. output page
        for l in links:  # iterate though the links
            if l["kind"] == pymupdf.LINK_NAMED:  # we do not handle named links
                print("named link page", pinput.number, l)
                link_skip += 1  # count them
                continue
            pout.insert_link(l)  # simply output the others

    # save the conversion result
    pdf.save(fn + ".pdf", garbage=4, deflate=True)
    # say how many named links we skipped
    if link_cnti > 0:
        print("Skipped %i named links of a total of %i in input." % (link_skip, link_cnti))



Changing Annotations: Unexpected Behaviour
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Problem
^^^^^^^^^
There are two scenarios:

1. **Updating** an annotation with PyMuPDF which was created by some other software.
2. **Creating** an annotation with PyMuPDF and later changing it with some other software.

In both cases you may experience unintended changes, like a different annotation icon or text font, the fill color or line dashing have disappeared, line end symbols have changed their size or even have disappeared too, etc.

Cause
^^^^^^
Annotation maintenance is handled differently by each PDF maintenance application. Some annotation types may not be supported, or not be supported fully or some details may be handled in a different way than in another application. **There is no standard.**

Almost always a PDF application also comes with its own icons (file attachments, sticky notes and stamps) and its own set of supported text fonts. For example:

* (Py-) MuPDF only supports these 5 basic fonts for 'FreeText' annotations: Helvetica, Times-Roman, Courier, ZapfDingbats and Symbol -- no italics / no bold variations. When changing a 'FreeText' annotation created by some other app, its font will probably not be recognized nor accepted and be replaced by Helvetica.

* PyMuPDF supports all PDF text markers (highlight, underline, strikeout, squiggly), but these types cannot be updated with Adobe Acrobat Reader.

In most cases there also exists limited support for line dashing which causes existing dashes to be replaced by straight lines. For example:

* PyMuPDF fully supports all line dashing forms, while other viewers only accept a limited subset.


Solutions
^^^^^^^^^^
Unfortunately there is not much you can do in most of these cases.

1. Stay with the same software for **creating and changing** an annotation.
2. When using PyMuPDF to change an "alien" annotation, try to **avoid** :meth:`Annot.update`. The following methods **can be used without it,** so that the original appearance should be maintained:

  * :meth:`Annot.set_rect` (location changes)
  * :meth:`Annot.set_flags` (annotation behaviour)
  * :meth:`Annot.set_info` (meta information, except changes to *content*)
  * :meth:`Annot.set_popup` (create popup or change its rect)
  * :meth:`Annot.set_oc` (add / remove reference to optional content information)
  * :meth:`Annot.set_open`
  * :meth:`Annot.update_file` (file attachment changes)


Missing or Unreadable Extracted Text
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Fairly often, text extraction does not work text as you would expect: text may be missing, or may not appear in the reading sequence visible on your screen, or contain garbled characters (like a ? or a "TOFU" symbol), etc. This can be caused by a number of different problems.

Problem: no text is extracted
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Your PDF viewer does display text, but you cannot select it with your cursor, and text extraction delivers nothing.

Cause
^^^^^^
1. You may be looking at an image embedded in the PDF page (e.g. a scanned PDF).
2. The PDF creator used no font, but **simulated** text by painting it, using little lines and curves. E.g. a capital "D" could be painted by a line "|" and a left-open semi-circle, an "o" by an ellipse, and so on.

Solution
^^^^^^^^^^
Use an OCR software like `OCRmyPDF <https://pypi.org/project/ocrmypdf/>`_ to insert a hidden text layer underneath the visible page. The resulting PDF should behave as expected.

Problem: unreadable text
^^^^^^^^^^^^^^^^^^^^^^^^
Text extraction does not deliver the text in readable order, duplicates some text, or is otherwise garbled.

Cause
^^^^^^
1. The single characters are readable as such (no "<?>" symbols), but the sequence in which the text is **coded in the file** deviates from the reading order. The motivation behind may be technical or protection of data against unwanted copies.
2. Many "<?>" symbols occur, indicating MuPDF could not interpret these characters. The font may indeed be unsupported by MuPDF, or the PDF creator may haved used a font that displays readable text, but on purpose obfuscates the originating corresponding unicode character.

Solution
^^^^^^^^
1. Use layout preserving text extraction: `python -m fitz gettext file.pdf`.
2. If other text extraction tools also don't work, then the only solution again is OCRing the page.

.. include:: footer.rst
