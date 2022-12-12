.. include:: header.rst

.. _Device:

================
Device
================

The different format handlers (pdf, xps, etc.) interpret pages to a "device". Devices are the basis for everything that can be done with a page: rendering, text extraction and searching. The device type is determined by the selected construction method.

**Class API**

.. class:: Device

   .. method:: __init__(self, object, clip)

      Constructor for either a pixel map or a display list device.

      :arg object: either a *Pixmap* or  a *DisplayList*.
      :type object: :ref:`Pixmap` or :ref:`DisplayList`

      :arg clip: An optional `IRect` for *Pixmap* devices to restrict rendering to a certain area of the page. If the complete page is required, specify *None*. For display list devices, this parameter must be omitted.
      :type clip: :ref:`IRect`

   .. method:: __init__(self, textpage, flags=0)

      Constructor for a text page device.

      :arg textpage: *TextPage* object
      :type textpage: :ref:`TextPage`

      :arg int flags: control the way how text is parsed into the text page. Currently 3 options can be coded into this parameter, see :ref:`TextPreserve`. To set these options use something like *flags=0 | TEXT_PRESERVE_LIGATURES | ...*.

.. include:: footer.rst
