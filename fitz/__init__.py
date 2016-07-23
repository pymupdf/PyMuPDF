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

    def preRotate(*args):
        raise NotImplementedError("Identity is readonly")
    def preShear(*args):
        raise NotImplementedError("Identity is readonly")
    def preScale(*args):
        raise NotImplementedError("Identity is readonly")
    def preTranslate(*args):
        raise NotImplementedError("Identity is readonly")
    def concat(*args):
        raise NotImplementedError("Identity is readonly")
    def invert(*args):
        raise NotImplementedError("Identity is readonly")
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
fitz.Pages                  = fitz.utils.Pages
fitz.Document.getPagePixmap = fitz.utils.getPagePixmap
fitz.Document.getPageText   = fitz.utils.getPageText
fitz.Document.setMetadata   = fitz.utils.setMetadata
fitz.Document.setToC        = fitz.utils.setToC
fitz.Page.getLinks          = fitz.utils.getLinks
fitz.Page.getPixmap         = fitz.utils.getPixmap
fitz.Page.getText           = fitz.utils.getText
fitz.Page.searchFor         = fitz.utils.searchFor
fitz.Pixmap.getIRect        = fitz.utils.getIRect
fitz.Pixmap.getColorspace   = fitz.utils.getColorspace
fitz.Pixmap.writeImage      = fitz.utils.writeImage
fitz.Rect.getRectArea       = fitz.utils.getRectArea
fitz.IRect.getRectArea      = fitz.utils.getRectArea
getPointDistance            = fitz.utils.getPointDistance
# matrix arithmetics
fitz.Matrix.__mul__         = fitz.utils.mat_mult
fitz.Matrix.__add__         = fitz.utils.mat_add
fitz.Matrix.__sub__         = fitz.utils.mat_sub
fitz.Matrix.__abs__         = fitz.utils.mat_abs
fitz.Matrix.__neg__         = fitz.utils.mat_neg
fitz.Matrix.__invert__      = fitz.utils.mat_invert
fitz.Matrix.__nonzero__     = fitz.utils.mat_true
# rect arithmetics
fitz.Rect.__neg__           = fitz.utils.rect_neg
fitz.Rect.__or__            = fitz.utils.rect_or
fitz.Rect.__and__           = fitz.utils.rect_and
fitz.Rect.__add__           = fitz.utils.rect_add
fitz.Rect.__sub__           = fitz.utils.rect_sub
fitz.Rect.__mul__           = fitz.utils.rect_mul
# irect arithmetics
fitz.IRect.__neg__          = fitz.utils.rect_neg
fitz.IRect.__or__           = fitz.utils.irect_or
fitz.IRect.__and__          = fitz.utils.irect_and
fitz.IRect.__add__          = fitz.utils.irect_add
fitz.IRect.__sub__          = fitz.utils.irect_sub
fitz.IRect.__mul__          = fitz.utils.irect_mul
# point arithmetics
fitz.Point.__neg__          = fitz.utils.point_neg
fitz.Point.__add__          = fitz.utils.point_add
fitz.Point.__sub__          = fitz.utils.point_sub
fitz.Point.__abs__          = fitz.utils.point_abs
fitz.Point.__mul__          = fitz.utils.point_mul


# ... and delete them from here
del utils
fitz.__doc__ = "PyMuPDF %s: Python bindings for the MuPDF %s library,\nbuilt on %s" \
               % (fitz.VersionBind, fitz.VersionFitz, fitz.VersionDate)
