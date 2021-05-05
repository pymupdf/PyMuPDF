"""
* Check various construction methods of rectangles
* Check matrix inversions in variations
"""
import fitz


def test_rectangles():
    p1 = fitz.Point(10, 20)
    p2 = fitz.Point(100, 200)
    p3 = fitz.Point(150, 250)
    r = fitz.Rect(10, 20, 100, 200)
    r_tuple = tuple(r)
    assert tuple(fitz.Rect(p1, p2)) == r_tuple
    assert tuple(fitz.Rect(p1, 100, 200)) == r_tuple
    assert tuple(fitz.Rect(10, 20, p2)) == r_tuple
    assert tuple(r.includePoint(p3)) == (10, 20, 150, 250)
    r = fitz.Rect(10, 20, 100, 200)
    assert tuple(r.includeRect((100, 200, 110, 220))) == (10, 20, 110, 220)
    r = fitz.Rect(10, 20, 100, 200)
    # include empty rect makes no change
    assert tuple(r.includeRect((0, 0, 0, 0))) == r_tuple
    # include infinite rect delivers infinite rect
    assert tuple(r.includeRect((1, 1, -1, -1))) == (1, 1, -1, -1)


def test_inversion():
    alpha = 255
    m1 = fitz.Matrix(alpha)
    m2 = fitz.Matrix(-alpha)
    m3 = m1 * m2  # should equal identity matrix
    assert abs(m3 - fitz.Identity) < fitz.EPSILON
    m = fitz.Matrix(1, 0, 1, 0, 1, 0)  # not invertible!
    # inverted matrix must be zero
    assert ~m == fitz.Matrix()


def test_matrix():
    m45p = fitz.Matrix(45)
    m45m = fitz.Matrix(-45)
    m90 = fitz.Matrix(90)
    assert abs(m90 - m45p * m45p) < fitz.EPSILON
    assert abs(fitz.Identity - m45p * m45m) < fitz.EPSILON
    assert abs(m45p - ~m45m) < fitz.EPSILON
