.. raw:: pdf

    PageBreak

.. _Rect:

==========
Rect
==========

``Rect`` represents a rectangle defined by its top left and its bottom right :ref:`Point` objects, in coordinates: ((x0, y0), (x1, y1)). Respectively, a rectangle can be defined in one of the four ways: as a pair of :ref:`Point` objects, as a tuple of four coordinates, or as an arbitrary combination of these.

Rectangle borders are always in parallel with the respective X- and Y-axes.
A rectangle is called *finite* if x0 <= x1 and y0 <= y1 is true, else *infinite*.

A rectangle is called *empty* if x0 = x1 or y0 = y1, i.e. if its area is zero.


============================= =======================================================
**Methods / Attributes**      **Short Description**
============================= =======================================================
:meth:`Rect.round`            create smallest :ref:`Irect` containing rectangle
:meth:`Rect.transform`        transform rectangle with a matrix
:meth:`Rect.intersect`        common part with another rectangle
:meth:`Rect.includePoint`     enlarge rectangle to also contain a point
:meth:`Rect.includeRect`      enlarge rectangle to also contain another one
:meth:`Rect.getRectArea`      calculate rectangle area
:attr:`Rect.height`           rectangle height
:attr:`Rect.width`            rectangle width
:attr:`Rect.x0`               top left corner's X-coordinate
:attr:`Rect.y0`               top left corner's Y-coordinate
:attr:`Rect.x1`               bottom right corner's X-coordinate
:attr:`Rect.y1`               bottom right corner's Y-coordinate
============================= =======================================================

**Class API**

.. class:: Rect

   .. method:: __init__(self, x0, y0, x1, y1)

      Constructor. Without parameters will create the empty rectangle ``Rect(0.0, 0.0, 0.0, 0.0)``.

   .. method:: __init__(self, p1, p2)

   .. method:: __init__(self, p1, x1, y1)

   .. method:: __init__(self, x0, y0, p2)

   .. method:: __init__(self, r)

      Overloaded constructors: ``p1``, ``p2`` stand for :ref:`Point` objects, ``r`` means another rectangle, while the other parameters mean float coordinates.

	  If ``r`` is specified, the constructor creates a **new copy** of ``r``.

   .. method:: round()

      Creates the smallest :ref:`IRect` containing ``Rect``. This is **not** the same as simply rounding each of the rectangle's coordinates! Look at the example below.

      :rtype: :ref:`IRect`

   .. method:: transform(m)

      Transforms rectangle with a matrix.

      :param `m`: The matrix to be used for the transformation.
      :type `m`: :ref:`Matrix`

   .. method:: intersect(r)

      The intersection (common rectangular area) of the current rectangle and ``r`` is calculated and replaces the current rectangle. If either rectangle is empty, the result is also empty. If one of the rectangles is infinite, the other one is taken as the result - and hence also infinite if both rectangles were infinite.

      :param `r`: Second rectangle
      :type `r`: :ref:`Rect`

   .. method:: includeRect(r)

      The smallest rectangle containing the current one and ``r`` is calculated and replaces the current one. If either rectangle is infinite, the result is also infinite. If one is empty, the other will be taken as the result (which will be empty if both were empty).

      :param `r`: Second rectangle
      :type `r`: :ref:`Rect`

   .. method:: includePoint(p)

      The smallest rectangle containing the current one and point ``p`` is calculated and replaces the current one. To create a rectangle to contain a series of points, start with the empty ``fitz.Rect(p1, p1)`` and successively perform ``includePoint`` operations for the other points.

      :param `p`: Point to include.
      :type `p`: :ref:`Point`

   .. method:: getRectArea(unit = 'pt')

      Calculates the area of the rectangle. The area of an infinite rectangle is always zero. So, at least one of ``fitz.Rect(p1, p2)`` and ``fitz.Rect(p2, p1)`` has a zero area.

      :param `unit`: Specify required unit: ``pt`` (pixel points, default) or ``mm`` (square millimeters).
      :type `unit`: string
      :rtype: float

   .. attribute:: width

      Contains the width of the rectangle. Equals ``x1 - x0``.

      :rtype: float

   .. attribute:: height

      Contains the height of the rectangle. Equals ``y1 - y0``.

      :rtype: float

   .. attribute:: x0

      X-coordinate of the top left corner.

      :type: float

   .. attribute:: y0

      Y-coordinate of the top left corner.

      :type: float

   .. attribute:: x1

      X-coordinate of the bottom right corner.

      :type: float

   .. attribute:: y1

      Y-coordinate of the bottom right corner.

      :type: float


Remark
------
A rectangle's coordinates can also be accessed via index, e.g. ``r.x0 == r[0]``.

Rect Algebra
-----------------
A number of arithmetics operations have been defined for the ``Rect`` class.

- **Addition:** ``r + x`` where ``r`` is a ``Rect`` and ``x`` can be a ``Rect``, ``IRect`` or a number. The result is a new ``Rect`` with added components of the operands. If ``x`` is a number, it is added to all components of ``r``.
- **Subtraction:** analogous to addition.
- **Negation:** ``-r`` is a new ``Rect`` with negated components of ``r``.
- **Inclusion:** ``r | x`` is the new ``Rect`` that also includes ``x``, which can be an ``IRect``, ``Rect`` or ``Point``.
- **Intersection:** ``r & x`` is a new ``Rect`` containing the area common to ``r`` and ``x`` which can be an ``IRect`` or ``Rect``.
- **Multiplication:** ``r * m`` is a new ``Rect`` containing ``r`` transformed with matrix ``m``.

Examples
----------

**Example 1:**
::
 >>> p1 = fitz.Point(10, 10)
 >>> p2 = fitz.Point(300, 450)
 >>>
 >>> fitz.Rect(p1, p2)
 fitz.Rect(10.0, 10.0, 300.0, 450.0)
 >>>
 >>> fitz.Rect(10, 10, 300, 450)
 fitz.Rect(10.0, 10.0, 300.0, 450.0)
 >>>
 >>> fitz.Rect(10, 10, p2)
 fitz.Rect(10.0, 10.0, 300.0, 450.0)
 >>>
 >>> fitz.Rect(p1, 300, 450)
 fitz.Rect(10.0, 10.0, 300.0, 450.0)

**Example 2:**
::
 >>> r = fitz.Rect(0.5, -0.01, 123.88, 455.123456)
 >>>
 >>> r
 fitz.Rect(0.5, -0.009999999776482582, 123.87999725341797, 455.1234436035156)
 >>>
 >>> r.round()
 fitz.IRect(0, -1, 124, 456)

**Example 3:**
::
  >>> m = fitz.Matrix(45)
  >>> r = fitz.Rect(10, 10, 410, 610)
  >>> r * m
  fitz.Rect(-424.2640686035156, 14.142135620117188, 282.84271240234375, 721.2489013671875)
  >>>
  >>> r | fitz.Point(5, 5)
  fitz.Rect(5.0, 5.0, 410.0, 610.0)
  >>>
  >>> r + 5
  fitz.Rect(15.0, 15.0, 415.0, 615.0)
  >>>
  >>> r & fitz.Rect(0, 0, 15, 15)
  fitz.Rect(10.0, 10.0, 15.0, 15.0)


As can be seen, all of the following evaluate to ``True``:

* ``r.round().x0 == int(math.floor(r.x0))``
* ``r.round().y0 == int(math.floor(r.y0))``
* ``r.round().x1 == int(math.ceil(r.x1))``
* ``r.round().y1 == int(math.ceil(r.y1))``.