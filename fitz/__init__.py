from __future__ import absolute_import
from fitz.fitz import *

# define the usual colorspaces for convenience
fitz.csRGB  = fitz.Colorspace(fitz.CS_RGB)
fitz.csGRAY = fitz.Colorspace(fitz.CS_GRAY)
fitz.csCMYK = fitz.Colorspace(fitz.CS_CMYK)
csRGB       = fitz.csRGB
csGRAY      = fitz.csGRAY
csCMYK      = fitz.csCMYK

import fitz.utils
# copy functions to their respective fitz classes
fitz.Document.getToC        = fitz.utils.getToC
fitz.Document.getPagePixmap = fitz.utils.getPagePixmap
fitz.Document.getPageText   = fitz.utils.getPageText
fitz.Page.getLinks          = fitz.utils.getLinks
fitz.Page.getPixmap         = fitz.utils.getPixmap
fitz.Page.getText           = fitz.utils.getText
fitz.Page.searchFor         = fitz.utils.searchFor
fitz.Pixmap.getIRect        = fitz.utils.getIRect
fitz.Pixmap.getColorspace   = fitz.utils.getColorspace
fitz.Pixmap.writeImage      = fitz.utils.writeImage
RectArea                    = fitz.utils.RectArea
PointDistance               = fitz.utils.PointDistance
# ... and delete them from here
del utils
