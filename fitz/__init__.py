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
fitz.Document.get_page_labels = fitz.utils.get_page_labels
fitz.Document.get_page_numbers = fitz.utils.get_page_numbers
fitz.Document.get_page_pixmap = fitz.utils.getPagePixmap
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
# deprecated Document aliases --------------------------------------------
fitz.Document.getCharWidths = fitz.utils.getCharWidths
fitz.Document.getPagePixmap = fitz.utils.getPagePixmap
fitz.Document.getPageText = fitz.utils.getPageText
fitz.Document.getSigFlags = fitz.Document.get_sigflags
fitz.Document.getToC = fitz.utils.getToC
fitz.Document.insertPage = fitz.utils.insertPage
fitz.Document.insertPDF = fitz.Document.insert_pdf
fitz.Document.isFormPDF = fitz.Document.is_form_pdf
fitz.Document.isPDF = fitz.Document.is_pdf
fitz.Document.isStream = fitz.Document.is_stream
fitz.Document.metadataXML = fitz.Document.xref_xml_metadata
fitz.Document.newPage = fitz.utils.newPage
fitz.Document.pageXref = fitz.Document.page_xref
fitz.Document.PDFCatalog = fitz.Document.pdf_catalog
fitz.Document.PDFTrailer = fitz.Document.pdf_trailer
fitz.Document.searchPageFor = fitz.utils.searchPageFor
fitz.Document.setMetadata = fitz.utils.setMetadata
fitz.Document.setToC = fitz.utils.setToC
fitz.Document.updateObject = fitz.Document.update_object
fitz.Document.updateStream = fitz.Document.update_stream
fitz.Document.xrefLength = fitz.Document.xref_length
fitz.Document.xrefObject = fitz.Document.xref_object
fitz.Document.xrefStream = fitz.Document.xref_stream
fitz.Document.xrefStreamRaw = fitz.Document.xref_stream_raw


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
fitz.Page.get_links = fitz.utils.getLinks
fitz.Page.get_pixmap = fitz.utils.getPixmap
fitz.Page.get_text = fitz.utils.getText
fitz.Page.get_text_blocks = fitz.utils.getTextBlocks
fitz.Page.get_text_selection = fitz.utils.getTextSelection
fitz.Page.get_text_words = fitz.utils.getTextWords
fitz.Page.get_textbox = fitz.utils.getTextbox
fitz.Page.getLinks = fitz.utils.getLinks
fitz.Page.insert_image = fitz.utils.insertImage
fitz.Page.insert_link = fitz.utils.insertLink
fitz.Page.insert_text = fitz.utils.insertText
fitz.Page.insert_textbox = fitz.utils.insertTextbox
fitz.Page.new_shape = lambda x: fitz.utils.Shape(x)
fitz.Page.search = fitz.utils.searchFor
fitz.Page.show_pdf_page = fitz.utils.show_pdf_page
fitz.Page.update_link = fitz.utils.updateLink
fitz.Page.write_text = fitz.utils.write_text
fitz.Page.get_label = fitz.utils.get_label
# deprecated Page aliases ------------------------------------------------
fitz.Page.writeText = fitz.utils.write_text
fitz.Page._isWrapped = fitz.Page.is_wrapped
fitz.Page.wrapContents = fitz.Page.wrap_contents
fitz.Page.updateLink = fitz.utils.updateLink
fitz.Page.showPDFpage = fitz.utils.show_pdf_page
fitz.Page.newShape = lambda x: fitz.utils.Shape(x)
fitz.Page.insertLink = fitz.utils.insertLink
fitz.Page.insertText = fitz.utils.insertText
fitz.Page.insertTextbox = fitz.utils.insertTextbox
fitz.Page.insertImage = fitz.utils.insertImage
fitz.Page.getPixmap = fitz.utils.getPixmap
fitz.Page.getText = fitz.utils.getText
fitz.Page.getTextBlocks = fitz.utils.getTextBlocks
fitz.Page.getTextbox = fitz.utils.getTextbox
fitz.Page.getTextSelection = fitz.utils.getTextSelection
fitz.Page.getTextWords = fitz.utils.getTextWords
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
fitz.Page.searchFor = fitz.utils.searchFor


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
# TextWriter
# ------------------------------------------------------------------------------
fitz.TextWriter.fillTextbox = fitz.utils.fillTextbox
fitz.TextWriter.fill_textbox = fitz.utils.fillTextbox
fitz.TextWriter.writeText = fitz.TextWriter.write_text


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
