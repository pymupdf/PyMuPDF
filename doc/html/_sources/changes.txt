.. raw:: pdf

    PageBreak

Changes in Version 1.10.0
==========================

MuPDF v1.10 Impact
------------------
MuPDF version 1.10 has a significant impact on our bindings. Some of the changes also affect the API - in other words, **you** as a PyMuPDF user.

* Link destination information has been reduced. Several properties of the ``linkDest`` class no longer contain valuable information. In fact, this class as a whole has been deleted from MuPDF's library and we in PyMuPDF only maintain it to provide compatibilty to existing code.

* In an effort to minimize memory requirements, several improvements have been built into MuPDF v1.10:

    - A new ``config.h`` file can be used to de-select unwanted features in the C base code. Using this feature we have been able to reduce the size of our binary ``_fitz.o`` / ``_fitz.pyd`` by about 50% (from 9 MB to 4.5 MB). When UPX-ing this, the size goes even further down to a very handy 2.3 MB.

    - The alpha (transparency) channel for pixmaps is now optional. Letting alpha default to ``False`` significantly reduces pixmap sizes (by 20% - CMYK, 25% - RGB, 50% - GRAY). Many ``Pixmap`` constructors therefore now accept an ``alpha`` boolean to control inclusion of this channel. Other pixmap constructors (e.g. those for file and image input) create pixmaps with no alpha alltogether. On the downside, save methods for pixmaps no longer accept a ``savealpha`` option: this channel will always be saved when present. In order to minimize code breaks, we have left this parameter in the call patterns - it will just be ignored.

* ``DisplayList`` and ``TextPage`` class constructors now **require the mediabox** of the page they are referring to (i.e. the ``page.bound()`` rectangle). There is no way to construct this information from other sources, therefore a source code change cannot be avoided in these cases. We assume however, that not many users are actually employing these rather low level classes explixitely. So the impact of that change should be minor.

Other Changes compared to Version 1.9.3
----------------------------------------
* The new :ref:`Document` method ``write()`` writes an opened PDF to memory as opposed to a file, like ``save()`` does.
* An annotation can now be scaled and moved around on its page. This is done by modifying its rectangle.
* Annotations can now be deleted. :ref:`Page` contains the new method ``deleteAnnot()``.
* Various annotation attributes can now be modified, e.g. content, dates, title (= author), border, colors, line end styles.
* Method ``Document.insertPDF()`` now also copies annotations of source pages.
* The ``Pages`` class has been deleted. As documents can now be accessed with page numbers as indices (like ``doc[n] = doc.loadPage(n)``), the benefit of this class was too low to maintain it.
* The :ref:`Pixmap` method ``getSize()`` has been replaced with property ``size``. As before ``Pixmap.size == len(Pixmap)`` is ``True``.
* In response to transparency (alpha) being optional, several new parameters and properties have been added to :ref:`Pixmap` and :ref:`Colorspace` classes to support determining their characteristics.
* The :ref:`Page` class now contains new properties ``firstAnnot`` and ``firstLink`` to provide starting points to the respective class chains, where ``firstLink`` is just a mnemonic synonym to method ``loadLinks()`` which continues to exist. Similarly, the new property ``rect`` is a synonym for method ``bound()``, which also continues to exist.
* :ref:`Pixmap` methods ``samplesRGB()`` and ``samplesAlpha()`` have been deleted because pixmaps can now be created without transparency.


Changes in Version 1.9.3
=========================
This version is also based on MuPDF v1.9a. Changes compared to version 1.9.2:

* As a major enhancement, annotations are now supported in a similar way as links. Annotations can be displayed (as pixmaps) and their properties can be accessed.
* In addition to the document ``select()`` method, some simpler methods can now be used to manipulate a PDF:

    - ``copyPage()`` copies a page within a document.
    - ``movePage()`` is similar, but deletes the original.
    - ``deletePage()`` deletes a page
    - ``deletePageRange()`` deletes a page range

* ``rotation`` or ``setRotation()`` access or change a PDF page's rotation, respectively.
* Available but undocumented before, :ref:`IRect`, :ref:`Rect`, :ref:`Point` and :ref:`Matrix` support the ``len()`` method and their coordinate properties can be accessed via indices, e.g. ``IRect.x1 == IRect[2]``.
* For convenience, documents now support simple indexing: ``doc.loadPage(n) == doc[n]``. The index may however be in range ``-pageCount < n < pageCount``, such that ``doc[-1]`` is the last page of the document.

Changes in Version 1.9.2
=========================
This version is also based on MuPDF v1.9a. Changes compared to version 1.9.1:

* ``fitz.open()`` (no parameters) creates a new empty **PDF** document, i.e. if saved afterwards, it must be given a ``.pdf`` extension.
* :ref:`Document` now accepts all of the following formats (``Document`` and ``open`` are synonyms):

  - ``open()``,
  - ``open(filename)`` (equivalent to ``open(filename, None)``),
  - ``open(filetype, area)`` (equivalent to ``open(filetype, stream = area)``).

  Type of memory area ``stream`` may be ``str`` (Python 2), ``bytes`` (Python 3) or ``bytearray`` (Python 2 and 3). Thus, e.g. ``area = open("file.pdf", "rb").read()`` may be used directly (without first converting it to bytearray).
* New method ``Document.insertPDF()`` (PDFs only) inserts a range of pages from another PDF.
* ``Document`` objects doc now support the ``len()`` function: ``len(doc) == doc.pageCount``.
* New method ``Document.getPageImageList()`` creates a list of images used on a page.
* New method ``Document.getPageFontList()`` creates a list of fonts referenced by a page.
* New pixmap constructor ``fitz.Pixmap(doc, xref)`` creates a pixmap based on an opened PDF document and an XREF number of the image.
* New pixmap constructor ``fitz.Pixmap(cspace, spix)`` creates a pixmap as a copy of another one ``spix`` with the colorspace converted to ``cspace``. This works for all colorspace combinations.
* Pixmap constructor ``fitz.Pixmap(colorspace, width, height, samples)`` now allows ``samples`` to also be ``str`` (Python 2) or ``bytes`` (Python 3), not only ``bytearray``.


Changes in Version 1.9.1
=========================
This version of PyMuPDF is based on MuPDF library source code version 1.9a published on April 21, 2016.

Please have a look at MuPDF's website to see which changes and enhancements are contained herein.

Changes in version 1.9.1 compared to version 1.8.0 are the following:

* New methods ``getRectArea()`` for both ``fitz.Rect`` and ``fitz.IRect``
* Pixmaps can now be created directly from files using the new constructor ``fitz.Pixmap(filename)``.
* The Pixmap constructor ``fitz.Pixmap(image)`` has been extended accordingly.
* ``fitz.Rect`` can now be created with all possible combinations of points and coordinates.
* PyMuPDF classes and methods now all contain  __doc__ strings,  most of them created by SWIG automatically. While the PyMuPDF documentation certainly is more detailed, this feature should help a lot when programming in Python-aware IDEs.
* A new document method of ``getPermits()`` returns the permissions associated with the current access to the document (print, edit, annotate, copy), as a Python dictionary.
* The identity matrix ``fitz.Identity`` is now **immutable**.
* The new document method ``select(list)`` removes all pages from a document that are not contained in the list. Pages can also be duplicated and re-arranged.
* Various improvements and new members in our demo and examples collections. Perhaps most prominently: ``PDF_display`` now supports scrolling with the mouse wheel, and there is a new example program ``wxTableExtract`` which allows to graphically identify and extract table data in documents.
* ``fitz.open()`` is now an alias of ``fitz.Document()``.
* New pixmap method ``getPNGData()`` which will return a bytearray formatted as a PNG image of the pixmap.
* New pixmap method ``samplesRGB()`` providing a ``samples`` version with alpha bytes stripped off (RGB colorspaces only).
* New pixmap method ``samplesAlpha()`` providing the alpha bytes only of the ``samples`` area.
* New iterator ``fitz.Pages(doc)`` over a document's set of pages.
* New matrix methods ``invert()`` (calculate inverted matrix), ``concat()`` (calculate matrix product), ``preTranslate()`` (perform a shift operation).
* New ``IRect`` methods ``intersect()`` (intersection with another rectangle), ``translate()`` (perform a shift operation).
* New ``Rect`` methods ``intersect()`` (intersection with another rectangle), ``transform()`` (transformation with a matrix), ``includePoint()`` (enlarge rectangle to also contain a point), ``includeRect()`` (enlarge rectangle to also contain another one).
* Documented ``Point.transform()`` (transform a point with a matrix).
* ``Matrix``, ``IRect``, ``Rect`` and ``Point`` classes now support compact, algebraic formulations for manipulating such objects.
* Incremental saves for changes are possible now using the call pattern ``doc.save(doc.name, incremental=True)``.
* A PDF's metadata can now be deleted, set or changed by document method ``setMetadata()``. Supports incremental saves.
* A PDF's bookmarks (or table of contents) can now be deleted, set or changed with the entries of a list using document method ``setToC(list)``. Supports incremental saves.