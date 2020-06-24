.. _Document:

================
Document
================

.. highlight:: python

This class represents a document. It can be constructed from a file or from memory.

Since version 1.9.0 there exists the alias *open* for this class.

For addional details on **embedded files** refer to Appendix 3.

======================================= ==========================================================
**Method / Attribute**                  **Short Description**
======================================= ==========================================================
:meth:`Document.authenticate`           gain access to an encrypted document
:meth:`Document.can_save_incrementally` check if incremental save is possible
:meth:`Document.chapterPageCount`       number of pages in chapter
:meth:`Document.close`                  close the document
:meth:`Document.convertToPDF`           write a PDF version to memory
:meth:`Document.copyPage`               PDF only: copy a page reference
:meth:`Document.deletePage`             PDF only: delete a page
:meth:`Document.deletePageRange`        PDF only: delete a page range
:meth:`Document.embeddedFileAdd`        PDF only: add a new embedded file from buffer
:meth:`Document.embeddedFileCount`      PDF only: number of embedded files
:meth:`Document.embeddedFileDel`        PDF only: delete an embedded file entry
:meth:`Document.embeddedFileGet`        PDF only: extract an embedded file buffer
:meth:`Document.embeddedFileInfo`       PDF only: metadata of an embedded file
:meth:`Document.embeddedFileNames`      PDF only: list of embedded files
:meth:`Document.embeddedFileUpd`        PDF only: change an embedded file
:meth:`Document.fullcopyPage`           PDF only: duplicate a page
:meth:`Document.getPageFontList`        PDF only: make a list of fonts on a page
:meth:`Document.getPageImageList`       PDF only: make a list of images on a page
:meth:`Document.getPageXObjectList`     PDF only: make a list of XObjects on a page
:meth:`Document.getPagePixmap`          create a pixmap of a page by page number
:meth:`Document.getPageText`            extract the text of a page by page number
:meth:`Document.getSigFlags`            PDF only: determine signature state
:meth:`Document.getToC`                 create a table of contents
:meth:`Document.insertPage`             PDF only: insert a new page
:meth:`Document.insertPDF`              PDF only: insert pages from another PDF
:meth:`Document.layout`                 re-paginate the document (if supported)
:meth:`Document.loadPage`               read a page
:meth:`Document.metadataXML`            PDF only: :data:`xref` of XML metadata
:meth:`Document.movePage`               PDF only: move a page to another location
:meth:`Document.newPage`                PDF only: insert a new empty page
:meth:`Document.pages`                  iterator over a page range
:meth:`Document.PDFCatalog`             PDF only: :data:`xref` of catalog (root)
:meth:`Document.PDFTrailer`             PDF only: trailer source
:meth:`Document.reload_page`            PDF only: provide a new copy of a page
:meth:`Document.save`                   PDF only: save the document
:meth:`Document.saveIncr`               PDF only: save the document incrementally
:meth:`Document.scrub`                  PDF only: remove sensitive data
:meth:`Document.searchPageFor`          search for a string on a page
:meth:`Document.select`                 PDF only: select a subset of pages
:meth:`Document.setMetadata`            PDF only: set the metadata
:meth:`Document.setToC`                 PDF only: set the table of contents (TOC)
:meth:`Document.updateObject`           PDF only: replace object source
:meth:`Document.nextLocation`           return (chapter, pno) of following page
:meth:`Document.previousLocation`       return (chapter, pno) of preceeding page
:meth:`Document.updateStream`           PDF only: replace stream source
:meth:`Document.write`                  PDF only: writes the document to memory
:meth:`Document.xrefObject`             PDF only: object source at the :data:`xref`
:meth:`Document.xrefStream`             PDF only: stream source at the :data:`xref`
:meth:`Document.xrefStreamRaw`          PDF only: raw stream source at the :data:`xref`
:attr:`Document.chapterCount`           number of chapters
:attr:`Document.FormFonts`              PDF only: list of global widget fonts
:attr:`Document.isClosed`               has document been closed?
:attr:`Document.isEncrypted`            document (still) encrypted?
:attr:`Document.isFormPDF`              is this a Form PDF?
:attr:`Document.isPDF`                  is this a PDF?
:attr:`Document.isReflowable`           is this a reflowable document?
:attr:`Document.lastLocation`           return (chapter, pno) of last page
:attr:`Document.metadata`               metadata
:attr:`Document.name`                   filename of document
:attr:`Document.needsPass`              require password to access data?
:attr:`Document.outline`                first `Outline` item
:attr:`Document.pageCount`              number of pages
:attr:`Document.permissions`            permissions to access the document
======================================= ==========================================================

**Class API**

.. class:: Document

    .. index::
       pair: filename; open
       pair: stream; open
       pair: filetype; open
       pair: rect; open
       pair: width; open
       pair: height; open
       pair: fontsize; open
       pair: open; Document
       pair: filename; Document
       pair: stream; Document
       pair: filetype; Document
       pair: rect; Document
       pair: fontsize; Document

    .. method:: __init__(self, filename=None, stream=None, filetype=None, rect=None, width=0, height=0, fontsize=11)

      Creates a *Document* object.

      * With default parameters, a **new empty PDF** document will be created.
      * If *stream* is given, then the document is created from memory and either *filename* or *filetype* must indicate its type.
      * If *stream* is *None*, then a document is created from the file given by *filename*. Its type is inferred from the extension, which can be overruled by specifying *filetype*.

      :arg str,pathlib filename: A UTF-8 string or *pathlib* object containing a file path (or a file type, see below).

      :arg bytes,bytearray,BytesIO stream: A memory area containing a supported document. Its type **must** be specified by either *filename* or *filetype*.

         *(Changed in version 1.14.13)* *io.BytesIO* is now also supported.

      :arg str filetype: A string specifying the type of document. This may be something looking like a filename (e.g. "x.pdf"), in which case MuPDF uses the extension to determine the type, or a mime type like *application/pdf*. Just using strings like "pdf" will also work.

      :arg rect_like rect: a rectangle specifying the desired page size. This parameter is only meaningful for documents with a variable page layout ("reflowable" documents), like e-books or HTML, and ignored otherwise. If specified, it must be a non-empty, finite rectangle with top-left coordinates (0, 0). Together with parameter *fontsize*, each page will be accordingly laid out and hence also determine the number of pages.

      :arg float width: may used together with *height* as an alternative to *rect* to specify layout information.

      :arg float height: may used together with *width* as an alternative to *rect* to specify layout information.

      :arg float fontsize: the default fontsize for reflowable document types. This parameter is ignored if none of the parameters *rect* or *width* and *height* are specified. Will be used to calculate the page layout.

      Overview of possible forms (using the *open* synonym of *Document*)::

          >>> # from a file
          >>> doc = fitz.open("some.pdf")
          >>> doc = fitz.open("some.file", None, "pdf")  # copes with wrong extension
          >>> doc = fitz.open("some.file", filetype="pdf")  # copes with wrong extension
          >>> 
          >>> # from memory
          >>> doc = fitz.open("pdf", mem_area)
          >>> doc = fitz.open(None, mem_area, "pdf")
          >>> doc = fitz.open(stream=mem_area, filetype="pdf")
          >>> 
          >>> # new empty PDF
          >>> doc = fitz.open()
          >>> 

    .. method:: authenticate(password)

      Decrypts the document with the string *password*. If successful, document data can be accessed. For PDF documents, the "owner" and the "user" have different priviledges, and hence different passwords may exist for these authorization levels. The method will automatically establish the appropriate access rights for the provided password.

      :arg str password: owner or user password.

      :rtype: int
      :returns: a positive value if successful, zero otherwise. If successful, the indicator *isEncrypted* is set to *False*. Positive return codes carry the following information detail:

        * bit 0 set => no password required -- happens if method was used although :meth:`needsPass` was zero.
        * bit 1 set => **user** password authenticated
        * bit 2 set => **owner** password authenticated


    .. method:: chapterPageCount(chapter)

      *(New in v.1.17.0)* Return the number of pages of a chapter.

      :arg int chapter: the 0-based chapter number.

      :rtype: int
      :returns: number of pages in chapter. Relevant only for document types whith chapter support (EPUB currently).


    .. method:: nextLocation(page_id)

      *(New in v.1.17.0)* Return the locator of the following page.

      :arg tuple page_id: the current page id. This must be a tuple *(chapter, pno)* identifying an existing page.

      :returns: The tuple of the following page, i.e. either *(chapter, pno + 1)* or *(chapter + 1, 0)*, **or** the empty tuple *()* if the argument was the last page. Relevant only for document types whith chapter support (EPUB currently).


    .. method:: previousLocation(page_id)

      *(New in v.1.17.0)* Return the locator of the preceeding page.

      :arg tuple page_id: the current page id. This must be a tuple *(chapter, pno)* identifying an existing page.

      :returns: The tuple of the preceeding page, i.e. either *(chapter, pno - 1)* or the last page of the receeding chapter, **or** the empty tuple *()* if the argument was the first page. Relevant only for document types whith chapter support (EPUB currently).


    .. method:: loadPage(page_id=0)

      Create a :ref:`Page` object for further processing (like rendering, text searching, etc.).

      *(Changed in v1.17.0)* For document types supporting a so-called "chapter structure" (like EPUB), pages can also be loaded via the combination of chapter number and relative page number, instead of the absolute page number. This should **significantly speed up access** for large documents.

      :arg int,tuple page_id: *(Changed in v1.17.0)*
      
          Either a 0-based page number, or a tuple *(chapter, pno)*. For an integer, any *-inf < page_id < pageCount* is acceptable. While page_id is negative, :attr:`pageCount` will be added to it. For example: to load the last page, you can use *doc.loadPage(-1)*. After this you have page.number = doc.pageCount - 1.
      
          For a tuple, *chapter* must be in range :attr:`Document.chapterCount`, and *pno* must be in range :meth:`Document.chapterPageCount` of that chapter. Both values are 0-based. With this notation, :attr:`Page.number` will equal the given tuple. Relevant only for document types whith chapter support (EPUB currently).

      :rtype: :ref:`Page`

    .. note::
    
       Documents also follow the Python sequence protocol with page numbers as indices: *doc.loadPage(n) == doc[n]*. Consequently, expressions like *"for page in doc: ..."* and *"for page in reversed(doc): ..."* will successively yield the document's pages. Refer to :meth:`Document.pages` which allows processing pages as with slicing.

       You can also use this notation with the new chapter-based page identification: use *page = doc[(5, 2)]* to load the third page of the sixth chapter.

       For document types not supporting a chapter structure (like PDFs), :attr:`Document.chapterCount` is 1, and pages can alternatively be loaded via tuples *(0, pno)*. See this [#f3]_ footnote for comments on performance improvements.

    .. method:: reload_page(page)

      *(New in version 1.16.10)*
  
      PDF only: Provide a new copy of a page after finishing and updating all pending changes.

      :arg page: page object.
      :type page: :ref:`Page`

      :rtype: :ref:`Page`

      :returns: a new copy of the same page. All pending updates (e.g. to annotations or widgets) will be finalized and a fresh copy of the page will be loaded.
        .. note:: In a typical use case, a page :ref:`Pixmap` should be taken after annotations / widgets have been added or changed. To force all those changes being reflected in the page structure, this method re-instates a fresh copy while keeping the object hierarchy "document -> page -> annotation(s)" intact.


    .. method:: pages(start=None, [stop=None, [step=None]])

      *(New in version 1.16.4)*
      
      A generator for a given range of pages. Parameters have the same meaning as in the built-in function *range()*. Intended for expressions of the form *"for page in doc.pages(start, stop, step): ..."*.

      :arg int start: start iteration with this page number. Default is zero, allowed values are -inf < start < pageCount. While this is negative, :attr:`pageCount` is added **before** starting the iteration.
      :arg int stop: stop iteration at this page number. Default is :attr:`pageCount`, possible are -inf < stop <= pageCount. Larger values are **silently replaced** by the default. Negative values will cyclically emit the pages in reversed order. As with the built-in *range()*, this is the first page **not** returned.
      :arg int step: stepping value. Defaults are 1 if start < stop and -1 if start > stop. Zero is not allowed.

      :returns: a generator iterator over the document's pages. Some examples:

          * "doc.pages()" emits all pages.
          * "doc.pages(4, 9, 2)" emits pages 4, 6, 8.
          * "doc.pages(0, None, 2)" emits all pages with even numbers.
          * "doc.pages(-2)" emits the last two pages.
          * "doc.pages(-1, -1)" emits all pages in reversed order.
          * "doc.pages(-1, -10)" emits pages in reversed order, starting with the last page **repeatedly**. For a 4-page document the following page numbers are emitted: 3, 2, 1, 0, 3, 2, 1, 0, 3, 2, 1, 0, 3.

    .. index::
       pair: from_page; convertToPDF (Document method)
       pair: to_page; convertToPDF (Document method)
       pair: rotate; convertToPDF (Document method)

    .. method:: convertToPDF(from_page=-1, to_page=-1, rotate=0)

      Create a PDF version of the current document and write it to memory. **All document types** (except PDF) are supported. The parameters have the same meaning as in :meth:`insertPDF`. In essence, you can restrict the conversion to a page subset, specify page rotation, and revert page sequence.

      :arg int from_page: first page to copy (0-based). Default is first page.

      :arg int to_page: last page to copy (0-based). Default is last page.

      :arg int rotate: rotation angle. Default is 0 (no rotation). Should be *n * 90* with an integer n (not checked).

      :rtype: bytes
      :returns: a Python *bytes* object containing a PDF file image. It is created by internally using *write(garbage=4, deflate=True)*. See :meth:`write`. You can output it directly to disk or open it as a PDF. Here are some examples::

          >>> # convert an XPS file to PDF
          >>> xps = fitz.open("some.xps")
          >>> pdfbytes = xps.convertToPDF()
          >>>
          >>> # either do this --->
          >>> pdf = fitz.open("pdf", pdfbytes)
          >>> pdf.save("some.pdf")
          >>>
          >>> # or this --->
          >>> pdfout = open("some.pdf", "wb")
          >>> pdfout.write(pdfbytes)
          >>> pdfout.close()

          >>> # copy image files to PDF pages
          >>> # each page will have image dimensions
          >>> doc = fitz.open()                     # new PDF
          >>> imglist = [ ... image file names ...] # e.g. a directory listing
          >>> for img in imglist:
                  imgdoc=fitz.open(img)           # open image as a document
                  pdfbytes=imgdoc.convertToPDF()  # make a 1-page PDF of it
                  imgpdf=fitz.open("pdf", pdfbytes)
                  doc.insertPDF(imgpdf)             # insert the image PDF
          >>> doc.save("allmyimages.pdf")

      .. note:: The method uses the same logic as the *mutool convert* CLI. This works very well in most cases -- however, beware of the following limitations.

        * Image files: perfect, no issues detected. Apparently however, image transparency is ignored. If you need that (like for a watermark), use :meth:`Page.insertImage` instead. Otherwise, this method is recommended for its much better prformance.
        * XPS: appearance very good. Links work fine, outlines (bookmarks) are lost, but can easily be recovered [#f2]_.
        * EPUB, CBZ, FB2: similar to XPS.
        * SVG: medium. Roughly comparable to `svglib <https://github.com/deeplook/svglib>`_.

    .. method:: getToC(simple=True)

      Creates a table of contents out of the document's outline chain.

      :arg bool simple: Indicates whether a simple or a detailed ToC is required. If *simple == False*, each entry of the list also contains a dictionary with :ref:`linkDest` details for each outline entry.

      :rtype: list

      :returns: a list of lists. Each entry has the form *[lvl, title, page, dest]*. Its entries have the following meanings:

        * *lvl* -- hierarchy level (positive *int*). The first entry is always 1. Entries in a row are either **equal**, **increase** by 1, or **decrease** by any number.
        * *title* -- title (*str*)
        * *page* -- 1-based page number (*int*). Page numbers *< 1* either indicate a target outside this document or no target at all (see next entry).
        * *dest* -- (*dict*) included only if *simple=False*. Contains details of the link destination.

    .. method:: getPagePixmap(pno, *args, **kwargs)

      Creates a pixmap from page *pno* (zero-based). Invokes :meth:`Page.getPixmap`.

      :arg int pno: page number, 0-based in -inf < pno < pageCount.

      :rtype: :ref:`Pixmap`

    .. method:: getPageXObjectList(pno)

      PDF only: *(New in v1.16.13)* Return a list of all XObjects referenced by a page.

      :arg int pno: page number, 0-based, *-inf < pno < pageCount*.

      :rtype: list
      :returns: a list of (non-image) XObjects. These objects typically represent pages *embedded* (not copied) from other PDFs. For example, meth:`Page.showPDFpage` will create this type of object. An item of this list has the following layout: **(xref, name, invoker, bbox)**, where

        * **xref** (*int*) is the XObject's :data:`xref`
        * **name** (*str*) is the symbolic name to reference the XObject
        * **invoker** (*int*) the :data:`xref` of the invoking XObject or zero if the page directly invokes it
        * **bbox** (*tuple*) the boundary box of the XObject's location on the page **in untransformed coordinates**. To get actual, non-rotated page coordinates, multiply with the page's transformation matrix :meth:`Page.getTransformation`.


    .. method:: getPageImageList(pno, full=False)

      PDF only: Return a list of all image descriptions referenced by a page.

      :arg int pno: page number, 0-based, *-inf < pno < pageCount*.
      :arg bool full: whether to also include the invoker's :data:`xref` (which is zero if this is the page).

      :rtype: list

      :returns: a list of images shown on this page. Each item looks like
      
      **(xref, smask, width, height, bpc, colorspace, alt. colorspace, name, filter, invoker)**
      
      Where

        * **xref** (*int*) is the image object number
        * **smask** (*int*) is the object number of its soft-mask image
        * **width** and **height** (*ints*) are the image dimensions
        * **bpc** (*int*) denotes the number of bits per component (normally 8)
        * **colorspace** (*str*) a string naming the colorspace (like **DeviceRGB**)
        * **alt. colorspace** (*str*) is any alternate colorspace depending on the value of **colorspace**
        * **name** (*str*) is the symbolic name by which the image is referenced
        * **filter** (*str*) is the decode filter of the image (:ref:`AdobeManual`, pp. 65).
        * **invoker** (*int*) the :data:`xref` of the invoker. Zero if directly referenced by the page. Only present if *full=True*.

      See below how this information can be used to extract PDF images as separate files. Another demonstration::

        >>> doc = fitz.open("pymupdf.pdf")
        >>> doc.getPageImageList(0, full=True)
        [[316, 0, 261, 115, 8, 'DeviceRGB', '', 'Im1', 'DCTDecode', 0]]
        >>> pix = fitz.Pixmap(doc, 316)  # 316 is the xref of the image
        >>> pix
        fitz.Pixmap(DeviceRGB, fitz.IRect(0, 0, 261, 115), 0)

    .. method:: getPageFontList(pno, full=False)

      PDF only: Return a list of all fonts referenced by the page.

      :arg int pno: page number, 0-based, -inf < pno < pageCount.
      :arg bool full: whether to also include the invoker's :data:`xref` (which is zero if directly referenced by the page).

      :rtype: list

      :returns: a list of fonts referenced by this page. Each entry looks like
        
      **(xref, ext, type, basefont, name, encoding, invoker)**,
        
      where

          * **xref** (*int*) is the font object number (may be zero if the PDF uses one of the builtin fonts directly)
          * **ext** (*str*) font file extension (e.g. "ttf", see :ref:`FontExtensions`)
          * **type** (*str*) is the font type (like "Type1" or "TrueType" etc.)
          * **basefont** (*str*) is the base font name,
          * **name** (*str*) is the symbolic name, by which the font is referenced
          * **encoding** (*str*) the font's character encoding if different from its built-in encoding (:ref:`AdobeManual`, p. 414):
          * **invoker** (*int* optional) the :data:`xref` of the invoker. Zero if directly referenced by the page. Only present if *full=True*.

      Example::

          >>> doc = fitz.open("some.pdf")
          >>> for f in doc.getPageFontList(0, full=False): print(f)
          [24, 'ttf', 'TrueType', 'DOKBTG+Calibri', 'R10', '']
          [17, 'ttf', 'TrueType', 'NZNDCL+CourierNewPSMT', 'R14', '']
          [32, 'ttf', 'TrueType', 'FNUUTH+Calibri-Bold', 'R8', '']
          [28, 'ttf', 'TrueType', 'NOHSJV+Calibri-Light', 'R12', '']
          [8, 'ttf', 'Type0', 'ECPLRU+Calibri', 'R23', 'Identity-H']

      .. note:: This list has no duplicate entries: the combination of :data:`xref` and *name* is unique. But by themselves, each of the two may occur multiple times. Duplicate *name* entries indicate the presence of "Form XObjects" on the page, e.g. generated by :meth:`Page.showPDFpage`.

    .. method:: getPageText(pno, output="text")

      Extracts the text of a page given its page number *pno* (zero-based). Invokes :meth:`Page.getText`.

      :arg int pno: page number, 0-based, any value *-inf < pno < pageCount*.

      :arg str output: A string specifying the requested output format: text, html, json or xml. Default is *text*.

      :rtype: str

    .. index::
       pair: fontsize; layout (Document method)
       pair: rect; layout (Document method)
       pair: width; layout (Document method)
       pair: height; layout (Document method)

    .. method:: layout(rect=None, width=0, height=0, fontsize=11)

      Re-paginate ("reflow") the document based on the given page dimension and fontsize. This only affects some document types like e-books and HTML. Ignored if not supported. Supported documents have *True* in property :attr:`isReflowable`.

      :arg rect_like rect: desired page size. Must be finite, not empty and start at point (0, 0).
      :arg float width: use it together with *height* as alternative to *rect*.
      :arg float height: use it together with *width* as alternative to *rect*.
      :arg float fontsize: the desired default fontsize.

    .. method:: select(s)

      PDF only: Keeps only those pages of the document whose numbers occur in the list. Empty sequences or elements outside *range(len(doc))* will cause a *ValueError*. For more details see remarks at the bottom or this chapter.

      :arg sequence s: The sequence (see :ref:`SequenceTypes`) of page numbers (zero-based) to be included. Pages not in the sequence will be deleted (from memory) and become unavailable until the document is reopened. **Page numbers can occur multiple times and in any order:** the resulting document will reflect the sequence exactly as specified.

      .. note::

          * Page numbers in the sequence need not be unique nor be in any particular order. This makes the method a versatile utility to e.g. select only the even or the odd pages or meeting some other criteria and so forth.

          * On a technical level, the method will always create a new :data:`pagetree`.

          * When dealing with only a few pages, methods :meth:`copyPage`, :meth:`movePage`, :meth:`deletePage` are easier to use. In fact, they are also **much faster** -- by at least one order of magnitude when the document has many pages.


    .. method:: setMetadata(m)

      PDF only: Sets or updates the metadata of the document as specified in *m*, a Python dictionary. As with :meth:`select`, these changes become permanent only when you save the document. Incremental save is supported.

      :arg dict m: A dictionary with the same keys as *metadata* (see below). All keys are optional. A PDF's format and encryption method cannot be set or changed and will be ignored. If any value should not contain data, do not specify its key or set the value to *None*. If you use *{}* all metadata information will be cleared to the string *"none"*. If you want to selectively change only some values, modify a copy of *doc.metadata* and use it as the argument. Arbitrary unicode values are possible if specified as UTF-8-encoded.

    .. method:: setToC(toc, collapse=1)

      PDF only: Replaces the **complete current outline** tree (table of contents) with the new one provided as the argument. After successful execution, the new outline tree can be accessed as usual via method *getToC()* or via property *outline*. Like with other output-oriented methods, changes become permanent only via *save()* (incremental save supported). Internally, this method consists of the following two steps. For a demonstration see example below.

      - Step 1 deletes all existing bookmarks.

      - Step 2 creates a new TOC from the entries contained in *toc*.

      :arg sequence toc:

          A Python sequence (list or tuple) with **all bookmark entries** that should form the new table of contents. Output variants of :meth:`getToC` are acceptable. To completely remove the table of contents specify an empty sequence or None. Each item must be a list with the following format.

          * [lvl, title, page [, dest]] where

            - **lvl** is the hierarchy level (int > 0) of the item, which **must be 1** for the first item and at most 1 larger than the previous one.

            - **title** (str) is the title to be displayed. It is assumed to be UTF-8-encoded (relevant for multibyte code points only).

            - **page** (int) is the target page number **(attention: 1-based)**. Must be in valid range if positive. Set it to -1 if there is no target, or the target is external.

            - **dest** (optional) is a dictionary or a number. If a number, it will be interpreted as the desired height (in points) this entry should point to on the page. Use a dictionary (like the one given as output by *getToC(False)*) if you want to store destinations that are either "named", or reside outside this document (other files, internet resources, etc.).

      :arg int collapse: *(new in version 1.16.9)* controls the hierarchy level beyond which outline entries should initially show up collapsed. The default 1 will hence only display level 1, higher levels must be expanded in the PDF viewer. To completely expand specify either a large integer, 0 or None.

      :rtype: int
      :returns: the number of inserted, resp. deleted items.


    .. method:: can_save_incrementally()

      *(New in version 1.16.0)*
      
      Check whether the document can be saved incrementally. Use it to choose the right option without encountering exceptions.

    .. method:: scrub(attached_files=True, clean_pages=True, embedded_files=True, hidden_text=True, javascript=True, metadata=True, redactions=True, remove_links=True, reset_fields=True, reset_responses=True, xml_metadata=True)

      PDF only: *(New in v1.16.14)* Remove potentially sensitive data from the PDF. This function is inspired by the similar "Sanitize" function in Adobe Acrobat products. The process is configurable by a number of options, which are all *True* by default.

      :arg bool attached_files: Search for 'FileAttachment' annotations and remove the file content.
      :arg bool clean_pages: Remove any comments from page painting sources. If this option is set to *False*, then this is also done for *hidden_text* and *redactions*.
      :arg bool embedded_files: Remove embedded files.
      :arg bool hidden_text: Remove OCR-ed text and invisible text.
      :arg bool javascript: Remove JavaScript sources.
      :arg bool metadata: Remove PDF standard metadata.
      :arg bool redactions: Apply redaction annotations.
      :arg bool remove_links: Remove all links.
      :arg bool reset_fields: Reset all form fields to their defaults.
      :arg bool reset_responses: Remove all responses from all annotations.
      :arg bool xml_metadata: Remove XML metadata.


    .. method:: save(outfile, garbage=0, clean=False, deflate=False, incremental=False, ascii=False, expand=0, linear=False, pretty=False, encryption=PDF_ENCRYPT_NONE, permissions=-1, owner_pw=None, user_pw=None)

      PDF only: Saves the document in its **current state**.

      :arg str outfile: The file path to save to. Must be different from the original value if "incremental" is false or zero. When saving incrementally, "garbage" and "linear" **must be** false or zero and this parameter **must equal** the original filename (for convenience use *doc.name*).

      :arg int garbage: Do garbage collection. Positive values exclude "incremental".

       * 0 = none
       * 1 = remove unused objects
       * 2 = in addition to 1, compact the :data:`xref` table
       * 3 = in addition to 2, merge duplicate objects
       * 4 = in addition to 3, check object streams for duplication (may be slow)

      :arg bool clean: Clean and sanitize content streams [#f1]_. Corresponds to "mutool clean -sc".

      :arg bool deflate: Deflate (compress) uncompressed streams.

      :arg bool incremental: Only save changed objects. Excludes "garbage" and "linear". Cannot be used for files that are decrypted or repaired and also in some other cases. To be sure, check :meth:`Document.can_save_incrementally`. If this is false, saving to a new file is required.

      :arg bool ascii: convert binary data to ASCII.

      :arg int expand: Decompress objects. Generates versions that can be better read by some other programs and will lead to larger files.

       * 0 = none
       * 1 = images
       * 2 = fonts
       * 255 = all

      :arg bool linear: Save a linearised version of the document. This option creates a file format for improved performance when read via internet connections. Excludes "incremental".

      :arg bool pretty: Prettify the document source for better readability. PDF objects will be reformatted to look like the default output of :meth:`Document.xrefObject`.

      :arg int permissions: *(new in version 1.16.0)* Set the desired permission levels. See :ref:`PermissionCodes` for possible values. Default is granting all.

      :arg int encryption: *(new in version 1.16.0)* set the desired encryption method. See :ref:`EncryptionMethods` for possible values.

      :arg str owner_pw: *(new in version 1.16.0)* set the document's owner password.

      :arg str user_pw: *(new in version 1.16.0)* set the document's user password.

    .. method:: saveIncr()

      PDF only: saves the document incrementally. This is a convenience abbreviation for *doc.save(doc.name, incremental=True, encryption=PDF_ENCRYPT_KEEP)*.


    .. method:: write(garbage=0, clean=False, deflate=False, ascii=False, expand=0, linear=False, pretty=False, encryption=PDF_ENCRYPT_NONE, permissions=-1, owner_pw=None, user_pw=None)

      PDF only: Writes the **current content of the document** to a bytes object instead of to a file. Obviously, you should be wary about memory requirements. The meanings of the parameters exactly equal those in :meth:`save`. Chater :ref:`FAQ` contains an example for using this method as a pre-processor to `pdfrw <https://pypi.python.org/pypi/pdfrw/0.3>`_.

      *(Changed in version 1.16.0)* for extended encryption support.

      :rtype: bytes
      :returns: a bytes object containing the complete document.

    .. method:: searchPageFor(pno, text, hit_max=16, quads=False)

       Search for "text" on page number "pno". Works exactly like the corresponding :meth:`Page.searchFor`. Any integer -inf < pno < pageCount is acceptable.

    .. index::
       pair: from_page; insertPDF (Document method)
       pair: to_page; insertPDF (Document method)
       pair: start_at; insertPDF (Document method)
       pair: rotate; insertPDF (Document method)
       pair: links; insertPDF (Document method)
       pair: annots; insertPDF (Document method)

    .. method:: insertPDF(docsrc, from_page=-1, to_page=-1, start_at=-1, rotate=-1, links=True, annots=True)

      PDF only: Copy the page range **[from_page, to_page]** (including both) of PDF document *docsrc* into the current one. Inserts will start with page number *start_at*. Negative values can be used to indicate default values. All pages thus copied will be rotated as specified. Links can be excluded in the target, see below. All page numbers are zero-based.

      :arg docsrc: An opened PDF *Document* which must not be the current document object. However, it may refer to the same underlying file.
      :type docsrc: *Document*

      :arg int from_page: First page number in *docsrc*. Default is zero.

      :arg int to_page: Last page number in *docsrc* to copy. Default is the last page.

      :arg int start_at: First copied page will become page number *start_at* in the destination. If omitted, the page range will be appended to current document. If zero, the page range will be inserted before current first page.

      :arg int rotate: All copied pages will be rotated by the provided value (degrees, integer multiple of 90).

      :arg bool links: Choose whether (internal and external) links should be included in the copy. Default is *True*. An **internal link is always excluded**, if its destination is not one of the copied pages.
      :arg bool annots: *(new in version 1.16.1)* choose whether annotations should be included in the copy.
      
    .. note::

       1. If *from_page > to_page*, pages will be **copied in reverse order**. If *0 <= from_page == to_page*, then one page will be copied.

       2. *docsrc* bookmarks **will not be copied**. It is easy however, to recover a table of contents for the resulting document. Look at the examples below and at program `PDFjoiner.py <https://github.com/pymupdf/PyMuPDF-Utilities/tree/master/examples/PDFjoiner.py>`_ in the *examples* directory: it can join PDF documents and at the same time piece together respective parts of the tables of contents.

    .. index::
       pair: width; newPage (Document method)
       pair: height; newPage (Document method)

    .. method:: newPage(pno=-1, width=595, height=842)

      PDF only: Insert an empty page.

      :arg int pno: page number in front of which the new page should be inserted. Must be in *1 < pno <= pageCount*. Special values -1 and *len(doc)* insert **after** the last page.

      :arg float width: page width.
      :arg float height: page height.

      :rtype: :ref:`Page`
      :returns: the created page object.

    .. index::
       pair: fontsize; insertPage (Document method)
       pair: width; insertPage (Document method)
       pair: height; insertPage (Document method)
       pair: fontname; insertPage (Document method)
       pair: fontfile; insertPage (Document method)
       pair: color; insertPage (Document method)

    .. method:: insertPage(pno, text=None, fontsize=11, width=595, height=842, fontname="helv", fontfile=None, color=None)

      PDF only: Insert a new page and insert some text. Convenience function which combines :meth:`Document.newPage` and (parts of) :meth:`Page.insertText`.

      :arg int pno: page number (0-based) **in front of which** to insert. Must be in *range(-1, len(doc) + 1)*. Special values -1 and *len(doc)* insert **after** the last page.

          Changed in version 1.14.12
             This is now a positional parameter

      For the other parameters, please consult the aforementioned methods.

      :rtype: int
      :returns: the result of :meth:`Page.insertText` (number of successfully inserted lines).

    .. method:: deletePage(pno=-1)

      PDF only: Delete a page given by its 0-based number in -inf < pno < pageCount - 1.

      Changed in version 1.14.17

      :arg int pno: the page to be deleted. Negative number count backwards from the end of the document (like with indices). Default is the last page.

    .. method:: deletePageRange(from_page=-1, to_page=-1)

      PDF only: Delete a range of pages given as 0-based numbers. Any *-1* parameter will first be replaced by *len(doc) - 1* (ie. last page number). After that, condition *0 <= from_page <= to_page < len(doc)* must be true. If the parameters are equal, this is equivalent to :meth:`deletePage`.

      *(Changed in version 1.14.17)* Table of contents and internal links are now resynchronized.

      :arg int from_page: the first page to be deleted.

      :arg int to_page: the last page to be deleted.

      .. note::

        In an effort to maintain a valid PDF structure, this method and :meth:`deletePage` will also remove the deleted pages from the table of contents.

        Similarly, it will **scan all pages** of the PDF and remove any links that point to deleted pages. This action may have an extended response time for documents with a lot of pages.

        The **number of deleted pages** has a very small response time effect. Therefore, whenever possible, delete page **ranges** instead of single pages.

        Example: Delete the page range 500 to 520 from a large PDF, using different methods.

        Method 1 - *deletePageRange*::

          import time, fitz
          doc = fitz.open("Adobe PDF Reference 1-7.pdf")
          t0=time.perf_counter();doc.deletePageRange(500, 520);t1=time.perf_counter()
          round(t1 - t0, 2)
          0.66


        Method 2 - *select*, this is more than 10 times **slower**::

          l = list(range(500)) + list(range(521, 1310))
          t0=time.perf_counter();doc.select(l);t1=time.perf_counter()
          round(t1 - t0, 2)
          7.62


    .. method:: copyPage(pno, to=-1)

      PDF only: Copy a page reference within the document.

      :arg int pno: the page to be copied. Must be in range *0 <= pno < len(doc)*.

      :arg int to: the page number in front of which to copy. The default inserts **after** the last page.

      .. note:: Only a new **reference** to the page object will be created -- not a new page object, all copied pages will have identical attribute values, including the :attr:`Page.xref`. This implies that any changes to one of these copies will appear on all of them.

    .. method:: fullcopyPage(pno, to=-1)

      *(New in version 1.14.17)*
      
      PDF only: Make a new copy (duplicate) of a page.

      :arg int pno: the page to be duplicated. Must be in range *0 <= pno < len(doc)*.

      :arg int to: the page number in front of which to copy. The default inserts **after** the last page.

      .. note:: In contrast to :meth:`copyPage`, this method creates a completely identical new page object -- with the exception of :attr:`Page.xref` of course, which will be different. So changes to a copy will only show there.

    .. method:: movePage(pno, to=-1)

      PDF only: Move (copy and then delete original) a page within the document.

      :arg int pno: the page to be moved. Must be in range *0 <= pno < len(doc)*.

      :arg int to: the page number in front of which to insert the moved page. The default moves **after** the last page.

    .. method:: getSigFlags()

      PDF only: Return whether the document contains signature fields. This is an optional PDF property: if not present, no conclusions can be drawn, because the PDF creator may just not have bothered to use it.

      :rtype: int
      :returns:
         * -1: not a Form PDF / no signature fields recorded / no *SigFlags* found.
         * 1: at least one signature field exists.
         * 3:  contains signatures that may be invalidated if the file is saved (written) in a way that alters its previous contents, as opposed to an incremental update.

    .. index::
       pair: filename; embeddedFileAdd (Document method)
       pair: ufilename; embeddedFileAdd (Document method)
       pair: desc; embeddedFileAdd (Document method)

    .. method:: embeddedFileAdd(name, buffer, filename=None, ufilename=None, desc=None)

      PDF only: Embed a new file. All string parameters except the name may be unicode (in previous versions, only ASCII worked correctly). File contents will be compressed (where beneficial).

      Changed in version 1.14.16
         The sequence of positional parameters "name" and "buffer" has been changed to comply with the layout of other functions.

      :arg str name: entry identifier, must not already exist.
      :arg bytes,bytearray,BytesIO buffer: file contents.

         *(Changed in version 1.14.13)* *io.BytesIO* is now also supported.

      :arg str filename: optional filename. Documentation only, will be set to *name* if *None*.
      :arg str ufilename: optional unicode filename. Documentation only, will be set to *filename* if *None*.
      :arg str desc: optional description. Documentation only, will be set to *name* if *None*.


    .. method:: embeddedFileCount()

      PDF only: Return the number of embedded files.

         Changed in version 1.14.16
            This is now a method. In previous versions, this was a property.

    .. method:: embeddedFileGet(item)

      PDF only: Retrieve the content of embedded file by its entry number or name. If the document is not a PDF, or entry cannot be found, an exception is raised.

      :arg int,str item: index or name of entry. An integer must be in *range(embeddedFileCount())*.

      :rtype: bytes

    .. method:: embeddedFileDel(item)

      PDF only: Remove an entry from `/EmbeddedFiles`. As always, physical deletion of the embedded file content (and file space regain) will occur only when the document is saved to a new file with a suitable garbage option.

         Changed in version 1.14.16
            Items can now be deleted by index, too.

      :arg int/str item: index or name of entry.

      .. warning:: When specifying an entry name, this function will only **delete the first item** with that name. Be aware that PDFs not created with PyMuPDF may contain duplicate names. So you may want to take appropriate precautions.

    .. method:: embeddedFileInfo(item)

      PDF only: Retrieve information of an embedded file given by its number or by its name.

      :arg int/str item: index or name of entry. An integer must be in *range(embeddedFileCount())*.

      :rtype: dict
      :returns: a dictionary with the following keys:

          * *name* -- (*str*) name under which this entry is stored
          * *filename* -- (*str*) filename
          * *ufilename* -- (*unicode*) filename
          * *desc* -- (*str*) description
          * *size* -- (*int*) original file size
          * *length* -- (*int*) compressed file length

    .. method:: embeddedFileNames()

      *(New in version 1.14.16)*
      
      PDF only: Return a list of embedded file names. The sequence of names equals the physical sequence in the document.

      :rtype: list

    .. index::
       pair: filename; embeddedFileUpd (Document method)
       pair: ufilename; embeddedFileUpd (Document method)
       pair: desc; embeddedFileUpd (Document method)

    .. method:: embeddedFileUpd(item, buffer=None, filename=None, ufilename=None, desc=None)

      PDF only: Change an embedded file given its entry number or name. All parameters are optional. Letting them default leads to a no-operation.

      :arg int/str item: index or name of entry. An integer must be in *range(0, embeddedFileCount())*.
      :arg bytes,bytearray,BytesIO buffer: the new file content.

         *(Changed in version 1.14.13)* *io.BytesIO* is now also supported.

      :arg str filename: the new filename.
      :arg str ufilename: the new unicode filename.
      :arg str desc: the new description.

    .. method:: embeddedFileSetInfo(n, filename=None, ufilename=None, desc=None)

      PDF only: Change embedded file meta information. All parameters are optional. Letting them default will lead to a no-operation.

      :arg int,str n: index or name of entry. An integer must be in *range(embeddedFileCount())*.
      :arg str filename: sets the filename.
      :arg str ufilename: sets the unicode filename.
      :arg str desc: sets the description.

      .. note:: Deprecated subset of :meth:`embeddedFileUpd`. Will be deleted in a future version.

    .. method:: close()

      Release objects and space allocations associated with the document. If created from a file, also closes *filename* (releasing control to the OS).

    .. method:: xrefObject(xref, compressed=False, ascii=False)

      *(New in version 1.16.8)*
      
      PDF only: Return the definition of a PDF object. For details please refer to :meth:`Document.xrefObject`.
  
    .. method:: PDFCatalog()
      
      *(New in version 1.16.8)*
      
      PDF only: Return the :data:`xref` of the PDF catalog (or root) object. For details please refer to :meth:`Document._getPDFroot`.


    .. method:: PDFTrailer(compressed=False)

      *(New in version 1.16.8)*
      
      PDF only: Return the trailer of the PDF (UTF-8), which is usually located at the PDF file's end. For details please refer to :meth:`Document._getTrailerString`.


    .. method:: metadataXML()

      *(New in version 1.16.8)*
      
      PDF only: Return the :data:`xref` of the document's XML metadata. For details please refer to :meth:`Document._getXmlMetadataXref`.

    .. method:: xrefStream(xref)

      *(New in version 1.16.8)*
      
      PDF only: Return the **decompressed** contents of the :data:`xref` stream object. For details please refer to :meth:`Document._getXrefStream`.

    .. method:: xrefStreamRaw(xref)

      *(New in version 1.16.8)*
      
      PDF only: Return the **unmodified** contents of the :data:`xref` stream object. Otherwise equal to :meth:`Document.xrefStream`.
 
    .. method:: updateObject(xref, obj_str, page=None)

      *(New in version 1.16.8)*
      
      PDF only: Update object at :data:`xref`. For details please refer to :meth:`Document._updateObject`.

    .. method:: updateStream(xref, data, new=False)

      *(New in version 1.16.8)*
      
      PDF only: Repleace the stream at :data`xref`. For details please refer to :meth:`Document._updateStream`.


    .. attribute:: outline

      Contains the first :ref:`Outline` entry of the document (or *None*). Can be used as a starting point to walk through all outline items. Accessing this property for encrypted, not authenticated documents will raise an *AttributeError*.

      :type: :ref:`Outline`

    .. attribute:: isClosed

      *False* if document is still open. If closed, most other attributes and methods will have been deleted / disabled. In addition, :ref:`Page` objects referring to this document (i.e. created with :meth:`Document.loadPage`) and their dependent objects will no longer be usable. For reference purposes, :attr:`Document.name` still exists and will contain the filename of the original document (if applicable).

      :type: bool

    .. attribute:: isPDF

      *True* if this is a PDF document, else *False*.

      :type: bool

    .. attribute:: isFormPDF

      *False* if this is not a PDF or has no form fields, otherwise the number of root form fields (fields with no ancestors).

      Changed in version 1.16.4 Returns the total number of (root) form fields.

      :type: bool,int

    .. attribute:: isReflowable

      *True* if document has a variable page layout (like e-books or HTML). In this case you can set the desired page dimensions during document creation (open) or via method :meth:`layout`.

      :type: bool

    .. attribute:: needsPass

      Indicates whether the document is password-protected against access. This indicator remains unchanged -- **even after the document has been authenticated**. Precludes incremental saves if true.

      :type: bool

    .. attribute:: isEncrypted

      This indicator initially equals *needsPass*. After successful authentication, it is set to *False* to reflect the situation.

      :type: bool

    .. attribute:: permissions

      Contains the permissions to access the document. This is an integer containing bool values in respective bit positions. For example, if *doc.permissions & fitz.PDF_PERM_MODIFY > 0*, you may change the document. See :ref:`PermissionCodes` for details.

      Changed in version 1.16.0 This is now an integer comprised of bit indicators. Was a dictionary previously.

      :type: int

    .. attribute:: metadata

      Contains the document's meta data as a Python dictionary or *None* (if *isEncrypted=True* and *needPass=True*). Keys are *format*, *encryption*, *title*, *author*, *subject*, *keywords*, *creator*, *producer*, *creationDate*, *modDate*. All item values are strings or *None*.

      Except *format* and *encryption*, for PDF documents, the key names correspond in an obvious way to the PDF keys */Creator*, */Producer*, */CreationDate*, */ModDate*, */Title*, */Author*, */Subject*, and */Keywords* respectively.

      - *format* contains the document format (e.g. 'PDF-1.6', 'XPS', 'EPUB').

      - *encryption* either contains *None* (no encryption), or a string naming an encryption method (e.g. *'Standard V4 R4 128-bit RC4'*). Note that an encryption method may be specified **even if** *needsPass=False*. In such cases not all permissions will probably have been granted. Check :attr:`Document.permissions` for details.

      - If the date fields contain valid data (which need not be the case at all!), they are strings in the PDF-specific timestamp format "D:<TS><TZ>", where

          - <TS> is the 12 character ISO timestamp *YYYYMMDDhhmmss* (*YYYY* - year, *MM* - month, *DD* - day, *hh* - hour, *mm* - minute, *ss* - second), and

          - <TZ> is a time zone value (time intervall relative to GMT) containing a sign ('+' or '-'), the hour (*hh*), and the minute (*'mm'*, note the apostrophies!).

      - A Paraguayan value might hence look like *D:20150415131602-04'00'*, which corresponds to the timestamp April 15, 2015, at 1:16:02 pm local time Asuncion.

      :type: dict

    .. Attribute:: name

      Contains the *filename* or *filetype* value with which *Document* was created.

      :type: str

    .. Attribute:: pageCount

      Contains the number of pages of the document. May return 0 for documents with no pages. Function *len(doc)* will also deliver this result.

      :type: int

    .. Attribute:: chapterCount
      
      *(New in version 1.17.0)*
      Contains the number of chapters in the document. Always at least 1. Relevant only for document types with chapter support (EPUB currently). Other documents will return 1.

      :type: int

    .. Attribute:: lastLocation

      *(New in version 1.17.0)*
      Contains (chapter, pno) of the document's last page. Relevant only for document types with chapter support (EPUB currently). Other documents will return *(0, len(doc) - 1)* and *(0, -1)* if it has no pages.

      :type: int

    .. Attribute:: FormFonts

      A list of form field font names defined in the */AcroForm* object. *None* if not a PDF.

      :type: list

.. NOTE:: For methods that change the structure of a PDF (:meth:`insertPDF`, :meth:`select`, :meth:`copyPage`, :meth:`deletePage` and others), be aware that objects or properties in your program may have been invalidated or orphaned. Examples are :ref:`Page` objects and their children (links, annotations, widgets), variables holding old page counts, tables of content and the like. Remember to keep such variables up to date or delete orphaned objects. Also refer to :ref:`ReferenialIntegrity`.

:meth:`setMetadata` Example
-------------------------------
Clear metadata information. If you do this out of privacy / data protection concerns, make sure you save the document as a new file with *garbage > 0*. Only then the old */Info* object will also be physically removed from the file. In this case, you may also want to clear any XML metadata inserted by several PDF editors:

>>> import fitz
>>> doc=fitz.open("pymupdf.pdf")
>>> doc.metadata             # look at what we currently have
{'producer': 'rst2pdf, reportlab', 'format': 'PDF 1.4', 'encryption': None, 'author':
'Jorj X. McKie', 'modDate': "D:20160611145816-04'00'", 'keywords': 'PDF, XPS, EPUB, CBZ',
'title': 'The PyMuPDF Documentation', 'creationDate': "D:20160611145816-04'00'",
'creator': 'sphinx', 'subject': 'PyMuPDF 1.9.1'}
>>> doc.setMetadata({})      # clear all fields
>>> doc.metadata             # look again to show what happened
{'producer': 'none', 'format': 'PDF 1.4', 'encryption': None, 'author': 'none',
'modDate': 'none', 'keywords': 'none', 'title': 'none', 'creationDate': 'none',
'creator': 'none', 'subject': 'none'}
>>> doc._delXmlMetadata()    # clear any XML metadata
>>> doc.save("anonymous.pdf", garbage = 4)       # save anonymized doc

:meth:`setToC` Demonstration
----------------------------------
This shows how to modify or add a table of contents. Also have a look at `csv2toc.py <https://github.com/pymupdf/PyMuPDF-Utilities/tree/master/examples/csv2toc.py>`_ and `toc2csv.py <https://github.com/pymupdf/PyMuPDF-Utilities/tree/master/examples/toc2csv.py>`_ in the examples directory.

>>> import fitz
>>> doc = fitz.open("test.pdf")
>>> toc = doc.getToC()
>>> for t in toc: print(t)                           # show what we have
[1, 'The PyMuPDF Documentation', 1]
[2, 'Introduction', 1]
[3, 'Note on the Name fitz', 1]
[3, 'License', 1]
>>> toc[1][1] += " modified by setToC"               # modify something
>>> doc.setToC(toc)                                  # replace outline tree
3                                                    # number of bookmarks inserted
>>> for t in doc.getToC(): print(t)                  # demonstrate it worked
[1, 'The PyMuPDF Documentation', 1]
[2, 'Introduction modified by setToC', 1]            # <<< this has changed
[3, 'Note on the Name fitz', 1]
[3, 'License', 1]

:meth:`insertPDF` Examples
----------------------------
**(1) Concatenate two documents including their TOCs:**

>>> doc1 = fitz.open("file1.pdf")          # must be a PDF
>>> doc2 = fitz.open("file2.pdf")          # must be a PDF
>>> pages1 = len(doc1)                     # save doc1's page count
>>> toc1 = doc1.getToC(False)     # save TOC 1
>>> toc2 = doc2.getToC(False)     # save TOC 2
>>> doc1.insertPDF(doc2)                   # doc2 at end of doc1
>>> for t in toc2:                         # increase toc2 page numbers
        t[2] += pages1                     # by old len(doc1)
>>> doc1.setToC(toc1 + toc2)               # now result has total TOC

Obviously, similar ways can be found in more general situations. Just make sure that hierarchy levels in a row do not increase by more than one. Inserting dummy bookmarks before and after *toc2* segments would heal such cases. A ready-to-use GUI (wxPython) solution can be found in script `PDFjoiner.py <https://github.com/pymupdf/PyMuPDF-Utilities/tree/master/examples/PDFjoiner.py>`_ of the examples directory.

**(2) More examples:**

>>> # insert 5 pages of doc2, where its page 21 becomes page 15 in doc1
>>> doc1.insertPDF(doc2, from_page=21, to_page=25, start_at=15)

>>> # same example, but pages are rotated and copied in reverse order
>>> doc1.insertPDF(doc2, from_page=25, to_page=21, start_at=15, rotate=90)

>>> # put copied pages in front of doc1
>>> doc1.insertPDF(doc2, from_page=21, to_page=25, start_at=0)

Other Examples
----------------
**Extract all page-referenced images of a PDF into separate PNG files**::

 for i in range(len(doc)):
     imglist = doc.getPageImageList(i)
     for img in imglist:
         xref = img[0]                  # xref number
         pix = fitz.Pixmap(doc, xref)   # make pixmap from image
         if pix.n - pix.alpha < 4:      # can be saved as PNG
             pix.writePNG("p%s-%s.png" % (i, xref))
         else:                          # CMYK: must convert first
             pix0 = fitz.Pixmap(fitz.csRGB, pix)
             pix0.writePNG("p%s-%s.png" % (i, xref))
             pix0 = None                # free Pixmap resources
         pix = None                     # free Pixmap resources

**Rotate all pages of a PDF:**

>>> for page in doc: page.setRotation(90)

.. rubric:: Footnotes

.. [#f1] Content streams describe what (e.g. text or images) appears where and how on a page. PDF uses a specialized mini language similar to PostScript to do this (pp. 985 in :ref:`AdobeManual`), which gets interpreted when a page is loaded.

.. [#f2] However, you **can** use :meth:`Document.getToC` and :meth:`Page.getLinks` (which are available for all document types) and copy this information over to the output PDF. See demo `pdf-converter.py <https://github.com/pymupdf/PyMuPDF-Utilities/tree/master/demo/pdf-converter.py>`_.

.. [#f3] For applicable (layoutable) document types, loading a page via its absolute number may result in layouting a large part of the document, before the page can be accessed. To avoid this, prefer the chapter-based access. Use convenience methods / attributes :meth:`Document.nextLocation`, :meth:`Document.previousLocation` and :attr:`Document.lastLocation` for maintaining a high level of coding efficiency.
