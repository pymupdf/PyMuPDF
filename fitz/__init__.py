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

# copy functions in 'utils' to their respective fitz classes
import fitz.utils

# ------------------------------------------------------------------------------
# Document
# ------------------------------------------------------------------------------
fitz.open = fitz.Document
fitz.Document._do_links = fitz.utils.do_links
fitz.Document.del_toc_item = fitz.utils.del_toc_item
fitz.Document.get_char_widths = fitz.utils.get_char_widths
fitz.Document.get_ocmd = fitz.utils.get_ocmd
fitz.Document.get_page_labels = fitz.utils.get_page_labels
fitz.Document.get_page_numbers = fitz.utils.get_page_numbers
fitz.Document.get_page_pixmap = fitz.utils.get_page_pixmap
fitz.Document.get_page_text = fitz.utils.getPageText
fitz.Document.get_toc = fitz.utils.getToC
fitz.Document.has_annots = fitz.utils.has_annots
fitz.Document.has_links = fitz.utils.has_links
fitz.Document.insert_page = fitz.utils.insertPage
fitz.Document.new_page = fitz.utils.newPage
fitz.Document.scrub = fitz.utils.scrub
fitz.Document.search_page_for = fitz.utils.searchPageFor
fitz.Document.set_metadata = fitz.utils.setMetadata
fitz.Document.set_ocmd = fitz.utils.set_ocmd
fitz.Document.set_page_labels = fitz.utils.set_page_labels
fitz.Document.set_toc = fitz.utils.setToC
fitz.Document.set_toc_item = fitz.utils.set_toc_item
fitz.Document.tobytes = fitz.Document.write
fitz.Document.subset_fonts = fitz.utils.subset_fonts


# ------------------------------------------------------------------------------
# Page
# ------------------------------------------------------------------------------
fitz.Page.apply_redactions = fitz.utils.apply_redactions
fitz.Page.delete_widget = fitz.utils.deleteWidget
fitz.Page.draw_bezier = fitz.utils.draw_bezier
fitz.Page.draw_circle = fitz.utils.draw_circle
fitz.Page.draw_curve = fitz.utils.draw_curve
fitz.Page.draw_line = fitz.utils.draw_line
fitz.Page.draw_oval = fitz.utils.draw_oval
fitz.Page.draw_polyline = fitz.utils.draw_polyline
fitz.Page.draw_quad = fitz.utils.draw_quad
fitz.Page.draw_rect = fitz.utils.draw_rect
fitz.Page.draw_sector = fitz.utils.draw_sector
fitz.Page.draw_squiggle = fitz.utils.draw_squiggle
fitz.Page.draw_zigzag = fitz.utils.draw_zigzag
fitz.Page.get_links = fitz.utils.get_links
fitz.Page.get_pixmap = fitz.utils.get_pixmap
fitz.Page.get_text = fitz.utils.getText
fitz.Page.get_text_blocks = fitz.utils.getTextBlocks
fitz.Page.get_text_selection = fitz.utils.getTextSelection
fitz.Page.get_text_words = fitz.utils.getTextWords
fitz.Page.get_textbox = fitz.utils.getTextbox
fitz.Page.insert_image = fitz.utils.insertImage
fitz.Page.insert_link = fitz.utils.insertLink
fitz.Page.insert_text = fitz.utils.insert_text
fitz.Page.insert_textbox = fitz.utils.insert_textbox
fitz.Page.new_shape = lambda x: fitz.utils.Shape(x)
fitz.Page.search_for = fitz.utils.searchFor
fitz.Page.show_pdf_page = fitz.utils.show_pdf_page
fitz.Page.update_link = fitz.utils.updateLink
fitz.Page.write_text = fitz.utils.write_text
fitz.Page.get_label = fitz.utils.get_label

# ------------------------------------------------------------------------
# Annot
# ------------------------------------------------------------------------
fitz.Annot.get_text = fitz.utils.getText
fitz.Annot.get_textbox = fitz.utils.getTextbox

# ------------------------------------------------------------------------
# Rect
# ------------------------------------------------------------------------
fitz.Rect.getRectArea = fitz.utils.getRectArea
fitz.Rect.getArea = fitz.utils.getRectArea

# ------------------------------------------------------------------------
# IRect
# ------------------------------------------------------------------------

fitz.IRect.getRectArea = fitz.utils.getRectArea
fitz.IRect.getArea = fitz.utils.getRectArea

# ------------------------------------------------------------------------
# TextWriter
# ------------------------------------------------------------------------
fitz.TextWriter.fill_textbox = fitz.utils.fillTextbox


def restore_aliases():
    # deprecated Document aliases
    fitz.Document.chapterCount = fitz.Document.chapter_count
    fitz.Document.chapterPageCount = fitz.Document.chapter_page_count
    fitz.Document.convertToPDF = fitz.Document.convert_to_pdf
    fitz.Document.copyPage = fitz.Document.copy_page
    fitz.Document.deletePage = fitz.Document.delete_page
    fitz.Document.deletePageRange = fitz.Document.delete_pages
    fitz.Document.embeddedFileAdd = fitz.Document.embfile_add
    fitz.Document.embeddedFileCount = fitz.Document.embfile_count
    fitz.Document.embeddedFileDel = fitz.Document.embfile_del
    fitz.Document.embeddedFileGet = fitz.Document.embfile_get
    fitz.Document.embeddedFileInfo = fitz.Document.embfile_info
    fitz.Document.embeddedFileNames = fitz.Document.embfile_names
    fitz.Document.embeddedFileUpd = fitz.Document.embfile_upd
    fitz.Document.extractFont = fitz.Document.extract_font
    fitz.Document.extractImage = fitz.Document.extract_image
    fitz.Document.findBookmark = fitz.Document.find_bookmark
    fitz.Document.fullcopyPage = fitz.Document.fullcopy_page
    fitz.Document.getCharWidths = fitz.Document.get_char_widths
    fitz.Document.getOCGs = fitz.Document.get_ocgs
    fitz.Document.getPageFontList = fitz.Document.get_page_fonts
    fitz.Document.getPageImageList = fitz.Document.get_page_images
    fitz.Document.getPagePixmap = fitz.Document.get_page_pixmap
    fitz.Document.getPageText = fitz.Document.get_page_text
    fitz.Document.getPageXObjectList = fitz.Document.get_page_xobjects
    fitz.Document.getSigFlags = fitz.Document.get_sigflags
    fitz.Document.getToC = fitz.Document.get_toc
    fitz.Document.getXmlMetadata = fitz.Document.get_xml_metadata
    fitz.Document.insertPage = fitz.Document.insert_page
    fitz.Document.insertPDF = fitz.Document.insert_pdf
    fitz.Document.isDirty = fitz.Document.is_dirty
    fitz.Document.isFormPDF = fitz.Document.is_form_pdf
    fitz.Document.isPDF = fitz.Document.is_pdf
    fitz.Document.isReflowable = fitz.Document.is_reflowable
    fitz.Document.isRepaired = fitz.Document.is_repaired
    fitz.Document.isStream = fitz.Document.is_stream
    fitz.Document.lastLocation = fitz.Document.last_location
    fitz.Document.loadPage = fitz.Document.load_page
    fitz.Document.makeBookmark = fitz.Document.make_bookmark
    fitz.Document.metadataXML = fitz.Document.xref_xml_metadata
    fitz.Document.movePage = fitz.Document.move_page
    fitz.Document.needsPass = fitz.Document.needs_pass
    fitz.Document.newPage = fitz.Document.new_page
    fitz.Document.nextLocation = fitz.Document.next_location
    fitz.Document.pageCount = fitz.Document.page_count
    fitz.Document.pageCropBox = fitz.Document.page_cropbox
    fitz.Document.pageXref = fitz.Document.page_xref
    fitz.Document.PDFCatalog = fitz.Document.pdf_catalog
    fitz.Document.PDFTrailer = fitz.Document.pdf_trailer
    fitz.Document.previousLocation = fitz.Document.prev_location
    fitz.Document.resolveLink = fitz.Document.resolve_link
    fitz.Document.searchPageFor = fitz.Document.search_page_for
    fitz.Document.setLanguage = fitz.Document.set_language
    fitz.Document.setMetadata = fitz.Document.set_metadata
    fitz.Document.setToC = fitz.Document.set_toc
    fitz.Document.setXmlMetadata = fitz.Document.set_xml_metadata
    fitz.Document.updateObject = fitz.Document.update_object
    fitz.Document.updateStream = fitz.Document.update_stream
    fitz.Document.xrefLength = fitz.Document.xref_length
    fitz.Document.xrefObject = fitz.Document.xref_object
    fitz.Document.xrefStream = fitz.Document.xref_stream
    fitz.Document.xrefStreamRaw = fitz.Document.xref_stream_raw

    # deprecated Page aliases
    fitz.Page._isWrapped = fitz.Page.is_wrapped
    fitz.Page.cleanContents = fitz.Page.clean_contents
    fitz.Page.CropBox = fitz.Page.cropbox
    fitz.Page.CropBoxPosition = fitz.Page.cropbox_position
    fitz.Page.deleteAnnot = fitz.Page.delete_annot
    fitz.Page.deleteLink = fitz.Page.delete_link
    fitz.Page.deleteWidget = fitz.Page.delete_widget
    fitz.Page.derotationMatrix = fitz.Page.derotation_matrix
    fitz.Page.drawBezier = fitz.Page.draw_bezier
    fitz.Page.drawCircle = fitz.Page.draw_circle
    fitz.Page.drawCurve = fitz.Page.draw_curve
    fitz.Page.drawLine = fitz.Page.draw_line
    fitz.Page.drawOval = fitz.Page.draw_oval
    fitz.Page.drawPolyline = fitz.Page.draw_polyline
    fitz.Page.drawQuad = fitz.Page.draw_quad
    fitz.Page.drawRect = fitz.Page.draw_rect
    fitz.Page.drawSector = fitz.Page.draw_sector
    fitz.Page.drawSquiggle = fitz.Page.draw_squiggle
    fitz.Page.drawZigzag = fitz.Page.draw_zigzag
    fitz.Page.firstAnnot = fitz.Page.first_annot
    fitz.Page.firstLink = fitz.Page.first_link
    fitz.Page.firstWidget = fitz.Page.first_widget
    fitz.Page.getContents = fitz.Page.get_contents
    fitz.Page.getDisplayList = fitz.Page.get_displaylist
    fitz.Page.getDrawings = fitz.Page.get_drawings
    fitz.Page.getFontList = fitz.Page.get_fonts
    fitz.Page.getImageBbox = fitz.Page.get_image_bbox
    fitz.Page.getImageList = fitz.Page.get_images
    fitz.Page.getLinks = fitz.Page.get_links
    fitz.Page.getPixmap = fitz.Page.get_pixmap
    fitz.Page.getSVGimage = fitz.Page.get_svg_image
    fitz.Page.getText = fitz.Page.get_text
    fitz.Page.getTextBlocks = fitz.Page.get_text_blocks
    fitz.Page.getTextbox = fitz.Page.get_textbox
    fitz.Page.getTextPage = fitz.Page.get_textpage
    fitz.Page.getTextWords = fitz.Page.get_text_words
    fitz.Page.insertFont = fitz.Page.insert_font
    fitz.Page.insertImage = fitz.Page.insert_image
    fitz.Page.insertLink = fitz.Page.insert_link
    fitz.Page.insertText = fitz.Page.insert_text
    fitz.Page.insertTextbox = fitz.Page.insert_textbox
    fitz.Page.loadAnnot = fitz.Page.load_annot
    fitz.Page.loadLinks = fitz.Page.load_links
    fitz.Page.MediaBox = fitz.Page.mediabox
    fitz.Page.MediaBoxSize = fitz.Page.mediabox_size
    fitz.Page.newShape = fitz.Page.new_shape
    fitz.Page.readContents = fitz.Page.read_contents
    fitz.Page.rotationMatrix = fitz.Page.rotation_matrix
    fitz.Page.searchFor = fitz.Page.search_for
    fitz.Page.setCropBox = fitz.Page.set_cropbox
    fitz.Page.setMediaBox = fitz.Page.set_mediabox
    fitz.Page.setRotation = fitz.Page.set_rotation
    fitz.Page.showPDFpage = fitz.Page.show_pdf_page
    fitz.Page.transformationMatrix = fitz.Page.transformation_matrix
    fitz.Page.updateLink = fitz.Page.update_link
    fitz.Page.wrapContents = fitz.Page.wrap_contents
    fitz.Page.writeText = fitz.Page.write_text

    # deprecated Annot aliases
    fitz.Annot.getText = fitz.Annot.get_text
    fitz.Annot.getTextbox = fitz.Annot.get_textbox
    fitz.Annot.fileGet = fitz.Annot.get_file
    fitz.Annot.fileUpd = fitz.Annot.update_file
    fitz.Annot.getPixmap = fitz.Annot.get_pixmap
    fitz.Annot.getTextPage = fitz.Annot.get_textpage
    fitz.Annot.lineEnds = fitz.Annot.line_ends
    fitz.Annot.setBlendMode = fitz.Annot.set_blendmode
    fitz.Annot.setBorder = fitz.Annot.set_border
    fitz.Annot.setColors = fitz.Annot.set_colors
    fitz.Annot.setFlags = fitz.Annot.set_flags
    fitz.Annot.setInfo = fitz.Annot.set_info
    fitz.Annot.setLineEnds = fitz.Annot.set_line_ends
    fitz.Annot.setName = fitz.Annot.set_name
    fitz.Annot.setOpacity = fitz.Annot.set_opacity
    fitz.Annot.setRect = fitz.Annot.set_rect
    fitz.Annot.setOC = fitz.Annot.set_oc
    fitz.Annot.soundGet = fitz.Annot.get_sound

    # deprecated TextWriter aliases
    fitz.TextWriter.writeText = fitz.TextWriter.write_text
    fitz.TextWriter.fillTextbox = fitz.TextWriter.fill_textbox


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

restore_aliases()
