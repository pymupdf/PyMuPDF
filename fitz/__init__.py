from __future__ import absolute_import, print_function
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
fitz.Document.getToC = fitz.utils.getToC
fitz.Document.get_toc = fitz.utils.getToC
fitz.Document.setToC = fitz.utils.setToC
fitz.Document.set_toc = fitz.utils.setToC
fitz.Document.set_toc_item = fitz.utils.setTOC_item
fitz.Document.del_toc_item = fitz.utils.delTOC_item
fitz.Document._do_links = fitz.utils.do_links
fitz.Document.getPagePixmap = fitz.utils.getPagePixmap
fitz.Document.get_page_pixmap = fitz.utils.getPagePixmap
fitz.Document.getPageText = fitz.utils.getPageText
fitz.Document.get_page_text = fitz.utils.getPageText
fitz.Document.setMetadata = fitz.utils.setMetadata
fitz.Document.set_metadata = fitz.utils.setMetadata
fitz.Document.searchPageFor = fitz.utils.searchPageFor
fitz.Document.search_page_for = fitz.utils.searchPageFor
fitz.Document.newPage = fitz.utils.newPage
fitz.Document.new_page = fitz.utils.newPage
fitz.Document.insertPage = fitz.utils.insertPage
fitz.Document.insert_page = fitz.utils.insertPage
fitz.Document.getCharWidths = fitz.utils.getCharWidths
fitz.Document.get_char_widths = fitz.utils.getCharWidths
fitz.Document.scrub = fitz.utils.scrub
fitz.Document.set_ocmd = fitz.utils.set_ocmd
fitz.Document.get_ocmd = fitz.utils.get_ocmd

# ------------------------------------------------------------------------------
# Page
# ------------------------------------------------------------------------------
fitz.Page.apply_redactions = fitz.utils.apply_redactions
fitz.Page.deleteWidget = fitz.utils.deleteWidget
fitz.Page.delete_widget = fitz.utils.deleteWidget
fitz.Page.drawBezier = fitz.utils.drawBezier
fitz.Page.draw_bezier = fitz.utils.drawBezier
fitz.Page.drawCircle = fitz.utils.drawCircle
fitz.Page.draw_circle = fitz.utils.drawCircle
fitz.Page.drawCurve = fitz.utils.drawCurve
fitz.Page.draw_curve = fitz.utils.drawCurve
fitz.Page.drawLine = fitz.utils.drawLine
fitz.Page.draw_line = fitz.utils.drawLine
fitz.Page.drawOval = fitz.utils.drawOval
fitz.Page.draw_oval = fitz.utils.drawOval
fitz.Page.drawPolyline = fitz.utils.drawPolyline
fitz.Page.draw_polyline = fitz.utils.drawPolyline
fitz.Page.drawQuad = fitz.utils.drawQuad
fitz.Page.draw_quad = fitz.utils.drawQuad
fitz.Page.drawRect = fitz.utils.drawRect
fitz.Page.draw_rect = fitz.utils.drawRect
fitz.Page.drawSector = fitz.utils.drawSector
fitz.Page.draw_sector = fitz.utils.drawSector
fitz.Page.drawSquiggle = fitz.utils.drawSquiggle
fitz.Page.draw_squiggle = fitz.utils.drawSquiggle
fitz.Page.drawZigzag = fitz.utils.drawZigzag
fitz.Page.draw_zigzag = fitz.utils.drawZigzag
fitz.Page.getLinks = fitz.utils.getLinks
fitz.Page.get_links = fitz.utils.getLinks
fitz.Page.getPixmap = fitz.utils.getPixmap
fitz.Page.get_pixmap = fitz.utils.getPixmap
fitz.Page.getText = fitz.utils.getText
fitz.Page.get_text = fitz.utils.getText
fitz.Page.getTextbox = fitz.utils.getTextbox
fitz.Page.get_textbox = fitz.utils.getTextbox
fitz.Page.getTextSelection = fitz.utils.getTextSelection
fitz.Page.get_text_selection = fitz.utils.getTextSelection
fitz.Page.getTextBlocks = fitz.utils.getTextBlocks
fitz.Page.get_text_blocks = fitz.utils.getTextBlocks
fitz.Page.getTextWords = fitz.utils.getTextWords
fitz.Page.get_text_words = fitz.utils.getTextWords
fitz.Page.insertImage = fitz.utils.insertImage
fitz.Page.insert_image = fitz.utils.insertImage
fitz.Page.insertLink = fitz.utils.insertLink
fitz.Page.insert_link = fitz.utils.insertLink
fitz.Page.insertText = fitz.utils.insertText
fitz.Page.insert_text = fitz.utils.insertText
fitz.Page.insertTextbox = fitz.utils.insertTextbox
fitz.Page.insert_textbox = fitz.utils.insertTextbox
fitz.Page.newShape = lambda x: fitz.utils.Shape(x)
fitz.Page.new_shape = lambda x: fitz.utils.Shape(x)
fitz.Page.searchFor = fitz.utils.searchFor
fitz.Page.search = fitz.utils.searchFor
fitz.Page.showPDFpage = fitz.utils.showPDFpage
fitz.Page.show_pdf_page = fitz.utils.showPDFpage
fitz.Page.updateLink = fitz.utils.updateLink
fitz.Page.updte_link = fitz.utils.updateLink
fitz.Page.writeText = fitz.utils.writeText
fitz.Page.write_text = fitz.utils.writeText
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
