.. include:: header.rst

.. _Point:

================
Point
================

*Point* represents a point in the plane, defined by its x and y coordinates.

============================ ============================================
**Attribute / Method**       **Description**
============================ ============================================
:meth:`Point.distance_to`    calculate distance to point or rect
:meth:`Point.norm`           the Euclidean norm
:meth:`Point.transform`      transform point with a matrix
:attr:`Point.abs_unit`       same as unit, but positive coordinates
:attr:`Point.unit`           point coordinates divided by *abs(point)*
:attr:`Point.x`              the X-coordinate
:attr:`Point.y`              the Y-coordinate
============================ ============================================

**Class API**

.. class:: Point

   .. method:: __init__(self)

   .. method:: __init__(self, x, y)

   .. method:: __init__(self, point)

   .. method:: __init__(self, sequence)

      Overloaded constructors.

      Without parameters, *Point(0, 0)* will be created.

      With another point specified, a **new copy** will be created, "sequence" is a Python sequence of 2 numbers (see :ref:`SequenceTypes`).

     :arg float x: x coordinate of the point

     :arg float y: y coordinate of the point

   .. method:: distance_to(x [, unit])

      Calculate the distance to *x*, which may be :data:`point_like` or :data:`rect_like`. The distance is given in units of either pixels (default), inches, centimeters or millimeters.

     :arg point_like,rect_like x: to which to compute the distance.

     :arg str unit: the unit to be measured in. One of "px", "in", "cm", "mm".

     :rtype: float
     :returns: the distance to *x*. If this is :data:`rect_like`, then the distance

         * is the length of the shortest line connecting to one of the rectangle sides
         * is calculated to the **finite version** of it
         * is zero if it **contains** the point

   .. method:: norm()

      * New in version 1.16.0
      
      Return the Euclidean norm (the length) of the point as a vector. Equals result of function *abs()*.

   .. method:: transform(m)

      Apply a matrix to the point and replace it with the result.

     :arg matrix_like m: The matrix to be applied.

     :rtype: :ref:`Point`

   .. attribute:: unit

      Result of dividing each coordinate by *norm(point)*, the distance of the point to (0,0). This is a vector of length 1 pointing in the same direction as the point does. Its x, resp. y values are equal to the cosine, resp. sine of the angle this vector (and the point itself) has with the x axis.

      .. image:: images/img-point-unit.*

      :type: :ref:`Point`

   .. attribute:: abs_unit

      Same as :attr:`unit` above, replacing the coordinates with their absolute values.

      :type: :ref:`Point`

   .. attribute:: x

      The x coordinate

      :type: float

   .. attribute:: y

      The y coordinate

      :type: float

.. note::

   * This class adheres to the Python sequence protocol, so components can be accessed via their index, too. Also refer to :ref:`SequenceTypes`.
   * Rectangles can be used with arithmetic operators -- see chapter :ref:`Algebra`.

.. include:: footer.rst
