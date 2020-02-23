.. _Quad:

==========
Quad
==========

Represents a four-sided mathematical shape (also called "quadrilateral" or "tetragon") in the plane, defined as a sequence of four :ref:`Point` objects ul, ur, ll, lr (conveniently called upper left, upper right, lower left, lower right).

Quads can **be obtained** as results of text search methods (:meth:`Page.searchFor`), and they **are used** to define text marker annotations (see e.g. :meth:`Page.addSquigglyAnnot` and friends), and in several draw methods (like :meth:`Page.drawQuad` / :meth:`Shape.drawQuad`, :meth:`Page.drawOval`/ :meth`Shape.drawQuad`).

.. note::

   * If the corners of a rectangle are transformed with a **rotation**, **scale** or **translation** :ref:`Matrix`, then the resulting quad is **rectangular**, i.e. its corners again enclose angles of 90 degrees. Property :attr:`Quad.isRectangular` checks whether a quad can be thought of being the result of such an operation. This is not true for all matrices: e.g. shear matrices produce parallelograms, and non-invertible matrices deliver "degenerate" tetragons like triangles or lines.

   * Attribute :attr:`Quad.rect` obtains the envelopping rectangle. Vice versa, rectangles now have attributes :attr:`Rect.quad`, resp. :attr:`IRect.quad` to obtain their respective tetragon versions.

============================= =======================================================
**Methods / Attributes**      **Short Description**
============================= =======================================================
:meth:`Quad.transform`        transform with a matrix
:attr:`Quad.ul`               upper left point
:attr:`Quad.ur`               upper right point
:attr:`Quad.ll`               lower left point
:attr:`Quad.lr`               lower right point
:attr:`Quad.isConvex`         true if quad is a convex set
:attr:`Quad.isEmpty`          true if quad is an empty set
:attr:`Quad.isRectangular`    true if quad is a (rotated) rectangle
:attr:`Quad.rect`             smallest containing :ref:`Rect`
:attr:`Quad.width`            the longest width value
:attr:`Quad.height`           the longest height value
============================= =======================================================

**Class API**

.. class:: Quad

   .. method:: __init__(self)

   .. method:: __init__(self, ul, ur, ll, lr)

   .. method:: __init__(self, quad)

   .. method:: __init__(self, sequence)

      Overloaded constructors: "ul", "ur", "ll", "lr" stand for :data:`point_like` objects (the four corners), "sequence" is a Python sequence with four :data:`point_like` objects.

      If "quad" is specified, the constructor creates a **new copy** of it.

      Without parameters, a quad consisting of 4 copies of *Point(0, 0)* is created.


   .. method:: transform(matrix)

      Modify the quadrilateral by transforming each of its corners with a matrix.

      :arg matrix_like matrix: the matrix.

   .. attribute:: rect

      The smallest rectangle containing the quad, represented by the blue area in the following picture.

      .. image:: images/img-quads.jpg

      :type: :ref:`Rect`

   .. attribute:: ul

      Upper left point.

      :type: :ref:`Point`

   .. attribute:: ur

      Upper right point.

      :type: :ref:`Point`

   .. attribute:: ll

      Lower left point.

      :type: :ref:`Point`

   .. attribute:: lr

      Lower right point.

      :type: :ref:`Point`

   .. attribute:: isConvex

      *(New in version 1.16.1)*
      
      True if all lines are contained in the quad which connect two points of the quad. 

      :type: bool

   .. attribute:: isEmpty

      True if enclosed area is zero, which means that all four points are on the same line. If this is false, the quad may still be degenerate or not look like a rectangle at all (triangles, parallelograms, trapezoids, ...).

      :type: bool

   .. attribute:: isRectangular

      True if all angles are 90 degrees. This also implies that the area is **not empty** and **convex**.

      :type: bool

   .. attribute:: width

      The maximum length of the top and the bottom side.

      :type: float

   .. attribute:: height

      The maximum length of the left and the right side.

      :type: float

Remark
------
This class adheres to the sequence protocol, so components can be dealt with via their indices, too. Also refer to :ref:`SequenceTypes`.

We are still in process to extend algebraic operations to quads. Multiplication and division with / by numbers and matrices are already defined. Addition, subtraction and any unary operations may follow when we see an actual need.
