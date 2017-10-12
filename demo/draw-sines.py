from __future__ import print_function
import fitz, math
"""
Created on 2017-08-17

@author: (c) 2017, Jorj X. McKie

License: GNU GPL V3

PyMuPDF Demo Program
---------------------
Create a PDF with drawings of the sine and the cosine functions using PyMuPDF.
The begin and end points, pb and pe respectively, are viewed as to providing
a full phase of length 2*pi = 360 degrees.

The function graphs are pieced together in 90 degree parts, for which Bezier
curves are used.

Note that the 'cp1' and 'cp2' constants below represent values for use as 
Bezier control points like so:
x-values (deg): [0, 30, 60, 90]
y-values:       [0, cp1, cp2, 1]

These values have been calculated by the scipy.interpolate.splrep() method.
They provide an excellent spline approximation of the sine / cosine
functions - please see the SciPy documentation for background.
-------------------------------------------------------------------------------
Updates
-------
2017-09-21: Add legend text, as morphing is also supported by "insertTextbox".
Other changes are minor performance and documentation improvements.

"""
def bsinPoints(pb, pe):
    """Return Bezier control points, when pb and pe stand for a full period
    from (0,0) to (2*pi, 0), respectively, in the user's coordinate system.
    The returned points can be used to draw up to four Bezier curves for
    the complete phase of the sine function graph from 0 to 2*pi.
    """
    v = pe - pb
    assert v.y == 0, "begin and end points must have same height"
    f = abs(v) * 0.5 / math.pi              # represents the unit
    cp1 = 5.34295228e-01
    cp2 = 1.01474288e+00
    y_ampl = (0, f)
    y_cp1 = (0, f * cp1)
    y_cp2 = (0, f * cp2)

    p0 = pb
    p4 = pe
    p1 = pb + v * 0.25 - y_ampl
    p2 = pb + v * 0.5
    p3 = pb + v * 0.75 + y_ampl
    k1 = pb + v * (1./12.)  - y_cp1
    k2 = pb + v * (2./12.)  - y_cp2
    k3 = pb + v * (4./12.)  - y_cp2
    k4 = pb + v * (5./12.)  - y_cp1
    k5 = pb + v * (7./12.)  + y_cp1
    k6 = pb + v * (8./12.)  + y_cp2
    k7 = pb + v * (10./12.) + y_cp2
    k8 = pb + v * (11./12.) + y_cp1
    return p0, k1, k2, p1, k3, k4, p2, k5, k6, p3, k7, k8, p4

def bcosPoints(pb, pe):
    """Return Bezier control points, when pb and pe stand for a full period
    from (0,0) to (2*pi, 0), respectively, in the user's coordinate system.
    The returned points can be used to draw up to four Bezier curves for
    the complete phase of the cosine function graph from 0 to 2*pi.
    """
    v = pe - pb
    assert v.y == 0, "begin and end points must have same height"
    f = abs(v) * 0.5 / math.pi              # represents the unit
    cp1 = 5.34295228e-01
    cp2 = 1.01474288e+00
    y_ampl = (0, f)
    y_cp1 = (0, f * cp1)
    y_cp2 = (0, f * cp2)

    p0 = pb - y_ampl
    p4 = pe - y_ampl
    p1 = pb + v * 0.25
    p2 = pb + v * 0.5 + y_ampl
    p3 = pb + v * 0.75
    k1 = pb + v * (1./12.)  - y_cp2
    k2 = pb + v * (2./12.)  - y_cp1
    k3 = pb + v * (4./12.)  + y_cp1
    k4 = pb + v * (5./12.)  + y_cp2
    k5 = pb + v * (7./12.)  + y_cp2
    k6 = pb + v * (8./12.)  + y_cp1
    k7 = pb + v * (10./12.) - y_cp1
    k8 = pb + v * (11./12.) - y_cp2
    return p0, k1, k2, p1, k3, k4, p2, k5, k6, p3, k7, k8, p4

def rot_points(pnts, pb, alfa):
    """Rotate a list of points by an angle alfa around pivotal point pb.
    Intended for modifying the control points of trigonometric functions.
    """
    points = []
    calfa = math.cos(alfa)
    salfa = math.sin(alfa)
    for p in pnts:
        s = p - pb
        r = abs(s)
        if r > 0: s /= r
        np = (s.x * calfa - s.y * salfa, s.y * calfa + s.x * salfa)
        points.append(pb + fitz.Point(np)*r)
    return points

if __name__ == "__main__":
    from fitz.utils import getColor
    doc    = fitz.open()          # a new PDF
    page   = doc.newPage()        # a new page in it
    img    = page.newShape()      # start a Shape
    red    = getColor("red")      # line color for sine
    blue   = getColor("blue")     # line color for cosine
    yellow = getColor("py_color") # background color
    w = 0.3                       # line width
    #--------------------------------------------------------------------------
    # Define start / end points of x axis that we want to use as 0 and 2*pi.
    # They may be oriented in any way.
    #--------------------------------------------------------------------------
    pb = fitz.Point(200, 200)               # begin, treated as (0, 0)
    pe = fitz.Point(400, 100)               # end, treated as (2*pi, 0)
        
    alfa = img.horizontal_angle(pb, pe)     # connection angle towards x-axis
    rad = abs(pe - pb)                      # distance of these points
    pe1 = pb + (rad, 0)                     # make corresp. horizontal end point
# =============================================================================
#   first draw a rectangle in which the functions graphs will later appear
# =============================================================================
    f = abs(pe - pb) * 0.5 / math.pi        # represents 1 unit
    rect = fitz.Rect(pb.x - 5, pb.y - f - 5, pe1.x + 5, pb.y + f + 5)
    img.drawRect(rect)                      # draw it
    morph = (pb, fitz.Matrix(math.degrees(-alfa)))
    img.finish(fill = yellow, morph = morph)  # rotate it around begin point
    
# =============================================================================
#   get all points for the sine function
# =============================================================================
    pntsin = bsinPoints(pb, pe1)            # only horizontal axis supported
    # therefore need rotate result points by angle alfa afterwards
    points = rot_points(pntsin, pb, alfa)
 
    for i in (0, 3, 6, 9):        # draw all 4 function segments
        img.drawBezier(points[i], points[i+1], points[i+2], points[i+3])
    
    img.finish(color = red, width = w, closePath = False)

# =============================================================================
#   same thing for cosine with "blue"
# =============================================================================
    pntcos = bcosPoints(pb, pe1)
    points = rot_points(pntcos, pb, alfa)
    
    for i in (0, 3, 6, 9):        # draw all 4 function segments
        img.drawBezier(points[i], points[i+1], points[i+2], points[i+3])
    img.finish(color = blue, width = w, closePath = False)

    img.drawLine(pb, pe)
    img.finish(width = w)         # draw x-axis (default color)
   
    # insert "sine" / "cosine" legend text
    r1 = fitz.Rect(rect.x0 + 2, rect.y1 - 20, rect.br)
    img.insertTextbox(r1, "sine", color = red, fontsize = 8, morph = morph)
    r2 = fitz.Rect(rect.x0 + 2, rect.y1 - 10, rect.br)
    img.insertTextbox(r2, "cosine", color = blue, fontsize = 8, morph = morph)
    img.commit()                  # commit with overlay = True
    
    doc.save("draw-sines.pdf")
