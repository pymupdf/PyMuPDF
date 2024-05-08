.. include:: header.rst

.. _RecipesLowLevelInterfaces:

=========================================
Low-Level Interfaces
=========================================


Numerous methods are available to access and manipulate PDF files on a fairly low level. Admittedly, a clear distinction between "low level" and "normal" functionality is not always possible or subject to personal taste.

It also may happen, that functionality previously deemed low-level is later on assessed as being part of the normal interface. This has happened in v1.14.0 for the class :ref:`Tools` - you now find it as an item in the Classes chapter.

It is a matter of documentation only in which chapter of the documentation you find what you are looking for. Everything is available and always via the same interface.

----------------------------------

How to Iterate through the :data:`xref` Table
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
A PDF's :data:`xref` table is a list of all objects defined in the file. This table may easily contain many thousands of entries -- the manual :ref:`AdobeManual` for example has 127,000 objects. Table entry "0" is reserved and must not be touched.
The following script loops through the :data:`xref` table and prints each object's definition::

    >>> xreflen = doc.xref_length()  # length of objects table
    >>> for xref in range(1, xreflen):  # skip item 0!
            print("")
            print("object %i (stream: %s)" % (xref, doc.xref_is_stream(xref)))
            print(doc.xref_object(xref, compressed=False))


.. highlight:: text

This produces the following output::

    object 1 (stream: False)
    <<
        /ModDate (D:20170314122233-04'00')
        /PXCViewerInfo (PDF-XChange Viewer;2.5.312.1;Feb  9 2015;12:00:06;D:20170314122233-04'00')
    >>

    object 2 (stream: False)
    <<
        /Type /Catalog
        /Pages 3 0 R
    >>

    object 3 (stream: False)
    <<
        /Kids [ 4 0 R 5 0 R ]
        /Type /Pages
        /Count 2
    >>

    object 4 (stream: False)
    <<
        /Type /Page
        /Annots [ 6 0 R ]
        /Parent 3 0 R
        /Contents 7 0 R
        /MediaBox [ 0 0 595 842 ]
        /Resources 8 0 R
    >>
    ...
    object 7 (stream: True)
    <<
        /Length 494
        /Filter /FlateDecode
    >>
    ...

.. highlight:: python

A PDF object definition is an ordinary ASCII string.

----------------------------------

How to Handle Object Streams
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Some object types contain additional data apart from their object definition. Examples are images, fonts, embedded files or commands describing the appearance of a page.

Objects of these types are called "stream objects". PyMuPDF allows reading an object's stream via method :meth:`Document.xref_stream` with the object's :data:`xref` as an argument. It is also possible to write back a modified version of a stream using :meth:`Document.update_stream`.

Assume that the following snippet wants to read all streams of a PDF for whatever reason::

    >>> xreflen = doc.xref_length() # number of objects in file
    >>> for xref in range(1, xreflen): # skip item 0!
            if stream := doc.xref_stream(xref):
                # do something with it (it is a bytes object or None)
                # e.g. just write it back:
                doc.update_stream(xref, stream)

:meth:`Document.xref_stream` automatically returns a stream decompressed as a bytes object -- and :meth:`Document.update_stream` automatically compresses it if beneficial.

----------------------------------

How to Handle Page Contents
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
A PDF page can have zero or multiple :data:`contents` objects. These are stream objects describing **what** appears **where** and **how** on a page (like text and images). They are written in a special mini-language described e.g. in chapter "APPENDIX A - Operator Summary" on page 643 of the :ref:`AdobeManual`.

Every PDF reader application must be able to interpret the contents syntax to reproduce the intended appearance of the page.

If multiple :data:`contents` objects are provided, they must be interpreted in the specified sequence in exactly the same way as if they were provided as a concatenation of the several.

There are good technical arguments for having multiple :data:`contents` objects:

* It is a lot easier and faster to just add new :data:`contents` objects than maintaining a single big one (which entails reading, decompressing, modifying, recompressing, and rewriting it for each change).
* When working with incremental updates, a modified big :data:`contents` object will bloat the update delta and can thus easily negate the efficiency of incremental saves.

For example, PyMuPDF adds new, small :data:`contents` objects in methods :meth:`Page.insert_image`, :meth:`Page.show_pdf_page` and the :ref:`Shape` methods.

However, there are also situations when a **single** :data:`contents` object is beneficial: it is easier to interpret and more compressible than multiple smaller ones.

Here are two ways of combining multiple contents of a page::

    >>> # method 1: use the MuPDF clean function
    >>> page.clean_contents()  # cleans and combines multiple Contents
    >>> xref = page.get_contents()[0]  # only one /Contents now!
    >>> cont = doc.xref_stream(xref)
    >>> # this has also reformatted the PDF commands

    >>> # method 2: extract concatenated contents
    >>> cont = page.read_contents()
    >>> # the /Contents source itself is unmodified

The clean function :meth:`Page.clean_contents` does a lot more than just glueing :data:`contents` objects: it also corrects and optimizes the PDF operator syntax of the page and removes any inconsistencies with the page's object definition.

----------------------------------

How to Access the PDF Catalog
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
This is a central ("root") object of a PDF. It serves as a starting point to reach important other objects and it also contains some global options for the PDF::

    >>> import pymupdf
    >>> doc=pymupdf.open("PyMuPDF.pdf")
    >>> cat = doc.pdf_catalog()  # get xref of the /Catalog
    >>> print(doc.xref_object(cat))  # print object definition
    <<
        /Type/Catalog                 % object type
        /Pages 3593 0 R               % points to page tree
        /OpenAction 225 0 R           % action to perform on open
        /Names 3832 0 R               % points to global names tree
        /PageMode /UseOutlines        % initially show the TOC
        /PageLabels<</Nums[0<</S/D>>2<</S/r>>8<</S/D>>]>> % labels given to pages
        /Outlines 3835 0 R            % points to outline tree
    >>

.. note:: Indentation, line breaks and comments are inserted here for clarification purposes only and will not normally appear. For more information on the PDF catalog see section 7.7.2 on page 71 of the :ref:`AdobeManual`.

----------------------------------

How to Access the PDF File Trailer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The trailer of a PDF file is a :data:`dictionary` located towards the end of the file. It contains special objects, and pointers to important other information. See :ref:`AdobeManual` p. 42. Here is an overview:

======= =========== ===================================================================================
**Key** **Type**    **Value**
======= =========== ===================================================================================
Size    int         Number of entries in the cross-reference table + 1.
Prev    int         Offset to previous :data:`xref` section (indicates incremental updates).
Root    dictionary  (indirect) Pointer to the catalog. See previous section.
Encrypt dictionary  Pointer to encryption object (encrypted files only).
Info    dictionary  (indirect) Pointer to information (metadata).
ID      array       File identifier consisting of two byte strings.
XRefStm int         Offset of a cross-reference stream. See :ref:`AdobeManual` p. 49.
======= =========== ===================================================================================

Access this information via PyMuPDF with :meth:`Document.pdf_trailer` or, equivalently, via :meth:`Document.xref_object` using -1 instead of a valid :data:`xref` number.

    >>> import pymupdf
    >>> doc=pymupdf.open("PyMuPDF.pdf")
    >>> print(doc.xref_object(-1))  # or: print(doc.pdf_trailer())
    <<
    /Type /XRef
    /Index [ 0 8263 ]
    /Size 8263
    /W [ 1 3 1 ]
    /Root 8260 0 R
    /Info 8261 0 R
    /ID [ <4339B9CEE46C2CD28A79EBDDD67CC9B3> <4339B9CEE46C2CD28A79EBDDD67CC9B3> ]
    /Length 19883
    /Filter /FlateDecode
    >>
    >>>

----------------------------------

How to Access XML Metadata
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
A PDF may contain XML metadata in addition to the standard metadata format. In fact, most PDF viewer or modification software adds this type of information when saving the PDF (Adobe, Nitro PDF, PDF-XChange, etc.).

PyMuPDF has no way to **interpret or change** this information directly, because it contains no XML features. XML metadata is however stored as a :data:`stream` object, so it can be read, modified with appropriate software and written back.

    >>> xmlmetadata = doc.get_xml_metadata()
    >>> print(xmlmetadata)
    <?xpacket begin="\ufeff" id="W5M0MpCehiHzreSzNTczkc9d"?>
    <x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="3.1-702">
    <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    ...
    omitted data
    ...
    <?xpacket end="w"?>

Using some XML package, the XML data can be interpreted and / or modified and then stored back. The following also works, if the PDF previously had no XML metadata::

    >>> # write back modified XML metadata:
    >>> doc.set_xml_metadata(xmlmetadata)
    >>>
    >>> # XML metadata can be deleted like this:
    >>> doc.del_xml_metadata()

----------------------------------

How to Extend PDF Metadata
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Attribute :attr:`Document.metadata` is designed so it works for all :ref:`supported document types<Supported_File_Types>` in the same way: it is a Python dictionary with a **fixed set of key-value pairs**. Correspondingly, :meth:`Document.set_metadata` only accepts standard keys.

However, PDFs may contain items not accessible like this. Also, there may be reasons to store additional information, like copyrights. Here is a way to handle **arbitrary metadata items** by using PyMuPDF low-level functions.

As an example, look at this standard metadata output of some PDF::

    # ---------------------
    # standard metadata
    # ---------------------
    pprint(doc.metadata)
    {'author': 'PRINCE',
     'creationDate': "D:2010102417034406'-30'",
     'creator': 'PrimoPDF http://www.primopdf.com/',
     'encryption': None,
     'format': 'PDF 1.4',
     'keywords': '',
     'modDate': "D:20200725062431-04'00'",
     'producer': 'macOS Version 10.15.6 (Build 19G71a) Quartz PDFContext, '
                 'AppendMode 1.1',
     'subject': '',
     'title': 'Full page fax print',
     'trapped': ''}

Use the following code to see **all items** stored in the metadata object::

    # ----------------------------------
    # metadata including private items
    # ----------------------------------
    metadata = {}  # make my own metadata dict
    what, value = doc.xref_get_key(-1, "Info")  # /Info key in the trailer
    if what != "xref":
        pass  # PDF has no metadata
    else:
        xref = int(value.replace("0 R", ""))  # extract the metadata xref
        for key in doc.xref_get_keys(xref):
            metadata[key] = doc.xref_get_key(xref, key)[1]
    pprint(metadata)
    {'Author': 'PRINCE',
     'CreationDate': "D:2010102417034406'-30'",
     'Creator': 'PrimoPDF http://www.primopdf.com/',
     'ModDate': "D:20200725062431-04'00'",
     'PXCViewerInfo': 'PDF-XChange Viewer;2.5.312.1;Feb  9 '
                     "2015;12:00:06;D:20200725062431-04'00'",
     'Producer': 'macOS Version 10.15.6 (Build 19G71a) Quartz PDFContext, '
                 'AppendMode 1.1',
     'Title': 'Full page fax print'}
    # ---------------------------------------------------------------
    # note the additional 'PXCViewerInfo' key - ignored in standard!
    # ---------------------------------------------------------------


*Vice versa*, you can also **store private metadata items** in a PDF. It is your responsibility to make sure that these items conform to PDF specifications - especially they must be (unicode) strings. Consult section 14.3 (p. 548) of the :ref:`AdobeManual` for details and caveats::

    what, value = doc.xref_get_key(-1, "Info")  # /Info key in the trailer
    if what != "xref":
        raise ValueError("PDF has no metadata")
    xref = int(value.replace("0 R", ""))  # extract the metadata xref
    # add some private information
    doc.xref_set_key(xref, "mykey", pymupdf.get_pdf_str("北京 is Beijing"))
    #
    # after executing the previous code snippet, we will see this:
    pprint(metadata)
    {'Author': 'PRINCE',
     'CreationDate': "D:2010102417034406'-30'",
     'Creator': 'PrimoPDF http://www.primopdf.com/',
     'ModDate': "D:20200725062431-04'00'",
     'PXCViewerInfo': 'PDF-XChange Viewer;2.5.312.1;Feb  9 '
                      "2015;12:00:06;D:20200725062431-04'00'",
     'Producer': 'macOS Version 10.15.6 (Build 19G71a) Quartz PDFContext, '
                 'AppendMode 1.1',
     'Title': 'Full page fax print',
     'mykey': '北京 is Beijing'}

To delete selected keys, use `doc.xref_set_key(xref, "mykey", "null")`. As explained in the next section, string "null" is the PDF equivalent to Python's `None`. A key with that value will be treated as not being specified -- and physically removed in garbage collections.

----------------------------------

How to Read and Update PDF Objects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. highlight:: python


There also exist granular, elegant ways to access and manipulate selected PDF :data:`dictionary` keys.

* :meth:`Document.xref_get_keys` returns the PDF keys of the object at :data:`xref`::

    In [1]: import pymupdf
    In [2]: doc = pymupdf.open("pymupdf.pdf")
    In [3]: page = doc[0]
    In [4]: from pprint import pprint
    In [5]: pprint(doc.xref_get_keys(page.xref))
    ('Type', 'Contents', 'Resources', 'MediaBox', 'Parent')

* Compare with the full object definition::

    In [6]: print(doc.xref_object(page.xref))
    <<
      /Type /Page
      /Contents 1297 0 R
      /Resources 1296 0 R
      /MediaBox [ 0 0 612 792 ]
      /Parent 1301 0 R
    >>

* Single keys can also be accessed directly via :meth:`Document.xref_get_key`. The value **always is a string** together with type information, that helps with interpreting it::

    In [7]: doc.xref_get_key(page.xref, "MediaBox")
    Out[7]: ('array', '[0 0 612 792]')

* Here is a full listing of the above page keys::

    In [9]: for key in doc.xref_get_keys(page.xref):
    ...:        print("%s = %s" % (key, doc.xref_get_key(page.xref, key)))
    ...:
    Type = ('name', '/Page')
    Contents = ('xref', '1297 0 R')
    Resources = ('xref', '1296 0 R')
    MediaBox = ('array', '[0 0 612 792]')
    Parent = ('xref', '1301 0 R')

* An undefined key inquiry returns `('null', 'null')` -- PDF object type `null` corresponds to `None` in Python. Similar for the booleans `true` and `false`.
* Let us add a new key to the page definition that sets its rotation to 90 degrees (you are aware that there actually exists :meth:`Page.set_rotation` for this?)::

    In [11]: doc.xref_get_key(page.xref, "Rotate")  # no rotation set:
    Out[11]: ('null', 'null')
    In [12]: doc.xref_set_key(page.xref, "Rotate", "90")  # insert a new key
    In [13]: print(doc.xref_object(page.xref))  # confirm success
    <<
      /Type /Page
      /Contents 1297 0 R
      /Resources 1296 0 R
      /MediaBox [ 0 0 612 792 ]
      /Parent 1301 0 R
      /Rotate 90
    >>

* This method can also be used to remove a key from the :data:`xref` dictionary by setting its value to `null`: The following will remove the rotation specification from the page: `doc.xref_set_key(page.xref, "Rotate", "null")`. Similarly, to remove all links, annotations and fields from a page, use `doc.xref_set_key(page.xref, "Annots", "null")`. Because `Annots` by definition is an array, setting en empty array with the statement `doc.xref_set_key(page.xref, "Annots", "[]")` would do the same job in this case.

* PDF dictionaries can be hierarchically nested. In the following page object definition both, `Font` and `XObject` are subdictionaries of `Resources`::

    In [15]: print(doc.xref_object(page.xref))
    <<
      /Type /Page
      /Contents 1297 0 R
      /Resources <<
        /XObject <<
          /Im1 1291 0 R
        >>
        /Font <<
          /F39 1299 0 R
          /F40 1300 0 R
        >>
      >>
      /MediaBox [ 0 0 612 792 ]
      /Parent 1301 0 R
      /Rotate 90
    >>

* The above situation **is supported** by methods :meth:`Document.xref_set_key` and :meth:`Document.xref_get_key`: use a path-like notation to point at the required key. For example, to retrieve the value of key `Im1` above, specify the complete chain of dictionaries "above" it in the key argument: `"Resources/XObject/Im1"`::

    In [16]: doc.xref_get_key(page.xref, "Resources/XObject/Im1")
    Out[16]: ('xref', '1291 0 R')

* The path notation can also be used to **directly set a value**: use the following to let `Im1` point to a different object::

    In [17]: doc.xref_set_key(page.xref, "Resources/XObject/Im1", "9999 0 R")
    In [18]: print(doc.xref_object(page.xref))  # confirm success:
    <<
      /Type /Page
      /Contents 1297 0 R
      /Resources <<
        /XObject <<
          /Im1 9999 0 R
        >>
        /Font <<
          /F39 1299 0 R
          /F40 1300 0 R
        >>
      >>
      /MediaBox [ 0 0 612 792 ]
      /Parent 1301 0 R
      /Rotate 90
    >>

  Be aware, that **no semantic checks** whatsoever will take place here: if the PDF has no xref 9999, it won't be detected at this point.

* If a key does not exist, it will be created by setting its value. Moreover, if any intermediate keys do not exist either, they will also be created as necessary. The following creates an array `D` several levels below the existing dictionary `A`. Intermediate dictionaries `B` and `C` are automatically created::

    In [5]: print(doc.xref_object(xref))  # some existing PDF object:
    <<
      /A <<
      >>
    >>
    In [6]: # the following will create 'B', 'C' and 'D'
    In [7]: doc.xref_set_key(xref, "A/B/C/D", "[1 2 3 4]")
    In [8]: print(doc.xref_object(xref))  # check out what happened:
    <<
      /A <<
        /B <<
          /C <<
            /D [ 1 2 3 4 ]
          >>
        >>
      >>
    >>

* When setting key values, basic **PDF syntax checking** will be done by MuPDF. For example, new keys can only be created **below a dictionary**. The following tries to create some new string item `E` below the previously created array `D`::

    In [9]: # 'D' is an array, no dictionary!
    In [10]: doc.xref_set_key(xref, "A/B/C/D/E", "(hello)")
    mupdf: not a dict (array)
    --- ... ---
    RuntimeError: not a dict (array)

* It is also **not possible**, to create a key if some higher level key is an **"indirect"** object, i.e. an xref. In other words, xrefs can only be modified directly and not implicitly via other objects referencing them::

    In [13]: # the following object points to an xref
    In [14]: print(doc.xref_object(4))
    <<
      /E 3 0 R
    >>
    In [15]: # 'E' is an indirect object and cannot be modified here!
    In [16]: doc.xref_set_key(4, "E/F", "90")
    mupdf: path to 'F' has indirects
    --- ... ---
    RuntimeError: path to 'F' has indirects

.. caution:: These are expert functions! There are no validations as to whether valid PDF objects, xrefs, etc. are specified. As with other low-level methods there is the risk to render the PDF, or parts of it unusable.

.. include:: footer.rst
