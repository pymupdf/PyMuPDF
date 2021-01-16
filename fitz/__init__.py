import sys
from fitz.fitz import *

# define the supported colorspaces for convenience
fitz.csRGB = fitz.Colorspace(fitz.CS_RGB)
fitz.csGRAY = fitz.Colorspace(fitz.CS_GRAY)
fitz.csCMYK = fitz.Colorspace(fitz.CS_CMYK)
csRGB = fitz.csRGB
csGRAY = fitz.csGRAY
csCMYK = fitz.csCMYK

# create the TOOLS object
TOOLS = fitz.Tools()
fitz.TOOLS = TOOLS

if fitz.VersionFitz != fitz.TOOLS.mupdf_version():
    v1 = fitz.VersionFitz.split(".")
    v2 = fitz.TOOLS.mupdf_version().split(".")
    if v1[:-1] != v2[:-1]:
        raise ValueError(
            "MuPDF library mismatch %s <> %s"
            % (fitz.VersionFitz, fitz.TOOLS.mupdf_version())
        )

# copy functions to their respective fitz classes
import fitz.utils

# ------------------------------------------------------------------------------
# Document
# ------------------------------------------------------------------------------
fitz.open = fitz.Document
fitz.Document._do_links = fitz.utils.do_links
fitz.Document.del_toc_item = fitz.utils.del_toc_item
fitz.Document.get_char_widths = fitz.utils.getCharWidths
fitz.Document.get_ocmd = fitz.utils.get_ocmd
fitz.Document.get_page_pixmap = fitz.utils.getPagePixmap
fitz.Document.get_page_text = fitz.utils.getPageText
fitz.Document.get_toc = fitz.utils.getToC
fitz.Document.getCharWidths = fitz.utils.getCharWidths
fitz.Document.getPagePixmap = fitz.utils.getPagePixmap
fitz.Document.getPageText = fitz.utils.getPageText
fitz.Document.getToC = fitz.utils.getToC
fitz.Document.insert_page = fitz.utils.insertPage
fitz.Document.insertPage = fitz.utils.insertPage
fitz.Document.new_page = fitz.utils.newPage
fitz.Document.newPage = fitz.utils.newPage
fitz.Document.scrub = fitz.utils.scrub
fitz.Document.search_page_for = fitz.utils.searchPageFor
fitz.Document.searchPageFor = fitz.utils.searchPageFor
fitz.Document.set_metadata = fitz.utils.setMetadata
fitz.Document.set_ocmd = fitz.utils.set_ocmd
fitz.Document.set_toc = fitz.utils.setToC
fitz.Document.set_toc_item = fitz.utils.set_toc_item
fitz.Document.setMetadata = fitz.utils.setMetadata
fitz.Document.setToC = fitz.utils.setToC
fitz.Document.tobytes = fitz.Document.write
fitz.Document.set_page_labels = fitz.utils.set_page_labels
fitz.Document.get_page_numbers = fitz.utils.get_page_numbers

# ------------------------------------------------------------------------------
# Page
# ------------------------------------------------------------------------------
fitz.Page.apply_redactions = fitz.utils.apply_redactions
fitz.Page.delete_widget = fitz.utils.deleteWidget
fitz.Page.deleteWidget = fitz.utils.deleteWidget
fitz.Page.draw_bezier = fitz.utils.drawBezier
fitz.Page.draw_circle = fitz.utils.drawCircle
fitz.Page.draw_curve = fitz.utils.drawCurve
fitz.Page.draw_line = fitz.utils.drawLine
fitz.Page.draw_oval = fitz.utils.drawOval
fitz.Page.draw_polyline = fitz.utils.drawPolyline
fitz.Page.draw_quad = fitz.utils.drawQuad
fitz.Page.draw_rect = fitz.utils.drawRect
fitz.Page.draw_sector = fitz.utils.drawSector
fitz.Page.draw_squiggle = fitz.utils.drawSquiggle
fitz.Page.draw_zigzag = fitz.utils.drawZigzag
fitz.Page.drawBezier = fitz.utils.drawBezier
fitz.Page.drawCircle = fitz.utils.drawCircle
fitz.Page.drawCurve = fitz.utils.drawCurve
fitz.Page.drawLine = fitz.utils.drawLine
fitz.Page.drawOval = fitz.utils.drawOval
fitz.Page.drawPolyline = fitz.utils.drawPolyline
fitz.Page.drawQuad = fitz.utils.drawQuad
fitz.Page.drawRect = fitz.utils.drawRect
fitz.Page.drawSector = fitz.utils.drawSector
fitz.Page.drawSquiggle = fitz.utils.drawSquiggle
fitz.Page.drawZigzag = fitz.utils.drawZigzag
fitz.Page.get_links = fitz.utils.getLinks
fitz.Page.get_pixmap = fitz.utils.getPixmap
fitz.Page.get_text = fitz.utils.getText
fitz.Page.get_text_blocks = fitz.utils.getTextBlocks
fitz.Page.get_text_selection = fitz.utils.getTextSelection
fitz.Page.get_text_words = fitz.utils.getTextWords
fitz.Page.get_textbox = fitz.utils.getTextbox
fitz.Page.getLinks = fitz.utils.getLinks
fitz.Page.getPixmap = fitz.utils.getPixmap
fitz.Page.getText = fitz.utils.getText
fitz.Page.getTextBlocks = fitz.utils.getTextBlocks
fitz.Page.getTextbox = fitz.utils.getTextbox
fitz.Page.getTextSelection = fitz.utils.getTextSelection
fitz.Page.getTextWords = fitz.utils.getTextWords
fitz.Page.insert_image = fitz.utils.insertImage
fitz.Page.insert_link = fitz.utils.insertLink
fitz.Page.insert_text = fitz.utils.insertText
fitz.Page.insert_textbox = fitz.utils.insertTextbox
fitz.Page.insertImage = fitz.utils.insertImage
fitz.Page.insertLink = fitz.utils.insertLink
fitz.Page.insertText = fitz.utils.insertText
fitz.Page.insertTextbox = fitz.utils.insertTextbox
fitz.Page.new_shape = lambda x: fitz.utils.Shape(x)
fitz.Page.newShape = lambda x: fitz.utils.Shape(x)
fitz.Page.search = fitz.utils.searchFor
fitz.Page.searchFor = fitz.utils.searchFor
fitz.Page.show_pdf_page = fitz.utils.showPDFpage
fitz.Page.showPDFpage = fitz.utils.showPDFpage
fitz.Page.updateLink = fitz.utils.updateLink
fitz.Page.updte_link = fitz.utils.updateLink
fitz.Page.write_text = fitz.utils.writeText
fitz.Page.writeText = fitz.utils.writeText
fitz.Page.get_label = fitz.utils.get_label

# ------------------------------------------------------------------------------
# Annot
# ------------------------------------------------------------------------------
fitz.Annot.getText = fitz.utils.getText
fitz.Annot.getTextbox = fitz.utils.getTextbox
# ------------------------------------------------------------------------------
# Rect
# ------------------------------------------------------------------------------
fitz.Rect.getRectArea = fitz.utils.getRectArea
fitz.Rect.getArea = fitz.utils.getRectArea

# ------------------------------------------------------------------------------
# IRect
# ------------------------------------------------------------------------------
fitz.IRect.getRectArea = fitz.utils.getRectArea
fitz.IRect.getArea = fitz.utils.getRectArea

# ------------------------------------------------------------------------------
# IRect
# ------------------------------------------------------------------------------
fitz.TextWriter.fillTextbox = fitz.utils.fillTextbox


fitz.Matrix.is_rectilinear = fitz.Matrix.isRectilinear # property
fitz.Matrix.pre_rotate = fitz.Matrix.preRotate
fitz.Matrix.pre_scale = fitz.Matrix.preScale
fitz.Matrix.pre_shear = fitz.Matrix.preShear
fitz.Matrix.pre_translate = fitz.Matrix.preTranslate
fitz.IdentityMatrix.is_rectilinear = fitz.IdentityMatrix.isRectilinear # property
fitz.IdentityMatrix.pre_rotate = fitz.IdentityMatrix.preRotate
fitz.IdentityMatrix.pre_scale = fitz.IdentityMatrix.preScale
fitz.IdentityMatrix.pre_shear = fitz.IdentityMatrix.preShear
fitz.IdentityMatrix.pre_translate = fitz.IdentityMatrix.preTranslate
fitz.Rect.get_area = fitz.Rect.getArea
fitz.Rect.get_rect_area = fitz.Rect.getRectArea
fitz.Rect.include_point = fitz.Rect.includePoint
fitz.Rect.include_rect = fitz.Rect.includeRect
fitz.Rect.is_empty = fitz.Rect.isEmpty # property
fitz.Rect.is_infinite = fitz.Rect.isInfinite # property
fitz.IRect.get_area = fitz.IRect.getArea
fitz.IRect.get_rect_area = fitz.IRect.getRectArea
fitz.IRect.include_point = fitz.IRect.includePoint
fitz.IRect.include_rect = fitz.IRect.includeRect
fitz.IRect.is_empty = fitz.IRect.isEmpty # property
fitz.IRect.is_infinite = fitz.IRect.isInfinite # property
fitz.Quad.is_convex = fitz.Quad.isConvex # property
fitz.Quad.is_empty = fitz.Quad.isEmpty # property
fitz.Quad.is_rectangular = fitz.Quad.isRectangular # property
fitz.Document.form_fonts = fitz.Document.FormFonts # property
fitz.Document._add_form_font = fitz.Document._addFormFont
fitz.Document._del_to_c = fitz.Document._delToC
fitz.Document._delete_object = fitz.Document._deleteObject
fitz.Document._delete_page = fitz.Document._deletePage
fitz.Document._drop_outline = fitz.Document._dropOutline
fitz.Document._embedded_file_add = fitz.Document._embeddedFileAdd
fitz.Document._embedded_file_del = fitz.Document._embeddedFileDel
fitz.Document._embedded_file_get = fitz.Document._embeddedFileGet
fitz.Document._embedded_file_index = fitz.Document._embeddedFileIndex
fitz.Document._embedded_file_info = fitz.Document._embeddedFileInfo
fitz.Document._embedded_file_names = fitz.Document._embeddedFileNames
fitz.Document._embedded_file_upd = fitz.Document._embeddedFileUpd
fitz.Document._get_char_widths = fitz.Document._getCharWidths
fitz.Document._get_metadata = fitz.Document._getMetadata
fitz.Document._get_ol_root_number = fitz.Document._getOLRootNumber
fitz.Document._get_pdf_fileid = fitz.Document._getPDFfileid
fitz.Document._get_page_info = fitz.Document._getPageInfo
fitz.Document._get_page_xref = fitz.Document._getPageXref
fitz.Document._has_xref_old_style = fitz.Document._hasXrefOldStyle # property
fitz.Document._has_xref_stream = fitz.Document._hasXrefStream # property
fitz.Document._load_outline = fitz.Document._loadOutline
fitz.Document._new_page = fitz.Document._newPage
fitz.Document._set_metadata = fitz.Document._setMetadata
fitz.Document.chapter_count = fitz.Document.chapterCount # property
fitz.Document.chapter_page_count = fitz.Document.chapterPageCount
fitz.Document.convert_to_pdf = fitz.Document.convertToPDF
fitz.Document.copy_page = fitz.Document.copyPage
fitz.Document.delete_page = fitz.Document.deletePage
fitz.Document.delete_page_range = fitz.Document.deletePageRange
fitz.Document.embedded_file_add = fitz.Document.embeddedFileAdd
fitz.Document.embedded_file_count = fitz.Document.embeddedFileCount
fitz.Document.embedded_file_del = fitz.Document.embeddedFileDel
fitz.Document.embedded_file_get = fitz.Document.embeddedFileGet
fitz.Document.embedded_file_info = fitz.Document.embeddedFileInfo
fitz.Document.embedded_file_names = fitz.Document.embeddedFileNames
fitz.Document.embedded_file_upd = fitz.Document.embeddedFileUpd
fitz.Document.extract_font = fitz.Document.extractFont
fitz.Document.extract_image = fitz.Document.extractImage
fitz.Document.find_bookmark = fitz.Document.findBookmark
fitz.Document.fullcopy_page = fitz.Document.fullcopyPage
fitz.Document.get_page_font_list = fitz.Document.getPageFontList
fitz.Document.get_page_image_list = fitz.Document.getPageImageList
fitz.Document.get_page_xobject_list = fitz.Document.getPageXObjectList
fitz.Document.get_sig_flags = fitz.Document.getSigFlags
fitz.Document.get_to_c = fitz.Document.getToC
fitz.Document.get_xml_metadata = fitz.Document.getXmlMetadata
fitz.Document.init_data = fitz.Document.initData
fitz.Document.insert_pdf = fitz.Document.insertPDF
fitz.Document.is_dirty = fitz.Document.isDirty # property
fitz.Document.is_form_pdf = fitz.Document.isFormPDF # property
fitz.Document.is_pdf = fitz.Document.isPDF # property
fitz.Document.is_reflowable = fitz.Document.isReflowable # property
fitz.Document.is_repaired = fitz.Document.isRepaired # property
fitz.Document.is_stream = fitz.Document.isStream
fitz.Document.last_location = fitz.Document.lastLocation # property
fitz.Document.load_page = fitz.Document.loadPage
fitz.Document.make_bookmark = fitz.Document.makeBookmark
fitz.Document.metadata_xml = fitz.Document.metadataXML
fitz.Document.move_page = fitz.Document.movePage
fitz.Document.needs_pass = fitz.Document.needsPass # property
fitz.Document.next_location = fitz.Document.nextLocation
fitz.Document.page_count = fitz.Document.pageCount # property
fitz.Document.page_crop_box = fitz.Document.pageCropBox
fitz.Document.previous_location = fitz.Document.previousLocation
fitz.Document.resolve_link = fitz.Document.resolveLink
fitz.Document.save_incr = fitz.Document.saveIncr
fitz.Document.set_language = fitz.Document.setLanguage
fitz.Document.set_to_c = fitz.Document.setToC
fitz.Page.crop_box_position = fitz.Page.CropBoxPosition # property
fitz.Page.media_box = fitz.Page.MediaBox # property
fitz.Page.media_box_size = fitz.Page.MediaBoxSize # property
fitz.Page._add_annot_from_string = fitz.Page._addAnnot_FromString
fitz.Page._add_widget = fitz.Page._addWidget
fitz.Page._get_drawings = fitz.Page._getDrawings
fitz.Page._insert_font = fitz.Page._insertFont
fitz.Page._insert_image = fitz.Page._insertImage
fitz.Page._is_wrapped = fitz.Page._isWrapped # property
fitz.Page._make_pixmap = fitz.Page._makePixmap
fitz.Page._show_pdf_page = fitz.Page._showPDFpage
fitz.Page.add_caret_annot = fitz.Page.addCaretAnnot
fitz.Page.add_circle_annot = fitz.Page.addCircleAnnot
fitz.Page.add_file_annot = fitz.Page.addFileAnnot
fitz.Page.add_freetext_annot = fitz.Page.addFreetextAnnot
fitz.Page.add_highlight_annot = fitz.Page.addHighlightAnnot
fitz.Page.add_ink_annot = fitz.Page.addInkAnnot
fitz.Page.add_line_annot = fitz.Page.addLineAnnot
fitz.Page.add_polygon_annot = fitz.Page.addPolygonAnnot
fitz.Page.add_polyline_annot = fitz.Page.addPolylineAnnot
fitz.Page.add_rect_annot = fitz.Page.addRectAnnot
fitz.Page.add_redact_annot = fitz.Page.addRedactAnnot
fitz.Page.add_squiggly_annot = fitz.Page.addSquigglyAnnot
fitz.Page.add_stamp_annot = fitz.Page.addStampAnnot
fitz.Page.add_strikeout_annot = fitz.Page.addStrikeoutAnnot
fitz.Page.add_text_annot = fitz.Page.addTextAnnot
fitz.Page.add_underline_annot = fitz.Page.addUnderlineAnnot
fitz.Page.add_widget = fitz.Page.addWidget
fitz.Page.delete_annot = fitz.Page.deleteAnnot
fitz.Page.delete_link = fitz.Page.deleteLink
fitz.Page.derotation_matrix = fitz.Page.derotationMatrix # property
fitz.Page.first_annot = fitz.Page.firstAnnot # property
fitz.Page.first_link = fitz.Page.firstLink # property
fitz.Page.first_widget = fitz.Page.firstWidget # property
fitz.Page.get_display_list = fitz.Page.getDisplayList
fitz.Page.get_drawings = fitz.Page.getDrawings
fitz.Page.get_font_list = fitz.Page.getFontList
fitz.Page.get_image_bbox = fitz.Page.getImageBbox
fitz.Page.get_image_list = fitz.Page.getImageList
fitz.Page.get_svgimage = fitz.Page.getSVGimage
fitz.Page.get_text_page = fitz.Page.getTextPage
fitz.Page.insert_font = fitz.Page.insertFont
fitz.Page.load_links = fitz.Page.loadLinks
fitz.Page.rotation_matrix = fitz.Page.rotationMatrix # property
fitz.Page.search_for = fitz.Page.searchFor
fitz.Page.set_crop_box = fitz.Page.setCropBox
fitz.Page.set_language = fitz.Page.setLanguage
fitz.Page.set_media_box = fitz.Page.setMediaBox
fitz.Page.set_rotation = fitz.Page.setRotation
fitz.Page.transformation_matrix = fitz.Page.transformationMatrix # property
fitz.Page.update_link = fitz.Page.updateLink
fitz.Pixmap._get_image_data = fitz.Pixmap._getImageData
fitz.Pixmap._write_img = fitz.Pixmap._writeIMG
fitz.Pixmap.clear_with = fitz.Pixmap.clearWith
fitz.Pixmap.copy_pixmap = fitz.Pixmap.copyPixmap
fitz.Pixmap.get_image_data = fitz.Pixmap.getImageData
fitz.Pixmap.get_png_data = fitz.Pixmap.getPNGData
fitz.Pixmap.get_png_data = fitz.Pixmap.getPNGdata
fitz.Pixmap.invert_irect = fitz.Pixmap.invertIRect
fitz.Pixmap.pillow_data = fitz.Pixmap.pillowData
fitz.Pixmap.pillow_write = fitz.Pixmap.pillowWrite
fitz.Pixmap.set_alpha = fitz.Pixmap.setAlpha
fitz.Pixmap.set_origin = fitz.Pixmap.setOrigin
fitz.Pixmap.set_pixel = fitz.Pixmap.setPixel
fitz.Pixmap.set_rect = fitz.Pixmap.setRect
fitz.Pixmap.set_resolution = fitz.Pixmap.setResolution
fitz.Pixmap.tint_with = fitz.Pixmap.tintWith
fitz.Pixmap.write_image = fitz.Pixmap.writeImage
fitz.Pixmap.write_png = fitz.Pixmap.writePNG
fitz.Outline.is_external = fitz.Outline.isExternal # property
fitz.Annot._get_ap = fitz.Annot._getAP
fitz.Annot._set_ap = fitz.Annot._setAP
fitz.Annot.blend_mode = fitz.Annot.blendMode
fitz.Annot.file_get = fitz.Annot.fileGet
fitz.Annot.file_upd = fitz.Annot.fileUpd
fitz.Annot.get_text = fitz.Annot.getText
fitz.Annot.get_text_page = fitz.Annot.getTextPage
fitz.Annot.get_textbox = fitz.Annot.getTextbox
fitz.Annot.set_blend_mode = fitz.Annot.setBlendMode
fitz.Annot.sound_get = fitz.Annot.soundGet
fitz.Link._set_border = fitz.Link._setBorder
fitz.Link._set_colors = fitz.Link._setColors
fitz.Link.is_external = fitz.Link.isExternal # property
fitz.Link.set_border = fitz.Link.setBorder
fitz.Link.set_colors = fitz.Link.setColors
fitz.DisplayList.get_pixmap = fitz.DisplayList.getPixmap
fitz.DisplayList.get_text_page = fitz.DisplayList.getTextPage
fitz.TextPage._extract_text = fitz.TextPage._extractText
fitz.TextPage._get_new_block_list = fitz.TextPage._getNewBlockList
fitz.TextPage.extract_blocks = fitz.TextPage.extractBLOCKS
fitz.TextPage.extract_dict = fitz.TextPage.extractDICT
fitz.TextPage.extract_html = fitz.TextPage.extractHTML
fitz.TextPage.extract_json = fitz.TextPage.extractJSON
fitz.TextPage.extract_rawdict = fitz.TextPage.extractRAWDICT
fitz.TextPage.extract_rawjson = fitz.TextPage.extractRAWJSON
fitz.TextPage.extract_selection = fitz.TextPage.extractSelection
fitz.TextPage.extract_text = fitz.TextPage.extractText
fitz.TextPage.extract_words = fitz.TextPage.extractWORDS
fitz.TextPage.extract_xhtml = fitz.TextPage.extractXHTML
fitz.TextPage.extract_xml = fitz.TextPage.extractXML
fitz.TextWriter.fill_textbox = fitz.TextWriter.fillTextbox
fitz.TextWriter.write_text = fitz.TextWriter.writeText
fitz.Font.is_writable = fitz.Font.isWritable # property


fitz.__doc__ = """
PyMuPDF %s: Python bindings for the MuPDF %s library.
Version date: %s.
Built for Python %i.%i on %s (%i-bit).
""" % (
    fitz.VersionBind,
    fitz.VersionFitz,
    fitz.VersionDate,
    sys.version_info[0],
    sys.version_info[1],
    sys.platform,
    64 if sys.maxsize > 2 ** 32 else 32,
)
