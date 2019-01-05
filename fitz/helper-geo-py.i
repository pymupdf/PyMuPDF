%pythoncode %{
class Matrix():
    """Matrix() - all zeros\nMatrix(a, b, c, d, e, f)\nMatrix(zoom-x, zoom-y) - zoom\nMatrix(shear-x, shear-y, 1) - shear\nMatrix(degree) - rotate\nMatrix(Matrix) - new copy\nMatrix(sequence) - from 'sequence'"""
    def __init__(self, *args):
        if not args:
            self.a = self.b = self.c = self.d = self.e = self.f = 0.0
            return None
        if len(args) > 6:
            raise ValueError("illegal sequ. length")
        if len(args) == 6:                       # 6 numbers
            self.a = float(args[0])
            self.b = float(args[1])
            self.c = float(args[2])
            self.d = float(args[3])
            self.e = float(args[4])
            self.f = float(args[5])
            return None
        if len(args) == 1:                       # either an angle or a sequ
            if hasattr(args[0], "__float__"):
                theta = args[0] * math.pi / 180.0
                c = round(math.cos(theta), 10)
                s = round(math.sin(theta), 10)
                self.a = self.d = c
                self.b = s
                self.c = -s
                self.e = self.f = 0.0
                return None
            else:
                self.a = float(args[0][0])
                self.b = float(args[0][1])
                self.c = float(args[0][2])
                self.d = float(args[0][3])
                self.e = float(args[0][4])
                self.f = float(args[0][5])
                return None
        if len(args) == 2 or len(args) == 3 and args[2] == 0:
            self.a, self.b, self.c, self.d, self.e, self.f = float(args[0]), \
                0.0, 0.0, float(args[1]), 0.0, 0.0
            return None
        if len(args) == 3 and args[2] == 1:
            self.a, self.b, self.c, self.d, self.e, self.f = 1.0, \
                float(args[1]), float(args[0]), 1.0, 0.0, 0.0
            return None
        raise ValueError("illegal Matrix constructor")

    def invert(self, src=None):
        """Calculate the inverted matrix. Return 0 if successful and replace
        current one. Else return 1 and do nothing.
        """
        if src is None:
            dst = TOOLS._invert_matrix(self)
        else:
            dst = TOOLS._invert_matrix(src)
        if dst[0] == 1:
            return 1
        self.a, self.b, self.c, self.d, self.e, self.f = dst[1]
        return 0

    def preTranslate(self, tx, ty):
        """Calculate pre translation and replace current matrix."""
        self.e += tx * self.a + ty * self.c
        self.f += tx * self.b + ty * self.d
        return self

    def preScale(self, sx, sy):
        """Calculate pre scaling and replacing current matrix."""
        self.a *= sx
        self.b *= sx
        self.c *= sy
        self.d *= sy
        return self

    def preShear(self, h, v):
        """Calculate pre shearing and replace current matrix."""
        a, b = self.a, self.b
        self.a += v * self.c
        self.b += v * self.d
        self.c += h * a
        self.d += h * b
        return self

    def preRotate(self, theta):
        """Calculate pre rotation and replace current matrix."""
        while theta < 0: theta += 360
        while theta >= 360: theta -= 360
        epsilon = 1e-5
        if abs(0 - theta) < epsilon:
            pass

        elif abs(90.0 - theta) < epsilon:
            a = self.a
            b = self.b
            self.a = self.c
            self.b = self.d
            self.c = -a
            self.d = -b

        elif abs(180.0 - theta) < epsilon:
            self.a = -self.a
            self.b = -self.b
            self.c = -self.c
            self.d = -self.d

        elif abs(270.0 - theta) < epsilon:
            a = self.a
            b = self.b
            self.a = -self.c
            self.b = -self.d
            self.c = a
            self.d = b

        else:
            s = math.sin(theta * math.pi / 180.0)
            c = math.cos(theta * math.pi / 180.0)
            a = self.a
            b = self.b
            self.a = c * a + s * self.c
            self.b = c * b + s * self.d
            self.c =-s * a + c * self.c
            self.d =-s * b + c * self.d

        return self

    def concat(self, one, two):
        """Multiply two matrices and replace current one."""
        self.a, self.b, self.c, self.d, self.e, self.f = TOOLS._concat_matrix(one, two)
        return self

    def __getitem__(self, i):
        return (self.a, self.b, self.c, self.d, self.e, self.f)[i]

    def __setitem__(self, i, v):
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
        m1 = Matrix()
        m1.invert(self)
        return m1
    __inv__ = __invert__

    def __mul__(self, m):
        if hasattr(m, "__float__"):
            return Matrix(self.a * m, self.b * m, self.c * m,
                          self.d * m, self.e * m, self.f * m)
        return self.concat(self, m)

    def __truediv__(self, m):
        if hasattr(m, "__float__"):
            return Matrix(self.a * 1./m, self.b * 1./m, self.c * 1./m,
                          self.d * 1./m, self.e * 1./m, self.f * 1./m)
        m1 = TOOLS._invert_matrix(m)[1]
        if not m1:
            raise ZeroDivisionError("matrix not invertible")
        return self.concat(self, m1)
    __div__ = __truediv__

    def __add__(self, m):
        if hasattr(m, "__float__"):
            return Matrix(self.a + m, self.b + m, self.c + m,
                          self.d + m, self.e + m, self.f + m)
        return Matrix(self.a + m[0], self.b + m[1], self.c + m[2],
                          self.d + m[3], self.e + m[4], self.f + m[5])

    def __sub__(self, m):
        if hasattr(m, "__float__"):
            return Matrix(self.a - m, self.b - m, self.c - m,
                          self.d - m, self.e - m, self.f - m)
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

    def __eq__(self, m):
        if not hasattr(m, "__len__"):
            return False
        return len(m) == 6 and bool(self - m) is False

    def __abs__(self):
        return math.sqrt(self.a*self.a + self.b*self.b + self.c*self.c + \
                         self.d*self.d + self.e*self.e + self.f*self.f)

    @property
    def isRectilinear(self):
        epsilon = 1e-5
        return (abs(self.b) < epsilon and abs(self.c) < epsilon) or \
            (abs(self.a) < epsilon and abs(self.d) < epsilon);

    def __hash__(self):
        return hash(tuple(self))


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
    preRotate    = checkargs
    preShear     = checkargs
    preScale     = checkargs
    preTranslate = checkargs
    concat       = checkargs
    invert       = checkargs
    def __repr__(self):
        return "IdentityMatrix(1.0, 0.0, 0.0, 1.0, 0.0, 0.0)"

Identity = IdentityMatrix()

class Point():
    """Point() - all zeros\nPoint(x, y)\nPoint(Point) - new copy\nPoint(sequence) - from 'sequence'"""
    def __init__(self, *args):
        if not args:
            self.x = 0.0
            self.y = 0.0
            return None

        if len(args) > 2:
            raise ValueError("illegal sequ. length")
        if len(args) == 2:
            self.x = float(args[0])
            self.y = float(args[1])
            return None
        if len(args) == 1:
            l = args[0]
            if hasattr(l, "__getitem__") is False:
                raise ValueError("illegal Point constructor")
            if len(l) != 2:
                raise ValueError("illegal sequ. length")
            self.x = float(l[0])
            self.y = float(l[1])
            return None
        raise ValueError("illegal Point constructor")

    def transform(self, m):
        """Replace point by its transformation with matrix-like m."""
        x = self.x
        self.x = x * m[0] + self.y * m[2] + m[4]
        self.y = x * m[1] + self.y * m[3] + m[5]
        return self

    @property
    def unit(self):
        """Return unit vector of a point."""
        s = self.x * self.x + self.y * self.y
        if s < 1e-5:
            return Point(0,0)
        s = math.sqrt(s)
        return Point(self.x / s, self.y / s)

    @property
    def abs_unit(self):
        """Return unit vector of a point with positive coordinates."""
        s = self.x * self.x + self.y * self.y
        if s < 1e-5:
            return Point(0,0)
        s = math.sqrt(s)
        return Point(abs(self.x) / s, abs(self.y) / s)

    def distance_to(self, *args):
        """Return the distance to a rectangle or another point."""
        assert len(args) > 0, "at least one parameter must be given"
        x = args[0]
        if len(args) > 1:
            unit = args[1]
        else:
            unit = "px"
        u = {"px": (1.,1.), "in": (1.,72.), "cm": (2.54, 72.), "mm": (25.4, 72.)}
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
        if   i == 0: self.x = float(v)
        elif i == 1: self.y = float(v)
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

    def __add__(self, p):
        if hasattr(p, "__float__"):
            return Point(self.x + p, self.y + p)
        if len(p) != 2:
            raise ValueError("require point-like object")
        return Point(self.x + p[0], self.y + p[1])

    def __sub__(self, p):
        if hasattr(p, "__float__"):
            return Point(self.x - p, self.y - p)
        if len(p) != 2:
            raise ValueError("require point-like object")
        return Point(self.x - p[0], self.y - p[1])

    def __mul__(self, m):
        if hasattr(m, "__float__"):
            return Point(self.x * m, self.y * m)
        p = Point(self)
        return p.transform(m)

    def __truediv__(self, m):
        if hasattr(m, "__float__"):
            return Point(self.x * 1./m, self.y * 1./m)
        m1 = TOOLS._invert_matrix(m)[1]
        if not m1:
            raise ZeroDivisionError("matrix not invertible")
        p = Point(self)
        return p.transform(m1)

    __div__ = __truediv__

    def __hash__(self):
        return hash(tuple(self))

class Rect():
    """Rect() - all zeros\nRect(x0, y0, x1, y1)\nRect(top-left, x1, y1)\nRect(x0, y0, bottom-right)\nRect(top-left, bottom-right)\nRect(Rect or IRect) - new copy\nRect(sequence) - from 'sequence'"""
    def __init__(self, *args):
        if not args:
            self.x0 = self.y0 = self.x1 = self.y1 = 0.0
            return None

        if len(args) > 4:
            raise ValueError("invalid sequ. length")
        if len(args) == 4:
            self.x0 = float(args[0])
            self.y0 = float(args[1])
            self.x1 = float(args[2])
            self.y1 = float(args[3])
            return None
        if len(args) == 1:
            l = args[0]
            if hasattr(l, "__getitem__") is False:
                raise ValueError("invalid Rect constructor")
            if len(l) != 4:
                raise ValueError("invalid sequ. length")
            self.x0 = float(l[0])
            self.y0 = float(l[1])
            self.x1 = float(l[2])
            self.y1 = float(l[3])
            return None
        if len(args) == 2:                  # 2 Points provided
            self.x0 = float(args[0][0])
            self.y0 = float(args[0][1])
            self.x1 = float(args[1][0])
            self.y1 = float(args[1][1])
            return None
        if len(args) == 3:                  # 2 floats and 1 Point provided
            a0 = args[0]
            a1 = args[1]
            a2 = args[2]
            if hasattr(a0, "__float__"):    # (float, float, Point) provided
                self.x0 = float(a0)
                self.y0 = float(a1)
                self.x1 = float(a2[0])
                self.y1 = float(a2[1])
                return None
            self.x0 = float(a0[0])          # (Point, float, float) provided
            self.y0 = float(a0[1])
            self.x1 = float(a1)
            self.y1 = float(a2)
            return None
        raise ValueError("invalid Rect constructor")

    def normalize(self):
        """Replace rectangle with its finite version."""
        if self.x1 < self.x0:
            self.x0, self.x1 = self.x1, self.x0
        if self.y1 < self.y0:
            self.y0, self.y1 = self.y1, self.y0
        return self

    @property
    def isEmpty(self):
        """Check if rectangle area is empty."""
        return self.x0 == self.x1 or self.y0 == self.y1

    @property
    def isInfinite(self):
        """Check if rectangle is infinite."""
        return self.x0 > self.x1 or self.y0 > self.y1

    @property
    def top_left(self):
        return Point(self.x0, self.y0)

    @property
    def top_right(self):
        return Point(self.x1, self.y0)

    @property
    def bottom_left(self):
        return Point(self.x0, self.y1)

    @property
    def bottom_right(self):
        return Point(self.x1, self.y1)

    tl = top_left
    tr = top_right
    bl = bottom_left
    br = bottom_right

    @property
    def quad(self):
        return Quad(self.tl, self.tr, self.bl, self.br)

    def round(self):
        return IRect(min(self.x0, self.x1), min(self.y0, self.y1),
                     max(self.x0, self.x1), max(self.y0, self.y1))

    irect = property(round)

    width  = property(lambda self: abs(self.x1 - self.x0))
    height = property(lambda self: abs(self.y1 - self.y0))

    def includePoint(self, p):
        """Extend rectangle to include point p."""
        self.x0, self.y0, self.x1, self.y1 = TOOLS._include_point_in_rect(self, p)
        return self

    def includeRect(self, r):
        """Extend rectangle to include rectangle r."""
        self.x0, self.y0, self.x1, self.y1 = TOOLS._union_rect(self, r)
        return self

    def intersect(self, r):
        """Restrict self to common area with rectangle r."""
        self.x0, self.y0, self.x1, self.y1 = TOOLS._intersect_rect(self, r)
        return self

    def transform(self, m):
        """Replace rectangle with its transformation by matrix m."""
        self.x0, self.y0, self.x1, self.y1 = TOOLS._transform_rect(self, m)
        return self

    def __getitem__(self, i):
        return (self.x0, self.y0, self.x1, self.y1)[i]

    def __len__(self):
        return 4

    def __setitem__(self, i, v):
        if   i == 0: self.x0 = float(v)
        elif i == 1: self.y0 = float(v)
        elif i == 2: self.x1 = float(v)
        elif i == 3: self.y1 = float(v)
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
        return not (max(self) == min(self) == 0)

    def __nonzero__(self):
        return not (max(self) == min(self) == 0)

    def __eq__(self, p):
        if not hasattr(p, "__len__"):
            return False
        return len(p) == 4 and bool(self - p) is False

    def __abs__(self):
        if self.isEmpty or self.isInfinite:
            return 0.0
        return (self.x1 - self.x0) * (self.y1 - self.y0)

    def __add__(self, p):
        if hasattr(p, "__float__"):
            r = Rect(self.x0 + p, self.y0 + p, self.x1 + p, self.y1 + p)
        else:
            if len(p) != 4:
                raise ValueError("require rect-like object")
            r = Rect(self.x0 + p[0], self.y0 + p[1], self.x1 + p[2], self.y1 + p[3])
        return r

    def __sub__(self, p):
        if hasattr(p, "__float__"):
            return Rect(self.x0 - p, self.y0 - p, self.x1 - p, self.y1 - p)
        if len(p) != 4:
            raise ValueError("require rect-like object")
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
        im = TOOLS._invert_matrix(m)[1]
        if not im:
            raise ZeroDivisionError("matrix not invertible")
        r = Rect(self)
        r = r.transform(im)
        return r

    __div__ = __truediv__

    def __contains__(self, x):
        if hasattr(x, "__float__"):
            return x in tuple(self)
        l = len(x)
        r = Rect(self).normalize()
        if l == 4:
            if r.isEmpty: return False
            xr = Rect(x).normalize()
            if xr.isEmpty: return True
            if r.x0 <= xr.x0 and r.y0 <= xr.y0 and \
               r.x1 >= xr.x1 and r.y1 >= xr.y1:
               return True
            return False
        if l == 2:
            if r.x0 <= x[0] <= r.x1 and \
               r.y0 <= x[1] <= r.y1:
               return True
            return False
        return False

    def __or__(self, x):
        if not hasattr(x, "__len__"):
            raise ValueError("op2 is an unsupported type")

        r = Rect(self)
        if len(x) == 2:
            return r.includePoint(x)
        if len(x) == 4:
            return r.includeRect(x)
        raise ValueError("op2 is an unsupported type")

    def __and__(self, x):
        if not hasattr(x, "__len__"):
            raise ValueError("op2 is an unsupported type")

        r1 = Rect(x)
        r = Rect(self)
        return r.intersect(r1)

    def intersects(self, x):
        """Check if intersection with rectangle x is not empty."""
        r1 = Rect(x)
        if self.isEmpty or self.isInfinite or r1.isEmpty:
            return False
        r = Rect(self)
        if r.intersect(r1).isEmpty:
            return False
        return True

    def __hash__(self):
        return hash(tuple(self))

class IRect(Rect):
    """IRect() - all zeros\nIRect(x0, y0, x1, y1)\nIRect(Rect or IRect) - new copy\nIRect(sequence) - from 'sequence'"""
    def __init__(self, *args):
        Rect.__init__(self, *args)
        self.x0 = math.floor(self.x0 + 0.001)
        self.y0 = math.floor(self.y0 + 0.001)
        self.x1 = math.ceil(self.x1 - 0.001)
        self.y1 = math.ceil(self.y1 - 0.001)
        return None

    @property
    def round(self):
        pass

    irect = round

    @property
    def rect(self):
        return Rect(self)

    def __repr__(self):
        return "IRect" + str(tuple(self))

    def includePoint(self, p):
        """Extend rectangle to include point p."""
        return Rect.includePoint(self, p).round()

    def includeRect(self, r):
        """Extend rectangle to include rectangle r."""
        return Rect.includeRect(self, r).round()

    def intersect(self, r):
        """Restrict rectangle to intersection with rectangle r."""
        return Rect.intersect(self, r).round()

    def __setitem__(self, i, v):
        if   i == 0: self.x0 = int(v)
        elif i == 1: self.y0 = int(v)
        elif i == 2: self.x1 = int(v)
        elif i == 3: self.y1 = int(v)
        else:
            raise IndexError("index out of range")
        return None

    def __pos__(self):
        return IRect(self)

    def __neg__(self):
        return IRect(-self.x0, -self.y0, -self.x1, -self.y1)

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

    def __or__(self, x):
        return Rect.__or__(self, x).round()

    def __and__(self, x):
        return Rect.__and__(self, x).round()

class Quad():
    """Quad() - all zero points\nQuad(ul, ur, ll, lr)\nQuad(quad) - new copy\nQuad(sequence) - from 'sequence'"""
    def __init__(self, *args):
        if not args:
            self.ul = self.ur = self.ll = self.lr = Point()
            return None

        if len(args) > 4:
            raise ValueError("invalid sequ. length")
        if len(args) == 4:
            self.ul = Point(args[0])
            self.ur = Point(args[1])
            self.ll = Point(args[2])
            self.lr = Point(args[3])
            return None
        if len(args) == 1:
            l = args[0]
            if hasattr(l, "__getitem__") is False:
                raise ValueError("invalid Quad constructor")
            if len(l) != 4:
                raise ValueError("invalid sequ. length")
            self.ul = Point(l[0])
            self.ur = Point(l[1])
            self.ll = Point(l[2])
            self.lr = Point(l[3])
            return None
        raise ValueError("invalid Quad constructor")

    @property
    def isRectangular(self):
        """Check if quad is rectangular.
        """
        # if any two of the 4 corners are equal return false
        upper = (self.ur - self.ul).unit
        if not bool(upper):
            return False
        right = (self.lr - self.ur).unit
        if not bool(right):
            return False
        left  = (self.ll - self.ul).unit
        if not bool(left):
            return False
        lower = (self.lr - self.ll).unit
        if not bool(lower):
            return False
        eps = 1e-5
        # we now have 4 sides of length 1. If 3 of them have 90 deg angles,
        # then it is a rectangle -- we check via scalar product == 0
        return abs(sum(map(lambda x,y: x*y, upper, right))) <= eps and \
               abs(sum(map(lambda x,y: x*y, upper, left))) <= eps and \
               abs(sum(map(lambda x,y: x*y, left, lower))) <= eps

    @property
    def isEmpty(self):
        """Check if quad is empty retangle. If rectangular, we are done (not empty).
        But all 4 points may still be on one line. We check this out here.
        In that case all 3 lines connecting corners to ul will have same angle with
        x-axis.
        """
        if self.isRectangular:
            return False
        eps = 1e-5
        ul = Point()
        ur = (self.ur - self.ul).abs_unit
        lr = (self.lr - self.ul).abs_unit
        ll = (self.ll - self.ul).abs_unit
        if max(ur.y, lr.y, ll.y) - min(ur.y, lr.y, ll.y) < eps:
            return True
        return False

    width  = property(lambda self: max(abs(self.ul - self.ur), abs(self.ll - self.lr)))
    height = property(lambda self: max(abs(self.ul - self.ll), abs(self.ur - self.lr)))

    @property
    def rect(self):
        return Rect(self.ul, self.ur) | self.ll | self.lr

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
        return not self.isEmpty

    def __nonzero__(self):
        return not self.isEmpty

    def __eq__(self, p):
        if not hasattr(p, "__len__"):
            return False
        return len(p) == 4 and self.ul == p[0] and self.ur == p[1] and \
               self.ll == p[3] and self.lr == p[3]

    def __abs__(self):
        if self.isEmpty:
            return 0.0
        return abs(self.ul - self.ur) * abs(self.ul - self.ll)

    def transform(self, m):
        """Replace quad by its transformation with matrix m."""
        self.ul *= m
        self.ur *= m
        self.ll *= m
        self.lr *= m
        return self

    def __mul__(self, m):
        r = Quad(self)
        r = r.transform(m)
        return r

    def __truediv__(self, m):
        if hasattr(m, "__float__"):
            im = 1. / m
        else:
            im = TOOLS._invert_matrix(m)[1]
            if not im:
                raise ZeroDivisionError("matrix not invertible")
        r = Quad(self)
        r = r.transform(im)
        return r

    __div__ = __truediv__

    def __hash__(self):
        return hash(tuple(self))

%}