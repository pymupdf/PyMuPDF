.. include:: header.rst

.. _Device:

================
DeviceWrapper
================

The different format handlers (pdf, xps, etc.) interpret pages to a "device". Devices are the basis for everything that can be done with a page: rendering, text extraction and searching. The device type is determined by the selected construction method.

In |PyMuPDF| a device is represented by class `pymupdf.DeviceWrapper`, which wraps a low-level |MuPDF| device (available as its attribute `this`). Most users never create one directly: :meth:`DocumentWriter.begin_page` returns a `DeviceWrapper`, which is then passed to :meth:`Story.draw`.

**Class API**

.. class:: DeviceWrapper

   .. method:: __init__(pixmap, clip)

      Constructor for a pixel map (draw) device.

      :arg pixmap: the pixmap to render to.
      :type pixmap: :ref:`Pixmap`

      :arg clip: an `IRect` to restrict rendering to a certain area of the page. If the complete page is required, specify ``None``. This argument must always be given.
      :type clip: :data:`irect_like`

   .. method:: __init__(displaylist)

      Constructor for a display list device.

      :arg displaylist: a low-level |MuPDF| display list, i.e. the `this` attribute of a :ref:`DisplayList` (`mupdf.FzDisplayList`). A :ref:`DisplayList` object itself is not accepted.

   .. method:: __init__(textpage, flags)

      Constructor for a text page device.

      :arg textpage: a low-level |MuPDF| text page, i.e. the `this` attribute of a :ref:`TextPage` (`mupdf.FzStextPage`). A :ref:`TextPage` object itself is not accepted.

      :arg int flags: control the way how text is parsed into the text page. Currently 3 options can be coded into this parameter, see :ref:`TextPreserve`. To set these options use something like `flags=0 | TEXT_PRESERVE_LIGATURES | ...`. This argument must always be given.

   .. method:: __init__(device)

      Wrap an existing low-level |MuPDF| device (`mupdf.FzDevice`). This is how :meth:`DocumentWriter.begin_page` creates its return value.

      :arg device: a `mupdf.FzDevice`.

.. include:: footer.rst
