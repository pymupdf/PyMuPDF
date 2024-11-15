.. include:: header.rst

.. _Annot:

================
Annot
================

|pdf_only_class|

Quote from the :ref:`AdobeManual`: "An annotation associates an object such as a note, sound, or movie with a location on a page of a PDF document, or provides a way to interact with the user by means of the mouse and keyboard."

There is a parent-child relationship between an annotation and its page. If the page object becomes unusable (closed document, any document structure change, etc.), then so does every of its existing annotation objects -- an exception is raised saying that the object is "orphaned", whenever an annotation property or method is accessed.

================================== ==============================================================
**Attribute**                      **Short Description**
================================== ==============================================================
:meth:`Annot.delete_responses`     delete all responding annotations
:meth:`Annot.get_file`             get attached file content
:meth:`Annot.get_oc`               get :data:`xref` of an :data:`OCG` / :data:`OCMD`
:meth:`Annot.get_pixmap`           image of the annotation as a pixmap
:meth:`Annot.get_sound`            get the sound of an audio annotation
:meth:`Annot.get_text`             extract annotation text
:meth:`Annot.get_textbox`          extract annotation text
:meth:`Annot.set_border`           set annotation's border properties
:meth:`Annot.set_blendmode`        set annotation's blend mode
:meth:`Annot.set_colors`           set annotation's colors
:meth:`Annot.set_flags`            set annotation's flags field
:meth:`Annot.set_irt_xref`         define the annotation to being "In Response To"
:meth:`Annot.set_name`             set annotation's name field
:meth:`Annot.set_oc`               set :data:`xref` to an :data:`OCG` / :data:`OCMD`
:meth:`Annot.set_opacity`          change transparency
:meth:`Annot.set_open`             open / close annotation or its Popup
:meth:`Annot.set_popup`            create a Popup for the annotation
:meth:`Annot.set_rect`             change annotation rectangle
:meth:`Annot.set_rotation`         change rotation
:meth:`Annot.update_file`          update attached file content
:meth:`Annot.update`               apply accumulated annot changes
:attr:`Annot.blendmode`            annotation BlendMode
:attr:`Annot.border`               border details
:attr:`Annot.colors`               border / background and fill colors
:attr:`Annot.file_info`            get attached file information
:attr:`Annot.flags`                annotation flags
:attr:`Annot.has_popup`            whether annotation has a Popup
:attr:`Annot.irt_xref`             annotation to which this one responds
:attr:`Annot.info`                 various information
:attr:`Annot.is_open`              whether annotation or its Popup is open
:attr:`Annot.line_ends`            start / end appearance of line-type annotations
:attr:`Annot.next`                 link to the next annotation
:attr:`Annot.opacity`              the annot's transparency
:attr:`Annot.parent`               page object of the annotation
:attr:`Annot.popup_rect`           rectangle of the annotation's Popup
:attr:`Annot.popup_xref`           the PDF :data:`xref` number of the annotation's Popup
:attr:`Annot.rect`                 rectangle containing the annotation
:attr:`Annot.type`                 type of the annotation
:attr:`Annot.vertices`             point coordinates of Polygons, PolyLines, etc.
:attr:`Annot.xref`                 the PDF :data:`xref` number
================================== ==============================================================

**Class API**

.. class:: Annot

   .. index::
      pair: matrix; Annot.get_pixmap
      pair: colorspace; Annot.get_pixmap
      pair: alpha; Annot.get_pixmap
      pair: dpi; Annot.get_pixmap

   .. method:: get_pixmap(matrix=pymupdf.Identity, dpi=None, colorspace=pymupdf.csRGB, alpha=False)

      * Changed in v1.19.2: added support of dpi parameter.

      Creates a pixmap from the annotation as it appears on the page in untransformed coordinates. The pixmap's :ref:`IRect` equals *Annot.rect.irect* (see below). **All parameters are keyword only.**

      :arg matrix_like matrix: a matrix to be used for image creation. Default is :ref:`Identity`.

      :arg int dpi: (new in v1.19.2) desired resolution in dots per inch. If not `None`, the matrix parameter is ignored.

      :arg colorspace: a colorspace to be used for image creation. Default is *pymupdf.csRGB*.
      :type colorspace: :ref:`Colorspace`

      :arg bool alpha: whether to include transparency information. Default is *False*.

      :rtype: :ref:`Pixmap`

      .. note::
         
         * If the annotation has just been created or modified, you should :meth:`Document.reload_page` the page first via `page = doc.reload_page(page)`.

         * The pixmap will have *"premultiplied"* pixels if `alpha=True`. To learn about some background, e.g. look for "Premultiplied alpha" `here <https://en.wikipedia.org/wiki/Glossary_of_computer_graphics#P>`_.


   .. index::
      pair: blocks; Annot.get_text
      pair: dict; Annot.get_text
      pair: clip; Annot.get_text
      pair: flags; Annot.get_text
      pair: html; Annot.get_text
      pair: json; Annot.get_text
      pair: rawdict; Annot.get_text
      pair: text; Annot.get_text
      pair: words; Annot.get_text
      pair: xhtml; Annot.get_text
      pair: xml; Annot.get_text

   .. method:: get_text(opt, clip=None, flags=None)

      * New in 1.18.0

      Retrieves the content of the annotation in a variety of formats -- much like the same method for :ref:`Page`.. This currently only delivers relevant data for annotation types 'FreeText' and 'Stamp'. Other types return an empty string (or equivalent objects).

      :arg str opt: (positional only) the desired format - one of the following values. Please note that this method works exactly like the same-named method of :ref:`Page`.

         * "text" -- :meth:`TextPage.extractTEXT`, default
         * "blocks" -- :meth:`TextPage.extractBLOCKS`
         * "words" -- :meth:`TextPage.extractWORDS`
         * "html" -- :meth:`TextPage.extractHTML`
         * "xhtml" -- :meth:`TextPage.extractXHTML`
         * "xml" -- :meth:`TextPage.extractXML`
         * "dict" -- :meth:`TextPage.extractDICT`
         * "json" -- :meth:`TextPage.extractJSON`
         * "rawdict" -- :meth:`TextPage.extractRAWDICT`

      :arg rect-like clip: (keyword only) restrict the extraction to this area. Should hardly ever be required, defaults to :attr:`Annot.rect`.
      :arg int flags: (keyword only) control the amount of data returned. Defaults to simple text extraction.

   .. method:: get_textbox(rect)

      * New in 1.18.0

      Return the annotation text. Mostly (except line breaks) equal to :meth:`Annot.get_text` with the "text" option.

      :arg rect-like rect: the area to consider, defaults to :attr:`Annot.rect`.


   .. method:: set_info(info=None, content=None, title=None, creationDate=None, modDate=None, subject=None)

      * Changed in version 1.16.10

      Changes annotation properties. These include dates, contents, subject and author (title). Changes for *name* and *id* will be ignored. The update happens selectively: To leave a property unchanged, set it to *None*. To delete existing data, use an empty string.

      :arg dict info: a dictionary compatible with the *info* property (see below). All entries must be strings. If this argument is not a dictionary, the other arguments are used instead -- else they are ignored.
      :arg str content: *(new in v1.16.10)* see description in :attr:`info`.
      :arg str title: *(new in v1.16.10)* see description in :attr:`info`.
      :arg str creationDate: *(new in v1.16.10)* date of annot creation. If given, should be in PDF datetime format.
      :arg str modDate: *(new in v1.16.10)* date of last modification. If given, should be in PDF datetime format.
      :arg str subject: *(new in v1.16.10)* see description in :attr:`info`.

   .. method:: set_line_ends(start, end)

      Sets an annotation's line ending styles. Each of these annotation types is defined by a list of points which are connected by lines. The symbol identified by *start* is attached to the first point, and *end* to the last point of this list. For unsupported annotation types, a no-operation with a warning message results.

      .. note::

         * While 'FreeText', 'Line', 'PolyLine', and 'Polygon' annotations can have these properties, (Py-) MuPDF does not support line ends for 'FreeText', because the call-out variant of it is not supported.
         * *(Changed in v1.16.16)* Some symbols have an interior area (diamonds, circles, squares, etc.). By default, these areas are filled with the fill color of the annotation. If this is *None*, then white is chosen. The *fill_color* argument of :meth:`Annot.update` can now be used to override this and give line end symbols their own fill color.

      :arg int start: The symbol number for the first point.
      :arg int end: The symbol number for the last point.

   .. method:: set_oc(xref)

      Set the annotation's visibility using PDF optional content mechanisms. This visibility is controlled by the user interface of supporting PDF viewers. It is independent from other attributes like :attr:`Annot.flags`.

      :arg int xref: the :data:`xref` of an optional contents group (OCG or OCMD). Any previous xref will be overwritten. If zero, a previous entry will be removed. An exception occurs if the xref is not zero and does not point to a valid PDF object.

      .. note:: This does **not require executing** :meth:`Annot.update` to take effect.

   .. method:: get_oc()

      Return the :data:`xref` of an optional content object, or zero if there is none.

      :returns: zero or the xref of an OCG (or OCMD).


   .. method:: set_irt_xref(xref)

      * New in v1.19.3

      Set annotation to be "In Response To" another one.

      :arg int xref: The :data:`xref` of another annotation.

         .. note:: Must refer to an existing annotation on this page. Setting this property requires no subsequent `update()`.


   .. method:: set_open(value)

      * New in v1.18.4

      Set the annotation's Popup annotation to open or closed -- **or** the annotation itself, if its type is 'Text' ("sticky note").

      :arg bool value: the desired open state.


   .. method:: set_popup(rect)

      * New in v1.18.4

      Create a Popup annotation for the annotation and specify its rectangle. If the Popup already exists, only its rectangle is updated.

      :arg rect_like rect: the desired rectangle.



   .. method:: set_opacity(value)

      Set the annotation's transparency. Opacity can also be set in :meth:`Annot.update`.

      :arg float value: a float in range *[0, 1]*. Any value outside is assumed to be 1. E.g. a value of 0.5 sets the transparency to 50%.

      Three overlapping 'Circle' annotations with each opacity set to 0.5:

      .. image:: images/img-opacity.*

   .. attribute:: blendmode

      * New in v1.18.4

      The annotation's blend mode. See :ref:`AdobeManual`, page 324 for explanations.

      :rtype: str
      :returns: the blend mode or *None*.


   .. method:: set_blendmode(blendmode)

      * New in v1.16.14
      
      Set the annotation's blend mode. See :ref:`AdobeManual`, page 324 for explanations. The blend mode can also be set in :meth:`Annot.update`.

      :arg str blendmode: set the blend mode. Use :meth:`Annot.update` to reflect this in the visual appearance. For predefined values see :ref:`BlendModes`. Use `PDF_BM_Normal` to **remove** a blend mode.


   .. method:: set_name(name)

      * New in version 1.16.0
      
      Change the name field of any annotation type. For 'FileAttachment' and 'Text' annotations, this is the icon name, for 'Stamp' annotations the text in the stamp. The visual result (if any) depends on your PDF viewer. See also :ref:`mupdficons`.

      :arg str name: the new name.

      .. caution:: If you set the name of a 'Stamp' annotation, then this will **not change** the rectangle, nor will the text be layouted in any way. If you choose a standard text from :ref:`StampIcons` (the **exact** name piece after `"STAMP_"`), you should receive the original layout. An **arbitrary text** will not be changed to upper case, but be written in font "Times-Bold" as is, horizontally centered in **one line** and be shortened to fit. To get your text fully displayed, its length using :data:`fontsize` 20 must not exceed 190 points. So please make sure that the following inequality is true: `pymupdf.get_text_length(text, fontname="tibo", fontsize=20) <= 190`.

   .. method:: set_rect(rect)

      Change the rectangle of an annotation. The annotation can be moved around and both sides of the rectangle can be independently scaled. However, the annotation appearance will never get rotated, flipped or sheared. This method only affects certain annotation types [#f2]_ and will lead to a message on Python's `sys.stderr` in other cases. No exception will be raised, but `False` will be returned.

      :arg rect_like rect: the new rectangle of the annotation (finite and not empty). E.g. using a value of *annot.rect + (5, 5, 5, 5)* will shift the annot position 5 pixels to the right and downwards.

      .. note:: You **need not** invoke :meth:`Annot.update` for activation of the effect.


   .. method:: set_rotation(angle)

      Set the rotation of an annotation. This rotates the annotation rectangle around its center point. Then a **new annotation rectangle** is calculated from the resulting quad.

      :arg int angle: rotation angle in degrees. Arbitrary values are possible, but will be clamped to the interval `[0, 360)`.

      .. note::
        * You **must invoke** :meth:`Annot.update` to activate the effect.
        * For PDF_ANNOT_FREE_TEXT, only one of the values 0, 90, 180 and 270 is possible and will **rotate the text** inside the current rectangle (which remains unchanged). Other values are silently ignored and replaced by 0.
        * Otherwise, only the following :ref:`AnnotationTypes` can be rotated: 'Square', 'Circle', 'Caret', 'Text', 'FileAttachment', 'Ink', 'Line', 'Polyline', 'Polygon', and 'Stamp'. For all others the method is a no-op.


   .. method:: set_border(border=None, width=None, style=None, dashes=None, clouds=None)

      * Changed in version 1.16.9: Allow specification without using a dictionary. The direct parameters are used if *border* is not a dictionary.

      * Changed in version 1.22.5: Support of the "cloudy" border effect.

      PDF only: Change border width, dashing, style and cloud effect. See the :attr:`Annot.border` attribute for more details.


      :arg dict border: a dictionary as returned by the :attr:`border` property, with keys *"width"* (*float*), *"style"* (*str*),  *"dashes"* (*sequence*) and *clouds* (*int*). Omitted keys will leave the resp. property unchanged. Set the border argument to `None` (the default) to use the other arguments.

      :arg float width: A non-negative value will change the border line width.
      :arg str style: A value other than `None` will change this border property.
      :arg sequence dashes: All items of the sequence must be integers, otherwise the parameter is ignored. To remove dashing use: `dashes=[]`. If dashes is a non-empty sequence, "style" will automatically be set to "D" (dashed). 
      :arg int clouds: A value >= 0 will change this property. Use `clouds=0` to remove the cloudy appearance completely. Only annotation types 'Square', 'Circle', and 'Polygon' are supported with this property.

   .. method:: set_flags(flags)

      Changes the annotation flags. Use the `|` operator to combine several.

      :arg int flags: an integer specifying the required flags.

   .. method:: set_colors(colors=None, stroke=None, fill=None)

      * Changed in version 1.16.9: Allow colors to be directly set. These parameters are used if *colors* is not a dictionary.

      Changes the "stroke" and "fill" colors for supported annotation types -- not all annotations accept both.

      :arg dict colors: a dictionary containing color specifications. For accepted dictionary keys and values see below. The most practical way should be to first make a copy of the *colors* property and then modify this dictionary as required.
      :arg sequence stroke: see above.
      :arg sequence fill: see above.

      *Changed in v1.18.5:* To completely remove a color specification, use an empty sequence like `[]`. If you specify `None`, an existing specification will not be changed.


   .. method:: delete_responses()

      * New in version 1.16.12
      
      Delete annotations referring to this one. This includes any 'Popup' annotations and all annotations responding to it.


   .. index::
      pair: blend_mode; Annot.update
      pair: fontsize; Annot.update
      pair: text_color; Annot.update
      pair: border_color; Annot.update
      pair: fill_color; Annot.update
      pair: cross_out; Annot.update
      pair: rotate; Annot.update

   .. method:: update(opacity=None, blend_mode=None, fontsize=0, text_color=None, border_color=None, fill_color=None, cross_out=True, rotate=-1)

      Synchronize the appearance of an annotation with its properties after relevant changes. 

      You can safely **omit** this method **only** for the following changes:

         * :meth:`Annot.set_rect`
         * :meth:`Annot.set_flags`
         * :meth:`Annot.set_oc`
         * :meth:`Annot.update_file`
         * :meth:`Annot.set_info` (except any changes to *"content"*)

      All arguments are optional. *(Changed in v1.16.14)* Blend mode and opacity are applicable to **all annotation types**. The other arguments are mostly special use, as described below.

      Color specifications may be made in the usual format used in PuMuPDF as sequences of floats ranging from 0.0 to 1.0 (including both). The sequence length must be 1, 3 or 4 (supporting GRAY, RGB and CMYK colorspaces respectively). For GRAY, just a float is also acceptable.

      :arg float opacity: *(new in v1.16.14)* **valid for all annotation types:** change or set the annotation's transparency. Valid values are *0 <= opacity < 1*.
      :arg str blend_mode: *(new in v1.16.14)* **valid for all annotation types:** change or set the annotation's blend mode. For valid values see :ref:`BlendModes`.
      :arg float fontsize: change :data:`fontsize` of the text. 'FreeText' annotations only.
      :arg sequence,float text_color: change the text color. 'FreeText' annotations only.
      :arg sequence,float border_color: change the border color. 'FreeText' annotations only.
      :arg sequence,float fill_color: the fill color.

          * 'Line', 'Polyline', 'Polygon' annotations: use it to give applicable line end symbols a fill color other than that of the annotation *(changed in v1.16.16)*.

      :arg bool cross_out: *(new in v1.17.2)* add two diagonal lines to the annotation rectangle. 'Redact' annotations only. If not desired, *False* must be specified even if the annotation was created with *False*.
      :arg int rotate: new rotation value. Default (-1) means no change. Supports 'FreeText' and several other annotation types (see :meth:`Annot.set_rotation`), [#f1]_. Only choose 0, 90, 180, or 270 degrees for 'FreeText'. Otherwise any integer is acceptable.

      :rtype: bool

      .. note:: Using this method inside a :meth:`Page.annots` loop is **not recommended!** This is because most annotation updates require the owning page to be reloaded -- which cannot be done inside this loop. Please use the example coding pattern given in the documentation of this generator.


   .. attribute:: file_info

      Basic information of the annot's attached file.

      :rtype: dict
      :returns: a dictionary with keys *filename*, *ufilename*, *desc* (description), *size* (uncompressed file size), *length* (compressed length) for FileAttachment annot types, else *None*.

   .. method:: get_file()

      Returns attached file content.

      :rtype: bytes
      :returns: the content of the attached file.

   .. index::
      pair: buffer; Annot.update_file
      pair: filename; Annot.update_file
      pair: ufilename; Annot.update_file
      pair: desc; Annot.update_file

   .. method:: update_file(buffer=None, filename=None, ufilename=None, desc=None)

      Updates the content of an attached file. All arguments are optional. No arguments lead to a no-op.

      :arg bytes|bytearray|BytesIO buffer: the new file content. Omit to only change meta-information.

         *(Changed in version 1.14.13)* *io.BytesIO* is now also supported.

      :arg str filename: new filename to associate with the file.

      :arg str ufilename: new unicode filename to associate with the file.

      :arg str desc: new description of the file content.

   .. method:: get_sound()

      Return the embedded sound of an audio annotation.

      :rtype: dict
      :returns: the sound audio file and accompanying properties. These are the possible dictionary keys, of which only "rate" and "stream" are always present.

        =========== =======================================================
        Key         Description
        =========== =======================================================
        rate        (float, requ.) samples per second
        channels    (int, opt.) number of sound channels
        bps         (int, opt.) bits per sample value per channel
        encoding    (str, opt.) encoding format: Raw, Signed, muLaw, ALaw
        compression (str, opt.) name of compression filter
        stream      (bytes, requ.) the sound file content
        =========== =======================================================


   .. attribute:: opacity

      The annotation's transparency. If set, it is a value in range *[0, 1]*. The PDF default is 1. However, in an effort to tell the difference, we return *-1.0* if not set.

      :rtype: float

   .. attribute:: parent

      The owning page object of the annotation.

      :rtype: :ref:`Page`

   .. attribute:: rotation

      The annot rotation.

      :rtype: int
      :returns: a value [-1, 359]. If rotation is not at all, -1 is returned (and implies a rotation angle of 0). Other possible values are normalized to some value value 0 <= angle < 360.

   .. attribute:: rect

      The rectangle containing the annotation.

      :rtype: :ref:`Rect`

   .. attribute:: next

      The next annotation on this page or None.

      :rtype: *Annot*

   .. attribute:: type

      A number and one or two strings describing the annotation type, like **[2, 'FreeText', 'FreeTextCallout']**. The second string entry is optional and may be empty. See the appendix :ref:`AnnotationTypes` for a list of possible values and their meanings.

      :rtype: list

   .. attribute:: info

      A dictionary containing various information. All fields are optional strings. For information items not provided, an empty string is returned.

      * *name* -- e.g. for 'Stamp' annotations it will contain the stamp text like "Sold" or "Experimental", for other annot types you will see the name of the annot's icon here ("PushPin" for FileAttachment).

      * *content* -- a string containing the text for type *Text* and *FreeText* annotations. Commonly used for filling the text field of annotation pop-up windows.

      * *title* -- a string containing the title of the annotation pop-up window. By convention, this is used for the **annotation author**.

      * *creationDate* -- creation timestamp.
      * *modDate* -- last modified timestamp.
      * *subject* -- subject.
      * *id* -- *(new in version 1.16.10)* a unique identification of the annotation. This is taken from PDF key */NM*. Annotations added by PyMuPDF will have a unique name, which appears here.

      :rtype: dict


   .. attribute:: flags

      An integer whose low order bits contain flags for how the annotation should be presented.

      :rtype: int

   .. attribute:: line_ends

      A pair of integers specifying start and end symbol of annotations types 'FreeText', 'Line', 'PolyLine', and 'Polygon'. *None* if not applicable. For possible values and descriptions in this list, see the :ref:`AdobeManual`, table 1.76 on page 400.

      :rtype: tuple

   .. attribute:: vertices

      A list containing a variable number of point ("vertices") coordinates (each given by a pair of floats) for various types of annotations:

      * 'Line' -- the starting and ending coordinates (2 float pairs).
      * 'FreeText' -- 2 or 3 float pairs designating the starting, the (optional) knee point, and the ending coordinates.
      * 'PolyLine' / 'Polygon' -- the coordinates of the edges connected by line pieces (n float pairs for n points).
      * text markup annotations -- 4 float pairs specifying the *QuadPoints* of the marked text span (see :ref:`AdobeManual`, page 403).
      * 'Ink' -- list of one to many sublists of vertex coordinates. Each such sublist represents a separate line in the drawing.

      :rtype: list


   .. attribute:: colors

      dictionary of two lists of floats in range *0 <= float <= 1* specifying the "stroke" and the interior ("fill") colors. The stroke color is used for borders and everything that is actively painted or written ("stroked"). The fill color is used for the interior of objects like line ends, circles and squares. The lengths of these lists implicitly determine the colorspaces used: 1 = GRAY, 3 = RGB, 4 = CMYK. So "[1.0, 0.0, 0.0]" stands for RGB color red. Both lists can be empty if no color is specified.

      :rtype: dict

   .. attribute:: xref

      The PDF :data:`xref`.

      :rtype: int

   .. attribute:: irt_xref

      The PDF :data:`xref` of an annotation to which this one responds. Return zero if this is no response annotation.

      :rtype: int

   .. attribute:: popup_xref

      The PDF :data:`xref` of the associated Popup annotation. Zero if non-existent.

      :rtype: int

   .. attribute:: has_popup

      Whether the annotation has a Popup annotation.

      :rtype: bool

   .. attribute:: is_open

      Whether the annotation's Popup is open -- **or** the annotation itself ('Text' annotations only).

      :rtype: bool

   .. attribute:: popup_rect

      The rectangle of the associated Popup annotation. Infinite rectangle if non-existent.

      :rtype: :ref:`Rect`

   .. attribute:: rect_delta

      A tuple of four floats representing the `/RD` entry of the annotation. The four numbers describe the numerical differences (left, top, -right, -bottom) between two rectangles: the :attr:`rect` of the annotation and a rectangle contained within that rectangle. If the entry is missing, this property is `(0, 0, 0, 0)`. If the annotation border is a normal, straight line, these numbers are typically border width divided by 2. If the annotation has a "cloudy" border, you will see the breadth of the cloud semi-circles here. In general, the numbers need not be identical. To compute the inner rectangle do `a.rect + a.rect_delta`.

   .. attribute:: border

      A dictionary containing border characteristics. Empty if no border information exists. The following keys may be present:

      * *width* -- a float indicating the border thickness in points. The value is -1.0 if no width is specified.

      * *dashes* -- a sequence of integers specifying a line dashing pattern. *[]* means no dashes, *[n]* means equal on-off lengths of *n* points, longer lists will be interpreted as specifying alternating on-off length values. See the :ref:`AdobeManual` page 126 for more details.

      * *style* -- 1-byte border style: **"S"** (Solid) = solid line surrounding the annotation, **"D"** (Dashed) = dashed line surrounding the annotation, the dash pattern is specified by the *dashes* entry, **"B"** (Beveled) = a simulated embossed rectangle that appears to be raised above the surface of the page, **"I"** (Inset) = a simulated engraved rectangle that appears to be recessed below the surface of the page, **"U"** (Underline) = a single line along the bottom of the annotation rectangle.

      * *clouds* -- an integer indicating a "cloudy" border, where ``n`` is an integer `-1 <= n <= 2`. A value `n = 0` indicates a straight line (no clouds), 1 means small and 2 means large semi-circles, mimicking the cloudy appearance. If -1, then no specification is present.

      :rtype: dict


.. _mupdficons:

Annotation Icons in MuPDF
-------------------------
This is a list of icons referenceable by name for annotation types 'Text' and 'FileAttachment'. You can use them via the *icon* parameter when adding an annotation, or use the as argument in :meth:`Annot.set_name`. It is left to your discretion which item to choose when -- no mechanism will keep you from using e.g. the "Speaker" icon for a 'FileAttachment'.

.. image:: images/mupdf-icons.*


Example
--------
Change the graphical image of an annotation. Also update the "author" and the text to be shown in the popup window::

 doc = pymupdf.open("circle-in.pdf")
 page = doc[0]                          # page 0
 annot = page.first_annot                # get the annotation
 annot.set_border(dashes=[3])           # set dashes to "3 on, 3 off ..."

 # set stroke and fill color to some blue
 annot.set_colors({"stroke":(0, 0, 1), "fill":(0.75, 0.8, 0.95)})
 info = annot.info                      # get info dict
 info["title"] = "Jorj X. McKie"        # set author

 # text in popup window ...
 info["content"] = "I changed border and colors and enlarged the image by 20%."
 info["subject"] = "Demonstration of PyMuPDF"     # some PDF viewers also show this
 annot.set_info(info)                   # update info dict
 r = annot.rect                         # take annot rect
 r.x1 = r.x0 + r.width  * 1.2           # new location has same top-left
 r.y1 = r.y0 + r.height * 1.2           # but 20% longer sides
 annot.set_rect(r)                      # update rectangle
 annot.update()                         # update the annot's appearance
 doc.save("circle-out.pdf")             # save

This is how the circle annotation looks like before and after the change (pop-up windows displayed using Nitro PDF viewer):

|circle|

.. |circle| image:: images/img-circle.*


.. rubric:: Footnotes

.. [#f1] Rotating an annotation also changes its rectangle. Depending on how the annotation was defined, the original rectangle is **cannot be reconstructed** by setting the rotation value to zero again and will be lost.

.. [#f2] Only the following annotation types support method :meth:`Annot.set_rect`: Text, FreeText, Square, Circle, Redact, Stamp, Caret, FileAttachment, Sound, and Movie.

.. include:: footer.rst
