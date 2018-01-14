from __future__ import absolute_import
from fitz.fitz import *

class M_Identity(fitz.Matrix):
    """Identity matrix [1, 0, 0, 1, 0, 0]"""
    def __init__(self):
        fitz.Matrix.__init__(self, 1.0, 1.0)
    def __setattr__(self, name, value):
        if name in "abcdef":
            raise NotImplementedError("Identity is readonly")
        else:
            super(fitz.Matrix, self).__setattr__(name, value)

    def checkargs(*args):
        raise NotImplementedError("Identity is readonly")
    preRotate    = checkargs
    preShear     = checkargs
    preScale     = checkargs
    preTranslate = checkargs
    concat       = checkargs
    invert       = checkargs
    def __repr__(self):
        return "fitz.Identity"
        
Identity = M_Identity()

fitz.Identity = Identity

# define the supported colorspaces for convenience
fitz.csRGB    = fitz.Colorspace(fitz.CS_RGB)
fitz.csGRAY   = fitz.Colorspace(fitz.CS_GRAY)
fitz.csCMYK   = fitz.Colorspace(fitz.CS_CMYK)
csRGB         = fitz.csRGB
csGRAY        = fitz.csGRAY
csCMYK        = fitz.csCMYK

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
# Pixmap
#------------------------------------------------------------------------------
fitz.Pixmap.writeImage      = fitz.utils.writeImage

#------------------------------------------------------------------------------
# Annot
#------------------------------------------------------------------------------
fitz.Annot.updateImage      = fitz.utils.updateImage

#------------------------------------------------------------------------------
# Matrix algebra
#------------------------------------------------------------------------------
fitz.Matrix.__abs__         = fitz.utils.mat_abs
fitz.Matrix.__add__         = fitz.utils.mat_add
fitz.Matrix.__bool__        = fitz.utils.mat_true
fitz.Matrix.__contains__    = fitz.utils.mat_contains
fitz.Matrix.__div__         = fitz.utils.mat_div
fitz.Matrix.__eq__          = fitz.utils.mat_equ
fitz.Matrix.__invert__      = fitz.utils.mat_invert
fitz.Matrix.__mul__         = fitz.utils.mat_mult
fitz.Matrix.__neg__         = lambda x: fitz.Matrix(x)*-1 # unary "-"
fitz.Matrix.__nonzero__     = fitz.utils.mat_true
fitz.Matrix.__pos__         = lambda x: fitz.Matrix(x)    # unary "+"
fitz.Matrix.__sub__         = fitz.utils.mat_sub
fitz.Matrix.__truediv__     = fitz.utils.mat_div


#------------------------------------------------------------------------------
# Rect
#------------------------------------------------------------------------------
fitz.Rect.getRectArea       = fitz.utils.getRectArea
fitz.Rect.getArea           = fitz.utils.getRectArea
fitz.Rect.intersects        = fitz.utils.intersects
# Rect algebra
fitz.Rect.__neg__           = lambda x: fitz.Rect(x)*-1 # unary "-"
fitz.Rect.__pos__           = lambda x: fitz.Rect(x)    # unary "+"
fitz.Rect.__abs__           = lambda x: fitz.Rect.getArea(x)  # abs
fitz.Rect.__or__            = fitz.utils.rect_or
fitz.Rect.__and__           = fitz.utils.rect_and
fitz.Rect.__add__           = fitz.utils.rect_add
fitz.Rect.__sub__           = fitz.utils.rect_sub
fitz.Rect.__mul__           = fitz.utils.rect_mul
fitz.Rect.__truediv__       = fitz.utils.rect_div
fitz.Rect.__div__           = fitz.utils.rect_div
fitz.Rect.__eq__            = fitz.utils.rect_equ
fitz.Rect.__nonzero__       = fitz.utils.rect_true
fitz.Rect.__bool__          = fitz.utils.rect_true
fitz.Rect.__contains__      = fitz.utils.rect_contains

#------------------------------------------------------------------------------
# IRect
#------------------------------------------------------------------------------
fitz.IRect.getRectArea      = fitz.utils.getRectArea
fitz.IRect.getArea          = fitz.utils.getRectArea
fitz.IRect.intersects       = fitz.utils.intersects
# IRect algebra
fitz.IRect.__neg__          = lambda x: fitz.IRect(x)*-1 # unary "-"
fitz.IRect.__pos__          = lambda x: fitz.IRect(x)    # unary "+"
fitz.IRect.__abs__          = lambda x: fitz.IRect.getArea(x)  # abs
fitz.IRect.__or__           = fitz.utils.rect_or
fitz.IRect.__and__          = fitz.utils.rect_and
fitz.IRect.__add__          = fitz.utils.rect_add
fitz.IRect.__sub__          = fitz.utils.rect_sub
fitz.IRect.__mul__          = fitz.utils.rect_mul
fitz.IRect.__truediv__      = fitz.utils.rect_div
fitz.IRect.__div__          = fitz.utils.rect_div
fitz.IRect.__eq__           = fitz.utils.rect_equ
fitz.IRect.__nonzero__      = fitz.utils.rect_true
fitz.IRect.__bool__         = fitz.utils.rect_true
fitz.IRect.__contains__     = fitz.utils.rect_contains

#------------------------------------------------------------------------------
# Point algebra
#------------------------------------------------------------------------------
fitz.Point.__neg__          = lambda x: fitz.Point(x)*-1 # unary "-"
fitz.Point.__pos__          = lambda x: fitz.Point(x)    # unary "+"
fitz.Point.__add__          = fitz.utils.point_add
fitz.Point.__sub__          = fitz.utils.point_sub
fitz.Point.__abs__          = fitz.utils.point_abs
fitz.Point.__mul__          = fitz.utils.point_mul
fitz.Point.__truediv__      = fitz.utils.point_div
fitz.Point.__div__          = fitz.utils.point_div
fitz.Point.__nonzero__      = fitz.utils.point_true
fitz.Point.__bool__         = fitz.utils.point_true
fitz.Point.__eq__           = fitz.utils.point_equ
fitz.Point.__contains__     = fitz.utils.point_contains


fitz.__doc__ = "PyMuPDF %s: Python bindings for the MuPDF %s library,\nbuilt on %s" \
               % (fitz.VersionBind, fitz.VersionFitz, fitz.VersionDate)
