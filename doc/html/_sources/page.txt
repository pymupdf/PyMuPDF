.. raw:: pdf

    PageBreak

.. _Page:

================
Page
================

Class representing one document page. A page object is created by :meth:`Document.loadPage` (or equivalently via indexing the document like ``doc[n]``).


======================== =========================================
**Method / Attribute**   **Short Description**
======================== =========================================
:meth:`Page.bound`       rectangle (mediabox) of the page
:meth:`Page.deleteAnnot` PDF only: delete an annotation
:meth:`Page.getLinks`    get all links
:meth:`Page.getPixmap`   create a ``Pixmap``
:meth:`Page.getText`     extract the text
:meth:`Page.run`         run a page through a device
:meth:`Page.searchFor`   search for a string
:meth:`Page.setRotation` PDF only: set page rotation
:attr:`Page.firstAnnot`  first :ref:`Annot` on the page
:attr:`Page.firstLink`   first :ref:`Link` on the page
:attr:`Page.number`      page number
:attr:`Page.parent`      the owning document object
:attr:`Page.rect`        rectangle (mediabox) of the page
:attr:`Page.rotation`    PDF only: page rotation
======================== =========================================

**Class API**

.. class:: Page

   .. method:: bound()

      Determine the rectangle ("mediabox", before transformation) of the page.

      :rtype: :ref:`Rect`

   .. attribute:: rect

      Contains the rectangle ("mediabox", before transformation) of the page. Same as result of method ``bound()``.

      :rtype: :ref:`Rect`

   .. method:: deleteAnnot(annot)

      PDF only: Delete the specified annotation from the page and (for all document types) return the next one.

      :param `annot`: the annotation to be deleted.
      :type `annot`: :ref:`Annot`
      :rtype: :ref:`Annot`
      :returns: the next annotation of the deleted one.

   .. method:: getLinks()

      Retrieves **all** links of a page.

      :rtype: list
      :returns: A list of dictionaries or ``[]``. The entries are in the order as specified during PDF generation.

   .. method:: getText(output = 'text')

      Retrieves the text of a page. Depending on the output parameter, the results of the :ref:`TextPage` extract methods are returned.

      If ``output = 'text'`` is specified, plain text is returned in the order as specified during PDF creation (which is not necessarily the normal reading order). As this may not always look like expected, consider using the example program ``PDF2TextJS.py``. It is based on ``extractJSON()`` and re-arranges text according to the Western reading layout convention "from top-left to bottom-right".

      :param `output`: A string indicating the requested text format, one of ``text`` (default), ``html``, ``json``, or ``xml``.

      :type `output`: string

      :rtype: string
      :returns: The page's text as one string.

   .. method:: getPixmap(matrix = fitz.Identity, colorspace = "RGB", clip = None, alpha = False)

     Creates a Pixmap from the page.

     :param `matrix`: A :ref:`Matrix` object. Default is the :ref:`Identity` matrix.
     :type `matrix`: :ref:`Matrix`

     :param `colorspace`: Defines the required colorspace, one of ``GRAY``, ``CMYK`` or ``RGB`` (default).
     :type `colorspace`: string

     :param `clip`: An ``Irect`` to restrict rendering of the page to the rectangle's area. If not specified, the complete page will be rendered.
     :type `clip`: :ref:`IRect`

     :param `alpha`: An bool indicating whether an alpha channel should be included in the pixmap. Leave it as ``False`` if you do not absolutely need transparency. This will save a lot of memory (25% in case of RGB).
     :type `alpha`: bool
     :rtype: :ref:`Pixmap`
     :returns: Pixmap of the page.


   .. method:: setRotation(rot)

      PDF only: Sets the rotation of the page.

      :param `rot`: An integer specifying the required rotation in degrees. Should be a (positive or negative) multiple of 90.
      :type `rot`: int
      :returns: zero if successfull, ``-1`` if not a PDF.


   .. method:: searchFor(text, hit_max = 16)

      Searches for ``text`` on a page. Identical to :meth:`TextPage.search`.

      :param `text`: Text to searched for. Upper / lower case is ignored.

      :type `text`: string

      :param `hit_max`: Maximum number of occurrences accepted.

      :type `hit_max`: int

      :rtype: list

      :returns: A list of :ref:`Rect` rectangles each of which surrounds one occurrence of ``text``.

   .. method:: run(dev, transform)

      Run a page through a device.

      :param `dev`: Device, obtained from one of the :ref:`Device` constructors.
      :type `dev`: :ref:`Device`

      :param `transform`: Transformation to apply to the page. Set it to :ref:`Identity` if no transformation is desired.
      :type `transform`: :ref:`Matrix`

   .. attribute:: rotation

      PDF only: contains the rotation of the page in degrees and ``-1`` for other document types.

      :rtype: int

   .. attribute:: firstLink

      Contains the first :ref:`Link` of a page (or ``None``).

      :rtype: :ref:`Link`

   .. attribute:: firstAnnot

      Contains the first :ref:`Annot` of a page (or ``None``).

      :rtype: :ref:`Annot`

   .. attribute:: number

      The page number.

      :rtype: int

   .. attribute:: parent

      The owning document object.

      :rtype: :ref:`Document`

