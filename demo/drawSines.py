import fitz, math
"""
Created on 2017-08-17

@author: (c) 2017, Jorj X. McKie

License: GNU GPL V3

PyMuPDF Demo Program
---------------------
Create a PDF with drawings of the sine and cosine functions using PyMuPDF.
Depending on how start and end points are located with respect to each
other, horizontal or vertical drawings result.
The vertical case can obviously be used for creating inverse function
(arcus sine / cosine) graphs.

The function graphs are pieced together in 90 degree parts, for which Bezier
curves are used.

Note that the 'alfa' and 'beta' constants represent values for use as 
Bezier control points like so:
x-values (written in degrees): [0, 30, 60, 90]
corresponding y-values:        [0, alfa, beta, 1]

These values have been calculated by the scipy.interpolate.splrep() method.
They provide an excellent spline approximation of the sine / cosine
functions - please look at SciPy documentation for background.

"""
def bsinPoints(pb, pe):
    """Return Bezier control points, when pb and pe stand for a full period
    from (0,0) to (2*pi, 0), respectively, in the user's coordinate system.
    The returned points can be used to draw up to four Bezier curves for
    the complete sine function graph from 0 to 2*pi.
    """
    f = abs(pe - pb) * 0.5 / math.pi     # represents the unit
    alfa = 5.34295228e-01
    beta = 1.01474288e+00
    # adjust for either horizontal or vertical
    if pb.y == pe.y:
        y_ampl = (0, f)
        y_alfa = (0, f * alfa)
        y_beta = (0, f * beta)
    elif pb.x == pe.x:
        y_ampl = (-f, 0)
        y_alfa = (-f * alfa, 0)
        y_beta = (-f * beta, 0)
    else:
        raise ValueError("can only draw horizontal or vertical")

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
    the complete cosine function graph from 0 to 2*pi.
    """
    f = abs(pe - pb) * 0.5 / math.pi     # represents the unit
    alfa = 5.34295228e-01
    beta = 1.01474288e+00
    # adjust for either horizontal or vertical
    if pb.y == pe.y:
        y_ampl = (0, f)
        y_alfa = (0, f * alfa)
        y_beta = (0, f * beta)
    elif pb.x == pe.x:
        y_ampl = (-f, 0)
        y_alfa = (-f * alfa, 0)
        y_beta = (-f * beta, 0)
    else:
        raise ValueError("can only draw horizontal or vertical")
        
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

if __name__ == "__main__":
    from fitz.utils import getColor
    doc = fitz.open()
    page = doc.newPage()
    red    = getColor("red")      # line color for sine
    blue   = getColor("blue")     # line color for cosine
    yellow = getColor("py_color") # background color
    w = 0.3                  # line width
    #--------------------------------------------------------------------------
    # define end points of x axis we want to use as 0 and 2*pi
    # these may be oriented horizontally or vertically
    #--------------------------------------------------------------------------
    pb = fitz.Point(50, 200)      # example values for
    pe = fitz.Point(550, 200)     # horizontal drawing
    #pb = fitz.Point(300, 100)     # example values for
    #pe = fitz.Point(300, 600)     # vertical drawing
    page.drawLine(pb, pe, width = w)   # draw x-axis (default color)

    # get all points for the sine function
    pnt = bsinPoints(pb, pe)
    # draw some points for better orientation
    for i in (0, 3, 6, 9, 12):
        page.drawCircle(pnt[i], 1, color = red)
    # now draw a complete sine graph period in "red"
    for i in (0, 3, 6, 9):        # draw all 4 function segments
        page.drawBezier(pnt[i], pnt[i+1], pnt[i+2], pnt[i+3],
                        color = red, width = w)

    # same thing for cosine with "blue"
    pnt = bcosPoints(pb, pe)
    for i in (0, 3, 6, 9, 12):
        page.drawCircle(pnt[i], 1, color = blue)
    for i in (0, 3, 6, 9):        # draw all 4 function segments
        page.drawBezier(pnt[i], pnt[i+1], pnt[i+2], pnt[i+3],
                        color = blue, width = w)

    # finally draw a rectangle around everything (in background):
    rect = fitz.Rect(pb, pb)      # create smallest rectangle
    for p in pnt:                 # containing all the points
        rect = rect | p
    # leave 5 px space around the picture
    rect.x0 -= 5
    rect.y0 -= 5
    rect.x1 += 5
    rect.y1 += 5
    page.drawRect(rect, width = w, fill = yellow, overlay = False)
    doc.save("drawSines.pdf")
