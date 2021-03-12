
.. _Matrix:

==========
Matrix
==========

Matrix is a row-major 3x3 matrix used by image transformations in MuPDF (which complies with the respective concepts laid down in the :ref:`AdobeManual`). With matrices you can manipulate the rendered image of a page in a variety of ways: (parts of) the page can be rotated, zoomed, flipped, sheared and shifted by setting some or all of just six float values.

.. |matrix| image:: images/img-matrix.*

Since all points or pixels live in a two-dimensional space, one column vector of that matrix is a constant unit vector, and only the remaining six elements are used for manipulations. These six elements are usually represented by *[a, b, c, d, e, f]*. Here is how they are positioned in the matrix:

|matrix|

Please note:

    * the below methods are just convenience functions -- everything they do, can also be achieved by directly manipulating the six numerical values
    * all manipulations can be combined -- you can construct a matrix that rotates **and** shears **and** scales **and** shifts, etc. in one go. If you however choose to do this, do have a look at the **remarks** further down or at the :ref:`AdobeManual`.

================================ ==============================================
**Method / Attribute**             **Description**
================================ ==============================================
:meth:`Matrix.preRotate`         perform a rotation
:meth:`Matrix.preScale`          perform a scaling
:meth:`Matrix.preShear`          perform a shearing (skewing)
:meth:`Matrix.preTranslate`      perform a translation (shifting)
:meth:`Matrix.concat`            perform a matrix multiplication
:meth:`Matrix.invert`            calculate the inverted matrix
:meth:`Matrix.norm`              the Euclidean norm
:attr:`Matrix.a`                 zoom factor X direction
:attr:`Matrix.b`                 shearing effect Y direction
:attr:`Matrix.c`                 shearing effect X direction
:attr:`Matrix.d`                 zoom factor Y direction
:attr:`Matrix.e`                 horizontal shift
:attr:`Matrix.f`                 vertical shift
:attr:`Matrix.isRectilinear`     true if rect corners will remain rect corners
================================ ==============================================

**Class API**

.. class:: Matrix

   .. method:: __init__(self)

   .. method:: __init__(self, zoom-x, zoom-y)

   .. method:: __init__(self, shear-x, shear-y, 1)

   .. method:: __init__(self, a, b, c, d, e, f)

   .. method:: __init__(self, matrix)

   .. method:: __init__(self, degree)

   .. method:: __init__(self, sequence)

      Overloaded constructors.

      Without parameters, the zero matrix *Matrix(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)* will be created.

      *zoom-** and *shear-** specify zoom or shear values (float) and create a zoom or shear matrix, respectively.

      For "matrix" a **new copy** of another matrix will be made.

      Float value "degree" specifies the creation of a rotation matrix which rotates anit-clockwise.

      A "sequence" must be any Python sequence object with exactly 6 float entries (see :ref:`SequenceTypes`).

      *fitz.Matrix(1, 1)*, *fitz.Matrix(0.0)* and *fitz.Matrix(fitz.Identity)* create modifyable versions of the :ref:`Identity` matrix, which looks like *[1, 0, 0, 1, 0, 0]*.

   .. method:: norm()

      *(New in version 1.16.0)*
      
      Return the Euclidean norm of the matrix as a vector.

   .. method:: preRotate(deg)

      Modify the matrix to perform a counter-clockwise rotation for positive *deg* degrees, else clockwise. The matrix elements of an identity matrix will change in the following way:

      *[1, 0, 0, 1, 0, 0] -> [cos(deg), sin(deg), -sin(deg), cos(deg), 0, 0]*.

      :arg float deg: The rotation angle in degrees (use conventional notation based on Pi = 180 degrees).

   .. method:: preScale(sx, sy)

      Modify the matrix to scale by the zoom factors sx and sy. Has effects on attributes *a* thru *d* only: *[a, b, c, d, e, f] -> [a*sx, b*sx, c*sy, d*sy, e, f]*.

      :arg float sx: Zoom factor in X direction. For the effect see description of attribute *a*.

      :arg float sy: Zoom factor in Y direction. For the effect see description of attribute *d*.

   .. method:: preShear(sx, sy)

      Modify the matrix to perform a shearing, i.e. transformation of rectangles into parallelograms (rhomboids). Has effects on attributes *a* thru *d* only: *[a, b, c, d, e, f] -> [c*sy, d*sy, a*sx, b*sx, e, f]*.

      :arg float sx: Shearing effect in X direction. See attribute *c*.

      :arg float sy: Shearing effect in Y direction. See attribute *b*.

   .. method:: preTranslate(tx, ty)

      Modify the matrix to perform a shifting / translation operation along the x and / or y axis. Has effects on attributes *e* and *f* only: *[a, b, c, d, e, f] -> [a, b, c, d, tx*a + ty*c, tx*b + ty*d]*.

      :arg float tx: Translation effect in X direction. See attribute *e*.

      :arg float ty: Translation effect in Y direction. See attribute *f*.

   .. method:: concat(m1, m2)

      Calculate the matrix product *m1 * m2* and store the result in the current matrix. Any of *m1* or *m2* may be the current matrix. Be aware that matrix multiplication is not commutative. So the sequence of *m1*, *m2* is important.

      :arg m1: First (left) matrix.
      :type m1: :ref:`Matrix`

      :arg m2: Second (right) matrix.
      :type m2: :ref:`Matrix`

   .. method:: invert(m = None)

      Calculate the matrix inverse of *m* and store the result in the current matrix. Returns *1* if *m* is not invertible ("degenerate"). In this case the current matrix **will not change**. Returns *0* if *m* is invertible, and the current matrix is replaced with the inverted *m*.

      :arg m: Matrix to be inverted. If not provided, the current matrix will be used.
      :type m: :ref:`Matrix`

      :rtype: int

   .. attribute:: a

      Scaling in X-direction **(width)**. For example, a value of 0.5 performs a shrink of the **width** by a factor of 2. If a < 0, a left-right flip will (additionally) occur.

      :type: float

   .. attribute:: b

      Causes a shearing effect: each *Point(x, y)* will become *Point(x, y - b*x)*. Therefore, looking from left to right, e.g. horizontal lines will be "tilt" -- downwards if b > 0, upwards otherwise (b is the tangens of the tilting angle).

      :type: float

   .. attribute:: c

      Causes a shearing effect: each *Point(x, y)* will become *Point(x - c*y, y)*. Therefore, looking upwards, vertical lines will be "tilt" -- to the left if c > 0, to the right otherwise (c ist the tangens of the tilting angle).

      :type: float

   .. attribute:: d

      Scaling in Y-direction **(height)**. For example, a value of 1.5 performs a stretch of the **height** by 50%. If d < 0, an up-down flip will (additionally) occur.

      :type: float

   .. attribute:: e

      Causes a horizontal shift effect: Each *Point(x, y)* will become *Point(x + e, y)*. Positive (negative) values of *e* will shift right (left).

      :type: float

   .. attribute:: f

      Causes a vertical shift effect: Each *Point(x, y)* will become *Point(x, y - f)*. Positive (negative) values of *f* will shift down (up).

      :type: float

   .. attribute:: isRectilinear

      Rectilinear means that no shearing is present and that any rotations are integer multiples of 90 degrees. Usually this is used to confirm that (axis-aligned) rectangles before the transformation are still axis-aligned rectangles afterwards.

      :type: bool

.. note::

   * This class adheres to the Python sequence protocol, so components can be accessed via their index, too. Also refer to :ref:`SequenceTypes`.
   * A matrix can be used with arithmetic operators -- see chapter :ref:`Algebra`.
   * Changes of matrix properties and execution of matrix methods can be executed consecutively. This is the same as multiplying the respective matrices.
   * Matrix multiplication is **not commutative** -- changing the execution sequence in general changes the result. So it can quickly become unclear which result a transformation will yield.

To keep results foreseeable for a series of matrix operations, Adobe recommends the following approach (:ref:`AdobeManual`, page 206):

1. Shift ("translate")
2. Rotate
3. Scale or shear ("skew")


Examples
-------------
Here are examples to illustrate some of the effects achievable. The following pictures start with a page of the PDF version of this help file. We show what happens when a matrix is being applied (though always full pages are created, only parts are displayed here to save space).

.. |original| image:: images/img-original.*

This is the original page image:

|original|

Shifting
------------
.. |e100| image:: images/img-e-is-100.*

We transform it with a matrix where *e = 100* (right shift by 100 pixels).

|e100|

.. |f100| image:: images/img-f-is-100.*

Next we do a down shift by 100 pixels: *f = 100*.

|f100|

Flipping
--------------
.. |aminus1| image:: images/img-a-is--1.*

Flip the page left-right (*a = -1*).

|aminus1|

.. |dminus1| image:: images/img-d-is--1.*

Flip up-down (*d = -1*).

|dminus1|

Shearing
----------------
.. |bnull5| image:: images/img-b-is-0.5.*

First a shear in Y direction (*b = 0.5*).

|bnull5|

.. |cnull5| image:: images/img-c-is-0.5.*

Second a shear in X direction (*c = 0.5*).

|cnull5|

Rotating
---------
.. |rot60| image:: images/img-rot-60.*

Finally a rotation by 30 clockwise degrees (*preRotate(-30)*).

|rot60|
