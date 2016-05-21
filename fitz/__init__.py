from __future__ import absolute_import
from fitz.fitz import *

class M_Identity(fitz.Matrix):
    def __init__(self):
        fitz.Matrix.__init__(self, 1.0, 1.0)
    def __setattr__(self, name, value):
        if name in "abcdef":
            raise NotImplementedError("Identity is a constant")
        else:
            super(fitz.Matrix, self).__setattr__(name, value)

    def preRotate(*args):
        raise NotImplementedError("Identity is a constant")
    def preShear(*args):
        raise NotImplementedError("Identity is a constant")
    def preScale(*args):
        raise NotImplementedError("Identity is a constant")
    def concat(*args):
        raise NotImplementedError("Identity is a constant")
    def invert(*args):
        raise NotImplementedError("Identity is a constant")
        
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
fitz.Document.select        = fitz.utils.select
fitz.Document.getPagePixmap = fitz.utils.getPagePixmap
fitz.Document.getPageText   = fitz.utils.getPageText
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
# ... and delete them from here
del utils
fitz.__doc__ = "PyMuPDF %s: the Python bindings for the MuPDF %s library,\ncreated on %s" \
               % (fitz.VersionBind, fitz.VersionFitz, fitz.VersionDate)
