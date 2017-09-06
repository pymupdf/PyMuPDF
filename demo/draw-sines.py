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

Note that the 'alfa' and 'beta' constants below represent values for use as 
Bezier control points like so:
x-values (deg): [0, 30, 60, 90]
y-values:       [0, alfa, beta, 1]

These values have been calculated by the scipy.interpolate.splrep() method.
They provide an excellent spline approximation of the sine / cosine
functions - please see the SciPy documentation for background.

"""
def bsinPoints(pb, pe):
    """Return Bezier control points, when pb and pe stand for a full period
    from (0,0) to (2*pi, 0), respectively, in the user's coordinate system.
    The returned points can be used to draw up to four Bezier curves for
    the complete phase of the sine function graph from 0 to 2*pi.
    """
    f = abs(pe - pb) * 0.5 / math.pi     # represents the unit
    alfa = 5.34295228e-01
    beta = 1.01474288e+00

    y_ampl = (0, f)
    y_alfa = (0, f * alfa)
    y_beta = (0, f * beta)

    p0 = pb
    p4 = pe
    p1 = pb + (pe - pb)*0.25 - y_ampl
    p2 = pb + (pe - pb)*0.5
    p3 = pb + (pe - pb)*0.75 + y_ampl
    k1 = pb + (pe - pb)*(1./12.)  - y_alfa
    k2 = pb + (pe - pb)*(2./12.)  - y_beta
    k3 = pb + (pe - pb)*(4./12.)  - y_beta
    k4 = pb + (pe - pb)*(5./12.)  - y_alfa
    k5 = pb + (pe - pb)*(7./12.)  + y_alfa
    k6 = pb + (pe - pb)*(8./12.)  + y_beta
    k7 = pb + (pe - pb)*(10./12.) + y_beta
    k8 = pb + (pe - pb)*(11./12.) + y_alfa
    return p0, k1, k2, p1, k3, k4, p2, k5, k6, p3, k7, k8, p4

def bcosPoints(pb, pe):
    """Return Bezier control points, when pb and pe stand for a full period
    from (0,0) to (2*pi, 0), respectively, in the user's coordinate system.
    The returned points can be used to draw up to four Bezier curves for
    the complete phase of the cosine function graph from 0 to 2*pi.
    """
    f = abs(pe - pb) * 0.5 / math.pi     # represents the unit
    alfa = 5.34295228e-01
    beta = 1.01474288e+00
    y_ampl = (0, f)
    y_alfa = (0, f * alfa)
    y_beta = (0, f * beta)
        
    p0 = pb - y_ampl
    p4 = pe - y_ampl
    p1 = pb + (pe - pb)*0.25
    p2 = pb + (pe - pb)*0.5 + y_ampl
    p3 = pb + (pe - pb)*0.75
    k1 = pb + (pe - pb)*(1./12.)  - y_beta
    k2 = pb + (pe - pb)*(2./12.)  - y_alfa
    k3 = pb + (pe - pb)*(4./12.)  + y_alfa
    k4 = pb + (pe - pb)*(5./12.)  + y_beta
    k5 = pb + (pe - pb)*(7./12.)  + y_beta
    k6 = pb + (pe - pb)*(8./12.)  + y_alfa
    k7 = pb + (pe - pb)*(10./12.) - y_alfa
    k8 = pb + (pe - pb)*(11./12.) - y_beta
    return p0, k1, k2, p1, k3, k4, p2, k5, k6, p3, k7, k8, p4

def rot_points(pnts, pb, alfa):
    """Rotate a list of points by an angle alfa around pivotal point pb.
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
    pb = fitz.Point(200, 200)               # begin, taken as (0, 0)
    pe = fitz.Point(400, 100)               # end, taken as (2*pi, 0)
        
    alfa = img.horizontal_angle(pb, pe)     # angle towards x-axis
    calfa = math.cos(alfa)                  # need these ...
    salfa = math.sin(alfa)                  # ... values later
    rad = abs(pe - pb)
    pe1 = pb + (rad, 0)                     # make corresp. horizontal end point
# =============================================================================
#   background-draw a rectangle in which the functions graphs will appear
# =============================================================================
    f = abs(pe - pb) * 0.5 / math.pi        # represents 1 unit
    rect = fitz.Rect(pb.x - 5, pb.y - f - 5, pe1.x + 5, pb.y + f + 5)
    img.drawRect(rect)
    img.finish(fill = yellow, morph = (pb, fitz.Matrix(math.degrees(-alfa))))
    
# =============================================================================
#   get all points for the sine function
# =============================================================================
    pntsin = bsinPoints(pb, pe1)
    # rotate points by angle alfa
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

    img.commit()
    doc.save("draw-sines.pdf")
