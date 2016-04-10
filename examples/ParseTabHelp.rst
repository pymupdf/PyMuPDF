ParseTab Help
==============
File ParseTab.py contains one method ``ParseTab``. It is used to parse table data contained in a specified rectangle.

Call Pattern
-------------
``table = ParseTab(doc, page, rect, columns=None)``

Parameters and Returns
----------------------
* **doc:** if required, it must be a PyMuPDF document created by ``fitz.Document()``. Any document types (PDF, XPS, etc.) of MuPDF are supported.
* **page:** specifies a page in the document. This can be either a number, in which case it must be 0-based, or a PyMuPDF page object (created with the ``loadPage()`` method). If a page object is specified, the ``doc`` will not be used and can be specified as ``None``.
* **rect:** specifies the rectangle to be parsed. Must be specified as a 4-tuple (or list) of numbers, e.g. ``[x0, y0, x1, y1]``, where x0 and y0 define the upper left corner of the rectangle, and x1, y1 the bottom right corner. The numbers must be specified as pixel values. They may be floats or integers.
* **columns:** an optional list of horizontal pixel values which shall be used as delimiting columns. If omitted, columns are detected automatically, see below.
* **table:** contains a list of lists of strings upon return. If the parsing was not successfull for any reason, ``table`` will be an empty list. If successfull, ``len(table)`` will equal the number of lines, and ``len(table[0])`` will be the number of columns.

Dependencies
------------
PyMuPDF (fitz), sqlite3 and json are required.

sqlite3 and json are part of standard Python distributions.

See PyMuPDF's documentation for how to get and install it.

Usage
------
A simple example:

    ``import fitz``

    ``from ParseTab import ParseTab``

    ``doc = fitz.Document("example.pdf")``

    ``table = ParseTab(doc, 20, [0, 0, 500, 700])``

If you do other work with this page, you can invoke the parsing with a slightly better performance like this:

    ``import fitz``

    ``from ParseTab import ParseTab``

    ``doc = fitz.Document("example.pdf")``

    ``page = doc.loadPage(20)``

    ``table = ParseTab(None, page, [0, 0, 500, 700])``

In both cases, you somehow need to know, that the rectangle actually contains the wanted table. If you don't, but you do know certain keywords above and below your table, you can let PyMuPDF help you like this:

    ``rl1 = page.searchFor("above", hit_max = 1)``

    ``y_above = rl1[0].y1                       # bottom of hit rectangle 1``

    ``rl2 = page.searchFor("below", hit_max = 1)``

    ``y_below = rl2[0].y0                       # top of hit rectangle 2``

    ``table = ParseTab(None, page, [0, y_above, 9999, y_below])``

``rl1`` and ``rl2`` are lists of rectangles surrounding the respective search strings. Because we have limited both searches to 1 occurrence, at most one rectangle will be contained in each.

The rectangles' properties ``y0`` and ``y1`` denote the top and the bottom, respectively. Here we used this information together with x values, that just mean "the whole width is valid".

Because no ``columns`` were specified, columns will be detected automatically. This is done by collecting all different left coordinates of all text pieces (so-called "spans") in the parsed rectangle.

In many cases, this logic may be sufficient - even though several unnecessary columns will usually result. If you do not like this behaviour (and if you do know where your real columns start!), supply a ``columns = [c1, c2, ...]`` parameter. If the parsed rectangle's top-left x coordinate x0 is smaller than c1, the tuple ``[x0, c1, c2, ...]`` will be used.

All encountered spans will now be distributed according to their left x coordinate. E.g. if ``c1 <= x < c2``, the correspondin text will land in column 1. If this is also the case for more spans in the same line, they will be concatenated to x.

Notes
------
* Any differences in fonts, point sizes, changes between bold and italic, etc. will be ignored, and normal plain text will result.
* This method does not directly support parsing tables that are spread over more than one page. You must use your own logic to combine sub tables from single pages.
* The example program ``TableExtract.py`` shows how all this works together by extracting a certain table in Adobe's PDF manual.
* Best use of this method can be made when it is combined with a graphical document viewer. This gives you the chance to graphically determine a table's rectangle and its columns. An example for this is ``wxTableExtract.py`` in this directory.
* This is **not** an OCR program. It cannot detect text that is contained in images.
