from __future__ import absolute_import
from fitz.fitz import *

class M_Identity(fitz.Matrix):
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
fitz.open                   = fitz.Document
fitz.Document.getToC        = fitz.utils.getToC
fitz.Document._do_links     = fitz.utils.do_links
fitz.Document.getPagePixmap = fitz.utils.getPagePixmap
fitz.Document.getPageText   = fitz.utils.getPageText
fitz.Document.setMetadata   = fitz.utils.setMetadata
fitz.Document.setToC        = fitz.utils.setToC
fitz.Document.searchPageFor = fitz.utils.searchPageFor
fitz.Page.getLinks          = fitz.utils.getLinks
fitz.Page.getPixmap         = fitz.utils.getPixmap
fitz.Page.getText           = fitz.utils.getText
fitz.Page.searchFor         = fitz.utils.searchFor
fitz.Page.updateLink        = fitz.utils.updateLink
fitz.Page.insertLink        = fitz.utils.insertLink
fitz.Pixmap.writeImage      = fitz.utils.writeImage
fitz.Rect.getRectArea       = fitz.utils.getRectArea
fitz.IRect.getRectArea      = fitz.utils.getRectArea
fitz.IRect.intersects       = fitz.utils.intersects
fitz.Rect.intersects        = fitz.utils.intersects
fitz.Annot.updateImage      = fitz.utils.updateImage
# matrix arithmetics
fitz.Matrix.__mul__         = fitz.utils.mat_mult
fitz.Matrix.__add__         = fitz.utils.mat_add
fitz.Matrix.__sub__         = fitz.utils.mat_sub
fitz.Matrix.__abs__         = fitz.utils.mat_abs
fitz.Matrix.__neg__         = lambda x: fitz.Matrix(x)*-1
fitz.Matrix.__pos__         = lambda x: fitz.Matrix(x)
fitz.Matrix.__invert__      = fitz.utils.mat_invert
fitz.Matrix.__nonzero__     = fitz.utils.mat_true
fitz.Matrix.__bool__        = fitz.utils.mat_true
fitz.Matrix.__eq__          = fitz.utils.mat_equ
fitz.Matrix.__contains__    = fitz.utils.mat_contains
# rect arithmetics
fitz.Rect.__neg__           = lambda x: fitz.Rect(x)*-1
fitz.Rect.__pos__           = lambda x: fitz.Rect(x)
fitz.Rect.__or__            = fitz.utils.rect_or
fitz.Rect.__and__           = fitz.utils.rect_and
fitz.Rect.__add__           = fitz.utils.rect_add
fitz.Rect.__sub__           = fitz.utils.rect_sub
fitz.Rect.__mul__           = fitz.utils.rect_mul
fitz.Rect.__eq__            = fitz.utils.rect_equ
fitz.Rect.__nonzero__       = fitz.utils.rect_true
fitz.Rect.__bool__          = fitz.utils.rect_true
# irect arithmetics
fitz.IRect.__neg__          = lambda x: fitz.IRect(x)*-1
fitz.IRect.__pos__          = lambda x: fitz.IRect(x)
fitz.IRect.__or__           = fitz.utils.rect_or
fitz.IRect.__and__          = fitz.utils.rect_and
fitz.IRect.__add__          = fitz.utils.rect_add
fitz.IRect.__sub__          = fitz.utils.rect_sub
fitz.IRect.__mul__          = fitz.utils.rect_mul
fitz.IRect.__eq__           = fitz.utils.rect_equ
fitz.IRect.__nonzero__      = fitz.utils.rect_true
fitz.IRect.__bool__         = fitz.utils.rect_true
# point arithmetics
fitz.Point.__neg__          = lambda x: fitz.Point(x)*-1
fitz.Point.__pos__          = lambda x: fitz.Point(x)
fitz.Point.__add__          = fitz.utils.point_add
fitz.Point.__sub__          = fitz.utils.point_sub
fitz.Point.__abs__          = fitz.utils.point_abs
fitz.Point.__mul__          = fitz.utils.point_mul
fitz.Point.__nonzero__      = fitz.utils.point_true
fitz.Point.__bool__         = fitz.utils.point_true
fitz.Point.__eq__           = fitz.utils.point_equ
fitz.Point.__contains__     = fitz.utils.point_contains

# ... and delete them from here
del utils
fitz.__doc__ = "PyMuPDF %s: Python bindings for the MuPDF %s library,\nbuilt on %s" \
               % (fitz.VersionBind, fitz.VersionFitz, fitz.VersionDate)
