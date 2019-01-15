from __future__ import absolute_import
from fitz.fitz import *

# define the supported colorspaces for convenience
fitz.csRGB    = fitz.Colorspace(fitz.CS_RGB)
fitz.csGRAY   = fitz.Colorspace(fitz.CS_GRAY)
fitz.csCMYK   = fitz.Colorspace(fitz.CS_CMYK)
csRGB         = fitz.csRGB
csGRAY        = fitz.csGRAY
csCMYK        = fitz.csCMYK

# create the TOOLS object
TOOLS         = fitz.Tools()
fitz.TOOLS    = TOOLS

if fitz.VersionFitz != fitz.TOOLS.mupdf_version():
    raise ValueError("MuPDF library mismatch %s <> %s" % (fitz.VersionFitz, fitz.TOOLS.mupdf_version()))

import fitz.utils

# copy functions to their respective fitz classes

#------------------------------------------------------------------------------
# Document
#------------------------------------------------------------------------------
fitz.open                   = fitz.Document
fitz.Document.getToC        = fitz.utils.getToC
fitz.Document._do_links     = fitz.utils.do_links
fitz.Document.getPagePixmap = fitz.utils.getPagePixmap
fitz.Document.getPageText   = fitz.utils.getPageText
fitz.Document.setMetadata   = fitz.utils.setMetadata
fitz.Document.setToC        = fitz.utils.setToC
fitz.Document.searchPageFor = fitz.utils.searchPageFor
fitz.Document.newPage       = fitz.utils.newPage
fitz.Document.getCharWidths = fitz.utils.getCharWidths

#------------------------------------------------------------------------------
# Page
#------------------------------------------------------------------------------
fitz.Page.drawBezier         = fitz.utils.drawBezier
fitz.Page.drawCircle         = fitz.utils.drawCircle
fitz.Page.drawCurve          = fitz.utils.drawCurve
fitz.Page.drawLine           = fitz.utils.drawLine
fitz.Page.drawOval           = fitz.utils.drawOval
fitz.Page.drawPolyline       = fitz.utils.drawPolyline
fitz.Page.drawRect           = fitz.utils.drawRect
fitz.Page.drawQuad           = fitz.utils.drawQuad
fitz.Page.drawSector         = fitz.utils.drawSector
fitz.Page.drawSquiggle       = fitz.utils.drawSquiggle
fitz.Page.drawZigzag         = fitz.utils.drawZigzag
fitz.Page.getTextBlocks      = fitz.utils.getTextBlocks
fitz.Page.getTextWords       = fitz.utils.getTextWords
fitz.Page.getLinks           = fitz.utils.getLinks
fitz.Page.getPixmap          = fitz.utils.getPixmap
fitz.Page.getText            = fitz.utils.getText
fitz.Page.insertLink         = fitz.utils.insertLink
fitz.Page.insertTextbox      = fitz.utils.insertTextbox
fitz.Page.insertText         = fitz.utils.insertText
fitz.Page.searchFor          = fitz.utils.searchFor
fitz.Page.showPDFpage        = fitz.utils.showPDFpage
fitz.Page.updateLink         = fitz.utils.updateLink
fitz.Page.newShape           = lambda x: fitz.utils.Shape(x)

#------------------------------------------------------------------------------
# Rect
#------------------------------------------------------------------------------
fitz.Rect.getRectArea       = fitz.utils.getRectArea
fitz.Rect.getArea           = fitz.utils.getRectArea

#------------------------------------------------------------------------------
# IRect
#------------------------------------------------------------------------------
fitz.IRect.getRectArea      = fitz.utils.getRectArea
fitz.IRect.getArea          = fitz.utils.getRectArea

fitz.__doc__ = "PyMuPDF %s: Python bindings for the MuPDF %s library,\nbuilt on %s" \
               % (fitz.VersionBind, fitz.VersionFitz, fitz.VersionDate)
