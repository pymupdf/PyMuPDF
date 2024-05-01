"""
* Check various construction methods of rects, points, matrices
* Check matrix inversions in variations
* Check algebra constructs
"""
import os

import pymupdf


def test_rect():
    assert tuple(pymupdf.Rect()) == (0, 0, 0, 0)
    if hasattr(pymupdf, 'mupdf'):
        assert tuple(pymupdf.Rect(y0=12)) == (0, 12, 0, 0)
        assert tuple(pymupdf.Rect(10, 20, 100, 200, x1=12)) == (10, 20, 12, 200)
    p1 = pymupdf.Point(10, 20)
    p2 = pymupdf.Point(100, 200)
    p3 = pymupdf.Point(150, 250)
    r = pymupdf.Rect(10, 20, 100, 200)
    r_tuple = tuple(r)
    assert tuple(pymupdf.Rect(p1, p2)) == r_tuple
    assert tuple(pymupdf.Rect(p1, 100, 200)) == r_tuple
    assert tuple(pymupdf.Rect(10, 20, p2)) == r_tuple
    assert tuple(r.include_point(p3)) == (10, 20, 150, 250)
    r = pymupdf.Rect(10, 20, 100, 200)
    assert tuple(r.include_rect((100, 200, 110, 220))) == (10, 20, 110, 220)
    r = pymupdf.Rect(10, 20, 100, 200)
    # include empty rect makes no change
    assert tuple(r.include_rect((0, 0, 0, 0))) == r_tuple
    # include invalid rect makes no change
    assert tuple(r.include_rect((1, 1, -1, -1))) == r_tuple
    r = pymupdf.Rect()
    for i in range(4):
        r[i] = i + 1
    assert r == pymupdf.Rect(1, 2, 3, 4)
    assert pymupdf.Rect() / 5 == pymupdf.Rect()
    assert pymupdf.Rect(1, 1, 2, 2) / pymupdf.Identity == pymupdf.Rect(1, 1, 2, 2)
    failed = False
    try:
        r = pymupdf.Rect(1)
    except:
        failed = True
    assert failed
    failed = False
    try:
        r = pymupdf.Rect(1, 2, 3, 4, 5)
    except:
        failed = True
    assert failed
    failed = False
    try:
        r = pymupdf.Rect((1, 2, 3, 4, 5))
    except:
        failed = True
    assert failed
    failed = False
    try:
        r = pymupdf.Rect(1, 2, 3, "x")
    except:
        failed = True
    assert failed
    failed = False
    try:
        r = pymupdf.Rect()
        r[5] = 1
    except:
        failed = True
    assert failed


def test_irect():
    p1 = pymupdf.Point(10, 20)
    p2 = pymupdf.Point(100, 200)
    p3 = pymupdf.Point(150, 250)
    r = pymupdf.IRect(10, 20, 100, 200)
    r_tuple = tuple(r)
    assert tuple(pymupdf.IRect(p1, p2)) == r_tuple
    assert tuple(pymupdf.IRect(p1, 100, 200)) == r_tuple
    assert tuple(pymupdf.IRect(10, 20, p2)) == r_tuple
    assert tuple(r.include_point(p3)) == (10, 20, 150, 250)
    r = pymupdf.IRect(10, 20, 100, 200)
    assert tuple(r.include_rect((100, 200, 110, 220))) == (10, 20, 110, 220)
    r = pymupdf.IRect(10, 20, 100, 200)
    # include empty rect makes no change
    assert tuple(r.include_rect((0, 0, 0, 0))) == r_tuple
    r = pymupdf.IRect()
    for i in range(4):
        r[i] = i + 1
    assert r == pymupdf.IRect(1, 2, 3, 4)

    failed = False
    try:
        r = pymupdf.IRect(1)
    except:
        failed = True
    assert failed
    failed = False
    try:
        r = pymupdf.IRect(1, 2, 3, 4, 5)
    except:
        failed = True
    assert failed
    failed = False
    try:
        r = pymupdf.IRect((1, 2, 3, 4, 5))
    except:
        failed = True
    assert failed
    failed = False
    try:
        r = pymupdf.IRect(1, 2, 3, "x")
    except:
        failed = True
    assert failed
    failed = False
    try:
        r = pymupdf.IRect()
        r[5] = 1
    except:
        failed = True
    assert failed


def test_inversion():
    alpha = 255
    m1 = pymupdf.Matrix(alpha)
    m2 = pymupdf.Matrix(-alpha)
    m3 = m1 * m2  # should equal identity matrix
    assert abs(m3 - pymupdf.Identity) < pymupdf.EPSILON
    m = pymupdf.Matrix(1, 0, 1, 0, 1, 0)  # not invertible!
    # inverted matrix must be zero
    assert ~m == pymupdf.Matrix()


def test_matrix():
    assert tuple(pymupdf.Matrix()) == (0, 0, 0, 0, 0, 0)
    assert tuple(pymupdf.Matrix(90)) == (0, 1, -1, 0, 0, 0)
    if hasattr(pymupdf, 'mupdf'):
        assert tuple(pymupdf.Matrix(c=1)) == (0, 0, 1, 0, 0, 0)
        assert tuple(pymupdf.Matrix(90, e=5)) == (0, 1, -1, 0, 5, 0)
    m45p = pymupdf.Matrix(45)
    m45m = pymupdf.Matrix(-45)
    m90 = pymupdf.Matrix(90)
    assert abs(m90 - m45p * m45p) < pymupdf.EPSILON
    assert abs(pymupdf.Identity - m45p * m45m) < pymupdf.EPSILON
    assert abs(m45p - ~m45m) < pymupdf.EPSILON
    assert pymupdf.Matrix(2, 3, 1) == pymupdf.Matrix(1, 3, 2, 1, 0, 0)
    m = pymupdf.Matrix(2, 3, 1)
    m.invert()
    assert abs(m * pymupdf.Matrix(2, 3, 1) - pymupdf.Identity) < pymupdf.EPSILON
    assert pymupdf.Matrix(1, 1).pretranslate(2, 3) == pymupdf.Matrix(1, 0, 0, 1, 2, 3)
    assert pymupdf.Matrix(1, 1).prescale(2, 3) == pymupdf.Matrix(2, 0, 0, 3, 0, 0)
    assert pymupdf.Matrix(1, 1).preshear(2, 3) == pymupdf.Matrix(1, 3, 2, 1, 0, 0)
    assert abs(pymupdf.Matrix(1, 1).prerotate(30) - pymupdf.Matrix(30)) < pymupdf.EPSILON
    small = 1e-6
    assert pymupdf.Matrix(1, 1).prerotate(90 + small) == pymupdf.Matrix(90)
    assert pymupdf.Matrix(1, 1).prerotate(180 + small) == pymupdf.Matrix(180)
    assert pymupdf.Matrix(1, 1).prerotate(270 + small) == pymupdf.Matrix(270)
    assert pymupdf.Matrix(1, 1).prerotate(small) == pymupdf.Matrix(0)
    assert pymupdf.Matrix(1, 1).concat(
        pymupdf.Matrix(1, 2), pymupdf.Matrix(3, 4)
    ) == pymupdf.Matrix(3, 0, 0, 8, 0, 0)
    assert pymupdf.Matrix(1, 2, 3, 4, 5, 6) / 1 == pymupdf.Matrix(1, 2, 3, 4, 5, 6)
    assert m[0] == m.a
    assert m[1] == m.b
    assert m[2] == m.c
    assert m[3] == m.d
    assert m[4] == m.e
    assert m[5] == m.f
    m = pymupdf.Matrix()
    for i in range(6):
        m[i] = i + 1
    assert m == pymupdf.Matrix(1, 2, 3, 4, 5, 6)
    failed = False
    try:
        m = pymupdf.Matrix(1, 2, 3)
    except:
        failed = True
    assert failed
    failed = False
    try:
        m = pymupdf.Matrix(1, 2, 3, 4, 5, 6, 7)
    except:
        failed = True
    assert failed

    failed = False
    try:
        m = pymupdf.Matrix((1, 2, 3, 4, 5, 6, 7))
    except:
        failed = True
    assert failed

    failed = False
    try:
        m = pymupdf.Matrix(1, 2, 3, 4, 5, "x")
    except:
        failed = True
    assert failed

    failed = False
    try:
        m = pymupdf.Matrix(1, 0, 1, 0, 1, 0)
        n = pymupdf.Matrix(1, 1) / m
    except:
        failed = True
    assert failed


def test_point():
    assert tuple(pymupdf.Point()) == (0, 0)
    assert pymupdf.Point(1, -1).unit == pymupdf.Point(5, -5).unit
    assert pymupdf.Point(-1, -1).abs_unit == pymupdf.Point(1, 1).unit
    assert pymupdf.Point(1, 1).distance_to(pymupdf.Point(1, 1)) == 0
    assert pymupdf.Point(1, 1).distance_to(pymupdf.Rect(1, 1, 2, 2)) == 0
    assert pymupdf.Point().distance_to((1, 1, 2, 2)) > 0
    failed = False
    try:
        p = pymupdf.Point(1, 2, 3)
    except:
        failed = True
    assert failed

    failed = False
    try:
        p = pymupdf.Point((1, 2, 3))
    except:
        failed = True
    assert failed

    failed = False
    try:
        p = pymupdf.Point(1, "x")
    except:
        failed = True
    assert failed

    failed = False
    try:
        p = pymupdf.Point()
        p[3] = 1
    except:
        failed = True
    assert failed


def test_algebra():
    p = pymupdf.Point(1, 2)
    m = pymupdf.Matrix(1, 2, 3, 4, 5, 6)
    r = pymupdf.Rect(1, 1, 2, 2)
    assert p + p == p * 2
    assert p - p == pymupdf.Point()
    assert m + m == m * 2
    assert m - m == pymupdf.Matrix()
    assert r + r == r * 2
    assert r - r == pymupdf.Rect()
    assert p + 5 == pymupdf.Point(6, 7)
    assert m + 5 == pymupdf.Matrix(6, 7, 8, 9, 10, 11)
    assert r.tl in r
    assert r.tr not in r
    assert r.br not in r
    assert r.bl not in r
    assert p * m == pymupdf.Point(12, 16)
    assert r * m == pymupdf.Rect(9, 12, 13, 18)
    assert (pymupdf.Rect(1, 1, 2, 2) & pymupdf.Rect(2, 2, 3, 3)).is_empty
    assert not pymupdf.Rect(1, 1, 2, 2).intersects((2, 2, 4, 4))
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
    r = pymupdf.Rect(10, 10, 20, 20)
    q = r.quad
    assert q.is_rectangular
    assert not q.is_empty
    assert q.is_convex
    q *= pymupdf.Matrix(1, 1).preshear(2, 3)
    assert not q.is_rectangular
    assert not q.is_empty
    assert q.is_convex
    assert r.tl not in q
    assert r not in q
    assert r.quad not in q
    failed = False
    try:
        q[5] = pymupdf.Point()
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
    doc = pymupdf.open()
    page = doc.new_page()
    assert page.cropbox == page.artbox == page.bleedbox == page.trimbox
    rect_methods = (
        page.set_cropbox,
        page.set_artbox,
        page.set_bleedbox,
        page.set_trimbox,
    )
    keys = ("CropBox", "ArtBox", "BleedBox", "TrimBox")
    rect = pymupdf.Rect(100, 200, 400, 700)
    for f in rect_methods:
        f(rect)
    for key in keys:
        assert doc.xref_get_key(page.xref, key) == ("array", "[100 142 400 642]")
    assert page.cropbox == page.artbox == page.bleedbox == page.trimbox

def test_3163():
    b = {'number': 0, 'type': 0, 'bbox': (403.3577880859375, 330.8871765136719, 541.2731323242188, 349.5766296386719), 'lines': [{'spans': [{'size': 14.0, 'flags': 4, 'font': 'SFHello-Medium', 'color': 1907995, 'ascender': 1.07373046875, 'descender': -0.26123046875, 'text': 'Inclusion and diversity', 'origin': (403.3577880859375, 345.9194030761719), 'bbox': (403.3577880859375, 330.8871765136719, 541.2731323242188, 349.5766296386719)}], 'wmode': 0, 'dir': (1.0, 0.0), 'bbox': (403.3577880859375, 330.8871765136719, 541.2731323242188, 349.5766296386719)}]}
    bbox = pymupdf.IRect(b["bbox"])

def test_3182():
    pix = pymupdf.Pixmap(os.path.abspath(f'{__file__}/../../tests/resources/img-transparent.png'))
    rect = pymupdf.Rect(0, 0, 100, 100)
    pix.invert_irect(rect)
