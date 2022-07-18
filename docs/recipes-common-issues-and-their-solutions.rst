.. _RecipesCommonIssuesAndTheirSolutions:

==========================================
Recipes: Common Issues and their Solutions
==========================================



Changing Annotations: Unexpected Behaviour
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Problem
^^^^^^^^^
There are two scenarios:

1. **Updating** an annotation with PyMuPDF which was created by some other software.
2. **Creating** an annotation with PyMuPDF and later changing it with some other software.

In both cases you may experience unintended changes, like a different annotation icon or text font, the fill color or line dashing have disappeared, line end symbols have changed their size or even have disappeared too, etc.

Cause
^^^^^^
Annotation maintenance is handled differently by each PDF maintenance application. Some annotation types may not be supported, or not be supported fully or some details may be handled in a different way than in another application. **There is no standard.**

Almost always a PDF application also comes with its own icons (file attachments, sticky notes and stamps) and its own set of supported text fonts. For example:

* (Py-) MuPDF only supports these 5 basic fonts for 'FreeText' annotations: Helvetica, Times-Roman, Courier, ZapfDingbats and Symbol -- no italics / no bold variations. When changing a 'FreeText' annotation created by some other app, its font will probably not be recognized nor accepted and be replaced by Helvetica.

* PyMuPDF supports all PDF text markers (highlight, underline, strikeout, squiggly), but these types cannot be updated with Adobe Acrobat Reader.

In most cases there also exists limited support for line dashing which causes existing dashes to be replaced by straight lines. For example:

* PyMuPDF fully supports all line dashing forms, while other viewers only accept a limited subset.


Solutions
^^^^^^^^^^
Unfortunately there is not much you can do in most of these cases.

1. Stay with the same software for **creating and changing** an annotation.
2. When using PyMuPDF to change an "alien" annotation, try to **avoid** :meth:`Annot.update`. The following methods **can be used without it,** so that the original appearance should be maintained:

  * :meth:`Annot.set_rect` (location changes)
  * :meth:`Annot.set_flags` (annotation behaviour)
  * :meth:`Annot.set_info` (meta information, except changes to *content*)
  * :meth:`Annot.set_popup` (create popup or change its rect)
  * :meth:`Annot.set_optional_content` (add / remove reference to optional content information)
  * :meth:`Annot.set_open`
  * :meth:`Annot.update_file` (file attachment changes)

Misplaced Item Insertions on PDF Pages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Problem
^^^^^^^^^

You inserted an item (like an image, an annotation or some text) on an existing PDF page, but later you find it being placed at a different location than intended. For example an image should be inserted at the top, but it unexpectedly appears near the bottom of the page.

Cause
^^^^^^

The creator of the PDF has established a non-standard page geometry without keeping it "local" (as they should!). Most commonly, the PDF standard point (0,0) at *bottom-left* has been changed to the *top-left* point. So top and bottom are reversed -- causing your insertion to be misplaced.

The visible image of a PDF page is controlled by commands coded in a special mini-language. For an overview of this language consult "Operator Summary" on pp. 643 of the :ref:`AdobeManual`. These commands are stored in :data:`contents` objects as strings (*bytes* in PyMuPDF).

There are commands in that language, which change the coordinate system of the page for all the following commands. In order to limit the scope of such commands local, they must be wrapped by the command pair *q* ("save graphics state", or "stack") and *Q* ("restore graphics state", or "unstack").

.. highlight:: text

So the PDF creator did this::

    stream
    1 0 0 -1 0 792 cm    % <=== change of coordinate system:
    ...                  % letter page, top / bottom reversed
    ...                  % remains active beyond these lines
    endstream

where they should have done this::

    stream
    q                    % put the following in a stack
    1 0 0 -1 0 792 cm    % <=== scope of this is limited by Q command
    ...                  % here, a different geometry exists
    Q                    % after this line, geometry of outer scope prevails
    endstream

.. note::

   * In the mini-language's syntax, spaces and line breaks are equally accepted token delimiters.
   * Multiple consecutive delimiters are treated as one.
   * Keywords "stream" and "endstream" are inserted automatically -- not by the programmer.

.. highlight:: python

Solutions
^^^^^^^^^^

Since v1.16.0, there is the property :attr:`Page.is_wrapped`, which lets you check whether a page's contents are wrapped in that string pair.

If it is *False* or if you want to be on the safe side, pick one of the following:

1. The easiest way: in your script, do a :meth:`Page.clean_contents` before you do your first item insertion.
2. Pre-process your PDF with the MuPDF command line utility *mutool clean -c ...* and work with its output file instead.
3. Directly wrap the page's :data:`contents` with the stacking commands before you do your first item insertion.

**Solutions 1. and 2.** use the same technical basis and **do a lot more** than what is required in this context: they also clean up other inconsistencies or redundancies that may exist, multiple */Contents* objects will be concatenated into one, and much more.

.. note:: For **incremental saves,** solution 1. has an unpleasant implication: it will bloat the update delta, because it changes so many things and, in addition, stores the **cleaned contents uncompressed**. So, if you use :meth:`Page.clean_contents` you should consider **saving to a new file** with (at least) *garbage=3* and *deflate=True*.

**Solution 3.** is completely under your control and only does the minimum corrective action. There exists a handy low-level utility function which you can use for this. Suggested procedure:

* **Prepend** the missing stacking command by executing *fitz.TOOLS._insert_contents(page, b"q\n", False)*.
* **Append** an unstacking command by executing *fitz.TOOLS._insert_contents(page, b"\nQ", True)*.
* Alternatively, just use :meth:`Page._wrap_contents`, which executes the previous two functions.

.. note:: If small incremental update deltas are a concern, this approach is the most effective. Other contents objects are not touched. The utility method creates two new PDF :data:`stream` objects and inserts them before, resp. after the page's other :data:`contents`. We therefore recommend the following snippet to get this situation under control:

    >>> if not page.is_wrapped:
            page.wrap_contents()
    >>> # start inserting text, images or annotations here


Missing or Unreadable Extracted Text
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Fairly often, text extraction does not work text as you would expect: text may be missing at all, or may not appear in the reading sequence visible on your screen, or contain garbled characters (like a ? or a "TOFU" symbol), etc. This can be caused by a number of different problems.

Problem: no text is extracted
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Your PDF viewer does display text, but you cannot select it with your cursor, and text extraction delivers nothing.

Cause
^^^^^^
1. You may be looking at an image embedded in the PDF page (e.g. a scanned PDF).
2. The PDF creator used no font, but **simulated** text by painting it, using little lines and curves. E.g. a capital "D" could be painted by a line "|" and a left-open semi-circle, an "o" by an ellipse, and so on.

Solution
^^^^^^^^^^
Use an OCR software like `OCRmyPDF <https://pypi.org/project/ocrmypdf/>`_ to insert a hidden text layer underneath the visible page. The resulting PDF should behave as expected.

Problem: unreadable text
^^^^^^^^^^^^^^^^^^^^^^^^
Text extraction does not deliver the text in readable order, duplicates some text, or is otherwise garbled.

Cause
^^^^^^
1. The single characters are redable as such (no "<?>" symbols), but the sequence in which the text is **coded in the file** deviates from the reading order. The motivation behind may be technical or protection of data against unwanted copies.
2. Many "<?>" symbols occur, indicating MuPDF could not interpret these characters. The font may indeed be unsupported by MuPDF, or the PDF creator may haved used a font that displays readable text, but on purpose obfuscates the originating corresponding unicode character.

Solution
^^^^^^^^
1. Use layout preserving text extraction: ``python -m fitz gettext file.pdf``.
2. If other text extraction tools also don't work, then the only solution again is OCRing the page.