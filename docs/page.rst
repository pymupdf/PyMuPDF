.. _Page:

================
Page
================

Class representing a document page. A page object is created by :meth:`Document.loadPage` or, equivalently, via indexing the document like *doc[n]* - it has no independent constructor.

There is a parent-child relationship between a document and its pages. If the document is closed or deleted, all page objects (and their respective children, too) in existence will become unusable ("orphaned"): If a page property or method is being used, an exception is raised.

Several page methods have a :ref:`Document` counterpart for convenience. At the end of this chapter you will find a synopsis.

Modifying Pages
---------------
Changing page properties and adding or changing page content is available for PDF documents only.

In a nutshell, this is what you can do with PyMuPDF:

* Modify page rotation and the visible part ("CropBox") of the page.
* Insert images, other PDF pages, text and simple geometrical objects.
* Add annotations and form fields.

.. note::

   Methods require coordinates (points, rectangles) to put content in desired places. Please be aware that since v1.17.0 these coordinates **must always** be provided relative to the **unrotated** page. The reverse is also true: expcept :attr:`Page.rect`, resp. :meth:`Page.bound` (both *reflect* when the page is rotated), all coordinates returned by methods and attributes pertain to the unrotated page.

   So the returned value of e.g. :meth:`Page.getImageBbox` will not change if you do a :meth:`Page.setRotation`. The same is true for coordinates returned by :meth:`Page.getText`, annotation rectangles, and so on. If you want to find out, where an object is located in **rotated coordinates**, multiply the coordinates with :attr:`Page.rotationMatrix`. There also is its inverse, :attr:`Page.derotationMatrix`, which you can use when interfacing with other readers, which may behave differently in this respect.

.. note::

   If you add or update annotations, links or form fields on the page and immediately afterwards need to work with them (i.e. **without leaving the page**), you should reload the page using :meth:`Document.reload_page` before referring to these new or updated items.

   This ensures all your changes have been fully applied to PDF structures, so can safely create Pixmaps or successfully iterate over annotations, links and form fields.

================================= =======================================================
**Method / Attribute**            **Short Description**
================================= =======================================================
:meth:`Page.addCaretAnnot`        PDF only: add a caret annotation
:meth:`Page.addCircleAnnot`       PDF only: add a circle annotation
:meth:`Page.addFileAnnot`         PDF only: add a file attachment annotation
:meth:`Page.addFreetextAnnot`     PDF only: add a text annotation
:meth:`Page.addHighlightAnnot`    PDF only: add a "highlight" annotation
:meth:`Page.addInkAnnot`          PDF only: add an ink annotation
:meth:`Page.addLineAnnot`         PDF only: add a line annotation
:meth:`Page.addPolygonAnnot`      PDF only: add a polygon annotation
:meth:`Page.addPolylineAnnot`     PDF only: add a multi-line annotation
:meth:`Page.addRectAnnot`         PDF only: add a rectangle annotation
:meth:`Page.addRedactAnnot`       PDF only: add a redaction annotation
:meth:`Page.addSquigglyAnnot`     PDF only: add a "squiggly" annotation
:meth:`Page.addStampAnnot`        PDF only: add a "rubber stamp" annotation
:meth:`Page.addStrikeoutAnnot`    PDF only: add a "strike-out" annotation
:meth:`Page.addTextAnnot`         PDF only: add a comment
:meth:`Page.addUnderlineAnnot`    PDF only: add an "underline" annotation
:meth:`Page.addWidget`            PDF only: add a PDF Form field
:meth:`Page.annot_names`          PDF only: a list of annotation and widget names
:meth:`Page.annots`               return a generator over the annots on the page
:meth:`Page.apply_redactions`     PDF olny: process the redactions of the page
:meth:`Page.bound`                rectangle of the page
:meth:`Page.deleteAnnot`          PDF only: delete an annotation
:meth:`Page.deleteLink`           PDF only: delete a link
:meth:`Page.drawBezier`           PDF only: draw a cubic Bezier curve
:meth:`Page.drawCircle`           PDF only: draw a circle
:meth:`Page.drawCurve`            PDF only: draw a special Bezier curve
:meth:`Page.drawLine`             PDF only: draw a line
:meth:`Page.drawOval`             PDF only: draw an oval / ellipse
:meth:`Page.drawPolyline`         PDF only: connect a point sequence
:meth:`Page.drawRect`             PDF only: draw a rectangle
:meth:`Page.drawSector`           PDF only: draw a circular sector
:meth:`Page.drawSquiggle`         PDF only: draw a squiggly line
:meth:`Page.drawZigzag`           PDF only: draw a zig-zagged line
:meth:`Page.getFontList`          PDF only: get list of used fonts
:meth:`Page.getImageBbox`         PDF only: get bbox of embedded image
:meth:`Page.getImageList`         PDF only: get list of used images
:meth:`Page.getLinks`             get all links
:meth:`Page.getPixmap`            create a page image in raster format
:meth:`Page.getSVGimage`          create a page image in SVG format
:meth:`Page.getText`              extract the page's text
:meth:`Page.getTextPage`          create a TextPage for the page
:meth:`Page.insertFont`           PDF only: insert a font for use by the page
:meth:`Page.insertImage`          PDF only: insert an image
:meth:`Page.insertLink`           PDF only: insert a link
:meth:`Page.insertText`           PDF only: insert text
:meth:`Page.insertTextbox`        PDF only: insert a text box
:meth:`Page.links`                return a generator of the links on the page
:meth:`Page.loadAnnot`            PDF only: load a specific annotation
:meth:`Page.loadLinks`            return the first link on a page
:meth:`Page.newShape`             PDF only: create a new :ref:`Shape`
:meth:`Page.searchFor`            search for a string
:meth:`Page.setCropBox`           PDF only: modify the visible page
:meth:`Page.setMediaBox`          PDF only: modify the mediabox
:meth:`Page.setRotation`          PDF only: set page rotation
:meth:`Page.showPDFpage`          PDF only: display PDF page image
:meth:`Page.updateLink`           PDF only: modify a link
:meth:`Page.widgets`              return a generator over the fields on the page
:meth:`Page.writeText`            write one or more :ref:`Textwriter` objects
:attr:`Page.CropBox`              the page's :data:`CropBox`
:attr:`Page.CropBoxPosition`      displacement of the :data:`CropBox`
:attr:`Page.firstAnnot`           first :ref:`Annot` on the page
:attr:`Page.firstLink`            first :ref:`Link` on the page
:attr:`Page.firstWidget`          first widget (form field) on the page
:attr:`Page.MediaBox`             the page's :data:`MediaBox`
:attr:`Page.MediaBoxSize`         bottom-right point of :data:`MediaBox`
:attr:`Page.derotationMatrix`     PDF only: get coordinates in unrotated page space
:attr:`Page.rotationMatrix`       PDF only: get coordinates in rotated page space
:attr:`Page.transformationMatrix` PDF only: translate between PDF and MuPDF space
:attr:`Page.number`               page number
:attr:`Page.parent`               owning document object
:attr:`Page.rect`                 rectangle of the page
:attr:`Page.rotation`             PDF only: page rotation
:attr:`Page.xref`                 PDF only: page :data:`xref`
================================= =======================================================

**Class API**

.. class:: Page

   .. method:: bound()

      Determine the rectangle of the page. Same as property :attr:`Page.rect` below. For PDF documents this **usually** also coincides with :data:`MediaBox` and :data:`CropBox`, but not always. For example, if the page is rotated, then this is reflected by this method -- the :attr:`Page.CropBox` however will not change.

      :rtype: :ref:`Rect`

   .. method:: addCaretAnnot(point)

      *(New in version 1.16.0)*
      
      PDF only: Add a caret icon. A caret annotation is a visual symbol normally used to indicate the presence of text edits on the page.

      :arg point_like point: the top left point of a 20 x 20 rectangle containing the MuPDF-provided icon.

      :rtype: :ref:`Annot`
      :returns: the created annotation.

      .. image:: images/img-caret-annot.jpg
         :scale: 70

   .. method:: addTextAnnot(point, text, icon="Note")

      PDF only: Add a comment icon ("sticky note") with accompanying text. Only the icon is visible, the accompanying text is hidden and can be visualized by many PDF viewers by hovering the mouse over the symbol.

      :arg point_like point: the top left point of a 20 x 20 rectangle containing the MuPDF-provided "note" icon.

      :arg str text: the commentary text. This will be shown on double clicking or hovering over the icon. May contain any Latin characters.
      :arg str icon: *(new in version 1.16.0)* choose one of "Note" (default), "Comment", "Help", "Insert", "Key", "NewParagraph", "Paragraph" as the visual symbol for the embodied text [#f4]_.

      :rtype: :ref:`Annot`
      :returns: the created annotation.

   .. index::
      pair: color; addFreetextAnnot
      pair: fontname; addFreetextAnnot
      pair: fontsize; addFreetextAnnot
      pair: rect; addFreetextAnnot
      pair: rotate; addFreetextAnnot
      pair: align; addFreetextAnnot

   .. method:: addFreetextAnnot(rect, text, fontsize=12, fontname="helv", text_color=0, fill_color=1, rotate=0, align=TEXT_ALIGN_LEFT)

      PDF only: Add text in a given rectangle.

      :arg rect_like rect: the rectangle into which the text should be inserted. Text is automatically wrapped to a new line at box width. Lines not fitting into the box will be invisible.

      :arg str text: the text. *(New in v1.17.0)* May contain any mixture of Latin, Greek, Cyrillic, Chinese, Japanese and Korean characters. The respective required font is automatically determined.
      :arg float fontsize: the font size. Default is 12.
      :arg str fontname: the font name. Default is "Helv". Accepted alternatives are "Cour", "TiRo", "ZaDb" and "Symb". The name may be abbreviated to the first two characters, like "Co" for "Cour". Lower case is also accepted. *(Changed in v1.16.0)* Bold or italic variants of the fonts are **no longer accepted**. A user-contributed script provides a circumvention for this restriction -- see section *Using Buttons and JavaScript* in chapter :ref:`FAQ`. *(New in v1.17.0)* The actual font to use is now determined on a by-character level, and all required fonts (or sub-fonts) are automatically included. Therefore, you should rarely ever need to care about this parameter and let it default (except you insist on a serifed font for your non-CJK text parts).
      :arg sequence,float text_color: *(new in version 1.16.0)* the text color. Default is black.

      :arg sequence,float fill_color: *(new in version 1.16.0)* the fill color. Default is white.
      :arg int align: *(new in version 1.17.0)* text alignment, one of TEXT_ALIGN_LEFT, TEXT_ALIGN_CENTER, TEXT_ALIGN_RIGHT - justify is not supported.


      :arg int rotate: the text orientation. Accepted values are 0, 90, 270, invalid entries are set to zero.

      :rtype: :ref:`Annot`
      :returns: the created annotation. Color properties **can only be changed** using special parameters of :meth:`Annot.update`. There, you can also set a border color different from the text color.

   .. method:: addFileAnnot(pos, buffer, filename, ufilename=None, desc=None, icon="PushPin")

      PDF only: Add a file attachment annotation with a "PushPin" icon at the specified location.

      :arg point_like pos: the top-left point of a 18x18 rectangle containing the MuPDF-provided "PushPin" icon.

      :arg bytes,bytearray,BytesIO buffer: the data to be stored (actual file content, any data, etc.).

         Changed in version 1.14.13 *io.BytesIO* is now also supported.

      :arg str filename: the filename to associate with the data.
      :arg str ufilename: the optional PDF unicode version of filename. Defaults to filename.
      :arg str desc: an optional description of the file. Defaults to filename.
      :arg str icon: *(new in version 1.16.0)* choose one of "PushPin" (default), "Graph", "Paperclip", "Tag" as the visual symbol for the attached data [#f4]_.

      :rtype: :ref:`Annot`
      :returns: the created annotation. Use methods of :ref:`Annot` to make any changes.

   .. method:: addInkAnnot(list)

      PDF only: Add a "freehand" scribble annotation.

      :arg sequence list: a list of one or more lists, each containing :data:`point_like` items. Each item in these sublists is interpreted as a :ref:`Point` through which a connecting line is drawn. Separate sublists thus represent separate drawing lines.

      :rtype: :ref:`Annot`
      :returns: the created annotation in default appearance (black line of width 1). Use annotation methods with a subsequent :meth:`Annot.update` to modify.

   .. method:: addLineAnnot(p1, p2)

      PDF only: Add a line annotation.

      :arg point_like p1: the starting point of the line.

      :arg point_like p2: the end point of the line.

      :rtype: :ref:`Annot`
      :returns: the created annotation. It is drawn with line color black and line width 1. The **rectangle** is automatically created to contain both points, each one surrounded by a circle of radius 3 * line width to make room for any line end symbols.

   .. method:: addRectAnnot(rect)

   .. method:: addCircleAnnot(rect)

      PDF only: Add a rectangle, resp. circle annotation.

      :arg rect_like rect: the rectangle in which the circle or rectangle is drawn, must be finite and not empty. If the rectangle is not equal-sided, an ellipse is drawn.

      :rtype: :ref:`Annot`
      :returns: the created annotation. It is drawn with line color red, no fill color and line width 1.

   .. method:: addRedactAnnot(quad, text=None, fontname=None, fontsize=11, align=TEXT_ALIGN_LEFT, fill=(1, 1, 1), text_color=(0, 0, 0), cross_out=True)

      PDF only: *(new in version 1.16.11)* Add a redaction annotation. A redaction annotation identifies content to be removed from the document. Adding such an annotation is the first of two steps. It makes visible what will be removed in the subsequent step, :meth:`Page.apply_redactions`.

      :arg quad_like,rect_like quad: specifies the (rectangular) area to be removed which is always equal to the annotation rectangle. This may be a :data:`rect_like` or :data:`quad_like` object. If a quad is specified, then the envelopping rectangle is taken.

      :arg str text: *(New in v1.16.12)* text to be placed in the rectangle after applying the redaction (and thus removing old content).

      :arg str fontname: *(New in v1.16.12)* the font to use when *text* is given, otherwise ignored. The same rules apply as for :meth:`Page.insertTextbox` -- which is the method :meth:`Page.apply_redactions` internally invokes. The replacement text will be **vertically centered**, if this is one of the CJK or :ref:`Base-14-Fonts`.

         .. note::

            * For an **existing** font of the page, use its reference name as *fontname* (this is *item[4]* of its entry in :meth:`Page.getFontList`).
            * For a **new, non-builtin** font, proceed as follows::

               page.insertText(point,  # anywhere, but outside all redaction rectangles
                   "somthing",  # some non-empty string
                   fontname="newname",  # new, unused reference name
                   fontfile="...",  # desired font file
                   render_mode=3,  # makes the text invisible
               )
               page.addRedactAnnot(..., fontname="newname")

      :arg float fontsize: *(New in v1.16.12)* the fontsize to use for the replacing text. If the text is too large to fit, several insertion attempts will be made, gradually reducing the fontsize to no less than 4. If then the text will still not fit, no text insertion will take place at all.

      :arg int align: *(New in v1.16.12)* the horizontal alignment for the replacing text. See :meth:`insertTextbox` for available values. The vertical alignment is (approximately) centered if a PDF built-in font is used (CJK or :ref:`Base-14-Fonts`).

      :arg sequence fill: *(New in v1.16.12)* the fill color of the rectangle **after applying** the redaction. The default is *white = (1, 1, 1)*, which is also taken if *None* is specified. *(Changed in v1.16.13)* To suppress a fill color alltogether, specify *False*. In this cases the rectangle remains transparent.

      :arg sequence text_color: *(New in v1.16.12)* the color of the replacing text. Default is *black = (0, 0, 0)*.

      :arg bool cross_out: *(new in v1.17.2)* add two diagonal lines to the annotation rectangle.

      :rtype: :ref:`Annot`
      :returns: the created annotation. *(Changed in v1.17.2)* Its standard appearance looks like a red rectangle (no fill color), optionally showing two diagonal lines. Colors, line width, dashing, opacity and blend mode can now be set and applied via :meth:`Annot.update` like with other annotations.

      .. image:: images/img-redact.jpg

   .. method:: addPolylineAnnot(points)

   .. method:: addPolygonAnnot(points)

      PDF only: Add an annotation consisting of lines which connect the given points. A **Polygon's** first and last points are automatically connected, which does not happen for a **PolyLine**. The **rectangle** is automatically created as the smallest rectangle containing the points, each one surrounded by a circle of radius 3 (= 3 * line width). The following shows a 'PolyLine' that has been modified with colors and line ends.

      :arg list points: a list of :data:`point_like` objects.

      :rtype: :ref:`Annot`
      :returns: the created annotation. It is drawn with line color black, no fill color and line width 1. Use methods of :ref:`Annot` to make any changes to achieve something like this:

      .. image:: images/img-polyline.png
         :scale: 70

   .. method:: addUnderlineAnnot(quads=None, start=None, stop=None, clip=None)

   .. method:: addStrikeoutAnnot(quads=None, start=None, stop=None, clip=None)

   .. method:: addSquigglyAnnot(quads=None, start=None, stop=None, clip=None)

   .. method:: addHighlightAnnot(quads=None, start=None, stop=None, clip=None)

      PDF only: These annotations are normally used for **marking text** which has previously been somehow located (for example via :meth:`Page.searchFor`). But this is not required: you are free to "mark" just anything.

      Standard colors are chosen per annotation type: **yellow** for highlighting, **red** for strike out, **green** for underlining, and **magenta** for wavy underlining.

      The methods convert the arguments into a list of :ref:`Quad` objects. The **annotation** rectangle is then calculated to envelop all these quadrilaterals.

      .. note:: :meth:`searchFor` delivers a list of either rectangles or quadrilaterals. Such a list can be directly used as parameter for these annotation types and will deliver **one common** annotation for all occurrences of the search string::

           >>> quads = page.searchFor("pymupdf", hit_max=100, quads=True)
           >>> page.addHighlightAnnot(quads)

      :arg rect_like,quad_like,list,tuple quads: *(Changed in v1.14.20)* the location(s) -- rectangle(s) or quad(s) -- to be marked. A list or tuple must consist of :data:`rect_like` or :data:`quad_like` items (or even a mixture of either). Every item must be finite, convex and not empty (as applicable). *(Changed in v1.16.14)* **Set this parameter to** *None* if you want to use the following arguments.
      :arg point_like start: *(New in v1.16.14)* start text marking at this point. Defaults to the top-left point of *clip*.
      :arg point_like stop: *(New in v1.16.14)* stop text marking at this point. Defaults to the bottom-right point of *clip*.
      :arg rect_like clip: *(New in v1.16.14)* only consider text lines intersecting this area. Defaults to the page rectangle.

      :rtype: :ref:`Annot` or *(changed in v1.16.14)* *None*
      :returns: the created annotation. *(Changed in v1.16.14)* If *quads* is an empty list, **no annotation** is created. To change colors, set the "stroke" color accordingly (:meth:`Annot.setColors`) and then perform an :meth:`Annot.update`.

      .. note:: Starting with v1.16.14 you can use parameters *start*, *stop* and *clip* to highlight consecutive lines between the points *start* and *stop*. Make use of *clip* to further reduce the selected line bboxes and thus deal with e.g. multi-column pages. The following multi-line highlight on a page with three text columnbs was created by specifying the two red points and setting clip accordingly.

      .. image:: images/img-markers.jpg
         :scale: 100

   .. method:: addStampAnnot(rect, stamp=0)

      PDF only: Add a "rubber stamp" like annotation to e.g. indicate the document's intended use ("DRAFT", "CONFIDENTIAL", etc.).

      :arg rect_like rect: rectangle where to place the annotation.

      :arg int stamp: id number of the stamp text. For available stamps see :ref:`StampIcons`.

      .. note::

         * The stamp's text and its border line will automatically be sized and be put horizontally and vertically centered in the given rectangle. :attr:`Annot.rect` is automatically calculated to fit the given **width** and will usually be smaller than this parameter.
         * The font chosen is "Times Bold" and the text will be upper case.
         * The appearance can be changed using :meth:`Annot.setOpacity` and by setting the "stroke" color (no "fill" color supported).
         * This can be used to create watermark images: on a temporary PDF page create a stamp annotation with a low opacity value, make a pixmap from it with *alpha=True* (and potentially also rotate it), discard the temporary PDF page and use the pixmap with :meth:`insertImage` for your target PDF.


      .. image :: images/img-stampannot.jpg
         :scale: 80

   .. method:: addWidget(widget)

      PDF only: Add a PDF Form field ("widget") to a page. This also **turns the PDF into a Form PDF**. Because of the large amount of different options available for widgets, we have developed a new class :ref:`Widget`, which contains the possible PDF field attributes. It must be used for both, form field creation and updates.

      :arg widget: a :ref:`Widget` object which must have been created upfront.
      :type widget: :ref:`Widget`

      :returns: a widget annotation.

   .. method:: deleteAnnot(annot)

      PDF only: Delete the specified annotation from the page and return the next one.

      Changed in version 1.16.6 The removal will now include any bound 'Popup' or response annotations and related objects.

      :arg annot: the annotation to be deleted.
      :type annot: :ref:`Annot`

      :rtype: :ref:`Annot`
      :returns: the annotation following the deleted one. Please remember that physical removal will take place only with saving to a new file with a positive garbage collection option.

   .. method:: apply_redactions()

      PDF only: *(New in version 1.16.11)* Remove all **text content** contained in any redaction rectangle.

      *(Changed in v1.16.12)* The previous *mark* parameter is gone. Instead, the respective rectangles are filled with the individual *fill* color of each redaction annotation. If a *text* was given in the annotation, then :meth:`insertTextbox` is invoked to insert it, using parameters provided with the redaction.

      **This method applies and then deletes all redaction annotations from the page.**

      :returns: *True* if at least one redaction annotation has been processed, *False* otherwise.

      .. note::
         Text contained in a redaction rectangle will be **physically** removed from the page and will no longer appear in e.g. text extractions or anywhere else. Other annotations are unaffected.

         Images and links will also **physically** be removed from the page. For an image, overlapping parts will be blanked-out. Links will always be completely removed.

         Text removal is done by character: A character is removed if its bbox has a **non-empty intersection** with a redaction *(changed in v1.17)*.

         Redactions are an easy way to replace single words in a PDF, or to just physically remove them from the PDF: locate the word "secret" using some text extraction or search method and insert a redaction using "xxxxxx" as replacement text for each occurrence.

            * Be wary if the replacement is longer than the original -- this may lead to an awkward appearance, line breaks or no new text at all.

            * For a number of reasons, the new text may not exactly be positioned on the same line like the old one -- especially true if the replacement font was not one of CJK or :ref:`Base-14-Fonts`.

   .. method:: deleteLink(linkdict)

      PDF only: Delete the specified link from the page. The parameter must be an **original item** of :meth:`getLinks()` (see below). The reason for this is the dictionary's *"xref"* key, which identifies the PDF object to be deleted.

      :arg dict linkdict: the link to be deleted.

   .. method:: insertLink(linkdict)

      PDF only: Insert a new link on this page. The parameter must be a dictionary of format as provided by :meth:`getLinks()` (see below).

      :arg dict linkdict: the link to be inserted.

   .. method:: updateLink(linkdict)

      PDF only: Modify the specified link. The parameter must be a (modified) **original item** of :meth:`getLinks()` (see below). The reason for this is the dictionary's *"xref"* key, which identifies the PDF object to be changed.

      :arg dict linkdict: the link to be modified.

   .. method:: getLinks()

      Retrieves **all** links of a page.

      :rtype: list
      :returns: A list of dictionaries. For a description of the dictionary entries see below. Always use this or the :meth:`Page.links` method if you intend to make changes to the links of a page.

   .. method:: links(kinds=None)

      *(New in version 1.16.4)*
      
      Return a generator over the page's links. The results equal the entries of :meth:`Page.getLinks`.

      :arg sequence kinds: a sequence of integers to down-select to one or more link kinds. Default is all links. Example: *kinds=(fitz.LINK_GOTO,)* will only return internal links.

      :rtype: generator
      :returns: an entry of :meth:`Page.getLinks()` for each iteration.

   .. method:: annots(types=None)

      *(New in version 1.16.4)*
      
      Return a generator over the page's annotations.

      :arg sequence types: a sequence of integers to down-select to one or annotation types. Default is all annotations. Example: *types=(fitz.PDF_ANNOT_FREETEXT, fitz.PDF_ANNOT_TEXT)* will only return 'FreeText' and 'Text' annotations.

      :rtype: generator
      :returns: an :ref:`Annot` for each iteration.

   .. method:: widgets(types=None)

      *(New in version 1.16.4)*
      
      Return a generator over the page's form fields.

      :arg sequence types: a sequence of integers to down-select to one or more widget types. Default is all form fields. Example: *types=(fitz.PDF_WIDGET_TYPE_TEXT,)* will only return 'Text' fields.

      :rtype: generator
      :returns: a :ref:`Widget` for each iteration.


   .. method:: writeText(rect=None, writers=None, overlay=True, color=None, opacity=None, keep_proportion=True, rotate=0)

      *(New in version 1.16.18)*
      
      PDF only: Write the text of one or more :ref:`Textwriter` ojects to the page.

      :arg rect_like rect: where to place the text. If omitted, the rectangle union of the text writers is used.
      :arg sequence writers: a non-empty tuple / list of :ref:`TextWriter` objects or a single :ref:`TextWriter`.
      :arg float opacity: set transparency, overwrites resp. value in the text writers.
      :arg sequ color: set the text color, overwrites  resp. value in the text writers.
      :arg bool overlay: put the text in foreground or background.
      :arg bool keep_proportion: maintain the aspect ratio.
      :arg float rotate: rotate the text by an arbitrary angle.

      .. note:: Parameters overlay, keep_proportion and rotate have the same meaning as in :ref:`showPDFpage`.


   .. index::
      pair: border_width; insertText
      pair: color; insertText
      pair: encoding; insertText
      pair: fill; insertText
      pair: fontfile; insertText
      pair: fontname; insertText
      pair: fontsize; insertText
      pair: morph; insertText
      pair: overlay; insertText
      pair: render_mode; insertText
      pair: rotate; insertText

   .. method:: insertText(point, text, fontsize=11, fontname="helv", fontfile=None, idx=0, color=None, fill=None, render_mode=0, border_width=1, encoding=TEXT_ENCODING_LATIN, rotate=0, morph=None, overlay=True)

      PDF only: Insert text starting at :data:`point_like` *point*. See :meth:`Shape.insertText`.

   .. index::
      pair: align; insertTextbox
      pair: border_width; insertTextbox
      pair: color; insertTextbox
      pair: encoding; insertTextbox
      pair: expandtabs; insertTextbox
      pair: fill; insertTextbox
      pair: fontfile; insertTextbox
      pair: fontname; insertTextbox
      pair: fontsize; insertTextbox
      pair: morph; insertTextbox
      pair: overlay; insertTextbox
      pair: render_mode; insertTextbox
      pair: rotate; insertTextbox

   .. method:: insertTextbox(rect, buffer, fontsize=11, fontname="helv", fontfile=None, idx=0, color=None, fill=None, render_mode=0, border_width=1, encoding=TEXT_ENCODING_LATIN, expandtabs=8, align=TEXT_ALIGN_LEFT, charwidths=None, rotate=0, morph=None, overlay=True)

      PDF only: Insert text into the specified :data:`rect_like` *rect*. See :meth:`Shape.insertTextbox`.

   .. index::
      pair: closePath; drawLine
      pair: color; drawLine
      pair: dashes; drawLine
      pair: fill; drawLine
      pair: lineCap; drawLine
      pair: lineJoin; drawLine
      pair: lineJoin; drawLine
      pair: morph; drawLine
      pair: overlay; drawLine
      pair: width; drawLine

   .. method:: drawLine(p1, p2, color=None, width=1, dashes=None, lineCap=0, lineJoin=0, overlay=True, morph=None)

      PDF only: Draw a line from *p1* to *p2* (:data:`point_like` \s). See :meth:`Shape.drawLine`.

   .. index::
      pair: breadth; drawZigzag
      pair: closePath; drawZigzag
      pair: color; drawZigzag
      pair: dashes; drawZigzag
      pair: fill; drawZigzag
      pair: lineCap; drawZigzag
      pair: lineJoin; drawZigzag
      pair: morph; drawZigzag
      pair: overlay; drawZigzag
      pair: width; drawZigzag

   .. method:: drawZigzag(p1, p2, breadth=2, color=None, width=1, dashes=None, lineCap=0, lineJoin=0, overlay=True, morph=None)

      PDF only: Draw a zigzag line from *p1* to *p2* (:data:`point_like` \s). See :meth:`Shape.drawZigzag`.

   .. index::
      pair: breadth; drawSquiggle
      pair: closePath; drawSquiggle
      pair: color; drawSquiggle
      pair: dashes; drawSquiggle
      pair: fill; drawSquiggle
      pair: lineCap; drawSquiggle
      pair: lineJoin; drawSquiggle
      pair: morph; drawSquiggle
      pair: overlay; drawSquiggle
      pair: width; drawSquiggle

   .. method:: drawSquiggle(p1, p2, breadth=2, color=None, width=1, dashes=None, lineCap=0, lineJoin=0, overlay=True, morph=None)

      PDF only: Draw a squiggly (wavy, undulated) line from *p1* to *p2* (:data:`point_like` \s). See :meth:`Shape.drawSquiggle`.

   .. index::
      pair: closePath; drawCircle
      pair: color; drawCircle
      pair: dashes; drawCircle
      pair: fill; drawCircle
      pair: lineCap; drawCircle
      pair: lineJoin; drawCircle
      pair: morph; drawCircle
      pair: overlay; drawCircle
      pair: width; drawCircle

   .. method:: drawCircle(center, radius, color=None, fill=None, width=1, dashes=None, lineCap=0, lineJoin=0, overlay=True, morph=None)

      PDF only: Draw a circle around *center* (:data:`point_like`) with a radius of *radius*. See :meth:`Shape.drawCircle`.

   .. index::
      pair: closePath; drawOval
      pair: color; drawOval
      pair: dashes; drawOval
      pair: fill; drawOval
      pair: lineCap; drawOval
      pair: lineJoin; drawOval
      pair: morph; drawOval
      pair: overlay; drawOval
      pair: width; drawOval

   .. method:: drawOval(quad, color=None, fill=None, width=1, dashes=None, lineCap=0, lineJoin=0, overlay=True, morph=None)

      PDF only: Draw an oval (ellipse) within the given :data:`rect_like` or :data:`quad_like`. See :meth:`Shape.drawOval`.

   .. index::
      pair: closePath; drawSector
      pair: color; drawSector
      pair: dashes; drawSector
      pair: fill; drawSector
      pair: fullSector; drawSector
      pair: lineCap; drawSector
      pair: lineJoin; drawSector
      pair: morph; drawSector
      pair: overlay; drawSector
      pair: width; drawSector

   .. method:: drawSector(center, point, angle, color=None, fill=None, width=1, dashes=None, lineCap=0, lineJoin=0, fullSector=True, overlay=True, closePath=False, morph=None)

      PDF only: Draw a circular sector, optionally connecting the arc to the circle's center (like a piece of pie). See :meth:`Shape.drawSector`.

   .. index::
      pair: closePath; drawPolyline
      pair: color; drawPolyline
      pair: dashes; drawPolyline
      pair: fill; drawPolyline
      pair: lineCap; drawPolyline
      pair: lineJoin; drawPolyline
      pair: morph; drawPolyline
      pair: overlay; drawPolyline
      pair: width; drawPolyline

   .. method:: drawPolyline(points, color=None, fill=None, width=1, dashes=None, lineCap=0, lineJoin=0, overlay=True, closePath=False, morph=None)

      PDF only: Draw several connected lines defined by a sequence of :data:`point_like` \s. See :meth:`Shape.drawPolyline`.


   .. index::
      pair: closePath; drawBezier
      pair: color; drawBezier
      pair: dashes; drawBezier
      pair: fill; drawBezier
      pair: lineCap; drawBezier
      pair: lineJoin; drawBezier
      pair: morph; drawBezier
      pair: overlay; drawBezier
      pair: width; drawBezier

   .. method:: drawBezier(p1, p2, p3, p4, color=None, fill=None, width=1, dashes=None, lineCap=0, lineJoin=0, overlay=True, closePath=False, morph=None)

      PDF only: Draw a cubic BÃ©zier curve from *p1* to *p4* with the control points *p2* and *p3* (all are :data`point_like` \s). See :meth:`Shape.drawBezier`.

   .. index::
      pair: closePath; drawCurve
      pair: color; drawCurve
      pair: dashes; drawCurve
      pair: fill; drawCurve
      pair: lineCap; drawCurve
      pair: lineJoin; drawCurve
      pair: morph; drawCurve
      pair: overlay; drawCurve
      pair: width; drawCurve

   .. method:: drawCurve(p1, p2, p3, color=None, fill=None, width=1, dashes=None, lineCap=0, lineJoin=0, overlay=True, closePath=False, morph=None)

      PDF only: This is a special case of *drawBezier()*. See :meth:`Shape.drawCurve`.

   .. index::
      pair: closePath; drawRect
      pair: color; drawRect
      pair: dashes; drawRect
      pair: fill; drawRect
      pair: lineCap; drawRect
      pair: lineJoin; drawRect
      pair: morph; drawRect
      pair: overlay; drawRect
      pair: width; drawRect

   .. method:: drawRect(rect, color=None, fill=None, width=1, dashes=None, lineCap=0, lineJoin=0, overlay=True, morph=None)

      PDF only: Draw a rectangle. See :meth:`Shape.drawRect`.

      .. note:: An efficient way to background-color a PDF page with the old Python paper color is

          >>> col = fitz.utils.getColor("py_color")
          >>> page.drawRect(page.rect, color=col, fill=col, overlay=False)

   .. index::
      pair: encoding; insertFont
      pair: fontbuffer; insertFont
      pair: fontfile; insertFont
      pair: fontname; insertFont
      pair: set_simple; insertFont

   .. method:: insertFont(fontname="helv", fontfile=None, fontbuffer=None, set_simple=False, encoding=TEXT_ENCODING_LATIN)

      PDF only: Add a new font to be used by text output methods and return its :data:`xref`. If not already present in the file, the font definition will be added. Supported are the built-in :data:`Base14_Fonts` and the CJK fonts via **"reserved"** fontnames. Fonts can also be provided as a file path or a memory area containing the image of a font file.

      :arg str fontname: The name by which this font shall be referenced when outputting text on this page. In general, you have a "free" choice here (but consult the :ref:`AdobeManual`, page 56, section 3.2.4 for a formal description of building legal PDF names). However, if it matches one of the :data:`Base14_Fonts` or one of the CJK fonts, *fontfile* and *fontbuffer* **are ignored**.

      In other words, you cannot insert a font via *fontfile* / *fontbuffer* and also give it a reserved *fontname*.

      .. note:: A reserved fontname can be specified in any mixture of upper or lower case and still match the right built-in font definition: fontnames "helv", "Helv", "HELV", "Helvetica", etc. all lead to the same font definition "Helvetica". But from a :ref:`Page` perspective, these are **different references**. You can exploit this fact when using different *encoding* variants (Latin, Greek, Cyrillic) of the same font on a page.

      :arg str fontfile: a path to a font file. If used, *fontname* must be **different from all reserved names**.

      :arg bytes/bytearray fontbuffer: the memory image of a font file. If used, *fontname* must be **different from all reserved names**. This parameter would typically be used to transfer fonts between different pages of the same or different PDFs.

      :arg int set_simple: applicable for *fontfile* / *fontbuffer* cases only: enforce treatment as a "simple" font, i.e. one that only uses character codes up to 255.

      :arg int encoding: applicable for the "Helvetica", "Courier" and "Times" sets of :data:`Base14_Fonts` only. Select one of the available encodings Latin (0), Cyrillic (2) or Greek (1). Only use the default (0 = Latin) for "Symbol" and "ZapfDingBats".

      :rytpe: int
      :returns: the :data:`xref` of the installed font.

      .. note:: Built-in fonts will not lead to the inclusion of a font file. So the resulting PDF file will remain small. However, your PDF viewer software is responsible for generating an appropriate appearance -- and there **exist** differences on whether or how each one of them does this. This is especially true for the CJK fonts. But also Symbol and ZapfDingbats are incorrectly handled in some cases. Following are the **Font Names** and their correspondingly installed **Base Font** names:

         **Base-14 Fonts** [#f1]_

         ============= ============================ =========================================
         **Font Name** **Installed Base Font**      **Comments**
         ============= ============================ =========================================
         helv          Helvetica                    normal
         heit          Helvetica-Oblique            italic
         hebo          Helvetica-Bold               bold
         hebi          Helvetica-BoldOblique        bold-italic
         cour          Courier                      normal
         coit          Courier-Oblique              italic
         cobo          Courier-Bold                 bold
         cobi          Courier-BoldOblique          bold-italic
         tiro          Times-Roman                  normal
         tiit          Times-Italic                 italic
         tibo          Times-Bold                   bold
         tibi          Times-BoldItalic             bold-italic
         symb          Symbol                       [#f3]_
         zadb          ZapfDingbats                 [#f3]_
         ============= ============================ =========================================

         **CJK Fonts** [#f2]_ (China, Japan, Korea)

         ============= ============================ =========================================
         **Font Name** **Installed Base Font**      **Comments**
         ============= ============================ =========================================
         china-s       Heiti                        simplified Chinese
         china-ss      Song                         simplified Chinese (serif)
         china-t       Fangti                       traditional Chinese
         china-ts      Ming                         traditional Chinese (serif)
         japan         Gothic                       Japanese
         japan-s       Mincho                       Japanese (serif)
         korea         Dotum                        Korean
         korea-s       Batang                       Korean (serif)
         ============= ============================ =========================================

   .. index::
      pair: filename; insertImage
      pair: keep_proportion; insertImage
      pair: overlay; insertImage
      pair: pixmap; insertImage
      pair: rotate; insertImage
      pair: stream; insertImage

   .. method:: insertImage(rect, filename=None, pixmap=None, stream=None, rotate=0, keep_proportion=True, overlay=True)

      PDF only: Put an image inside the given rectangle. The image can be taken from a pixmap, a file or a memory area - of these parameters **exactly one** must be specified.

         Changed in version 1.14.11 By default, the image keeps its aspect ratio.

      :arg rect_like rect: where to put the image. Must be finite and not empty.
      
         *(Changed in v1.17.6)* Needs no longer have a non-empty intersection with the page's :attr:`Page.CropBox` [#f5]_.

         *(Changed in version 1.14.13)* The image is now always placed **centered** in the rectangle, i.e. the centers of image and rectangle are equal.

      :arg str filename: name of an image file (all formats supported by MuPDF -- see :ref:`ImageFiles`). If the same image is to be inserted multiple times, choose one of the other two options to avoid some overhead.

      :arg bytes,bytearray,io.BytesIO stream: image in memory (all formats supported by MuPDF -- see :ref:`ImageFiles`). This is the most efficient option.
      
         Changed in version 1.14.13 *io.BytesIO* is now also supported.

      :arg pixmap: a pixmap containing the image.
      :type pixmap: :ref:`Pixmap`

      :arg int rotate: *(new in version v1.14.11)* rotate the image. Must be an integer multiple of 90 degrees. If you need a rotation by an arbitrary angle, consider converting the image to a PDF (:meth:`Document.convertToPDF`) first and then use :meth:`Page.showPDFpage` instead.

      :arg bool keep_proportion: *(new in version v1.14.11)* maintain the aspect ratio of the image.

      For a description of *overlay* see :ref:`CommonParms`.

      This example puts the same image on every page of a document::

         >>> doc = fitz.open(...)
         >>> rect = fitz.Rect(0, 0, 50, 50)       # put thumbnail in upper left corner
         >>> img = open("some.jpg", "rb").read()  # an image file
         >>> for page in doc:
               page.insertImage(rect, stream = img)
         >>> doc.save(...)

      .. note::

         1. If that same image had already been present in the PDF, then only a reference to it will be inserted. This of course considerably saves disk space and processing time. But to detect this fact, existing PDF images need to be compared with the new one. This is achieved by storing an MD5 code for each image in a table and only compare the new image's MD5 code against the table entries. Generating this MD5 table, however, is done when the first image is inserted - which therefore may have an extended response time.

         2. You can use this method to provide a background or foreground image for the page, like a copyright, a watermark. Please remember, that watermarks require a transparent image ...

         3. The image may be inserted uncompressed, e.g. if a *Pixmap* is used or if the image has an alpha channel. Therefore, consider using *deflate=True* when saving the file.

         4. The image is stored in the PDF in its original quality. This may be much better than you ever need for your display. In this case consider decreasing the image size before inserting it -- e.g. by using the pixmap option and then shrinking it or scaling it down (see :ref:`Pixmap` chapter). The PIL method *Image.thumbnail()* can also be used for that purpose. The file size savings can be very significant.

         5. The most efficient way to display the same image on multiple pages is another method: :meth:`showPDFpage`. Consult :meth:`Document.convertToPDF` for how to obtain intermediary PDFs usable for that method. Demo script `fitz-logo.py <https://github.com/pymupdf/PyMuPDF-Utilities/tree/master/demo/fitz-logo.py>`_ implements a fairly complete approach.

   .. index::
      pair: blocks; getText
      pair: dict; getText
      pair: flags; getText
      pair: html; getText
      pair: json; getText
      pair: rawdict; getText
      pair: text; getText
      pair: words; getText
      pair: xhtml; getText
      pair: xml; getText

   .. method:: getText(opt="text", flags=None)

      Retrieves the content of a page in a variety of formats. This is a wrapper for :ref:`TextPage` methods by choosing the output option as follows:

      * "text" -- :meth:`TextPage.extractTEXT`, default
      * "blocks" -- :meth:`TextPage.extractBLOCKS`
      * "words" -- :meth:`TextPage.extractWORDS`
      * "html" -- :meth:`TextPage.extractHTML`
      * "xhtml" -- :meth:`TextPage.extractXHTML`
      * "xml" -- :meth:`TextPage.extractXML`
      * "dict" -- :meth:`TextPage.extractDICT`
      * "json" -- :meth:`TextPage.extractJSON`
      * "rawdict" -- :meth:`TextPage.extractRAWDICT`

      :arg str opt: A string indicating the requested format, one of the above. A mixture of upper and lower case is supported.

         Changed in version 1.16.3 Values "words" and "blocks" are now also accepted.

      :arg int flags: *(new in version 1.16.2)* indicator bits to control whether to include images or how text should be handled with respect to white spaces and ligatures. See :ref:`TextPreserve` for available indicators and :ref:`text_extraction_flags` for default settings.

      :rtype: *str, list, dict*
      :returns: The page's content as a string, list or as a dictionary. Refer to the corresponding :ref:`TextPage` method for details.

      .. note:: You can use this method as a **document conversion tool** from any supported document type (not only PDF!) to one of TEXT, HTML, XHTML or XML documents.

   .. index::
      pair: flags; getTextPage

   .. method:: getTextPage(flags=3)

      *(New in version 1.16.5)*
      
      Create a :ref:`TextPage` for the page. This method avoids using an intermediate :ref:`DisplayList`.

      :arg in flags: indicator bits controlling the content available for subsequent extraction -- see the parameter of :meth:`Page.getText`.

      :returns: :ref:`TextPage`

   .. method:: getFontList(full=False)

      PDF only: Return a list of fonts referenced by the page. Wrapper for :meth:`Document.getPageFontList`.

   .. method:: getImageList(full=False)

      PDF only: Return a list of images referenced by the page. Wrapper for :meth:`Document.getPageImageList`.

   .. method:: getImageBbox(item)

      PDF only: Return the boundary box of an image.

      *Changed in version 1.17.0:*

      * The method should deliver correct results now.
      * The page's ``/Contents`` are no longer modified by this method.
      
      :arg list,str item: an item of the list :meth:`Page.getImageList` with *full=True* specified, or the **name** entry of such an item, which is item[-3] (or item[7] respectively).

      :rtype: :ref:`Rect`
      :returns: the boundary box of the image.
         *(Changed in v1.16.7)* -- If the page in fact does not display this image, an infinite rectangle is returned now. In previous versions, an exception was raised.
         *(Changed in v.17.0)* -- Only images referenced directly by the page are considered. This means that images occurring in embedded PDF pages are ignored and an exception is raised.

      .. note::

         * Be aware that :meth:`Page.getImageList` may contain "dead" entries, i.e. there may be image references which are **not displayed** by this page. In this case an infinite rectangle is returned.
         * As mentioned above, images inside embedded PDF pages are ignored by this method.

   .. index::
      pair: matrix; getSVGimage

   .. method:: getSVGimage(matrix=fitz.Identity, text_as_path=True)

      Create an SVG image from the page. Only full page images are currently supported.

     :arg matrix_like matrix: a matrix, default is :ref:`Identity`.
     :arg bool text_as_path: *(new in v1.17.5)* -- controls how text is represented. *True* outputs each character as a series of elementary draw commands, which leads to a more precise text display in browsers, but a **very much larger** output for text-oriented pages. Display quality for *False* relies on the presence of the referenced fonts on the current system. For missing fonts, the internet browser will fall back to some default -- leading to unpleasant appearances. Choose *False* if you want to parse the text of the SVG.

     :returns: a UTF-8 encoded string that contains the image. Because SVG has XML syntax it can be saved in a text file with extension *.svg*.

   .. index::
      pair: alpha; getPixmap
      pair: annots; getPixmap
      pair: clip; getPixmap
      pair: colorspace; getPixmap
      pair: matrix; getPixmap

   .. method:: getPixmap(matrix=fitz.Identity, colorspace=fitz.csRGB, clip=None, alpha=False, annots=True)

     Create a pixmap from the page. This is probably the most often used method to create a :ref:`Pixmap`.

     :arg matrix_like matrix: default is :ref:`Identity`.
     :arg colorspace: Defines the required colorspace, one of "GRAY", "RGB" or "CMYK" (case insensitive). Or specify a :ref:`Colorspace`, ie. one of the predefined ones: :data:`csGRAY`, :data:`csRGB` or :data:`csCMYK`.
     :type colorspace: str or :ref:`Colorspace`
     :arg irect_like clip: restrict rendering to this area.
     :arg bool alpha: whether to add an alpha channel. Always accept the default *False* if you do not really need transparency. This will save a lot of memory (25% in case of RGB ... and pixmaps are typically **large**!), and also processing time. Also note an **important difference** in how the image will be rendered: with *True* the pixmap's samples area will be pre-cleared with *0x00*. This results in **transparent** areas where the page is empty. With *False* the pixmap's samples will be pre-cleared with *0xff*. This results in **white** where the page has nothing to show.

      Changed in version 1.14.17
         The default alpha value is now *False*.

         * Generated with *alpha=True*

         .. image:: images/img-alpha-1.png


         * Generated with *alpha=False*

         .. image:: images/img-alpha-0.png

     :arg bool annots: *(new in vrsion 1.16.0)* whether to also render annotations or to suppress them. You can create pixmaps for annotations separately.

     :rtype: :ref:`Pixmap`
     :returns: Pixmap of the page. For fine-controlling the generated image, the by far most important parameter is **matrix**. E.g. you can increase or decrease the image resolution by using **Matrix(xzoom, yzoom)**. If zoom > 1, you will get a higher resolution: zoom=2 will double the number of pixels in that direction and thus generate a 2 times larger image. Non-positive values will flip horizontally, resp. vertically. Similarly, matrices also let you rotate or shear, and you can combine effects via e.g. matrix multiplication. See the :ref:`Matrix` section to learn more.

   .. method:: annot_names()

      *(New in version 1.16.10)*

      PDF only: return a list of the names of annotations, widgets and links. Technically, these are the */NM* values of every PDF object found in the page's */Annots*  array.

      :rtype: list


   .. method:: annot_xrefs()

      *(New in version 1.17.1)*

      PDF only: return a list of the :data`xref` numbers of annotations, widgets and links -- technically of all entries found in the page's */Annots*  array.

      :rtype: list
      :returns: a list of items *(xref, type)* where type is the annotation type. Use the type to tell apart links, fields and annotations, see :ref:`AnnotationTypes`.


   .. method:: load_annot(ident)

      *(Deprecated since v1.17.1)*.

   .. method:: loadAnnot(ident)

      *(New in version 1.17.1)*

      PDF only: return the annotation identified by *ident*. This may be its unique name (PDF */NM* key), or its :data:`xref`.

      :arg str,int ident: the annotation name or xref.

      :rtype: :ref:`Annot`
      :returns: the annotation or *None*.

      .. note:: Methods :meth:`Page.annot_names`, :meth:`Page.annots_xrefs` provide lists of names or xrefs, respectively, from where an item may be picked and loaded via this method.

   .. method:: loadLinks()

      Return the first link on a page. Synonym of property :attr:`firstLink`.

      :rtype: :ref:`Link`
      :returns: first link on the page (or *None*).

   .. index::
      pair: rotate; setRotation

   .. method:: setRotation(rotate)

      PDF only: Sets the rotation of the page.

      :arg int rotate: An integer specifying the required rotation in degrees. Must be an integer multiple of 90. Values will be converted to one of 0, 90, 180, 270.

   .. index::
      pair: clip; showPDFpage
      pair: keep_proportion; showPDFpage
      pair: overlay; showPDFpage
      pair: rotate; showPDFpage

   .. method:: showPDFpage(rect, docsrc, pno=0, keep_proportion=True, overlay=True, rotate=0, clip=None)

      PDF only: Display a page of another PDF as a **vector image** (otherwise similar to :meth:`Page.insertImage`). This is a multi-purpose method. For example, you can use it to

      * create "n-up" versions of existing PDF files, combining several input pages into **one output page** (see example `4-up.py <https://github.com/pymupdf/PyMuPDF-Utilities/tree/master/examples/4-up.py>`_),
      * create "posterized" PDF files, i.e. every input page is split up in parts which each create a separate output page (see `posterize.py <https://github.com/pymupdf/PyMuPDF-Utilities/tree/master/examples/posterize.py>`_),
      * include PDF-based vector images like company logos, watermarks, etc., see `svg-logo.py <https://github.com/pymupdf/PyMuPDF-Utilities/tree/master/examples/svg-logo.py>`_, which puts an SVG-based logo on each page (requires additional packages to deal with SVG-to-PDF conversions).

      Changed in version 1.14.11
         Parameter *reuse_xref* has been deprecated.

      :arg rect_like rect: where to place the image on current page. Must be finite and its intersection with the page must not be empty.

          Changed in version 1.14.11
             Position the source rectangle centered in this rectangle.

      :arg docsrc: source PDF document containing the page. Must be a different document object, but may be the same file.
      :type docsrc: :ref:`Document`

      :arg int pno: page number (0-based, in *-inf < pno < docsrc.pageCount*) to be shown.

      :arg bool keep_proportion: whether to maintain the width-height-ratio (default). If false, all 4 corners are always positioned on the border of the target rectangle -- whatever the rotation value. In general, this will deliver distorted and /or non-rectangular images.

      :arg bool overlay: put image in foreground (default) or background.

      :arg float rotate: *(new in version 1.14.10)* show the source rectangle rotated by some angle. *Changed in version 1.14.11:* Any angle is now supported.

      :arg rect_like clip: choose which part of the source page to show. Default is the full page, else must be finite and its intersection with the source page must not be empty.

      .. note:: In contrast to method :meth:`Document.insertPDF`, this method does not copy annotations or links, so they are not shown. But all its **other resources (text, images, fonts, etc.)** will be imported into the current PDF. They will therefore appear in text extractions and in :meth:`getFontList` and :meth:`getImageList` lists -- even if they are not contained in the visible area given by *clip*.

      Example: Show the same source page, rotated by 90 and by -90 degrees:

      >>> doc = fitz.open()  # new empty PDF
      >>> page=doc.newPage()  # new page in A4 format
      >>>
      >>> # upper half page
      >>> r1 = fitz.Rect(0, 0, page.rect.width, page.rect.height/2)
      >>>
      >>> # lower half page
      >>> r2 = r1 + (0, page.rect.height/2, 0, page.rect.height/2)
      >>>
      >>> src = fitz.open("PyMuPDF.pdf")  # show page 0 of this
      >>>
      >>> page.showPDFpage(r1, src, 0, rotate=90)
      >>> page.showPDFpage(r2, src, 0, rotate=-90)
      >>> doc.save("show.pdf")

      .. image:: images/img-showpdfpage.jpg
         :scale: 70

   .. method:: newShape()

      PDF only: Create a new :ref:`Shape` object for the page.

      :rtype: :ref:`Shape`
      :returns: a new :ref:`Shape` to use for compound drawings. See description there.


   .. index::
      pair: flags; searchFor
      pair: hit_max; searchFor
      pair: quads; searchFor

   .. method:: searchFor(text, hit_max=16, quads=False, flags=None)

      Searches for *text* on a page. Wrapper for :meth:`TextPage.search`.

      :arg str text: Text to search for. Upper / lower case is ignored. The string may contain spaces.

      :arg int hit_max: Maximum number of returned occurrences.
      :arg bool quads: Return :ref:`Quad` instead of :ref:`Rect` objects.
      :arg int flags: Control the data extracted by the underlying :ref:`TextPage`. Default is 0 (ligatures are dissolved, white space is replaced with space and excessive spaces are not suppressed).

      :rtype: list

      :returns: A list of :ref:`Rect` \s (resp. :ref:`Quad` \s) each of which  -- **normally!** -- surrounds one occurrence of *text*. **However:** if the search string spreads across more than one line, then a separate item is recorded in the list for each part of the string per line. So, if you are looking for "search string" and the two words happen to be located on separate lines, two entries will be recorded in the list: one for "search" and one for "string".

        .. note:: In this way, the effect supports multi-line text marker annotations.

        .. note:: The number of returned objects will never exceed *hit_max*. Hence, if the returned list has this many items, you cannot know whether there really exist more on the page. So please make sure you provide a hit_max value which is large enough.

        .. note:: Please also be aware of a trickier aspect: the search logic regards **contiguous multiple** occurrences of the search string as one: assuming your search string is "abc", and the page contains "abc" and "abcabc", then only **two** rectangles will be returned, one containing "abc", and a second one containing "abcabc".


   .. method:: setMediaBox(r)

      PDF only: *(New in v1.16.13)* Change the physical page dimension by setting :data:`MediaBox` in the page's object definition.

      :arg rect-like r: the new :data:`MediaBox` value.

      .. note:: This method also sets the page's :data:`CropBox` to the same value -- to prevent mismatches caused by values further up in the parent hierarchy.

      .. caution:: For existing pages this may have unexpected effects, if painting commands depend on a certain setting, and may lead to an empty or distorted appearance.


   .. method:: setCropBox(r)

      PDF only: change the visible part of the page.

      :arg rect_like r: the new visible area of the page. Note that this **must** be specified in **unrotated coordinates**.

      After execution if the page is not rotated, :attr:`Page.rect` will equal this rectangle, shifted to the top-left position (0, 0). Example session:

      >>> page = doc.newPage()
      >>> page.rect
      fitz.Rect(0.0, 0.0, 595.0, 842.0)
      >>>
      >>> page.CropBox                   # CropBox and MediaBox still equal
      fitz.Rect(0.0, 0.0, 595.0, 842.0)
      >>>
      >>> # now set CropBox to a part of the page
      >>> page.setCropBox(fitz.Rect(100, 100, 400, 400))
      >>> # this will also change the "rect" property:
      >>> page.rect
      fitz.Rect(0.0, 0.0, 300.0, 300.0)
      >>>
      >>> # but MediaBox remains unaffected
      >>> page.MediaBox
      fitz.Rect(0.0, 0.0, 595.0, 842.0)
      >>>
      >>> # revert everything we did
      >>> page.setCropBox(page.MediaBox)
      >>> page.rect
      fitz.Rect(0.0, 0.0, 595.0, 842.0)

   .. attribute:: rotation

      Contains the rotation of the page in degrees (always 0 for non-PDF types).

      :type: int

   .. attribute:: CropBoxPosition

      Contains the top-left point of the page's */CropBox* for a PDF, otherwise *Point(0, 0)*.

      :type: :ref:`Point`

   .. attribute:: CropBox

      The page's */CropBox* for a PDF. Always the **unrotated** page rectangle is returned. For a non-PDF this will always equal the page rectangle.

      :type: :ref:`Rect`

   .. attribute:: MediaBoxSize

      Contains the width and height of the page's :attr:`Page.MediaBox` for a PDF, otherwise the bottom-right coordinates of :attr:`Page.rect`.

      :type: :ref:`Point`

   .. attribute:: MediaBox

      The page's :data:`MediaBox` for a PDF, otherwise :attr:`Page.rect`.

      :type: :ref:`Rect`

      .. note:: For most PDF documents and for **all other document types**, *page.rect == page.CropBox == page.MediaBox* is true. However, for some PDFs the visible page is a true subset of :data:`MediaBox`. Also, if the page is rotated, its ``Page.rect`` may not equal ``Page.CropBox``. In these cases the above attributes help to correctly locate page elements.

   .. attribute:: transformationMatrix

      This matrix translates coordinates from the PDF space to the MuPDF space. For example, in PDF ``/Rect [x0 y0 x1 y1]`` the pair (x0, y0) specifies the **bottom-left** point of the rectangle -- in contrast to MuPDF's system, where (x0, y0) specify top-left. Multiplying the PDF coordinates with this matrix will deliver the (Py-) MuPDF rectangle version. Obviously, the inverse matrix will again yield the PDF rectangle.

      :type: :ref:`Matrix`

   .. attribute:: rotationMatrix

   .. attribute:: derotationMatrix

      These matrices may be used for dealing with rotated PDF pages. When adding / inserting anything to a PDF page with PyMuPDF, the coordinates of the **unrotated** page are always used. These matrices help translating between the two states. Example: if a page is rotated by 90 degrees -- what would then be the coordinates of the top-left Point(0, 0) of an A4 page?

         >>> page.setRotation(90)  # rotate an ISO A4 page
         >>> page.rect
         Rect(0.0, 0.0, 842.0, 595.0)
         >>> p = fitz.Point(0, 0)  # where did top-left point land?
         >>> p * page.rotationMatrix
         Point(842.0, 0.0)
         >>> 

      :type: :ref:`Matrix`

   .. attribute:: firstLink

      Contains the first :ref:`Link` of a page (or *None*).

      :type: :ref:`Link`

   .. attribute:: firstAnnot

      Contains the first :ref:`Annot` of a page (or *None*).

      :type: :ref:`Annot`

   .. attribute:: firstWidget

      Contains the first :ref:`Widget` of a page (or *None*).

      :type: :ref:`Widget`

   .. attribute:: number

      The page number.

      :type: int

   .. attribute:: parent

      The owning document object.

      :type: :ref:`Document`


   .. attribute:: rect

      Contains the rectangle of the page. Same as result of :meth:`Page.bound()`.

      :type: :ref:`Rect`

   .. attribute:: xref

      The page's PDF :data:`xref`. Zero if not a PDF.

      :type: :ref:`Rect`

-----

Description of *getLinks()* Entries
----------------------------------------
Each entry of the *getLinks()* list is a dictionay with the following keys:

* *kind*:  (required) an integer indicating the kind of link. This is one of *LINK_NONE*, *LINK_GOTO*, *LINK_GOTOR*, *LINK_LAUNCH*, or *LINK_URI*. For values and meaning of these names refer to :ref:`linkDest Kinds`.

* *from*:  (required) a :ref:`Rect` describing the "hot spot" location on the page's visible representation (where the cursor changes to a hand image, usually).

* *page*:  a 0-based integer indicating the destination page. Required for *LINK_GOTO* and *LINK_GOTOR*, else ignored.

* *to*:   either a *fitz.Point*, specifying the destination location on the provided page, default is *fitz.Point(0, 0)*, or a symbolic (indirect) name. If an indirect name is specified, *page = -1* is required and the name must be defined in the PDF in order for this to work. Required for *LINK_GOTO* and *LINK_GOTOR*, else ignored.

* *file*: a string specifying the destination file. Required for *LINK_GOTOR* and *LINK_LAUNCH*, else ignored.

* *uri*:  a string specifying the destination internet resource. Required for *LINK_URI*, else ignored.

* *xref*: an integer specifying the PDF :data:`xref` of the link object. Do not change this entry in any way. Required for link deletion and update, otherwise ignored. For non-PDF documents, this entry contains *-1*. It is also *-1* for **all** entries in the *getLinks()* list, if **any** of the links is not supported by MuPDF - see the note below.

Notes on Supporting Links
---------------------------
MuPDF's support for links has changed in **v1.10a**. These changes affect link types :data:`LINK_GOTO` and :data:`LINK_GOTOR`.

Reading (pertains to method *getLinks()* and the *firstLink* property chain)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If MuPDF detects a link to another file, it will supply either a *LINK_GOTOR* or a *LINK_LAUNCH* link kind. In case of *LINK_GOTOR* destination details may either be given as page number (eventually including position information), or as an indirect destination.

If an indirect destination is given, then this is indicated by *page = -1*, and *link.dest.dest* will contain this name. The dictionaries in the *getLinks()* list will contain this information as the *to* value.

**Internal links are always** of kind *LINK_GOTO*. If an internal link specifies an indirect destination, it **will always be resolved** and the resulting direct destination will be returned. Names are **never returned for internal links**, and undefined destinations will cause the link to be ignored.

Writing
~~~~~~~~~

PyMuPDF writes (updates, inserts) links by constructing and writing the appropriate PDF object **source**. This makes it possible to specify indirect destinations for *LINK_GOTOR* **and** *LINK_GOTO* link kinds (pre *PDF 1.2* file formats are **not supported**).

.. warning:: If a *LINK_GOTO* indirect destination specifies an undefined name, this link can later on not be found / read again with MuPDF / PyMuPDF. Other readers however **will** detect it, but flag it as erroneous.

Indirect *LINK_GOTOR* destinations can in general of course not be checked for validity and are therefore **always accepted**.

Homologous Methods of :ref:`Document` and :ref:`Page`
--------------------------------------------------------
This is an overview of homologous methods on the :ref:`Document` and on the :ref:`Page` level.

====================================== =====================================
**Document Level**                     **Page Level**
====================================== =====================================
*Document.getPageFontlist(pno)*        :meth:`Page.getFontList`
*Document.getPageImageList(pno)*       :meth:`Page.getImageList`
*Document.getPagePixmap(pno, ...)*     :meth:`Page.getPixmap`
*Document.getPageText(pno, ...)*       :meth:`Page.getText`
*Document.searchPageFor(pno, ...)*     :meth:`Page.searchFor`
====================================== =====================================

The page number "pno" is a 0-based integer *-inf < pno < pageCount*.

.. note::

   Most document methods (left column) exist for convenience reasons, and are just wrappers for: *Document[pno].<page method>*. So they **load and discard the page** on each execution.

   However, the first two methods work differently. They only need a page's object definition statement - the page itself will **not** be loaded. So e.g. :meth:`Page.getFontList` is a wrapper the other way round and defined as follows: *page.getFontList == page.parent.getPageFontList(page.number)*.

.. rubric:: Footnotes

.. [#f1] If your existing code already uses the installed base name as a font reference (as it was supported by PyMuPDF versions earlier than 1.14), this will continue to work.

.. [#f2] Not all PDF reader software (including internet browsers and office software) display all of these fonts. And if they do, the difference between the **serifed** and the **non-serifed** version may hardly be noticable. But serifed and non-serifed versions lead to different installed base fonts, thus providing an option to be displayable with your specific PDF viewer.

.. [#f3] Not all PDF readers display these fonts at all. Some others do, but use a wrong character spacing, etc.

.. [#f4] You are generally free to choose any of the :ref:`mupdficons` you consider adequate.

.. [#f5] The previous algorithm caused images to be **shrunk** to this intersection. Now the image can be anywhere on :attr:`Page.MediaBox`, potentially being invisible or only partially visible if the cropbox (representing the visible page part) is smaller.
