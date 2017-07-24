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

The main purpose of this function is to demonstrate that working with PyMuPDF
is easy and straightforward ...
What does introduce complexity is the ability to left-right flip the image.
--------------------------
The main part of the script consists of the pencil function itself.
The bottom part just invokes it to create to images and then save the document.
I have some flexibility built into the pencil function:
Parameters:
page      - PyMuPDF page object
penciltip - coordinates of the pencil tip (fitz.Point object)
pb_height - the thickness of the pencil. This controls the dimension of the
            picture: it will be contained in a rectangle of 100 x 345 pixels
            if this parameter is 100.
left      - a bool indicating whether the pencil points left (True) or right.

"""
def pencil(page, penciltip, pb_height, left):
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
    # some adjustments follow depending on pencil tip is left or right:
    # when choices need be made between a left point (lp) or a right point (rb),
    # we specify lp*a + rp*b, delivering either lp or rp.
    # Variable 's' is used as a sign and is either +1 or -1.
    #---------------------------------------------------------------------------
    if left:                                     # pencil tip is left
        a = 1
        b = 0
        s = 1
    else:
        a = 0
        b = 1
        s = -1
        
    w = pb_height * 0.01                         # standard line thickness
    pb_width  = 2 * pb_height                    # pencil body width
    tipendtop = penciltip + fitz.Point(1, -0.5) * pb_height * s
    tipendbot = penciltip + fitz.Point(1, 0.5) * pb_height * s
    r = fitz.Rect(tipendtop,
                  tipendbot + fitz.Point(pb_width, 0) * s) # pencil body
    r.normalize()                                 # force r to be finite
    # topline / botline indicate the pencil edges
    topline0  = fitz.Point(r.x0 + r.width*0.1,
                           r.y0 + pb_height/5.) # upper pencil edge - left
    topline1  = fitz.Point(r.x0 + r.width*0.9,
                           topline0.y)    # upper epncil edge - right
    botline0  = fitz.Point(r.x0 + r.width*0.1,
                           r.y1 - pb_height/5.) # lower pencil edge - left
    botline1  = fitz.Point(r.x0 + r.width*0.9,
                           botline0.y)    # lower pencil edge - right
    
    # control point 1 for pencil rubber
    hp1 = r.top_right * a + r.top_left * b + fitz.Point(pb_height*0.6, 0) * s
    # control point 2 for pencil rubber
    hp2 = r.bottom_right * a + r.bottom_left * b + fitz.Point(pb_height*0.6, 0) * s
    # pencil body is some type of yellow
    page.drawRect(r, fill = yellow, color = wood, width = w)
    page.drawPolyline((r.top_left, topline0, botline0, r.bottom_left),
                      fill = wood, color = yellow, width = w)
    page.drawPolyline((r.top_right, topline1, botline1, r.bottom_right),
                      fill = wood, color = yellow, width = w)
    # draw pencil edge lines
    page.drawLine(topline0, topline1, width = w, color=wood2)
    page.drawLine(botline0, botline1, width = w, color=wood2)
    
    #===========================================================================
    # draw the pencil rubber
    #===========================================================================
    page.drawBezier(r.top_right*a + r.top_left*b,
                    hp1, hp2,
                    r.bottom_right*a + r.bottom_left*b,
                    fill = red, width = w)
    #===========================================================================
    # black rectangle near pencil rubber
    #===========================================================================
    blackrect = fitz.Rect((r.top_right - fitz.Point(pb_height/2.,0))*a +\
                           r.top_left*b,
                           r.bottom_right*a + (r.bottom_left + \
                                              fitz.Point(pb_height/2.,0))*b)
    page.drawRect(blackrect, fill = black, width = w)
    
    #===========================================================================
    # draw pencil tip and curves indicating pencil sharpening traces
    #===========================================================================
    page.drawPolyline((tipendtop, penciltip, tipendbot), width = w,
                      fill = wood)          # pencil tip
    p1 = r.top_left*a + r.top_right*b       # either left or right
    p2 = topline0*a + topline1*b
    p3 = botline0*a + botline1*b
    p4 = r.bottom_left*a + r.bottom_right*b
    p0 = -fitz.Point(pb_height/5., 0)*s     # horiz. displacment of ctrl points
    cp1 = p1 + (p2-p1)*0.5 + p0             # ctrl point upper rounding
    cp2 = p2 + (p3-p2)*0.5 + p0*2.9         # ctrl point middle rounding
    cp3 = p3 + (p4-p3)*0.5 + p0             # ctrl point lower rounding
    page.drawCurve(p1, cp1, p2, fill = yellow, width = w, color=wood)
    page.drawCurve(p2, cp2, p3, fill = yellow, width = w, color=wood)
    page.drawCurve(p3, cp3, p4, fill = yellow, width = w, color=wood)
    
    #===========================================================================
    # draw the pencil tip lead mine
    #===========================================================================
    page.drawPolyline((penciltip+(tipendtop - penciltip)*0.4,
                       penciltip,
                       penciltip+(tipendbot - penciltip)*0.4),
                       fill = black, width = w, closePath = True)
    #===========================================================================
    # add a curve to indicate lead mine is round
    #===========================================================================
    page.drawCurve(penciltip+(tipendtop - penciltip)*0.4,
                    fitz.Point(penciltip.x+pb_height*0.6*s, penciltip.y),
                    penciltip+(tipendbot - penciltip)*0.4, 
                    width = w, fill = black)
                    
    #===========================================================================
    # re-border pencil body getting rid of some pesky pixels
    #===========================================================================
    page.drawLine(r.top_left, r.top_right, width = w)
    page.drawLine(r.bottom_left, r.bottom_right, width = w)
    page.drawPolyline((tipendtop, penciltip, tipendbot), width = w)
    #===========================================================================
    # draw pencil label - first a rounded rectangle
    #===========================================================================
    p1 = fitz.Point(0.65, 0.15) * pb_height
    p2 = fitz.Point(0.45, 0.15) * pb_height
    lblrect = fitz.Rect(topline0 + p1*a + p2*b,
                        botline1 - p2*a - p1*b)
    page.drawRect(lblrect, width = w, fill = black)
    page.drawCurve(lblrect.top_right,
                   fitz.Point(lblrect.x1+pb_height/4., penciltip.y),
                   lblrect.bottom_right, width = w, fill = black)
    page.drawCurve(lblrect.top_left,
                   fitz.Point(lblrect.x0-pb_height/4., penciltip.y),
                   lblrect.bottom_left, width = w, fill = black)
    # ... then text indicating it's a medium pencil
    if page.insertTextbox(lblrect, "No.2", color = white, fontname = "Helvetica", 
                       fontsize = pb_height * 0.22, align = 1) < 0:
        raise ValueError("not enough space to store pencil text")
                       
    #===========================================================================
    # finally the white vertical stripes - whatever they are good for
    #===========================================================================
    p1t = blackrect.top_left + fitz.Point(blackrect.width/3., pb_height/20.)
    p1b = blackrect.bottom_left + fitz.Point(blackrect.width/3., -pb_height/20.)
    p2t = blackrect.top_left + fitz.Point(blackrect.width*2/3., pb_height/20.)
    p2b = blackrect.bottom_left + fitz.Point(blackrect.width*2/3., -pb_height/20.)
    page.drawLine(p1t, p1b, color=white, width = pb_height*0.08, roundCap = False)
    page.drawLine(p2t, p2b, color=white, width = pb_height*0.08, roundCap = False)
    return

#==============================================================================
# invoke the pencil function
#==============================================================================
doc=fitz.open()
doc.insertPage()
page=doc[0]

penheight = 100

pentip2 = fitz.Point(100, 150)
pencil(page, pentip2, penheight, True)

penheight = 20

pentip1 = fitz.Point(100, 250)
pencil(page, pentip1, penheight, False)
pentip1.x += 10                        # insert a litle distance
text = "Like the ReportLab User Guide does,\nyou may want to use this image, to\nemphasize content, e.g. cautionary\nremarks, notes, examples, etc."
page.insertText(pentip1, text)

doc.save("pencil.pdf")
