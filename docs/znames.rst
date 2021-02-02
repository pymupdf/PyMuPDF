.. _Deprecated:

================
Deprecated Names
================

This is a list of names for methods and attributes with references to their current notions.
This list is a result of the effort to replace "mixedCase" names by their "snake_case" alternative.

This is a major effort, that we only can muster in a step-wise fashion. We believe we so far (v1.18.7) are done with :ref:`Annot`, :ref:`Document`, :ref:`Page` and :ref:`TextWriter`.

Names of classes and package-wide constants remain untouched.
Old names remain available for some time, but will be removed in some future version. Apart from this section however, old names will no longer be mentioned in this documentation.

Document
-----------

================== =============================================================
Old Name           New Name
================== =============================================================
chapterCount       :attr:`Document.chapter_count`
chapterPageCount   :meth:`Document.chapter_page_count`
convertToPDF       :meth:`Document.convert_to_pdf`
copyPage           :meth:`Document.copy_page`
deletePage         :meth:`Document.delete_page`
deletePageRange    :meth:`Document.delete_pages`
embeddedFileAdd    :meth:`Document.embfile_add`
embeddedFileCount  :meth:`Document.embfile_count`
embeddedFileDel    :meth:`Document.embfile_del`
embeddedFileGet    :meth:`Document.embfile_get`
embeddedFileInfo   :meth:`Document.embfile_info`
embeddedFileNames  :meth:`Document.embfile_names`
embeddedFileUpd    :meth:`Document.embfile_upd`
findBookmark       :meth:`Document.find_bookmark`
fullcopyPage       :meth:`Document.fullcopy_page`
getPagePixmap      :meth:`Document.get_page_pixmap`
getPageText        :meth:`Document.get_page_text`
getSigFlags        :meth:`Document.get_sigflags`
getToC             :meth:`Document.get_toc`
getXmlMetadata     :meth:`Document.get_xml_metadata`
insertPage         :meth:`Document.insert_page`
insertPDF          :meth:`Document.insert_pdf`
isFormPDF          :attr:`Document.is_form_pdf`
isPDF              :attr:`Document.is_pdf`
isStream           :attr:`Document.is_stream`
lastLocation       :attr:`Document.last_location`
loadPage           :meth:`Document.load_page`
makeBookmark       :meth:`Document.make_bookmark`
metadataXML        :meth:`Document.xref_xml_metadata`
newPage            :meth:`Document.new_page`
nextLocation       :meth:`Document.next_location`
pageCount          :attr:`Document.page_count`
pageCropBox        :meth:`Document.page_cropbox`
pageXref           :meth:`Document.page_xref`
PDFCatalog         :meth:`Document.pdf_catalog`
PDFTrailer         :meth:`Document.pdf_trailer`
previousLocation   :meth:`Document.prev_location`
searchPageFor      :meth:`Document.search_page_for`
setMetadata        :meth:`Document.set_metadata`
setToC             :meth:`Document.set_toc`
updateObject       :meth:`Document.update_object`
updateStream       :meth:`Document.update_stream`
xrefLength         :meth:`Document.xref_length`
xrefObject         :meth:`Document.xref_object`
xrefStream         :meth:`Document.xref_stream`
xrefStreamRaw      :meth:`Document.xref_stream_raw`
================== =============================================================

Page and Shape
---------------

======================= ========================================================
Old Name                New Name
======================= ========================================================
_isWrapped              :attr:`Page.is_wrapped`
cleanContents           :meth:`Page.clean_contents`
CropBox                 :attr:`Page.cropbox`
CropBoxPosition         :attr:`Page.cropbox_position`
deleteAnnot             :meth:`Page.delete_annot`
deleteLink              :meth:`Page.delete_link`
derotationMatrix        :attr:`Page.derotation_matrix`
drawBezier              :meth:`Page.draw_bezier`, :meth:`Shape.draw_bezier`
drawCircle              :meth:`Page.draw_circle`, :meth:`Shape.draw_circle`
drawCurve               :meth:`Page.draw_curve`, :meth:`Shape.draw_curve`
drawLine                :meth:`Page.draw_line`, :meth:`Shape.draw_line`
drawOval                :meth:`Page.draw_oval`, :meth:`Shape.draw_oval`
drawPolyline            :meth:`Page.draw_polyline`, :meth:`Shape.draw_polyline`
drawQuad                :meth:`Page.draw_quad`, :meth:`Shape.draw_quad`
drawRect                :meth:`Page.draw_rect`, :meth:`Shape.draw_rect`
drawSector              :meth:`Page.draw_sector`, :meth:`Shape.draw_sector`
drawSquiggle            :meth:`Page.draw_squiggle`, :meth:`Shape.draw_squiggle`
drawZigzag              :meth:`Page.draw_zigzag`, :meth:`Shape.draw_zigzag`
firstAnnot              :attr:`Page.first_annot`
firstLink               :attr:`Page.first_link`
firstWidget             :attr:`Page.first_widget`
getContents             :meth:`Page.get_contents`
getDisplayList          :meth:`Page.get_displaylist`
getDrawings             :meth:`Page.get_drawings`
getFontList             :meth:`Page.get_fonts`
getImageBbox            :meth:`Page.get_image_bbox`
getImageList            :meth:`Page.get_images`
getPixmap               :meth:`Page.get_pixmap`
getSVGimage             :meth:`Page.get_svg_image`
getText                 :meth:`Page.get_text`
getTextBlocks           :meth:`Page.get_text_blocks`
getTextbox              :meth:`Page.get_textbox`
getTextPage             :meth:`Page.get_textpage`
getTextSelection        :meth:`Page.get_text_selection`
getTextWords            :meth:`Page.get_text_words`
insertFont              :meth:`Page.insert_font`
insertImage             :meth:`Page.insert_image`
insertLink              :meth:`Page.insert_link`
insertText              :meth:`Page.insert_text`
insertTextbox           :meth:`Page.insert_textbox`
loadAnnot               :meth:`Page.load_annot`
loadLinks               :meth:`Page.load_links`
MediaBox                :attr:`Page.mediabox`
MediaBoxSize            :attr:`Page.mediabox_size`
newShape                :meth:`Page.new_shape`
rotationMatrix          :attr:`Page.rotation_matrix`
searchFor               :meth:`Page.search_for`
setCropBox              :meth:`Page.set_cropbox`
setMediaBox             :meth:`Page.set_mediabox`
setRotation             :meth:`Page.set_rotation`
showPDFpage             :meth:`Page.show_pdf_page`
transformationMatrix    :attr:`Page.transformation_matrix`
updateLink              :meth:`Page.update_link`
wrapContents            :meth:`Page.wrap_contents`
writeText               :meth:`Page.write_text`
======================= ========================================================


Annot
-----

=============================== ================================================
Old Name                        New Name
=============================== ================================================
getText                         :meth:`Annot.get_text`
getTextbox                      :meth:`Annot.get_textbox`
fileGet                         :meth:`Annot.get_file`
fileUpd                         :meth:`Annot.update_file`
getPixmap                       :meth:`Annot.get_pixmap`
getTextPage                     :meth:`Annot.get_textpage`
lineEnds                        :meth:`Annot.line_ends`
setBlendMode                    :meth:`Annot.set_blendmode`
setBorder                       :meth:`Annot.set_border`
setColors                       :meth:`Annot.set_colors`
setFlags                        :meth:`Annot.set_flags`
setInfo                         :meth:`Annot.set_info`
setLineEnds                     :meth:`Annot.set_line_ends`
setName                         :meth:`Annot.set_name`
setOpacity                      :meth:`Annot.set_opacity`
setRect                         :meth:`Annot.set_rect`
set_rotation                    :meth:`Annot.set_rotation`
soundGet                        :meth:`Annot.get_sound`
=============================== ================================================
