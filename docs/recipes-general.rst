.. include:: header.rst

.. _RecipesGeneral:

==============================
Recipes: General
==============================


How to Open with :index:`a Wrong File Extension <pair: wrong; file extension>`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
If you have a document with a wrong file extension for its type, you can still correctly open it.

Assume that "some.file" is actually an XPS. Open it like so:

>>> doc = fitz.open("some.file", filetype="xps")

.. note::

    MuPDF itself does not try to determine the file type from the file contents. **You** are responsible for supplying the filetype info in some way -- either implicitly via the file extension, or explicitly as shown. There are pure Python packages like `filetype <https://pypi.org/project/filetype/>`_ that help you doing this. Also consult the :ref:`Document` chapter for a full description.

    If MuPDF encounters a file with an unknown / missing extension, it will try to open it as a PDF. So in these cases there is no need to for additional precautions. Similarly, for memory documents, you can just specify ``doc=fitz.open(stream=mem_area)`` to open it as a PDF document.

----------

How to :index:`Embed or Attach Files <triple: attach;embed;file>`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
PDF supports incorporating arbitrary data. This can be done in one of two ways: "embedding" or "attaching". PyMuPDF supports both options.

1. Attached Files: data are **attached to a page** by way of a *FileAttachment* annotation with this statement: *annot = page.add_file_annot(pos, ...)*, for details see :meth:`Page.add_file_annot`. The first parameter "pos" is the :ref:`Point`, where a "PushPin" icon should be placed on the page.

2. Embedded Files: data are embedded on the **document level** via method :meth:`Document.embfile_add`.

The basic differences between these options are **(1)** you need edit permission to embed a file, but only annotation permission to attach, **(2)** like all annotations, attachments are visible on a page, embedded files are not.

There exist several example scripts: `embedded-list.py <https://github.com/pymupdf/PyMuPDF-Utilities/tree/master/examples/embedded-list.py>`_, `new-annots.py <https://github.com/pymupdf/PyMuPDF-Utilities/tree/master/demo/new-annots.py>`_.

Also look at the sections above and at chapter :ref:`Appendix 3`.

----------

.. index::
   pair: delete;pages
   pair: rearrange;pages

How to Delete and Re-Arrange Pages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
With PyMuPDF you have all options to copy, move, delete or re-arrange the pages of a PDF. Intuitive methods exist that allow you to do this on a page-by-page level, like the :meth:`Document.copy_page` method.

Or you alternatively prepare a complete new page layout in form of a Python sequence, that contains the page numbers you want, in the sequence you want, and as many times as you want each page. The following may illustrate what can be done with :meth:`Document.select`:

*doc.select([1, 1, 1, 5, 4, 9, 9, 9, 0, 2, 2, 2])*

Now let's prepare a PDF for double-sided printing (on a printer not directly supporting this):

The number of pages is given by ``len(doc)`` (equal to ``doc.page_count``). The following lists represent the even and the odd page numbers, respectively:

>>> p_even = [p in range(doc.page_count) if p % 2 == 0]
>>> p_odd  = [p in range(doc.page_count) if p % 2 == 1]

This snippet creates the respective sub documents which can then be used to print the document:

>>> doc.select(p_even)  # only the even pages left over
>>> doc.save("even.pdf")  # save the "even" PDF
>>> doc.close()  # recycle the file
>>> doc = fitz.open(doc.name)  # re-open
>>> doc.select(p_odd)  # and do the same with the odd pages
>>> doc.save("odd.pdf")

For more information also have a look at this Wiki `article <https://github.com/pymupdf/PyMuPDF/wiki/Rearranging-Pages-of-a-PDF>`_.


The following example will reverse the order of all pages (**extremely fast:** sub-second time for the 756 pages of the :ref:`AdobeManual`):

>>> lastPage = doc.page_count - 1
>>> for i in range(lastPage):
        doc.move_page(lastPage, i)  # move current last page to the front

This snippet duplicates the PDF with itself so that it will contain the pages *0, 1, ..., n, 0, 1, ..., n* **(extremely fast and without noticeably increasing the file size!)**:

>>> page_count = len(doc)
>>> for i in range(page_count):
        doc.copy_page(i)  # copy this page to after last page

----------

How to Join PDFs
~~~~~~~~~~~~~~~~~~
It is easy to join PDFs with method :meth:`Document.insert_pdf`. Given open PDF documents, you can copy page ranges from one to the other. You can select the point where the copied pages should be placed, you can revert the page sequence and also change page rotation. This Wiki `article <https://github.com/pymupdf/PyMuPDF/wiki/Inserting-Pages-from-other-PDFs>`_ contains a full description.

The GUI script `PDFjoiner.py <https://github.com/pymupdf/PyMuPDF-Utilities/tree/master/examples/PDFjoiner.py>`_ uses this method to join a list of files while also joining the respective table of contents segments. It looks like this:

.. image:: images/img-pdfjoiner.*
   :scale: 60

----------

How to Add Pages
~~~~~~~~~~~~~~~~~~
There two methods for adding new pages to a PDF: :meth:`Document.insert_page` and :meth:`Document.new_page` (and they share a common code base).

**new_page**

:meth:`Document.new_page` returns the created :ref:`Page` object. Here is the constructor showing defaults::

 >>> doc = fitz.open(...)  # some new or existing PDF document
 >>> page = doc.new_page(to = -1,  # insertion point: end of document
                        width = 595,  # page dimension: A4 portrait
                        height = 842)

The above could also have been achieved with the short form *page = doc.new_page()*. The *to* parameter specifies the document's page number (0-based) **in front of which** to insert.

To create a page in *landscape* format, just exchange the width and height values.

Use this to create the page with another pre-defined paper format:

>>> w, h = fitz.paper_size("letter-l")  # 'Letter' landscape
>>> page = doc.new_page(width = w, height = h)

The convenience function :meth:`paper_size` knows over 40 industry standard paper formats to choose from. To see them, inspect dictionary :attr:`paperSizes`. Pass the desired dictionary key to :meth:`paper_size` to retrieve the paper dimensions. Upper and lower case is supported. If you append "-L" to the format name, the landscape version is returned.

.. note:: Here is a 3-liner that creates a PDF with one empty page. Its file size is 470 bytes:

   >>> doc = fitz.open()
   >>> doc.new_page()
   >>> doc.save("A4.pdf")


**insert_page**

:meth:`Document.insert_page` also inserts a new page and accepts the same parameters *to*, *width* and *height*. But it lets you also insert arbitrary text into the new page and returns the number of inserted lines::

 >>> doc = fitz.open(...)  # some new or existing PDF document
 >>> n = doc.insert_page(to = -1,  # default insertion point
                        text = None,  # string or sequence of strings
                        fontsize = 11,
                        width = 595,
                        height = 842,
                        fontname = "Helvetica",  # default font
                        fontfile = None,  # any font file name
                        color = (0, 0, 0))  # text color (RGB)

The text parameter can be a (sequence of) string (assuming UTF-8 encoding). Insertion will start at :ref:`Point` (50, 72), which is one inch below top of page and 50 points from the left. The number of inserted text lines is returned. See the method definition for more details.

----------

How To Dynamically Clean Up Corrupt PDFs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This shows a potential use of PyMuPDF with another Python PDF library (the excellent pure Python package `pdfrw <https://pypi.python.org/pypi/pdfrw>`_ is used here as an example).

If a clean, non-corrupt / decompressed PDF is needed, one could dynamically invoke PyMuPDF to recover from many problems like so::

 import sys
 from io import BytesIO
 from pdfrw import PdfReader
 import fitz

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
     doc = fitz.open("pdf", ibuffer)
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

How to Split Single Pages
~~~~~~~~~~~~~~~~~~~~~~~~~~

This deals with splitting up pages of a PDF in arbitrary pieces. For example, you may have a PDF with *Letter* format pages which you want to print with a magnification factor of four: each page is split up in 4 pieces which each go to a separate PDF page in *Letter* format again::

    """
    Create a PDF copy with split-up pages (posterize)
    ---------------------------------------------------
    License: GNU AFFERO GPL V3
    (c) 2018 Jorj X. McKie

    Usage
    ------
    python posterize.py input.pdf

    Result
    -------
    A file "poster-input.pdf" with 4 output pages for every input page.

    Notes
    -----
    (1) Output file is chosen to have page dimensions of 1/4 of input.

    (2) Easily adapt the example to make n pages per input, or decide per each
        input page or whatever.

    Dependencies
    ------------
    PyMuPDF 1.12.2 or later
    """
    import fitz, sys
    infile = sys.argv[1]  # input file name
    src = fitz.open(infile)
    doc = fitz.open()  # empty output PDF

    for spage in src:  # for each page in input
        r = spage.rect  # input page rectangle
        d = fitz.Rect(spage.cropbox_position,  # CropBox displacement if not
                      spage.cropbox_position)  # starting at (0, 0)
        #--------------------------------------------------------------------------
        # example: cut input page into 2 x 2 parts
        #--------------------------------------------------------------------------
        r1 = r / 2  # top left rect
        r2 = r1 + (r1.width, 0, r1.width, 0)  # top right rect
        r3 = r1 + (0, r1.height, 0, r1.height)  # bottom left rect
        r4 = fitz.Rect(r1.br, r.br)  # bottom right rect
        rect_list = [r1, r2, r3, r4]  # put them in a list

        for rx in rect_list:  # run thru rect list
            rx += d  # add the CropBox displacement
            page = doc.new_page(-1,  # new output page with rx dimensions
                               width = rx.width,
                               height = rx.height)
            page.show_pdf_page(
                    page.rect,  # fill all new page with the image
                    src,  # input document
                    spage.number,  # input page number
                    clip = rx,  # which part to use of input page
                )

    # that's it, save output file
    doc.save("poster-" + src.name,
             garbage=3,  # eliminate duplicate objects
             deflate=True,  # compress stuff where possible
    )


This shows what happens to an input page:

.. image:: images/img-posterize.png

--------------------------

How to Combine Single Pages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This deals with joining PDF pages to form a new PDF with pages each combining two or four original ones (also called "2-up", "4-up", etc.). This could be used to create booklets or thumbnail-like overviews::

    '''
    Copy an input PDF to output combining every 4 pages
    ---------------------------------------------------
    License: GNU AFFERO GPL V3
    (c) 2018 Jorj X. McKie

    Usage
    ------
    python 4up.py input.pdf

    Result
    -------
    A file "4up-input.pdf" with 1 output page for every 4 input pages.

    Notes
    -----
    (1) Output file is chosen to have A4 portrait pages. Input pages are scaled
        maintaining side proportions. Both can be changed, e.g. based on input
        page size. However, note that not all pages need to have the same size, etc.

    (2) Easily adapt the example to combine just 2 pages (like for a booklet) or
        make the output page dimension dependent on input, or whatever.

    Dependencies
    -------------
    PyMuPDF 1.12.1 or later
    '''
    import fitz, sys
    infile = sys.argv[1]
    src = fitz.open(infile)
    doc = fitz.open()  # empty output PDF

    width, height = fitz.paper_size("a4")  # A4 portrait output page format
    r = fitz.Rect(0, 0, width, height)

    # define the 4 rectangles per page
    r1 = r / 2  # top left rect
    r2 = r1 + (r1.width, 0, r1.width, 0)  # top right
    r3 = r1 + (0, r1.height, 0, r1.height)  # bottom left
    r4 = fitz.Rect(r1.br, r.br)  # bottom right

    # put them in a list
    r_tab = [r1, r2, r3, r4]

    # now copy input pages to output
    for spage in src:
        if spage.number % 4 == 0:  # create new output page
            page = doc.new_page(-1,
                          width = width,
                          height = height)
        # insert input page into the correct rectangle
        page.show_pdf_page(r_tab[spage.number % 4],  # select output rect
                         src,  # input document
                         spage.number)  # input page number

    # by all means, save new file using garbage collection and compression
    doc.save("4up-" + infile, garbage=3, deflate=True)

Example effect:

.. image:: images/img-4up.png


--------------------------

How to Convert Any Document to PDF
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here is a script that converts any PyMuPDF supported document to a PDF. These include XPS, EPUB, FB2, CBZ and all image formats, including multi-page TIFF images.

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
    import fitz
    if not (list(map(int, fitz.VersionBind.split("."))) >= [1,14,0]):
        raise SystemExit("need PyMuPDF v1.14.0+")
    fn = sys.argv[1]

    print("Converting '%s' to '%s.pdf'" % (fn, fn))

    doc = fitz.open(fn)

    b = doc.convert_to_pdf()  # convert to pdf
    pdf = fitz.open("pdf", b)  # open as pdf

    toc= doc.het_toc()  # table of contents of input
    pdf.set_toc(toc)  # simply set it for output
    meta = doc.metadata  # read and set metadata
    if not meta["producer"]:
        meta["producer"] = "PyMuPDF v" + fitz.VersionBind

    if not meta["creator"]:
        meta["creator"] = "PyMuPDF PDF converter"
    meta["modDate"] = fitz.get_pdf_now()
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
            if l["kind"] == fitz.LINK_NAMED:  # we do not handle named links
                print("named link page", pinput.number, l)
                link_skip += 1  # count them
                continue
            pout.insert_link(l)  # simply output the others

    # save the conversion result
    pdf.save(fn + ".pdf", garbage=4, deflate=True)
    # say how many named links we skipped
    if link_cnti > 0:
        print("Skipped %i named links of a total of %i in input." % (link_skip, link_cnti))

--------------------------

How to Deal with Messages Issued by MuPDF
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Since PyMuPDF v1.16.0, **error messages** issued by the underlying MuPDF library are being redirected to the Python standard device *sys.stderr*. So you can handle them like any other output going to this devices.

In addition, these messages go to the internal buffer together with any MuPDF warnings -- see below.

We always prefix these messages with an identifying string *"mupdf:"*.
If you prefer to not see recoverable MuPDF errors at all, issue the command ``fitz.TOOLS.mupdf_display_errors(False)``.

MuPDF warnings continue to be stored in an internal buffer and can be viewed using :meth:`Tools.mupdf_warnings`.

Please note that MuPDF errors may or may not lead to Python exceptions. In other words, you may see error messages from which MuPDF can recover and continue processing.

Example output for a **recoverable error**. We are opening a damaged PDF, but MuPDF is able to repair it and gives us a little information on what happened. Then we illustrate how to find out whether the document can later be saved incrementally. Checking the :attr:`Document.is_dirty` attribute at this point also indicates that during ``fitz.open`` the document had to be repaired:

>>> import fitz
>>> doc = fitz.open("damaged-file.pdf")  # leads to a sys.stderr message:
mupdf: cannot find startxref
>>> print(fitz.TOOLS.mupdf_warnings())  # check if there is more info:
cannot find startxref
trying to repair broken xref
repairing PDF document
object missing 'endobj' token
>>> doc.can_save_incrementally()  # this is to be expected:
False
>>> # the following indicates whether there are updates so far
>>> # this is the case because of the repair actions:
>>> doc.is_dirty
True
>>> # the document has nevertheless been created:
>>> doc
fitz.Document('damaged-file.pdf')
>>> # we now know that any save must occur to a new file

Example output for an **unrecoverable error**:

>>> import fitz
>>> doc = fitz.open("does-not-exist.pdf")
mupdf: cannot open does-not-exist.pdf: No such file or directory
Traceback (most recent call last):
  File "<pyshell#1>", line 1, in <module>
    doc = fitz.open("does-not-exist.pdf")
  File "C:\Users\Jorj\AppData\Local\Programs\Python\Python37\lib\site-packages\fitz\fitz.py", line 2200, in __init__
    _fitz.Document_swiginit(self, _fitz.new_Document(filename, stream, filetype, rect, width, height, fontsize))
RuntimeError: cannot open does-not-exist.pdf: No such file or directory
>>>

--------------------------

How to Deal with PDF Encryption
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Starting with version 1.16.0, PDF decryption and encryption (using passwords) are fully supported. You can do the following:

* Check whether a document is password protected / (still) encrypted (:attr:`Document.needs_pass`, :attr:`Document.is_encrypted`).
* Gain access authorization to a document (:meth:`Document.authenticate`).
* Set encryption details for PDF files using :meth:`Document.save` or :meth:`Document.write` and

    - decrypt or encrypt the content
    - set password(s)
    - set the encryption method
    - set permission details

.. note:: A PDF document may have two different passwords:

   * The **owner password** provides full access rights, including changing passwords, encryption method, or permission detail.
   * The **user password** provides access to document content according to the established permission details. If present, opening the PDF in a viewer will require providing it.

   Method :meth:`Document.authenticate` will automatically establish access rights according to the password used.

The following snippet creates a new PDF and encrypts it with separate user and owner passwords. Permissions are granted to print, copy and annotate, but no changes are allowed to someone authenticating with the user password::

    import fitz

    text = "some secret information"  # keep this data secret
    perm = int(
        fitz.PDF_PERM_ACCESSIBILITY  # always use this
        | fitz.PDF_PERM_PRINT  # permit printing
        | fitz.PDF_PERM_COPY  # permit copying
        | fitz.PDF_PERM_ANNOTATE  # permit annotations
    )
    owner_pass = "owner"  # owner password
    user_pass = "user"  # user password
    encrypt_meth = fitz.PDF_ENCRYPT_AES_256  # strongest algorithm
    doc = fitz.open()  # empty pdf
    page = doc.new_page()  # empty page
    page.insert_text((50, 72), text)  # insert the data
    doc.save(
        "secret.pdf",
        encryption=encrypt_meth,  # set the encryption method
        owner_pw=owner_pass,  # set the owner password
        user_pw=user_pass,  # set the user password
        permissions=perm,  # set permissions
    )

Opening this document with some viewer (Nitro Reader 5) reflects these settings:

.. image:: images/img-encrypting.*
   :scale: 50

**Decrypting** will automatically happen on save as before when no encryption parameters are provided.

To **keep the encryption method** of a PDF save it using *encryption=fitz.PDF_ENCRYPT_KEEP*. If *doc.can_save_incrementally() == True*, an incremental save is also possible.

To **change the encryption method** specify the full range of options above (encryption, owner_pw, user_pw, permissions). An incremental save is **not possible** in this case.

.. include:: footer.rst
