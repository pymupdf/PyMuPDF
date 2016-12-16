.. _Device:

================
Device
================

The different format handlers (pdf, xps, etc.) interpret pages to a "device". These devices are the basis for everything that can be done with a page: rendering, text extraction and searching. The device type is determined by the selected construction method.

**Class API**

.. class:: Device

   .. method:: __init__(self, object, clip)

      Constructor for either a pixel map or a display list device.

      :param `object`: one of ``Pixmap`` or ``DisplayList``
      :type `object`: :ref:`Pixmap` or :ref:`DisplayList`

      :param `clip`: An optional `IRect` for ``Pixmap`` devices only to restrict rendering to a certain area of the page. If the complete page is required, specify ``None``. For display list devices, this parameter must be omitted.
      :type `clip`: :ref:`IRect`

   .. method:: __init__(self, textsheet, textpage)

      Constructor for a text page device.

      :param `textsheet`: ``TextSheet`` object
      :type `textsheet`: :ref:`TextSheet`

      :param `textpage`: ``TextPage`` object
      :type `textpage`: :ref:`TextPage`

