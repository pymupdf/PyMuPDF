.. _Document:

================
Document
================

.. highlight:: python

This class represents a document. It can be constructed from a file or from memory.

There exists the alias *open* for this class, i.e. ``fitz.Document(...)`` and ``fitz.open(...)`` do exactly the same thing.

For details on **embedded files** refer to Appendix 3.

.. note::

  Starting with v1.17.0, a new page addressing mechanism for **EPUB files only** is supported. This document type is internally organized in chapters such that pages can most efficiently be found by their so-called "location". The location is a tuple *(chapter, pno)* consisting of the chapter number and the page number **in that chapter**. Both numbers are zero-based.

  While it is still possible to locate a page via its (absoute) number, doing so may mean that the complete EPUB document must be layouted before the page can be addressed. This may have a significant performance impact if the document is very large. Using the page's *(chapter, pno)* prevents this from happening.

  To maintain a consistent API, PyMuPDF supports the page *location* syntax for **all file types** -- documents without this feature simply have just one chapter. :meth:`Document.load_page` and the equivalent index access now also support a *location* argument.

  There are a number of methods for converting between page numbers and locations, for determining the chapter count, the page count per chapter, for computing the next and the previous locations, and the last page location of a document.

======================================= ==========================================================
**Method / Attribute**                  **Short Description**
======================================= ==========================================================
:meth:`Document.add_layer_config`       PDF only: make new optional content configuration
:meth:`Document.add_ocg`                PDF only: add new optional content group
:meth:`Document.authenticate`           gain access to an encrypted document
:meth:`Document.can_save_incrementally` check if incremental save is possible
:meth:`Document.chapter_page_count`     number of pages in chapter
:meth:`Document.close`                  close the document
:meth:`Document.convert_to_pdf`         write a PDF version to memory
:meth:`Document.copy_page`              PDF only: copy a page reference
:meth:`Document.del_toc_item`           PDF only: remove a single TOC item
:meth:`Document.delete_page`            PDF only: delete a page
:meth:`Document.delete_pages`           PDF only: delete a page range
:meth:`Document.embfile_add`            PDF only: add a new embedded file from buffer
:meth:`Document.embfile_count`          PDF only: number of embedded files
:meth:`Document.embfile_del`            PDF only: delete an embedded file entry
:meth:`Document.embfile_get`            PDF only: extract an embedded file buffer
:meth:`Document.embfile_info`           PDF only: metadata of an embedded file
:meth:`Document.embfile_names`          PDF only: list of embedded files
:meth:`Document.embfile_upd`            PDF only: change an embedded file
:meth:`Document.find_bookmark`          retrieve page location after layouting
:meth:`Document.fullcopy_page`          PDF only: duplicate a page
:meth:`Document.get_oc_states`          PDF only: lists of OCGs in ON, OFF, RBGroups
:meth:`Document.get_oc`                 PDF only: get OCG /OCMD xref of image / form xobject
:meth:`Document.get_ocgs`               PDF only: info on all optional content groups
:meth:`Document.get_ocmd`               PDF only: retrieve definition of an :data:`OCMD`
:meth:`Document.get_page_fonts`         PDF only: make a list of fonts on a page
:meth:`Document.get_page_images`        PDF only: make a list of images on a page
:meth:`Document.get_page_labels`        PDF only: list of page label definitions
:meth:`Document.get_page_numbers`       PDF only: get page numbers having a given label
:meth:`Document.get_page_xobjects`      PDF only: make a list of XObjects on a page
:meth:`Document.get_toc`                extract the table of contents
:meth:`Document.get_page_pixmap`        create a pixmap of a page by page number
:meth:`Document.get_page_text`          extract the text of a page by page number
:meth:`Document.get_sigflags`           PDF only: determine signature state
:meth:`Document.get_xml_metadata`       PDF only: read the XML metadata
:meth:`Document.has_annots`             PDF only: check if PDF contains any annots
:meth:`Document.has_links`              PDF only: check if PDF contains any links
:meth:`Document.insert_page`            PDF only: insert a new page
:meth:`Document.insert_pdf`             PDF only: insert pages from another PDF
:meth:`Document.layer_configs`          PDF only: list of optional content configurations
:meth:`Document.layer_ui_configs`       PDF only: list of optional content intents
:meth:`Document.layout`                 re-paginate the document (if supported)
:meth:`Document.load_page`              read a page
:meth:`Document.make_bookmark`          create a page pointer in reflowable documents
:meth:`Document.xref_xml_metadata`      PDF only: :data:`xref` of XML metadata
:meth:`Document.move_page`              PDF only: move a page to different location in doc
:meth:`Document.need_appearances`       PDF only: get/set ``/NeedAppearances`` property
:meth:`Document.new_page`               PDF only: insert a new empty page
:meth:`Document.next_location`          return (chapter, pno) of following page
:meth:`Document.outline_xref`           PDF only: :data:`xref` a TOC item
:meth:`Document.page_cropbox`           PDF only: the unrotated page rectangle
:meth:`Document.pages`                  iterator over a page range
:meth:`Document.page_xref`              PDF only: :data:`xref` of a page number
:meth:`Document.pdf_catalog`            PDF only: :data:`xref` of catalog (root)
:meth:`Document.pdf_trailer`            PDF only: trailer source
:meth:`Document.prev_location`          return (chapter, pno) of preceeding page
:meth:`Document.reload_page`            PDF only: provide a new copy of a page
:meth:`Document.save`                   PDF only: save the document
:meth:`Document.saveIncr`               PDF only: save the document incrementally
:meth:`Document.scrub`                  PDF only: remove sensitive data
:meth:`Document.search_page_for`        search for a string on a page
:meth:`Document.select`                 PDF only: select a subset of pages
:meth:`Document.set_layer_ui_config`    PDF only: set OCG visibility temporarily
:meth:`Document.set_metadata`           PDF only: set the metadata
:meth:`Document.set_oc_states`          PDF only: mass changing OCG states
:meth:`Document.set_oc`                 PDF only: attach OCG/OCMD to image / form xobject
:meth:`Document.set_ocmd`               PDF only: create or update an :data:`OCMD`
:meth:`Document.set_page_labels`        PDF only: add/update page label definitions
:meth:`Document.set_toc_item`           PDF only: change a single TOC item
:meth:`Document.set_toc`                PDF only: set the table of contents (TOC)
:meth:`Document.set_xml_metadata`       PDF only: create or update document XML metadata
:meth:`Document.subset_fonts`           PDF only: create font subsets **(experimental)**
:meth:`Document.switch_layer`           PDF only: activate OC configuration
:meth:`Document.tobytes`                PDF only: writes document to memory
:meth:`Document.xref_object`            PDF only: get the definition source of :data:`xref`
:meth:`Document.xref_get_key`           PDF only: get the value of a dictionary key
:meth:`Document.xref_get_keys`          PDF only: list the keys of object at :data:`xref`
:meth:`Document.xref_set_key`           PDF only: set the value of a dictionary key
:meth:`Document.xref_stream_raw`        PDF only: raw stream source at :data:`xref`
:attr:`Document.chapter_count`          number of chapters
:attr:`Document.FormFonts`              PDF only: list of global widget fonts
:attr:`Document.is_closed`              has document been closed?
:attr:`Document.is_dirty`               PDF only: has document been changed yet?
:attr:`Document.is_encrypted`           document (still) encrypted?
:attr:`Document.is_form_pdf`            is this a Form PDF?
:attr:`Document.is_pdf`                 is this a PDF?
:attr:`Document.is_reflowable`          is this a reflowable document?
:attr:`Document.is_repaired`            PDF only: has this PDF been repaired during open?
:attr:`Document.last_location`          (chapter, pno) of last page
:attr:`Document.metadata`               metadata
:attr:`Document.name`                   filename of document
:attr:`Document.needs_pass`             require password to access data?
:attr:`Document.outline`                first `Outline` item
:attr:`Document.page_count`             number of pages
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

      Overview of possible forms (*open* is a synonym of *Document*)::

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

      The Document class can be also be used as a **context manager**. On exit, the document will automatically be closed.

          >>> import fitz
          >>> with fitz.open(...) as doc:
                  for page in doc: print("page %i" % page.number)
          page 0
          page 1
          page 2
          page 3
          >>> doc.is_closed
          True
          >>> 

    .. method:: get_oc(xref)

      *(New in v1.18.4)*

      Return the cross reference number of an :data:`OCG` or :data:`OCMD` attached to an image or form xobject.

      :arg int xref: the :data:`xref` of an image or form xobject. Valid such cross reference numbers are returned by :meth:`Document.get_page_images`, resp. :meth:`Document.get_page_xobjects`. For invalid numbers, an exception is raised.
      :rtype: int
      :returns: the cross reference number of an optional contents object or zero if there is none.

    .. method:: set_oc(xref, ocxref)

      *(New in v1.18.4)*

      If *xref* represents an image or form xobject, set or remove the cross reference number *ocxref* of an optional contents object.

      :arg int xref: the :data:`xref` of an image or form xobject [#f5]_. Valid such cross reference numbers are returned by :meth:`Document.get_page_images`, resp. :meth:`Document.get_page_xobjects`. For invalid numbers, an exception is raised.
      :arg int ocxref: the :data:`xref` number of an :data:`OCG` / :data:`OCMD`. If not zero, an invalid reference raises an exception. If zero, any OC reference is removed.


    .. method:: layer_configs()

      *(New in v1.18.3)*

      Show optional layer configurations. There always is a standard one, which is not included in the response.

        >>> for item in doc.layer_configs: print(item)
        {'number': 0, 'name': 'my-config', 'creator': ''}
        >>> # use 'number' as config identifyer in add_ocg

    .. method:: add_layer_config(name, creator=None, on=None)

      *(New in v1.18.3)*

      Add an optional content configuration. Layers serve as a collection of ON / OFF states for optional content groups. They allow fast visibility switches between different views on the same document.

      :arg str name: arbitrary name.
      :arg str creator: creating software.
      :arg sequ on: a sequence of OCG :data:`xref` numbers which should be set to ON (visible). All other OCGs will be set to OFF.


    .. method:: switch_layer(number, as_default=False)

      *(New in v1.18.3)*

      Switch to a document view as defined by the optional layer's configuration number. This is temporary, except if established as default.

      :arg int number: config number as returned by :meth:`Document.layer_configs`.
      :arg bool as_default: make this the default configuration.

      Activates the ON / OFF states of OCGs as defined in the identified layer. If *as_default=True*, then additionally all layers, including the standard one, are merged and the result is written back to the standard layer, and **all optional layers are deleted**.


    .. method:: add_ocg(name, config=-1, on=True, intent="View", usage="Artwork")

      *(New in v1.18.3)*

      Add an optional content group. An OCG is the most important unit of information to determine object visibility. For a PDF, in order to be regarded as having optional content, at least one OCG must exist.

      :arg str name: arbitrary name. Will show up in supporting PDF viewers.
      :arg int config: layer configuration number. Default -1 is the standard configuration.
      :arg bool on: standard visibility status for objects pointing to this OCG.
      :arg str,list intent: a string or list of strings declaring the visibility intents. There are two PDF standard values to choose from: "View" and "Design". Default is "View". Correct **spelling is important**.
      :arg str usage: another influencer for OCG visibility. This will become part of the OCG's ``/Usage`` key. There are two PDF standard values to choose from: "Artwork" and "Technical". Default is "Artwork". Please only change when required.

      :returns: :data:`xref` of the created OCG. Use as entry for ``oc`` parameter in supporting objects.

      .. note:: Multiple OCGs with identical parameters may be created. This will not cause problems. Garbage option 3 of :meth:`Document.save` will get rid of any duplicates.


    .. method:: set_ocmd(xref=0, ocgs=None, policy="AnyOn", ve=None)

      *(New in v1.18.4)*

      Create or update an :data:`OCMD` (optional content membership dictionary).

      :arg int xref: :data:`xref` of the OCMD to be updated, or 0 for a new OCMD.
      :arg list ocgs: a sequence of :data:`xref` numbers of existing :data:`OCG` PDF objects.
      :arg str policy: one of "AnyOn" (default), "AnyOff", "AllOn", "AllOff" (mixed or lower case).
      :arg list ve: a "visibility expression". This is a list of arbitrarily nested other lists -- see explanation below. Use as an alternative to the combination *ocgs* / *policy* if you need to formulate more complex conditions.
      :rtype: int
      :returns: :data:`xref` of the OCMD. Use as ``oc=xref`` parameter in supporting objects, and respectively in :meth:`Document.set_oc` or :meth:`Annot.set_oc`.

      .. note::

        The purpose of OCMDs is to more flexibly determine visibility. An OCMD actually is a boolean expression: it evaluates the current visibility of one or more optional content groups and then computes its own ON (true) or OFF (false) state.

        There are two ways to formulate the OCMD's visibility:

        1. Use the combination of *ocgs* and *policy*: The *policy* value is interpreted as follows:

          - AnyOn -- (default) true if at least one OCG is ON.
          - AnyOff -- true if at least one OCG is OFF.
          - AllOn -- true if all OCGs are ON.
          - AllOff -- true if all OCGs are OFF.

          Suppose you want two PDF objects be displayed exactly one at a time (if one is ON, then the other one must be OFF):
          
          Solution: use an **OCG** for object 1 and an **OCMD** for object 2. Create the OCMD via ``set_ocmd(ocgs=[xref], policy="AllOff")``, with the :data:`xref` of the OCG.

        2. Use the **visibility expression** *ve*: This is a list of a logical expression keyword (string) followed by integers or other lists. The possible logical expressions are **"and"**, **"or"**, and **"not"**. The integers must be :data:`xref` numbers of OCGs. The syntax of this parameter is a bit awkward, but quite powerful:

          - Each list, including the top one, must start with a logical expression.
          - If the first item is a **"not"**, then the list must have exactly two items. If it is **"and"** or **"or"**, any number of other items may follow.
          - Items following the logical expression may be either integers or other lists. An *integer* must be the xref of an OCG. A *list* must conform to the rules above.

          **Examples:**

          - ``set_ocmd(ve=["or", 4, ["not", 5], ["and", 6, 7]])``. This delivers ON if the following is true: **"4 is ON, or 5 is OFF, or 6 and 7 are both ON"**.
          - ``set_ocmd(ve=["not", xref])``. This has the same effect as the OCMD example created under 1.

          For more details and examples see page 367 of :ref:`AdobeManual`. Also do have a look at example scripts `here <https://github.com/pymupdf/PyMuPDF-Utilities/tree/master/optional-content>`_.

          Visibility expressions, ``/VE``, are part of the PDF version 1.6 specification. If you are using an older PDF consumer software, you hence may find it unsupported (i.e. ignored).


    .. method:: get_ocmd(xref)

      *(New in v1.18.4)*

      Retrieve the definition of an OCMD (optional content membership dictionary).

      :arg int xref: the :data:`xref` of the OCMD.
      :rtype: dict
      :returns: a dictionary with the keys *xref*, *ocgs*, *policy* and *ve*.


    .. method:: get_oc_states(config=-1)

      *(New in v1.18.3)*

      List of optional content groups by status in the specified configuration. This is a dictionary with lists of cross reference numbers for OCGs that occur in the arrays ``/ON``, ``/OFF`` or in some radio button group (``/RBGroups``).

      :arg int config: the configuration layer (default is the standard config layer).

      >>> pprint(doc.get_oc_states())
      {'off': [8, 9, 10], 'on': [5, 6, 7], 'rbgroups': [[7, 10]]}
      >>>

    .. method:: set_oc_states(config, on=None, off=None, basestate=None, rbgroups=None)

      *(New in v1.18.3)*

      Mass status changes of optional content groups. **Permanently** sets the status of OCGs.

      :arg int config: desired configuration layer, choose -1 for the default one.
      :arg list on: list of :data:`xref` of OCGs to set ON. Replaces previous values. An empty list will cause no OCG being set to ON anymore. Should be specified if ``basestate="ON"`` is used.
      :arg list off: list of :data:`xref` of OCGs to set OFF. Replaces previous values. An empty list will cause no OCG being set to OFF anymore. Should be specified if ``basestate="OFF"`` is used.
      :arg str basestate: desired state of OCGs that are not mentioned in *on* resp. *off*. Possible values are "ON", "OFF" or "Unchanged". Upper / lower case possible.
      :arg list rbgroups: a list of lists. Replaces previous values. Each sublist should contain two or more OCG xrefs. OCGs in the same sublist are handled like buttons in a radio button group: setting one to ON automatically sets all other group members to OFF.

      Values *None* will not change the corresponding PDF array.

        >>> doc.set_oc_states(-1, basestate="OFF")  # only changes the base state
        >>> pprint(doc.get_oc_states())
        {'basestate': 'OFF', 'off': [8, 9, 10], 'on': [5, 6, 7], 'rbgroups': [[7, 10]]}


    .. method:: get_ocgs()

      *(New in v1.18.3)*

      Details of all optional content groups. This is a dictionary of dictionaries like this (key is the OCG's :data:`xref`):

        >>> pprint(doc.get_ocgs())
        {13: {'on': True,
              'intent': ['View', 'Design'],
              'name': 'Circle',
              'usage': 'Artwork'},
        14: {'on': True,
              'intent': ['View', 'Design'],
              'name': 'Square',
              'usage': 'Artwork'},
        15: {'on': False, 'intent': ['View'], 'name': 'Square', 'usage': 'Artwork'}}
        >>> 

    .. method:: layer_ui_configs()

      *(New in v1.18.3)*

      Show the visibility status of optional content that is modifyable by the user interface of supporting PDF viewers. Example:

        >>> pprint(doc.layer_ui_configs())
         ({'depth': 0,
          'locked': False,
          'number': 0,
          'on': True,
          'text': 'Circle',
          'type': 'checkbox'},
         {'depth': 0,
          'locked': False,
          'number': 1,
          'on': False,
          'text': 'Square',
          'type': 'checkbox'})
         >>> # refers to OCGs named "Circle" (ON), resp. "Square" (OFF)

       .. note::

          * Only reports items contained in the currently selected layer configuration.

          * The meaning of the dictionary keys is as follows:
             - *depth:* item's nesting level in the `/Order` array 
             - *locked:* whether changing the item's state is prohibited
             - *number:* running sequence number
             - *on:* item state
             - *text:* text string or name field of the originating OCG
             - *type:* one of "label" (set by a text string), "checkbox" (set by a single OCG) or "radiobox" (set by a set of connected OCGs)

    .. method:: set_layer_ui_config(number, action=0)

      *(New in v1.18.3)*

      Modify OC visibility status of content groups. This is analog to what supporting PDF viewers would offer.

      .. note::
        Visibility is **not** a property stored with the OCG. It is not even an information necessarily present in the PDF document at all. Instead, the current visibility is **temporarily** set using the user interface of some supporting PDF consumer software. The same type of functionality is offered by this method.

        To make **permanent** changes, use :meth:`Document.set_oc_states`.

      :arg in number: number as returned by :meth:`Document.layer_ui_configs`.
      :arg int action: 0 = set on (default), 1 = toggle on/off, 2 = set off.

      Example:

          >>> # let's make above "Square" visible:
          >>> doc.set_layer_ui_config(1, action=0)
          >>> pprint(doc.layer_ui_configs())
          ({'depth': 0,
            'locked': False,
            'number': 0,
            'on': True,
            'text': 'Circle',
            'type': 'checkbox'},
          {'depth': 0,
            'locked': False,
            'number': 1,
            'on': True,  # <===
            'text': 'Square',
            'type': 'checkbox'})
          >>> 

    .. method:: authenticate(password)

      Decrypts the document with the string *password*. If successful, document data can be accessed. For PDF documents, the "owner" and the "user" have different priviledges, and hence different passwords may exist for these authorization levels. The method will automatically establish the appropriate access rights for the provided password.

      :arg str password: owner or user password.

      :rtype: int
      :returns: a positive value if successful, zero otherwise. If positive, the indicator :attr:`Document.is_encrypted` is set to *False*. Positive return codes carry the following information detail:

        * bit 0 set => authenticated, but no password required -- happens if method was used although :attr:`needs_pass` was zero.
        * bit 1 set => authenticated with the **user** password.
        * bit 2 set => authenticated with the **owner** password.


    .. method:: get_page_numbers(label, only_one=False)

       *(New in v 1.18.6)*

       PDF only: Return a list of page numbers that have the specified label -- note that labels may not be unique in a PDF. This implies a sequential search through **all page numbers** to compare their labels.
       
       .. note:: Implementation detail -- pages are **not loaded** for this purpose. 

       :arg str label: the label to look for, e.g. "vii" (Roman number 7).
       :arg bool only_one: stop after first hit. Useful e.g. if labelling is known to be unique, there are many pages, etc. The default will check every page number.
       :rtype: list
       :returns: list of page numbers that have this label. Empty if none found, no labels defined, etc.


    .. method:: get_page_labels()

       *(New in v1.18.7)*

       PDF only: Extract the list of page label definitions. Typically used for modifications before feeding it into :meth:`Document.set_page_labels`.

       :returns: a list of dictionaries as defined in :meth:`Document.set_page_labels`.

    .. method:: set_page_labels(labels)

       *(New in v1.18.6)*

       PDF only: Add or update the page label definitions of the PDF.
       
       :arg list labels: a list of dictionaries. Each dictionary defines a label building rule and a 0-based "start" page number. That start page number is the first for which the label definition is valid. Each dictionary has up to 4 items and looks like ``{'startpage': int, 'prefix': str, 'style': str, 'firstpagenum': int}`` and has the following items.

          - ``startpage``: (int) the first page number (0-based) to apply the label rule. This key **must be present**. The rule is applied to all subsequent pages until either end of document or superseded by the rule with the next larger page number.
          - ``prefix``: (str) an arbitrary string to start the label with, e.g. "A-". Default is "".
          - ``style``: (str) the numbering style. Available are "D" (decimal), "r"/"R" (Roman numbers, lower or upper case), and "a"/"A" (lower or upper case alphabetical numbering: "a" through "z", then "aa" through "az", etc.). Default is "". If "", no numbering will take place and the pages in that range will receive the same label consisting of the ``prefix`` value. If prefix is also omitted, then the label will be "".
          - ``firstpagenum``: (int) start numbering with this value. Default is 1, smaller values are ignored.

       For example::
       
        [{'startpage': 6, 'prefix': 'A-', 'style': 'D', 'firstpagenum': 10},
         {'startpage': 10, 'prefix': '', 'style': 'D', 'firstpagenum': 1}]
       
       will generate the labels "A-10", "A-11", "A-12", "A-13", "1", "2", "3", ... for pages 6, 7 and so on until end of document. Pages 0 through 5 will have the label "".


    .. method:: make_bookmark(loc)

      *(New in v.1.17.3)* Return a page pointer in a reflowable document. After re-layouting the document, the result of this method can be used to find the new location of the page.

      .. note:: Do not confuse with items of a table of contents, TOC.

      :arg list,tuple loc: page location. Must be a valid *(chapter, pno)*.

      :rtype: pointer
      :returns: a long integer in pointer format. To be used for finding the new location of the page after re-layouting the document. Do not touch or re-assign.


    .. method:: find_bookmark(bookmark)

      *(New in v.1.17.3)* Return the new page location after re-layouting the document.

      :arg pointer bookmark: created by :meth:`Document.make_bookmark`.

      :rtype: tuple
      :returns: the new (chapter, pno) of the page.


    .. method:: chapter_page_count(chapter)

      *(New in v.1.17.0)* Return the number of pages of a chapter.

      :arg int chapter: the 0-based chapter number.

      :rtype: int
      :returns: number of pages in chapter. Relevant only for document types whith chapter support (EPUB currently).


    .. method:: next_location(page_id)

      *(New in v.1.17.0)* Return the location of the following page.

      :arg tuple page_id: the current page id. This must be a tuple *(chapter, pno)* identifying an existing page.

      :returns: The tuple of the following page, i.e. either *(chapter, pno + 1)* or *(chapter + 1, 0)*, **or** the empty tuple *()* if the argument was the last page. Relevant only for document types whith chapter support (EPUB currently).


    .. method:: prev_location(page_id)

      *(New in v.1.17.0)* Return the locator of the preceeding page.

      :arg tuple page_id: the current page id. This must be a tuple *(chapter, pno)* identifying an existing page.

      :returns: The tuple of the preceeding page, i.e. either *(chapter, pno - 1)* or the last page of the receeding chapter, **or** the empty tuple *()* if the argument was the first page. Relevant only for document types whith chapter support (EPUB currently).


    .. method:: load_page(page_id=0)

      Create a :ref:`Page` object for further processing (like rendering, text searching, etc.).

      *(Changed in v1.17.0)* For document types supporting a so-called "chapter structure" (like EPUB), pages can also be loaded via the combination of chapter number and relative page number, instead of the absolute page number. This should **significantly speed up access** for large documents.

      :arg int,tuple page_id: *(Changed in v1.17.0)*
      
          Either a 0-based page number, or a tuple *(chapter, pno)*. For an **integer**, any *-inf < page_id < page_count* is acceptable. While page_id is negative, :attr:`page_count` will be added to it. For example: to load the last page, you can use *doc.load_page(-1)*. After this you have page.number = doc.page_count - 1.
      
          For a tuple, *chapter* must be in range :attr:`Document.chapter_count`, and *pno* must be in range :meth:`Document.chapter_page_count` of that chapter. Both values are 0-based. Using this notation, :attr:`Page.number` will equal the given tuple. Relevant only for document types whith chapter support (EPUB currently).

      :rtype: :ref:`Page`

    .. note::
    
       Documents also follow the Python sequence protocol with page numbers as indices: *doc.load_page(n) == doc[n]*.
       
       For **absolute page numbers** only, expressions like *"for page in doc: ..."* and *"for page in reversed(doc): ..."* will successively yield the document's pages. Refer to :meth:`Document.pages` which allows processing pages as with slicing.

       You can also use index notation with the new chapter-based page identification: use *page = doc[(5, 2)]* to load the third page of the sixth chapter.

       To maintain a consistent API, for document types not supporting a chapter structure (like PDFs), :attr:`Document.chapter_count` is 1, and pages can also be loaded via tuples *(0, pno)*. See this [#f3]_ footnote for comments on performance improvements.

    .. method:: reload_page(page)

      *(New in version 1.16.10)*
  
      PDF only: Provide a new copy of a page after finishing and updating all pending changes.

      :arg page: page object.
      :type page: :ref:`Page`

      :rtype: :ref:`Page`

      :returns: a new copy of the same page. All pending updates (e.g. to annotations or widgets) will be finalized and a fresh copy of the page will be loaded.
        .. note:: In a typical use case, a page :ref:`Pixmap` should be taken after annotations / widgets have been added or changed. To force all those changes being reflected in the page structure, this method re-instates a fresh copy while keeping the object hierarchy "document -> page -> annotation(s)" intact.


    .. method:: page_cropbox(pno)

      *(New in version 1.17.7)*

      PDF only: Return the unrotated page rectangle -- **without reading the page (via :meth:`Document.load_page`). This is meant for internal purpose requiring best possible performance.

      :arg int pno: 0-based page number.

      :returns: :ref:`Rect` of the page like :meth:`Page.rect`, but ignoring any rotation.
      
    .. method:: page_xref(pno)

      *(New in version 1.17.7)*

      PDF only: Return the :data:`xref` of the page -- **without reading the page (via :meth:`Document.load_page`). This is meant for internal purpose requiring best possible performance.

      :arg int pno: 0-based page number.

      :returns: :data:`xref` of the page like :attr:`Page.xref`.
      
    .. method:: pages(start=None, [stop=None, [step=None]])

      *(New in version 1.16.4)*
      
      A generator for a given range of pages. Parameters have the same meaning as in the built-in function *range()*. Intended for expressions of the form *"for page in doc.pages(start, stop, step): ..."*.

      :arg int start: start iteration with this page number. Default is zero, allowed values are -inf < start < page_count. While this is negative, :attr:`page_count` is added **before** starting the iteration.
      :arg int stop: stop iteration at this page number. Default is :attr:`page_count`, possible are -inf < stop <= page_count. Larger values are **silently replaced** by the default. Negative values will cyclically emit the pages in reversed order. As with the built-in *range()*, this is the first page **not** returned.
      :arg int step: stepping value. Defaults are 1 if start < stop and -1 if start > stop. Zero is not allowed.

      :returns: a generator iterator over the document's pages. Some examples:

          * "doc.pages()" emits all pages.
          * "doc.pages(4, 9, 2)" emits pages 4, 6, 8.
          * "doc.pages(0, None, 2)" emits all pages with even numbers.
          * "doc.pages(-2)" emits the last two pages.
          * "doc.pages(-1, -1)" emits all pages in reversed order.
          * "doc.pages(-1, -10)" emits pages in reversed order, starting with the last page **repeatedly**. For a 4-page document the following page numbers are emitted: 3, 2, 1, 0, 3, 2, 1, 0, 3, 2, 1, 0, 3.

    .. index::
       pair: from_page; convert_to_pdf (Document method)
       pair: to_page; convert_to_pdf (Document method)
       pair: rotate; convert_to_pdf (Document method)

    .. method:: convert_to_pdf(from_page=-1, to_page=-1, rotate=0)

      Create a PDF version of the current document and write it to memory. **All document types** are supported. The parameters have the same meaning as in :meth:`insert_pdf`. In essence, you can restrict the conversion to a page subset, specify page rotation, and revert page sequence.

      :arg int from_page: first page to copy (0-based). Default is first page.

      :arg int to_page: last page to copy (0-based). Default is last page.

      :arg int rotate: rotation angle. Default is 0 (no rotation). Should be *n * 90* with an integer n (not checked).

      :rtype: bytes
      :returns: a Python *bytes* object containing a PDF file image. It is created by internally using ``tobytes(garbage=4, deflate=True)``. See :meth:`tobytes`. You can output it directly to disk or open it as a PDF. Here are some examples::

          >>> # convert an XPS file to PDF
          >>> xps = fitz.open("some.xps")
          >>> pdfbytes = xps.convert_to_pdf()
          >>>
          >>> # either do this --->
          >>> pdf = fitz.open("pdf", pdfbytes)
          >>> pdf.save("some.pdf")
          >>>
          >>> # or this --->
          >>> pdfout = open("some.pdf", "wb")
          >>> pdfout.tobytes(pdfbytes)
          >>> pdfout.close()

          >>> # copy image files to PDF pages
          >>> # each page will have image dimensions
          >>> doc = fitz.open()                     # new PDF
          >>> imglist = [ ... image file names ...] # e.g. a directory listing
          >>> for img in imglist:
                  imgdoc=fitz.open(img)           # open image as a document
                  pdfbytes=imgdoc.convert_to_pdf()  # make a 1-page PDF of it
                  imgpdf=fitz.open("pdf", pdfbytes)
                  doc.insert_pdf(imgpdf)             # insert the image PDF
          >>> doc.save("allmyimages.pdf")

      .. note:: The method uses the same logic as the *mutool convert* CLI. This works very well in most cases -- however, beware of the following limitations.

        * Image files: perfect, no issues detected. Apparently however, image transparency is ignored. If you need that (like for a watermark), use :meth:`Page.insert_image` instead. Otherwise, this method is recommended for its much better prformance.
        * XPS: appearance very good. Links work fine, outlines (bookmarks) are lost, but can easily be recovered [#f2]_.
        * EPUB, CBZ, FB2: similar to XPS.
        * SVG: medium. Roughly comparable to `svglib <https://github.com/deeplook/svglib>`_.

    .. method:: get_toc(simple=True)

      Creates a table of contents (TOC) out of the document's outline chain.

      :arg bool simple: Indicates whether a simple or a detailed TOC is required. If *False*, each item of the list also contains a dictionary with :ref:`linkDest` details for each outline entry.

      :rtype: list

      :returns: a list of lists. Each entry has the form *[lvl, title, page, dest]*. Its entries have the following meanings:

        * *lvl* -- hierarchy level (positive *int*). The first entry is always 1. Entries in a row are either **equal**, **increase** by 1, or **decrease** by any number.
        * *title* -- title (*str*)
        * *page* -- 1-based page number (*int*). If `-1` either no destination or outside document.
        * *dest* -- (*dict*) included only if *simple=False*. Contains details of the TOC item as follows:

          - kind: destination kind, see :ref:`linkDest Kinds`.
          - file: filename if kind is :data:`LINK_GOTOR` or :data:`LINK_LAUNCH`.
          - page: target page, 0-based, :data:`LINK_GOTOR` or :data:`LINK_GOTO` only.
          - to: position on target page (:ref:`Point`).
          - zoom: (float) zoom factor on target page.
          - xref: :data:`xref` of the item (0 if no PDF).
          - color: item color in PDF RGB format ``(red, green, blue)``, or omitted (always omitted if no PDF).
          - bold: true if bold item text or omitted. PDF only.
          - italic: true if italic item text, or omitted. PDF only.
          - collapse: true if sub-items are folded, or omitted. PDF only.


    .. method:: xref_get_keys(xref)

      *(New in v 1.18.7)*

      PDF only: Return the PDF dictionary keys of the object provided by its xref number.

      :arg int xref: the :data:`xref`.

      :returns: a tuple of dictionary keys present in object :data:`xref`. Example:

        >>> from pprint import pprint
        >>> import fitz
        >>> doc=fitz.open("pymupdf.pdf")
        >>> xref = doc.page_xref(0)  # xref of page 0
        >>> pprint(doc.xref_get_keys(xref))
        ('Type', 'Contents', 'Resources', 'MediaBox', 'Parent')
        >>> 


    .. method:: xref_get_key(xref, key)

      *(New in v 1.18.7)*

      PDF only: Return type and value of a PDF dictionary key of an xref.

      :arg int xref: the :data:`xref`.
      :arg str key: the desired PDF key. Must **exactly** match (case-sensitive) one of the keys contained in :meth:`Document.xref_get_keys`.

      :returns: a tuple (type, value), where type is one of "xref", "array", "dict", "int", "float" "null", "bool", "float", "name", "string" or "unknown" (should not occur). Independent of "type", the value of the key is **always** formatted as a string -- see the following example -- and a faithful reflection of what is stored in the PDF. An argument like the return value can be used to modify the value of a key of :data:`xref`.

          >>> for key in doc.xref_get_keys(xref):
                  print(key, "=" , doc.xref_get_key(xref, key))
          Type = ['name', '/Page']
          Contents = ['xref', '1297 0 R']
          Resources = ['xref', '1296 0 R']
          MediaBox = ['array', '[0 0 612 792]']
          Parent = ['xref', '1301 0 R']
          >>>


    .. method:: xref_set_key(xref, key, value)

      *(New in v 1.18.7)*

      PDF only: Set the value of a PDF key in the object given by an xref. This is an expert function: if you do not know what you are doing, there is a high risk to render (parts of) the PDF unusable. Please do consult :ref:`AdobeManual` about object specification formats (page 51) and the structure of special dictionary types like page objects.

      :arg int xref: the :data:`xref`.
      :arg str key: the desired PDF key (without leading "/"). Must not be empty. Any valid PDF key -- whether already present in the object (which will be overwritten) -- or new. It is possible to use PDF path notation like ``"Resources/ExtGState"`` -- which sets the value for key ``"/ExtGState"`` as a sub-object of ``"/Resources"``.
      :arg str value: the value for the key. It must be a non-empty string and, depending on the desired PDF object type, the following rules must be observed -- there is some syntax, but no type checking and no checking of the PDF semantics. Upper or lower case are important!

          * **xref** -- must be provided as ``"nnn 0 R"`` with a valid :data:`xref` number nnn of the PDF. The suffix "``0 R``" is required to be recognizable as a xref.
          * **array** -- a string like ``"[a b c d e f ...]"``. The brackets are required. Array items must be separated by at least one space (not commas like in Python). An empty array ``"[]"`` is possible and equivalent to removing the key. Array items may be any PDF objects, like dictionaries, xrefs, other arrays, etc. Like in Python, array items need not be of the same type.
          * **dict** -- a string like ``"<< ... >>"``. The brackets are required and must enclose a valid PDF dictionary definition. The empty dictionary ``"<<>>"`` is possible and equivalent to removing the key.
          * **int** -- an integer formatted **as a string**.
          * **float** -- a float formatted **as a string**. Scientific notation (with exponents) is not allowed by PDF.
          * **null** -- the string ``"null"``. This is the PDF equivalent to Python's ``None`` and causes the key to be ignored -- however not necessarily removed.
          * **bool** -- one of the strings ``"true"`` or ``"false"``.
          * **name** -- a valid PDF name with a leading slash: ``"/PageLayout"``.
          * **string** -- a valid PDF string. Denote the empty string as ``"()"``. Depending on its content, it must be enclosed in bracket types "(...)" or "<...>", and reserved PDF characters must be escaped. If in doubt, we **strongly recommend** to use :meth:`getPDFstr`! This function automatically determines the required format. E.g. it will do conversions like ``fitz.getPDFstr("Pay in $ or €.") = "<feff00500061007900200069006e002000240020006f0072002020ac002e>"``, or ``fitz.getPDFstr("Prices in USD (EUR accepted).") = "(Prices in USD \(EUR accepted\).)"``.


    .. method:: get_page_pixmap(pno, *args, **kwargs)

      Creates a pixmap from page *pno* (zero-based). Invokes :meth:`Page.get_pixmap`.

      :arg int pno: page number, 0-based in -inf < pno < page_count.

      :rtype: :ref:`Pixmap`

    .. method:: get_page_xobjects(pno)

      PDF only: *(New in v1.16.13)* Return a list of all XObjects referenced by a page.

      :arg int pno: page number, 0-based, *-inf < pno < page_count*.

      :rtype: list
      :returns: a list of (non-image) XObjects. These objects typically represent pages *embedded* (not copied) from other PDFs. For example, :meth:`Page.show_pdf_page` will create this type of object. An item of this list has the following layout: **(xref, name, invoker, bbox)**, where

        * **xref** (*int*) is the XObject's :data:`xref`
        * **name** (*str*) is the symbolic name to reference the XObject
        * **invoker** (*int*) the :data:`xref` of the invoking XObject or zero if the page directly invokes it
        * **bbox** (*tuple*) the boundary box of the XObject's location on the page **in untransformed coordinates**. To get actual, non-rotated page coordinates, multiply with the page's transformation matrix :attr:`Page.transformation_matrix`.


    .. method:: get_page_images(pno, full=False)

      PDF only: Return a list of all images (directly or indirectly) referenced by the page.

      :arg int pno: page number, 0-based, *-inf < pno < page_count*.
      :arg bool full: whether to also include the referencer's :data:`xref` (which is zero if this is the page).

      :rtype: list

      :returns: a list of images shown on this page. Each item looks like
      
      **(xref, smask, width, height, bpc, colorspace, alt. colorspace, name, filter, referencer)**
      
      Where

        * **xref** (*int*) is the image object number
        * **smask** (*int*) is the object number of its soft-mask image
        * **width** and **height** (*ints*) are the image dimensions
        * **bpc** (*int*) denotes the number of bits per component (normally 8)
        * **colorspace** (*str*) a string naming the colorspace (like **DeviceRGB**)
        * **alt. colorspace** (*str*) is any alternate colorspace depending on the value of **colorspace**
        * **name** (*str*) is the symbolic name by which the image is referenced
        * **filter** (*str*) is the decode filter of the image (:ref:`AdobeManual`, pp. 65).
        * **referencer** (*int*) the :data:`xref` of the referencer. Zero if directly referenced by the page. Only present if *full=True*.

      See below how this information can be used to extract PDF images as separate files. Another demonstration::

        >>> doc = fitz.open("pymupdf.pdf")
        >>> doc.get_page_images(0, full=True)
        [[316, 0, 261, 115, 8, 'DeviceRGB', '', 'Im1', 'DCTDecode', 0]]
        >>> pix = fitz.Pixmap(doc, 316)  # 316 is the xref of the image
        >>> pix
        fitz.Pixmap(DeviceRGB, fitz.IRect(0, 0, 261, 115), 0)


    .. method:: get_page_fonts(pno, full=False)

      PDF only: Return a list of all fonts (directly or indirectly) referenced by the page.

      :arg int pno: page number, 0-based, -inf < pno < page_count.
      :arg bool full: whether to also include the referencer's :data:`xref`. If *True*, the returned items are one entry longer. Use this option if you need to know, whether the page directly references the font. In this case the last entry is 0. If the font is referenced by an ``/XObject`` of the page, you will find its :data:`xref` here.

      :rtype: list

      :returns: a list of fonts referenced by this page. Each entry looks like

      **(xref, ext, type, basefont, name, encoding, referencer)**,
        
      where

          * **xref** (*int*) is the font object number (may be zero if the PDF uses one of the builtin fonts directly)
          * **ext** (*str*) font file extension (e.g. "ttf", see :ref:`FontExtensions`)
          * **type** (*str*) is the font type (like "Type1" or "TrueType" etc.)
          * **basefont** (*str*) is the base font name,
          * **name** (*str*) is the symbolic name, by which the font is referenced
          * **encoding** (*str*) the font's character encoding if different from its built-in encoding (:ref:`AdobeManual`, p. 414):
          * **referencer** (*int* optional) the :data:`xref` of the referencer. Zero if directly referenced by the page, otherwise the xref of an XObject. Only present if *full=True*.

      Example::

          >>> pprint(doc.get_page_fonts(0, full=False))
          [(12, 'ttf', 'TrueType', 'FNUUTH+Calibri-Bold', 'R8', ''),
           (13, 'ttf', 'TrueType', 'DOKBTG+Calibri', 'R10', ''),
           (14, 'ttf', 'TrueType', 'NOHSJV+Calibri-Light', 'R12', ''),
           (15, 'ttf', 'TrueType', 'NZNDCL+CourierNewPSMT', 'R14', ''),
           (16, 'ttf', 'Type0', 'MNCSJY+SymbolMT', 'R17', 'Identity-H'),
           (17, 'cff', 'Type1', 'UAEUYH+Helvetica', 'R20', 'WinAnsiEncoding'),
           (18, 'ttf', 'Type0', 'ECPLRU+Calibri', 'R23', 'Identity-H'),
           (19, 'ttf', 'Type0', 'TONAYT+CourierNewPSMT', 'R27', 'Identity-H')]

      .. note:: This list has no duplicate entries: the combination of :data:`xref`, *name* and *referencer* is unique.

    .. method:: get_page_text(pno, output="text")

      Extracts the text of a page given its page number *pno* (zero-based). Invokes :meth:`Page.get_text`.

      :arg int pno: page number, 0-based, any value *-inf < pno < page_count*.

      :arg str output: A string specifying the requested output format: text, html, json or xml. Default is *text*.

      :rtype: str

    .. index::
       pair: fontsize; layout (Document method)
       pair: rect; layout (Document method)
       pair: width; layout (Document method)
       pair: height; layout (Document method)

    .. method:: layout(rect=None, width=0, height=0, fontsize=11)

      Re-paginate ("reflow") the document based on the given page dimension and fontsize. This only affects some document types like e-books and HTML. Ignored if not supported. Supported documents have *True* in property :attr:`is_reflowable`.

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

          * When dealing with only a few pages, methods :meth:`copy_page`, :meth:`move_page`, :meth:`delete_page` are easier to use. In fact, they are also **much faster** -- by at least one order of magnitude when the document has many pages.


    .. method:: set_metadata(m)

      PDF only: Sets or updates the metadata of the document as specified in *m*, a Python dictionary.

      :arg dict m: A dictionary with the same keys as *metadata* (see below). All keys are optional. A PDF's format and encryption method cannot be set or changed and will be ignored. If any value should not contain data, do not specify its key or set the value to *None*. If you use *{}* all metadata information will be cleared to the string *"none"*. If you want to selectively change only some values, modify a copy of *doc.metadata* and use it as the argument. Arbitrary unicode values are possible if specified as UTF-8-encoded.

      *(Changed in v1.18.4)* Empty values or "none" are no longer written, but completely omitted.

    .. method:: get_xml_metadata()

      PDF only: Get the document XML metadata.

      :rtype: str
      :returns: XML metadata of the document. Empty string if not present or not a PDF.

    .. method:: set_xml_metadata(xml)

      PDF only: Sets or updates XML metadata of the document.

      :arg str xml: the new XML metadata. Should be XML syntax, however no checking is done by this method and any string is accepted.

    .. method:: set_toc(toc, collapse=1)

      PDF only: Replaces the **complete current outline** tree (table of contents) with the one provided as the argument. After successful execution, the new outline tree can be accessed as usual via :meth:`Document.get_toc` or via :attr:`Document.outline`. Like with other output-oriented methods, changes become permanent only via :meth:`save` (incremental save supported). Internally, this method consists of the following two steps. For a demonstration see example below.

      - Step 1 deletes all existing bookmarks.

      - Step 2 creates a new TOC from the entries contained in *toc*.

      :arg sequence toc:

          A list / tuple with **all bookmark entries** that should form the new table of contents. Output variants of :meth:`get_toc` are acceptable. To completely remove the table of contents specify an empty sequence or None. Each item must be a list with the following format.

          * [lvl, title, page [, dest]] where

            - **lvl** is the hierarchy level (int > 0) of the item, which **must be 1** for the first item and at most 1 larger than the previous one.

            - **title** (str) is the title to be displayed. It is assumed to be UTF-8-encoded (relevant for multibyte code points only).

            - **page** (int) is the target page number **(attention: 1-based)**. Must be in valid range if positive. Set it to -1 if there is no target, or the target is external.

            - **dest** (optional) is a dictionary or a number. If a number, it will be interpreted as the desired height (in points) this entry should point to on the page. Use a dictionary (like the one given as output by ``get_toc(False)``) for a detailed control of the bookmark's properties, see :meth:`Document.get_toc` for a description.

      :arg int collapse: *(new in version 1.16.9)* controls the hierarchy level beyond which outline entries should initially show up collapsed. The default 1 will hence only display level 1, higher levels must be unfolded using the PDF viewer. To unfold everything, specify either a large integer, 0 or None.

      :rtype: int
      :returns: the number of inserted, resp. deleted items.

    .. method:: outline_xref(idx)

      *(New in v1.17.7)*

      PDF only: Return the :data:`xref` of the outline item. This is mainly used for internal purposes.

      arg int idx: index of the item in list :meth:`Document.get_toc`.

      :returns: :data:`xref`.

    .. method:: del_toc_item(idx)

      *(New in v1.17.7)*

      PDF only: Remove this TOC item. This is a high-speed method primarily meant for *disabling* items, which are pointing to deleted pages. Physically, the item still exists in the TOC tree, but will show an empty title and no longer point to a destination. So the overall TOC structure remains intact.

      This also implies that you can reassign the item to a destination when required.

      :arg int idx: the index of the item in list :meth:`Document.get_toc`.


    .. method:: set_toc_item(idx, dest_dict=None, kind=None, pno=None, uri=None, title=None, to=None, filename=None, zoom=0)

      *(New in v1.17.7)*

      *(Changed in v1.18.6)*

      PDF only: Changes the TOC item identified by its index. Change the item **title**, **destination**, **appearance** (color, bold, italic) or collapsing sub-items -- or to remove the item altogether.

      Use this method if you need specific changes for selected entries only and want to avoid replacing the complete TOC. This is beneficial especially when dealing with large table of contents.

      :arg int idx: the index of the entry in the list created by :meth:`Document.get_toc`.
      :arg dict dest_dict: the new destination. A dictionary like the last entry of an item in ``doc.get_toc(False)``. Using this as a template is recommended. When given, **all other parameters are ignored** -- except title.
      :arg int kind: the link kind, see :ref:`linkDest Kinds`. If :data:`LINK_NONE`, then all remaining parameter will be ignored, and the TOC item will be removed -- same as :meth:`Document.del_toc_item`. If None, then only the title is modified and the remaining parameters are ignored. All other values will lead to making a new destination dictionary using the subsequent arguments.
      :arg int pno: the 1-based page number, i.e. a value 1 <= pno <= doc.page_count. Required for LINK_GOTO.
      :arg str uri: the URL text. Required for LINK_URI.
      :arg str title: the desired new title. None if no change.
      :arg point_like to: (optional) points to a coordinate on the arget page. Relevant for LINK_GOTO. If omitted, a point near the page's top is chosen.
      :arg str filename: required for LINK_GOTOR and LINK_LAUNCH.
      :arg float zoom: use this zoom factor when showing the target page.

      **Example use:** Change the TOC of the SWIG manual to achieve this:
      
      Collapse everything below top level and show the chapter on Python support in red, bold and italic::

        >>> import fitz
        >>> doc=fitz.open("SWIGDocumentation.pdf")
        >>> toc = doc.get_toc(False)  # we need the detailed TOC
        >>> # make a list of level 1 indices and their titles
        >>> lvl1 = [(i, item[1]) for i, item in enumerate(toc) if item[0] == 1]
        >>> for i, title in lvl1:
                d = toc[i][3]  # get the destination dict
                d["collapse"] = True  # collapse items underneath
                if "Python" in title:  # show the 'Python' chapter
                    d["color"] = (1, 0, 0)  # in red,
                    d["bold"] = True  # bold and
                    d["italic"] = True  # italic
                doc.set_toc_item(i, dest_dict=d)  # update this toc item
        >>> doc.save("NEWSWIG.pdf",garbage=3,deflate=True)

      In the previous example, we have changed only 42 of the 1240 TOC items of the file.

    .. method:: can_save_incrementally()

      *(New in version 1.16.0)*
      
      Check whether the document can be saved incrementally. Use it to choose the right option without encountering exceptions.

    .. method:: scrub(attached_files=True, clean_pages=True, embedded_files=True, hidden_text=True, javascript=True, metadata=True, redactions=True, redact_images=0, remove_links=True, reset_fields=True, reset_responses=True, thumbnails=True, xml_metadata=True)

      PDF only: *(New in v1.16.14)* Remove potentially sensitive data from the PDF. This function is inspired by the similar "Sanitize" function in Adobe Acrobat products. The process is configurable by a number of options, which are all *True* by default.

      :arg bool attached_files: Search for 'FileAttachment' annotations and remove the file content.
      :arg bool clean_pages: Remove any comments from page painting sources. If this option is set to *False*, then this is also done for *hidden_text* and *redactions*.
      :arg bool embedded_files: Remove embedded files.
      :arg bool hidden_text: Remove OCR-ed text and invisible text.
      :arg bool javascript: Remove JavaScript sources.
      :arg bool metadata: Remove PDF standard metadata.
      :arg bool redactions: Apply redaction annotations.
      :arg int redact_images: how to handle images if applying redactions. One of 0 (ignore), 1 (blank out overlaps) or 2 (remove).
      :arg bool remove_links: Remove all links.
      :arg bool reset_fields: Reset all form fields to their defaults.
      :arg bool reset_responses: Remove all responses from all annotations.
      :arg bool thumbnails: Remove thumbnail images from pages.
      :arg bool xml_metadata: Remove XML metadata.


    .. method:: save(outfile, garbage=0, clean=False, deflate=False, deflate_images=False, deflate_fonts=False, incremental=False, ascii=False, expand=0, linear=False, pretty=False, encryption=PDF_ENCRYPT_NONE, permissions=-1, owner_pw=None, user_pw=None)

      *(Changed in v1.18.7)*

      PDF only: Saves the document in its **current state**.

      :arg str,Path,fp outfile: The file path, ``pathlib.Path`` or file object to save to. A file object must have been created before via ``open(...)`` or ``io.BytesIO()``. Choosing ``io.BytesIO()`` is similar to :meth:`Document.tobytes` below, which equals the ``getvalue()`` output of an internally created ``io.BytesIO()``.

      :arg int garbage: Do garbage collection. Positive values exclude "incremental".

       * 0 = none
       * 1 = remove unused (unreferenced) objects.
       * 2 = in addition to 1, compact the :data:`xref` table.
       * 3 = in addition to 2, merge duplicate objects.
       * 4 = in addition to 3, check :data:`stream` objects for duplication. This may be slow because such data are typically large.

      :arg bool clean: Clean and sanitize content streams [#f1]_. Corresponds to "mutool clean -sc".

      :arg bool deflate: Deflate (compress) uncompressed streams.
      :arg bool deflate_images: *(new in v1.18.3)* Deflate (compress) uncompressed image streams [#f4]_.
      :arg bool deflate_fonts: *(new in v1.18.3)* Deflate (compress) uncompressed fontfile streams [#f4]_.

      :arg bool incremental: Only save changes to the PDF. Excludes "garbage" and "linear". Can only be used if *outfile* is a string or a ``pathlib.Path`` and equal to :attr:`Document.name`. Cannot be used for files that are decrypted or repaired and also in some other cases. To be sure, check :meth:`Document.can_save_incrementally`. If this is false, saving to a new file is required.

      :arg bool ascii: convert binary data to ASCII.

      :arg int expand: Decompress objects. Generates versions that can be better read by some other programs and will lead to larger files.

       * 0 = none
       * 1 = images
       * 2 = fonts
       * 255 = all

      :arg bool linear: Save a linearised version of the document. This option creates a file format for improved performance for Internet access. Excludes "incremental".

      :arg bool pretty: Prettify the document source for better readability. PDF objects will be reformatted to look like the default output of :meth:`Document.xref_object`.

      :arg int permissions: *(new in version 1.16.0)* Set the desired permission levels. See :ref:`PermissionCodes` for possible values. Default is granting all.

      :arg int encryption: *(new in version 1.16.0)* set the desired encryption method. See :ref:`EncryptionMethods` for possible values.

      :arg str owner_pw: *(new in version 1.16.0)* set the document's owner password. *(Changed in v1.18.3)* If not provided, the user password is taken if provided.

      :arg str user_pw: *(new in version 1.16.0)* set the document's user password.

    .. method:: saveIncr()

      PDF only: saves the document incrementally. This is a convenience abbreviation for *doc.save(doc.name, incremental=True, encryption=PDF_ENCRYPT_KEEP)*.


    .. method:: tobytes(garbage=0, clean=False, deflate=False, deflate_images=False, deflate_fonts=False, ascii=False, expand=0, linear=False, pretty=False, encryption=PDF_ENCRYPT_NONE, permissions=-1, owner_pw=None, user_pw=None)

      *(Changed in v1.18.7)*

      PDF only: Writes the **current content of the document** to a bytes object instead of to a file. Obviously, you should be wary about memory requirements. The meanings of the parameters exactly equal those in :meth:`save`. Chapter :ref:`FAQ` contains an example for using this method as a pre-processor to `pdfrw <https://pypi.python.org/pypi/pdfrw/0.3>`_.

      *(Changed in version 1.16.0)* for extended encryption support.

      :rtype: bytes
      :returns: a bytes object containing the complete document.

    .. method:: search_page_for(pno, text, quads=False)

       Search for "text" on page number "pno". Works exactly like the corresponding :meth:`Page.search_for`. Any integer -inf < pno < page_count is acceptable.

    .. index::
       pair: from_page; insert_pdf (Document method)
       pair: to_page; insert_pdf (Document method)
       pair: start_at; insert_pdf (Document method)
       pair: rotate; insert_pdf (Document method)
       pair: links; insert_pdf (Document method)
       pair: annots; insert_pdf (Document method)
       pair: show_progress; insert_pdf (Document method)

    .. method:: insert_pdf(docsrc, from_page=-1, to_page=-1, start_at=-1, rotate=-1, links=True, annots=True, show_progress=0, final=1)

      PDF only: Copy the page range **[from_page, to_page]** (including both) of PDF document *docsrc* into the current one. Inserts will start with page number *start_at*. Value -1 indicates default values. All pages thus copied will be rotated as specified. Links and annotations can be excluded in the target, see below. All page numbers are 0-based.

      :arg docsrc: An opened PDF *Document* which must not be the current document. However, it may refer to the same underlying file.
      :type docsrc: *Document*

      :arg int from_page: First page number in *docsrc*. Default is zero.

      :arg int to_page: Last page number in *docsrc* to copy. Defaults to last page.

      :arg int start_at: First copied page, will become page number *start_at* in the target. Default -1 appends the page range to the end. If zero, the page range will be inserted before current first page.

      :arg int rotate: All copied pages will be rotated by the provided value (degrees, integer multiple of 90).

      :arg bool links: Choose whether (internal and external) links should be included in the copy. Default is *True*. Internal links to outside the copied page range are **always excluded**.
      :arg bool annots: *(new in version 1.16.1)* choose whether annotations should be included in the copy.
      :arg int show_progress: *(new in version 1.17.7)* specify an interval size greater zero to see progress messages on ``sys.stdout``. After each interval, a message like ``Inserted 30 of 47 pages.`` will be printed.
      :arg int final: *(new in v1.18.0)* controls whether the list of already copied objects should be **dropped** after this method, default *True*. Set it to 0 except for the last one of multiple insertions from the same source PDF. This saves target file size and speeds up execution considerably.
      
    .. note::

       1. If *from_page > to_page*, pages will be **copied in reverse order**. If *0 <= from_page == to_page*, then one page will be copied.

       2. *docsrc* TOC entries **will not be copied**. It is easy however, to recover a table of contents for the resulting document. Look at the examples below and at program `PDFjoiner.py <https://github.com/pymupdf/PyMuPDF-Utilities/tree/master/examples/PDFjoiner.py>`_ in the *examples* directory: it can join PDF documents and at the same time piece together respective parts of the tables of contents.

    .. index::
       pair: width; new_page (Document method)
       pair: height; new_page (Document method)

    .. method:: new_page(pno=-1, width=595, height=842)

      PDF only: Insert an empty page.

      :arg int pno: page number in front of which the new page should be inserted. Must be in *1 < pno <= page_count*. Special values -1 and *doc.page_count* insert **after** the last page.

      :arg float width: page width.
      :arg float height: page height.

      :rtype: :ref:`Page`
      :returns: the created page object.

    .. index::
       pair: fontsize; insert_page (Document method)
       pair: width; insert_page (Document method)
       pair: height; insert_page (Document method)
       pair: fontname; insert_page (Document method)
       pair: fontfile; insert_page (Document method)
       pair: color; insert_page (Document method)

    .. method:: insert_page(pno, text=None, fontsize=11, width=595, height=842, fontname="helv", fontfile=None, color=None)

      PDF only: Insert a new page and insert some text. Convenience function which combines :meth:`Document.new_page` and (parts of) :meth:`Page.insert_text`.

      :arg int pno: page number (0-based) **in front of which** to insert. Must be in *range(-1, len(doc) + 1)*. Special values -1 and *len(doc)* insert **after** the last page.

          Changed in version 1.14.12
             This is now a positional parameter

      For the other parameters, please consult the aforementioned methods.

      :rtype: int
      :returns: the result of :meth:`Page.insert_text` (number of successfully inserted lines).

    .. method:: delete_page(pno=-1)

      PDF only: Delete a page given by its 0-based number in -inf < pno < page_count - 1.

      Changed in version 1.14.17

      :arg int pno: the page to be deleted. Negative number count backwards from the end of the document (like with indices). Default is the last page.

    .. method:: delete_pages(from_page=-1, to_page=-1)

      PDF only: Delete a range of pages given as 0-based numbers. Any *-1* parameter will first be replaced by *doc.page_count - 1* (ie. last page number). After that, condition *0 <= from_page <= to_page < doc.page_count* must be true. If the parameters are equal, this is equivalent to :meth:`delete_page`.

      :arg int from_page: the first page to be deleted.

      :arg int to_page: the last page to be deleted.

      .. note::

        *(Changed in v1.14.17, optimized in v1.17.7)* In an effort to maintain a valid PDF structure, this method and :meth:`delete_page` will also invalidate items in the table of contents which happen to point to deleted pages. "Invalidation" here means, that the bookmark will point to nowhere and the title will show the string "<>". So the overall TOC structure is left intact.

        Similarly, it will remove any **links on remaining pages** that point to a deleted page. This action may have an extended response time for documents with many pages.

        Example: Delete the page range 500 to 520 from a large PDF, using different methods.

        Method 1 - *delete_pages*::

          import time, fitz
          doc = fitz.open("Adobe PDF Reference 1-7.pdf")
          t0=time.perf_counter();doc.delete_pages(500, 520);t1=time.perf_counter()
          round(t1 - t0, 2)
          0.66


        Method 2 - *select*, this is more than 10 times **slower**::

          l = list(range(500)) + list(range(521, 1310))
          t0=time.perf_counter();doc.select(l);t1=time.perf_counter()
          round(t1 - t0, 2)
          7.62


    .. method:: copy_page(pno, to=-1)

      PDF only: Copy a page reference within the document.

      :arg int pno: the page to be copied. Must be in range *0 <= pno < len(doc)*.

      :arg int to: the page number in front of which to copy. The default inserts **after** the last page.

      .. note:: Only a new **reference** to the page object will be created -- not a new page object, all copied pages will have identical attribute values, including the :attr:`Page.xref`. This implies that any changes to one of these copies will appear on all of them.

    .. method:: fullcopy_page(pno, to=-1)

      *(New in version 1.14.17)*
      
      PDF only: Make a full copy (duplicate) of a page.

      :arg int pno: the page to be duplicated. Must be in range *0 <= pno < len(doc)*.

      :arg int to: the page number in front of which to copy. The default inserts **after** the last page.

      .. note::
      
          * In contrast to :meth:`copy_page`, this method creates a new page object (with a new :data:`xref`), which can be changed independently from the original.

          * Any Popup and "IRT" ("in response to") annotations are **not copied** to avoid potentially incorrect situations.

    .. method:: move_page(pno, to=-1)

      PDF only: Move (copy and then delete original) a page within the document.

      :arg int pno: the page to be moved. Must be in range *0 <= pno < len(doc)*.

      :arg int to: the page number in front of which to insert the moved page. The default moves **after** the last page.


    .. method:: need_appearances(value=None)

      *(New in v1.17.4)*

      PDF only: Get or set the */NeedAppearances* property of Form PDFs. Quote: *"(Optional) A flag specifying whether to construct appearance streams and appearance dictionaries for all widget annotations in the document ... Default value: false."* This may help controlling the behavior of some readers / viewers.

      :arg bool value: set the property to this value. If omitted or *None*, inquire the current value.

      :rtype: bool
      :returns:
         * None: not a Form PDF or property not defined.
         * True / False: the value of the property (either just set or existing for inquiries).

         Once set, the property cannot be removed again (which is no problem).


    .. method:: get_sigflags()

      PDF only: Return whether the document contains signature fields. This is an optional PDF property: if not present (return value -1), no conclusions can be drawn -- the PDF creator may just not have bothered to use it.

      :rtype: int
      :returns:
         * -1: not a Form PDF / no signature fields recorded / no *SigFlags* found.
         * 1: at least one signature field exists.
         * 3:  contains signatures that may be invalidated if the file is saved (written) in a way that alters its previous contents, as opposed to an incremental update.

    .. index::
       pair: filename; embfile_add (Document method)
       pair: ufilename; embfile_add (Document method)
       pair: desc; embfile_add (Document method)

    .. method:: embfile_add(name, buffer, filename=None, ufilename=None, desc=None)

      PDF only: Embed a new file. All string parameters except the name may be unicode (in previous versions, only ASCII worked correctly). File contents will be compressed (where beneficial).

      Changed in version 1.14.16
         The sequence of positional parameters "name" and "buffer" has been changed to comply with the layout of other functions.

      :arg str name: entry identifier, must not already exist.
      :arg bytes,bytearray,BytesIO buffer: file contents.

         *(Changed in version 1.14.13)* *io.BytesIO* is now also supported.

      :arg str filename: optional filename. Documentation only, will be set to *name* if *None*.
      :arg str ufilename: optional unicode filename. Documentation only, will be set to *filename* if *None*.
      :arg str desc: optional description. Documentation only, will be set to *name* if *None*.


    .. method:: embfile_count()

      PDF only: Return the number of embedded files.

         Changed in version 1.14.16
            This is now a method. In previous versions, this was a property.

    .. method:: embfile_get(item)

      PDF only: Retrieve the content of embedded file by its entry number or name. If the document is not a PDF, or entry cannot be found, an exception is raised.

      :arg int,str item: index or name of entry. An integer must be in *range(embfile_count())*.

      :rtype: bytes

    .. method:: embfile_del(item)

      PDF only: Remove an entry from `/EmbeddedFiles`. As always, physical deletion of the embedded file content (and file space regain) will occur only when the document is saved to a new file with a suitable garbage option.

         Changed in version 1.14.16
            Items can now be deleted by index, too.

      :arg int/str item: index or name of entry.

      .. warning:: When specifying an entry name, this function will only **delete the first item** with that name. Be aware that PDFs not created with PyMuPDF may contain duplicate names. So you may want to take appropriate precautions.

    .. method:: embfile_info(item)

      PDF only: Retrieve information of an embedded file given by its number or by its name.

      :arg int/str item: index or name of entry. An integer must be in *range(embfile_count())*.

      :rtype: dict
      :returns: a dictionary with the following keys:

          * *name* -- (*str*) name under which this entry is stored
          * *filename* -- (*str*) filename
          * *ufilename* -- (*unicode*) filename
          * *desc* -- (*str*) description
          * *size* -- (*int*) original file size
          * *length* -- (*int*) compressed file length

    .. method:: embfile_names()

      *(New in version 1.14.16)*
      
      PDF only: Return a list of embedded file names. The sequence of names equals the physical sequence in the document.

      :rtype: list

    .. index::
       pair: filename; embfile_upd (Document method)
       pair: ufilename; embfile_upd (Document method)
       pair: desc; embfile_upd (Document method)

    .. method:: embfile_upd(item, buffer=None, filename=None, ufilename=None, desc=None)

      PDF only: Change an embedded file given its entry number or name. All parameters are optional. Letting them default leads to a no-operation.

      :arg int/str item: index or name of entry. An integer must be in *range(0, embfile_count())*.
      :arg bytes,bytearray,BytesIO buffer: the new file content.

         *(Changed in version 1.14.13)* *io.BytesIO* is now also supported.

      :arg str filename: the new filename.
      :arg str ufilename: the new unicode filename.
      :arg str desc: the new description.

    .. method:: embfile_setinfo(n, filename=None, ufilename=None, desc=None)

      PDF only: Change embedded file meta information. All parameters are optional. Letting them default will lead to a no-operation.

      :arg int,str n: index or name of entry. An integer must be in *range(embfile_count())*.
      :arg str filename: sets the filename.
      :arg str ufilename: sets the unicode filename.
      :arg str desc: sets the description.

      .. note:: Deprecated subset of :meth:`embfile_upd`. Will be deleted in a future version.

    .. method:: close()

      Release objects and space allocations associated with the document. If created from a file, also closes *filename* (releasing control to the OS).

    .. method:: xref_object(xref, compressed=False, ascii=False)

      *(New in version 1.16.8)*
      
      PDF only: Return the definition source of a PDF object.
  
    .. method:: pdf_catalog()
      
      *(New in version 1.16.8)*
      
      PDF only: Return the :data:`xref` number of the PDF catalog (or root) object. Use that number with :meth:`Document.xref_object` to see its source.


    .. method:: pdf_trailer(compressed=False)

      *(New in version 1.16.8)*
      
      PDF only: Return the trailer source of the PDF (UTF-8), which is usually located at the PDF file's end. This is similar to :meth:`Document.xref_object` except that this object has no identifier to access it.


    .. method:: xref_xml_metadata()

      *(New in version 1.16.8)*
      
      PDF only: Return the :data:`xref` of the document's XML metadata.

    .. method:: xref_stream(xref)

      *(New in version 1.16.8)*
      
      PDF only: Return the **decompressed** contents of the :data:`xref` stream object.

      :arg int xref: :data:`xref` number.

      :rtype: bytes
      :returns: the (decompressed) stream of the object.

    .. method:: xref_stream_raw(xref)

      *(New in version 1.16.8)*
      
      PDF only: Return the **unmodified** (esp. **not decompressed**) contents of the :data:`xref` stream object. Otherwise equal to :meth:`Document.xref_stream`.
 
      :rtype: bytes
      :returns: the (original, unmodified) stream of the object.

    .. method:: update_object(xref, obj_str, page=None)

      *(New in version 1.16.8)*
      
      PDF only: Replace object definition of :data:`xref` with the provided string. The xref may also be new, in which case this instruction completes the object definition. If a page object is also given, its links and annotations will be reloaded afterwards.

      :arg int xref: :data:`xref` number.

      :arg str obj_str: a string containing a valid PDF object definition.

      :arg page: a page object. If provided, indicates, that annotations of this page should be refreshed (reloaded) to reflect changes incurred with links and / or annotations.
      :type page: :ref:`Page`

      :rtype: int
      :returns: zero if successful, otherwise an exception will be raised.


    .. method:: update_stream(xref, data, new=False)

      *(New in version 1.16.8)*
      
      Replace the stream of an object identified by *xref*. If the object has no stream, an exception is raised unless *new=True* is used. The function automatically performs a compress operation ("deflate") where beneficial.

      :arg int xref: :data:`xref` number.

      :arg bytes|bytearray|BytesIO stream: the new content of the stream.

         *(Changed in version 1.14.13:)* *io.BytesIO* objects are now also supported.

      :arg bool new: whether to force accepting the stream, and thus **turning it into a stream object**.

        .. caution:: The object of :data:`xref` must be a PDF dictionary for this to work, and especially must not be empty -- as is the case if you just created the xref via :meth:`Document.get_new_xref`. To avoid this, execute ``doc.update_object(xref, "<<>>")`` before inserting the stream.

      This method is intended to manipulate streams containing PDF operator syntax (see pp. 985 of the :ref:`AdobeManual`) as it is the case for e.g. page content streams.

      If you update a contents stream, you should use save parameter *clean=True*. This ensures consistency between PDF operator source and the object structure.

      Example: Let us assume that you no longer want a certain image appear on a page. This can be achieved by deleting the respective reference in its contents source(s) -- and indeed: the image will be gone after reloading the page. But the page's :data:`resources` object would still show the image as being referenced by the page. This save option will clean up any such mismatches.

    .. method:: has_links()

    .. method:: has_annots()

      *(New in v1.18.7)*

      PDF only: Check whether there are links, resp. annotations anywhere in the document.

      :returns: *True* / *False*. As opposed to fields, which are stored in a central place of a PDF document, the existence of links / annotations can only be detected by parsing each page. These methods are tuned to do this efficiently and will immediately return, if the answer is *True* for a page. For PDFs with many thousand pages however, an answer may take some time [#f6]_ if no link, resp. no annotation is found.


    .. method:: subset_fonts()

      *(New in v1.18.7, changed in v1.18.9)*

      PDF only: **Experimental:** Investigate eligible fonts for their use by text in the document. If a font is supported and a size reduction is possible, that font is replaced by a version with a character subset.

      Use this method immediately before saving the document. The following features and restrictions apply for the time being:

      * Package `fontTools <https://pypi.org/project/fonttools/>`_ **must be installed**. It is required for creating the font subsets.
      * Supported font types only include embedded OTF, TTF and WOFF that are **not already subsets**.
      * The script directory must be available for writing temporary files during the subsetting process.
      * **Changed in v1.18.9:** A subset font directly replaces its original -- text remains untouched and **is not rewritten.** It thus should retain all its properties, like spacing, hiddenness, control by Optional Content, etc.

      The greatest benefit can be achieved when creating new PDFs using large fonts like is typical for Asian scripts. In these cases, the set of actually used unicodes mostly is small compared to the number of glyphs in the font. Using this feature can easily reduce the embedded font binary by two orders of magnitude -- from several megabytes to a low two-digit kilobyte amount.


    .. attribute:: outline

      Contains the first :ref:`Outline` entry of the document (or *None*). Can be used as a starting point to walk through all outline items. Accessing this property for encrypted, not authenticated documents will raise an *AttributeError*.

      :type: :ref:`Outline`

    .. attribute:: is_closed

      *False* if document is still open. If closed, most other attributes and methods will have been deleted / disabled. In addition, :ref:`Page` objects referring to this document (i.e. created with :meth:`Document.load_page`) and their dependent objects will no longer be usable. For reference purposes, :attr:`Document.name` still exists and will contain the filename of the original document (if applicable).

      :type: bool

    .. attribute:: is_dirty

      *True* if this is a PDF document and contains unsaved changes, else *False*.

      :type: bool

    .. attribute:: is_pdf

      *True* if this is a PDF document, else *False*.

      :type: bool

    .. attribute:: is_pdf

      *True* if this is a PDF document, else *False*.

      :type: bool

    .. attribute:: is_form_pdf

      *False* if this is not a PDF or has no form fields, otherwise the number of root form fields (fields with no ancestors).

      *(Changed in version 1.16.4)* Returns the total number of (root) form fields.

      :type: bool,int

    .. attribute:: is_reflowable

      *True* if document has a variable page layout (like e-books or HTML). In this case you can set the desired page dimensions during document creation (open) or via method :meth:`layout`.

      :type: bool

    .. attribute:: is_repaired

      *(New in v1.18.2)*

      *True* if PDF has been repaired during open (because of major structure issues). Always *False* for non-PDF documents. If true, more details have been stored in ``TOOLS.mupdf_warnings()``, and :meth:`Document.can_save_incrementally` will return *False*.

      :type: bool

    .. attribute:: needs_pass

      Indicates whether the document is password-protected against access. This indicator remains unchanged -- **even after the document has been authenticated**. Precludes incremental saves if true.

      :type: bool

    .. attribute:: is_encrypted

      This indicator initially equals :attr:`Document.needs_pass`. After successful authentication, it is set to *False* to reflect the situation.

      :type: bool

    .. attribute:: permissions

      Contains the permissions to access the document. This is an integer containing bool values in respective bit positions. For example, if *doc.permissions & fitz.PDF_PERM_MODIFY > 0*, you may change the document. See :ref:`PermissionCodes` for details.

      Changed in version 1.16.0 This is now an integer comprised of bit indicators. Was a dictionary previously.

      :type: int

    .. attribute:: metadata

      Contains the document's meta data as a Python dictionary or *None* (if *is_encrypted=True* and *needPass=True*). Keys are *format*, *encryption*, *title*, *author*, *subject*, *keywords*, *creator*, *producer*, *creationDate*, *modDate*, *trapped*. All item values are strings or *None*.

      Except *format* and *encryption*, for PDF documents, the key names correspond in an obvious way to the PDF keys */Creator*, */Producer*, */CreationDate*, */ModDate*, */Title*, */Author*, */Subject*, */Trapped* and */Keywords* respectively.

      - *format* contains the document format (e.g. 'PDF-1.6', 'XPS', 'EPUB').

      - *encryption* either contains *None* (no encryption), or a string naming an encryption method (e.g. *'Standard V4 R4 128-bit RC4'*). Note that an encryption method may be specified **even if** *needs_pass=False*. In such cases not all permissions will probably have been granted. Check :attr:`Document.permissions` for details.

      - If the date fields contain valid data (which need not be the case at all!), they are strings in the PDF-specific timestamp format "D:<TS><TZ>", where

          - <TS> is the 12 character ISO timestamp *YYYYMMDDhhmmss* (*YYYY* - year, *MM* - month, *DD* - day, *hh* - hour, *mm* - minute, *ss* - second), and

          - <TZ> is a time zone value (time intervall relative to GMT) containing a sign ('+' or '-'), the hour (*hh*), and the minute (*'mm'*, note the apostrophies!).

      - A Paraguayan value might hence look like *D:20150415131602-04'00'*, which corresponds to the timestamp April 15, 2015, at 1:16:02 pm local time Asuncion.

      :type: dict

    .. Attribute:: name

      Contains the *filename* or *filetype* value with which *Document* was created.

      :type: str

    .. Attribute:: page_count

      Contains the number of pages of the document. May return 0 for documents with no pages. Function *len(doc)* will also deliver this result.

      :type: int

    .. Attribute:: chapter_count
      
      *(New in version 1.17.0)*
      Contains the number of chapters in the document. Always at least 1. Relevant only for document types with chapter support (EPUB currently). Other documents will return 1.

      :type: int

    .. Attribute:: last_location

      *(New in version 1.17.0)*
      Contains (chapter, pno) of the document's last page. Relevant only for document types with chapter support (EPUB currently). Other documents will return *(0, len(doc) - 1)* and *(0, -1)* if it has no pages.

      :type: int

    .. Attribute:: FormFonts

      A list of form field font names defined in the */AcroForm* object. *None* if not a PDF.

      :type: list

.. NOTE:: For methods that change the structure of a PDF (:meth:`insert_pdf`, :meth:`select`, :meth:`copy_page`, :meth:`delete_page` and others), be aware that objects or properties in your program may have been invalidated or orphaned. Examples are :ref:`Page` objects and their children (links, annotations, widgets), variables holding old page counts, tables of content and the like. Remember to keep such variables up to date or delete orphaned objects. Also refer to :ref:`ReferenialIntegrity`.

:meth:`set_metadata` Example
-------------------------------
Clear metadata information. If you do this out of privacy / data protection concerns, make sure you save the document as a new file with *garbage > 0*. Only then the old */Info* object will also be physically removed from the file. In this case, you may also want to clear any XML metadata inserted by several PDF editors:

>>> import fitz
>>> doc=fitz.open("pymupdf.pdf")
>>> doc.metadata             # look at what we currently have
{'producer': 'rst2pdf, reportlab', 'format': 'PDF 1.4', 'encryption': None, 'author':
'Jorj X. McKie', 'modDate': "D:20160611145816-04'00'", 'keywords': 'PDF, XPS, EPUB, CBZ',
'title': 'The PyMuPDF Documentation', 'creationDate': "D:20160611145816-04'00'",
'creator': 'sphinx', 'subject': 'PyMuPDF 1.9.1'}
>>> doc.set_metadata({})      # clear all fields
>>> doc.metadata             # look again to show what happened
{'producer': 'none', 'format': 'PDF 1.4', 'encryption': None, 'author': 'none',
'modDate': 'none', 'keywords': 'none', 'title': 'none', 'creationDate': 'none',
'creator': 'none', 'subject': 'none'}
>>> doc._delXmlMetadata()    # clear any XML metadata
>>> doc.save("anonymous.pdf", garbage = 4)       # save anonymized doc

:meth:`set_toc` Demonstration
----------------------------------
This shows how to modify or add a table of contents. Also have a look at `csv2toc.py <https://github.com/pymupdf/PyMuPDF-Utilities/tree/master/examples/csv2toc.py>`_ and `toc2csv.py <https://github.com/pymupdf/PyMuPDF-Utilities/tree/master/examples/toc2csv.py>`_ in the examples directory.

>>> import fitz
>>> doc = fitz.open("test.pdf")
>>> toc = doc.get_toc()
>>> for t in toc: print(t)                           # show what we have
[1, 'The PyMuPDF Documentation', 1]
[2, 'Introduction', 1]
[3, 'Note on the Name fitz', 1]
[3, 'License', 1]
>>> toc[1][1] += " modified by set_toc"               # modify something
>>> doc.set_toc(toc)                                  # replace outline tree
3                                                    # number of bookmarks inserted
>>> for t in doc.get_toc(): print(t)                  # demonstrate it worked
[1, 'The PyMuPDF Documentation', 1]
[2, 'Introduction modified by set_toc', 1]            # <<< this has changed
[3, 'Note on the Name fitz', 1]
[3, 'License', 1]

:meth:`insert_pdf` Examples
----------------------------
**(1) Concatenate two documents including their TOCs:**

>>> doc1 = fitz.open("file1.pdf")          # must be a PDF
>>> doc2 = fitz.open("file2.pdf")          # must be a PDF
>>> pages1 = len(doc1)                     # save doc1's page count
>>> toc1 = doc1.get_toc(False)     # save TOC 1
>>> toc2 = doc2.get_toc(False)     # save TOC 2
>>> doc1.insert_pdf(doc2)                   # doc2 at end of doc1
>>> for t in toc2:                         # increase toc2 page numbers
        t[2] += pages1                     # by old len(doc1)
>>> doc1.set_toc(toc1 + toc2)               # now result has total TOC

Obviously, similar ways can be found in more general situations. Just make sure that hierarchy levels in a row do not increase by more than one. Inserting dummy bookmarks before and after *toc2* segments would heal such cases. A ready-to-use GUI (wxPython) solution can be found in script `PDFjoiner.py <https://github.com/pymupdf/PyMuPDF-Utilities/tree/master/examples/PDFjoiner.py>`_ of the examples directory.

**(2) More examples:**

>>> # insert 5 pages of doc2, where its page 21 becomes page 15 in doc1
>>> doc1.insert_pdf(doc2, from_page=21, to_page=25, start_at=15)

>>> # same example, but pages are rotated and copied in reverse order
>>> doc1.insert_pdf(doc2, from_page=25, to_page=21, start_at=15, rotate=90)

>>> # put copied pages in front of doc1
>>> doc1.insert_pdf(doc2, from_page=21, to_page=25, start_at=0)

Other Examples
----------------
**Extract all page-referenced images of a PDF into separate PNG files**::

 for i in range(len(doc)):
     imglist = doc.get_page_images(i)
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

>>> for page in doc: page.set_rotation(90)

.. rubric:: Footnotes

.. [#f1] Content streams describe what (e.g. text or images) appears where and how on a page. PDF uses a specialized mini language similar to PostScript to do this (pp. 985 in :ref:`AdobeManual`), which gets interpreted when a page is loaded.

.. [#f2] However, you **can** use :meth:`Document.get_toc` and :meth:`Page.get_links` (which are available for all document types) and copy this information over to the output PDF. See demo `pdf-converter.py <https://github.com/pymupdf/PyMuPDF-Utilities/tree/master/demo/pdf-converter.py>`_.

.. [#f3] For applicable (EPUB) document types, loading a page via its absolute number may result in layouting a large part of the document, before the page can be accessed. To avoid this performance impact, prefer chapter-based access. Use convenience methods / attributes :meth:`Document.next_location`, :meth:`Document.prev_location` and :attr:`Document.last_location` for maintaining a high level of coding efficiency.

.. [#f4] These parameters cause separate handling of stream categories: use it together with ``expand`` to restrict decompression to streams other than images / fontfiles.

.. [#f5] Examples for "Form XObjects" are created by :meth:`Page.show_pdf_page`.

.. [#f6] For a *False* the **complete document** must be scanned. Both methods **do not load pages,** but only scan object definitions. This makes them at least 10 times faster than application-level loops (where total response time roughly equals the time for loading all pages). For the :ref:`AdobeManual` (1'310 pages) and the Pandas documentation (over 3'070 pages) -- both havo no annotations -- the method needs about 11 ms for the answer *False*. So response times will probably become significant only well beyond this order of magnitude.

