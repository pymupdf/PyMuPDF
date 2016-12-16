.. raw:: pdf

    PageBreak

.. _Point:

================
Point
================

``Point`` represents a point in the plane, defined by its x and y coordinates.

======================== ====================================
**Attribute / Method**    **Short Description**
======================== ====================================
:meth:`Point.transform`  transform point with a matrix
:attr:`Point.x`          the X-coordinate
:attr:`Point.y`          the Y-coordinate
======================== ====================================

**Class API**

.. class:: Point

   .. method:: __init__(self, [x, y])

      Constructor. Without parameters defaulting to ``Point(0.0, 0.0)`` ("top left"). Also see the example below.

     :param `x`: X coordinate of the point
     :type `x`: float

     :param `y`: Y coordinate of the point
     :type `y`: float

   .. method:: __init__(self, p)

      Constructor. Makes a **new copy** of point ``p``.

     :param `p`: The point to copy from.
     :type `p`: :ref:`Point`

   .. method:: transform(m)

      Applies matrix ``m`` to the point.

     :param `m`: The matrix to be applied.
     :type `m`: :ref:`Matrix`

Remark
------
A point's ``p`` attributes ``x`` and ``y`` can also be accessed as indices, e.g. ``p.x == p[0]``.

Point Algebra
------------------
A number of arithmetics operations have been defined for the ``Point`` class:

- **Addition:** ``p + x`` is a new ``Point`` with added coordinates of ``p`` and ``x`` (another ``Point`` or a number). If ``x`` is a number, it is added to both components of ``p``.
- **Subtraction:** analogous to addition.
- **Negation:** ``-p`` is the point with negated coordinates of ``p``.
- **Multiplication:** ``p * m`` means ``p.transform(m)`` for matrix ``m``, however p is left untouched and a new point is returned.
- **Absolute Value:** ``abs(p)`` means the Euclidean norm of ``p``, i.e. its length as a vector.

Examples
---------
**Example 1:**
::
 >>> point = fitz.Point(25, 30)
 >>> point
 fitz.Point(25.0, 30.0)
 >>> m = fitz.Matrix(2, 2)
 >>> point.transform(m)
 fitz.Point(50.0, 60.0)

**Example 2:**
::
 >>> fitz.Point(25, 30) + 5
 fitz.Point(30.0, 35.0)
 >>>
 >>> fitz.Point(25, 30) + fitz.Point(1, 2)
 fitz.Point(26.0, 32.0)
 >>>
 >>> abs(fitz.Point(25, 30))
 39.05124837953327
