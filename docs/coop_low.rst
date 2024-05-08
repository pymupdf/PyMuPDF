.. include:: header.rst

.. _cooperation:

===============================================================
Working together: DisplayList and TextPage
===============================================================
Here are some instructions on how to use these classes together.

In some situations, performance improvements may be achievable, when you fall back to the detail level explained here.

Create a DisplayList
---------------------
A :ref:`DisplayList` represents an interpreted document page. Methods for pixmap creation, text extraction and text search are  -- behind the curtain -- all using the page's display list to perform their tasks. If a page must be rendered several times (e.g. because of changed zoom levels), or if text search and text extraction should both be performed, overhead can be saved, if the display list is created only once and then used for all other tasks.

>>> dl = page.get_displaylist()              # create the display list

You can also create display lists for many pages "on stack" (in a list), may be during document open, during idling times, or you store it when a page is visited for the first time (e.g. in GUI scripts).

Note, that for everything what follows, only the display list is needed -- the corresponding :ref:`Page` object could have been deleted.

Generate Pixmap
------------------
The following creates a Pixmap from a :ref:`DisplayList`. Parameters are the same as for :meth:`Page.get_pixmap`.

>>> pix = dl.get_pixmap()                    # create the page's pixmap

The execution time of this statement may be up to 50% shorter than that of :meth:`Page.get_pixmap`.

Perform Text Search
---------------------
With the display list from above, we can also search for text.

For this we need to create a :ref:`TextPage`.

>>> tp = dl.get_textpage()                    # display list from above
>>> rlist = tp.search("needle")              # look up "needle" locations
>>> for r in rlist:                          # work with the found locations, e.g.
        pix.invert_irect(r.irect)             # invert colors in the rectangles

Extract Text
----------------
With the same :ref:`TextPage` object from above, we can now immediately use any or all of the 5 text extraction methods.

.. note:: Above, we have created our text page without argument. This leads to a default argument of 3 (:data:`ligatures` and white-space are preserved), IAW images will **not** be extracted -- see below.

>>> txt  = tp.extractText()                  # plain text format
>>> json = tp.extractJSON()                  # json format
>>> html = tp.extractHTML()                  # HTML format
>>> xml  = tp.extractXML()                   # XML format
>>> xml  = tp.extractXHTML()                 # XHTML format

Further Performance improvements
---------------------------------
Pixmap
~~~~~~~
As explained in the :ref:`Page` chapter:

If you do not need transparency set *alpha = 0* when creating pixmaps. This will save 25% memory (if RGB, the most common case) and possibly 5% execution time (depending on the GUI software).

TextPage
~~~~~~~~~
If you do not need images extracted alongside the text of a page, you can set the following option:

>>> flags = pymupdf.TEXT_PRESERVE_LIGATURES | pymupdf.TEXT_PRESERVE_WHITESPACE
>>> tp = dl.get_textpage(flags)

This will save ca. 25% overall execution time for the HTML, XHTML and JSON text extractions and **hugely** reduce the amount of storage (both, memory and disk space) if the document is graphics oriented.

If you however do need images, use a value of 7 for flags:

>>> flags = pymupdf.TEXT_PRESERVE_LIGATURES | pymupdf.TEXT_PRESERVE_WHITESPACE | pymupdf.TEXT_PRESERVE_IMAGES

.. include:: footer.rst
