
.. _Matrix:

==========
Matrix
==========

Matrix is a row-major 3x3 matrix used by image transformations in MuPDF (which complies with the respective concepts laid down in the Adobe manual). With matrices you can manipulate the rendered image of a page in a variety of ways: (parts of) the page can be rotated, zoomed, flipped, sheared and shifted by setting some or all of just six float values.

.. |matrix| image:: matrix.png

Since all points or pixels live in a two-dimensional space, one column vector of that matrix is a constant unit vector, and only the remaining six elements are used for manipulations. These six elements are usually represented by ``[a, b, c, d, e, f]``. Here is how they are positioned in the matrix:

|matrix|

It should be noted, that

    * the below methods are just convenience functions - everything they do, can also be achieved by directly manipulating ``[a,b,c,d,e,f]``
    * all manipulations can be combined - you can construct a matrix that does a rotate **and** a shear **and** a scale **and** a shift, etc. in one go. If you however choose to do this, do have a look at the **remarks** further down or at the Adobe manual.


================================ ==============================================
**Method / Attribute**             **Description**
================================ ==============================================
:meth:`Matrix.preRotate`         perform a rotation
:meth:`Matrix.preScale`          perform a scaling
:meth:`Matrix.preShear`          perform a shearing (skewing)
:meth:`Matrix.preTranslate`      perform a translation (shifting)
:meth:`Matrix.concat`            perform a matrix multiplication
:meth:`Matrix.invert`            calculate the inverted matrix
:attr:`Matrix.a`                 zoom factor X direction
:attr:`Matrix.b`                 shearing effect Y direction
:attr:`Matrix.c`                 shearing effect X direction
:attr:`Matrix.d`                 zoom factor Y direction
:attr:`Matrix.e`                 horizontal shift
:attr:`Matrix.f`                 vertical shift
================================ ==============================================

**Class API**

.. class:: Matrix

   .. method:: __init__(self, sx, sy, [shear])

      Constructor. Creates a matrix with scale or shear factors ``sx``, ``sy`` in x and y direction, respectively. The boolean ``shear`` controls the meaning of the other two paramters. ``fitz.Matrix(1, 1)`` creates a modifyable version of the :ref:`Identity` matrix, which looks like ``[1, 0, 0, 1, 0, 0]``.

      :param `sx`: Scale or shear factor in x direction as controlled by ``shear``.
      :type `sx`: float

      :param `sy`: Scale or shear factor in y direction as controlled by ``shear``.
      :type `sy`: float

      :param `shear`: Controls whether ``sx`` and ``sy`` should be treated as scale or as shear factors. If shear is ``False`` (default), the scaling matrix ``[sx, 0, 0, sy, 0, 0]`` will be created. If ``shear`` is ``True``, the shearing matrix ``[1, sx, sy, 1, 0, 0]`` will be created.
      :type `shear`: bool

   .. method:: __init__(self, m)

      Constructor. Creates **a new copy** of matrix m.

      :param `m`: The matrix to copy from.
      :type `m`: :ref:`Matrix`

   .. method:: __init__(self, deg)

      Constructor. Creates a matrix that performs a rotation by ``deg`` degrees. See method ``preRotate()`` for details. ``fitz.Matrix(0)`` creates a modifyable version of the :ref:`Identity` matrix.

      :param `deg`: Rotation degrees.
      :type `deg`: float

   .. method:: preRotate(deg)

      Modify the matrix to perform a counterclockwise rotation for positive ``deg`` degrees, else clockwise. The matrix elements of an identity matrix will change in the following way:

      ``[1, 0, 0, 1, 0, 0] -> [cos(deg), sin(deg), -sin(deg), cos(deg), 0, 0]``.

      :param `deg`: The rotation angle in degrees (use conventional notation based on Pi = 180 degrees).
      :type `deg`: float

   .. method:: preScale(sx, sy)

      Modify the matrix to scale by the zoom factors sx and sy. Has effects on attributes ``a`` thru ``d`` only: ``[a, b, c, d, e, f] -> [a*sx, b*sx, c*sy, d*sy, e, f]``.

      :param `sx`: Zoom factor in X direction. For the effect see description of attribute ``a``.
      :type `sx`: float

      :param `sy`: Zoom factor in Y direction. For the effect see description of attribute ``d``.
      :type `sy`: float

   .. method:: preShear(sx, sy)

      Modify the matrix to perform a shearing, i.e. transformation of rectangles into parallelograms (rhomboids). Has effects on attributes ``a`` thru ``d`` only: ``[a, b, c, d, e, f] -> [c*sy, d*sy, a*sx, b*sx, e, f]``.

      :param `sx`: Shearing effect in X direction. See attribute ``c``.
      :type `sx`: float

      :param `sy`: Shearing effect in Y direction. See attribute ``b``.
      :type `sy`: float

   .. method:: preTranslate(tx, ty)

      Modify the matrix to perform a shifting / translation operation along the x and / or y axis. Has effects on attributes ``e`` and ``f`` only: ``[a, b, c, d, e, f] -> [a, b, c, d, tx*a + ty*c, tx*b + ty*d]``.

      :param `tx`: Translation effect in X direction. See attribute ``e``.
      :type `tx`: float

      :param `ty`: Translation effect in Y direction. See attribute ``f``.
      :type `ty`: float

   .. method:: concat(m1, m2)

      Calculate the matrix product ``m1 * m2`` and store the result in the current matrix. Any of ``m1`` or ``m2`` may be the current matrix. Be aware that matrix multiplication is not commutative. So the sequence of ``m1``, ``m2`` is important.

      :param `m1`: First (left) matrix.
      :type `m1`: :ref:`Matrix`

      :param `m2`: Second (right) matrix.
      :type `m2`: :ref:`Matrix`

   .. method:: invert(m)

      Calculate the matrix inverse of ``m`` and store the result in the current matrix. Returns ``1`` if ``m`` is not invertible ("degenerate"). In this case the current matrix **will not change**. Returns ``0`` if ``m`` is invertible, and the current matrix is replaced with the inverted ``m``.

      :param `m`: Matrix to be inverted.
      :type `m`: :ref:`Matrix`

      :rtype: int

   .. attribute:: a

      Scaling in X-direction **(width)**. For example, a value of 0.5 performs a shrink of the **width** by a factor of 2. If a < 0, a left-right flip will (additionally) occur.

      :type: float

   .. attribute:: b

      Causes a shearing effect: each ``Point(x, y)`` will become ``Point(x, y - b*x)``. Therefore, looking from left to right, e.g. horizontal lines will be "tilt" - downwards if b > 0, upwards otherwise (b is the tangens of the tilting angle).

      :type: float

   .. attribute:: c

      Causes a shearing effect: each ``Point(x, y)`` will become ``Point(x - c*y, y)``. Therefore, looking upwards, vertical lines will be "tilt" - to the left if c > 0, to the right otherwise (c ist the tangens of the tilting angle).

      :type: float

   .. attribute:: d

      Scaling in Y-direction **(height)**. For example, a value of 1.5 performs a stretch of the **height** by 50%. If d < 0, an up-down flip will (additionally) occur.

      :type: float

   .. attribute:: e

      Causes a horizontal shift effect: Each ``Point(x, y)`` will become ``Point(x + e, y)``. Positive (negative) values of ``e`` will shift right (left).

      :type: float

   .. attribute:: f

      Causes a vertical shift effect: Each ``Point(x, y)`` will become ``Point(x, y - f)``. Positive (negative) values of ``f`` will shift down (up).

      :type: float

Remarks 1
---------
For a matrix ``m``, properties ``a`` to ``f`` can also be accessed by index, e.g. ``m.a == m[0]`` and ``m[0] = 1`` has the same effect as ``m.a = 1``.

Remarks 2
---------
Obviously, changes of matrix properties and execution of matrix methods can be combined, i.e. executed consecutively. This is done by multiplying the respective matrices.

Matrix multiplications are **not commutative**, i.e. execution sequence determines the result: a **shift-rotate** is not equal a **rotate-shift** in general. So it can easily become unclear which result a transformation will yield. E.g. if you apply ``preRotate(x)`` to an arbitrary matrix ``[a, b, c, d, e, f]`` you will get the matrix ``[a*cos(x)+c*sin(x), b*cos(x)+d*sin(x), -a*sin(x)+c*cos(x), -b*sin(x)+d*cos(x), e, f]`` ...

In order to keep results foreseeable for a series of transformations, Adobe recommends the following sequence (see page 206 of their manual):

1. Shift ("translate")
2. Rotate
3. Scale or shear ("skew")

Matrix Algebra
-------------------
A number of arithmetics operations have been defined for the ``Matrix`` class. In what follows, m, m1, m2 are matrices:

* **Addition:** with ``m1 + m2`` is a new matrix containing ``[m1.a + m2.a, ..., m1.f + m2.f]``
* **Subtraction:** analogous to addition
* **Multiplication:** ``m1 * m2`` is a new matrix calculated as ``concat(m1, m2)``
* **Negation:** ``-m`` is the new matrix ``[-m.a, -m.b, ...]``
* **Inversion:** ``~m`` is the new matrix such that ``m * ~m = fitz.Identity``. If ``m`` is degenerate (not invertible), ``~m`` will be ``[0, 0, 0, 0, 0, 0]``.
* **Absolute Value:** ``abs(m)`` is a float containing the Euclidean norm of ``m``. Typically used for testing whether two matrices are "almost equal", like ``abs(m1 - m2) < epsilon``.
* **Non-Zero-Test:** You can test whether a matrix is all zero (``[0, 0, 0, 0, 0, 0]``): ``if not ~m: print "m is not invertible"``

This makes the following operations possible:
::
 >>> import fitz
 >>> m45p = fitz.Matrix(45)            # rotate 45 degrees counterclockwise
 >>> m45m = fitz.Matrix(-45)           # rotate 45 degrees clockwise
 >>> m90p = fitz.Matrix(90)            # rotate 90 degrees counterclockwise
 >>>
 >>> abs(m90p - m45p * m45p)           # should be (close to) zero
 8.429369702178807e-08
 >>>
 >>> abs(m45p * m45m - fitz.Identity)  # should be (close to) zero
 2.1073424255447017e-07
 >>>
 >>> abs(m45p - ~m45m)                 # should be (close to) zero
 2.384185791015625e-07
 >>>
 >>> m90p * m90p * m90p * m90p         # should be 360 degrees = fitz.Identity
 fitz.Matrix(1.0, -0.0, 0.0, 1.0, 0.0, 0.0)


Examples
-------------
Here are examples to illustrate some of the effects achievable. The following pictures start with a page of the PDF version of this help file. We show what happens when a matrix is being applied (though always full pages are created, only parts are displayed here to save space).

.. |original| image:: original.png

This is the original page image:

|original|

Shifting
------------
.. |e100| image:: e_is_100.png

We transform it with a matrix where ``e = 100`` (right shift by 100 pixels).

|e100|

.. |f100| image:: f_is_100.png

Next we do a down shift by 100 pixels: ``f = 100``.

|f100|

Flipping
--------------
.. |aminus1| image:: a_is_-1.png

Flip the page left-right (``a = -1``).

|aminus1|

.. |dminus1| image:: d_is_-1.png

Flip up-down (``d = -1``).

|dminus1|

Shearing
----------------
.. |bnull5| image:: b_is_0.5.png

First a shear in Y direction (``b = 0.5``).

|bnull5|

.. |cnull5| image:: c_is_0.5.png

Second a shear in X direction (``c = 0.5``).

|cnull5|

Rotating
---------
.. |rot60| image:: rot_60.png

Finally a rotation by 30 clockwise degrees (``preRotate(-30)``).

|rot60|