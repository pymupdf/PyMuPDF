===============================
Constants and Enumerations
===============================
Constants and enumerations of MuPDF as implemented by PyMuPDF. Each of the following variables is accessible as *fitz.variable*.


Constants
---------

.. py:data:: Base14_Fonts

    Predefined Python list of valid :ref:`Base-14-Fonts`.

    :rtype: list

.. py:data:: csRGB

    Predefined RGB colorspace *fitz.Colorspace(fitz.CS_RGB)*.

    :rtype: :ref:`Colorspace`

.. py:data:: csGRAY

    Predefined GRAY colorspace *fitz.Colorspace(fitz.CS_GRAY)*.

    :rtype: :ref:`Colorspace`

.. py:data:: csCMYK

    Predefined CMYK colorspace *fitz.Colorspace(fitz.CS_CMYK)*.

    :rtype: :ref:`Colorspace`

.. py:data:: CS_RGB

    1 -- Type of :ref:`Colorspace` is RGBA

    :rtype: int

.. py:data:: CS_GRAY

    2 -- Type of :ref:`Colorspace` is GRAY

    :rtype: int

.. py:data:: CS_CMYK

    3 -- Type of :ref:`Colorspace` is CMYK

    :rtype: int

.. py:data:: VersionBind

    'x.xx.x' -- version of PyMuPDF (these bindings)

    :rtype: string

.. py:data:: VersionFitz

    'x.xxx' -- version of MuPDF

    :rtype: string

.. py:data:: VersionDate

    ISO timestamp *YYYY-MM-DD HH:MM:SS* when these bindings were built.

    :rtype: string

.. Note:: The docstring of *fitz* contains information of the above which can be retrieved like so: *print(fitz.__doc__)*, and should look like: *PyMuPDF 1.10.0: Python bindings for the MuPDF 1.10 library, built on 2016-11-30 13:09:13*.

.. py:data:: version

    (VersionBind, VersionFitz, timestamp) -- combined version information where *timestamp* is the generation point in time formatted as "YYYYMMDDhhmmss".

    :rtype: tuple


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
The table show file extensions you should use when extracting fonts from a PDF file.

==== ============================================================================
Ext  Description
==== ============================================================================
ttf  TrueType font
pfa  Postscript for ASCII font (various subtypes)
cff  Type1C font (compressed font equivalent to Type1)
cid  character identifier font (postscript format)
otf  OpenType font
n/a  built-in font (:ref:`Base-14-Fonts` or CJK: cannot be extracted)
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

Preserve Text Flags
--------------------
Options controlling the amount of data a text device parses into a :ref:`TextPage`.

.. py:data:: TEXT_PRESERVE_LIGATURES

    1 -- If set, ligatures are passed through to the application in their original form. Otherwise ligatures are expanded into their constituent parts, e.g. the ligature ffi is expanded into three  eparate characters f, f and i.

.. py:data:: TEXT_PRESERVE_WHITESPACE

    2 -- If set, whitespace is passed through to the application in its original form. Otherwise any type of horizontal whitespace (including horizontal tabs) will be replaced with space characters of variable width.

.. py:data:: TEXT_PRESERVE_IMAGES

    4 -- If set, then images will be stored in the structured text structure.

.. py:data:: TEXT_INHIBIT_SPACES

    8 -- If set, we will not try to add missing space characters where there are large gaps between characters.

.. py:data:: TEXT_DEHYPHENATE

    16 -- Ignore hyphens at line ends and join with next line. Used mainly with search function

.. py:data:: TEXT_PRESERVE_SPANS

    32 -- Generate a new line for every span. Not used in PyMuPDF.


.. _linkDest Kinds:

Link Destination Kinds
-----------------------
Possible values of :attr:`linkDest.kind` (link destination kind). For details consult :ref:`AdobeManual`, chapter 8.2 on pp. 581.

.. py:data:: LINK_NONE

    0 -- No destination. Indicates a dummy link.

    :rtype: int

.. py:data:: LINK_GOTO

    1 -- Points to a place in this document.

    :rtype: int

.. py:data:: LINK_URI

    2 -- Points to a URI -- typically a resource specified with internet syntax.

    :rtype: int

.. py:data:: LINK_LAUNCH

    3 -- Launch (open) another file (of any "executable" type).

    :rtype: int

.. py:data:: LINK_NAMED

    4 -- points to a named location.

    :rtype: int

.. py:data:: LINK_GOTOR

    5 -- Points to a place in another PDF document.

    :rtype: int

.. _linkDest Flags:

Link Destination Flags
-------------------------

.. Note:: The rightmost byte of this integer is a bit field, so test the truth of these bits with the *&* operator.

.. py:data:: LINK_FLAG_L_VALID

    1  (bit 0) Top left x value is valid

    :rtype: bool

.. py:data:: LINK_FLAG_T_VALID

    2  (bit 1) Top left y value is valid

    :rtype: bool

.. py:data:: LINK_FLAG_R_VALID

    4  (bit 2) Bottom right x value is valid

    :rtype: bool

.. py:data:: LINK_FLAG_B_VALID

    8  (bit 3) Bottom right y value is valid

    :rtype: bool

.. py:data:: LINK_FLAG_FIT_H

    16 (bit 4) Horizontal fit

    :rtype: bool

.. py:data:: LINK_FLAG_FIT_V

    32 (bit 5) Vertical fit

    :rtype: bool

.. py:data:: LINK_FLAG_R_IS_ZOOM

    64 (bit 6) Bottom right x is a zoom figure

    :rtype: bool


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

For an explanation see :ref:`AdobeManual`, page 520::

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
