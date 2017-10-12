from __future__ import print_function
import fitz
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
The main part of the script consists of the pencil function itself.
The bottom part just invokes it, to create images and then save the document.
I have some flexibility built into the pencil function:
Parameters:
page      - PyMuPDF page object
penciltip - coordinates of the pencil tip (fitz.Point object)
pb_height - the thickness of the pencil. This controls the dimension of the
            picture: it will be contained in a rectangle of 100 x 345 pixels
            if this parameter is 100.
left      - a bool indicating whether the pencil points left (True) or right.
-------------------------------------------------------------------------------
"""
def pencil(img, penciltip, pb_height, left, morph = None):
    """Draws a pencil image. 
    """
    from fitz.utils import getColor
    # define some colors
    yellow  = getColor("darkgoldenrod")
    black   = getColor("black")
    white   = getColor("white")
    red     = getColor("red")
    wood    = getColor("wheat2")
    wood2   = getColor("wheat3")
    #---------------------------------------------------------------------------
    # some adjustments depending on pencil tip is left or right:
    # for choosing between a left point (lp) or a right point (rb),
    # we specify oneof(lp, rp), delivering either lp or rp.
    # Variable 's' is used as a sign and is either +1 or -1.
    #---------------------------------------------------------------------------
    if left: s = +1                              # pencil tip is left
    else:    s = -1                              # pencil tip is right
    
    def oneof(l, r):
        if left: return l
        else: return r
    
    w = pb_height * 0.01                         # standard line thickness
    pb_width  = 2 * pb_height                    # pencil body width
    tipendtop = penciltip + fitz.Point(1, -0.5) * pb_height * s
    tipendbot = penciltip + fitz.Point(1, 0.5) * pb_height * s
    r = fitz.Rect(tipendtop,
                  tipendbot + (pb_width * s, 0)) # pencil body
    r.normalize()                                # force r to be finite
    # topline / botline indicate the pencil edges
    topline0  = fitz.Point(r.x0 + r.width*0.1,
                           r.y0 + pb_height/5.)  # upper pencil edge - left
    topline1  = fitz.Point(r.x0 + r.width*0.9,
                           topline0.y)           # upper epncil edge - right
    botline0  = fitz.Point(r.x0 + r.width*0.1,
                           r.y1 - pb_height/5.)  # lower pencil edge - left
    botline1  = fitz.Point(r.x0 + r.width*0.9,
                           botline0.y)           # lower pencil edge - right
    
    # control point 1 for pencil rubber
    hp1 = oneof(r.tr, r.tl) + (pb_height*0.6*s, 0)
    # control point 2 for pencil rubber
    hp2 = oneof(r.br, r.bl) + (pb_height*0.6*s, 0)
    # pencil body is some type of yellow
    img.drawRect(r)
    img.finish(fill = yellow, color = wood, width = w, morph = morph)
    img.drawPolyline((r.tl, topline0, botline0, r.bl))
    img.drawPolyline((r.tr, topline1, botline1, r.br))
    img.finish(fill = wood, color = wood, width = w, closePath = False,
               morph = morph)
    # draw pencil edge lines
    img.drawLine(topline0, topline1)
    img.drawLine(botline0, botline1)
    img.finish(width = w, color=wood2, closePath = False, morph = morph)
    
    #===========================================================================
    # draw the pencil rubber
    #===========================================================================
    img.drawBezier(oneof(r.tr, r.tl), hp1, hp2, oneof(r.br, r.bl))
    img.finish(fill = red, width = w, closePath = False, morph = morph)
    #===========================================================================
    # black rectangle near pencil rubber
    #===========================================================================
    blackrect = fitz.Rect(oneof((r.tr - (pb_height/2., 0)), r.tl),
                          oneof(r.br, (r.bl + (pb_height/2., 0))))
    img.drawRect(blackrect)
    img.finish(fill = black, width = w, morph = morph)
    
    #===========================================================================
    # draw pencil tip and curves indicating pencil sharpening traces
    #===========================================================================
    img.drawPolyline((tipendtop, penciltip, tipendbot))
    img.finish(width = w, fill = wood, closePath = False,
               morph = morph)               # pencil tip
    p1 = oneof(r.tl, r.tr)                  # either left or right
    p2 = oneof(topline0, topline1)
    p3 = oneof(botline0, botline1)
    p4 = oneof(r.bl, r.br)
    p0 = -fitz.Point(pb_height/5., 0)*s     # horiz. displacment of ctrl points
    cp1 = p1 + (p2-p1)*0.5 + p0             # ctrl point upper rounding
    cp2 = p2 + (p3-p2)*0.5 + p0*2.9         # ctrl point middle rounding
    cp3 = p3 + (p4-p3)*0.5 + p0             # ctrl point lower rounding
    img.drawCurve(p1, cp1, p2)
    img.finish(fill = yellow, width = w, color=yellow, morph = morph,
               closePath = True)
    img.drawCurve(p2, cp2, p3)
    img.finish(fill = yellow, width = w, color=yellow, morph = morph,
               closePath = True)
    img.drawCurve(p3, cp3, p4)
    img.finish(fill = yellow, width = w, color=yellow, morph = morph,
               closePath = True)
    
    #===========================================================================
    # draw the pencil tip lead
    #===========================================================================
    img.drawPolyline((penciltip + (tipendtop - penciltip)*0.4,
                      penciltip,
                      penciltip + (tipendbot - penciltip)*0.4))
    #===========================================================================
    # add a curve to indicate lead is round
    #===========================================================================
    img.drawCurve(penciltip + (tipendtop - penciltip)*0.4,
                  penciltip + (pb_height * 0.6 * s, 0),
                  penciltip + (tipendbot - penciltip)*0.4)
    img.finish(width = w, fill = black, morph = morph)
                    
    #===========================================================================
    # re-border pencil body to get rid of some pesky pixels
    #===========================================================================
    img.drawPolyline((p1, p2, p3, p4))
    img.finish(color = yellow, closePath = False, width = w, morph = morph)
    img.drawLine(r.tl, r.tr)
    img.drawLine(r.bl, r.br)
    img.drawPolyline((tipendtop, penciltip, tipendbot))
    img.finish(width = w, closePath = False, morph = morph)
    #===========================================================================
    # draw pencil label - first a rounded rectangle
    #===========================================================================
    p1 = fitz.Point(0.65, 0.15) * pb_height
    p2 = fitz.Point(0.45, 0.15) * pb_height
    lblrect = fitz.Rect(topline0 + oneof(p1, p2),
                        botline1 - oneof(p2, p1))
    img.drawRect(lblrect)
    img.drawCurve(lblrect.tr,
                   fitz.Point(lblrect.x1+pb_height/4., penciltip.y),
                   lblrect.br)
    img.drawCurve(lblrect.tl,
                   fitz.Point(lblrect.x0-pb_height/4., penciltip.y),
                   lblrect.bl)
    img.finish(width = w, fill = black, morph = morph)
    
    #===========================================================================
    # finally the white vertical stripes - whatever they are good for
    #===========================================================================
    p1t = blackrect.tl + fitz.Point(blackrect.width/3., pb_height/20.)
    p1b = blackrect.bl + fitz.Point(blackrect.width/3., -pb_height/20.)
    p2t = blackrect.tl + fitz.Point(blackrect.width*2/3., pb_height/20.)
    p2b = blackrect.bl + fitz.Point(blackrect.width*2/3., -pb_height/20.)
    img.drawLine(p1t, p1b)
    img.drawLine(p2t, p2b)
    img.finish(color=white, width = pb_height*0.08, roundCap = False,
               morph = morph)

    # indicate a medium lead grade
    if img.insertTextbox(lblrect, "HB", color = white,
                          fontname = "Helvetica", morph = morph,
                          fontsize = pb_height * 0.22, align = 1) < 0:
        raise ValueError("not enough space to store pencil text")
    img.commit(True)                   # commit everythinh                       
    return

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
    
    doc.save("pencil.pdf")
