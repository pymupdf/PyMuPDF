.. include:: header.rst

.. _ColorDatabase:

================
Color Database
================
Since the introduction of methods involving colors (like :meth:`Page.draw_circle`), a requirement may be to have access to predefined colors.

The fabulous GUI package `wxPython <https://wxpython.org/>`_ has a database of over 540 predefined RGB colors, which are given more or less memorizable names. Among them are not only standard names like "green" or "blue", but also "turquoise", "skyblue", and 100 (not only 50 ...) shades of "gray", etc.

We have taken the liberty to copy this database (a list of tuples) modified into PyMuPDF and make its colors available as PDF compatible float triples: for wxPython's *("WHITE", 255, 255, 255)* we return *(1, 1, 1)*, which can be directly used in *color* and *fill* parameters. We also accept any mixed case of "wHiTe" to find a color.

Function *getColor()*
------------------------
As the color database may not be needed very often, one additional import statement seems acceptable to get access to it::

    >>> # "getColor" is the only method you really need
    >>> from pymupdf.utils import getColor
    >>> getColor("aliceblue")
    (0.9411764705882353, 0.9725490196078431, 1.0)
    >>> #
    >>> # to get a list of all existing names
    >>> from pymupdf.utils import getColorList
    >>> cl = getColorList()
    >>> cl
    ['ALICEBLUE', 'ANTIQUEWHITE', 'ANTIQUEWHITE1', 'ANTIQUEWHITE2', 'ANTIQUEWHITE3',
    'ANTIQUEWHITE4', 'AQUAMARINE', 'AQUAMARINE1'] ...
    >>> #
    >>> # to see the full integer color coding
    >>> from pymupdf.utils import getColorInfoList
    >>> il = getColorInfoList()
    >>> il
    [('ALICEBLUE', 240, 248, 255), ('ANTIQUEWHITE', 250, 235, 215),
    ('ANTIQUEWHITE1', 255, 239, 219), ('ANTIQUEWHITE2', 238, 223, 204),
    ('ANTIQUEWHITE3', 205, 192, 176), ('ANTIQUEWHITE4', 139, 131, 120),
    ('AQUAMARINE', 127, 255, 212), ('AQUAMARINE1', 127, 255, 212)] ...


Printing the Color Database
----------------------------
If you want to actually see how the many available colors look like, use scripts `print by RGB <https://github.com/pymupdf/PyMuPDF-Utilities/blob/master/examples/print-rgb/print.py>`_ or `print by HSV <https://github.com/pymupdf/PyMuPDF-Utilities/blob/master/examples/print-hsv/print.py>`_ in the examples directory. They create PDFs (already existing in the same directory) with all these colors. Their only difference is sorting order: one takes the RGB values, the other one the Hue-Saturation-Values as sort criteria.
This is a screen print of what these files look like.

.. image:: images/img-colordb.*

.. include:: footer.rst