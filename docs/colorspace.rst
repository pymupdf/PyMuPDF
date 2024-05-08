.. include:: header.rst

.. _Colorspace:

================
Colorspace
================

Represents the color space of a :ref:`Pixmap`.


**Class API**

.. class:: Colorspace

   .. method:: __init__(self, n)

      Constructor

      :arg int n: A number identifying the colorspace. Possible values are :data:`CS_RGB`, :data:`CS_GRAY` and :data:`CS_CMYK`.

   .. attribute:: name

      The name identifying the colorspace. Example: *pymupdf.csCMYK.name = 'DeviceCMYK'*.

      :type: str

   .. attribute:: n

      The number of bytes required to define the color of one pixel. Example: *pymupdf.csCMYK.n == 4*.

      :type: int


    **Predefined Colorspaces**

    For saving some typing effort, there exist predefined colorspace objects for the three available cases.

    * :data:`csRGB`  = *pymupdf.Colorspace(pymupdf.CS_RGB)*
    * :data:`csGRAY` = *pymupdf.Colorspace(pymupdf.CS_GRAY)*
    * :data:`csCMYK` = *pymupdf.Colorspace(pymupdf.CS_CMYK)*

.. include:: footer.rst