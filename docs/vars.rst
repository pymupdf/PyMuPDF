.. include:: header.rst

===============================
Constants and Enumerations
===============================
Constants and enumerations of :title:`MuPDF` as implemented by |PyMuPDF|. Each of the following values is accessible as `pymupdf.value`.


Constants
---------

.. py:data:: Base14_Fonts

    Predefined Python list of valid :ref:`Base-14-Fonts`.

    :type: list

.. py:data:: csRGB

    Predefined RGB colorspace *pymupdf.Colorspace(pymupdf.CS_RGB)*.

    :type: :ref:`Colorspace`

.. py:data:: csGRAY

    Predefined GRAY colorspace *pymupdf.Colorspace(pymupdf.CS_GRAY)*.

    :type: :ref:`Colorspace`

.. py:data:: csCMYK

    Predefined CMYK colorspace *pymupdf.Colorspace(pymupdf.CS_CMYK)*.

    :type: :ref:`Colorspace`

.. py:data:: CS_RGB

    1 -- Type of :ref:`Colorspace` is RGBA

    :type: int

.. py:data:: CS_GRAY

    2 -- Type of :ref:`Colorspace` is GRAY

    :type: int

.. py:data:: CS_CMYK

    3 -- Type of :ref:`Colorspace` is CMYK

    :type: int

.. py:data:: mupdf_version

    'x.xx.x' -- MuPDF version that is being used by PyMuPDF.

    :type: string

.. py:data:: mupdf_version_tuple

    MuPDF version as a tuple of integers, `(major, minor, patch)`.
    
    :type: tuple

.. py:data:: pymupdf_version

    'x.xx.x' -- PyMuPDF version.

    :type: string

.. py:data:: pymupdf_version_tuple

    PyMuPDF version as a tuple of integers, `(major, minor, patch)`.
    
    :type: tuple

.. py:data:: pymupdf_date

    ISO timestamp *YYYY-MM-DD HH:MM:SS* when these bindings were built.

    :type: string

.. py:data:: version

    (pymupdf_version, mupdf_version, timestamp) -- combined version information where `timestamp` is the generation point in time formatted as "YYYYMMDDhhmmss".

    :type: tuple

.. py:data:: VersionBind

    Legacy equivalent to `mupdf_version`.

.. py:data:: VersionFitz

    Legacy equivalent to `pymupdf_version`.

.. py:data:: VersionDate

    Legacy equivalent to `mupdf_version`.


.. _PermissionCodes:

Document Permissions
----------------------------

====================== =======================================================================
Code                   Permitted Action
====================== =======================================================================
PDF_PERM_PRINT         Print the document
PDF_PERM_MODIFY        Modify the document's contents
PDF_PERM_COPY          Copy or otherwise extract text and graphics
PDF_PERM_ANNOTATE      Add or modify text annotations and interactive form fields
PDF_PERM_FORM          Fill in forms and sign the document
PDF_PERM_ACCESSIBILITY Obsolete, always permitted
PDF_PERM_ASSEMBLE      Insert, rotate, or delete pages, bookmarks, thumbnail images
PDF_PERM_PRINT_HQ      High quality printing
====================== =======================================================================

.. _OptionalContentCodes:

PDF Optional Content Codes
----------------------------

====================== =======================================================================
Code                   Meaning
====================== =======================================================================
PDF_OC_ON              Set an OCG to ON temporarily
PDF_OC_TOGGLE          Toggle OCG status temporarily
PDF_OC_OFF             Set an OCG to OFF temporarily
====================== =======================================================================

.. _EncryptionMethods:

PDF encryption method codes
----------------------------

=================== ====================================================
Code                Meaning
=================== ====================================================
PDF_ENCRYPT_KEEP    do not change
PDF_ENCRYPT_NONE    remove any encryption
PDF_ENCRYPT_RC4_40  RC4 40 bit
PDF_ENCRYPT_RC4_128 RC4 128 bit
PDF_ENCRYPT_AES_128 *Advanced Encryption Standard* 128 bit
PDF_ENCRYPT_AES_256 *Advanced Encryption Standard* 256 bit
PDF_ENCRYPT_UNKNOWN unknown
=================== ====================================================

.. _FontExtensions:

Font File Extensions
-----------------------
The table show file extensions you should use when saving fontfile buffers extracted from a PDF. This string is returned by :meth:`Document.get_page_fonts`, :meth:`Page.get_fonts` and :meth:`Document.extract_font`.

==== ============================================================================
Ext  Description
==== ============================================================================
ttf  TrueType font
pfa  Postscript for ASCII font (various subtypes)
cff  Type1C font (compressed font equivalent to Type1)
cid  character identifier font (postscript format)
otf  OpenType font
n/a  not extractable, e.g. :ref:`Base-14-Fonts`, Type 3 fonts and others
==== ============================================================================

.. _TextAlign:

Text Alignment
-----------------------
.. py:data:: TEXT_ALIGN_LEFT

    0 -- align left.

.. py:data:: TEXT_ALIGN_CENTER

    1 -- align center.

.. py:data:: TEXT_ALIGN_RIGHT

    2 -- align right.

.. py:data:: TEXT_ALIGN_JUSTIFY

    3 -- align justify.

.. _TextPreserve:

.. _FontProperties:

Font Properties
-----------------------
Please note that the following bits are derived from what a font has to say about its properties. It may not be (and quite often is not) correct.

.. py:data:: TEXT_FONT_SUPERSCRIPT

    1 -- the character or span is a superscript. This property is computed by MuPDF and not part of any font information.

.. py:data:: TEXT_FONT_ITALIC

    2 -- the font is italic.

.. py:data:: TEXT_FONT_SERIFED

    4 -- the font is serifed.

.. py:data:: TEXT_FONT_MONOSPACED

    8 -- the font is mono-spaced.

.. py:data:: TEXT_FONT_BOLD

    16 -- the font is bold.

Text Extraction Flags
---------------------
Option bits controlling the amount of data, that are parsed into a :ref:`TextPage`.

For the PyMuPDF programmer, some combination (using Python's `|` operator, or simply use `+`) of these values are aggregated in the ``flags`` integer, a parameter of all text search and text extraction methods. Depending on the individual method, different default combinations of the values are used. Please use a value that meets your situation. Especially make sure to switch off image extraction unless you really need them. The impact on performance and memory is significant!

.. py:data:: TEXT_PRESERVE_LIGATURES

    1 -- If set, ligatures are passed through to the application in their original form. Otherwise ligatures are expanded into their constituent parts, e.g. the ligature "ffi" is expanded into three  eparate characters f, f and i. Default is "on" in PyMuPDF. MuPDF supports the following 7 ligatures: "ff", "fi", "fl", "ffi", "ffl", , "ft", "st".

.. py:data:: TEXT_PRESERVE_WHITESPACE

    2 -- If set, whitespace is passed through. Otherwise any type of horizontal whitespace (including horizontal tabs) will be replaced with space characters of variable width. Default is "on" in PyMuPDF.

.. py:data:: TEXT_PRESERVE_IMAGES

    4 -- If set, then images will be stored in the :ref:`TextPage`. This causes the presence of (usually large!) binary image content in the output of text extractions of types "blocks", "dict", "json", "rawdict", "rawjson", "html", and "xhtml" and is the default there. If used with "blocks" however, only image metadata will be returned, not the image itself.

.. py:data:: TEXT_INHIBIT_SPACES

    8 -- If set, Mupdf will not try to add missing space characters where there are large gaps between characters. In PDF, the creator often does not insert spaces to point to the next character's position, but will provide the direct location address. The default in PyMuPDF is "off" -- so spaces **will be generated**.

.. py:data:: TEXT_DEHYPHENATE

    16 -- Ignore hyphens at line ends and join with next line. Used internally with the text search functions. However, it is generally available: if on, text extractions will return joined text lines (or spans) with the ending hyphen of the first line eliminated. So two separate spans **"first meth-"** and **"od leads to wrong results"** on different lines will be joined to one span **"first method leads to wrong results"** and correspondingly updated bboxes: the characters of the resulting span will no longer have identical y-coordinates.

.. py:data:: TEXT_PRESERVE_SPANS

    32 -- Generate a new line for every span. Not used ("off") in PyMuPDF, but available for your use. Every line in "dict", "json", "rawdict", "rawjson" will contain exactly one span.

.. py:data:: TEXT_MEDIABOX_CLIP

    64 -- Characters entirely outside a page's **mediabox** or contained in other "clipped" areas will be ignored. This is default in PyMuPDF.

.. py:data:: TEXT_CID_FOR_UNKNOWN_UNICODE

    128 -- Use raw character codes instead of U+FFFD. This is the default for **text extraction** in PyMuPDF. If you **want to detect** when encoding information is missing or uncertain, toggle this flag and scan for the presence of U+FFFD (= `chr(0xfffd)`) code points in the resulting text.

.. py:data:: TEXT_ACCURATE_BBOXES

    512 -- Ignore metric values of all fonts when computing character boundary boxes -- most prominently the `ascender <https://en.wikipedia.org/wiki/Ascender_(typography)>`_ and `descender <https://en.wikipedia.org/wiki/Descender>`_ values. Instead, follow the drawing commands of each character's glyph and compute its rectangle hull. This is the smallest rectangle wrapping all points used for drawing the visual appearance - see the :ref:`Shape` class for understanding the background. This will especially result in individual character heights. For instance a (white) space will have a **bbox of height 0** (because nothing is drawn) -- in contrast to the non-zero boundary box generated when using font metrics. This option may be useful to cope with getting meaningful boundary boxes even for fonts containing errors. Its use will slow down text extraction somewhat because of the incurred computational effort.

.. py:data:: TEXT_IGNORE_ACTUALTEXT

    2048 -- Ignore built-in differences between text appearing in e.g. PDF viewers versus text stored in the PDF. See :ref:`AdobeManual`, page 615 for background. If set, the **stored** ("replacement" text) is ignored in favor of the displayed text.

.. py:data:: TEXT_COLLECT_STRUCTURE

    256 -- Not supported.

.. py:data:: TEXT_ACCURATE_BBOXES

    512 -- Calculates exact bboxes for each glyph, instead of relying on the information in the font or PDF document.

.. py:data:: TEXT_COLLECT_VECTORS

    1024 -- Not supported.

.. py:data:: TEXT_IGNORE_ACTUALTEXT

    2048 -- Do not use ActualText replacement if present.

.. py:data:: TEXT_STEXT_SEGMENT

    4096 -- Attempt to segment page into different regions.

The following constants represent the default combinations of the above for text extraction and searching:

.. py:data:: TEXTFLAGS_TEXT

    `TEXT_PRESERVE_LIGATURES | TEXT_PRESERVE_WHITESPACE | TEXT_MEDIABOX_CLIP | TEXT_CID_FOR_UNKNOWN_UNICODE`

.. py:data:: TEXTFLAGS_WORDS

    `TEXT_PRESERVE_LIGATURES | TEXT_PRESERVE_WHITESPACE | TEXT_MEDIABOX_CLIP | TEXT_CID_FOR_UNKNOWN_UNICODE`

.. py:data:: TEXTFLAGS_BLOCKS

    `TEXT_PRESERVE_LIGATURES | TEXT_PRESERVE_WHITESPACE | TEXT_MEDIABOX_CLIP | TEXT_CID_FOR_UNKNOWN_UNICODE`

.. py:data:: TEXTFLAGS_DICT

    `TEXT_PRESERVE_LIGATURES | TEXT_PRESERVE_WHITESPACE | TEXT_MEDIABOX_CLIP | TEXT_PRESERVE_IMAGES | TEXT_CID_FOR_UNKNOWN_UNICODE`

.. py:data:: TEXTFLAGS_RAWDICT

    `TEXT_PRESERVE_LIGATURES | TEXT_PRESERVE_WHITESPACE | TEXT_MEDIABOX_CLIP | TEXT_PRESERVE_IMAGES | TEXT_CID_FOR_UNKNOWN_UNICODE`

.. py:data:: TEXTFLAGS_HTML

    `TEXT_PRESERVE_LIGATURES | TEXT_PRESERVE_WHITESPACE | TEXT_MEDIABOX_CLIP | TEXT_PRESERVE_IMAGES | TEXT_CID_FOR_UNKNOWN_UNICODE`

.. py:data:: TEXTFLAGS_XHTML

    `TEXT_PRESERVE_LIGATURES | TEXT_PRESERVE_WHITESPACE | TEXT_MEDIABOX_CLIP | TEXT_PRESERVE_IMAGES | TEXT_CID_FOR_UNKNOWN_UNICODE`

.. py:data:: TEXTFLAGS_XML

    `TEXT_PRESERVE_LIGATURES | TEXT_PRESERVE_WHITESPACE | TEXT_MEDIABOX_CLIP | TEXT_CID_FOR_UNKNOWN_UNICODE`

.. py:data:: TEXTFLAGS_SEARCH

    `TEXT_PRESERVE_WHITESPACE | TEXT_MEDIABOX_CLIP | TEXT_DEHYPHENATE`


.. _linkDest Kinds:

Link Destination Kinds
-----------------------
Possible values of :attr:`linkDest.kind` (link destination kind).

.. py:data:: LINK_NONE

    0 -- No destination. Indicates a dummy link.

    :type: int

.. py:data:: LINK_GOTO

    1 -- Points to a place in this document.

    :type: int

.. py:data:: LINK_URI

    2 -- Points to a URI -- typically a resource specified with internet syntax.
    
    * PyMuPDF treats any external link that contains a colon and does not start
      with `file:`, as `LINK_URI`.

    :type: int

.. py:data:: LINK_LAUNCH

    3 -- Launch (open) another file (of any "executable" type).
    
    * |PyMuPDF| treats any external link that starts with `file:` or doesn't
      contain a colon, as `LINK_LAUNCH`.

    :type: int

.. py:data:: LINK_NAMED

    4 -- points to a named location.

    :type: int

.. py:data:: LINK_GOTOR

    5 -- Points to a place in another PDF document.

    :type: int

.. _linkDest Flags:

Link Destination Flags
-------------------------

.. Note:: The rightmost byte of this integer is a bit field, so test the truth of these bits with the *&* operator.

.. py:data:: LINK_FLAG_L_VALID

    1  (bit 0) Top left x value is valid

    :type: bool

.. py:data:: LINK_FLAG_T_VALID

    2  (bit 1) Top left y value is valid

    :type: bool

.. py:data:: LINK_FLAG_R_VALID

    4  (bit 2) Bottom right x value is valid

    :type: bool

.. py:data:: LINK_FLAG_B_VALID

    8  (bit 3) Bottom right y value is valid

    :type: bool

.. py:data:: LINK_FLAG_FIT_H

    16 (bit 4) Horizontal fit

    :type: bool

.. py:data:: LINK_FLAG_FIT_V

    32 (bit 5) Vertical fit

    :type: bool

.. py:data:: LINK_FLAG_R_IS_ZOOM

    64 (bit 6) Bottom right x is a zoom figure

    :type: bool


Annotation Related Constants
-----------------------------
See chapter 8.4.5, pp. 615 of the :ref:`AdobeManual` for details.

.. _AnnotationTypes:

Annotation Types
~~~~~~~~~~~~~~~~~
These identifiers also cover **links** and **widgets**: the PDF specification technically handles them all in the same way, whereas **MuPDF** (and PyMuPDF) treats them as three basically different types of objects.

::

    PDF_ANNOT_TEXT 0
    PDF_ANNOT_LINK 1  # <=== Link object in PyMuPDF
    PDF_ANNOT_FREE_TEXT 2
    PDF_ANNOT_LINE 3
    PDF_ANNOT_SQUARE 4
    PDF_ANNOT_CIRCLE 5
    PDF_ANNOT_POLYGON 6
    PDF_ANNOT_POLY_LINE 7
    PDF_ANNOT_HIGHLIGHT 8
    PDF_ANNOT_UNDERLINE 9
    PDF_ANNOT_SQUIGGLY 10
    PDF_ANNOT_STRIKE_OUT 11
    PDF_ANNOT_REDACT 12
    PDF_ANNOT_STAMP 13
    PDF_ANNOT_CARET 14
    PDF_ANNOT_INK 15
    PDF_ANNOT_POPUP 16
    PDF_ANNOT_FILE_ATTACHMENT 17
    PDF_ANNOT_SOUND 18
    PDF_ANNOT_MOVIE 19
    PDF_ANNOT_RICH_MEDIA 20
    PDF_ANNOT_WIDGET 21  # <=== Widget object in PyMuPDF
    PDF_ANNOT_SCREEN 22
    PDF_ANNOT_PRINTER_MARK 23
    PDF_ANNOT_TRAP_NET 24
    PDF_ANNOT_WATERMARK 25
    PDF_ANNOT_3D 26
    PDF_ANNOT_PROJECTION 27
    PDF_ANNOT_UNKNOWN -1

.. _AnnotationFlags:

Annotation Flag Bits
~~~~~~~~~~~~~~~~~~~~~
::

    PDF_ANNOT_IS_INVISIBLE 1 << (1-1)
    PDF_ANNOT_IS_HIDDEN 1 << (2-1)
    PDF_ANNOT_IS_PRINT 1 << (3-1)
    PDF_ANNOT_IS_NO_ZOOM 1 << (4-1)
    PDF_ANNOT_IS_NO_ROTATE 1 << (5-1)
    PDF_ANNOT_IS_NO_VIEW 1 << (6-1)
    PDF_ANNOT_IS_READ_ONLY 1 << (7-1)
    PDF_ANNOT_IS_LOCKED 1 << (8-1)
    PDF_ANNOT_IS_TOGGLE_NO_VIEW 1 << (9-1)
    PDF_ANNOT_IS_LOCKED_CONTENTS 1 << (10-1)

.. _AnnotationLineEnds:

Annotation Line Ending Styles
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
::

    PDF_ANNOT_LE_NONE 0
    PDF_ANNOT_LE_SQUARE 1
    PDF_ANNOT_LE_CIRCLE 2
    PDF_ANNOT_LE_DIAMOND 3
    PDF_ANNOT_LE_OPEN_ARROW 4
    PDF_ANNOT_LE_CLOSED_ARROW 5
    PDF_ANNOT_LE_BUTT 6
    PDF_ANNOT_LE_R_OPEN_ARROW 7
    PDF_ANNOT_LE_R_CLOSED_ARROW 8
    PDF_ANNOT_LE_SLASH 9


Widget Constants
-----------------

.. _WidgetTypes:

Widget Types (*field_type*)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
::

    PDF_WIDGET_TYPE_UNKNOWN 0
    PDF_WIDGET_TYPE_BUTTON 1
    PDF_WIDGET_TYPE_CHECKBOX 2
    PDF_WIDGET_TYPE_COMBOBOX 3
    PDF_WIDGET_TYPE_LISTBOX 4
    PDF_WIDGET_TYPE_RADIOBUTTON 5
    PDF_WIDGET_TYPE_SIGNATURE 6
    PDF_WIDGET_TYPE_TEXT 7

Text Widget Subtypes (*text_format*)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
::

    PDF_WIDGET_TX_FORMAT_NONE 0
    PDF_WIDGET_TX_FORMAT_NUMBER 1
    PDF_WIDGET_TX_FORMAT_SPECIAL 2
    PDF_WIDGET_TX_FORMAT_DATE 3
    PDF_WIDGET_TX_FORMAT_TIME 4


Widget flags (*field_flags*)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Common to all field types**::

    PDF_FIELD_IS_READ_ONLY 1
    PDF_FIELD_IS_REQUIRED 1 << 1
    PDF_FIELD_IS_NO_EXPORT 1 << 2

**Text widgets**::

    PDF_TX_FIELD_IS_MULTILINE  1 << 12
    PDF_TX_FIELD_IS_PASSWORD  1 << 13
    PDF_TX_FIELD_IS_FILE_SELECT  1 << 20
    PDF_TX_FIELD_IS_DO_NOT_SPELL_CHECK  1 << 22
    PDF_TX_FIELD_IS_DO_NOT_SCROLL  1 << 23
    PDF_TX_FIELD_IS_COMB  1 << 24
    PDF_TX_FIELD_IS_RICH_TEXT  1 << 25

**Button widgets**::

    PDF_BTN_FIELD_IS_NO_TOGGLE_TO_OFF  1 << 14
    PDF_BTN_FIELD_IS_RADIO  1 << 15
    PDF_BTN_FIELD_IS_PUSHBUTTON  1 << 16
    PDF_BTN_FIELD_IS_RADIOS_IN_UNISON  1 << 25

**Choice widgets**::

    PDF_CH_FIELD_IS_COMBO  1 << 17
    PDF_CH_FIELD_IS_EDIT  1 << 18
    PDF_CH_FIELD_IS_SORT  1 << 19
    PDF_CH_FIELD_IS_MULTI_SELECT  1 << 21
    PDF_CH_FIELD_IS_DO_NOT_SPELL_CHECK  1 << 22
    PDF_CH_FIELD_IS_COMMIT_ON_SEL_CHANGE  1 << 26


.. _BlendModes:

PDF Standard Blend Modes
----------------------------

For an explanation see :ref:`AdobeManual`, page 324::

    PDF_BM_Color "Color"
    PDF_BM_ColorBurn "ColorBurn"
    PDF_BM_ColorDodge "ColorDodge"
    PDF_BM_Darken "Darken"
    PDF_BM_Difference "Difference"
    PDF_BM_Exclusion "Exclusion"
    PDF_BM_HardLight "HardLight"
    PDF_BM_Hue "Hue"
    PDF_BM_Lighten "Lighten"
    PDF_BM_Luminosity "Luminosity"
    PDF_BM_Multiply "Multiply"
    PDF_BM_Normal "Normal"
    PDF_BM_Overlay "Overlay"
    PDF_BM_Saturation "Saturation"
    PDF_BM_Screen "Screen"
    PDF_BM_SoftLight "Softlight"


.. _StampIcons:

Stamp Annotation Icons
----------------------------
MuPDF has defined the following icons for **rubber stamp** annotations::

    STAMP_Approved 0
    STAMP_AsIs 1
    STAMP_Confidential 2
    STAMP_Departmental 3
    STAMP_Experimental 4
    STAMP_Expired 5
    STAMP_Final 6
    STAMP_ForComment 7
    STAMP_ForPublicRelease 8
    STAMP_NotApproved 9
    STAMP_NotForPublicRelease 10
    STAMP_Sold 11
    STAMP_TopSecret 12
    STAMP_Draft 13

.. include:: footer.rst
