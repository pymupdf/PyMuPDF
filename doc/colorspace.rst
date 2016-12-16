.. _Colorspace:

================
Colorspace
================

Represents the color space of a :ref:`Pixmap`.


**Class API**

.. class:: Colorspace

   .. method:: __init__(self, cno)

      Constructor

      :param `cno`: A number identifying the colorspace. Possible values are :data:`CS_RGB`, :data:`CS_GRAY` and :data:`CS_CMYK`.

      :type `cno`: int

   .. attribute:: name

      The name identifying the colorspace. Example: ``fitz.csCMYK.name = 'DeviceCMYK'``.

      :rtype: string

   .. attribute:: n

      The number of bytes required to define the color of one pixel. Example: ``fitz.csCMYK.n = 4``.

      :rtype: int


    **Predefined Colorspaces**

    For saving some typing effort, there exist predefined colorspace objects for the three available cases.

    * :data:`csRGB`  = ``fitz.Colorspace(fitz.CS_RGB)``
    * :data:`csGRAY` = ``fitz.Colorspace(fitz.CS_GRAY)``
    * :data:`csCMYK` = ``fitz.Colorspace(fitz.CS_CMYK)``