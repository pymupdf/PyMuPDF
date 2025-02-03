.. include:: header.rst

.. _Page:

================
Page
================

Class representing a document page. A page object is created by :meth:`Document.load_page` or, equivalently, via indexing the document like `doc[n]` - it has no independent constructor.

There is a parent-child relationship between a document and its pages. If the document is closed or deleted, all page objects (and their respective children, too) in existence will become unusable ("orphaned"): If a page property or method is being used, an exception is raised.

Several page methods have a :ref:`Document` counterpart for convenience. At the end of this chapter you will find a synopsis.

.. note:: Many times in this chapter we are using the term **coordinate**. It is of high importance to have at least a basic understanding of what that is and that you feel comfortable with the section :ref:`Coordinates`.

Modifying Pages
---------------
Changing page properties and adding or changing page content is available for PDF documents only.

In a nutshell, this is what you can do with PyMuPDF:

* Modify page rotation and the visible part ("cropbox") of the page.
* Insert images, other PDF pages, text and simple geometrical objects.
* Add annotations and form fields.

.. note::

   Methods require coordinates (points, rectangles) to put content in desired places. Please be aware that these coordinates **must always** be provided relative to the **unrotated** page (since v1.17.0). The reverse is also true: except :attr:`Page.rect`, resp. :meth:`Page.bound` (both *reflect* when the page is rotated), all coordinates returned by methods and attributes pertain to the unrotated page.

   So the returned value of e.g. :meth:`Page.get_image_bbox` will not change if you do a :meth:`Page.set_rotation`. The same is true for coordinates returned by :meth:`Page.get_text`, annotation rectangles, and so on. If you want to find out, where an object is located in **rotated coordinates**, multiply the coordinates with :attr:`Page.rotation_matrix`. There also is its inverse, :attr:`Page.derotation_matrix`, which you can use when interfacing with other readers, which may behave differently in this respect.

.. note::

   If you add or update annotations, links or form fields on the page and immediately afterwards need to work with them (i.e. **without leaving the page**), you should reload the page using :meth:`Document.reload_page` before referring to these new or updated items.

   Reloading the page is generally recommended -- although not strictly required in all cases. However, some annotation and widget types have extended features in PyMuPDF compared to MuPDF. More of these extensions may also be added in the future.

   Releoading the page ensures all your changes have been fully applied to PDF structures, so you can safely create Pixmaps or successfully iterate over annotations, links and form fields.

================================== =======================================================
**Method / Attribute**             **Short Description**
================================== =======================================================
:meth:`Page.add_caret_annot`       PDF only: add a caret annotation
:meth:`Page.add_circle_annot`      PDF only: add a circle annotation
:meth:`Page.add_file_annot`        PDF only: add a file attachment annotation
:meth:`Page.add_freetext_annot`    PDF only: add a text annotation
:meth:`Page.add_highlight_annot`   PDF only: add a "highlight" annotation
:meth:`Page.add_ink_annot`         PDF only: add an ink annotation
:meth:`Page.add_line_annot`        PDF only: add a line annotation
:meth:`Page.add_polygon_annot`     PDF only: add a polygon annotation
:meth:`Page.add_polyline_annot`    PDF only: add a multi-line annotation
:meth:`Page.add_rect_annot`        PDF only: add a rectangle annotation
:meth:`Page.add_redact_annot`      PDF only: add a redaction annotation
:meth:`Page.add_squiggly_annot`    PDF only: add a "squiggly" annotation
:meth:`Page.add_stamp_annot`       PDF only: add a "rubber stamp" annotation
:meth:`Page.add_strikeout_annot`   PDF only: add a "strike-out" annotation
:meth:`Page.add_text_annot`        PDF only: add a comment
:meth:`Page.add_underline_annot`   PDF only: add an "underline" annotation
:meth:`Page.add_widget`            PDF only: add a PDF Form field
:meth:`Page.annot_names`           PDF only: a list of annotation (and widget) names
:meth:`Page.annot_xrefs`           PDF only: a list of annotation (and widget) xrefs
:meth:`Page.annots`                return a generator over the annots on the page
:meth:`Page.apply_redactions`      PDF only: process the redactions of the page
:meth:`Page.bound`                 rectangle of the page
:meth:`Page.cluster_drawings`      PDF only: bounding boxes of vector graphics
:meth:`Page.delete_annot`          PDF only: delete an annotation
:meth:`Page.delete_image`          PDF only: delete an image
:meth:`Page.delete_link`           PDF only: delete a link
:meth:`Page.delete_widget`         PDF only: delete a widget / field
:meth:`Page.draw_bezier`           PDF only: draw a cubic Bezier curve
:meth:`Page.draw_circle`           PDF only: draw a circle
:meth:`Page.draw_curve`            PDF only: draw a special Bezier curve
:meth:`Page.draw_line`             PDF only: draw a line
:meth:`Page.draw_oval`             PDF only: draw an oval / ellipse
:meth:`Page.draw_polyline`         PDF only: connect a point sequence
:meth:`Page.draw_quad`             PDF only: draw a quad
:meth:`Page.draw_rect`             PDF only: draw a rectangle
:meth:`Page.draw_sector`           PDF only: draw a circular sector
:meth:`Page.draw_squiggle`         PDF only: draw a squiggly line
:meth:`Page.draw_zigzag`           PDF only: draw a zig-zagged line
:meth:`Page.find_tables`           locate tables on the page
:meth:`Page.get_drawings`          get vector graphics on page
:meth:`Page.get_fonts`             PDF only: get list of referenced fonts
:meth:`Page.get_image_bbox`        PDF only: get bbox and matrix of embedded image
:meth:`Page.get_image_info`        get list of meta information for all used images
:meth:`Page.get_image_rects`       PDF only: improved version of :meth:`Page.get_image_bbox`
:meth:`Page.get_images`            PDF only: get list of referenced images
:meth:`Page.get_label`             PDF only: return the label of the page
:meth:`Page.get_links`             get all links
:meth:`Page.get_pixmap`            create a page image in raster format
:meth:`Page.get_svg_image`         create a page image in SVG format
:meth:`Page.get_text`              extract the page's text
:meth:`Page.get_textbox`           extract text contained in a rectangle
:meth:`Page.get_textpage_ocr`      create a TextPage with OCR for the page
:meth:`Page.get_textpage`          create a TextPage for the page
:meth:`Page.get_xobjects`          PDF only: get list of referenced xobjects
:meth:`Page.insert_font`           PDF only: insert a font for use by the page
:meth:`Page.insert_image`          PDF only: insert an image
:meth:`Page.insert_link`           PDF only: insert a link
:meth:`Page.insert_text`           PDF only: insert text
:meth:`Page.insert_htmlbox`        PDF only: insert html text in a rectangle
:meth:`Page.insert_textbox`        PDF only: insert a text box
:meth:`Page.links`                 return a generator of the links on the page
:meth:`Page.load_annot`            PDF only: load a specific annotation
:meth:`Page.load_widget`           PDF only: load a specific field
:meth:`Page.load_links`            return the first link on a page
:meth:`Page.new_shape`             PDF only: create a new :ref:`Shape`
:meth:`Page.remove_rotation`       PDF only: set page rotation to 0
:meth:`Page.replace_image`         PDF only: replace an image
:meth:`Page.search_for`            search for a string
:meth:`Page.set_artbox`            PDF only: modify `/ArtBox`
:meth:`Page.set_bleedbox`          PDF only: modify `/BleedBox`
:meth:`Page.set_cropbox`           PDF only: modify the :data:`cropbox` (visible page)
:meth:`Page.set_mediabox`          PDF only: modify `/MediaBox`
:meth:`Page.set_rotation`          PDF only: set page rotation
:meth:`Page.set_trimbox`           PDF only: modify `/TrimBox`
:meth:`Page.show_pdf_page`         PDF only: display PDF page image
:meth:`Page.update_link`           PDF only: modify a link
:meth:`Page.widgets`               return a generator over the fields on the page
:meth:`Page.write_text`            write one or more :ref:`Textwriter` objects
:attr:`Page.cropbox_position`      displacement of the :data:`cropbox`
:attr:`Page.cropbox`               the page's :data:`cropbox`
:attr:`Page.artbox`                the page's `/ArtBox`
:attr:`Page.bleedbox`              the page's `/BleedBox`
:attr:`Page.trimbox`               the page's `/TrimBox`
:attr:`Page.derotation_matrix`     PDF only: get coordinates in unrotated page space
:attr:`Page.first_annot`           first :ref:`Annot` on the page
:attr:`Page.first_link`            first :ref:`Link` on the page
:attr:`Page.first_widget`          first widget (form field) on the page
:attr:`Page.mediabox_size`         bottom-right point of :data:`mediabox`
:attr:`Page.mediabox`              the page's :data:`mediabox`
:attr:`Page.number`                page number
:attr:`Page.parent`                owning document object
:attr:`Page.rect`                  rectangle of the page
:attr:`Page.rotation_matrix`       PDF only: get coordinates in rotated page space
:attr:`Page.rotation`              PDF only: page rotation
:attr:`Page.transformation_matrix` PDF only: translate between PDF and MuPDF space
:attr:`Page.xref`                  PDF only: page :data:`xref`
================================== =======================================================

**Class API**

.. class:: Page

   .. method:: bound()

      Determine the rectangle of the page. Same as property :attr:`Page.rect`. For PDF documents this **usually** also coincides with :data:`mediabox` and :data:`cropbox`, but not always. For example, if the page is rotated, then this is reflected by this method -- the :attr:`Page.cropbox` however will not change.

      :rtype: :ref:`Rect`

   .. method:: add_caret_annot(point)

      PDF only: Add a caret icon. A caret annotation is a visual symbol normally used to indicate the presence of text edits on the page.

      :arg point_like point: the top left point of a 20 x 20 rectangle containing the MuPDF-provided icon.

      :rtype: :ref:`Annot`
      :returns: the created annotation. Stroke color blue = (0, 0, 1), no fill color support.

      .. image:: images/img-caret-annot.*
         :scale: 70

      |history_begin|

      * New in v1.16.0

      |history_end|

   .. method:: add_text_annot(point, text, icon="Note")

      PDF only: Add a comment icon ("sticky note") with accompanying text. Only the icon is visible, the accompanying text is hidden and can be visualized by many PDF viewers by hovering the mouse over the symbol.

      :arg point_like point: the top left point of a 20 x 20 rectangle containing the MuPDF-provided "note" icon.

      :arg str text: the commentary text. This will be shown on double clicking or hovering over the icon. May contain any Latin characters.
      :arg str icon: choose one of "Note" (default), "Comment", "Help", "Insert", "Key", "NewParagraph", "Paragraph" as the visual symbol for the embodied text [#f4]_. (New in v1.16.0)

      :rtype: :ref:`Annot`
      :returns: the created annotation. Stroke color yellow = (1, 1, 0), no fill color support.

   .. index::
      pair: rect; add_freetext_annot
      pair: fontsize; add_freetext_annot
      pair: fontname; add_freetext_annot
      pair: text_color; add_freetext_annot
      pair: fill_color; add_freetext_annot
      pair: border_width; add_freetext_annot
      pair: dashes; add_freetext_annot
      pair: callout; add_freetext_annot
      pair: line_end; add_freetext_annot
      pair: opacity; add_freetext_annot
      pair: align; add_freetext_annot
      pair: rotate; add_freetext_annot
      pair: richtext; add_freetext_annot
      pair: style; add_freetext_annot

   .. method:: add_freetext_annot(rect, text, *, fontsize=11, fontname="helv", text_color=0, fill_color=None, border_width=0, dashes=None, callout=None, line_end=PDF_ANNOT_LE_OPEN_ARROW, opacity=1, align=TEXT_ALIGN_LEFT, rotate=0, richtext=False, style=None)

      PDF only: Add text in a given rectangle. Optionally, the appearance of a "callout" shape can be requested by specifying two or three point-like objects -- see below.

      :arg rect_like rect: the rectangle into which the text should be inserted. Text is automatically wrapped to a new line at box width. Text portions not fitting into the rectangle will be invisible without warning.

      :arg str text: the text. May contain any mixture of Latin, Greek, Cyrillic, Chinese, Japanese and Korean characters. If `richtext=True` (see below), the string is interpreted as HTML syntax. This adds a plethora of ways for attractive effects.

      :arg float fontsize: the :data:`fontsize`. Default is 11. Ignored if `richtext=True`.

      :arg str fontname: The font name. Default is "Helv". Ignored if `richtext=True`, otherwise the following **restritions apply:**
        
        * Accepted alternatives are "Helv" (Helvetica), "Cour" (Courier), "TiRo" (Timnes-Roman), "ZaDb" (ZapfDingBats) and "Symb" (Symbol). The name may be abbreviated to the first two characters, like "Co" for "Cour", lower case accepted.

        * Bold or italic variants of the fonts are **not supported.**
        
      :arg list,tuple,float text_color: the text color. Default is black. Ignored if `richtext=True`.

      :arg list,tuple,float fill_color: the fill color. This is used for ``rect`` and the end point of the callout lines when applicable. Default is ``None``.

      :arg list,tuple,float border_color:  This parameter only has an effect if `richtext=True`. Otherwise, ``text_color`` is used.
      
      :arg float border_width: the width of border and ``callout`` lines. Default is 0 (no border), in which case callout lines may still appear with some hairline width, depending on the PDF viewer used.
      
      :arg list,tuple dashes: a list of floats specifying how border and callout lines should be dashed. Default is ``None``.
      
      :arg list,tuple callout: a list / tuple of two or three :data:`point_like` objects, which will be interpreted as end point [, knee point] and start point (in this sequence) of up to two line segments, converting this annotation into a call-out shape.
      
      :arg int line_end: the line end symbol of the call-out line. It is drawn at the first point specified in the `callout` list. Default is an open arrow. For possible values see :ref:`AnnotationLineEnds`.
      
      :arg float opacity: a float `0 <= opacity < 1` turning the annotation transparent. Default is no transparency.
      
      :arg int align: text alignment, one of TEXT_ALIGN_LEFT, TEXT_ALIGN_CENTER, TEXT_ALIGN_RIGHT - justify is **not supported**. Ignored if `richtext=True`.
      
      :arg int rotate: the text orientation. Accepted values are integer multiples of 90°. Invalid entries receive a rotation of 0.
      
      :arg bool richtext: treat ``text`` as HTML syntax. This allows to achieve **bold**, *italic*, arbitrary text colors, font sizes, text alignment including justify and more - as far as HTML and styling instructions support this. This is similar to what happens in :meth:`Page.insert_htmlbox`. The base library will for example pull in required fonts if it encounters characters not contained in the standard ones. Some parameters are ignored if this option is set, as mentioned above. Default is ``False``.
      
      :arg str style: supply optional HTML styling information in CSS syntax. Ignored if `richtext=False`.

      :rtype: :ref:`Annot`
      :returns: the created annotation.

      |history_begin|

      * Changed in v1.19.6: add border color parameter

      |history_end|

   .. method:: add_file_annot(pos, buffer, filename, ufilename=None, desc=None, icon="PushPin")

      PDF only: Add a file attachment annotation with a "PushPin" icon at the specified location.

      :arg point_like pos: the top-left point of a 18x18 rectangle containing the MuPDF-provided "PushPin" icon.

      :arg bytes,bytearray,BytesIO buffer: the data to be stored (actual file content, any data, etc.).

         Changed in v1.14.13: *io.BytesIO* is now also supported.

      :arg str filename: the filename to associate with the data.
      :arg str ufilename: the optional PDF unicode version of filename. Defaults to filename.
      :arg str desc: an optional description of the file. Defaults to filename.
      :arg str icon: choose one of "PushPin" (default), "Graph", "Paperclip", "Tag" as the visual symbol for the attached data [#f4]_. (New in v1.16.0)

      :rtype: :ref:`Annot`
      :returns: the created annotation.  Stroke color yellow = (1, 1, 0), no fill color support.

   .. method:: add_ink_annot(list)

      PDF only: Add a "freehand" scribble annotation.

      :arg sequence list: a list of one or more lists, each containing :data:`point_like` items. Each item in these sublists is interpreted as a :ref:`Point` through which a connecting line is drawn. Separate sublists thus represent separate drawing lines.

      :rtype: :ref:`Annot`
      :returns: the created annotation in default appearance black =(0, 0, 0),line width 1. No fill color support.

   .. method:: add_line_annot(p1, p2)

      PDF only: Add a line annotation.

      :arg point_like p1: the starting point of the line.

      :arg point_like p2: the end point of the line.

      :rtype: :ref:`Annot`
      :returns: the created annotation. It is drawn with line (stroke) color red = (1, 0, 0) and line width 1. No fill color support. The **annot rectangle** is automatically created to contain both points, each one surrounded by a circle of radius 3 * line width to make room for any line end symbols.

   .. method:: add_rect_annot(rect)

   .. method:: add_circle_annot(rect)

      PDF only: Add a rectangle, resp. circle annotation.

      :arg rect_like rect: the rectangle in which the circle or rectangle is drawn, must be finite and not empty. If the rectangle is not equal-sided, an ellipse is drawn.

      :rtype: :ref:`Annot`
      :returns: the created annotation. It is drawn with line (stroke) color red = (1, 0, 0), line width 1, fill color is supported.

   ---------

   Redactions
   ~~~~~~~~~~~

   .. method:: add_redact_annot(quad, text=None, fontname=None, fontsize=11, align=TEXT_ALIGN_LEFT, fill=(1, 1, 1), text_color=(0, 0, 0), cross_out=True)
      
      **PDF only**: Add a redaction annotation. A redaction annotation identifies content to be removed from the document. Adding such an annotation is the first of two steps. It makes visible what will be removed in the subsequent step, :meth:`Page.apply_redactions`.

      :arg quad_like,rect_like quad: specifies the (rectangular) area to be removed which is always equal to the annotation rectangle. This may be a :data:`rect_like` or :data:`quad_like` object. If a quad is specified, then the enveloping rectangle is taken.

      :arg str text: text to be placed in the rectangle after applying the redaction (and thus removing old content). (New in v1.16.12)

      :arg str fontname: the font to use when *text* is given, otherwise ignored. The same rules apply as for :meth:`Page.insert_textbox` -- which is the method :meth:`Page.apply_redactions` internally invokes. The replacement text will be **vertically centered**, if this is one of the CJK or :ref:`Base-14-Fonts`. (New in v1.16.12)

         .. note::

            * For an **existing** font of the page, use its reference name as *fontname* (this is *item[4]* of its entry in :meth:`Page.get_fonts`).
            * For a **new, non-builtin** font, proceed as follows::

               page.insert_text(point,  # anywhere, but outside all redaction rectangles
                   "something",  # some non-empty string
                   fontname="newname",  # new, unused reference name
                   fontfile="...",  # desired font file
                   render_mode=3,  # makes the text invisible
               )
               page.add_redact_annot(..., fontname="newname")

      :arg float fontsize: the :data:`fontsize` to use for the replacing text. If the text is too large to fit, several insertion attempts will be made, gradually reducing the :data:`fontsize` to no less than 4. If then the text will still not fit, no text insertion will take place at all. (New in v1.16.12)

      :arg int align: the horizontal alignment for the replacing text. See :meth:`insert_textbox` for available values. The vertical alignment is (approximately) centered if a PDF built-in font is used (CJK or :ref:`Base-14-Fonts`). (New in v1.16.12)

      :arg sequence fill: the fill color of the rectangle **after applying** the redaction. The default is *white = (1, 1, 1)*, which is also taken if ``None`` is specified. To suppress a fill color altogether, specify ``False``. In this cases the rectangle remains transparent. (New in v1.16.12)

      :arg sequence text_color: the color of the replacing text. Default is *black = (0, 0, 0)*. (New in v1.16.12)

      :arg bool cross_out: add two diagonal lines to the annotation rectangle. (New in v1.17.2)

      :rtype: :ref:`Annot`
      :returns: the created annotation. Its standard appearance looks like a red rectangle (no fill color), optionally showing two diagonal lines. Colors, line width, dashing, opacity and blend mode can now be set and applied via :meth:`Annot.update` like with other annotations. (Changed in v1.17.2)

      .. image:: images/img-redact.*

      |history_begin|

      * New in v1.16.11

      |history_end|


      .. method:: apply_redactions(images=PDF_REDACT_IMAGE_PIXELS|2, graphics=PDF_REDACT_LINE_ART_REMOVE_IF_TOUCHED|2, text=PDF_REDACT_TEXT_REMOVE|0)

      **PDF only**: Remove all **content** contained in any redaction rectangle on the page.

      **This method applies and then deletes all redactions from the page.**

      :arg int images: How to redact overlapping images. The default (2) blanks out overlapping pixels. `PDF_REDACT_IMAGE_NONE | 0` ignores, and `PDF_REDACT_IMAGE_REMOVE | 1` completely removes images overlapping any redaction annotation. Option `PDF_REDACT_IMAGE_REMOVE_UNLESS_INVISIBLE | 3` only removes images that are actually visible.

      :arg int graphics: How to redact overlapping vector graphics (also called "line-art" or "drawings"). The default (2) removes any overlapping vector graphics. `PDF_REDACT_LINE_ART_NONE | 0` ignores, and `PDF_REDACT_LINE_ART_REMOVE_IF_COVERED | 1` removes graphics fully contained in a redaction annotation. When removing line-art, please be aware that **stroked** vector graphics (i.e. type "s" or "sf") have a **larger wrapping rectangle** than one might expect: first of all, at least 50% of the path's line width have to be added in each direction to truly include all of the drawing. If a so-called "miter limit" is provided (see page 121 of the PDF specification), the enlarging value is `miter * width / 2`. So, when letting everything default (width = 1, miter = 10), the redaction rectangle should be at least 5 points larger in every direction.

      :arg int text: Whether to redact overlapping text. The default `PDF_REDACT_TEXT_REMOVE | 0` removes all characters whose boundary box overlaps any redaction rectangle. This complies with the original legal / data protection intentions of redaction annotations. Other use cases however may require to **keep text** while redacting vector graphics or images. This can be achieved by setting `text=True|PDF_REDACT_TEXT_NONE | 1`. This does **not comply** with the data protection intentions of redaction annotations. **Do so at your own risk.**

      :returns: `True` if at least one redaction annotation has been processed, `False` otherwise.

      .. note::
         * Text contained in a redaction rectangle will be **physically** removed from the page (assuming :meth:`Document.save` with a suitable garbage option) and will no longer appear in e.g. text extractions or anywhere else. All redaction annotations will also be removed. Other annotations are unaffected.

         * All overlapping links will be removed. If the rectangle of the link was covering text, then only the overlapping part of the text is being removed. Similar applies to images covered by link rectangles.

         * The overlapping parts of **images** will be blanked-out for default option `PDF_REDACT_IMAGE_PIXELS` (changed in v1.18.0). Option 0 does not touch any images and 1 will remove any image with an overlap.

         * For option `images=PDF_REDACT_IMAGE_REMOVE` only this page's **references to the images** are removed - not necessarily the images themselves. Images are completely removed from the file only, if no longer referenced at all (assuming suitable garbage collection options).

         * For option `images=PDF_REDACT_IMAGE_PIXELS` a new image of format PNG is created, which the page will use in place of the original one. The original image is not deleted or replaced as part of this process, so other pages may still show the original. In addition, the new, modified PNG image currently is **stored uncompressed**. Do keep these aspects in mind when choosing the right garbage collection method and compression options during save.

         * **Text removal** is done by character: A character is removed if its bbox has a **non-empty overlap** with a redaction rectangle (changed in MuPDF v1.17). Depending on the font properties and / or the chosen line height, deletion may occur for undesired text parts. Using :meth:`Tools.set_small_glyph_heights` with a ``True`` argument before text search may help to prevent this.

         * Redactions are a simple way to replace single words in a PDF, or to just physically remove them. Locate the word "secret" using some text extraction or search method and insert a redaction using "xxxxxx" as replacement text for each occurrence.

           - Be wary if the replacement is longer than the original -- this may lead to an awkward appearance, line breaks or no new text at all.

           - For a number of reasons, the new text may not exactly be positioned on the same line like the old one -- especially true if the replacement font was not one of CJK or :ref:`Base-14-Fonts`.

      |history_begin|

      * New in v1.16.11
      * Changed in v1.16.12: The previous *mark* parameter is gone. Instead, the respective rectangles are filled with the individual *fill* color of each redaction annotation. If a *text* was given in the annotation, then :meth:`insert_textbox` is invoked to insert it, using parameters provided with the redaction.
      * Changed in v1.18.0: added option for handling images that overlap redaction areas.
      * Changed in v1.23.27: added option for removing graphics as well.
      * Changed in v1.24.2: added option `keep_text` to leave text untouched.

      |history_end|

      ---------

   .. method:: add_polyline_annot(points)

   .. method:: add_polygon_annot(points)

      PDF only: Add an annotation consisting of lines which connect the given points. A **Polygon's** first and last points are automatically connected, which does not happen for a **PolyLine**. The **rectangle** is automatically created as the smallest rectangle containing the points, each one surrounded by a circle of radius 3 (= 3 * line width). The following shows a 'PolyLine' that has been modified with colors and line ends.

      :arg list points: a list of :data:`point_like` objects.

      :rtype: :ref:`Annot`
      :returns: the created annotation. It is drawn with line color black, line width 1 no fill color but fill color support. Use methods of :ref:`Annot` to make any changes to achieve something like this:

      .. image:: images/img-polyline.*
         :scale: 70

   .. method:: add_underline_annot(quads=None, start=None, stop=None, clip=None)

   .. method:: add_strikeout_annot(quads=None, start=None, stop=None, clip=None)

   .. method:: add_squiggly_annot(quads=None, start=None, stop=None, clip=None)

   .. method:: add_highlight_annot(quads=None, start=None, stop=None, clip=None)

      PDF only: These annotations are normally used for **marking text** which has previously been somehow located (for example via :meth:`Page.search_for`). But this is not required: you are free to "mark" just anything.

      Standard (stroke only -- no fill color support) colors are chosen per annotation type: **yellow** for highlighting, **red** for striking out, **green** for underlining, and **magenta** for wavy underlining.

      All these four methods convert the arguments into a list of :ref:`Quad` objects. The **annotation** rectangle is then calculated to envelop all these quadrilaterals.

      .. note::

        :meth:`search_for` delivers a list of either :ref:`Rect` or :ref:`Quad` objects. Such a list can be directly used as an argument for these annotation types and will deliver **one common annotation** for all occurrences of the search string::

           >>> # prefer quads=True in text searching for annotations!
           >>> quads = page.search_for("pymupdf", quads=True)
           >>> page.add_highlight_annot(quads)

      .. note::
        Obviously, text marker annotations need to know what is the top, the bottom, the left, and the right side of the area(s) to be marked. If the arguments are quads, this information is given by the sequence of the quad points. In contrast, a rectangle delivers much less information -- this is illustrated by the fact, that 4! = 24 different quads can be constructed with the four corners of a rectangle.

        Therefore, we **strongly recommend** to use the `quads` option for text searches, to ensure correct annotations. A similar consideration applies to marking **text spans** extracted with the "dict" / "rawdict" options of :meth:`Page.get_text`. For more details on how to compute quadrilaterals in this case, see section "How to Mark Non-horizontal Text" of :ref:`FAQ`.

      :arg rect_like,quad_like,list,tuple quads:
        the location(s) -- rectangle(s) or quad(s) -- to be marked. (Changed in v1.14.20)
        A list or tuple must consist of :data:`rect_like` or :data:`quad_like` items (or even a mixture of either).
        Every item must be finite, convex and not empty (as applicable).
        **Set this parameter to** ``None`` if you want to use the following arguments (Changed in v1.16.14).
        And vice versa: if not ``None``, the remaining parameters must be ``None``.
        
      :arg point_like start: start text marking at this point. Defaults to the top-left point of *clip*. Must be provided if `quads` is ``None``. (New in v1.16.14)
      :arg point_like stop: stop text marking at this point. Defaults to the bottom-right point of *clip*. Must be used if `quads` is ``None``. (New in v1.16.14)
      :arg rect_like clip: only consider text lines intersecting this area. Defaults to the page rectangle. Only use if `start` and `stop` are provided. (New in v1.16.14)

      :rtype: :ref:`Annot` or ``None`` (changed in v1.16.14).
      :returns: the created annotation. If *quads* is an empty list, **no annotation** is created (changed in v1.16.14).

      .. note::
        You can use parameters *start*, *stop* and *clip* to highlight consecutive lines between the points *start* and *stop* (starting with v1.16.14).
        Make use of *clip* to further reduce the selected line bboxes and thus deal with e.g. multi-column pages.
        The following multi-line highlight on a page with three text columns was created by specifying the two red points and setting clip accordingly.

      .. image:: images/img-markers.*
         :scale: 100

   .. method:: cluster_drawings(clip=None, drawings=None, x_tolerance=3, y_tolerance=3)

      Cluster vector graphics (synonyms are line-art or drawings) based on their geometrical vicinity. The method walks through the output of :meth:`Page.get_drawings` and joins paths whose `path["rect"]` are closer to each other than some tolerance values (given in the arguments). The result is a list of rectangles that each wrap things like tables (with gridlines), pie charts, bar charts, etc.

      :arg rect_like clip: only consider paths inside this area. The default is the full page.

      :arg list drawings: (optional) provide a previously generated output of :meth:`Page.get_drawings`. If `None` the method will execute the method.

      :arg float x_tolerance: 

   .. method:: find_tables(clip=None, strategy=None, vertical_strategy=None, horizontal_strategy=None, vertical_lines=None, horizontal_lines=None, snap_tolerance=None, snap_x_tolerance=None, snap_y_tolerance=None, join_tolerance=None, join_x_tolerance=None, join_y_tolerance=None, edge_min_length=3, min_words_vertical=3, min_words_horizontal=1, intersection_tolerance=None, intersection_x_tolerance=None, intersection_y_tolerance=None, text_tolerance=None, text_x_tolerance=None, text_y_tolerance=None, add_lines=None)

      Find tables on the page and return an object with related information. Typically, the default values of the many parameters will be sufficient. Adjustments should ever only be needed in corner case situations.

      :arg rect_like clip: specify a region to consider within the page rectangle and ignore the rest. Default is the full page.

      :arg str strategy: Request a **table detection** strategy. Valid values are "lines", "lines_strict" and "text".
      
         Default is **"lines"** which uses all vector graphics on the page to detect grid lines.
         
         Strategy **"lines_strict"** ignores borderless rectangle vector graphics. Sometimes single text pieces have background colors which may lead to false columns or lines. This strategy ignores them and can thus increase detection precision.
         
         If **"text"** is specified, text positions are used to generate "virtual" column and / or row boundaries. Use `min_words_*` to request the number of words for considering their coordinates.
         
         Use parameters `vertical_strategy` and `horizontal_strategy` **instead** for a more fine-grained treatment of the dimensions.

      :arg sequence[floats] horizontal_lines: y-coordinates of rows. If provided, there will be no attempt to identify additional table rows. This influences table detection.

      :arg sequence[floats] vertical_lines: x-coordinates of columns. If provided, there will be no attempt to identify additional table columns. This influences table detection.

      :arg int min_words_vertical: relevant for vertical strategy option "text": at least this many words must coincide to establish a **virtual column** boundary.

      :arg int min_words_horizontal: relevant for horizontal strategy option "text": at least this many words must coincide to establish a **virtual row** boundary.

      :arg float snap_tolerance: Any two horizontal lines whose y-values differ by no more than this value will be **snapped** into one. Accordingly for vertical lines. Default is 3. Separate values can be specified instead for the dimensions, using `snap_x_tolerance` and `snap_y_tolerance`.

      :arg float join_tolerance: Any two lines will be **joined** to one if the end and the start points differ by no more than this value (in points). Default is 3. Instead of this value, separate values can be specified for the dimensions using `join_x_tolerance` and `join_y_tolerance`.

      :arg float edge_min_length: Ignore a line if its length does not exceed this value (points). Default is 3.

      :arg float intersection_tolerance: When combining lines into cell borders, orthogonal lines must be within this value (points) to be considered intersecting. Default is 3. Instead of this value, separate values can be specified for the dimensions using `intersection_x_tolerance` and `intersection_y_tolerance`.

      :arg float text_tolerance: Characters will be combined into words only if their distance is no larger than this value (points). Default is 3. Instead of this value, separate values can be specified for the dimensions using `text_x_tolerance` and `text_y_tolerance`.

      :arg tuple,list add_lines: Specify a list of "lines" (i.e. pairs of :data:`point_like` objects) as **additional**, "virtual" vector graphics. These lines may help with table and / or cell detection and will not otherwise influence the detection strategy. Especially, in contrast to parameters `horizontal_lines` and `vertical_lines`, they will not prevent detecting rows or columns in other ways. These lines will be treated exactly like "real" vector graphics in terms of joining, snapping, intersectiing, minimum length and containment in the `clip` rectangle. Similarly, lines not parallel to any of the coordinate axes will be ignored.

      .. image:: images/img-findtables.*

      :returns: a `TableFinder` object that has the following significant attributes:

         * `cells`: a list of **all bboxes** on the page, that have been identified as table cells (across all tables). Each cell is a :data:`rect_like` tuple `(x0, y0, x1, y1)` of coordinates or `None`.
         * `tables`: a list of `Table` objects. This is `[]` if the page has no tables. Single tables can be found as items of this list. But the `TableFinder` object itself is also a sequence of its tables. This means that if `tabs` is a `TableFinder` object, then table "n" is delivered by `tabs.tables[n]` as well as by the shorter `tabs[n]`.


         * The `Table` object has the following attributes:

           * ``bbox``: the bounding box of the table as a tuple `(x0, y0, x1, y1)`.
           * ``cells``: bounding boxes of the table's cells (list of tuples). A cell may also be `None`.
           * ``extract()``: this method returns the text content of each table cell as a list of list of strings.
           * ``to_markdown()``: this method returns the table as a **string in markdown format** (compatible to Github). Supporting viewers can render the string as a table. This output is optimized for **small token** sizes, which is especially beneficial for LLM/RAG feeds. Pandas DataFrames (see method `to_pandas()` below) offer an equivalent markdown table output which however is better readable for the human eye.
           * `to_pandas()`: this method returns the table as a `pandas <https://pypi.org/project/pandas/>`_ `DataFrame <https://pandas.pydata.org/docs/reference/frame.html>`_. DataFrames are very versatile objects allowing a plethora of table manipulation methods and outputs to almost 20 well-known formats, among them Excel files, CSV, JSON, markdown-formatted tables and more. `DataFrame.to_markdown()` generates a Github-compatible markdown format optimized for human readability. This method however requires the package `tabulate <https://pypi.org/project/tabulate/>`_ to be installed in addition to pandas itself.
           * ``header``: a `TableHeader` object containing header information of the table.
           * ``col_count``: an integer containing the number of table columns.
           * ``row_count``: an integer containing the number of table rows.
           * ``rows``: a list of `TableRow` objects containing two attributes, ``bbox`` is the boundary box of the row, and `cells` is a list of table cells contained in this row.

         * The `TableHeader` object has the following attributes:

           * ``bbox``: the bounding box of the header.
           * `cells`: a list of bounding boxes containing the name of the respective column.
           * `names`: a list of strings containing the text of each of the cell bboxes. They represent the column names -- which are used when exporting the table to pandas DataFrames, markdown, etc.
           * `external`: a bool indicating whether the header bbox is outside the table body (`True`) or not. Table headers are never identified by the `TableFinder` logic. Therefore, if `external` is true, then the header cells are not part of any cell identified by `TableFinder`. If `external == False`, then the first table row is the header.

         Please have a look at these `Jupyter notebooks <https://github.com/pymupdf/PyMuPDF-Utilities/tree/master/table-analysis>`_, which cover standard situations like multiple tables on one page or joining table fragments across multiple pages.

         .. caution:: The lifetime of the `TableFinder` object, as well as that of all its tables **equals the lifetime of the page**. If the page object is deleted or reassigned, all tables are no longer valid.
         
            The only way to keep table content beyond the page's availability is to **extract it** via methods `Table.to_markdown()`, `Table.to_pandas()` or a copy of `Table.extract()` (e.g. `Table.extract()[:]`).

         .. note::

            Once a table has been extracted to a **Pandas DataFrame** with `to_pandas()` it is easy to convert to other file types with the **Pandas API**:

            - table to Markdown, use `to_markdown <https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_markdown.html#pandas.DataFrame.to_markdown>`_
            - table to JSON, use: `to_json <https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_json.html>`_
            - table to Excel, use: `to_excel <https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_excel.html>`_
            - table to CSV, use: `to_csv <https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_csv.html>`_
            - table to HTML, use: `to_html <https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_html.html>`_
            - table to SQL, use: `to_sql <https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_sql.html>`_


      |history_begin|

      * New in version 1.23.0
      * Changed in version 1.23.19: new argument `add_lines`.

      |history_end|

      .. important::

         There is also the `pdf2docx extract tables method`_ which is capable of table extraction if you prefer.


   .. method:: add_stamp_annot(rect, stamp=0)

      PDF only: Add a "rubber stamp" like annotation to e.g. indicate the document's intended use ("DRAFT", "CONFIDENTIAL", etc.).

      :arg rect_like rect: rectangle where to place the annotation.

      :arg int stamp: id number of the stamp text. For available stamps see :ref:`StampIcons`.

      .. note::

         * The stamp's text and its border line will automatically be sized and be put horizontally and vertically centered in the given rectangle. :attr:`Annot.rect` is automatically calculated to fit the given **width** and will usually be smaller than this parameter.
         * The font chosen is "Times Bold" and the text will be upper case.
         * The appearance can be changed using :meth:`Annot.set_opacity` and by setting the "stroke" color (no "fill" color supported).
         * This can be used to create watermark images: on a temporary PDF page create a stamp annotation with a low opacity value, make a pixmap from it with *alpha=True* (and potentially also rotate it), discard the temporary PDF page and use the pixmap with :meth:`insert_image` for your target PDF.


      .. image:: images/img-stampannot.*
         :scale: 80

   .. method:: add_widget(widget)

      PDF only: Add a PDF Form field ("widget") to a page. This also **turns the PDF into a Form PDF**. Because of the large amount of different options available for widgets, we have developed a new class :ref:`Widget`, which contains the possible PDF field attributes. It must be used for both, form field creation and updates.

      :arg widget: a :ref:`Widget` object which must have been created upfront.
      :type widget: :ref:`Widget`

      :returns: a widget annotation.

   .. method:: delete_annot(annot)

      * The removal will now include any bound 'Popup' or response annotations and related objects (changed in v1.16.6).

      PDF only: Delete annotation from the page and return the next one.

      :arg annot: the annotation to be deleted.
      :type annot: :ref:`Annot`

      :rtype: :ref:`Annot`
      :returns: the annotation following the deleted one. Please remember that physical removal requires saving to a new file with garbage > 0.

   .. method:: delete_widget(widget)

      PDF only: Delete field from the page and return the next one.

      :arg widget: the widget to be deleted.
      :type widget: :ref:`Widget`

      :rtype: :ref:`Widget`
      :returns: the widget following the deleted one. Please remember that physical removal requires saving to a new file with garbage > 0.

      |history_begin|

      (New in v1.18.4)

      |history_end|


   .. method:: delete_link(linkdict)

      PDF only: Delete the specified link from the page. The parameter must be an **original item** of :meth:`get_links()`, see :ref:`link_dict_description`. The reason for this is the dictionary's *"xref"* key, which identifies the PDF object to be deleted.

      :arg dict linkdict: the link to be deleted.

   .. method:: insert_link(linkdict)

      PDF only: Insert a new link on this page. The parameter must be a dictionary of format as provided by :meth:`get_links()`, see :ref:`link_dict_description`.

      :arg dict linkdict: the link to be inserted.

   .. method:: update_link(linkdict)

      PDF only: Modify the specified link. The parameter must be a (modified) **original item** of :meth:`get_links()`, see :ref:`link_dict_description`. The reason for this is the dictionary's *"xref"* key, which identifies the PDF object to be changed.

      :arg dict linkdict: the link to be modified.

      .. warning:: If updating / inserting a URI link (`"kind": LINK_URI`), please make sure to start the value for the `"uri"` key with a disambiguating string like `"http://"`, `"https://"`, `"file://"`, `"ftp://"`, `"mailto:"`, etc. Otherwise -- depending on your browser or other "consumer" software -- unexpected default assumptions may lead to unwanted behaviours.


   .. method:: get_label()

      PDF only: Return the label for the page.

      :rtype: str

      :returns: the label string like "vii" for Roman numbering or "" if not defined.

      |history_begin|

      * New in v1.18.6

      |history_end|

   .. method:: get_links()

      Retrieves **all** links of a page.

      :rtype: list
      :returns: A list of dictionaries. For a description of the dictionary entries, see :ref:`link_dict_description`. Always use this or the :meth:`Page.links` method if you intend to make changes to the links of a page.

   .. method:: links(kinds=None)

      Return a generator over the page's links. The results equal the entries of :meth:`Page.get_links`.

      :arg sequence kinds: a sequence of integers to down-select to one or more link kinds. Default is all links. Example: *kinds=(pymupdf.LINK_GOTO,)* will only return internal links.

      :rtype: generator
      :returns: an entry of :meth:`Page.get_links()` for each iteration.

      |history_begin|

      * New in v1.16.4

      |history_end|

   .. method:: annots(types=None)

      Return a generator over the page's annotations.

      :arg sequence types: a sequence of integers to down-select to one or more annotation types. Default is all annotations. Example: `types=(pymupdf.PDF_ANNOT_FREETEXT, pymupdf.PDF_ANNOT_TEXT)` will only return 'FreeText' and 'Text' annotations.

      :rtype: generator
      :returns: an :ref:`Annot` for each iteration.

         .. caution::
              You **cannot safely update annotations** from within this generator. This is because most annotation updates require reloading the page via `page = doc.reload_page(page)`. To circumvent this restriction, make a list of annotations xref numbers first and then iterate over these numbers::

               In [4]: xrefs = [annot.xref for annot in page.annots(types=[...])]
               In [5]: for xref in xrefs:
                  ...:     annot = page.load_annot(xref)
                  ...:     annot.update()
                  ...:     page = doc.reload_page(page)
               In [6]:

      |history_begin|

      * New in v1.16.4

      |history_end|

   .. method:: widgets(types=None)

      Return a generator over the page's form fields.

      :arg sequence types: a sequence of integers to down-select to one or more widget types. Default is all form fields. Example: `types=(pymupdf.PDF_WIDGET_TYPE_TEXT,)` will only return 'Text' fields.

      :rtype: generator
      :returns: a :ref:`Widget` for each iteration.

      |history_begin|

      * New in v1.16.4

      |history_end|


   .. method:: write_text(rect=None, writers=None, overlay=True, color=None, opacity=None, keep_proportion=True, rotate=0, oc=0)

      PDF only: Write the text of one or more :ref:`Textwriter` objects to the page.

      :arg rect_like rect: where to place the text. If omitted, the rectangle union of the text writers is used.
      :arg sequence writers: a non-empty tuple / list of :ref:`TextWriter` objects or a single :ref:`TextWriter`.
      :arg float opacity: set transparency, overwrites resp. value in the text writers.
      :arg sequ color: set the text color, overwrites  resp. value in the text writers.
      :arg bool overlay: put the text in foreground or background.
      :arg bool keep_proportion: maintain the aspect ratio.
      :arg float rotate: rotate the text by an arbitrary angle.
      :arg int oc: the :data:`xref` of an :data:`OCG` or :data:`OCMD`. (New in v1.18.4)

      .. note:: Parameters *overlay, keep_proportion, rotate* and *oc* have the same meaning as in :meth:`Page.show_pdf_page`.

      |history_begin|

      * New in v1.16.18

      |history_end|


   .. index::
      pair: border_width; insert_text
      pair: color; insert_text
      pair: encoding; insert_text
      pair: fill; insert_text
      pair: fontfile; insert_text
      pair: fontname; insert_text
      pair: fontsize; insert_text
      pair: morph; insert_text
      pair: overlay; insert_text
      pair: render_mode; insert_text
      pair: miter_limit; insert_text
      pair: rotate; insert_text
      pair: stroke_opacity; insert_text
      pair: fill_opacity; insert_text
      pair: oc; insert_text

   .. method:: insert_text(point, text, *, fontsize=11, fontname="helv", fontfile=None, idx=0, color=None, fill=None, render_mode=0, miter_limit=1, border_width=0.05, encoding=TEXT_ENCODING_LATIN, rotate=0, morph=None, stroke_opacity=1, fill_opacity=1, overlay=True, oc=0)

      PDF only: Insert text lines starting at :data:`point_like` ``point``. See :meth:`Shape.insert_text`.

      |history_begin|

      * Changed in v1.18.4

      |history_end|

   .. index::
      pair: align; insert_textbox
      pair: border_width; insert_textbox
      pair: color; insert_textbox
      pair: encoding; insert_textbox
      pair: expandtabs; insert_textbox
      pair: fill; insert_textbox
      pair: fontfile; insert_textbox
      pair: fontname; insert_textbox
      pair: fontsize; insert_textbox
      pair: morph; insert_textbox
      pair: overlay; insert_textbox
      pair: render_mode; insert_textbox
      pair: miter_limit; insert_textbox
      pair: rotate; insert_textbox
      pair: stroke_opacity; insert_textbox
      pair: fill_opacity; insert_textbox
      pair: oc; insert_textbox

   .. method:: insert_textbox(rect, buffer, *, fontsize=11, fontname="helv", fontfile=None, idx=0, color=None, fill=None, render_mode=0, miter_limit=1, border_width=1, encoding=TEXT_ENCODING_LATIN, expandtabs=8, align=TEXT_ALIGN_LEFT, charwidths=None, rotate=0, morph=None, stroke_opacity=1, fill_opacity=1, oc=0, overlay=True)

      PDF only: Insert text into the specified :data:`rect_like` *rect*. See :meth:`Shape.insert_textbox`.

      |history_begin|

      * Changed in v1.18.4

      |history_end|

   .. index::
      pair: rect; insert_htmlbox
      pair: text; insert_htmlbox
      pair: css; insert_htmlbox
      pair: adjust; insert_htmlbox
      pair: archive; insert_htmlbox
      pair: overlay; insert_htmlbox
      pair: rotate; insert_htmlbox
      pair: oc; insert_htmlbox
      pair: opacity; insert_htmlbox
      pair: morph; insert_htmlbox

   .. method:: insert_htmlbox(rect, text, *, css=None, scale_low=0, archive=None, rotate=0, oc=0, opacity=1, overlay=True)

      **PDF only:** Insert text into the specified rectangle. The method has similarities with methods :meth:`Page.insert_textbox` and :meth:`TextWriter.fill_textbox`, but is **much more powerful**. This is achieved by letting a :ref:`Story` object do all the required processing.

      * Parameter ``text`` may be a string as in the other methods. But it will be **interpreted as HTML source** and may therefore also contain HTML language elements -- including styling. The `css` parameter may be used to pass in additional styling instructions.

      * Automatic line breaks are generated at word boundaries. The "soft hyphen" character `"&#173;"` (or `&shy;`) can be used to cause hyphenation and thus may also cause line breaks. **Forced** line breaks however are only achievable via the HTML tag ``<br>`` - ``\n`` is ignored and will be treated like a space.

      * With this method the following can be achieved:

        - Styling effects like bold, italic, text color, text alignment, font size or font switching.
        - The text may include arbitrary languages -- **including right-to-left** languages.
        - Scripts like `Devanagari <https://en.wikipedia.org/wiki/Devanagari>`_ and several others in Asia have a highly complex system of ligatures, where two or more unicodes together yield one glyph. The Story uses the software package `HarfBuzz <https://harfbuzz.github.io/>`_ , to deal with these things and produce correct output.
        - One can also **include images** via HTML tag `<img>` -- the Story will take care of the appropriate layout. This is an alternative option to insert images, compared to :meth:`Page.insert_image`.
        - HTML tables (tag `<table>`) may be included in the text and will be handled appropriately.
        - Links are automatically generated when present.

      * If content does not fit in the rectangle, the developer has two choices:
         
        - **either** only be informed about this (and accept a no-op, just like with the other textbox insertion methods), 
        - **or** (`scale_low=0` - the default) scale down the content until it fits.

      :arg rect_like rect: rectangle on page to receive the text.
      :arg str,Story text: the text to be written. Can contain a mixture of plain text and HTML tags with styling instructions. Alternatively, a :ref:`Story` object may be specified (in which case the internal Story generation step will be omitted). A Story must have been generated with all required styling and Archive information.
      :arg str css: optional string containing additional CSS instructions. This parameter is ignored if ``text`` is a Story.
      :arg float scale_low: if necessary, scale down the content until it fits in the target rectangle. This sets the down scaling limit. Default is 0, no limit. A value of 1 means no down-scaling permitted. A value of e.g. 0.2 means maximum down-scaling by 80%.
      :arg Archive archive: an Archive object that points to locations where to find images or non-standard fonts. If ``text`` refers to images or non-standard fonts, this parameter is required. This parameter is ignored if ``text`` is a Story.
      :arg int rotate: one of the values 0, 90, 180, 270. Depending on this, text will be filled:
      
          - 0: top-left to bottom-right.
          - 90: bottom-left to top-right.
          - 180: bottom-right to top-left.
          - 270: top-right to bottom-left.

          .. image:: images/img-rotate.*

      :arg int oc:  the xref of an :data:`OCG` / :data:`OCMD` or 0. Please refer to :meth:`Page.show_pdf_page` for details.
      :arg float opacity: set the fill and stroke opacity of the content. Only values `0 <= opacity < 1` are considered.
      :arg bool overlay: put the text in front of other content. Please refer to :meth:`Page.show_pdf_page` for details.

      :returns: A tuple of floats `(spare_height, scale)`.

         - `spare_height`: -1 if content did not fit, else >= 0. It is the height of the unused (still available) rectangle stripe. Positive only if scale = 1 (no down-scaling happened).
         - `scale`: down-scaling factor, 0 < scale <= 1.

         Please refer to examples in this section of the recipes: :ref:`RecipesText_I_c`.

      |history_begin|

      * New in v1.23.8; rebased-only.
      * New in v1.23.9: `opacity` parameter.

      |history_end|
      

   **Drawing Methods**

   .. index::
      pair: closePath; draw_line
      pair: color; draw_line
      pair: dashes; draw_line
      pair: fill; draw_line
      pair: lineCap; draw_line
      pair: lineJoin; draw_line
      pair: lineJoin; draw_line
      pair: morph; draw_line
      pair: overlay; draw_line
      pair: width; draw_line
      pair: stroke_opacity; draw_line
      pair: fill_opacity; draw_line
      pair: oc; draw_line

   .. method:: draw_line(p1, p2, color=(0,), width=1, dashes=None, lineCap=0, lineJoin=0, overlay=True, morph=None, stroke_opacity=1, fill_opacity=1, oc=0)

      PDF only: Draw a line from *p1* to *p2* (:data:`point_like` \s). See :meth:`Shape.draw_line`.

      |history_begin|

      * Changed in v1.18.4

      |history_end|

   .. index::
      pair: breadth; draw_zigzag
      pair: closePath; draw_zigzag
      pair: color; draw_zigzag
      pair: dashes; draw_zigzag
      pair: fill; draw_zigzag
      pair: lineCap; draw_zigzag
      pair: lineJoin; draw_zigzag
      pair: morph; draw_zigzag
      pair: overlay; draw_zigzag
      pair: width; draw_zigzag
      pair: stroke_opacity; draw_zigzag
      pair: fill_opacity; draw_zigzag
      pair: oc; draw_zigzag

   .. method:: draw_zigzag(p1, p2, breadth=2, color=(0,), width=1, dashes=None, lineCap=0, lineJoin=0, overlay=True, morph=None, stroke_opacity=1, fill_opacity=1, oc=0)

      PDF only: Draw a zigzag line from *p1* to *p2* (:data:`point_like` \s). See :meth:`Shape.draw_zigzag`.

      |history_begin|

      * Changed in v1.18.4

      |history_end|

   .. index::
      pair: breadth; draw_squiggle
      pair: closePath; draw_squiggle
      pair: color; draw_squiggle
      pair: dashes; draw_squiggle
      pair: fill; draw_squiggle
      pair: lineCap; draw_squiggle
      pair: lineJoin; draw_squiggle
      pair: morph; draw_squiggle
      pair: overlay; draw_squiggle
      pair: width; draw_squiggle
      pair: stroke_opacity; draw_squiggle
      pair: fill_opacity; draw_squiggle
      pair: oc; draw_squiggle

   .. method:: draw_squiggle(p1, p2, breadth=2, color=(0,), width=1, dashes=None, lineCap=0, lineJoin=0, overlay=True, morph=None, stroke_opacity=1, fill_opacity=1, oc=0)

      PDF only: Draw a squiggly (wavy, undulated) line from *p1* to *p2* (:data:`point_like` \s). See :meth:`Shape.draw_squiggle`.

      |history_begin|

      * Changed in v1.18.4

      |history_end|

   .. index::
      pair: closePath; draw_circle
      pair: color; draw_circle
      pair: dashes; draw_circle
      pair: fill; draw_circle
      pair: lineCap; draw_circle
      pair: lineJoin; draw_circle
      pair: morph; draw_circle
      pair: overlay; draw_circle
      pair: width; draw_circle
      pair: stroke_opacity; draw_circle
      pair: fill_opacity; draw_circle
      pair: oc; draw_circle

   .. method:: draw_circle(center, radius, color=(0,), fill=None, width=1, dashes=None, lineCap=0, lineJoin=0, overlay=True, morph=None, stroke_opacity=1, fill_opacity=1, oc=0)

      PDF only: Draw a circle around *center* (:data:`point_like`) with a radius of *radius*. See :meth:`Shape.draw_circle`.

      |history_begin|

      * Changed in v1.18.4

      |history_end|

   .. index::
      pair: closePath; draw_oval
      pair: color; draw_oval
      pair: dashes; draw_oval
      pair: fill; draw_oval
      pair: lineCap; draw_oval
      pair: lineJoin; draw_oval
      pair: morph; draw_oval
      pair: overlay; draw_oval
      pair: width; draw_oval
      pair: stroke_opacity; draw_oval
      pair: fill_opacity; draw_oval
      pair: oc; draw_oval

   .. method:: draw_oval(quad, color=(0,), fill=None, width=1, dashes=None, lineCap=0, lineJoin=0, overlay=True, morph=None, stroke_opacity=1, fill_opacity=1, oc=0)

      PDF only: Draw an oval (ellipse) within the given :data:`rect_like` or :data:`quad_like`. See :meth:`Shape.draw_oval`.

      |history_begin|

      * Changed in v1.18.4

      |history_end|

   .. index::
      pair: closePath; draw_sector
      pair: color; draw_sector
      pair: dashes; draw_sector
      pair: fill; draw_sector
      pair: fullSector; draw_sector
      pair: lineCap; draw_sector
      pair: lineJoin; draw_sector
      pair: morph; draw_sector
      pair: overlay; draw_sector
      pair: width; draw_sector
      pair: stroke_opacity; draw_sector
      pair: fill_opacity; draw_sector
      pair: oc; draw_sector

   .. method:: draw_sector(center, point, angle, color=(0,), fill=None, width=1, dashes=None, lineCap=0, lineJoin=0, fullSector=True, overlay=True, closePath=False, morph=None, stroke_opacity=1, fill_opacity=1, oc=0)

      PDF only: Draw a circular sector, optionally connecting the arc to the circle's center (like a piece of pie). See :meth:`Shape.draw_sector`.

      |history_begin|

      * Changed in v1.18.4

      |history_end|

   .. index::
      pair: closePath; draw_polyline
      pair: color; draw_polyline
      pair: dashes; draw_polyline
      pair: fill; draw_polyline
      pair: lineCap; draw_polyline
      pair: lineJoin; draw_polyline
      pair: morph; draw_polyline
      pair: overlay; draw_polyline
      pair: width; draw_polyline
      pair: stroke_opacity; draw_polyline
      pair: fill_opacity; draw_polyline
      pair: oc; draw_polyline

   .. method:: draw_polyline(points, color=(0,), fill=None, width=1, dashes=None, lineCap=0, lineJoin=0, overlay=True, closePath=False, morph=None, stroke_opacity=1, fill_opacity=1, oc=0)

      PDF only: Draw several connected lines defined by a sequence of :data:`point_like` \s. See :meth:`Shape.draw_polyline`.

      |history_begin|

      * Changed in v1.18.4

      |history_end|


   .. index::
      pair: closePath; draw_bezier
      pair: color; draw_bezier
      pair: dashes; draw_bezier
      pair: fill; draw_bezier
      pair: lineCap; draw_bezier
      pair: lineJoin; draw_bezier
      pair: morph; draw_bezier
      pair: overlay; draw_bezier
      pair: width; draw_bezier
      pair: stroke_opacity; draw_bezier
      pair: fill_opacity; draw_bezier
      pair: oc; draw_bezier

   .. method:: draw_bezier(p1, p2, p3, p4, color=(0,), fill=None, width=1, dashes=None, lineCap=0, lineJoin=0, overlay=True, closePath=False, morph=None, stroke_opacity=1, fill_opacity=1, oc=0)

      PDF only: Draw a cubic Bézier curve from *p1* to *p4* with the control points *p2* and *p3* (all are :data:`point_like` \s). See :meth:`Shape.draw_bezier`.

      |history_begin|

      * Changed in v1.18.4

      |history_end|

   .. index::
      pair: closePath; draw_curve
      pair: color; draw_curve
      pair: dashes; draw_curve
      pair: fill; draw_curve
      pair: lineCap; draw_curve
      pair: lineJoin; draw_curve
      pair: morph; draw_curve
      pair: overlay; draw_curve
      pair: width; draw_curve
      pair: stroke_opacity; draw_curve
      pair: fill_opacity; draw_curve
      pair: oc; draw_curve

   .. method:: draw_curve(p1, p2, p3, color=(0,), fill=None, width=1, dashes=None, lineCap=0, lineJoin=0, overlay=True, closePath=False, morph=None, stroke_opacity=1, fill_opacity=1, oc=0)

      PDF only: This is a special case of *draw_bezier()*. See :meth:`Shape.draw_curve`.

      |history_begin|

      * Changed in v1.18.4

      |history_end|

   .. index::
      pair: closePath; draw_rect
      pair: color; draw_rect
      pair: dashes; draw_rect
      pair: fill; draw_rect
      pair: lineCap; draw_rect
      pair: lineJoin; draw_rect
      pair: morph; draw_rect
      pair: overlay; draw_rect
      pair: width; draw_rect
      pair: stroke_opacity; draw_rect
      pair: fill_opacity; draw_rect
      pair: radius; draw_rect
      pair: oc; draw_rect

   .. method:: draw_rect(rect, color=(0,), fill=None, width=1, dashes=None, lineCap=0, lineJoin=0, overlay=True, morph=None, stroke_opacity=1, fill_opacity=1, radius=None, oc=0)

      PDF only: Draw a rectangle. See :meth:`Shape.draw_rect`.

      |history_begin|

      * Changed in v1.18.4
      * Changed in v1.22.0: Added parameter *radius*.

      |history_end|

   .. index::
      pair: closePath; draw_quad
      pair: color; draw_quad
      pair: dashes; draw_quad
      pair: fill; draw_quad
      pair: lineCap; draw_quad
      pair: lineJoin; draw_quad
      pair: morph; draw_quad
      pair: overlay; draw_quad
      pair: width; draw_quad
      pair: stroke_opacity; draw_quad
      pair: fill_opacity; draw_quad
      pair: oc; draw_quad

   .. method:: draw_quad(quad, color=(0,), fill=None, width=1, dashes=None, lineCap=0, lineJoin=0, overlay=True, morph=None, stroke_opacity=1, fill_opacity=1, oc=0)

      PDF only: Draw a quadrilateral. See :meth:`Shape.draw_quad`.

      |history_begin|

      * Changed in v1.18.4

      |history_end|


   .. index::
      pair: encoding; insert_font
      pair: fontbuffer; insert_font
      pair: fontfile; insert_font
      pair: fontname; insert_font
      pair: set_simple; insert_font

   .. method:: insert_font(fontname="helv", fontfile=None, fontbuffer=None, set_simple=False, encoding=TEXT_ENCODING_LATIN)

      PDF only: Add a new font to be used by text output methods and return its :data:`xref`. If not already present in the file, the font definition will be added. Supported are the built-in :data:`Base14_Fonts` and the CJK fonts via **"reserved"** fontnames. Fonts can also be provided as a file path or a memory area containing the image of a font file.

      :arg str fontname: The name by which this font shall be referenced when outputting text on this page. In general, you have a "free" choice here (but consult the :ref:`AdobeManual`, page 16, section 7.3.5 for a formal description of building legal PDF names). However, if it matches one of the :data:`Base14_Fonts` or one of the CJK fonts, *fontfile* and *fontbuffer* **are ignored**.

        In other words, you cannot insert a font via *fontfile* / *fontbuffer* and also give it a reserved *fontname*.

        .. note:: A reserved fontname can be specified in any mixture of upper or lower case and still match the right built-in font definition: fontnames "helv", "Helv", "HELV", "Helvetica", etc. all lead to the same font definition "Helvetica". But from a :ref:`Page` perspective, these are **different references**. You can exploit this fact when using different *encoding* variants (Latin, Greek, Cyrillic) of the same font on a page.

      :arg str fontfile: a path to a font file. If used, *fontname* must be **different from all reserved names**.

      :arg bytes/bytearray fontbuffer: the memory image of a font file. If used, *fontname* must be **different from all reserved names**. This parameter would typically be used with :attr:`Font.buffer` for fonts supported / available via :ref:`Font`.

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
      pair: filename; insert_image
      pair: keep_proportion; insert_image
      pair: overlay; insert_image
      pair: pixmap; insert_image
      pair: rotate; insert_image
      pair: stream; insert_image
      pair: mask; insert_image
      pair: oc; insert_image
      pair: xref; insert_image

   .. method:: insert_image(rect, *, alpha=-1, filename=None, height=0, keep_proportion=True, mask=None, oc=0, overlay=True, pixmap=None, rotate=0, stream=None, width=0, xref=0)

      PDF only: Put an image inside the given rectangle. The image may already
      exist in the PDF or be taken from a pixmap, a file, or a memory area.

      :arg rect_like rect: where to put the image. Must be finite and not empty.
      :arg int alpha: deprecated and ignored.
      :arg str filename:
        name of an image file (all formats supported by MuPDF -- see
        :ref:`ImageFiles`).
      :arg int height:
      :arg bool keep_proportion:
        maintain the aspect ratio of the image.
      :arg bytes,bytearray,io.BytesIO mask:
        image in memory -- to be used as image mask (alpha values) for the base
        image. When specified, the base image must be provided as a filename or
        a stream -- and must not be an image that already has a mask.
      :arg int oc:
        (:data:`xref`) make image visibility dependent on this :data:`OCG`
        or :data:`OCMD`. Ignored after the first of multiple insertions. The
        property is stored with the generated PDF image object and therefore
        controls the image's visibility throughout the PDF.
      :arg overlay: see :ref:`CommonParms`.
      :arg pixmap: a pixmap containing the image.
      :arg int rotate: rotate the image.
        Must be an integer multiple of 90 degrees.
        Positive values rotate anti-clockwise.
        If you need a rotation by an arbitrary angle,
        consider converting the image to a PDF
        (:meth:`Document.convert_to_pdf`)
        first and then use :meth:`Page.show_pdf_page` instead.
      :arg bytes,bytearray,io.BytesIO stream:
        image in memory (all formats supported by MuPDF -- see :ref:`ImageFiles`).
      :arg int width:
      :arg int xref:
        the :data:`xref` of an image already present in the PDF. If given,
        parameters `filename`, `pixmap`, `stream`, `alpha` and `mask` are
        ignored. The page will simply receive a reference to the existing
        image.

      :type pixmap: :ref:`Pixmap`
      
      :returns:
        The `xref` of the embedded image. This can be used as the `xref`
        argument for very significant performance boosts, if the image is
        inserted again.

      This example puts the same image on every page of a document::

         >>> doc = pymupdf.open(...)
         >>> rect = pymupdf.Rect(0, 0, 50, 50)       # put thumbnail in upper left corner
         >>> img = open("some.jpg", "rb").read()  # an image file
         >>> img_xref = 0                         # first execution embeds the image
         >>> for page in doc:
               img_xref = page.insert_image(rect, stream=img,
                          xref=img_xref,  2nd time reuses existing image
                   )
         >>> doc.save(...)

      .. note::

         1.
           The method detects multiple insertions of the same image (like
           in the above example) and will store its data only on the first
           execution.  This is even true (although less performant), if using
           the default `xref=0`.
         2.
           The method cannot detect if the same image had already been part of
           the file before opening it.

         3.
           You can use this method to provide a background or foreground image
           for the page, like a copyright or a watermark. Please remember, that
           watermarks require a transparent image if put in foreground ...

         4.
           The image may be inserted uncompressed, e.g. if a `Pixmap` is used
           or if the image has an alpha channel. Therefore, consider using
           `deflate=True` when saving the file. In addition, there are ways to
           control the image size -- even if transparency comes into play. Have
           a look at :ref:`RecipesImages_O`.

         5.
           The image is stored in the PDF at its original quality level. This
           may be much better than what you need for your display. Consider
           **decreasing the image size** before insertion -- e.g. by using
           the pixmap option and then shrinking it or scaling it down (see
           :ref:`Pixmap` chapter). The PIL method `Image.thumbnail()` can
           also be used for that purpose. The file size savings can be very
           significant.

         6.
           Another efficient way to display the same image on multiple
           pages is another method: :meth:`show_pdf_page`. Consult
           :meth:`Document.convert_to_pdf` for how to obtain intermediary PDFs
           usable for that method.

      |history_begin|

      * Changed in v1.14.1: By default, the image keeps its aspect ratio.
      * Changed in v1.14.11: Added args `keep_proportion`, `rotate`.
      * Changed in v1.14.13:

        *
          The image is now always placed **centered** in the rectangle, i.e.
          the centers of image and rectangle are equal.
        * Added support for `stream` as `io.BytesIO`.
      
      * Changed in v1.17.6:
        Insertion rectangle no longer needs to have a non-empty intersection
        with the page's :attr:`Page.cropbox` [#f5]_.
      * Changed in v1.18.1: Added `mask` arg.
      * Changed in v1.18.3: Added `oc` arg.
      * Changed in v1.18.13:
        
        * Allow providing the image as the xref of an existing one.
        * Added `xref` arg.
        * Return `xref` of stored image.
      
      * Changed in v1.19.3: deprecate and ignore `alpha` arg.

      |history_end|

   
   .. index::
      pair: filename; replace_image
      pair: pixmap; replace_image
      pair: stream; replace_image
      pair: xref; replace_image

   .. method:: replace_image(xref, filename=None, pixmap=None, stream=None)

      Replace the image at xref with another one.

      :arg int xref: the :data:`xref` of the image.
      :arg filename: the filename of the new image.
      :arg pixmap: the :ref:`Pixmap` of the new image.
      :arg stream: the memory area containing the new image.

      Arguments `filename`, `pixmap`, `stream` have the same meaning as in :meth:`Page.insert_image`, especially exactly one of these must be provided.

      This is a **global replacement:** the new image will also be shown wherever the old one has been displayed throughout the file.

      This method mainly exists for technical purposes. Typical uses include replacing large images by smaller versions, like a lower resolution, graylevel instead of colored, etc., or changing transparency.

      |history_begin|

      * New in v1.21.0

      |history_end|
   
   
   .. index::
      pair: xref; delete_image

   .. method:: delete_image(xref)

      Delete the image at xref. This is slightly misleading: actually the image is being replaced with a small transparent :ref:`Pixmap` using above :meth:`Page.replace_image`. The visible effect however is equivalent.

      :arg int xref: the :data:`xref` of the image.

      This is a **global replacement:** the image will disappear wherever the old one has been displayed throughout the file.
   
      If you inspect / extract a page's images by methods like :meth:`Page.get_images`,
      :meth:`Page.get_image_info` or :meth:`Page.get_text`,
      the replacing "dummy" image will be detected like so
      `(45, 47, 1, 1, 8, 'DeviceGray', '', 'Im1', 'FlateDecode')`
      and also seem to "cover" the same boundary box on the page.

      |history_begin|

      * New in v1.21.0

      |history_end|

   
   .. index::
      pair: blocks; Page.get_text
      pair: dict; Page.get_text
      pair: clip; Page.get_text
      pair: flags; Page.get_text
      pair: html; Page.get_text
      pair: json; Page.get_text
      pair: rawdict; Page.get_text
      pair: text; Page.get_text
      pair: words; Page.get_text
      pair: xhtml; Page.get_text
      pair: xml; Page.get_text
      pair: textpage; Page.get_text
      pair: sort; Page.get_text
      pair: delimiters; Page.get_text

   .. method:: get_text(option,*, clip=None, flags=None, textpage=None, sort=False, delimiters=None)

      Retrieves the content of a page in a variety of formats. Depending on the ``flags`` value, this may include text, images and several other object types. The method is a wrapper for multiple :ref:`TextPage` methods by choosing the output option `opt` as follows:

      * "text" -- :meth:`TextPage.extractTEXT`, default. Always includes **text only.**
      * "blocks" -- :meth:`TextPage.extractBLOCKS`. Includes text and **may** include image meta information.
      * "words" -- :meth:`TextPage.extractWORDS`. Always includes **text only.**
      * "html" -- :meth:`TextPage.extractHTML`. May include text and images.
      * "xhtml" -- :meth:`TextPage.extractXHTML`. May include text and images.
      * "xml" -- :meth:`TextPage.extractXML`. Always includes **text only.**
      * "dict" -- :meth:`TextPage.extractDICT`. May include text and images.
      * "json" -- :meth:`TextPage.extractJSON`. May include text and images.
      * "rawdict" -- :meth:`TextPage.extractRAWDICT`. May include text and images.
      * "rawjson" -- :meth:`TextPage.extractRAWJSON`. May include text and images.

      :arg str opt: A string indicating the requested format, one of the above. A mixture of upper and lower case is supported. If misspelled, option "text" is silently assumed.

      :arg rect-like clip: restrict the extraction to this rectangle. If ``None`` (default), the visible part of the page is taken. Any content (text, images) that is **not fully contained** in ``clip`` will be completely omitted. To avoid clipping altogether use ``clip=pymupdf.INFINITE_RECT()``. Only then the extraction will contain all items. This parameter has **no effect** on options "html", "xhtml" and "xml".

      :arg int flags: indicator bits to control whether to include images or how text should be handled with respect to white spaces and :data:`ligatures`. See :ref:`TextPreserve` for available indicators and :ref:`text_extraction_flags` for default settings. (New in v1.16.2)

      :arg textpage: use a previously created :ref:`TextPage`. This reduces execution time **very significantly:** by more than 50% and up to 95%, depending on the extraction option. If specified, the 'flags' and 'clip' arguments are ignored, because they are textpage-only properties. If omitted, a new, temporary textpage will be created.

      :arg bool sort: sort the output by vertical, then horizontal coordinates. In many cases, this should suffice to generate a "natural" reading order. Has no effect on (X)HTML and XML. For options "blocks", "dict", "json", "rawdict", "rawjson", sorting happens by coordinates `(y1, x0)` of the respective block bbox. For options "words" and "text", the text lines are completely re-synthesized to follow the reading sequence and appearance in the document -- which even establishes the original layout to some extent.

      :arg str delimiters: use these characters as *additional* word separators with the "words" output option (ignored otherwise). By default, all white spaces (including non-breaking space `0xA0`) indicate start and end of a word. Now you can specify more characters causing this. For instance, the default will return `"john.doe@outlook.com"` as **one** word. If you specify `delimiters="@."` then the **four** words `"john"`, `"doe"`, `"outlook"`, `"com"` will be returned. Other possible uses include ignoring punctuation characters `delimiters=string.punctuation`. The "word" strings will not contain any delimiting character. (New in v1.23.5)

      :rtype: *str, list, dict*
      :returns: The page's content as a string, a list or a dictionary. Refer to the corresponding :ref:`TextPage` method for details.

      .. note::

        1. You can use this method as a **document conversion tool** from :ref:`any supported document type<Supported_File_Types>` to one of TEXT, HTML, XHTML or XML documents.
        2. The inclusion of text via the *clip* parameter is decided on a by-character level: a character becomes part of the output, if its bbox is contained in `clip`. This **deviates** from the algorithm used in redaction annotations: a character will be **removed if its bbox intersects** any redaction annotation.

      |history_begin|

      * Changed in v1.19.0: added `textpage` parameter
      * Changed in v1.19.1: added `sort` parameter
      * Changed in v1.19.6: added new constants for defining default flags per method.
      * Changed in v1.23.5: added `delimiters` parameter
      * Changed in v1.24.11: changed the effect of `sort_True` for "text" and "words" to closely follow natural reading sequence.

      |history_end|

   .. index::
      pair: rect; get_textbox
      pair: textpage; get_textbox

   .. method:: get_textbox(rect, textpage=None)

      Retrieve the text contained in a rectangle.

      :arg rect-like rect: rect-like.
      :arg textpage: a :ref:`TextPage` to use. If omitted, a new, temporary textpage will be created.

      :returns: a string with interspersed linebreaks where necessary. It is based on dedicated code (changed in v1.19.0). A typical use is checking the result of :meth:`Page.search_for`:

        >>> rl = page.search_for("currency:")
        >>> page.get_textbox(rl[0])
        'Currency:'
        >>>

      |history_begin|

      * New in v1.17.7
      * Changed in v1.19.0: add `textpage` parameter

      |history_end|


   .. index::
      pair: flags; get_textpage
      pair: clip; get_textpage

   .. method:: get_textpage(clip=None, flags=3)

      Create a :ref:`TextPage` for the page.

      :arg int flags: indicator bits controlling the content available for subsequent text extractions and searches -- see the parameter of :meth:`Page.get_text`.

      :arg rect-like clip: restrict extracted text to this area. (New in v1.17.7)

      :returns: :ref:`TextPage`

      |history_begin|

      * New in v1.16.5
      * Changed in v1.17.7: introduced `clip` parameter.

      |history_end|


   .. index::
      pair: flags; get_textpage_ocr
      pair: language; get_textpage_ocr
      pair: dpi; get_textpage_ocr
      pair: full; get_textpage_ocr
      pair: tessdata; get_textpage_ocr

   .. method:: get_textpage_ocr(flags=3, language="eng", dpi=72, full=False, tessdata=None)

      **Optical Character Recognition** (**OCR**) technology can be used to extract text data for documents where text is in a raster image format throughout the page. Use this method to **OCR** a page for text extraction.

      This method returns a :ref:`TextPage` for the page that includes OCRed text. MuPDF will invoke Tesseract-OCR if this method is used. Otherwise this is a normal :ref:`TextPage` object.

      :arg int flags: indicator bits controlling the content available for subsequent test extractions and searches -- see the parameter of :meth:`Page.get_text`.
      :arg str language: the expected language(s). Use "+"-separated values if multiple languages are expected, "eng+spa" for English and Spanish.
      :arg int dpi: the desired resolution in dots per inch. Influences recognition quality (and execution time).
      :arg bool full: whether to OCR the full page, or just the displayed images.
      :arg str tessdata: The name of Tesseract's language support folder `tessdata`. If omitted, this information must be present as environment variable `TESSDATA_PREFIX`. Can be determined by function :meth:`get_tessdata`.

      .. note:: This method does **not** support a clip parameter -- OCR will always happen for the complete page rectangle.

      :returns:
      
         a :ref:`TextPage`. Execution may be significantly longer than :meth:`Page.get_textpage`.

         For a full page OCR, **all text** will have the font "GlyphlessFont" from Tesseract. In case of partial OCR, normal text will keep its properties, and only text coming from images will have the GlyphlessFont.

         .. note::
         
            **OCRed text is only available** to PyMuPDF's text extractions and searches if their `textpage` parameter specifies the output of this method.

            `This Jupyter notebook <https://github.com/pymupdf/PyMuPDF-Utilities/blob/master/jupyter-notebooks/partial-ocr.ipynb>`_ walks through an example for using OCR textpages.

      |history_begin|

      * New in v.1.19.0
      * Changed in v1.19.1: support full and partial OCRing a page.

      |history_end|


   .. method:: get_drawings(extended=False)

      Return the vector graphics of the page. These are instructions which draw lines, rectangles, quadruples or curves, including properties like colors, transparency, line width and dashing, etc. Alternative terms are "line art" and "drawings".

      :returns: a list of dictionaries. Each dictionary item contains one or more single draw commands belonging together: they have the same properties (colors, dashing, etc.). This is called a **"path"** in PDF, so we adopted that name here, but the method **works for all document types**.

      The path dictionary for fill, stroke and fill-stroke paths has been designed to be compatible with class :ref:`Shape`. There are the following keys:

      ============== ============================================================================
      Key            Value
      ============== ============================================================================
      closePath      Same as the parameter in :ref:`Shape`.
      color          Stroke color (see :ref:`Shape`).
      dashes         Dashed line specification (see :ref:`Shape`).
      even_odd       Fill colors of area overlaps -- same as the parameter in :ref:`Shape`.
      fill           Fill color  (see :ref:`Shape`).
      items          List of draw commands: lines, rectangles, quads or curves.
      lineCap        Number 3-tuple, use its max value on output with :ref:`Shape`.
      lineJoin       Same as the parameter in :ref:`Shape`.
      fill_opacity   fill color transparency (see :ref:`Shape`). (New in v1.18.17)
      stroke_opacity stroke color transparency  (see :ref:`Shape`). (New in v1.18.17)
      rect           Page area covered by this path. Information only.
      layer          name of applicable Optional Content Group. (New in v1.22.0)
      level          the hierarchy level if `extended=True`. (New in v1.22.0)
      seqno          command number when building page appearance. (New in v1.19.0)
      type           type of this path. (New in v1.18.17)
      width          Stroke line width. (see :ref:`Shape`).
      ============== ============================================================================

      Key `"opacity"` has been replaced by the new keys `"fill_opacity"` and `"stroke_opacity"`. This is now compatible with the corresponding parameters of :meth:`Shape.finish`. (Changed in v1.18.17)


      For paths other than groups or clips, key `"type"` takes one of the following values:

      * **"f"** -- this is a *fill-only* path. Only key-values relevant for this operation have a meaning, not applicable ones are present with a value of ``None``: `"color"`, `"lineCap"`, `"lineJoin"`, `"width"`, `"closePath"`, `"dashes"` and should be ignored.
      * **"s"** -- this is a *stroke-only* path. Similar to previous, key `"fill"` is present with value ``None``.
      * **"fs"** -- this is a path performing combined *fill* and *stroke* operations.

      Each item in `path["items"]` is one of the following:

      * `("l", p1, p2)` - a line from p1 to p2 (:ref:`Point` objects).
      * `("c", p1, p2, p3, p4)` - cubic Bézier curve **from p1 to p4** (p2 and p3 are the control points). All objects are of type :ref:`Point`.
      * `("re", rect, orientation)` - a :ref:`Rect`. Multiple rectangles within the same path are now detected (changed in v1.18.17). Integer `orientation` is 1 resp. -1 indicating whether the enclosed area is rotated left (1 = anti-clockwise), or resp. right [#f7]_ (changed in v1.19.2).
      * `("qu", quad)` - a :ref:`Quad`. 3 or 4 consecutive lines are detected to actually represent a :ref:`Quad` (changed in v1.19.2:). (New in v1.18.17)

      .. note::, quads and rectangles are more reliably recognized as such. (Starting with v1.19.2)

      Using class :ref:`Shape`, you should be able to recreate the original drawings on a separate (PDF) page with high fidelity under normal, not too sophisticated circumstances. Please see the following comments on restrictions. A coding draft can be found in :ref:`How to Extract Drawings <RecipesDrawingAndGraphics_Extract_Drawings>`.

      Specifying `extended=True` significantly alters the output. Most importantly, new dictionary types are present: "clip" and "group". All paths will now be organized in a hierarchic structure which is encoded by the new integer key "level", the hierarchy level. Each group or clip establishes a new hierarchy, which applies to all subsequent paths having a *larger* level value. (New in v1.22.0)

      Any path with a smaller level value than its predecessor will end the scope of (at least) the preceding hierarchy level. A "clip" path with the same level as the preceding clip will end the scope of that clip. Same is true for groups. This is best explained by an example::

         +------+------+--------+------+--------+
         | line | lvl0 | lvl1   | lvl2 |  lvl3  |
         +------+------+--------+------+--------+
         |  0   | clip |        |      |        |
         |  1   |      | fill   |      |        |
         |  2   |      | group  |      |        |
         |  3   |      |        | clip |        |
         |  4   |      |        |      | stroke |
         |  5   |      |        | fill |        |  ends scope of clip in line 3
         |  6   |      | stroke |      |        |  ends scope of group in line 2
         |  7   |      | clip   |      |        |
         |  8   | fill |        |      |        |  ends scope of line 0
         +------+------+--------+------+--------+

      The clip in line 0 applies to line including line 7. Group in line 2 applies to lines 3 to 5, clip in line 3 only applies to line 4.

      "stroke" in line 4 is under control of "group" in line 2 and "clip" in line 3 (which in turn is a subset of line 0 clip).

      * **"clip"** dictionary. Its values (most importantly "scissor") remain valid / apply as long as following dictionaries have a **larger "level"** value.

        ============== ============================================================================
        Key            Value
        ============== ============================================================================
        closePath      Same as in "stroke" or "fill" dictionaries
        even_odd       Same as in "stroke" or "fill" dictionaries
        items          Same as in "stroke" or "fill" dictionaries
        rect           Same as in "stroke" or "fill" dictionaries
        layer          Same as in "stroke" or "fill" dictionaries
        level          Same as in "stroke" or "fill" dictionaries
        scissor        the clip rectangle
        type           "clip"
        ============== ============================================================================

      * "group" dictionary. Its values remain valid (apply) as long as following dictionaries have a **larger "level"** value. Any dictionary with an equal or lower level end this group.

        ============== ============================================================================
        Key            Value
        ============== ============================================================================
        rect           Same as in "stroke" or "fill" dictionaries
        layer          Same as in "stroke" or "fill" dictionaries
        level          Same as in "stroke" or "fill" dictionaries
        isolated       (bool) Whether this group is isolated
        knockout       (bool) Whether this is a "Knockout Group"
        blendmode      Name of the BlendMode, default is "Normal"
        opacity        Float value in range [0, 1].
        type           "group"
        ============== ============================================================================

      .. note:: The method is based on the output of :meth:`Page.get_cdrawings` -- which is much faster, but requires somewhat more attention processing its output.

      |history_begin|
      
      * New in v1.18.0
      * Changed in v1.18.17
      * Changed in v1.19.0: add "seqno" key, remove "clippings" key
      * Changed in v1.19.1: "color" / "fill" keys now always are either are RGB tuples or `None`. This resolves issues caused by exotic colorspaces.
      * Changed in v1.19.2: add an indicator for the *"orientation"* of the area covered by an "re" item.
      * Changed in v1.22.0: add new key `"layer"` which contains the name of the Optional Content Group of the path (or `None`).
      * Changed in v1.22.0: add parameter `extended` to also return clipping and group paths.
      
      |history_end|



   .. method:: get_cdrawings(extended=False)

      Extract the vector graphics on the page. Apart from following technical differences, functionally equivalent to :meth:`Page.get_drawings`, but much faster:

      * Every path type only contains the relevant keys, e.g. a stroke path has no `"fill"` color key. See comment in method :meth:`Page.get_drawings`.
      * Coordinates are given as :data:`point_like`, :data:`rect_like` and :data:`quad_like` **tuples** -- not as :ref:`Point`, :ref:`Rect`, :ref:`Quad` objects.

      If performance is a concern, consider using this method: Compared to versions earlier than 1.18.17, you should see much shorter response times. We have seen pages that required 2 seconds then, now only need 200 ms with this method.

      |history_begin|

      * New in v1.18.17
      * Changed in v1.19.0: removed "clippings" key, added "seqno" key.
      * Changed in v1.19.1: always generate RGB color tuples.
      * Changed in v1.22.0: added new key `"layer"` which contains the name of the Optional Content Group of the path (or `None`).
      * Changed in v1.22.0: added parameter `extended` to also return clipping paths.
      
      |history_end|


   .. method:: get_fonts(full=False)

      PDF only: Return a list of fonts referenced by the page. Wrapper for :meth:`Document.get_page_fonts`.


   .. method:: get_images(full=False)

      PDF only: Return a list of images referenced by the page. Wrapper for :meth:`Document.get_page_images`.


   .. index::
      pair: hashes; get_image_info
      pair: xrefs; get_image_info

   .. method:: get_image_info(hashes=False, xrefs=False)

      Return a list of meta information dictionaries for all images displayed by the page. This works for all document types.

      :arg bool hashes: Compute the MD5 hashcode for each encountered image, which allows identifying image duplicates. This adds the key `"digest"` to the output, whose value is a 16 byte `bytes` object. (New in v1.18.13)

      :arg bool xrefs: **PDF only.** Try to find the :data:`xref` for each image. Implies `hashes=True`. Adds the `"xref"` key to the dictionary. If not found, the value is 0, which means, the image is either "inline" or its xref is undetectable for some reason. Please note that this option has an extended response time, because the MD5 hashcode will be computed at least two times for each image with an xref. (New in v1.18.13)

      :rtype: list[dict]
      :returns: A list of dictionaries. This includes information for **exactly those** images, that are shown on the page -- including *"inline images"*. The dictionary layout is similar to that of image blocks in `page.get_text("dict")`.
      
         In contrast to images included in :meth:`Page.get_text`, image **binary content** is not loaded by this method, which drastically reduces memory usage. Another difference is that image detection is not restricted to the visible part of the page or any ``clip`` parameter: method :meth:`Page.get_text` will only extract images **fully contained** in the provided ``clip``.

         =============== ===============================================================
         **Key**             **Value**
         =============== ===============================================================
         number          block number (``int``)
         bbox            image bbox on page, :data:`rect_like`
         width           original image width (``int``)
         height          original image height (``int``)
         cs-name         colorspace name (``str``)
         colorspace      colorspace.n (``int``)
         xres            resolution in x-direction (``int``)
         yres            resolution in y-direction (``int``)
         bpc             bits per component (``int``)
         size            storage occupied by image (``int``)
         digest          MD5 hashcode (``bytes``), if ``hashes`` is true
         xref            image :data:`xref` or 0, if *xrefs* is true
         transform       matrix transforming image rect to bbox, :data:`matrix_like`
         has-mask        whether the image is transparent and has a mask (``bool``)
         =============== ===============================================================

         Multiple occurrences of the same image are always reported. You can detect duplicates by comparing their `digest` values.

      |history_begin|

      * New in v1.18.11
      * Changed in v1.18.13: added image MD5 hashcode computation and :data:`xref` search.

      |history_end|


   .. method:: get_xobjects()

      PDF only: Return a list of Form XObjects referenced by the page. Wrapper for :meth:`Document.get_page_xobjects`.


   .. index::
      pair: transform; get_image_rects

   .. method:: get_image_rects(item, transform=False)

      PDF only: Return boundary boxes and transformation matrices of an embedded image. This is an improved version of :meth:`Page.get_image_bbox` with the following differences:

      * There is no restriction on **how** the image is invoked (by the page or one of its Form XObjects). The result is always complete and correct.
      * The result is a list of :ref:`Rect` or (:ref:`Rect`, :ref:`Matrix`) objects -- depending on *transform*. Each list item represents one location of the image on the page. Multiple occurrences might not be detectable by :meth:`Page.get_image_bbox`.
      * The method invokes :meth:`Page.get_image_info` with `xrefs=True` and therefore has a noticeably longer response time than :meth:`Page.get_image_bbox`.

      :arg list,str,int item: an item of the list :meth:`Page.get_images`, or the reference **name** entry of such an item (item[7]), or the image :data:`xref`.
      :arg bool transform: also return the matrix used to transform the image rectangle to the bbox on the page. If true, then tuples `(bbox, matrix)` are returned.

      :rtype: list
      :returns: Boundary boxes and respective transformation matrices for each image occurrence on the page. If the item is not on the page, an empty list `[]` is returned.

      |history_begin|

      New in v1.18.13

      |history_end|


   .. index::
      pair: transform; get_image_bbox

   .. method:: get_image_bbox(item, transform=False)

      PDF only: Return boundary box and transformation matrix of an embedded image.

      :arg list,str item: an item of the list :meth:`Page.get_images` with *full=True* specified, or the reference **name** entry of such an item, which is item[-3] (or item[7] respectively).
      :arg bool transform: return the matrix used to transform the image rectangle to the bbox on the page (new in v1.18.11). Default is just the bbox. If true, then a tuple `(bbox, matrix)` is returned.

      :rtype: :ref:`Rect` or (:ref:`Rect`, :ref:`Matrix`)
      :returns: the boundary box of the image -- optionally also its transformation matrix.

        |history_begin|
        
        * (Changed in v1.16.7): If the page in fact does not display this image, an infinite rectangle is returned now. In previous versions, an exception was raised. Formally invalid parameters still raise exceptions.
        * (Changed in v1.17.0): Only images referenced directly by the page are considered. This means that images occurring in embedded PDF pages are ignored and an exception is raised.
        * (Changed in v1.18.5): Removed the restriction introduced in v1.17.0: any item of the page's image list may be specified.
        * (Changed in v1.18.11): Partially re-instated a restriction: only those images are considered, that are either directly referenced by the page or by a Form XObject directly referenced by the page.
        * (Changed in v1.18.11): Optionally also return the transformation matrix together with the bbox as the tuple `(bbox, transform)`.

        |history_end|

      .. note::

         1. Be aware that :meth:`Page.get_images` may contain "dead" entries i.e. images, which the page **does not display**. This is no error, but intended by the PDF creator. No exception will be raised in this case, but an infinite rectangle is returned. You can avoid this from happening by executing :meth:`Page.clean_contents` before this method.
         2. The image's "transformation matrix" is defined as the matrix, for which the expression `bbox / transform == pymupdf.Rect(0, 0, 1, 1)` is true, lookup details here: :ref:`ImageTransformation`.

      |history_begin|

      * Changed in v1.18.11: return image transformation matrix

      |history_end|

   .. index::
      pair: matrix; get_svg_image

   .. method:: get_svg_image(matrix=pymupdf.Identity, text_as_path=True)

     Create an SVG image from the page. Only full page images are currently supported.

     :arg matrix_like matrix: a matrix, default is :ref:`Identity`.
     :arg bool text_as_path: -- controls how text is represented. ``True`` outputs each character as a series of elementary draw commands, which leads to a more precise text display in browsers, but a **very much larger** output for text-oriented pages. Display quality for ``False`` relies on the presence of the referenced fonts on the current system. For missing fonts, the internet browser will fall back to some default -- leading to unpleasant appearances. Choose ``False`` if you want to parse the text of the SVG. (New in v1.17.5)

     :returns: a UTF-8 encoded string that contains the image. Because SVG has XML syntax it can be saved in a text file, the standard extension is `.svg`.

         .. note:: In case of a PDF, you can circumvent the "full page image only" restriction by modifying the page's CropBox before using the method.

   .. index::
      pair: alpha; get_pixmap
      pair: annots; get_pixmap
      pair: clip; get_pixmap
      pair: colorspace; get_pixmap
      pair: matrix; get_pixmap
      pair: dpi; get_pixmap

   .. method:: get_pixmap(*, matrix=pymupdf.Identity, dpi=None, colorspace=pymupdf.csRGB, clip=None, alpha=False, annots=True)

     Create a pixmap from the page. This is probably the most often used method to create a :ref:`Pixmap`.

     All parameters are *keyword-only.*

     :arg matrix_like matrix: default is :ref:`Identity`.
     :arg int dpi: desired resolution in x and y direction. If not `None`, the `"matrix"` parameter is ignored. (New in v1.19.2)
     :arg colorspace: The desired colorspace, one of "GRAY", "RGB" or "CMYK" (case insensitive). Or specify a :ref:`Colorspace`, ie. one of the predefined ones: :data:`csGRAY`, :data:`csRGB` or :data:`csCMYK`.
     :type colorspace: str or :ref:`Colorspace`
     :arg irect_like clip: restrict rendering to the intersection of this area with the page's rectangle.
     :arg bool alpha: whether to add an alpha channel. Always accept the default ``False`` if you do not really need transparency. This will save a lot of memory (25% in case of RGB ... and pixmaps are typically **large**!), and also processing time. Also note an **important difference** in how the image will be rendered: with ``True`` the pixmap's samples area will be pre-cleared with *0x00*. This results in **transparent** areas where the page is empty. With ``False`` the pixmap's samples will be pre-cleared with *0xff*. This results in **white** where the page has nothing to show.

       |history_begin|
      
       Changed in v1.14.17
         The default alpha value is now ``False``.

         * Generated with *alpha=True*

         .. image:: images/img-alpha-1.*


         * Generated with *alpha=False*

         .. image:: images/img-alpha-0.*

       |history_end|

     :arg bool annots: *(new in version 1.16.0)* whether to also render annotations or to suppress them. You can create pixmaps for annotations separately.

     :rtype: :ref:`Pixmap`
     :returns: Pixmap of the page. For fine-controlling the generated image, the by far most important parameter is **matrix**. E.g. you can increase or decrease the image resolution by using **Matrix(xzoom, yzoom)**. If zoom > 1, you will get a higher resolution: zoom=2 will double the number of pixels in that direction and thus generate a 2 times larger image. Non-positive values will flip horizontally, resp. vertically. Similarly, matrices also let you rotate or shear, and you can combine effects via e.g. matrix multiplication. See the :ref:`Matrix` section to learn more.

     .. note::

         * The pixmap will have *"premultiplied"* pixels if `alpha=True`. To learn about some background, e.g. look for "Premultiplied alpha" `here <https://en.wikipedia.org/wiki/Glossary_of_computer_graphics#P>`_.

         * The method will respect any page rotation and will not exceed the intersection of `clip` and :attr:`Page.cropbox`. If you need the page's mediabox (and if this is a different rectangle), you can use a snippet like the following to achieve this::

            In [1]: import pymupdf
            In [2]: doc=pymupdf.open("demo1.pdf")
            In [3]: page=doc[0]
            In [4]: rotation = page.rotation
            In [5]: cropbox = page.cropbox
            In [6]: page.set_cropbox(page.mediabox)
            In [7]: page.set_rotation(0)
            In [8]: pix = page.get_pixmap()
            In [9]: page.set_cropbox(cropbox)
            In [10]: if rotation != 0:
               ...:     page.set_rotation(rotation)
               ...:
            In [11]:

     |history_begin|

     * Changed in v1.19.2: added support of parameter dpi.

     |history_end|



   .. method:: annot_names()

      PDF only: return a list of the names of annotations, widgets and links. Technically, these are the */NM* values of every PDF object found in the page's */Annots*  array.

      :rtype: list

      |history_begin|

      * New in v1.16.10

      |history_end|


   .. method:: annot_xrefs()

      PDF only: return a list of the :data:`xref` numbers of annotations, widgets and links -- technically of all entries found in the page's */Annots*  array.

      :rtype: list
      :returns: a list of items *(xref, type)* where type is the annotation type. Use the type to tell apart links, fields and annotations, see :ref:`AnnotationTypes`.

      |history_begin|

      * New in v1.17.1

      |history_end|


   .. method:: load_annot(ident)

      PDF only: return the annotation identified by *ident*. This may be its unique name (PDF `/NM` key), or its :data:`xref`.

      :arg str,int ident: the annotation name or xref.

      :rtype: :ref:`Annot`
      :returns: the annotation or ``None``.

      .. note:: Methods :meth:`Page.annot_names`, :meth:`Page.annot_xrefs` provide lists of names or xrefs, respectively, from where an item may be picked and loaded via this method.

      |history_begin|

      * New in v1.17.1

      |history_end|

   .. method:: load_widget(xref)

      PDF only: return the field identified by *xref*.

      :arg int xref: the field's xref.

      :rtype: :ref:`Widget`
      :returns: the field or ``None``.

      .. note:: This is similar to the analogous method :meth:`Page.load_annot` -- except that here only the xref is supported as identifier.

      |history_begin|

      * New in v1.19.6

      |history_end|

   .. method:: load_links()

      Return the first link on a page. Synonym of property :attr:`first_link`.

      :rtype: :ref:`Link`
      :returns: first link on the page (or ``None``).

   .. index::
      pair: rotate; set_rotation

   .. method:: set_rotation(rotate)

      PDF only: Set the rotation of the page.

      :arg int rotate: An integer specifying the required rotation in degrees. Must be an integer multiple of 90. Values will be converted to one of 0, 90, 180, 270.

   .. method:: remove_rotation()

      PDF only: Set page rotation to 0 while maintaining appearance and page content.

      :returns: The inverted matrix used to achieve this change. If the page was not rotated (rotation 0), :ref:`Identity` is returned. The method automatically recomputes the rectangles of any annotations, links and widgets present on the page.

         This method may come in handy when e.g. used with :meth:`Page.show_pdf_page`.

   .. index::
      pair: clip; show_pdf_page
      pair: keep_proportion; show_pdf_page
      pair: overlay; show_pdf_page
      pair: rotate; show_pdf_page

   .. method:: show_pdf_page(rect, docsrc, pno=0, keep_proportion=True, overlay=True, oc=0, rotate=0, clip=None)

      PDF only: Display a page of another PDF as a **vector image** (otherwise similar to :meth:`Page.insert_image`). This is a multi-purpose method. For example, you can use it to:

      * create "n-up" versions of existing PDF files, combining several input pages into **one output page** (see example `combine.py <https://github.com/pymupdf/PyMuPDF-Utilities/blob/master/examples/combine-pages/combine.py>`_),
      * create "posterized" PDF files, i.e. every input page is split up in parts which each create a separate output page (see `posterize.py <https://github.com/pymupdf/PyMuPDF-Utilities/blob/master/examples/posterize-document/posterize.py>`_),
      * include PDF-based vector images like company logos, watermarks, etc., see `svg-logo.py <https://github.com/pymupdf/PyMuPDF-Utilities/tree/master/examples/svg-logo.py>`_, which puts an SVG-based logo on each page (requires additional packages to deal with SVG-to-PDF conversions).

      :arg rect_like rect: where to place the image on current page. Must be finite and its intersection with the page must not be empty.
      :arg docsrc: source PDF document containing the page. Must be a different document object, but may be the same file.
      :type docsrc: :ref:`Document`

      :arg int pno: page number (0-based, in `-∞ < pno < docsrc.page_count`) to be shown.

      :arg bool keep_proportion: whether to maintain the width-height-ratio (default). If false, all 4 corners are always positioned on the border of the target rectangle -- whatever the rotation value. In general, this will deliver distorted and /or non-rectangular images.

      :arg bool overlay: put image in foreground (default) or background.

      :arg int oc: (:data:`xref`) make visibility dependent on this :data:`OCG` / :data:`OCMD` (which must be defined in the target PDF) [#f9]_. (New in v1.18.3)
      :arg float rotate: show the source rectangle rotated by some angle. Any angle is supported (changed in v1.14.11). (New in v1.14.10)

      :arg rect_like clip: choose which part of the source page to show. Default is the full page, else must be finite and its intersection with the source page must not be empty.

      .. note:: In contrast to method :meth:`Document.insert_pdf`, this method does not copy annotations, widgets or links, so these are not included in the target [#f6]_. But all its **other resources (text, images, fonts, etc.)** will be imported into the current PDF. They will therefore appear in text extractions and in :meth:`get_fonts` and :meth:`get_images` lists -- even if they are not contained in the visible area given by *clip*.

      Example: Show the same source page, rotated by 90 and by -90 degrees:

      >>> doc = pymupdf.open()  # new empty PDF
      >>> page=doc.new_page()  # new page in A4 format
      >>>
      >>> # upper half page
      >>> r1 = pymupdf.Rect(0, 0, page.rect.width, page.rect.height/2)
      >>>
      >>> # lower half page
      >>> r2 = r1 + (0, page.rect.height/2, 0, page.rect.height/2)
      >>>
      >>> src = pymupdf.open("PyMuPDF.pdf")  # show page 0 of this
      >>>
      >>> page.show_pdf_page(r1, src, 0, rotate=90)
      >>> page.show_pdf_page(r2, src, 0, rotate=-90)
      >>> doc.save("show.pdf")

      .. image:: images/img-showpdfpage.*
         :scale: 70

      |history_begin|

      * Changed in v1.14.11: Parameter *reuse_xref* has been deprecated. Position the source rectangle centered in target rectangle. Any rotation angle is now supported.
      * Changed in v1.18.3: New parameter `oc`.

      |history_end|

   .. method:: new_shape()

      PDF only: Create a new :ref:`Shape` object for the page.

      :rtype: :ref:`Shape`
      :returns: a new :ref:`Shape` to use for compound drawings. See description there.


   .. index::
      pair: flags; search_for
      pair: quads; search_for
      pair: clip; search_for
      pair: textpage; search_for

   .. method:: search_for(needle, *, clip=None, quads=False, flags=TEXT_DEHYPHENATE | TEXT_PRESERVE_WHITESPACE | TEXT_PRESERVE_LIGATURES | TEXT_MEDIABOX_CLIP, textpage=None)

      Search for *needle* on a page. Wrapper for :meth:`TextPage.search`.

      :arg str needle: Text to search for. May contain spaces. Upper / lower case is ignored, but only works for ASCII characters: For example, "COMPÉTENCES" will not be found if needle is "compétences" -- "compÉtences" however will. Similar is true for German umlauts and the like.
      :arg rect_like clip: only search within this area. (New in v1.18.2)
      :arg bool quads: Return object type :ref:`Quad` instead of :ref:`Rect`.
      :arg int flags: Control the data extracted by the underlying :ref:`TextPage`. By default, ligatures and white spaces are kept, and hyphenation [#f8]_ is detected.
      :arg textpage: use a previously created :ref:`TextPage`. This reduces execution time **significantly.** If specified, the 'flags' and 'clip' arguments are ignored. If omitted, a temporary textpage will be created. (New in v1.19.0)

      :rtype: list

      :returns:

        A list of :ref:`Rect` or  :ref:`Quad` objects, each of which  -- **normally!** -- surrounds one occurrence of *needle*. **However:** if parts of *needle* occur on more than one line, then a separate item is generated for each these parts. So, if `needle = "search string"`, two rectangles may be generated.

        |history_begin|
        
        Changes in v1.18.2:

        * There no longer is a limit on the list length (removal of the `hit_max` parameter).
        * If a word is **hyphenated** at a line break, it will still be found. E.g. the needle "method" will be found even if hyphenated as "meth-od" at a line break, and two rectangles will be returned: one surrounding "meth" (without the hyphen) and another one surrounding "od".

        |history_end|

      .. note:: The method supports multi-line text marker annotations: you can use the full returned list as **one single** parameter for creating the annotation.

      .. caution::

         * There is a tricky aspect: the search logic regards **contiguous multiple occurrences** of *needle* as one: assuming *needle* is "abc", and the page contains "abc" and "abcabc", then only **two** rectangles will be returned, one for "abc", and a second one for "abcabc".
         * You can always use :meth:`Page.get_textbox` to check what text actually is being surrounded by each rectangle.

      .. note:: A feature repeatedly asked for is supporting **regular expressions** when specifying the `"needle"` string: **There is no way to do this.** If you need something in that direction, first extract text in the desired format and then subselect the result by matching with some regex pattern. Here is an example for matching words::

         >>> pattern = re.compile(r"...")  # the regex pattern
         >>> words = page.get_text("words")  # extract words on page
         >>> matches = [w for w in words if pattern.search(w[4])]

         The `matches` list will contain the words matching the given pattern. In the same way you can select `span["text"]` from the output of `page.get_text("dict")`.

      |history_begin|

      * Changed in v1.18.2: added `clip` parameter. Remove `hit_max` parameter. Add default "dehyphenate".
      * Changed in v1.19.0: added `textpage` parameter.

      |history_end|


   .. method:: set_mediabox(r)

      PDF only: Change the physical page dimension by setting :data:`mediabox` in the page's object definition.

      :arg rect-like r: the new :data:`mediabox` value.

      .. note:: This method also removes the page's other (optional) rectangles (:data:`cropbox`, ArtBox, TrimBox and Bleedbox) to prevent inconsistent situations. This will cause those to assume their default values.

      .. caution:: For non-empty pages this may have undesired effects, because the location of all content depends on this value and will therefore change position or even disappear.

      |history_begin|

      * New in v1.16.13
      * Changed in v1.19.4: remove all other rectangle definitions.

      |history_end|


   .. method:: set_cropbox(r)

      PDF only: change the visible part of the page.

      :arg rect_like r: the new visible area of the page. Note that this **must** be specified in **unrotated coordinates**, not empty, nor infinite and be completely contained in the :attr:`Page.mediabox`.

      After execution **(if the page is not rotated)**, :attr:`Page.rect` will equal this rectangle, but be shifted to the top-left position (0, 0) if necessary. Example session:

      >>> page = doc.new_page()
      >>> page.rect
      pymupdf.Rect(0.0, 0.0, 595.0, 842.0)
      >>>
      >>> page.cropbox  # cropbox and mediabox still equal
      pymupdf.Rect(0.0, 0.0, 595.0, 842.0)
      >>>
      >>> # now set cropbox to a part of the page
      >>> page.set_cropbox(pymupdf.Rect(100, 100, 400, 400))
      >>> # this will also change the "rect" property:
      >>> page.rect
      pymupdf.Rect(0.0, 0.0, 300.0, 300.0)
      >>>
      >>> # but mediabox remains unaffected
      >>> page.mediabox
      pymupdf.Rect(0.0, 0.0, 595.0, 842.0)
      >>>
      >>> # revert CropBox change
      >>> # either set it to MediaBox
      >>> page.set_cropbox(page.mediabox)
      >>> # or 'refresh' MediaBox: will remove all other rectangles
      >>> page.set_mediabox(page.mediabox)

   .. method:: set_artbox(r)

   .. method:: set_bleedbox(r)

   .. method:: set_trimbox(r)

      PDF only: Set the resp. rectangle in the page object. For the meaning of these objects see :ref:`AdobeManual`, page 77. Parameter and restrictions are the same as for :meth:`Page.set_cropbox`.

      |history_begin|

      * New in v1.19.4

      |history_end|

   .. attribute:: rotation

      Contains the rotation of the page in degrees (always 0 for non-PDF types). This is a copy of the value in the PDF file. The PDF documentation says:
      
         *"The number of degrees by which the page should be rotated clockwise when displayed or printed. The value must be a multiple of 90. Default value: 0."*

         In PyMuPDF, we make sure that this attribute is always one of 0, 90, 180 or 270.

      :type: int

   .. attribute:: cropbox_position

      Contains the top-left point of the page's `/CropBox` for a PDF, otherwise *Point(0, 0)*.

      :type: :ref:`Point`

   .. attribute:: cropbox

      The page's `/CropBox` for a PDF. Always the **unrotated** page rectangle is returned. For a non-PDF this will always equal the page rectangle.

      .. note:: In PDF, the relationship between `/MediaBox`, `/CropBox` and page rectangle may sometimes be confusing, please do lookup the glossary for :data:`MediaBox`.

      :type: :ref:`Rect`

   .. attribute:: artbox

   .. attribute:: bleedbox

   .. attribute:: trimbox

      The page's `/ArtBox`, `/BleedBox`, `/TrimBox`, respectively. If not provided, defaulting to :attr:`Page.cropbox`.

      :type: :ref:`Rect`

   .. attribute:: mediabox_size

      Contains the width and height of the page's :attr:`Page.mediabox` for a PDF, otherwise the bottom-right coordinates of :attr:`Page.rect`.

      :type: :ref:`Point`

   .. attribute:: mediabox

      The page's :data:`mediabox` for a PDF, otherwise :attr:`Page.rect`.

      :type: :ref:`Rect`

      .. note:: For most PDF documents and for **all other document types**, `page.rect == page.cropbox == page.mediabox` is true. However, for some PDFs the visible page is a true subset of :data:`mediabox`. Also, if the page is rotated, its `Page.rect` may not equal `Page.cropbox`. In these cases the above attributes help to correctly locate page elements.

   .. attribute:: transformation_matrix

      This matrix translates coordinates from the PDF space to the MuPDF space. For example, in PDF `/Rect [x0 y0 x1 y1]` the pair (x0, y0) specifies the **bottom-left** point of the rectangle -- in contrast to MuPDF's system, where (x0, y0) specify top-left. Multiplying the PDF coordinates with this matrix will deliver the (Py-) MuPDF rectangle version. Obviously, the inverse matrix will again yield the PDF rectangle.

      :type: :ref:`Matrix`

   .. attribute:: rotation_matrix

   .. attribute:: derotation_matrix

      These matrices may be used for dealing with rotated PDF pages. When adding / inserting anything to a PDF page, the coordinates of the **unrotated** page are always used. These matrices help translating between the two states. Example: if a page is rotated by 90 degrees -- what would then be the coordinates of the top-left Point(0, 0) of an A4 page?

         >>> page.set_rotation(90)  # rotate an ISO A4 page
         >>> page.rect
         Rect(0.0, 0.0, 842.0, 595.0)
         >>> p = pymupdf.Point(0, 0)  # where did top-left point land?
         >>> p * page.rotation_matrix
         Point(842.0, 0.0)
         >>>

      :type: :ref:`Matrix`

   .. attribute:: first_link

      Contains the first :ref:`Link` of a page (or ``None``).

      :type: :ref:`Link`

   .. attribute:: first_annot

      Contains the first :ref:`Annot` of a page (or ``None``).

      :type: :ref:`Annot`

   .. attribute:: first_widget

      Contains the first :ref:`Widget` of a page (or ``None``).

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

.. _link_dict_description:

Description of *get_links()* Entries
----------------------------------------
Each entry of the :meth:`Page.get_links` list is a dictionary with the following keys:

* *kind*:  (required) an integer indicating the kind of link. This is one of *LINK_NONE*, *LINK_GOTO*, *LINK_GOTOR*, *LINK_LAUNCH*, or *LINK_URI*. For values and meaning of these names refer to :ref:`linkDest Kinds`.

* *from*:  (required) a :ref:`Rect` describing the "hot spot" location on the page's visible representation (where the cursor changes to a hand image, usually).

* *page*:  a 0-based integer indicating the destination page. Required for *LINK_GOTO* and *LINK_GOTOR*, else ignored.

* *to*:   either a *pymupdf.Point*, specifying the destination location on the provided page, default is *pymupdf.Point(0, 0)*, or a symbolic (indirect) name. If an indirect name is specified, *page = -1* is required and the name must be defined in the PDF in order for this to work. Required for *LINK_GOTO* and *LINK_GOTOR*, else ignored.

* *file*: a string specifying the destination file. Required for *LINK_GOTOR* and *LINK_LAUNCH*, else ignored.

* *uri*:  a string specifying the destination internet resource. Required for *LINK_URI*, else ignored. You should make sure to start this string with an unambiguous substring, that classifies the subtype of the URL, like `"http://"`, `"https://"`, `"file://"`, `"ftp://"`, `"mailto:"`, etc. Otherwise your browser will try to interpret the text and come to unwanted / unexpected conclusions about the intended URL type.

* *xref*: an integer specifying the PDF :data:`xref` of the link object. Do not change this entry in any way. Required for link deletion and update, otherwise ignored. For non-PDF documents, this entry contains *-1*. It is also *-1* for **all** entries in the *get_links()* list, if **any** of the links is not supported by MuPDF - see :ref:`notes_on_supporting_links`.

.. _notes_on_supporting_links:

Notes on Supporting Links
---------------------------
MuPDF's support for links has changed in **v1.10a**. These changes affect link types :data:`LINK_GOTO` and :data:`LINK_GOTOR`.

Reading (pertains to method *get_links()* and the *first_link* property chain)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If MuPDF detects a link to another file, it will supply either a *LINK_GOTOR* or a *LINK_LAUNCH* link kind. In case of *LINK_GOTOR* destination details may either be given as page number (eventually including position information), or as an indirect destination.

If an indirect destination is given, then this is indicated by *page = -1*, and *link.dest.dest* will contain this name. The dictionaries in the *get_links()* list will contain this information as the *to* value.

**Internal links are always** of kind *LINK_GOTO*. If an internal link specifies an indirect destination, it **will always be resolved** and the resulting direct destination will be returned. Names are **never returned for internal links**, and undefined destinations will cause the link to be ignored.

Writing
~~~~~~~~~

PyMuPDF writes (updates, inserts) links by constructing and writing the appropriate PDF object **source**. This makes it possible to specify indirect destinations for *LINK_GOTOR* **and** *LINK_GOTO* link kinds (pre *PDF 1.2* file formats are **not supported**).

.. warning:: If a *LINK_GOTO* indirect destination specifies an undefined name, this link can later on not be found / read again with MuPDF / PyMuPDF. Other readers however **will** detect it, but flag it as erroneous.

Indirect *LINK_GOTOR* destinations can in general of course not be checked for validity and are therefore **always accepted**.

**Example: How to insert a link pointing to another page in the same document**

1. Determine the rectangle on the current page, where the link should be placed. This may be the bbox of an image or some text.

2. Determine the target page number ("pno", 0-based) and a :ref:`Point` on it, where the link should be directed to.

3. Create a dictionary `d = {"kind": pymupdf.LINK_GOTO, "page": pno, "from": bbox, "to": point}`.

4. Execute `page.insert_link(d)`.


Homologous Methods of :ref:`Document` and :ref:`Page`
--------------------------------------------------------
This is an overview of homologous methods on the :ref:`Document` and on the :ref:`Page` level.

====================================== =====================================
**Document Level**                     **Page Level**
====================================== =====================================
*Document.get_page_fonts(pno)*         :meth:`Page.get_fonts`
*Document.get_page_images(pno)*        :meth:`Page.get_images`
*Document.get_page_pixmap(pno, ...)*   :meth:`Page.get_pixmap`
*Document.get_page_text(pno, ...)*     :meth:`Page.get_text`
*Document.search_page_for(pno, ...)*   :meth:`Page.search_for`
====================================== =====================================

The page number "pno" is a 0-based integer `-∞ < pno < page_count`.

.. note::

   Most document methods (left column) exist for convenience reasons, and are just wrappers for: *Document[pno].<page method>*. So they **load and discard the page** on each execution.

   However, the first two methods work differently. They only need a page's object definition statement - the page itself will **not** be loaded. So e.g. :meth:`Page.get_fonts` is a wrapper the other way round and defined as follows: *page.get_fonts == page.parent.get_page_fonts(page.number)*.

.. rubric:: Footnotes

.. [#f1] If your existing code already uses the installed base name as a font reference (as it was supported by PyMuPDF versions earlier than 1.14), this will continue to work.

.. [#f2] Not all PDF reader software (including internet browsers and office software) display all of these fonts. And if they do, the difference between the **serifed** and the **non-serifed** version may hardly be noticeable. But serifed and non-serifed versions lead to different installed base fonts, thus providing an option to be displayable with your specific PDF viewer.

.. [#f3] Not all PDF readers display these fonts at all. Some others do, but use a wrong character spacing, etc.

.. [#f4] You are generally free to choose any of the :ref:`mupdficons` you consider adequate.

.. [#f5] The previous algorithm caused images to be **shrunk** to this intersection. Now the image can be anywhere on :attr:`Page.mediabox`, potentially being invisible or only partially visible if the cropbox (representing the visible page part) is smaller.

.. [#f6] If you need to also see annotations or fields in the target page, you can convert the source PDF using :meth:`Document.bake`. The underlying MuPDF function of that method will convert these objects to normal page content. Then use :meth:`Page.show_pdf_page` with the converted PDF page.

.. [#f7] In PDF, an area enclosed by some lines or curves can have a property called "orientation". This is significant for switching on or off the fill color of that area when there exist multiple area overlaps - see discussion in method :meth:`Shape.finish` using the "non-zero winding number" rule. While orientation of curves, quads, triangles and other shapes enclosed by lines always was detectable, this has been impossible for "re" (rectangle) items in the past. Adding the orientation parameter now delivers the missing information.

.. [#f8] Hyphenation detection simply means that if the last character of a line is "-", it will be assumed to be a continuation character. That character will not be found by text searching with its default flag setting. Please take note, that a MuPDF *line* may not always be what you expect: words separated by overly large gaps (e.g. caused by text justification) may constitute separate MuPDF lines. If then any of these words ends with a hyphen, it will only be found by text searching if hyphenation is switched off.

.. [#f9] Objects inside the source page, like images, text or drawings, are never aware of whether their owning page now is under OC control inside the target PDF. If source page objects are OC-controlled in the source PDF, then this will not be retained on the target: they will become unconditionally visible.

.. include:: footer.rst
