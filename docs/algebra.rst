.. include:: header.rst

.. _Algebra:

Operator Algebra for Geometry Objects
======================================

.. highlight:: python

Instances of classes :ref:`Point`, :ref:`IRect`, :ref:`Rect`, :ref:`Quad` and :ref:`Matrix` are collectively also called "geometry" objects.

They all are special cases of Python sequences, see :ref:`SequenceTypes` for more background.

We have defined operators for these classes that allow dealing with them (almost) like ordinary numbers in terms of addition, subtraction, multiplication, division, and some others.

This chapter is a synopsis of what is possible.

General Remarks
-----------------
1. Operators can be either **binary** (i.e. involving two objects) or **unary**.

2. The resulting type of **binary** operations is either a **new object of the left operand's class,** a bool or (for dot products) a float.

3. The result of **unary** operations is either a **new object** of the same class, a bool or a float.

4. The binary operators `+, -, *, /` are defined for all classes. They *roughly* do what you would expect -- **except, that the second operand ...**

    - may always be a number which then performs the operation on every component of the first one,
    - may always be a numeric sequence of the same length (2, 4 or 6) -- we call such sequences :data:`point_like`, :data:`rect_like`, :data:`quad_like` or :data:`matrix_like`, respectively.

5. Rectangles support **additional binary** operations: **intersection** (operator `"&"`), **union** (operator `"|"`) and **containment** checking.

6. Binary operators fully support in-place operations. So if "°" is a binary operator then the expression `a °= b` is always valid and the same as `a = a ° b`. Therefore, be careful and do **not** do `p1 *= p2` for two points, because thereafter "p1" is a **float**.


Unary Operations
------------------

=========== ===================================================================
Oper.       Result
=========== ===================================================================
 bool(OBJ)  is false exactly if all components of OBJ are zero
 abs(OBJ)   the rectangle area -- equal to norm(OBJ) for the other types
 norm(OBJ)  square root of the component squares (Euclidean norm)
 +OBJ       new copy of OBJ
 -OBJ       new copy of OBJ with negated components
 ~m         inverse of matrix "m", or the null matrix if not invertible
=========== ===================================================================


Binary Operations
------------------
These are expressions like `a ° b` where "°" is any of the operators `+, -, *, /`. Also binary operations are expressions of the form `a == b` and `b in a`.

If "b" is a number, then the respective operation is executed for each component of "a". Otherwise, if "b" is **not a number,** then the following happens:


========= ===========================================================================
Oper.     Result
========= ===========================================================================
a+b, a-b  component-wise execution, "b" must be "a-like".
a*m, a/m  "a" can be a point, rectangle or matrix and "m" is a
          :data:`matrix_like`. *"a/m"* is treated as *"a*~m"* (see note below
          for non-invertible matrices). If "a" is a **point** or a **rectangle**,
          then *"a.transform(m)"* is executed. If "a" is a matrix, then
          matrix concatenation takes place.
a*b       returns the **vector dot product** for a point "a" and point-like "b".
a&b       **intersection rectangle:** "a" must be a rectangle and
          "b" :data:`rect_like`. Delivers the **largest rectangle**
          contained in both operands.
a|b       **union rectangle:** "a" must be a rectangle, and "b" may be
          :data:`point_like` or :data:`rect_like`.
          Delivers the **smallest rectangle** containing both operands.
b in a    if "b" is a number, then `b in tuple(a)` is returned.
          If "b" is :data:`point_like`, :data:`rect_like` or :data:`quad_like`,
          then "a" must be a rectangle, and `a.contains(b)` is returned.
a == b    *True* if *bool(a-b)* is *False* ("b" may be "a-like").
========= ===========================================================================


.. note:: Please note an important difference to usual arithmetic:

        Matrix multiplication is **not commutative**, i.e. in general we have `m*n != n*m` for two matrices. Also, there are non-zero matrices which have no inverse, for example `m = Matrix(1, 0, 1, 0, 1, 0)`. If you try to divide by any of these, you will receive a `ZeroDivisionError` exception using operator *"/"*, e.g. for the expression `pymupdf.Identity / m`. But if you formulate `pymupdf.Identity * ~m`, the result will be `pymupdf.Matrix()` (the null matrix).

        Admittedly, this represents an inconsistency, and we are considering to remove it. For the time being, you can choose to avoid an exception and check whether ~m is the null matrix, or accept a potential *ZeroDivisionError* by using `pymupdf.Identity / m`.

.. note::

  * With these conventions, all the usual algebra rules apply. For example, arbitrarily using brackets **(among objects of the same class!)** is possible: if r1, r2 are rectangles and m1, m2 are matrices, you can do this `(r1 + r2) * m1 * m2`.
  * For all objects of the same class, `a + b + c == (a + b) + c == a + (b + c)` is true.
  * For matrices in addition the following is true: `(m1 + m2) * m3 == m1 * m3 + m2 * m3` (distributivity property).
  * **But the sequence of applying matrices is important:** If r is a rectangle and m1, m2 are matrices, then -- **caution!:**
     - `r * m1 * m2 == (r * m1) * m2 != r * (m1 * m2)`

Some Examples
--------------

Manipulation with numbers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
For the usual arithmetic operations, numbers are always allowed as second operand. In addition, you can formulate `"x in OBJ"`, where x is a number. It is implemented as `"x in tuple(OBJ)"`::

  >>> pymupdf.Rect(1, 2, 3, 4) + 5
  pymupdf.Rect(6.0, 7.0, 8.0, 9.0)
  >>> 3 in pymupdf.Rect(1, 2, 3, 4)
  True
  >>> 

The following will create the upper left quarter of a document page rectangle::

  >>> page.rect
  Rect(0.0, 0.0, 595.0, 842.0)
  >>> page.rect / 2
  Rect(0.0, 0.0, 297.5, 421.0)
  >>> 

The following will deliver the **middle point of a line** that connects two points **p1** and **p2**::

  >>> p1 = pymupdf.Point(1, 2)
  >>> p2 = pymupdf.Point(4711, 3141)
  >>> mp = (p1 + p2) / 2
  >>> mp
  Point(2356.0, 1571.5)
  >>> 

Compute the **vector dot product** of two points. You can compute the **cosine of angles** and check orthogonality.

  >>> p1 = pymupdf.Point(1, 0)
  >>> p2 = pymupdf.Point(1, 1)
  >>> dot = p1 * p2
  >>> dot
  1.0

  >>> # compute the cosine of the angle between p1 and p2:
  >>> cosine = dot / (abs(p1) * abs(p2))
  >>> cosine  # cosine of 45 degrees
  0.7071067811865475

  >>> math.cos(mat.radians(45))  # verify:
  0.7071067811865476

  >>> # check orhogonality
  >>> p3 = pymupdf.Point(0, 1)
  >>> # p1 and p3 are orthogonal so, as expected:
  >>> p1 * p3  
  0.0


Manipulation with "like" Objects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The second operand of a binary operation can always be "like" the left operand. "Like" in this context means "a sequence of numbers of the same length". With the above examples::

  >>> p1 + p2
  Point(4712.0, 3143.0)
  >>> p1 + (4711, 3141)
  Point(4712.0, 3143.0)
  >>> p1 += (4711, 3141)
  >>> p1
  Point(4712.0, 3143.0)
  >>> 

To shift a rectangle for 5 pixels to the right, do this::

  >>> pymupdf.Rect(100, 100, 200, 200) + (5, 0, 5, 0)  # add 5 to the x coordinates
  Rect(105.0, 100.0, 205.0, 200.0)
  >>>

Points, rectangles and matrices can be *transformed* with matrices. In PyMuPDF, we treat this like a **"multiplication"** (or resp. **"division"**), where the second operand may be "like" a matrix. Division in this context means "multiplication with the inverted matrix"::

  >>> m = pymupdf.Matrix(1, 2, 3, 4, 5, 6)
  >>> n = pymupdf.Matrix(6, 5, 4, 3, 2, 1)
  >>> p = pymupdf.Point(1, 2)
  >>> p * m
  Point(12.0, 16.0)
  >>> p * (1, 2, 3, 4, 5, 6)
  Point(12.0, 16.0)
  >>> p / m
  Point(2.0, -2.0)
  >>> p / (1, 2, 3, 4, 5, 6)
  Point(2.0, -2.0)
  >>>
  >>> m * n  # matrix multiplication
  Matrix(14.0, 11.0, 34.0, 27.0, 56.0, 44.0)
  >>> m / n  # matrix division
  Matrix(2.5, -3.5, 3.5, -4.5, 5.5, -7.5)
  >>>
  >>> m / m  # result is equal to the Identity matrix
  Matrix(1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
  >>>
  >>> # look at this non-invertible matrix:
  >>> m = pymupdf.Matrix(1, 0, 1, 0, 1, 0)
  >>> ~m
  Matrix(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
  >>> # we try dividing by it in two ways:
  >>> p = pymupdf.Point(1, 2)
  >>> p * ~m  # this delivers point (0, 0):
  Point(0.0, 0.0)
  >>> p / m  # but this is an exception:
  Traceback (most recent call last):
    File "<pyshell#6>", line 1, in <module>
      p / m
    File "... /site-packages/fitz/pymupdf.py", line 869, in __truediv__
      raise ZeroDivisionError("matrix not invertible")
  ZeroDivisionError: matrix not invertible
  >>>


As a specialty, rectangles support additional binary operations:

* **intersection** -- the common area of rectangle-likes, operator *"&"*
* **inclusion** -- enlarge to include a point-like or rect-like, operator *"|"*
* **containment** check -- whether a point-like or rect-like is inside

Here is an example for creating the smallest rectangle enclosing given points::

  >>> # first define some point-likes
  >>> points = []
  >>> for i in range(10):
          for j in range(10):
              points.append((i, j))
  >>>
  >>> # now create a rectangle containing all these 100 points
  >>> # start with an empty rectangle
  >>> r = pymupdf.Rect(points[0], points[0])
  >>> for p in points[1:]:  # and include remaining points one by one
          r |= p
  >>> r  # here is the to be expected result:
  Rect(0.0, 0.0, 9.0, 9.0)
  >>> (4, 5) in r  # this point-like lies inside the rectangle
  True
  >>> # and this rect-like is also inside
  >>> (4, 4, 5, 5) in r
  True
  >>>

.. include:: footer.rst