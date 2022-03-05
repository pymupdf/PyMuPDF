"""
* Check various construction methods of rects, points, matrices
* Check matrix inversions in variations
* Check algebra constructs
"""
import fitz


def test_rect():
    assert tuple(fitz.Rect()) == (0, 0, 0, 0)
    p1 = fitz.Point(10, 20)
    p2 = fitz.Point(100, 200)
    p3 = fitz.Point(150, 250)
    r = fitz.Rect(10, 20, 100, 200)
    r_tuple = tuple(r)
    assert tuple(fitz.Rect(p1, p2)) == r_tuple
    assert tuple(fitz.Rect(p1, 100, 200)) == r_tuple
    assert tuple(fitz.Rect(10, 20, p2)) == r_tuple
    assert tuple(r.include_point(p3)) == (10, 20, 150, 250)
    r = fitz.Rect(10, 20, 100, 200)
    assert tuple(r.include_rect((100, 200, 110, 220))) == (10, 20, 110, 220)
    r = fitz.Rect(10, 20, 100, 200)
    # include empty rect makes no change
    assert tuple(r.include_rect((0, 0, 0, 0))) == r_tuple
    # include invalid rect makes no change
    assert tuple(r.include_rect((1, 1, -1, -1))) == r_tuple
    r = fitz.Rect()
    for i in range(4):
        r[i] = i + 1
    assert r == fitz.Rect(1, 2, 3, 4)
    assert fitz.Rect() / 5 == fitz.Rect()
    assert fitz.Rect(1, 1, 2, 2) / fitz.Identity == fitz.Rect(1, 1, 2, 2)
    failed = False
    try:
        r = fitz.Rect(1)
    except:
        failed = True
    assert failed
    failed = False
    try:
        r = fitz.Rect(1, 2, 3, 4, 5)
    except:
        failed = True
    assert failed
    failed = False
    try:
        r = fitz.Rect((1, 2, 3, 4, 5))
    except:
        failed = True
    assert failed
    failed = False
    try:
        r = fitz.Rect(1, 2, 3, "x")
    except:
        failed = True
    assert failed
    failed = False
    try:
        r = fitz.Rect()
        r[5] = 1
    except:
        failed = True
    assert failed


def test_irect():
    p1 = fitz.Point(10, 20)
    p2 = fitz.Point(100, 200)
    p3 = fitz.Point(150, 250)
    r = fitz.IRect(10, 20, 100, 200)
    r_tuple = tuple(r)
    assert tuple(fitz.IRect(p1, p2)) == r_tuple
    assert tuple(fitz.IRect(p1, 100, 200)) == r_tuple
    assert tuple(fitz.IRect(10, 20, p2)) == r_tuple
    assert tuple(r.include_point(p3)) == (10, 20, 150, 250)
    r = fitz.IRect(10, 20, 100, 200)
    assert tuple(r.include_rect((100, 200, 110, 220))) == (10, 20, 110, 220)
    r = fitz.IRect(10, 20, 100, 200)
    # include empty rect makes no change
    assert tuple(r.include_rect((0, 0, 0, 0))) == r_tuple
    r = fitz.IRect()
    for i in range(4):
        r[i] = i + 1
    assert r == fitz.IRect(1, 2, 3, 4)

    failed = False
    try:
        r = fitz.IRect(1)
    except:
        failed = True
    assert failed
    failed = False
    try:
        r = fitz.IRect(1, 2, 3, 4, 5)
    except:
        failed = True
    assert failed
    failed = False
    try:
        r = fitz.IRect((1, 2, 3, 4, 5))
    except:
        failed = True
    assert failed
    failed = False
    try:
        r = fitz.IRect(1, 2, 3, "x")
    except:
        failed = True
    assert failed
    failed = False
    try:
        r = fitz.IRect()
        r[5] = 1
    except:
        failed = True
    assert failed


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
    assert tuple(fitz.Matrix()) == (0, 0, 0, 0, 0, 0)
    m45p = fitz.Matrix(45)
    m45m = fitz.Matrix(-45)
    m90 = fitz.Matrix(90)
    assert abs(m90 - m45p * m45p) < fitz.EPSILON
    assert abs(fitz.Identity - m45p * m45m) < fitz.EPSILON
    assert abs(m45p - ~m45m) < fitz.EPSILON
    assert fitz.Matrix(2, 3, 1) == fitz.Matrix(1, 3, 2, 1, 0, 0)
    m = fitz.Matrix(2, 3, 1)
    m.invert()
    assert abs(m * fitz.Matrix(2, 3, 1) - fitz.Identity) < fitz.EPSILON
    assert fitz.Matrix(1, 1).pretranslate(2, 3) == fitz.Matrix(1, 0, 0, 1, 2, 3)
    assert fitz.Matrix(1, 1).prescale(2, 3) == fitz.Matrix(2, 0, 0, 3, 0, 0)
    assert fitz.Matrix(1, 1).preshear(2, 3) == fitz.Matrix(1, 3, 2, 1, 0, 0)
    assert abs(fitz.Matrix(1, 1).prerotate(30) - fitz.Matrix(30)) < fitz.EPSILON
    small = 1e-6
    assert fitz.Matrix(1, 1).prerotate(90 + small) == fitz.Matrix(90)
    assert fitz.Matrix(1, 1).prerotate(180 + small) == fitz.Matrix(180)
    assert fitz.Matrix(1, 1).prerotate(270 + small) == fitz.Matrix(270)
    assert fitz.Matrix(1, 1).prerotate(small) == fitz.Matrix(0)
    assert fitz.Matrix(1, 1).concat(
        fitz.Matrix(1, 2), fitz.Matrix(3, 4)
    ) == fitz.Matrix(3, 0, 0, 8, 0, 0)
    assert fitz.Matrix(1, 2, 3, 4, 5, 6) / 1 == fitz.Matrix(1, 2, 3, 4, 5, 6)
    assert m[0] == m.a
    assert m[1] == m.b
    assert m[2] == m.c
    assert m[3] == m.d
    assert m[4] == m.e
    assert m[5] == m.f
    m = fitz.Matrix()
    for i in range(6):
        m[i] = i + 1
    assert m == fitz.Matrix(1, 2, 3, 4, 5, 6)
    failed = False
    try:
        m = fitz.Matrix(1, 2, 3)
    except:
        failed = True
    assert failed
    failed = False
    try:
        m = fitz.Matrix(1, 2, 3, 4, 5, 6, 7)
    except:
        failed = True
    assert failed

    failed = False
    try:
        m = fitz.Matrix((1, 2, 3, 4, 5, 6, 7))
    except:
        failed = True
    assert failed

    failed = False
    try:
        m = fitz.Matrix(1, 2, 3, 4, 5, "x")
    except:
        failed = True
    assert failed

    failed = False
    try:
        m = fitz.Matrix(1, 0, 1, 0, 1, 0)
        n = fitz.Matrix(1, 1) / m
    except:
        failed = True
    assert failed


def test_point():
    assert tuple(fitz.Point()) == (0, 0)
    assert fitz.Point(1, -1).unit == fitz.Point(5, -5).unit
    assert fitz.Point(-1, -1).abs_unit == fitz.Point(1, 1).unit
    assert fitz.Point(1, 1).distance_to(fitz.Point(1, 1)) == 0
    assert fitz.Point(1, 1).distance_to(fitz.Rect(1, 1, 2, 2)) == 0
    assert fitz.Point().distance_to((1, 1, 2, 2)) > 0
    failed = False
    try:
        p = fitz.Point(1, 2, 3)
    except:
        failed = True
    assert failed

    failed = False
    try:
        p = fitz.Point((1, 2, 3))
    except:
        failed = True
    assert failed

    failed = False
    try:
        p = fitz.Point(1, "x")
    except:
        failed = True
    assert failed

    failed = False
    try:
        p = fitz.Point()
        p[3] = 1
    except:
        failed = True
    assert failed


def test_algebra():
    p = fitz.Point(1, 2)
    m = fitz.Matrix(1, 2, 3, 4, 5, 6)
    r = fitz.Rect(1, 1, 2, 2)
    assert p + p == p * 2
    assert p - p == fitz.Point()
    assert m + m == m * 2
    assert m - m == fitz.Matrix()
    assert r + r == r * 2
    assert r - r == fitz.Rect()
    assert p + 5 == fitz.Point(6, 7)
    assert m + 5 == fitz.Matrix(6, 7, 8, 9, 10, 11)
    assert r.tl in r
    assert r.tr not in r
    assert r.br not in r
    assert r.bl not in r
    assert p * m == fitz.Point(12, 16)
    assert r * m == fitz.Rect(9, 12, 13, 18)
    assert (fitz.Rect(1, 1, 2, 2) & fitz.Rect(2, 2, 3, 3)).is_empty
    assert not fitz.Rect(1, 1, 2, 2).intersects((2, 2, 4, 4))
    failed = False
    try:
        x = m + p
    except:
        failed = True
    assert failed
    failed = False
    try:
        x = m + r
    except:
        failed = True
    assert failed
    failed = False
    try:
        x = p + r
    except:
        failed = True
    assert failed
    failed = False
    try:
        x = r + m
    except:
        failed = True
    assert failed
    assert m not in r


def test_quad():
    r = fitz.Rect(10, 10, 20, 20)
    q = r.quad
    assert q.is_rectangular
    assert not q.is_empty
    assert q.is_convex
    q *= fitz.Matrix(1, 1).preshear(2, 3)
    assert not q.is_rectangular
    assert not q.is_empty
    assert q.is_convex
    assert r.tl not in q
    assert r not in q
    assert r.quad not in q
    failed = False
    try:
        q[5] = fitz.Point()
    except:
        failed = True
    assert failed

    failed = False
    try:
        q /= (1, 0, 1, 0, 1, 0)
    except:
        failed = True
    assert failed


def test_pageboxes():
    """Tests concerning ArtBox, TrimBox, BleedBox."""
    doc = fitz.open()
    page = doc.new_page()
    assert page.cropbox == page.artbox == page.bleedbox == page.trimbox
    rect_methods = (
        page.set_cropbox,
        page.set_artbox,
        page.set_bleedbox,
        page.set_trimbox,
    )
    keys = ("CropBox", "ArtBox", "BleedBox", "TrimBox")
    rect = fitz.Rect(100, 200, 400, 700)
    for f in rect_methods:
        f(rect)
    for key in keys:
        assert doc.xref_get_key(page.xref, key) == ("array", "[100 142 400 642]")
    assert page.cropbox == page.artbox == page.bleedbox == page.trimbox
