import fitz
from fitz.utils import getColor

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
    img.close()
    doc.save("symbols.pdf")
