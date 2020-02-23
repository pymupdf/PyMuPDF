.. _DisplayList:

================
DisplayList
================

DisplayList is a list containing drawing commands (text, images, etc.). The intent is two-fold:

1. as a caching-mechanism to reduce parsing of a page
2. as a data structure in multi-threading setups, where one thread parses the page and another one renders pages. This aspect is currently not supported by PyMuPDF.

A display list is populated with objects from a page, usually by executing :meth:`Page.getDisplayList`. There also exists an independent constructor.

"Replay" the list (once or many times) by invoking one of its methods :meth:`~DisplayList.run`, :meth:`~DisplayList.getPixmap` or :meth:`~DisplayList.getTextPage`.


================================= ============================================
**Method**                        **Short Description**
================================= ============================================
:meth:`~DisplayList.run`          Run a display list through a device.
:meth:`~DisplayList.getPixmap`    generate a pixmap
:meth:`~DisplayList.getTextPage`  generate a text page
:attr:`~DisplayList.rect`         mediabox of the display list
================================= ============================================


**Class API**

.. class:: DisplayList

   .. method:: __init__(self, mediabox)

      Create a new display list.

      :arg mediabox: The page's rectangle.
      :type mediabox: :ref:`Rect`

      :rtype: *DisplayList*

   .. method:: run(device, matrix, area)
    
      Run the display list through a device. The device will populate the display list with its "commands" (i.e. text extraction or image creation). The display list can later be used to "read" a page many times without having to re-interpret it from the document file.

      You will most probably instead use one of the specialized run methods below -- :meth:`getPixmap` or :meth:`getTextPage`.

      :arg device: Device
      :type device: :ref:`Device`

      :arg matrix: Transformation matrix to apply to the display list contents.
      :type matrix: :ref:`Matrix`

      :arg area: Only the part visible within this area will be considered when the list is run through the device.
      :type area: :ref:`Rect`

   .. index::
      pair: matrix; getPixmap
      pair: colorspace; getPixmap
      pair: clip; getPixmap
      pair: alpha; getPixmap

   .. method:: getPixmap(matrix=fitz.Identity, colorspace=fitz.csRGB, alpha=0, clip=None)

      Run the display list through a draw device and return a pixmap.

      :arg matrix: matrix to use. Default is the identity matrix.
      :type matrix: :ref:`Matrix`

      :arg colorspace: the desired colorspace. Default is RGB.
      :type colorspace: :ref:`Colorspace`

      :arg int alpha: determine whether or not (0, default) to include a transparency channel.

      :arg clip: an area of the full mediabox to which the pixmap should be restricted.
      :type clip: :ref:`IRect` or :ref:`Rect`

      :rtype: :ref:`Pixmap`
      :returns: pixmap of the display list.

   .. method:: getTextPage(flags)

      Run the display list through a text device and return a text page.

      :arg int flags: control which information is parsed into a text page. Default value in PyMuPDF is **3 = TEXT_PRESERVE_LIGATURES | TEXT_PRESERVE_WHITESPACE**, i.e. ligatures are **passed through**, white spaces are **passed through** (not translated to spaces), and images are **not included**. See :ref:`TextPreserve`.

      :rtype: :ref:`TextPage`
      :returns: text page of the display list.

   .. attribute:: rect

      Contains the display list's mediabox. This will equal the page's rectangle if it was created via :meth:`Page.getDisplayList`.

      :type: :ref:`Rect`
