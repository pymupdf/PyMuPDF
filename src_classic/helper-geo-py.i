%pythoncode %{

# ------------------------------------------------------------------------
# Copyright 2020-2022, Harald Lieder, mailto:harald.lieder@outlook.com
# License: GNU AFFERO GPL 3.0, https://www.gnu.org/licenses/agpl-3.0.html
#
# Part of "PyMuPDF", a Python binding for "MuPDF" (http://mupdf.com), a
# lightweight PDF, XPS, and E-book viewer, renderer and toolkit which is
# maintained and developed by Artifex Software, Inc. https://artifex.com.
# ------------------------------------------------------------------------

# largest 32bit integers surviving C float conversion roundtrips
# used by MuPDF to define infinite rectangles
FZ_MIN_INF_RECT = -0x80000000
FZ_MAX_INF_RECT = 0x7fffff80


class Matrix(object):
    """Matrix() - all zeros
    Matrix(a, b, c, d, e, f)
    Matrix(zoom-x, zoom-y) - zoom
    Matrix(shear-x, shear-y, 1) - shear
    Matrix(degree) - rotate
    Matrix(Matrix) - new copy
    Matrix(sequence) - from 'sequence'"""
    def __init__(self, *args):
        if not args:
            self.a = self.b = self.c = self.d = self.e = self.f = 0.0
            return None
        if len(args) > 6:
            raise ValueError("Matrix: bad seq len")
        if len(args) == 6:  # 6 numbers
            self.a, self.b, self.c, self.d, self.e, self.f = map(float, args)
            return None
        if len(args) == 1:  # either an angle or a sequ
            if hasattr(args[0], "__float__"):
                theta = math.radians(args[0])
                c = round(math.cos(theta), 12)
                s = round(math.sin(theta), 12)
                self.a = self.d = c
                self.b = s
                self.c = -s
                self.e = self.f = 0.0
                return None
            else:
                self.a, self.b, self.c, self.d, self.e, self.f = map(float, args[0])
                return None
        if len(args) == 2 or len(args) == 3 and args[2] == 0:
            self.a, self.b, self.c, self.d, self.e, self.f = float(args[0]), \
                0.0, 0.0, float(args[1]), 0.0, 0.0
            return None
        if len(args) == 3 and args[2] == 1:
            self.a, self.b, self.c, self.d, self.e, self.f = 1.0, \
                float(args[1]), float(args[0]), 1.0, 0.0, 0.0
            return None
        raise ValueError("Matrix: bad args")

    def invert(self, src=None):
        """Calculate the inverted matrix. Return 0 if successful and replace
        current one. Else return 1 and do nothing.
        """
        if src is None:
            dst = util_invert_matrix(self)
        else:
            dst = util_invert_matrix(src)
        if dst[0] == 1:
            return 1
        self.a, self.b, self.c, self.d, self.e, self.f = dst[1]
        return 0

    def pretranslate(self, tx, ty):
        """Calculate pre translation and replace current matrix."""
        tx = float(tx)
        ty = float(ty)
        self.e += tx * self.a + ty * self.c
        self.f += tx * self.b + ty * self.d
        return self

    def prescale(self, sx, sy):
        """Calculate pre scaling and replace current matrix."""
        sx = float(sx)
        sy = float(sy)
        self.a *= sx
        self.b *= sx
        self.c *= sy
        self.d *= sy
        return self

    def preshear(self, h, v):
        """Calculate pre shearing and replace current matrix."""
        h = float(h)
        v = float(v)
        a, b = self.a, self.b
        self.a += v * self.c
        self.b += v * self.d
        self.c += h * a
        self.d += h * b
        return self

    def prerotate(self, theta):
        """Calculate pre rotation and replace current matrix."""
        theta = float(theta)
        while theta < 0: theta += 360
        while theta >= 360: theta -= 360
        if abs(0 - theta) < EPSILON:
            pass

        elif abs(90.0 - theta) < EPSILON:
            a = self.a
            b = self.b
            self.a = self.c
            self.b = self.d
            self.c = -a
            self.d = -b

        elif abs(180.0 - theta) < EPSILON:
            self.a = -self.a
            self.b = -self.b
            self.c = -self.c
            self.d = -self.d

        elif abs(270.0 - theta) < EPSILON:
            a = self.a
            b = self.b
            self.a = -self.c
            self.b = -self.d
            self.c = a
            self.d = b

        else:
            rad = math.radians(theta)
            s = math.sin(rad)
            c = math.cos(rad)
            a = self.a
            b = self.b
            self.a = c * a + s * self.c
            self.b = c * b + s * self.d
            self.c =-s * a + c * self.c
            self.d =-s * b + c * self.d

        return self

    def concat(self, one, two):
        """Multiply two matrices and replace current one."""
        if not len(one) == len(two) == 6:
            raise ValueError("Matrix: bad seq len")
        self.a, self.b, self.c, self.d, self.e, self.f = util_concat_matrix(one, two)
        return self

    def __getitem__(self, i):
        return (self.a, self.b, self.c, self.d, self.e, self.f)[i]

    def __setitem__(self, i, v):
        v = float(v)
        if   i == 0: self.a = v
        elif i == 1: self.b = v
        elif i == 2: self.c = v
        elif i == 3: self.d = v
        elif i == 4: self.e = v
        elif i == 5: self.f = v
        else:
            raise IndexError("index out of range")
        return

    def __len__(self):
        return 6

    def __repr__(self):
        return "Matrix" + str(tuple(self))

    def __invert__(self):
        """Calculate inverted matrix."""
        m1 = Matrix()
        m1.invert(self)
        return m1
    __inv__ = __invert__

    def __mul__(self, m):
        if hasattr(m, "__float__"):
            return Matrix(self.a * m, self.b * m, self.c * m,
                          self.d * m, self.e * m, self.f * m)
        m1 = Matrix(1,1)
        return m1.concat(self, m)

    def __truediv__(self, m):
        if hasattr(m, "__float__"):
            return Matrix(self.a * 1./m, self.b * 1./m, self.c * 1./m,
                          self.d * 1./m, self.e * 1./m, self.f * 1./m)
        m1 = util_invert_matrix(m)[1]
        if not m1:
            raise ZeroDivisionError("matrix not invertible")
        m2 = Matrix(1,1)
        return m2.concat(self, m1)
    __div__ = __truediv__

    def __add__(self, m):
        if hasattr(m, "__float__"):
            return Matrix(self.a + m, self.b + m, self.c + m,
                          self.d + m, self.e + m, self.f + m)
        if len(m) != 6:
            raise ValueError("Matrix: bad seq len")
        return Matrix(self.a + m[0], self.b + m[1], self.c + m[2],
                          self.d + m[3], self.e + m[4], self.f + m[5])

    def __sub__(self, m):
        if hasattr(m, "__float__"):
            return Matrix(self.a - m, self.b - m, self.c - m,
                          self.d - m, self.e - m, self.f - m)
        if len(m) != 6:
            raise ValueError("Matrix: bad seq len")
        return Matrix(self.a - m[0], self.b - m[1], self.c - m[2],
                          self.d - m[3], self.e - m[4], self.f - m[5])

    def __pos__(self):
        return Matrix(self)

    def __neg__(self):
        return Matrix(-self.a, -self.b, -self.c, -self.d, -self.e, -self.f)

    def __bool__(self):
        return not (max(self) == min(self) == 0)

    def __nonzero__(self):
        return not (max(self) == min(self) == 0)

    def __eq__(self, mat):
        if not hasattr(mat, "__len__"):
            return False
        return len(mat) == 6 and bool(self - mat) is False

    def __abs__(self):
        return math.sqrt(sum([c*c for c in self]))

    norm = __abs__

    @property
    def is_rectilinear(self):
        """True if rectangles are mapped to rectangles."""
        return (abs(self.b) < EPSILON and abs(self.c) < EPSILON) or \
            (abs(self.a) < EPSILON and abs(self.d) < EPSILON);


class IdentityMatrix(Matrix):
    """Identity matrix [1, 0, 0, 1, 0, 0]"""
    def __init__(self):
        Matrix.__init__(self, 1.0, 1.0)
    def __setattr__(self, name, value):
        if name in "ad":
            self.__dict__[name] = 1.0
        elif name in "bcef":
            self.__dict__[name] = 0.0
        else:
            self.__dict__[name] = value

    def checkargs(*args):
        raise NotImplementedError("Identity is readonly")

    prerotate    = checkargs
    preshear     = checkargs
    prescale     = checkargs
    pretranslate = checkargs
    concat       = checkargs
    invert       = checkargs

    def __repr__(self):
        return "IdentityMatrix(1.0, 0.0, 0.0, 1.0, 0.0, 0.0)"

    def __hash__(self):
        return hash((1,0,0,1,0,0))


Identity = IdentityMatrix()

class Point(object):
    """Point() - all zeros\nPoint(x, y)\nPoint(Point) - new copy\nPoint(sequence) - from 'sequence'"""
    def __init__(self, *args):
        if not args:
            self.x = 0.0
            self.y = 0.0
            return None

        if len(args) > 2:
            raise ValueError("Point: bad seq len")
        if len(args) == 2:
            self.x = float(args[0])
            self.y = float(args[1])
            return None
        if len(args) == 1:
            l = args[0]
            if hasattr(l, "__getitem__") is False:
                raise ValueError("Point: bad args")
            if len(l) != 2:
                raise ValueError("Point: bad seq len")
            self.x = float(l[0])
            self.y = float(l[1])
            return None
        raise ValueError("Point: bad args")

    def transform(self, m):
        """Replace point by its transformation with matrix-like m."""
        if len(m) != 6:
            raise ValueError("Matrix: bad seq len")
        self.x, self.y = util_transform_point(self, m)
        return self

    @property
    def unit(self):
        """Unit vector of the point."""
        s = self.x * self.x + self.y * self.y
        if s < EPSILON:
            return Point(0,0)
        s = math.sqrt(s)
        return Point(self.x / s, self.y / s)

    @property
    def abs_unit(self):
        """Unit vector with positive coordinates."""
        s = self.x * self.x + self.y * self.y
        if s < EPSILON:
            return Point(0,0)
        s = math.sqrt(s)
        return Point(abs(self.x) / s, abs(self.y) / s)

    def distance_to(self, *args):
        """Return distance to rectangle or another point."""
        if not len(args) > 0:
            raise ValueError("at least one parameter must be given")

        x = args[0]
        if len(x) == 2:
            x = Point(x)
        elif len(x) == 4:
            x = Rect(x)
        else:
            raise ValueError("arg1 must be point-like or rect-like")

        if len(args) > 1:
            unit = args[1]
        else:
            unit = "px"
        u = {"px": (1.,1.), "in": (1.,72.), "cm": (2.54, 72.),
             "mm": (25.4, 72.)}
        f = u[unit][0] / u[unit][1]

        if type(x) is Point:
            return abs(self - x) * f

        # from here on, x is a rectangle
        # as a safeguard, make a finite copy of it
        r = Rect(x.top_left, x.top_left)
        r = r | x.bottom_right
        if self in r:
            return 0.0
        if self.x > r.x1:
            if self.y >= r.y1:
                return self.distance_to(r.bottom_right, unit)
            elif self.y <= r.y0:
                return self.distance_to(r.top_right, unit)
            else:
                return (self.x - r.x1) * f
        elif r.x0 <= self.x <= r.x1:
            if self.y >= r.y1:
                return (self.y - r.y1) * f
            else:
                return (r.y0 - self.y) * f
        else:
            if self.y >= r.y1:
                return self.distance_to(r.bottom_left, unit)
            elif self.y <= r.y0:
                return self.distance_to(r.top_left, unit)
            else:
                return (r.x0 - self.x) * f

    def __getitem__(self, i):
        return (self.x, self.y)[i]

    def __len__(self):
        return 2

    def __setitem__(self, i, v):
        v = float(v)
        if   i == 0: self.x = v
        elif i == 1: self.y = v
        else:
            raise IndexError("index out of range")
        return None

    def __repr__(self):
        return "Point" + str(tuple(self))

    def __pos__(self):
        return Point(self)

    def __neg__(self):
        return Point(-self.x, -self.y)

    def __bool__(self):
        return not (max(self) == min(self) == 0)

    def __nonzero__(self):
        return not (max(self) == min(self) == 0)

    def __eq__(self, p):
        if not hasattr(p, "__len__"):
            return False
        return len(p) == 2 and bool(self - p) is False

    def __abs__(self):
        return math.sqrt(self.x * self.x + self.y * self.y)

    norm = __abs__

    def __add__(self, p):
        if hasattr(p, "__float__"):
            return Point(self.x + p, self.y + p)
        if len(p) != 2:
            raise ValueError("Point: bad seq len")
        return Point(self.x + p[0], self.y + p[1])

    def __sub__(self, p):
        if hasattr(p, "__float__"):
            return Point(self.x - p, self.y - p)
        if len(p) != 2:
            raise ValueError("Point: bad seq len")
        return Point(self.x - p[0], self.y - p[1])

    def __mul__(self, m):
        if hasattr(m, "__float__"):
            return Point(self.x * m, self.y * m)
        p = Point(self)
        return p.transform(m)

    def __truediv__(self, m):
        if hasattr(m, "__float__"):
            return Point(self.x * 1./m, self.y * 1./m)
        m1 = util_invert_matrix(m)[1]
        if not m1:
            raise ZeroDivisionError("matrix not invertible")
        p = Point(self)
        return p.transform(m1)

    __div__ = __truediv__

    def __hash__(self):
        return hash(tuple(self))

class Rect(object):
    """Rect() - all zeros
    Rect(x0, y0, x1, y1) - 4 coordinates
    Rect(top-left, x1, y1) - point and 2 coordinates
    Rect(x0, y0, bottom-right) - 2 coordinates and point
    Rect(top-left, bottom-right) - 2 points
    Rect(sequ) - new from sequence or rect-like
    """
    def __init__(self, *args):
        self.x0, self.y0, self.x1, self.y1 = util_make_rect(args)
        return None

    def normalize(self):
        """Replace rectangle with its valid version."""
        if self.x1 < self.x0:
            self.x0, self.x1 = self.x1, self.x0
        if self.y1 < self.y0:
            self.y0, self.y1 = self.y1, self.y0
        return self

    @property
    def is_empty(self):
        """True if rectangle area is empty."""
        return self.x0 >= self.x1 or self.y0 >= self.y1

    @property
    def is_valid(self):
        """True if rectangle is valid."""
        return self.x0 <= self.x1 and self.y0 <= self.y1

    @property
    def is_infinite(self):
        """True if this is the infinite rectangle."""
        return self.x0 == self.y0 == FZ_MIN_INF_RECT and self.x1 == self.y1 == FZ_MAX_INF_RECT

    @property
    def top_left(self):
        """Top-left corner."""
        return Point(self.x0, self.y0)

    @property
    def top_right(self):
        """Top-right corner."""
        return Point(self.x1, self.y0)

    @property
    def bottom_left(self):
        """Bottom-left corner."""
        return Point(self.x0, self.y1)

    @property
    def bottom_right(self):
        """Bottom-right corner."""
        return Point(self.x1, self.y1)

    tl = top_left
    tr = top_right
    bl = bottom_left
    br = bottom_right

    @property
    def quad(self):
        """Return Quad version of rectangle."""
        return Quad(self.tl, self.tr, self.bl, self.br)

    def torect(self, r):
        """Return matrix that converts to target rect."""

        r = Rect(r)
        if self.is_infinite or self.is_empty or r.is_infinite or r.is_empty:
            raise ValueError("rectangles must be finite and not empty")
        return (
            Matrix(1, 0, 0, 1, -self.x0, -self.y0)
            * Matrix(r.width / self.width, r.height / self.height)
            * Matrix(1, 0, 0, 1, r.x0, r.y0)
        )

    def morph(self, p, m):
        """Morph with matrix-like m and point-like p.

        Returns a new quad."""
        if self.is_infinite:
            return INFINITE_QUAD()
        return self.quad.morph(p, m)

    def round(self):
        """Return the IRect."""
        return IRect(util_round_rect(self))

    irect = property(round)

    width  = property(lambda self: self.x1 - self.x0 if self.x1 > self.x0 else 0)
    height = property(lambda self: self.y1 - self.y0 if self.y1 > self.y0 else 0)

    def include_point(self, p):
        """Extend to include point-like p."""
        if len(p) != 2:
            raise ValueError("Point: bad seq len")
        self.x0, self.y0, self.x1, self.y1 = util_include_point_in_rect(self, p)
        return self

    def include_rect(self, r):
        """Extend to include rect-like r."""
        if len(r) != 4:
            raise ValueError("Rect: bad seq len")
        r = Rect(r)
        if r.is_infinite or self.is_infinite:
            self.x0, self.y0, self.x1, self.y1 = FZ_MIN_INF_RECT, FZ_MIN_INF_RECT, FZ_MAX_INF_RECT, FZ_MAX_INF_RECT
        elif r.is_empty:
            return self
        elif self.is_empty:
            self.x0, self.y0, self.x1, self.y1 = r.x0, r.y0, r.x1, r.y1
        else:
            self.x0, self.y0, self.x1, self.y1 = util_union_rect(self, r)
        return self

    def intersect(self, r):
        """Restrict to common rect with rect-like r."""
        if not len(r) == 4:
            raise ValueError("Rect: bad seq len")
        r = Rect(r)
        if r.is_infinite:
            return self
        elif self.is_infinite:
            self.x0, self.y0, self.x1, self.y1 = r.x0, r.y0, r.x1, r.y1
        elif r.is_empty:
            self.x0, self.y0, self.x1, self.y1 = r.x0, r.y0, r.x1, r.y1
        elif self.is_empty:
            return self
        else:
            self.x0, self.y0, self.x1, self.y1 = util_intersect_rect(self, r)
        return self

    def contains(self, x):
        """Check if containing point-like or rect-like x."""
        return self.__contains__(x)

    def transform(self, m):
        """Replace with the transformation by matrix-like m."""
        if not len(m) == 6:
            raise ValueError("Matrix: bad seq len")
        self.x0, self.y0, self.x1, self.y1 = util_transform_rect(self, m)
        return self

    def __getitem__(self, i):
        return (self.x0, self.y0, self.x1, self.y1)[i]

    def __len__(self):
        return 4

    def __setitem__(self, i, v):
        v = float(v)
        if   i == 0: self.x0 = v
        elif i == 1: self.y0 = v
        elif i == 2: self.x1 = v
        elif i == 3: self.y1 = v
        else:
            raise IndexError("index out of range")
        return None

    def __repr__(self):
        return "Rect" + str(tuple(self))

    def __pos__(self):
        return Rect(self)

    def __neg__(self):
        return Rect(-self.x0, -self.y0, -self.x1, -self.y1)

    def __bool__(self):
        return not self.x0 == self.y0 == self.x1 == self.y1 == 0

    def __nonzero__(self):
        return not self.x0 == self.y0 == self.x1 == self.y1 == 0

    def __eq__(self, r):
        if not hasattr(r, "__len__"):
            return False
        return len(r) == 4 and self.x0 == r[0] and self.y0 == r[1] and self.x1 == r[2] and self.y1 == r[3]

    def __abs__(self):
        if self.is_infinite or not self.is_valid:
            return 0.0
        return self.width * self.height

    def norm(self):
        return math.sqrt(sum([c*c for c in self]))

    def __add__(self, p):
        if hasattr(p, "__float__"):
            return Rect(self.x0 + p, self.y0 + p, self.x1 + p, self.y1 + p)
        if len(p) != 4:
            raise ValueError("Rect: bad seq len")
        return Rect(self.x0 + p[0], self.y0 + p[1], self.x1 + p[2], self.y1 + p[3])


    def __sub__(self, p):
        if hasattr(p, "__float__"):
            return Rect(self.x0 - p, self.y0 - p, self.x1 - p, self.y1 - p)
        if len(p) != 4:
            raise ValueError("Rect: bad seq len")
        return Rect(self.x0 - p[0], self.y0 - p[1], self.x1 - p[2], self.y1 - p[3])


    def __mul__(self, m):
        if hasattr(m, "__float__"):
            return Rect(self.x0 * m, self.y0 * m, self.x1 * m, self.y1 * m)
        r = Rect(self)
        r = r.transform(m)
        return r

    def __truediv__(self, m):
        if hasattr(m, "__float__"):
            return Rect(self.x0 * 1./m, self.y0 * 1./m, self.x1 * 1./m, self.y1 * 1./m)
        im = util_invert_matrix(m)[1]
        if not im:
            raise ZeroDivisionError("Matrix not invertible")
        r = Rect(self)
        r = r.transform(im)
        return r

    __div__ = __truediv__

    def __contains__(self, x):
        if hasattr(x, "__float__"):
            return x in tuple(self)
        l = len(x)
        if l == 2:
            return util_is_point_in_rect(x, self)
        if l == 4:
            r = INFINITE_RECT()
            try:
                r = Rect(x)
            except:
                r = Quad(x).rect
            return (self.x0 <= r.x0 <= r.x1 <= self.x1 and
                    self.y0 <= r.y0 <= r.y1 <= self.y1)
        return False
    

    def __or__(self, x):
        if not hasattr(x, "__len__"):
            raise ValueError("bad type op 2")

        r = Rect(self)
        if len(x) == 2:
            return r.include_point(x)
        if len(x) == 4:
            return r.include_rect(x)
        raise ValueError("bad type op 2")

    def __and__(self, x):
        if not hasattr(x, "__len__") or len(x) != 4:
            raise ValueError("bad type op 2")
        r = Rect(self)
        return r.intersect(x)

    def intersects(self, x):
        """Check if intersection with rectangle x is not empty."""
        r1 = Rect(x)
        if self.is_empty or self.is_infinite or r1.is_empty or r1.is_infinite:
            return False
        r = Rect(self)
        if r.intersect(r1).is_empty:
            return False
        return True

    def __hash__(self):
        return hash(tuple(self))

class IRect(object):
    """IRect() - all zeros
    IRect(x0, y0, x1, y1) - 4 coordinates
    IRect(top-left, x1, y1) - point and 2 coordinates
    IRect(x0, y0, bottom-right) - 2 coordinates and point
    IRect(top-left, bottom-right) - 2 points
    IRect(sequ) - new from sequence or rect-like
    """
    def __init__(self, *args):
        self.x0, self.y0, self.x1, self.y1 = util_make_irect(args)
        return None

    def normalize(self):
        """Replace rectangle with its valid version."""
        if self.x1 < self.x0:
            self.x0, self.x1 = self.x1, self.x0
        if self.y1 < self.y0:
            self.y0, self.y1 = self.y1, self.y0
        return self

    @property
    def is_empty(self):
        """True if rectangle area is empty."""
        return self.x0 >= self.x1 or self.y0 >= self.y1

    @property
    def is_valid(self):
        """True if rectangle is valid."""
        return self.x0 <= self.x1 and self.y0 <= self.y1

    @property
    def is_infinite(self):
        """True if rectangle is infinite."""
        return self.x0 == self.y0 == FZ_MIN_INF_RECT and self.x1 == self.y1 == FZ_MAX_INF_RECT

    @property
    def top_left(self):
        """Top-left corner."""
        return Point(self.x0, self.y0)

    @property
    def top_right(self):
        """Top-right corner."""
        return Point(self.x1, self.y0)

    @property
    def bottom_left(self):
        """Bottom-left corner."""
        return Point(self.x0, self.y1)

    @property
    def bottom_right(self):
        """Bottom-right corner."""
        return Point(self.x1, self.y1)

    tl = top_left
    tr = top_right
    bl = bottom_left
    br = bottom_right

    @property
    def quad(self):
        """Return Quad version of rectangle."""
        return Quad(self.tl, self.tr, self.bl, self.br)


    def torect(self, r):
        """Return matrix that converts to target rect."""

        r = Rect(r)
        if self.is_infinite or self.is_empty or r.is_infinite or r.is_empty:
            raise ValueError("rectangles must be finite and not empty")
        return (
            Matrix(1, 0, 0, 1, -self.x0, -self.y0)
            * Matrix(r.width / self.width, r.height / self.height)
            * Matrix(1, 0, 0, 1, r.x0, r.y0)
        )

    def morph(self, p, m):
        """Morph with matrix-like m and point-like p.

        Returns a new quad."""
        if self.is_infinite:
            return INFINITE_QUAD()
        return self.quad.morph(p, m)

    @property
    def rect(self):
        return Rect(self)

    width  = property(lambda self: self.x1 - self.x0 if self.x1 > self.x0 else 0)
    height = property(lambda self: self.y1 - self.y0 if self.y1 > self.y0 else 0)

    def include_point(self, p):
        """Extend rectangle to include point p."""
        rect = self.rect.include_point(p)
        return rect.irect

    def include_rect(self, r):
        """Extend rectangle to include rectangle r."""
        rect = self.rect.include_rect(r)
        return rect.irect

    def intersect(self, r):
        """Restrict rectangle to intersection with rectangle r."""
        rect = self.rect.intersect(r)
        return rect.irect

    def __getitem__(self, i):
        return (self.x0, self.y0, self.x1, self.y1)[i]

    def __len__(self):
        return 4

    def __setitem__(self, i, v):
        v = int(v)
        if   i == 0: self.x0 = v
        elif i == 1: self.y0 = v
        elif i == 2: self.x1 = v
        elif i == 3: self.y1 = v
        else:
            raise IndexError("index out of range")
        return None

    def __repr__(self):
        return "IRect" + str(tuple(self))

    def __pos__(self):
        return IRect(self)

    def __neg__(self):
        return IRect(-self.x0, -self.y0, -self.x1, -self.y1)

    def __bool__(self):
        return not self.x0 == self.y0 == self.x1 == self.y1 == 0

    def __nonzero__(self):
        return not self.x0 == self.y0 == self.x1 == self.y1 == 0

    def __eq__(self, r):
        if not hasattr(r, "__len__"):
            return False
        return len(r) == 4 and self.x0 == r[0] and self.y0 == r[1] and self.x1 == r[2] and self.y1 == r[3]

    def __abs__(self):
        if self.is_infinite or not self.is_valid:
            return 0
        return self.width * self.height

    def norm(self):
        return math.sqrt(sum([c*c for c in self]))

    def __add__(self, p):
        return Rect.__add__(self, p).round()

    def __sub__(self, p):
        return Rect.__sub__(self, p).round()

    def transform(self, m):
        return Rect.transform(self, m).round()

    def __mul__(self, m):
        return Rect.__mul__(self, m).round()

    def __truediv__(self, m):
        return Rect.__truediv__(self, m).round()

    __div__ = __truediv__


    def __contains__(self, x):
        return Rect.__contains__(self, x)


    def __or__(self, x):
        return Rect.__or__(self, x).round()

    def __and__(self, x):
        return Rect.__and__(self, x).round()

    def intersects(self, x):
        return Rect.intersects(self, x)

    def __hash__(self):
        return hash(tuple(self))


class Quad(object):
    """Quad() - all zero points\nQuad(ul, ur, ll, lr)\nQuad(quad) - new copy\nQuad(sequence) - from 'sequence'"""
    def __init__(self, *args):
        if not args:
            self.ul = self.ur = self.ll = self.lr = Point()
            return None

        if len(args) > 4:
            raise ValueError("Quad: bad seq len")
        if len(args) == 4:
            self.ul, self.ur, self.ll, self.lr = map(Point, args)
            return None
        if len(args) == 1:
            l = args[0]
            if hasattr(l, "__getitem__") is False:
                raise ValueError("Quad: bad args")
            if len(l) != 4:
                raise ValueError("Quad: bad seq len")
            self.ul, self.ur, self.ll, self.lr = map(Point, l)
            return None
        raise ValueError("Quad: bad args")

    @property
    def is_rectangular(self)->bool:
        """Check if quad is rectangular.

        Notes:
            Some rotation matrix can thus transform it into a rectangle.
            This is equivalent to three corners enclose 90 degrees.
        Returns:
            True or False.
        """

        sine = util_sine_between(self.ul, self.ur, self.lr)
        if abs(sine - 1) > EPSILON:  # the sine of the angle
            return False

        sine = util_sine_between(self.ur, self.lr, self.ll)
        if abs(sine - 1) > EPSILON:
            return False

        sine = util_sine_between(self.lr, self.ll, self.ul)
        if abs(sine - 1) > EPSILON:
            return False

        return True


    @property
    def is_convex(self)->bool:
        """Check if quad is convex and not degenerate.

        Notes:
            Check that for the two diagonals, the other two corners are not
            on the same side of the diagonal.
        Returns:
            True or False.
        """
        m = planish_line(self.ul, self.lr)  # puts this diagonal on x-axis
        p1 = self.ll * m  # transform the
        p2 = self.ur * m  # other two points
        if p1.y * p2.y > 0:
            return False
        m = planish_line(self.ll, self.ur)  # puts other diagonal on x-axis
        p1 = self.lr * m  # tranform the
        p2 = self.ul * m  # remaining points
        if p1.y * p2.y > 0:
            return False
        return True


    width  = property(lambda self: max(abs(self.ul - self.ur), abs(self.ll - self.lr)))
    height = property(lambda self: max(abs(self.ul - self.ll), abs(self.ur - self.lr)))

    @property
    def is_empty(self):
        """Check whether all quad corners are on the same line.

        This is the case if width or height is zero.
        """
        return self.width < EPSILON or self.height < EPSILON

    @property
    def is_infinite(self):
        """Check whether this is the infinite quad."""
        return self.rect.is_infinite

    @property
    def rect(self):
        r = Rect()
        r.x0 = min(self.ul.x, self.ur.x, self.lr.x, self.ll.x)
        r.y0 = min(self.ul.y, self.ur.y, self.lr.y, self.ll.y)
        r.x1 = max(self.ul.x, self.ur.x, self.lr.x, self.ll.x)
        r.y1 = max(self.ul.y, self.ur.y, self.lr.y, self.ll.y)
        return r


    def __contains__(self, x):
        try:
            l = x.__len__()
        except:
            return False
        if l == 2:
            return util_point_in_quad(x, self)
        if l != 4:
            return False
        if CheckRect(x):
            if Rect(x).is_empty:
                return True
            return util_point_in_quad(x[:2], self) and util_point_in_quad(x[2:], self)
        if CheckQuad(x):
            for i in range(4):
                if not util_point_in_quad(x[i], self):
                    return False
            return True
        return False


    def __getitem__(self, i):
        return (self.ul, self.ur, self.ll, self.lr)[i]

    def __len__(self):
        return 4

    def __setitem__(self, i, v):
        if   i == 0: self.ul = Point(v)
        elif i == 1: self.ur = Point(v)
        elif i == 2: self.ll = Point(v)
        elif i == 3: self.lr = Point(v)
        else:
            raise IndexError("index out of range")
        return None

    def __repr__(self):
        return "Quad" + str(tuple(self))

    def __pos__(self):
        return Quad(self)

    def __neg__(self):
        return Quad(-self.ul, -self.ur, -self.ll, -self.lr)

    def __bool__(self):
        return not self.is_empty

    def __nonzero__(self):
        return not self.is_empty

    def __eq__(self, quad):
        if not hasattr(quad, "__len__"):
            return False
        return len(quad) == 4 and (
            self.ul == quad[0] and
            self.ur == quad[1] and
            self.ll == quad[2] and
            self.lr == quad[3]
        )

    def __abs__(self):
        if self.is_empty:
            return 0.0
        return abs(self.ul - self.ur) * abs(self.ul - self.ll)


    def morph(self, p, m):
        """Morph the quad with matrix-like 'm' and point-like 'p'.

        Return a new quad."""
        if self.is_infinite:
            return INFINITE_QUAD()
        delta = Matrix(1, 1).pretranslate(p.x, p.y)
        q = self * ~delta * m * delta
        return q


    def transform(self, m):
        """Replace quad by its transformation with matrix m."""
        if hasattr(m, "__float__"):
            pass
        elif len(m) != 6:
            raise ValueError("Matrix: bad seq len")
        self.ul *= m
        self.ur *= m
        self.ll *= m
        self.lr *= m
        return self

    def __mul__(self, m):
        q = Quad(self)
        q = q.transform(m)
        return q

    def __add__(self, q):
        if hasattr(q, "__float__"):
            return Quad(self.ul + q, self.ur + q, self.ll + q, self.lr + q)
        if len(p) != 4:
            raise ValueError("Quad: bad seq len")
        return Quad(self.ul + q[0], self.ur + q[1], self.ll + q[2], self.lr + q[3])


    def __sub__(self, q):
        if hasattr(q, "__float__"):
            return Quad(self.ul - q, self.ur - q, self.ll - q, self.lr - q)
        if len(p) != 4:
            raise ValueError("Quad: bad seq len")
        return Quad(self.ul - q[0], self.ur - q[1], self.ll - q[2], self.lr - q[3])


    def __truediv__(self, m):
        if hasattr(m, "__float__"):
            im = 1. / m
        else:
            im = util_invert_matrix(m)[1]
            if not im:
                raise ZeroDivisionError("Matrix not invertible")
        q = Quad(self)
        q = q.transform(im)
        return q

    __div__ = __truediv__


    def __hash__(self):
        return hash(tuple(self))


# some special geometry objects
def EMPTY_RECT():
    return Rect(FZ_MAX_INF_RECT, FZ_MAX_INF_RECT, FZ_MIN_INF_RECT, FZ_MIN_INF_RECT)


def INFINITE_RECT():
    return Rect(FZ_MIN_INF_RECT, FZ_MIN_INF_RECT, FZ_MAX_INF_RECT, FZ_MAX_INF_RECT)


def EMPTY_IRECT():
    return IRect(FZ_MAX_INF_RECT, FZ_MAX_INF_RECT, FZ_MIN_INF_RECT, FZ_MIN_INF_RECT)


def INFINITE_IRECT():
    return IRect(FZ_MIN_INF_RECT, FZ_MIN_INF_RECT, FZ_MAX_INF_RECT, FZ_MAX_INF_RECT)


def INFINITE_QUAD():
    return INFINITE_RECT().quad


def EMPTY_QUAD():
    return EMPTY_RECT().quad


%}
