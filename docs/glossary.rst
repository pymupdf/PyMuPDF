.. include:: header.rst

.. _Glossary:

==============
Glossary
==============

.. data:: coordinate

        This is an essential general mathematical / geometrical term for understanding this documentation. Please see this section for a more detailed discussion: :ref:`Coordinates`.

.. data:: matrix_like

        A Python sequence of 6 numbers.

.. data:: rect_like

        A Python sequence of 4 numbers.

.. data:: irect_like

        A Python sequence of 4 integers.

.. data:: point_like

        A Python sequence of 2 numbers.

.. data:: quad_like

        A Python sequence of 4 :data:`point_like` items.

.. data:: inheritable

        A number of values in a PDF can inherited by objects further down in a parent-child relationship. The mediabox (physical size) of pages may for example be specified only once or in some node(s) of the :data:`pagetree` and will then be taken as value for all *kids*, that do not specify their own value.

.. _Glossary_MediaBox:

.. data:: MediaBox

        A PDF array of 4 floats specifying a physical page size -- (:data:`inheritable`, mandatory). This rectangle should contain all other PDF  -- optional -- page rectangles, which may be specified in addition: CropBox, TrimBox, ArtBox and BleedBox. Please consult :ref:`AdobeManual` for details. The MediaBox is the only rectangle, for which there is no difference between MuPDF and PDF coordinate systems: :attr:`Page.mediabox` will always show the same coordinates as the `/MediaBox` key in a page's object definition. For all other rectangles, MuPDF transforms y coordinates such that the **top** border is the point of reference. This can sometimes be confusing -- you may for example encounter a situation like this one:

        * The page definition contains the following identical values: `/MediaBox [ 36 45 607.5 765 ]`, `/CropBox [ 36 45 607.5 765 ]`.
        * PyMuPDF accordingly shows `page.mediabox = Rect(36.0, 45.0, 607.5, 765.0)`.
        * **BUT:** `page.cropbox = Rect(36.0, 0.0, 607.5, 720.0)`, because the two y-coordinates have been transformed (45 subtracted from both of them).

.. data:: CropBox

        A PDF array of 4 floats specifying a page's visible area -- (:data:`inheritable`, optional). It is the default for TrimBox, ArtBox and BleedBox. If not present, it defaults to MediaBox. This value is **not affected** if the page is rotated -- in contrast to :attr:`Page.rect`. Also, other than the page rectangle, the top-left corner of the cropbox may or may not be *(0, 0)*.


.. data:: catalog

        A central PDF :data:`dictionary` -- also called the "root" -- containing document-wide parameters and pointers to many other information. Its :data:`xref` is returned by :meth:`Document.pdf_catalog`.

.. data:: trailer

        More precisely, the **PDF trailer** contains information in :data:`dictionary` format. It is usually located at the file's end. In this dictionary, you will find things like the xrefs of the catalog and the metadata, the number of :data:`xref` numbers, etc. Here is the definition of the PDF spec:
        
        *"The trailer of a PDF file enables an application reading the file to quickly find the cross-reference table and certain special objects. Applications should read a PDF file from its end."*

        To access the trailer in PyMuPDF, use the usual methods :meth:`Document.xref_object`, :meth:`Document.xref_get_key` and :meth:`Document.xref_get_keys` with `-1` instead of a positive xref number.

.. data:: contents

        A **content stream** is a PDF :data:`object` with an attached :data:`stream`, whose data consists of a sequence of instructions describing the graphical elements to be painted on a page, see "Stream Objects" on page 19 of :ref:`AdobeManual`. For an overview of the mini-language used in these streams, see chapter "Operator Summary" on page 643 of the :ref:`AdobeManual`. A PDF :data:`page` can have none to many contents objects. If it has none, the page is empty (but still may show annotations). If it has several, they will be interpreted in sequence as if their instructions had been present in one such object (i.e. like in a concatenated string). It should be noted that there are more stream object types which use the same syntax: e.g. appearance dictionaries associated with annotations and Form XObjects.

        PyMuPDF provides a number of methods to deal with contents of PDF pages:

        * :meth:`Page.read_contents()` -- reads and concatenates all page contents into one `bytes` object.
        * :meth:`Page.clean_contents()` -- a wrapper of a MuPDF function that reads, concatenates and syntax-cleans all page contents. After this, only one `/Contents` object will exist. In addition, page :data:`resources` will have been synchronized with it such that it will contain exactly those images, fonts and other objects that the page actually references.
        * :meth:`Page.get_contents()` -- return a list of :data:`xref` numbers of a page's :data:`contents` objects. May be empty. Use :meth:`Document.xref_stream()` with one of these xrefs to read the resp. contents section.
        * :meth:`Page.set_contents()` -- set a page's `/Contents` key to the provided :data:`xref` number.

.. data:: resources

        A :data:`dictionary` containing references to any resources (like images or fonts) required by a PDF :data:`page` (required, inheritable, :ref:`AdobeManual` p. 81) and certain other objects (Form XObjects). This dictionary appears as a sub-dictionary in the object definition under the key */Resources*. Being an inheritable object type, there may exist "parent" resources for all pages or certain subsets of pages.

.. data:: dictionary

        A PDF :data:`object` type, which is somewhat comparable to the same-named Python notion: "A dictionary object is an associative table containing pairs of objects, known as the dictionary's entries. The first element of each entry is the key and the second element is the value. The key must be a name (...). The value can be any kind of object, including another dictionary. A dictionary entry whose value is null (...) is equivalent to an absent entry." (:ref:`AdobeManual` p. 18).

        Dictionaries are the most important :data:`object` type in PDF. Here is an example (describing a :data:`page`)::

            <<
            /Contents 40 0 R                  % value: an indirect object
            /Type/Page                        % value: a name object
            /MediaBox[0 0 595.32 841.92]      % value: an array object
            /Rotate 0                         % value: a number object
            /Parent 12 0 R                    % value: an indirect object
            /Resources<<                      % value: a dictionary object
                /ExtGState<</R7 26 0 R>>
                /Font<<
                     /R8 27 0 R/R10 21 0 R/R12 24 0 R/R14 15 0 R
                     /R17 4 0 R/R20 30 0 R/R23 7 0 R /R27 20 0 R
                     >>
                /ProcSet[/PDF/Text]           % value: array of two name objects
                >>
            /Annots[55 0 R]                   % value: array, one entry (indirect object)
            >>

        *Contents*, *Type*, *MediaBox*, etc. are **keys**, *40 0 R*, *Page*, *[0 0 595.32 841.92]*, etc. are the respective **values**. The strings *"<<"* and *">>"* are used to enclose object definitions.

        This example also shows the syntax of **nested** dictionary values: *Resources* has an object as its value, which in turn is a dictionary with keys like *ExtGState* (with the value *<</R7 26 0 R>>*, which is another dictionary), etc.

.. data:: page

        A PDF page is a :data:`dictionary` object which defines one page in a PDF, see :ref:`AdobeManual` p. 71.

.. data:: pagetree

        The pages of a document are accessed through a structure known as the page tree, which defines the ordering of pages in the document. The tree structure allows PDF consumer applications, using only limited memory, to quickly open a document containing thousands of pages. The tree contains nodes of two types: intermediate nodes, called page tree nodes, and leaf nodes, called page objects. (:ref:`AdobeManual` p. 75).

        While it is possible to list all page references in just one array, PDFs with many pages are often created using *balanced tree* structures ("page trees") for faster access to any single page. In relation to the total number of pages, this can reduce the average page access time by page number from a linear to some logarithmic order of magnitude.

        For fast page access, MuPDF can use its own array in memory -- independently from what may or may not be present in the document file. This array is indexed by page number and therefore much faster than even the access via a perfectly balanced page tree.

.. data:: object

        Similar to Python, PDF supports the notion *object*, which can come in eight basic types: boolean values ("true" or "false"), integer and real numbers, strings (**always** enclosed in brackets -- either "()", or "<>" to indicate hexadecimal), names (must always start with a "/", e.g. `/Contents`), arrays (enclosed in brackets "[]"), dictionaries (enclosed in brackets "<<>>"), streams (enclosed by keywords "stream" / "endstream"), and the null object ("null") (:ref:`AdobeManual` p. 13). Objects can be made identifiable by assigning a label. This label is then called *indirect* object. PyMuPDF supports retrieving definitions of indirect objects via their cross reference number via :meth:`Document.xref_object`.

.. data:: stream

        A PDF :data:`dictionary` :data:`object` type which is followed by a sequence of bytes, similar to Python *bytes*. "However, a PDF application can read a stream incrementally, while a string must be read in its entirety. Furthermore, a stream can be of unlimited length, whereas a string is subject to an implementation limit. For this reason, objects with potentially large amounts of data, such as images and page descriptions, are represented as streams." "A stream consists of a :data:`dictionary` followed by zero or more bytes bracketed between the keywords *stream* and *endstream*"::

            nnn 0 obj
            <<
               dictionary definition
            >>
            stream
            (zero or more bytes)
            endstream
            endobj

        See :ref:`AdobeManual` p. 19. PyMuPDF supports retrieving stream content via :meth:`Document.xref_stream`. Use :meth:`Document.is_stream` to determine whether an object is of stream type.

.. data:: unitvector

        A mathematical notion meaning a vector of norm ("length") 1 -- usually the Euclidean norm is implied. In PyMuPDF, this term is restricted to :ref:`Point` objects, see :attr:`Point.unit`.

.. data:: xref

        Abbreviation for cross-reference number: this is an integer unique identification for objects in a PDF. There exists a cross-reference table (which may physically consist of several separate segments) in each PDF, which stores the relative position of each object for quick lookup. The cross-reference table is one entry longer than the number of existing object: item zero is reserved and must not be used in any way. Many PyMuPDF classes have an *xref* attribute (which is zero for non-PDFs), and one can find out the total number of objects in a PDF via :meth:`Document.xref_length` *- 1*.


.. data:: fontsize

        When referring to font size this metric is measured in points where 1 inch = 72 points.

.. data:: resolution

        Images and :ref:`Pixmap` objects may contain resolution information provided as "dots per inch", dpi, in each direction (horizontal and vertical). When MuPDF reads an image from a file or from a PDF object, it will parse this information and put it in :attr:`Pixmap.xres`, :attr:`Pixmap.yres`, respectively. If it finds no meaningful information in the input (like non-positive values or values exceeding 4800), it will use "sane" defaults instead. The usual default value is 96, but it may also be 72 in some cases (e.g. for JPX images).

.. data:: OCPD

        Optional content properties dictionary - a sub :data:`dictionary` of the PDF :data:`catalog`. The central place to store optional content information, which is identified by the key `/OCProperties`. This dictionary has two required and one optional entry: (1) `/OCGs`, required, an array listing all optional content groups, (2) `/D`, required, the default optional content configuration dictionary (OCCD), (3) `/Configs`, optional, an array of alternative OCCDs.


.. data:: OCCD

        Optional content configuration dictionary - a PDF :data:`dictionary` inside the PDF :data:`OCPD`. It stores a setting of ON / OFF states of OCGs and how they are presented to a PDF viewer program. Selecting a configuration is quick way to achieve temporary mass visibility state changes. After opening a PDF, the `/D` configuration of the :data:`OCPD` is always activated. Viewer should offer a way to switch between the `/D`, or one of the optional configurations contained in array `/Configs`.


.. data:: OCG

        Optional content group -- a :data:`dictionary` object used to control the visibility of other PDF objects like images or annotations. Independently on which page they are defined, objects with the same OCG can simultaneously be shown or hidden by setting their OCG to ON or OFF. This can be achieved via the user interface provided by many PDF viewers (Adobe Acrobat), or programmatically.

.. data:: OCMD
        
        Optional content membership dictionary -- a :data:`dictionary` object which can be used like an :data:`OCG`: it has a visibility state. The visibility of an OCMD is **computed:** it is a logical expression, which uses the state of one or more OCGs to produce a boolean value. The expression's result is interpreted as ON (true) or OFF (false).

.. data:: ligature
        
        Some frequent character combinations are represented by their own special glyphs in more advanced fonts. Typical examples are "fi", "fl", "ffi" and "ffl". These compounds are called *ligatures*. In PyMuPDF text extractions, there is the option to either return the corresponding unicode unchanged, or split ligatures up into their constituent parts: "fi" ==> "f" + "i", etc.

.. include:: footer.rst
