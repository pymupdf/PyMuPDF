import fitz
from fitz.utils import getColor
"""
-------------------------------------------------------------------------------
Created on Fri Nov 10 07:00:00 2017

@author: Jorj McKie
Copyright (c) 2017 Jorj X. McKie

The license of this program is governed by the GNU GENERAL PUBLIC LICENSE
Version 3, 29 June 2007. See the "COPYING" file of the PyMuPDF repository.
-------------------------------------------------------------------------------
Contains signs and symbols created with PyMuPDF's image creation features.
The intention is to facilitate the use of these features by providing functions
that create ready-made symbols. We strive to increase the function set from
time to time.

To include a function in your Python script, import it like so:

from shapes_and_symbols import smiley

Using a function
----------------

smiley(img, rect, ...)

Allmost all functions have the same first and second parameter:

img    - fitz.Shape object created by page.newShape()
rect   - fitz.Rect object. This is the area in which the image should appear.

Other parameters are function-specific, but always include a "morph" argument.
This can be used to change the image's appearance in an almost arbitrary way:
rotation, shearing, mirroring. For this you must provide a fitz.Point and a
fitz.Matrix object. See PyMuPDF documentation, chapter "Shape".

Using function "pencil"
-----------------------

pencil(img, penciltip, thickness, ...)

penciltip - (fitz.Point) location of the pencil's tip
thickness - (int) pencil's thickness in pixels.

The pencil's rectangle is computed from these two values - fixed proportions are
100 x 340, if thickness is 100. However, you can use the "morph" argument to
change appearance.
The main reasons for this special treatment are the appearance of some text and
the option of letting pencil point to left or right.

-------------------------------------------------------------------------------
Available functions
-------------------

dontenter - traffic sign Do Not Enter
heart     - heart
clover    - 4 leaved clover
diamond   - rhombus
caro      - one of the 4 card game colors
arrow     - a triangle
hand      - a hand symbol similar to internet
pencil    - a pencil (eye catcher)
smiley    - emoji
frowney   - emoji
-------------------------------------------------------------------------------

Dependencies
------------
PyMuPDF
-------------------------------------------------------------------------------
"""
# =============================================================================
# Do Not Enter
# =============================================================================
def dontenter(img, r, morph = None):
    """Draw the "Do Not Enter" traffic symbol.
    """
    red = getColor("red3")
    white = (1,1,1)
    img.drawOval(r)               # draw red circle w/ thick white border
    img.finish(fill = red, color = white, width = r.width * 0.04)
    img.drawOval(r)               # draw empty circle, thin black border
    img.finish(width = r.width * 0.001)
    deltah = r.width * 0.13
    deltav = r.height * 0.45
    rs = r + (deltah, deltav, -deltah, -deltav)
    img.drawRect(rs)              # draw white horizontal rectangle
    img.finish(color = white, fill = white, width = r.width * 0.06,
               roundCap = False, morph = morph)
    return

# =============================================================================
# Heart
# =============================================================================
def heart(img, r, col, morph = None):
    """Draw a heart image inside a rectangle.
    """
    mtop = r.tl + (r.tr - r.tl) * 0.5
    mbot = r.bl + (r.br - r.bl) * 0.5
    htop = mtop + (mbot - mtop)*0.3     # top point where arcs meet
    hbot = mtop + (mbot - mtop)*0.8     # bottom point joining arcs
    # left and right ctrl points, symmetrical.
    pl1  = r.tl + (r.tr - r.tl) * 0.25
    pr1  = r.tr - (r.tr - r.tl) * 0.25
    pl2  = r.tl + (r.bl - r.tl) * 0.40
    pr2  = r.tr + (r.br - r.tr) * 0.40
    # we have defined all 6 points and now draw 2 Bezier curves
    img.drawBezier(htop, pl1, pl2, hbot)
    img.drawBezier(htop, pr1, pr2, hbot)
    img.finish(color = col, fill = col, closePath = True, morph = morph)

# =============================================================================
# Clover leaf    
# =============================================================================
def clover(img, r, col, morph = None):
    """Draw a 4-leaf clover image inside a rectangle.
    """
    # this is made of 4 Bezier curves, each starting and ending in the
    # rect's middle point M
    M = r.tl + (r.br - r.tl) * 0.5
    img.drawBezier(M, r.tl, r.tr, M)
    img.drawBezier(M, r.tr, r.br, M)
    img.drawBezier(M, r.bl, r.tl, M)
    img.drawBezier(M, r.br, r.bl, M)
    img.finish(color = col, fill = col, width = 0.3, morph = morph)

# =============================================================================
# Diamond
# =============================================================================
def diamond(img, r, col, morph = None):
    """Draw a rhombus in a rectangle.
    """
    white = (1,1,1)
    mto = r.tl + (r.tr - r.tl) * 0.5
    mri = r.tr + (r.br - r.tr) * 0.5
    mbo = r.bl + (r.br - r.bl) * 0.5
    mle = r.tl + (r.bl - r.tl) * 0.5
    img.drawPolyline((mto, mri, mbo, mle))
    img.finish(color = white, fill = col, closePath = True, morph = morph)

# =============================================================================
# Caro (card game color)
# =============================================================================
def caro(img, r, col, morph = None):
    """Draw a caro symbol in a rectangle.
    """
    white = (1,1,1)
    mto = r.tl + (r.tr - r.tl) * 0.5
    mri = r.tr + (r.br - r.tr) * 0.5
    mbo = r.bl + (r.br - r.bl) * 0.5
    mle = r.tl + (r.bl - r.tl) * 0.5
    M = r.tl + (r.br - r.tl) * 0.5
    img.drawCurve(mle, M, mto)
    img.drawCurve(mto, M, mri)
    img.drawCurve(mri, M, mbo)
    img.drawCurve(mbo, M, mle)
    img.finish(color = white, fill = col, morph = morph)

# =============================================================================
# Arrow
# =============================================================================
def arrow(img, r, col, morph = None):
    """Draw a triangle symbol in a rectangle. Last parameter indicates direction
    the arrow points to: either as a number or as first letter of east(0), south(1),
    west(3), north(4).
    """
    white = (1,1,1)
    p1 = r.tl
    p2 = r.bl
    p3 = r.tr + (r.br - r.tr) * 0.5
    img.drawPolyline((p1, p2, p3))
    img.finish(color = white, fill = col, closePath = True, morph = morph)

# =============================================================================
# Hand
# =============================================================================
def hand(img, rect, color = None, fill = None, morph = None):
    """Put a hand symbol inside a rectangle on a PDF page. Parameters:
    img - an object of the Shape class (contains relevant page information)
    rect - a rectangle. Its width must be at least 30% larger than its height.
    color, fill - color triples for border and filling (optional).
    morph - morphing parameters (point, matrix)
    """
    if rect.width / rect.height < 1.25:
        raise ValueError("rect width:height ratio must be at least 1.25")
    if not color:
        line = getColor("orange")
    else:
        line = color
    if not fill:
        skin = getColor("burlywood1")
    else:
        skin = fill
    # define control points for the symbol, relative to a rect height of 3.
    points = ((0.0, 1.4), (1.4, 0.2), (1.4, 1.4), (2.2, 0.0), (1.4, 1.4),
              (3.4, 1.4), (3.4, 1.8), (2.8, 1.8), (2.8, 2.2), (2.6, 2.2),
              (2.6, 2.6), (2.5, 2.6), (2.5, 3.0),
             )
    # rescale points to the argument rectangle.
    f = rect.height / 3
    tl = rect.tl                           # need this as displacement
    p1 =  fitz.Point(points[0]) * f + tl
    p2 =  fitz.Point(points[1]) * f + tl
    p3 =  fitz.Point(points[2]) * f + tl
    p4 =  fitz.Point(points[3]) * f + tl
    p5 =  fitz.Point(points[4]) * f + tl
    p6 =  fitz.Point(points[5]) * f + tl
    p7 =  fitz.Point(points[6]) * f + tl
    p8 =  fitz.Point(points[7]) * f + tl
    p9 =  fitz.Point(points[8]) * f + tl
    p10 = fitz.Point(points[9]) * f + tl
    p11 = fitz.Point(points[10]) * f + tl
    p12 = fitz.Point(points[11]) * f + tl
    p13 = fitz.Point(points[12]) * f + tl
    # some additional helper points for Bezier curves of the finger tips.
    d1 = fitz.Point(0.4, 0) *f
    d7 = p7 - fitz.Point(1.2, 0) * f
    d9 = fitz.Point(d7.x, p9.y)
    d11 = fitz.Point(d7.x, p11.y)
    # now draw everything
    # IMPORTANT: the end point of each draw method must equal the start point
    # of the next one in order to create one connected path. Only then the
    # "finish" parameters will apply to all draws.
    img.drawCurve(p1, p3, p2)
    img.drawCurve(p2, p4, p5)
    img.drawLine(p5, p6)
    img.drawBezier(p6, p6 + d1, p7 + d1, p7)
    img.drawLine(p7, d7)
    img.drawLine(d7, p8)
    img.drawBezier(p8, p8 + d1, p9 + d1, p9)
    img.drawLine(p9, d9)
    img.drawLine(d9, p10)
    img.drawBezier(p10, p10 + d1, p11 + d1, p11)
    img.drawLine(p11, d11)
    img.drawLine(d11, p12)
    img.drawBezier(p12, p12 + d1, p13 + d1, p13)
    img.drawLine(p13, rect.bl)
    img.finish(color = line, fill = skin, closePath = False, morph = morph)
    return

# =============================================================================
# Pencil
# =============================================================================
def pencil(img, penciltip, pb_height, left, morph = None):
    """Draw a pencil image. Parameters:
    img       -  Shape object
    penciltip - fitz.Point, coordinates of the pencil tip
    pb_height - the thickness of the pencil. This controls the dimension of the
                picture: it will be contained in a rectangle of 100 x 345 pixels
                if this parameter is 100.
    left      - bool, indicates whether the pencil points left (True) or right.
    morph     - a tuple (point, matrix) to achieve image torsion.
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
    # we specify oneof(lp, rp), delivering either lp or rp. Likewise,
    # variable 's' is used as a sign and is either +1 or -1.
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
    img.finish(width = w, color = wood2, closePath = False, morph = morph)
    
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
    p1t = blackrect.tl + (blackrect.width/3.,   pb_height/20.)
    p1b = blackrect.bl + (blackrect.width/3.,   -pb_height/20.)
    p2t = blackrect.tl + (blackrect.width*2/3., pb_height/20.)
    p2b = blackrect.bl + (blackrect.width*2/3., -pb_height/20.)
    img.drawLine(p1t, p1b)
    img.drawLine(p2t, p2b)
    img.finish(color = white, width = pb_height*0.08, roundCap = False,
               morph = morph)

    # insert text to indicate a medium lead grade
    if img.insertTextbox(lblrect, "HB", color = white,
                          fontname = "Helvetica", morph = morph,
                          fontsize = pb_height * 0.22, align = 1) < 0:
        raise ValueError("not enough space to store 'HB' text")
    return

# =============================================================================
# Smiley emoji
# =============================================================================
def smiley(img, rect, color = (0,0,0), fill = (1,1,0), morph = None):
    dx = rect.width * 0.2
    dy = rect.height * 0.25
    w = rect.width * 0.01
    img.drawOval(rect)                      # draw face
    img.finish(fill = fill, width = w, morph = morph)
    # calculate rectangles containing the eyes
    rl = fitz.Rect(rect.tl + (dx, dy),
                   rect.tl + (2 * dx, 2 * dy))
    rr = fitz.Rect(rect.tr + (-2 * dx, dy),
                   rect.tr + (-dx, 2 * dy))
    img.drawOval(rl)                        # draw left eye
    img.drawOval(rr)                        # draw right eye
    img.finish(fill = color, morph = morph)
    p0 = rl.bl + (0, 0.75 * dy)             # left corner of mouth
    p1 = rr.br + (0, 0.75 * dy)             # right corner of mouth
    c  = rect.bl + (rect.br - rect.bl)*0.5
    img.drawCurve(p0, c, p1)                # draw mouth
    img.finish(width = 4 * w, closePath = False, morph = morph)

# =============================================================================
# Frowney emoji
# =============================================================================
def frowney(img, rect, color = (0,0,0), fill = (1,1,0), morph = None):
    dx = rect.width * 0.2
    dy = rect.height * 0.25
    w = rect.width * 0.01
    img.drawOval(rect)                      # draw face
    img.finish(fill = fill, width = w, morph = morph)
    # calculate rectangles containing the eyes
    rl = fitz.Rect(rect.tl + (dx, dy),
                   rect.tl + (2 * dx, 2 * dy))
    rr = fitz.Rect(rect.tr + (-2 * dx, dy),
                   rect.tr + (-dx, 2 * dy))
    img.drawOval(rl)                        # draw left eye
    img.drawOval(rr)                        # draw right eye
    img.finish(fill = color, morph = morph)
    p0 = rl.bl + (0, dy)                    # left corner of mouth
    p1 = rr.br + (0, dy)                    # right corner of mouth
    c  = rl.bl + (rr.br - rl.bl)*0.5
    img.drawCurve(p0, c, p1)                # draw mouth
    img.finish(width = 4 * w, closePath = False, morph = morph)

#------------------------------------------------------------------------------
# Main program
#------------------------------------------------------------------------------
if __name__ == "__main__":
    green = getColor("limegreen")
    red = getColor("red2")
    doc = fitz.open()
    p = doc.newPage()
    img = p.newShape()
    r = fitz.Rect(100, 100, 200, 200)
    heart(img, r, red)
    
    r1 = r + (100, 0, 100, 0)
    p = r1.tl + (r1.br - r1.tl)*0.5
    clover(img, r1, green, morph = (p, fitz.Matrix(45)))
    
    r2 = r1 + (100, 0, 100, 0)
    diamond(img, r2, red)
    
    r3 = r2 + (100, 0, 100, 0)
    p = r3.tl + (r3.br - r3.tl)*0.5
    caro(img, r3, red, morph = (p, fitz.Matrix(45)))
    
    r4 = r + (0, 150, 0, 150)
    p = r4.tl + (r4.br - r4.tl)*0.5
    arrow(img, r4, red, morph = (p, fitz.Matrix(0)))
    
    r5 = r4 + (r4.width, 0, r4.width, 0)
    dontenter(img, r5, morph = None)
    
    r8 = r4 + (0, 120, 30, 120)
    hand(img, r8, morph = None)
    img.commit()
    doc.save("symbols.pdf")
