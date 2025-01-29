.. include:: header.rst

.. _TextPage:

================
TextPage
================

This class represents text and images shown on a document page. All :ref:`MuPDF document types<Supported_File_Types>` are supported.

The usual ways to create a textpage are :meth:`DisplayList.get_textpage` and :meth:`Page.get_textpage`. Because there is a limited set of methods in this class, there exist wrappers in :ref:`Page` which are handier to use. The last column of this table shows these corresponding :ref:`Page` methods.

For a description of what this class is all about, see Appendix 2.

======================== ================================ ==============================
**Method**               **Description**                  page get_text or search method
======================== ================================ ==============================
:meth:`~.extractText`    extract plain text               "text"
:meth:`~.extractTEXT`    synonym of previous              "text"
:meth:`~.extractBLOCKS`  plain text grouped in blocks     "blocks"
:meth:`~.extractWORDS`   all words with their bbox        "words"
:meth:`~.extractHTML`    page content in HTML format      "html"
:meth:`~.extractXHTML`   page content in XHTML format     "xhtml"
:meth:`~.extractXML`     page text in XML format          "xml"
:meth:`~.extractDICT`    page content in *dict* format    "dict"
:meth:`~.extractJSON`    page content in JSON format      "json"
:meth:`~.extractRAWDICT` page content in *dict* format    "rawdict"
:meth:`~.extractRAWJSON` page content in JSON format      "rawjson"
:meth:`~.search`         Search for a string in the page  :meth:`Page.search_for`
======================== ================================ ==============================

**Class API**

.. class:: TextPage

   .. method:: extractText(sort=False)

   .. method:: extractTEXT(sort=False)

      Return a string of the page's complete text. The text is UTF-8 unicode and in the same sequence as specified at the time of document creation.

      :arg bool sort: (new in v1.19.1) sort the output by vertical, then horizontal coordinates. In many cases, this should suffice to generate a "natural" reading order.

      :rtype: str


   .. method:: extractBLOCKS

      Textpage content as a list of text lines grouped by block. Each list items looks like this::

         (x0, y0, x1, y1, "lines in the block", block_no, block_type)

      The first four entries are the block's bbox coordinates, *block_type* is 1 for an image block, 0 for text. *block_no* is the block sequence number. Multiple text lines are joined via line breaks.

      For an image block, its bbox and a text line with some image meta information is included -- **not the image content**.

      This is a high-speed method with just enough information to output plain text in desired reading sequence.

      :rtype: list

   .. method:: extractWORDS(delimiters=None)

      * Changed in v1.23.5: added `delimiters` parameter

      Textpage content as a list of single words with bbox information. An item of this list looks like this::

         (x0, y0, x1, y1, "word", block_no, line_no, word_no)

      :arg str delimiters: (new in v1.23.5) use these characters as *additional* word separators. By default, all white spaces (including the non-breaking space `0xA0`) indicate start and end of a word. Now you can specify more characters causing this. For instance, the default will return `"john.doe@outlook.com"` as **one** word. If you specify `delimiters="@."` then the **four** words `"john"`, `"doe"`, `"outlook"`, `"com"` will be returned. Other possible uses include ignoring punctuation characters `delimiters=string.punctuation`. The "word" strings will not contain any delimiting character.

      This is a high-speed method which e.g. allows extracting text from within given areas or recovering the text reading sequence.

      :rtype: list

   .. method:: extractHTML

      Textpage content as a string in HTML format. This version contains complete formatting and positioning information. Images are included (encoded as base64 strings). You need an HTML package to interpret the output in Python. Your internet browser should be able to adequately display this information, but see :ref:`HTMLQuality`.

      :rtype: str

   .. method:: extractDICT(sort=False)

      Textpage content as a Python dictionary. Provides same information detail as HTML. See below for the structure.

      :arg bool sort: (new in v1.19.1) sort the output by vertical, then horizontal coordinates. In many cases, this should suffice to generate a "natural" reading order.

      :rtype: dict

   .. method:: extractJSON(sort=False)

      Textpage content as a JSON string. Created by `json.dumps(TextPage.extractDICT())`. It is included for backlevel compatibility. You will probably use this method ever only for outputting the result to some file. The  method detects binary image data and converts them to base64 encoded strings.

      :arg bool sort: (new in v1.19.1) sort the output by vertical, then horizontal coordinates. In many cases, this should suffice to generate a "natural" reading order.

      :rtype: str

   .. method:: extractXHTML

      Textpage content as a string in XHTML format. Text information detail is comparable with :meth:`extractTEXT`, but also contains images (base64 encoded). This method makes no attempt to re-create the original visual appearance.

      :rtype: str

   .. method:: extractXML

      Textpage content as a string in XML format. This contains complete formatting information about every single character on the page: font, size, line, paragraph, location, color, etc. Contains no images. You need an XML package to interpret the output in Python.

      :rtype: str

   .. method:: extractRAWDICT(sort=False)

      Textpage content as a Python dictionary -- technically similar to :meth:`extractDICT`, and it contains that information as a subset (including any images). It provides additional detail down to each character, which makes using XML obsolete in many cases. See below for the structure.

      :arg bool sort: (new in v1.19.1) sort the output by vertical, then horizontal coordinates. In many cases, this should suffice to generate a "natural" reading order.

      :rtype: dict

   .. method:: extractRAWJSON(sort=False)

      Textpage content as a JSON string. Created by `json.dumps(TextPage.extractRAWDICT())`. You will probably use this method ever only for outputting the result to some file. The  method detects binary image data and converts them to base64 encoded strings.

      :arg bool sort: (new in v1.19.1) sort the output by vertical, then horizontal coordinates. In many cases, this should suffice to generate a "natural" reading order.

      :rtype: str

   .. method:: search(needle, quads=False)

      * Changed in v1.18.2

      Search for *string* and return a list of found locations.

      :arg str needle: the string to search for. Upper and lower cases will all match if needle consists of ASCII letters only -- it does not yet work for "Ä" versus "ä", etc.
      :arg bool quads: return quadrilaterals instead of rectangles.
      :rtype: list
      :returns: a list of :ref:`Rect` or :ref:`Quad` objects, each surrounding a found *needle* occurrence. As the search string may contain spaces, its parts may be found on different lines. In this case, more than one rectangle (resp. quadrilateral) are returned. **(Changed in v1.18.2)** The method **now supports dehyphenation**, so it will find e.g. "method", even if it was hyphenated in two parts "meth-" and "od" across two lines. The two returned rectangles will contain "meth" (no hyphen) and "od".

      .. note:: **Overview of changes in v1.18.2:**

        1. The `hit_max` parameter has been removed: all hits are always returned.
        2. The `rect` parameter of the :ref:`TextPage` is now respected: only text inside this area is examined. Only characters with fully contained bboxes are considered. The wrapper method :meth:`Page.search_for` correspondingly supports a *clip* parameter.
        3. **Hyphenated words** are now found.
        4. **Overlapping rectangles** in the same line are now automatically joined. We assume that such separations are an artifact created by multiple marked content groups, containing parts of the same search needle.

      Example Quad versus Rect: when searching for needle "pymupdf", then the corresponding entry will either be the blue rectangle, or, if *quads* was specified, the quad *Quad(ul, ur, ll, lr)*.

      .. image:: images/img-quads.*

   .. attribute:: rect

      The rectangle associated with the text page. This either equals the rectangle of the creating page or the `clip` parameter of :meth:`Page.get_textpage` and text extraction / searching methods.

      .. note:: The output of text searching and most text extractions **is restricted to this rectangle**. (X)HTML and XML output will however always extract the full page.

.. _textpagedict:

Structure of Dictionary Outputs
--------------------------------
Methods :meth:`TextPage.extractDICT`, :meth:`TextPage.extractJSON`, :meth:`TextPage.extractRAWDICT`, and :meth:`TextPage.extractRAWJSON` return dictionaries, containing the page's text and image content. The dictionary structures of all four methods are almost equal. They strive to map the text page's information hierarchy of blocks, lines, spans and characters as precisely as possible, by representing each of these by its own sub-dictionary:

* A **page** consists of a list of **block dictionaries**.
* A (text) **block** consists of a list of **line dictionaries**.
* A **line** consists of a list of **span dictionaries**.
* A **span** either consists of the text itself or, for the RAW variants, a list of **character dictionaries**.
* RAW variants: a **character** is a dictionary of its origin, bbox and unicode.

All PyMuPDF geometry objects herein (points, rectangles, matrices) are represented by there **"like"** formats: a :data:`rect_like` *tuple* is used instead of a :ref:`Rect`, etc. The reasons for this are performance and memory considerations:

* This code is written in C, where Python tuples can easily be generated. The geometry objects on the other hand are defined in Python source only. A conversion of each Python tuple into its corresponding geometry object would add significant -- and largely unnecessary -- execution time.
* A 4-tuple needs about 168 bytes, the corresponding :ref:`Rect` 472 bytes - almost three times the size. A "dict" dictionary for a text-heavy page contains 300+ bbox objects -- which thus require about 50 KB storage as 4-tuples versus 140 KB as :ref:`Rect` objects. A "rawdict" output for such a page will however contain **4 to 5 thousand** bboxes, so in this case we talk about 750 KB versus 2 MB.

Please also note, that only **bboxes** (= :data:`rect_like` 4-tuples) are returned, whereas a :ref:`TextPage` actually has the **full position information** -- in :ref:`Quad` format. The reason for this decision is again a memory consideration: a :data:`quad_like` needs 488 bytes (3 times the size of a :data:`rect_like`). Given the mentioned amounts of generated bboxes, returning :data:`quad_like` information would have a significant impact.

In the vast majority of cases, we are dealing with **horizontal text only**, where bboxes provide entirely sufficient information.

In addition, **the full quad information is not lost**: it can be recovered as needed for lines, spans, and characters by using the appropriate function from the following list:

* :meth:`recover_quad` -- the quad of a complete span
* :meth:`recover_span_quad` -- the quad of a character subset of a span
* :meth:`recover_line_quad` -- the quad of a line
* :meth:`recover_char_quad` -- the quad of a character

As mentioned, using these functions is ever only needed, if the text is **not written horizontally** -- `line["dir"] != (1, 0)` -- and you need the quad for text marker annotations (:meth:`Page.add_highlight_annot` and friends).


.. image:: images/img-textpage.*

..
  We used to do `:scale: 66` here, but current (2024-04-22) sphinx messes up
  the aspect ratio.

Page Dictionary
~~~~~~~~~~~~~~~~~

=============== ============================================
**Key**         **Value**
=============== ============================================
width           width of the `clip` rectangle *(float)*
height          height of the `clip` rectangle *(float)*
blocks          *list* of block dictionaries
=============== ============================================

Block Dictionaries
~~~~~~~~~~~~~~~~~~
Block dictionaries come in two different formats for **image blocks** and for **text blocks**.

**Image block:**

=============== ===============================================================
**Key**             **Value**
=============== ===============================================================
type            1 = image (``int``)
bbox            image bbox on page (:data:`rect_like`)
number          block count (``int``)
ext             image type (``str``), as file extension, see below
width           original image width (``int``)
height          original image height (``int``)
colorspace      colorspace component count (``int``)
xres            resolution in x-direction (``int``)
yres            resolution in y-direction (``int``)
bpc             bits per component (``int``)
transform       matrix transforming image rect to bbox (:data:`matrix_like`)
size            size of the image in bytes (``int``)
image           image content (``bytes``)
mask            image mask content (``bytes``) for transparent images
=============== ===============================================================

Possible values of the "ext" key are "bmp", "gif", "jpeg", "jpx" (JPEG 2000), "jxr" (JPEG XR), "png", "pnm", and "tiff".

.. note::

   1. An image block is generated for **all and every image occurrence** on the page. Hence there may be duplicates, if an image is shown at different locations.

   2. :ref:`TextPage` and corresponding method :meth:`Page.get_text` are **available for all document types**. Only for PDF documents, methods :meth:`Document.get_page_images` / :meth:`Page.get_images` offer some overlapping functionality as far as image lists are concerned. But both lists **may or may not** contain the same items. Any differences are most probably caused by one of the following:

       - "Inline" images (see page 214 of the :ref:`AdobeManual`) of a PDF page are contained in a textpage, but **do not appear** in :meth:`Page.get_images`.
       - Annotations may also contain images -- these will **not appear** in :meth:`Page.get_images`.
       - Image blocks in a textpage are generated for **every** image location -- whether or not there are any duplicates. This is in contrast to :meth:`Page.get_images`, which will list each image only once (per reference name).
       - Images mentioned in the page's :data:`object` definition will **always** appear in :meth:`Page.get_images` [#f1]_. But it may happen, that there is no "display" command in the page's :data:`contents` (erroneously or on purpose). In this case the image will **not appear** in the textpage.

   3. The image's "transformation matrix" is defined as the matrix, for which the expression `bbox / transform == pymupdf.Rect(0, 0, 1, 1)` is true, lookup details here: :ref:`ImageTransformation`.

   4. A transparent image may be accompanied by a mask image. This is stored under key `"mask"` and has the format of a `DeviceGray` PNG image. Otherwise the value of this key is ``None``. If present, you may be able to recover (an equivalent of) the original image -- i.e. with transparency -- by creating :ref:`Pixmap` objects from the "image", respectively "mask" values and overlay them. This is not guaranteed to always work because mask images come in multiple formats, of which not all qualify for the conditions under which overlaying Pixmaps are supported. Here is a code snippet:

   >>> base = pymupdf.Pixmap(block["image"])
   >>> mask = pymupdf.Pixmap(block["mask"])
   >>> result = pymupdf.Pixmap(base, mask)


**Text block:**

=============== ====================================================
**Key**             **Value**
=============== ====================================================
type            0 = text *(int)*
bbox            block rectangle, :data:`rect_like`
number          block count *(int)*
lines           *list* of text line dictionaries
=============== ====================================================

Line Dictionary
~~~~~~~~~~~~~~~~~

=============== =====================================================
**Key**             **Value**
=============== =====================================================
bbox            line rectangle, :data:`rect_like`
wmode           writing mode *(int)*: 0 = horizontal, 1 = vertical
dir             writing direction, :data:`point_like`
spans           *list* of span dictionaries
=============== =====================================================

The value of key *"dir"* is the **unit vector** `dir = (cosine, -sine)` of the angle, which the text has relative to the x-axis [#f2]_. See the following picture: The word in each quadrant (counter-clockwise from top-right to bottom-right) is rotated by 30, 120, 210 and 300 degrees respectively.

.. image:: images/img-line-dir.*
   :scale: 100

Span Dictionary
~~~~~~~~~~~~~~~~~

Spans contain the actual text. A line contains **more than one span only**, if it contains text with different font properties.

* Changed in version 1.14.17 Spans now also have a *bbox* key (again).
* Changed in version 1.17.6 Spans now also have an *origin* key.

=============== =====================================================================
**Key**             **Value**
=============== =====================================================================
bbox            span rectangle, :data:`rect_like`
origin          the first character's origin, :data:`point_like`
font            font name *(str)*
ascender        ascender of the font *(float)*
descender       descender of the font *(float)*
size            font size *(float)*
flags           font characteristics *(int)*
char_flags      char characteristics *(int)*
color           text color in sRGB format 0xRRGGBB *(int)*.
alpha           text opacity 0..255 *(int)*.
text            (only for :meth:`extractDICT`) text *(str)*
chars           (only for :meth:`extractRAWDICT`) *list* of character dictionaries
=============== =====================================================================

|history_begin|

*(New in version 1.25.3.0):* Added *"alpha"* item.

*(New in version 1.16.0):* *"color"* is the text color encoded in sRGB (int) format, e.g. 0xFF0000 for red. There are functions for converting this integer back to formats (r, g, b) (PDF with float values from 0 to 1) :meth:`sRGB_to_pdf`, or (R, G, B), :meth:`sRGB_to_rgb` (with integer values from 0 to 255).

*(New in v1.18.5):* *"ascender"* and *"descender"* are font properties, provided relative to :data:`fontsize` 1. Note that descender is a negative value. The following picture shows the relationship to other values and properties.

|history_end|

.. image:: images/img-asc-desc.*
   :scale: 60

These numbers may be used to compute the minimum height of a character (or span) -- as opposed to the standard height provided in the "bbox" values (which actually represents the **line height**). The following code recalculates the span bbox to have a height of **fontsize** exactly fitting the text inside:

>>> a = span["ascender"]
>>> d = span["descender"]
>>> r = pymupdf.Rect(span["bbox"])
>>> o = pymupdf.Point(span["origin"])  # its y-value is the baseline
>>> r.y1 = o.y - span["size"] * d / (a - d)
>>> r.y0 = r.y1 - span["size"]
>>> # r now is a rectangle of height 'fontsize'

.. caution:: The above calculation may deliver a **larger** height! This may e.g. happen for OCRed documents, where the risk of all sorts of text artifacts is high. MuPDF tries to come up with a reasonable bbox height, independently from the :data:`fontsize` found in the PDF. So please ensure that the height of `span["bbox"]` is **larger** than `span["size"]`.

.. note:: You may request PyMuPDF to do all of the above automatically by executing `pymupdf.TOOLS.set_small_glyph_heights(True)`. This sets a global parameter so that all subsequent text searches and text extractions are based on reduced glyph heights, where meaningful.

The following shows the original span rectangle in red and the rectangle with re-computed height in blue.

.. image:: images/img-span-rect.*
   :scale: 200


*"flags"* is an integer, which represents font properties except for the first bit 0. They are to be interpreted like this:

* bit 0: superscripted (:data:`TEXT_FONT_SUPERSCRIPT`) -- not a font property, detected by MuPDF code.
* bit 1: italic (:data:`TEXT_FONT_ITALIC`)
* bit 2: serifed (:data:`TEXT_FONT_SERIFED`)
* bit 3: monospaced (:data:`TEXT_FONT_MONOSPACED`)
* bit 4: bold (:data:`TEXT_FONT_BOLD`)

Test these characteristics like so:

>>> if flags & pymupdf.TEXT_FONT_BOLD & pymupdf.TEXT_FONT_ITALIC:
        print(f"{span['text']=} is bold and italic")


Bits 1 thru 4 are font properties, i.e. encoded in the font program. Please note, that this information is not necessarily correct or complete: fonts quite often contain wrong data here.

*"char_flags"* is an integer, which represents extra character properties:

* bit 0: strikeout.
* bit 1: underline.
* bit 2: synthetic (always 0, see char dictionary).
* bit 3: filled.
* bit 4: stroked.
* bit 5: clipped.

For example if not filled and not stroked (`if not (char_flags & 2**3 & 2**4):
...`) then the text will be invisible.

(`char_flags` is new in v1.25.2.)


Character Dictionary for :meth:`extractRAWDICT`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

=============== ===========================================================
**Key**             **Value**
=============== ===========================================================
origin          character's left baseline point, :data:`point_like`
bbox            character rectangle, :data:`rect_like`
synthetic       bool.
c               the character (unicode)
=============== ===========================================================

(`synthetic` is new in v1.25.3.)

This image shows the relationship between a character's bbox and its quad: |textpagechar|

.. |textpagechar| image:: images/img-textpage-char.*
   :align: top
   :scale: 66

.. rubric:: Footnotes

.. [#f1] Image specifications for a PDF page are done in a page's (sub-) :data:`dictionary`, called `/Resources`. Resource dictionaries can be **inherited** from any of the page's parent objects (usually the :data:`catalog` -- the top-level parent). The PDF creator may e.g. define one `/Resources` on file level, naming all images and / or all fonts ever used by any page. In these cases, :meth:`Page.get_images` and :meth:`Page.get_fonts` will consequently return the same lists for all pages. If desired, this situation can be reverted using :meth:`Page.clean_contents`. After execution, the page's object definition will show fonts and images that are actually used.

.. [#f2] The coordinate systems of MuPDF and PDF are different in that MuPDF uses the page's top-left point as `(0, 0)`. In PDF, this is the bottom-left point. Therefore, the positive direction for MuPDF's y-axis is **from top to bottom**. This causes the sign change for the sine value here: a **negative** value indicates anti-clockwise rotation of the text.

.. include:: footer.rst
