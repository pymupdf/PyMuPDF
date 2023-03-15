.. include:: header.rst

.. _Quad:

==========
Quad
==========

Represents a four-sided mathematical shape (also called "quadrilateral" or "tetragon") in the plane, defined as a sequence of four :ref:`Point` objects ul, ur, ll, lr (conveniently called upper left, upper right, lower left, lower right).

Quads can **be obtained** as results of text search methods (:meth:`Page.search_for`), and they **are used** to define text marker annotations (see e.g. :meth:`Page.add_squiggly_annot` and friends), and in several draw methods (like :meth:`Page.draw_quad` / :meth:`Shape.draw_quad`, :meth:`Page.draw_oval`/ :meth:`Shape.draw_quad`).

.. note::

   * If the corners of a rectangle are transformed with a **rotation**, **scale** or **translation** :ref:`Matrix`, then the resulting quad is **rectangular** (= congruent to a rectangle), i.e. all of its corners again enclose angles of 90 degrees. Property :attr:`Quad.is_rectangular` checks whether a quad can be thought of being the result of such an operation.

   * This is not true for all matrices: e.g. shear matrices produce parallelograms, and non-invertible matrices deliver "degenerate" tetragons like triangles or lines.

   * Attribute :attr:`Quad.rect` obtains the enveloping rectangle. Vice versa, rectangles now have attributes :attr:`Rect.quad`, resp. :attr:`IRect.quad` to obtain their respective tetragon versions.


============================= =======================================================
**Methods / Attributes**      **Short Description**
============================= =======================================================
:meth:`Quad.transform`        transform with a matrix
:meth:`Quad.morph`            transform with a point and matrix
:attr:`Quad.ul`               upper left point
:attr:`Quad.ur`               upper right point
:attr:`Quad.ll`               lower left point
:attr:`Quad.lr`               lower right point
:attr:`Quad.is_convex`        true if quad is a convex set
:attr:`Quad.is_empty`         true if quad is an empty set
:attr:`Quad.is_rectangular`   true if quad is congruent to a rectangle
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

   .. method:: morph(fixpoint, matrix)

      *(New in version 1.17.0)* "Morph" the quad with a matrix-like using a point-like as fixed point.

      :arg point_like fixpoint: the point.
      :arg matrix_like matrix: the matrix.
      :returns: a new quad (no operation if this is the infinite quad).


   .. attribute:: rect

      The smallest rectangle containing the quad, represented by the blue area in the following picture.

      .. image:: images/img-quads.*

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

   .. attribute:: is_convex

      * New in version 1.16.1

      Checks if for any two points of the quad, all points on their connecting line also belong to the quad.

         .. image:: images/img-convexity.*
            :scale: 30

      :type: bool

   .. attribute:: is_empty

      True if enclosed area is zero, which means that at least three of the four corners are on the same line. If this is false, the quad may still be degenerate or not look like a tetragon at all (triangles, parallelograms, trapezoids, ...).

      :type: bool

   .. attribute:: is_rectangular

      True if all corner angles are 90 degrees. This implies that the quad is **convex and not empty**.

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

Algebra and Containment Checks
-------------------------------
Starting with v1.19.6, quads can be used in algebraic expressions like the other geometry object -- the respective restrictions have been lifted. In particular, all the following combinations of containment checking are now possible:

`{Point | IRect | Rect | Quad} in {IRect | Rect | Quad}`

Please note the following interesting detail:

For a rectangle, only its top-left point belongs to it. Since v1.19.0, rectangles are defined to be "open", such that its bottom and its right edge do not belong to it -- including the respective corners. But for quads there exists no such notion like "openness", so we have the following somewhat surprising implication:

   >>> rect.br in rect
   False
   >>> # but:
   >>> rect.br in rect.quad
   True

.. include:: footer.rst
