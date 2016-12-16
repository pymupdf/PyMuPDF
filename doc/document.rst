.. _Document:

================
Document
================

This class represents a document. It can be constructed from a file or from memory. See below for details.

Since version 1.9.0 there exists an alias ``open`` for this class.

===================================== ==========================================================
**Method / Attribute**                **Short Description**
===================================== ==========================================================
:meth:`Document.authenticate`         decrypt the document
:meth:`Document.close`                close the document
:meth:`Document.copyPage`             PDF only: copy a page to another location
:meth:`Document.deletePage`           PDF only: delete a page by its number
:meth:`Document.deletePageRange`      PDF only: delete a range of pages
:meth:`Document.getPageFontList`      make a list of fonts on a page
:meth:`Document.getPageImageList`     make a list of images on a page
:meth:`Document.getPagePixmap`        create a pixmap of a page by page number
:meth:`Document.getPageText`          extract the text of a page by page number
:meth:`Document.getToC`               create a table of contents
:meth:`Document.insertPDF`            PDF only: insert a page range from another PDF
:meth:`Document.loadPage`             read a page
:meth:`Document.movePage`             PDF only: move a page to another location
:meth:`Document.save`                 PDF only: save the document
:meth:`Document.saveIncr`             PDF only: save the document incrementally
:meth:`Document.write`                PDF only: writes the document to memory
:meth:`Document.select`               PDF only: select a subset of pages
:meth:`Document.setMetadata`          PDF only: set the metadata
:meth:`Document.setToC`               PDF only: set the table of contents (TOC)
:attr:`Document.isClosed`             has document been closed?
:attr:`Document.isEncrypted`          document still encrypted?
:attr:`Document.metadata`             metadata
:attr:`Document.name`                 filename of document
:attr:`Document.needsPass`            require password to access data?
:attr:`Document.openErrCode`          > 0 if repair occurred during open
:attr:`Document.openErrMsg`           last error message if openErrCode > 0
:attr:`Document.outline`              first `Outline` item
:attr:`Document.pageCount`            number of pages
:attr:`Document.permissions`          show permissions to access the document
===================================== ==========================================================

**Class API**

.. class:: Document

    .. method:: __init__(self, [filename])

      Constructs a ``Document`` object from ``filename``.

      :param `filename`: A string containing the path / name of the document file to be used. The file will be opened and remain open until either explicitely closed (see below) or until end of program. If omitted or ``None``, a new empty **PDF** document will be created.
      :type `filename`: string

      :rtype: ``Document``
      :returns: A ``Document`` object.

    .. method:: __init__(self, filetype, stream)

      Constructs a ``Document`` object from memory ``stream``.

      :param `filetype`: A string specifying the type of document contained in ``stream``. This may be either something that looks like a filename (e.g. ``x.pdf``), in which case MuPDF uses the extension to determine the type, or a mime type like ``application/pdf``. Recommended is using the filename scheme, or even the name of the original file for documentation purposes.
      :type `filetype`: string

      :param `stream`: A memory area representing the content of a supported document type.
      :type `stream`: bytearray, bytes or (Python 2 only) str

      :rtype: ``Document``
      :returns: A ``Document`` object.

    .. method:: authenticate(password)

      Decrypts the document with the string ``password``. If successful, all of the document's data can be accessed (e.g. for rendering).

      :param `password`: The password to be used.
      :type `password`: string

      :rtype: int
      :returns: ``True (1)`` if decryption with ``password`` was successful, ``False (0)`` otherwise. If successfull, indicator ``isEncrypted`` is set to ``False``.

    .. method:: loadPage(number)

      Loads a ``Page`` for further processing like rendering, text searching, etc. See the :ref:`Page` object.

      :param `number`: page number, zero-based (0 is the first page of the document) and ``< doc.pageCount``. If ``number < 0``, then page ``number % pageCount`` will be loaded (IAW ``pageCount`` will be added to ``number`` repeatedly, until the result is no longer negative). For example: in order to load the last page, you can specify ``doc.loadPage(-1)``. After this you have ``page.number == doc.pageCount - 1``.
      :type `number`: int

      :rtype: :ref:`Page`

    .. note:: Conveniently, pages can also be loaded via indexes over the document: ``doc.loadPage(n) == doc[n]``.

    .. method:: getToC(simple = True)

      Creates a table of contents out of the document's outline chain.

      :param `simple`: Indicates whether a detailed ToC is required. If ``simple = False``, each entry of the list also contains a dictionary with :ref:`linkDest` details for each outline entry.

      :type `simple`: boolean

      :rtype: list

      :returns: a list of lists. Each entry has the form ``[lvl, title, page, dest]``. Its entries have the following meanings:

      * lvl - hierarchy level (integer). The first entry has hierarchy level 1, and entries in a row increase by at most one level.
      * title - title (string)
      * page - 1-based page number (integer). Page numbers ``< 1`` either indicate a target outside this document or no target at all (see next entry).
      * dest - included only if ``simple = False`` is specified. A dictionary containing details of the link destination.

    .. method:: getPagePixmap(pno, matrix = fitz.Identity, colorspace = "rgb", clip = None, alpha = False)

      Creates a pixmap from page ``pno`` (zero-based).

      :param `pno`: Page number, zero-based

      :type `pno`: int

      :param `matrix`: A transformation matrix - default is :ref:`Identity`.

      :type `matrix`: Matrix

      :param `colorspace`: A string specifying the requested colorspace - default is ``rgb``.

      :type `colorspace`: string

      :param `clip`: An :ref:`Irect` to restrict rendering of the page to the rectangle's area. If not specified, the complete page will be rendered.

      :type `clip`: :ref:`IRect`

      :param `alpha`: Indicates whether transparency should be included. Leave it as ``False`` if not absolutely required, as it saves memory considerably (25% for RGB).

      :type `alpha`: bool

      :rtype: :ref:`Pixmap`

    .. method:: getPageImageList(pno)

      Returns a nested list of all image descriptions referenced by a page.

      :param `pno`: page number, zero-based.
      :type `pno`: int

      :rtype: list

      :returns: a list of images shown on this page. Each entry looks like ``[xref, gen, width, height, bpc, colorspace, alt. colorspace]``. Where ``xref`` is the image object number, ``gen`` its generation number (should usually be zero), ``width`` and ``height`` are the image dimensions, ``bpc`` denotes the number of bits per component (a typical value is 8), ``colorspace`` a string naming the colorspace (like ``DeviceRGB``), and ``alt. colorspace`` is any alternate colorspace depending on the value of ``colorspace``. See below how this information can be used to extract pages images as separate files. Another demonstration:

       >>> doc = fitz.open("pymupdf.pdf")
       >>> imglist = doc.getPageImageList(85)
       >>> for img in imglist: print img
       [1052, 0, 365, 414, 8, 'DeviceRGB', '']
       >>> pix = fitz.Pixmap(doc, 1052)
       >>> pix
       fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 365, 414), 0)


    .. method:: getPageFontList(pno)

      Returns a nested list of all fonts referenced by a page.

      :param `pno`: page number, zero-based
      :type `pno`: int

      :rtype: list

      :returns: a list of fonts referenced by this page. Each entry looks like ``[xref, gen, type, basefont, name]``. Where ``xref`` is the image object number, ``gen`` its generation number (should usually be zero), ``type`` is the font type (like ``Type1``, ``TrueType``), ``basefont`` is the base font name und ``name`` is the PDF name of this font if given:

       >>> doc = fitz.open("pymupdf.pdf")
       >>> fontlist = doc.getPageFontList(85)
       >>> for font in fontlist: print font
       [100, 0, 'Type1', 'BVGEBM+NimbusSanL-Bold', '']
       [102, 0, 'Type1', 'LMMQFJ+NimbusRomNo9L-Regu', '']

    .. method:: getPageText(pno, output = "text")

      Extracts the text of a page given its page number ``pno`` (zero-based).

      :param `pno`: Page number, zero-based

      :type `pno`: int

      :param `output`: A string specifying the requested output format: text, html, json or xml. Default is ``text``.

      :type `output`: string

      :rtype: String

    .. method:: select(list)

      PDF only: Keeps only those pages of the document whose numbers occur in the list. Empty lists or elements outside the range ``0 <= page < doc.pageCount`` will cause a ``ValueError``. For more details see remarks at the bottom or this chapter.

      :param `list`: A list (or tuple) of page numbers (zero-based) to be included. Pages not in the list will be deleted (from memory) and become unavailable until the document is reopened. **Page numbers can occur multiple times and in any order:** the resulting sub-document will reflect the list exactly as specified.

      :type `list`: list

      :rtype: int
      :returns: Zero upon successful execution. All document information will be updated to reflect the new state of the document, like outlines, number and sequence of pages, etc. Changes become permanent only after saving the document. Incremental save is supported.

    .. method:: setMetadata(m)

      PDF only: Sets or updates the metadata of the document as specified in ``m``, a Python dictionary. As with method ``select()``, these changes become permanent only when you save the document. Incremental save is supported.

      :param `m`: A dictionary with the same keys as ``metadata`` (see below). All keys are optional. A PDF's format and encryption method cannot be set or changed, these keys therefore have no effect and will be ignored. If any value should not contain data, do not specify its key or set the value to ``None``. If you use ``m = {}`` all metadata information will be cleared to ``none``. If you want to selectively change only some values, modify ``doc.metadata`` directly and use it as the argument for this method.

      :type `m`: dict

      :rtype: int
      :returns: Zero upon successful execution and ``doc.metadata`` will be updated.

    .. method:: setToC(toc)

      PDF only: Replaces the **complete current outline** tree (table of contents) with a new one. After successful execution, the new outline tree can be accessed as usual via method ``getToC()`` or via property ``outline``. Like with other output-oriented methods, changes become permanent only via ``save()`` (incremental save supported). Internally, this method consists of the following two steps. For a demonstration see example below.

      - Step 1 deletes all existing bookmarks.

      - Step 2 creates a new TOC from the entries contained in ``toc``.

      :param `toc`:
      :type `toc`: list

      A Python list with **all bookmark entries** that should form the new table of contents. Each entry of this list is again a list with the following format. Output variants of method ``getToC()`` are acceptable as input, too.

      - ``[lvl, title, page, dest]``, where

        - ``lvl`` is the hierarchy level (int > 0) of the item, starting with ``1`` and being at most 1 higher than that of the predecessor,

        - ``title`` (str) is the title to be displayed.

        - ``page`` (int) is the target page number **(attention: 1-based to support getToC()-output)**, must be in valid page range if positive. Set this to ``-1`` if there is no target, or the target is external.

        - ``dest`` (optional) is a dictionary or a number. If a number, it will be interpreted as the desired height (in points) this entry should point to on ``page`` in the current document. Use a dictionary (like the one given as output by ``getToC(simple = False)``) if you want to store destinations that are either "named", or reside outside this documennt (other files, internet resources, etc.).

      :rtype: int
      :returns: ``outline`` and ``getToC()`` will be updated upon successful execution. The return code will either equal the number of inserted items (``len(toc)``) or the number of deleted items if ``toc = []``.

    .. method:: save(outfile, garbage=0, clean=0, deflate=0, incremental=0, ascii=0, expand=0, linear=0)

      PDF only: Saves the **current content of the document** under the name ``outfile`` (include path specifications as necessary). A document may have changed for a number of reasons: e.g. after a successful ``authenticate``, a decrypted copy will be saved, and, in addition (even without optional parameters), some basic cleaning may also have occurred, e.g. broken xref tables have been repaired and earlier incremental changes have been resolved. If you executed any modifying methods like ``select()``, ``setMetadata()``, ``setToC()``, etc., their results will also be reflected in the saved version.

      :param `outfile`: The file name to save to. Must be different from the original value value if ``incremental=False``. When saving incrementally, ``garbage`` and ``linear`` **must be** ``False / 0`` and ``outfile`` **must equal** the original filename (for convenience use ``doc.name``).
      :type `outfile`: string

      :param `garbage`: Do garbage collection: 0 = none, 1 = remove unused objects, 2 = in addition to 1, compact xref table, 3 = in addition to 2, merge duplicate objects, 4 = in addition to 3, check streams for duplication. Excludes ``incremental``.
      :type `garbage`: int

      :param `clean`: Clean content streams: 0 / False, 1 / True.
      :type `clean`: int

      :param `deflate`: Deflate uncompressed streams: 0 / False, 1 / True.
      :type `deflate`: int

      :param `incremental`: Only save changed objects: 0 / False, 1 / True. Excludes ``garbage`` and ``linear``. Cannot be used for decrypted files and for files opened in repair mode (``openErrCode > 0``). In these cases saving to a new file is required.
      :type `incremental`: int

      :param `ascii`: Where possible make the output ASCII: 0 / False, 1 / True.
      :type `ascii`: int

      :param `expand`: Decompress contents: 0 = none, 1 = images, 2 = fonts, 255 = all. This convenience option generates a decompressed file version that can be better read by some other programs.
      :type `expand`: int

      :param `linear`: Save a linearised version of the document: 0 = False, 1 = True. This option creates a file format for improved performance when read via internet connections. Excludes ``incremental``.
      :type `linear`: int

      :rtype: int
      :returns: Zero upon successful execution.

    .. method:: saveIncr()

      PDF only: saves the document incrementally. This is a convenience abbreviation for ``doc.save(doc.name, incremental = True)``.

    .. caution:: A PDF may not be encrypted, but still be password protected against changes - see the ``permissions`` property. Performing incremental saves if ``permissions["edit"] == False`` can lead to unpredictable results. Save to a new file in such a case. We also consider raising an exception under this condition.

    .. method:: write(garbage=0, clean=0, deflate=0, ascii=0, expand=0, linear=0)

      PDF only: Writes the **current content of the document** to a bytearray instead of to a file like ``save()``. Obviously, you should be wary about memory requirements. The meanings of the parameters exactly equal those in :meth:`Document.save`.

      :rtype: bytearray
      :returns: a bytearray containing the complete document data.

    .. method:: insertPDF(doc2, from_page = -1, to_page = -1, start_at = -1, rotate = -1, links = True)

      PDF only: Copies the page range **[from_page, to_page]** (including both) of the PDF document object ``doc2`` into the current PDF. ``from_page`` will start with page number ``start_at``. Negative values can be used to indicate default values. All pages thus copied will be rotated as specified. Links can be excluded in the target, see below. All page numbers are zero-based.

      :param `doc2`: An opened PDF document. The ``doc2`` object **must not be the current document** (not checked) - the results are unpredictable and an exception is probable. It may, however, refer to the **same PDF file** opened as a different ``fitz.Document``. The reason is, that separate documents have their own separate buffer areas and are thus treated as different beasts that just happen to have the same filename.
      :type `doc2`: ``Document``

      :param `from_page`: First page number in ``doc2``. Default is zero.
      :type `from_page`: int

      :param `to_page`: Last page number in ``doc2`` to copy. Default is the last page.
      :type `to_page`: int

      :param `start_at`: First copied page will become page number ``start_at`` in the destination. If omitted, the page range will be appended. If zero, the page range will be inserted before current first page.
      :type `start_at`: int

      :param `rotate`: All copied pages will be rotated by the provided value (degrees). If you do not specify a value (or ``-1``), the original will not be changed. Otherwise it must be an integer multiple of 90 (not checked). Rotation is clockwise if ``rotate`` is positive, else counter-clockwise.
      :type `rotate`: int

      :param `links`: Choose whether (internal and external) links should be included with the copy. Default is ``True``. Only those internal links will be included that point to a member of the copied page range.
      :type `links`: bool

      :rtype: int
      :returns: Zero upon successful execution.

    .. note:: If ``from_page > to_page``, pages will be copied in reverse order. If ``0 <= from_page == to_page``, then one page will be copied.

    .. note:: ``doc2`` bookmarks **will not be copied**. It is easy however, to recover a table of contents for the resulting document. Look at the examples below and at program ``PDFjoiner.py`` in the *examples* directory: it can join PDF documents and at the same time piece together respective parts of the tables of contents.

    .. method:: deletePage(pno)

      PDF only: Deletes a page given by its 0-based number in range ``0 <= pno < pageCount``.

      :param `pno`: the page to be deleted.
      :type `pno`: int

    .. method:: deletePageRange(from_page = -1, to_page = -1)

      PDF only: Deletes a range of pages specified as 0-based numbers. Every negative value will first be replaced by ``pageCount - 1``. After that, condition ``0 <= from_page <= to_page < pageCount`` must be true. If the parameters are equal, one page will be deleted.

      :param `from_page`: the first page to be deleted.
      :type `from_page`: int

      :param `to_page`: the last page to be deleted.
      :type `to_page`: int

    .. method:: copyPage(pno, to = -1)

      PDF only: Copies a page to another location.

      :param `pno`: the page to be copied. Number must be in range ``0 <= pno < pageCount``.
      :type `pno`: int

      :param `to`: the page number in front of which to insert the copied page. To insert at end of document (default), specify a negative value.
      :type `to`: int

    .. method:: movePage(pno, to = -1)

      PDF only: Moves (copies and then deletes) a page to another location.

      :param `pno`: the page to be moved. Number must be in range ``0 <= pno < pageCount``.
      :type `pno`: int

      :param `to`: the page number in front of which to insert the moved page. To insert at end of document (default), specify a negative value. Must not equal (or evaluate to) ``pno`` or ``pno + 1``.
      :type `to`: int

    .. method:: close()

      Releases objects and space allocations associated with the document. If created from a file, also closes ``filename`` (releasing control to the OS).

    .. attribute:: outline

      Contains the first :ref:`Outline` entry of the document (or ``None``). Can be used as a starting point to walk through all outline items. Accessing this property for encrypted, not authenticated documents will raise an ``AttributeError``.

      :rtype: :ref:`Outline`

    .. attribute:: isClosed

      ``False / 0`` if document is still open, ``True / 1`` otherwise. If closed, most other attributes and methods will have been deleted / disabled. In addition, :ref:`Page` objects referring to this document (i.e. created with :meth:`Document.loadPage`) and their dependent objects will no longer be usable. For reference purposes, :attr:`Document.name` still exists and will contain the filename of the original document (if applicable).

      :rtype: int

    .. attribute:: needsPass

      Contains an indicator showing whether the document is encrypted (``True / 1``) or not (``False / 0``). This indicator remains unchanged - even after the document has been authenticated. Precludes incremental saves if set.

      :rtype: bool

    .. attribute:: isEncrypted

      This indicator initially equals ``needsPass``. After successful authentication, it is set to ``False`` to reflect the situation.

      :rtype: bool

    .. attribute:: permissions

      Shows the permissions to access the document. Contains a dictionary likes this:
      ::
       >>> doc.permissions
       {'print': True, 'edit': True, 'note': True, 'copy': True}

      The keys have the obvious meaning of permissions to print, change, annotate and copy the document, respectively.

      :rtype: dict

    .. attribute:: metadata

      Contains the document's meta data as a Python dictionary or ``None`` (if ``isEncrypted = True`` and ``needPass=True``). Keys are ``format``, ``encryption``, ``title``, ``author``, ``subject``, ``keywords``, ``creator``, ``producer``, ``creationDate``, ``modDate``. All item values are strings or ``None``.

      Except ``format`` and ``encryption``, the key names correspond in an obvious way to the PDF keys ``/Creator``, ``/Producer``, ``/CreationDate``, ``/ModDate``, ``/Title``, ``/Author``, ``/Subject``, and ``/Keywords`` respectively.

      - ``format`` contains the PDF version (e.g. 'PDF-1.6').

      - ``encryption`` either contains ``None`` (no encryption), or a string naming an encryption method (e.g. ``'Standard V4 R4 128-bit RC4'``). Note that an encryption method may be specified even if ``needsPass = False``. In such cases not all permissions will probably have been granted. Check dictionary ``getPermits()`` for details.

      - If the date fields contain meaningful data (which need not be the case at all!), they are strings in the PDF-internal timestamp format "D:<TS><TZ>", where

          - <TS> is the 12 character ISO timestamp ``YYYYMMDDhhmmss`` (``YYYY`` - year, ``MM`` - month, ``DD`` - day, ``hh`` - hour, ``mm`` - minute, ``ss`` - second), and

          - <TZ> is a time zone value (time intervall relative to GMT) containing a sign ('+' or '-'), the hour (``hh``), and the minute (``'mm'``, note the apostrophies!).

      - A Paraguayan value might hence look like ``D:20150415131602-04'00'``, which corresponds to the timestamp April 15, 2015, at 1:16:02 pm local time Asuncion.

      :rtype: dict

    .. Attribute:: name

      Contains the ``filename`` or ``filetype`` value with which ``Document`` was created.

      :rtype: string

    .. Attribute:: pageCount

      Contains the number of pages of the document. May return 0 for documents with no pages. Function ``len(doc)`` will also deliver this result.

      :rtype: int

    .. Attribute:: openErrCode

      If ``openErrCode > 0``, errors occurred while opening / parsing the document. In this case incremental save cannot be used.

      :rtype: int

    .. Attribute:: openErrMsg

      Contains either an empty string or the last error message if ``openErrCode > 0``. Together with any other error messages of MuPDF's C library, it will also appear on ``SYSERR``.

      :rtype: string

.. NOTE:: For methods that change the structure of a PDF (``insertPDF()``, ``select()``, ``copyPage()``, ``deletePage()``, ``deletePageRange()`` and others), be aware that objects or properties in your program may have been invalidated or orphaned. Examples are :ref:`Page` objects and their children, variables holding old page counts and the like. Remember to keep such variables up to date or delete (set to ``None``) orphaned objects.


Remarks on ``select()``
------------------------

Page numbers in the list need not be unique nor be in any particular sequence. This makes the method a versatile utility to e.g. select only the even or the odd pages, re-arrange a document from back to front, duplicate it, and so forth. In combination with text extraction you can also omit / include pages with no text or containing a certain text, etc.

You can execute several selections in a row. The document structure will be updated after each method execution.

Any of those changes will become permanent only with a ``doc.save()``. If you have de-selected many pages, consider specifying the ``garbage`` option to eventually reduce the resulting document's size (when saving to a new file).

Also note, that this method **preserves all links, annotations and bookmarks** that are still valid. In other words: deleting pages only deletes references pointing to de-selected pages.

The results of this method can of course also be achieved using combinations of methods ``copyPage()``, ``deletePage()`` and ``movePage()``. While there are cases, when the latter are more practical, ``select()`` is easier and safer to use when many pages are involved.

``select()`` Examples
----------------------------------------

In general, any list of integers within the document's page range can be used. Here are some illustrations.

Create a document copy deleting pages with no text:
::
 import fitz
 doc = fitz.open("any.pdf")
 r = list(range(len(doc)))                  # list of all pages

 for i in range(len(doc)):
     if not doc.getPageText(i):             # contains no text
         r.remove(i)                        # remove page number from list

 doc.select(r)                              # apply the list
 doc.save("out.pdf", garbage = 4)           # save the resulting PDF, OR

 # update the original document ... *** VERY FAST! ***
 doc.saveIncr()


Create a sub document with the odd pages:
::
 import fitz
 doc = fitz.open("any.pdf")
 r = list(range(0, len(doc), 2))
 doc.select(r)                              # apply the list
 doc.save("oddpages.pdf", garbage = 4)      # save sub-PDF of the odd pages


Concatenate a document with itself:
::
 import fitz
 doc = fitz.open("any.pdf")
 r = list(range(len(doc)))
 r += r                                     # turn PDF into a copy of itself
 doc.select(r)
 doc.save("any-any.pdf")                    # contains doubled <any.pdf>

Create document copy in reverse page order (well, don't try with a million pages):
::
 import fitz
 doc = fitz.open("any.pdf")
 r = list(range(len(doc) - 1, -1, -1))
 doc.select(r)
 doc.save("back-to-front.pdf")

``setMetadata()`` Example
----------------------------------------
Clear metadata information. If you do this out of privacy / data protection concerns, make sure you save the document as a new file with ``garbage > 0``. Only then the old ``/Info`` object will also be physically removed from the file:
::
 >>> import fitz
 >>> doc=fitz.open("pymupdf.pdf")
 >>> doc.metadata
 {'producer': 'rst2pdf, reportlab', 'format': 'PDF 1.4', 'encryption': None, 'author':
 'Jorj X. McKie', 'modDate': "D:20160611145816-04'00'", 'keywords': 'PDF, XPS, EPUB, CBZ',
 'title': 'The PyMuPDF Documentation', 'creationDate': "D:20160611145816-04'00'",
 'creator': 'sphinx', 'subject': 'PyMuPDF 1.9.1'}
 >>> doc.setMetadata({})
 0
 >>> doc.metadata
 {'producer': 'none', 'format': 'PDF 1.4', 'encryption': None, 'author': 'none',
 'modDate': 'none', 'keywords': 'none', 'title': 'none', 'creationDate': 'none',
 'creator': 'none', 'subject': 'none'}
 >>> doc.save("anonymous.pdf", garbage = 4)
 0


``setToC()`` Example
----------------------------------
This shows how to modify or add a table of contents:
::
 >>> import fitz
 >>> doc = fitz.open("test.pdf")
 >>> toc = doc.getToC()
 >>> for t in toc: print(t)                           # show what we have
 ...
 [1, 'The PyMuPDF Documentation', 1]
 [2, 'Introduction', 1]
 [3, 'Note on the Name fitz', 1]
 [3, 'License', 1]
 >>> toc[1][1] += " modified by setToC"               # modify something
 >>> doc.setToC(toc)                                  # replace outline tree
 3                                                    # number of bookmarks inserted
 >>> for t in doc.getToC(): print(t)                  # demonstrate it worked
 ...
 [1, 'The PyMuPDF Documentation', 1]
 [2, 'Introduction modified by setToC', 1]            # <<< this has changed
 [3, 'Note on the Name fitz', 1]
 [3, 'License', 1]

``insertPDF()`` Examples
-------------------------
**(1) Concatenate two documents including their TOCs:**
::
 doc1 = fitz.open("file1.pdf")          # must be a PDF
 doc2 = fitz.open("file2.pdf")          # must be a PDF
 pages1 = len(doc1)                     # save doc1's page count
 toc1 = doc1.getToC(simple = False)     # save TOC 1
 toc2 = doc2.getToC(simple = False)     # save TOC 2
 doc1.insertPDF(doc2)                   # doc2 at end of doc1
 for t in toc2:                         # increase toc2 page numbers
     t[2] += pages1                     # by old len(doc1)
 doc1.setToC(toc1 + toc2)               # now result has total TOC

Obviously, similar ways can be found in more general situations. Just watch out that hierarchy levels in a row do not increase by more than one. Inserting dummy bookmarks before and after the ``toc2`` segment would heal such cases.

**(2) More examples:**
::
 # insert 5 pages of doc2, where its page 21 becomes page 15 in doc1
 doc1.insertPDF(doc2, from_page = 21, to_page = 25, start_at = 15)

 # same example, but source pages are rotated and in reverse order
 doc1.insertPDF(doc2, from_page = 25, to_page = 21, start_at = 15, rotate = 90)

 # insert doc2 pages in front of doc1
 doc1.insertPDF(doc2, from_page = 21, to_page = 25, start_at = 0)


Other Examples
----------------
**Extract all page-referenced images of a PDF into separate PNG files:**
::
 for i in range(len(doc)):
     imglist = doc.getPageImageList(i)
     for img in imglist:
         xref = img[0]                  # xref number
         pix = fitz.Pixmap(doc, xref)   # make pixmap from image
         if pix.colorspace != "DeviceCMYK": # can be saved as PNG
             pix.writePNG("p%s-%s.png" % (i, xref))
         else:                          # CMYK: must convert first
             pix0 = fitz.Pixmap(fitz.csRGB, pix)
             pix0.writePNG("p%s-%s.png" % (i, xref))
             pix0 = None                # free Pixmap resources
         pix = None                     # free Pixmap resources

**Rotate all pages of a PDF:**
::
 for i in range(len(doc)):
     doc[i].setRotation(90)

