.. include:: header.rst

.. _Matrix:

==========
Matrix
==========

Matrix is a row-major 3x3 matrix used by image transformations in MuPDF (which complies with the respective concepts laid down in the :ref:`AdobeManual`). With matrices you can manipulate the rendered image of a page in a variety of ways: (parts of) the page can be rotated, zoomed, flipped, sheared and shifted by setting some or all of just six float values.


Since all points or pixels live in a two-dimensional space, one column vector of that matrix is a constant unit vector, and only the remaining six elements are used for manipulations. These six elements are usually represented by *[a, b, c, d, e, f]*. Here is how they are positioned in the matrix:

.. image:: images/img-matrix.*


Please note:

    * the below methods are just convenience functions -- everything they do, can also be achieved by directly manipulating the six numerical values
    * all manipulations can be combined -- you can construct a matrix that rotates **and** shears **and** scales **and** shifts, etc. in one go. If you however choose to do this, do have a look at the **remarks** further down or at the :ref:`AdobeManual`.

================================ ==============================================
**Method / Attribute**             **Description**
================================ ==============================================
:meth:`Matrix.prerotate`         perform a rotation
:meth:`Matrix.prescale`          perform a scaling
:meth:`Matrix.preshear`          perform a shearing (skewing)
:meth:`Matrix.pretranslate`      perform a translation (shifting)
:meth:`Matrix.concat`            perform a matrix multiplication
:meth:`Matrix.invert`            calculate the inverted matrix
:meth:`Matrix.norm`              the Euclidean norm
:attr:`Matrix.a`                 zoom factor X direction
:attr:`Matrix.b`                 shearing effect Y direction
:attr:`Matrix.c`                 shearing effect X direction
:attr:`Matrix.d`                 zoom factor Y direction
:attr:`Matrix.e`                 horizontal shift
:attr:`Matrix.f`                 vertical shift
:attr:`Matrix.is_rectilinear`    true if rect corners will remain rect corners
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

      Float value "degree" specifies the creation of a rotation matrix which rotates anti-clockwise.

      A "sequence" must be any Python sequence object with exactly 6 float entries (see :ref:`SequenceTypes`).

      *pymupdf.Matrix(1, 1)* and *pymupdf.Matrix(pymupdf.Identity)* create modifiable versions of the :ref:`Identity` matrix, which looks like *[1, 0, 0, 1, 0, 0]*.

   .. method:: norm()

      * New in version 1.16.0
      
      Return the Euclidean norm of the matrix as a vector.

   .. method:: prerotate(deg)

      Modify the matrix to perform a counter-clockwise rotation for positive *deg* degrees, else clockwise. The matrix elements of an identity matrix will change in the following way:

      *[1, 0, 0, 1, 0, 0] -> [cos(deg), sin(deg), -sin(deg), cos(deg), 0, 0]*.

      :arg float deg: The rotation angle in degrees (use conventional notation based on Pi = 180 degrees).

   .. method:: prescale(sx, sy)

      Modify the matrix to scale by the zoom factors sx and sy. Has effects on attributes *a* thru *d* only: *[a, b, c, d, e, f] -> [a*sx, b*sx, c*sy, d*sy, e, f]*.

      :arg float sx: Zoom factor in X direction. For the effect see description of attribute *a*.

      :arg float sy: Zoom factor in Y direction. For the effect see description of attribute *d*.

   .. method:: preshear(sx, sy)

      Modify the matrix to perform a shearing, i.e. transformation of rectangles into parallelograms (rhomboids). Has effects on attributes *a* thru *d* only: *[a, b, c, d, e, f] -> [c*sy, d*sy, a*sx, b*sx, e, f]*.

      :arg float sx: Shearing effect in X direction. See attribute *c*.

      :arg float sy: Shearing effect in Y direction. See attribute *b*.

   .. method:: pretranslate(tx, ty)

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

      Causes a shearing effect: each `Point(x, y)` will become `Point(x, y - b*x)`. Therefore, horizontal lines will be "tilt".

      :type: float

   .. attribute:: c

      Causes a shearing effect: each `Point(x, y)` will become `Point(x - c*y, y)`. Therefore, vertical lines will be "tilt".

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

   .. attribute:: is_rectilinear

      Rectilinear means that no shearing is present and that any rotations are integer multiples of 90 degrees. Usually this is used to confirm that (axis-aligned) rectangles before the transformation are still axis-aligned rectangles afterwards.

      :type: bool

.. note::

   * This class adheres to the Python sequence protocol, so components can be accessed via their index, too. Also refer to :ref:`SequenceTypes`.
   * Matrices can be used with arithmetic operators almost like ordinary numbers: they can be added, subtracted, multiplied or divided -- see chapter :ref:`Algebra`.
   * Matrix multiplication is **not commutative** -- changing the sequence of the multiplicands will change the result in general. So it can quickly become unclear which result a transformation will yield.


Examples
-------------
Here are examples that illustrate some of the achievable effects. All pictures show some text, inserted under control of some matrix and relative to a fixed reference point (the red dot).

1. The :ref:`Identity` matrix performs no operation.

.. image:: images/img-matrix-0.*
   :scale: 66

2. The scaling matrix `Matrix(2, 0.5)` stretches by a factor of 2 in horizontal, and shrinks by factor 0.5 in vertical direction.

.. image:: images/img-matrix-1.*
   :scale: 66

3. Attributes :attr:`Matrix.e` and :attr:`Matrix.f` shift horizontally and, respectively vertically. In the following 10 to the right and 20 down.

.. image:: images/img-matrix-2.*
   :scale: 66

4. A negative :attr:`Matrix.a` causes a left-right flip.

.. image:: images/img-matrix-3.*
   :scale: 66

5. A negative :attr:`Matrix.d` causes an up-down flip.

.. image:: images/img-matrix-4.*
   :scale: 66

6. Attribute :attr:`Matrix.b` tilts upwards / downwards along the x-axis.

.. image:: images/img-matrix-5.*
   :scale: 66

7. Attribute :attr:`Matrix.c` tilts left / right along the y-axis.

.. image:: images/img-matrix-6.*
   :scale: 66

8. Matrix `Matrix(beta)` performs counterclockwise rotations for positive angles `beta`.

.. image:: images/img-matrix-7.*
   :scale: 66

9. Show some effects on a rectangle::

      import pymupdf
      
      # just definitions and a temp PDF
      RED = (1, 0, 0)
      BLUE = (0, 0, 1)
      GREEN = (0, 1, 0)
      doc = pymupdf.open()
      page = doc.new_page()
      
      # rectangle
      r1 = pymupdf.Rect(100, 100, 200, 200)
      
      # scales down by 50% in x- and up by 50% in y-direction
      mat1 = pymupdf.Matrix(0.5, 1.5)
      
      # shifts by 50 in both directions
      mat2 = pymupdf.Matrix(1, 0, 0, 1, 50, 50)
      
      # draw corresponding rectangles
      page.draw_rect(r1, color=RED)  # original
      page.draw_rect(r1 * mat1, color=GREEN)  # scaled
      page.draw_rect(r1 * mat2, color=BLUE)  # shifted
      doc.ez_save("matrix-effects.pdf")


.. image:: images/img-matrix-9.*
   :scale: 66

.. include:: footer.rst
