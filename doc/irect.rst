.. _IRect:

==========
IRect
==========

IRect is a rectangular bounding box similar to :ref:`Rect`, except that all corner coordinates are integers. IRect is used to specify an area of pixels, e.g. to receive image data during rendering.

============================== ===========================================
**Attribute / Method**          **Short Description**
============================== ===========================================
:meth:`IRect.getRect`          return a :ref:`Rect` with same coordinates
:meth:`IRect.getRectArea`      calculate the area of the rectangle
:meth:`IRect.intersect`        common part with another rectangle
:meth:`IRect.translate`        shift rectangle
:attr:`IRect.width`            width of the rectangle
:attr:`IRect.height`           height of the rectangle
:attr:`IRect.x0`               X-coordinate of the top left corner
:attr:`IRect.y0`               Y-coordinate of the top left corner
:attr:`IRect.x1`               X-coordinate of the bottom right corner
:attr:`IRect.y1`               Y-coordinate of the bottom right corner
============================== ===========================================

**Class API**

.. class:: IRect

   .. method:: __init__(self, x0, y0, x1, y1)

      Constructor. Without parameters defaulting to ``IRect(0, 0, 0, 0)``, an empty rectangle. Also see the example below. Function :meth:`Rect.round` creates the smallest ``IRect`` containing ``Rect``.

      :param `x0`: Top-left x coordinate.
      :type `x0`: int

      :param `y0`: Top-left y coordinate.
      :type `y0`: int

      :param `x1`: Bottom-right x coordinate.
      :type `x1`: int

      :param `y1`: Bottom-right y coordinate.
      :type `y1`: int

   .. method:: getRect()

      A convenience function returning a :ref:`Rect` with the same coordinates as floating point values.

      :rtype: :ref:`Rect`

   .. method:: getRectArea(unit = 'pt')

      Calculates the area of the rectangle.

      :param `unit`: Specify the unit: ``pt`` (square pixel points, default) or ``mm`` (square millimeters).

      :type `unit`: string

      :rtype: float

   .. method:: intersect(ir)

      The intersection (common rectangular area) of the current rectangle and ``ir`` is calculated and replaces the current rectangle. If either rectangle is empty, the result is also empty. If one of the rectangles is infinite, the other one is taken as the result - and hence also infinite if both rectangles were infinite.

      :param `ir`: Second rectangle.

      :type `ir`: :ref:`IRect`


   .. method:: translate(tx, ty)

      Modifies the rectangle to perform a shift in x and / or y direction.

      :param `tx`: Number of pixels to shift horizontally. Negative values mean shifting left.
      :type `tx`: int

      :param `ty`: Number of pixels to shift vertically. Negative values mean shifting down.
      :type `ty`: int


   .. attribute:: width

      Contains the width of the bounding box. Equals ``x1 - x0``.

      :type: int

   .. attribute:: height

      Contains the height of the bounding box. Equals ``y1 - y0``.

      :type: int

   .. attribute:: x0

      X-coordinate of the top left corner.

      :type: int


   .. attribute:: y0

      Y-coordinate of the top left corner.

      :type: int

   .. attribute:: x1

      X-coordinate of the bottom right corner.

      :type: int


   .. attribute:: y1

      Y-coordinate of the bottom right corner.

      :type: int


Remark
------
A rectangle's coordinates can also be accessed via index, e.g. ``r.x0 == r[0]``.

IRect Algebra
------------------
A number of arithmetics operations have been defined for the ``IRect`` class.

- **Addition:** ``ir + x`` where ``ir`` is an ``IRect`` and ``x`` is a number, ``Rect`` or ``IRect``. The result is a new ``IRect`` with added components of the operands. If ``x`` is a number, it is added to all components of ``ir``.
- **Subtraction:** analogous to addition.
- **Negation:** ``-ir`` is a new ``IRect`` with negated components of ``ir``.
- **Inclusion:** ``ir | x`` is the new ``IRect`` that also includes ``x``, which can be a ``Rect``, ``IRect`` or ``Point``.
- **Intersection:** ``ir & x`` is a new ``IRect`` containing the area common to ``ir`` and ``x`` which can be a ``Rect`` or ``IRect``.
- **Multiplication:** ``ir * m`` is a new ``IRect`` containing ``ir`` transformed with matrix ``m``.

Examples
---------
**Example 1:**
::
  >>> ir = fitz.IRect(10, 10, 410, 610)
  >>> ir
  fitz.IRect(10, 10, 410, 610)
  >>> ir.height
  600
  >>> ir.width
  400
  >>> ir.getRectArea(unit = 'mm')
  29868.51852

**Example 2:**
::
  >>> m = fitz.Matrix(45)
  >>> ir = fitz.IRect(10, 10, 410, 610)
  >>> ir * m
  fitz.IRect(-425, 14, 283, 722)
  >>>
  >>> ir | fitz.Point(5, 5)
  fitz.IRect(5, 5, 410, 610)
  >>>
  >>> ir + 5
  fitz.IRect(15, 15, 415, 615)
  >>>
  >>> ir & fitz.Rect(0.0, 0.0, 15.0, 15.0)
  fitz.IRect(10, 10, 15, 15)

