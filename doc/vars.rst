.. raw:: pdf

    PageBreak

===============================
Constants and Enumerations
===============================
Constants and enumerations of MuPDF as implemented by PyMuPDF. If your import statement was ``import fitz`` then each of the following variables is accessible as ``fitz.variable``.


Constants
---------

.. py:data:: csRGB

    Predefined RGB colorspace ``fitz.Colorspace(fitz.CS_RGB)``.

    :rtype: :ref:`Colorspace`

.. py:data:: csGRAY

    Predefined GRAY colorspace  ``fitz.Colorspace(fitz.CS_GRAY)``.

    :rtype: :ref:`Colorspace`

.. py:data:: csCMYK

    Predefined CMYK colorspace  ``fitz.Colorspace(fitz.CS_CMYK)``.

    :rtype: :ref:`Colorspace`

.. py:data:: CS_RGB

    1 - Type of :ref:`Colorspace` is RGBA

    :rtype: int

.. py:data:: CS_GRAY

    2 - Type of :ref:`Colorspace` is GRAY

    :rtype: int

.. py:data:: CS_CMYK

    3 - Type of :ref:`Colorspace` is CMYK

    :rtype: int

.. py:data:: VersionBind

    '1.10.x' - version of PyMuPDF (these bindings)

    :rtype: string

.. py:data:: VersionFitz

    '1.10' - version of MuPDF

    :rtype: string

.. py:data:: VersionDate

    ISO timestamp ``YYYY-MM-DD HH:MM:SS`` when these bindings were built.

    :rtype: string

.. Note:: The docstring of ``fitz`` contains information of the above which can be retrieved like so: ``print(fitz.__doc__)``, and a possible response should look like: ``PyMuPDF 1.10.0: Python bindings for the MuPDF 1.10 library, built on 2016-11-30 13:09:13``.


.. _linkDest Kinds:

Enumerations
-------------
Possible values of :attr:`linkDest.kind` (link destination type). For details consult `Adobe PDF Reference sixth edition 1.7 November 2006 <http://www.adobe.com/content/dam/Adobe/en/devnet/acrobat/pdfs/pdf_reference_1-7.pdf>`_, chapter 8.2 on pp. 581.

.. py:data:: LINK_NONE

    0 - No destination

    :rtype: int

.. py:data:: LINK_GOTO

    1 - Points to a place in this document.

    :rtype: int

.. py:data:: LINK_URI

    2 - Points to a URI - typically an internet resource.

    :rtype: int

.. py:data:: LINK_LAUNCH

    3 - Launch (open) another document.

    :rtype: int

.. py:data:: LINK_NAMED

    4 - Perform some action, like "FirstPage", "NextPage", etc.

    :rtype: int

.. py:data:: LINK_GOTOR

    5 - Points to a place in another document.

    :rtype: int

.. _linkDest Flags:

Link Destination Flags
-------------------------

.. Note:: The rightmost byte of this integer is a bit field, so test the truth of these bits with the ``&`` operator.

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

.. _Annotation Types:

Annotation Types
---------------------
Possible values (integer) for PDF annotation types. See chapter 8.4.5, pp. 615 of the Adobe manual for more details.

.. py:data:: ANNOT_TEXT

    0 - Text annotation

.. py:data:: ANNOT_LINK

    1 - Link annotation

.. py:data:: ANNOT_FREETEXT

    2 -  Free text annotation

.. py:data:: ANNOT_LINE

    3 - Line annotation

.. py:data:: ANNOT_SQUARE

    4 -  Square annotation

.. py:data:: ANNOT_CIRCLE

    5 -  Circle annotation

.. py:data:: ANNOT_POLYGON

    6 - Polygon annotation

.. py:data:: ANNOT_POLYLINE

    7 - PolyLine annotation

.. py:data:: ANNOT_HIGHLIGHT

    8 -  Highlight annotation

.. py:data:: ANNOT_UNDERLINE

    9 - Underline annotation

.. py:data:: ANNOT_SQUIGGLY

    10 -  Squiggly-underline annotation

.. py:data:: ANNOT_STRIKEOUT

    11 - Strikeout annotation

.. py:data:: ANNOT_STAMP

    12 -  Rubber stamp annotation

.. py:data:: ANNOT_CARET

    13 - Caret annotation

.. py:data:: ANNOT_INK

    14 -  Ink annotation

.. py:data:: ANNOT_POPUP

    15 -  Pop-up annotation

.. py:data:: ANNOT_FILEATTACHMENT

    16 - File attachment annotation

.. py:data:: ANNOT_SOUND

    17 - Sound annotation

.. py:data:: ANNOT_MOVIE

    18 - Movie annotation

.. py:data:: ANNOT_WIDGET

    19 - Widget annotation

.. py:data:: ANNOT_SCREEN

    20 - Screen annotation

.. py:data:: ANNOT_PRINTERMARK

    21 - Printer’s mark annotation

.. py:data:: ANNOT_TRAPNET

    22 - Trap network annotation

.. py:data:: ANNOT_WATERMARK

    23 - Watermark annotation

.. py:data:: ANNOT_3D

    24 - 3D annotation

.. _Annotation Flags:

Annotation Flags
---------------------
Possible mask values for PDF annotation flags.

.. Note:: Annotation flags is a bit field, so test the truth of its bits with the ``&`` operator. When changing flags for an annotation, use the ``|`` operator to combine several values. The following descriptions were extracted from the Adobe manual, pages 608 pp.

.. py:data:: ANNOT_XF_Invisible

    1 - If set, do not display the annotation if it does not belong to one of the standard annotation types and no annotation handler is available. If clear, display such an unknown annotation using an appearance stream specified by its appearance dictionary, if any.

.. py:data:: ANNOT_XF_Hidden

    2 - If set, do not display or print the annotation or allow it to interact with the user, regardless of its annotation type or whether an annotation handler is available. In cases where screen space is limited, the ability to hide and show annotations selectively can be used in combination with appearance streams to display auxiliary pop-up information similar in function to online help systems.

.. py:data:: ANNOT_XF_Print

    4 - If set, print the annotation when the page is printed. If clear, never print the annotation, regardless of whether it is displayed on the screen. This can be useful, for example, for annotations representing interactive pushbuttons, which would serve no meaningful purpose on the printed page.

.. py:data:: ANNOT_XF_NoZoom

    8 - If set, do not scale the annotation’s appearance to match the magnification of the page. The location of the annotation on the page (defined by the upper-left corner of its annotation rectangle) remains fixed, regardless of the page magnification.

.. py:data:: ANNOT_XF_NoRotate

    16 -  If set, do not rotate the annotation’s appearance to match the rotation of the page. The upper-left corner of the annotation rectangle remains in a fixed location on the page, regardless of the page rotation.

.. py:data:: ANNOT_XF_NoView

    32 -  If set, do not display the annotation on the screen or allow it to interact with the user. The annotation may be printed (depending on the setting of the Print flag) but should be considered hidden for purposes of on-screen display and user interaction.

.. py:data:: ANNOT_XF_ReadOnly

    64 - If set, do not allow the annotation to interact with the user. The annotation may be displayed or printed (depending on the settings of the NoView and Print flags) but should not respond to mouse clicks or change its appearance in response to mouse motions.

.. py:data:: ANNOT_XF_Locked

    128 - If set, do not allow the annotation to be deleted or its properties (including position and size) to be modified by the user. However, this flag does not restrict changes to the annotation’s contents, such as the value of a form field.

.. py:data:: ANNOT_XF_ToggleNoView

    256 - If set, invert the interpretation of the NoView flag for certain events. A typical use is to have an annotation that appears only when a mouse cursor is held over it.

.. py:data:: ANNOT_XF_LockedContents

    512 - If set, do not allow the contents of the annotation to be modified by the user. This flag does not restrict deletion of the annotation or changes to other annotation properties, such as position and size.

.. _Annotation Line Ends:

Annotation Line End Styles
----------------------------
The following descriptions are taken from the Adobe manual TABLE 8.27 on page 630.

.. py:data:: ANNOT_LE_None

    0 - No line ending.

.. py:data:: ANNOT_LE_Square

    1 - A square filled with the annotation’s interior color, if any.

.. py:data:: ANNOT_LE_Circle

    2 - A circle filled with the annotation’s interior color, if any.

.. py:data:: ANNOT_LE_Diamond

    3 - A diamond shape filled with the annotation’s interior color, if any.

.. py:data:: ANNOT_LE_OpenArrow

    4 - Two short lines meeting in an acute angle to form an open arrowhead.

.. py:data:: ANNOT_LE_ClosedArrow

    5 - Two short lines meeting in an acute angle as in the OpenArrow style (see above) and connected by a third line to form a triangular closed arrowhead filled with the annotation’s interior color, if any.

.. py:data:: ANNOT_LE_Butt

    6 - (PDF 1.5) A short line at the endpoint perpendicular to the line itself.

.. py:data:: ANNOT_LE_ROpenArrow

    7 - (PDF 1.5) Two short lines in the reverse direction from OpenArrow.

.. py:data:: ANNOT_LE_RClosedArrow

    8 - (PDF 1.5) A triangular closed arrowhead in the reverse direction from ClosedArrow.

.. py:data:: ANNOT_LE_Slash

    9 - (PDF 1.6) A short line at the endpoint approximately 30 degrees clockwise from perpendicular to the line itself.

