from __future__ import print_function
import fitz
from shapes_and_symbols import pencil
"""
@created: 2017-07-03 14:00:00

@author: (c) Jorj X. McKie

PyMuPDF demo function for creating a pencil drawing similar to ReportLab's
Users Guide on pp. 39. The main difference: pencil sharpening traces are shown
more correctly ... :-)

Dependencies:
PyMuPDF

License:
 GNU GPL 3+
-------------------------------------------------------------------------------
Main purpose of this function is to demonstrate that working with PyMuPDF
is easy and straightforward ...
What does introduce some complexity is the ability to scale, and to left-right
flip the image while maintaining the text legible.
-------------------------------------------------------------------------------
New (2017-09-21):
-----------------
Scaling and other morphing effects can now also be achieved with a morphing
matrix. This is possible after page method "insertTextbox" also supports this.
-------------------------------------------------------------------------------
"""
#==============================================================================
# invoke the pencil function
#==============================================================================
if __name__ == "__main__":
    doc=fitz.open()                         # empty new PDF
    page = doc.newPage()                    # create page (A4)
    img  = page.newShape()                  # create shape
# =============================================================================
#   pencil 1
# =============================================================================
    penheight = 100                         # thickness of pencil
    pentip = fitz.Point(100, 150)           # first pencil tip here
    pencil(img, pentip, penheight, True)    # pencil points left
# =============================================================================
#   pencil 2    
# =============================================================================
    penheight = 20                          # now a smaller one
    pentip = fitz.Point(100, 250)           # new pencil tip
    pencil(img, pentip, penheight, False)   # this one points right
    
    pentip.x += 10                          # insert a little distance
    text = """Like the ReportLab User Guide does,\nyou may want to use this image, to\nemphasize content, e.g. cautionary\nremarks, notes, examples, etc."""
    page.insertText(pentip, text)           # insert explanatory text
# =============================================================================
#   pencil 3    
# =============================================================================
    # yet another pencil, which we will morph around its tip
    mat = fitz.Matrix(-150)*fitz.Matrix(0.5,0.5,1)    # morphing: rotate & shear
    pentip = fitz.Point(300, 400)
    # instead of another thickness (40) we could have used a scale matrix
    pencil(img, pentip, 40, True, morph=(pentip, mat))
    img.commit()
    doc.save("pencil.pdf")
