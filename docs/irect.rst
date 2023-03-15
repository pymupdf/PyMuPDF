.. include:: header.rst

.. _IRect:

==========
IRect
==========

IRect is a rectangular bounding box, very similar to :ref:`Rect`, except that all corner coordinates are integers. IRect is used to specify an area of pixels, e.g. to receive image data during rendering. Otherwise, e.g. considerations concerning emptiness and validity of rectangles also apply to this class. Methods and attributes have the same names, and in many cases are implemented by re-using the respective :ref:`Rect` counterparts.

============================== ==============================================
**Attribute / Method**          **Short Description**
============================== ==============================================
:meth:`IRect.contains`         checks containment of another object
:meth:`IRect.get_area`         calculate rectangle area
:meth:`IRect.intersect`        common part with another rectangle
:meth:`IRect.intersects`       checks for non-empty intersection
:meth:`IRect.morph`            transform with a point and a matrix
:meth:`IRect.torect`           matrix that transforms to another rectangle
:meth:`IRect.norm`             the Euclidean norm
:meth:`IRect.normalize`        makes a rectangle finite
:attr:`IRect.bottom_left`      bottom left point, synonym *bl*
:attr:`IRect.bottom_right`     bottom right point, synonym *br*
:attr:`IRect.height`           height of the rectangle
:attr:`IRect.is_empty`         whether rectangle is empty
:attr:`IRect.is_infinite`      whether rectangle is infinite
:attr:`IRect.rect`             the :ref:`Rect` equivalent
:attr:`IRect.top_left`         top left point, synonym *tl*
:attr:`IRect.top_right`        top_right point, synonym *tr*
:attr:`IRect.quad`             :ref:`Quad` made from rectangle corners
:attr:`IRect.width`            width of the rectangle
:attr:`IRect.x0`               X-coordinate of the top left corner
:attr:`IRect.x1`               X-coordinate of the bottom right corner
:attr:`IRect.y0`               Y-coordinate of the top left corner
:attr:`IRect.y1`               Y-coordinate of the bottom right corner
============================== ==============================================

**Class API**

.. class:: IRect

   .. method:: __init__(self)

   .. method:: __init__(self, x0, y0, x1, y1)

   .. method:: __init__(self, irect)

   .. method:: __init__(self, sequence)

      Overloaded constructors. Also see examples below and those for the :ref:`Rect` class.

      If another irect is specified, a **new copy** will be made.

      If sequence is specified, it must be a Python sequence type of 4 numbers (see :ref:`SequenceTypes`). Non-integer numbers will be truncated, non-numeric values will raise an exception.

      The other parameters mean integer coordinates.


   .. method:: get_area([unit])

      Calculates the area of the rectangle and, with no parameter, equals *abs(IRect)*. Like an empty rectangle, the area of an infinite rectangle is also zero.

      :arg str unit: Specify required unit: respective squares of "px" (pixels, default), "in" (inches), "cm" (centimeters), or "mm" (millimeters).

      :rtype: float

   .. method:: intersect(ir)

      The intersection (common rectangular area) of the current rectangle and *ir* is calculated and replaces the current rectangle. If either rectangle is empty, the result is also empty. If either rectangle is infinite, the other one is taken as the result -- and hence also infinite if both rectangles were infinite.

      :arg rect_like ir: Second rectangle.

   .. method:: contains(x)

      Checks whether *x* is contained in the rectangle. It may be :data:`rect_like`, :data:`point_like` or a number. If *x* is an empty rectangle, this is always true. Conversely, if the rectangle is empty this is always *False*, if *x* is not an empty rectangle and not a number. If *x* is a number, it will be checked to be one of the four components. *x in irect* and *irect.contains(x)* are equivalent.

      :arg x: the object to check.
      :type x: :ref:`IRect` or :ref:`Rect` or :ref:`Point` or int

      :rtype: bool

   .. method:: intersects(r)

      Checks whether the rectangle and the :data:`rect_like` "r" contain a common non-empty :ref:`IRect`. This will always be *False* if either is infinite or empty.

      :arg rect_like r: the rectangle to check.

      :rtype: bool

   .. method:: torect(rect)

      * New in version 1.19.3
      
      Compute the matrix which transforms this rectangle to a given one. See :meth:`Rect.torect`.

      :arg rect_like rect: the target rectangle. Must not be empty or infinite.
      :rtype: :ref:`Matrix`
      :returns: a matrix `mat` such that `self * mat = rect`. Can for example be used to transform between the page and the pixmap coordinates.


   .. method:: morph(fixpoint, matrix)

      * New in version 1.17.0
      
      Return a new quad after applying a matrix to it using a fixed point.

      :arg point_like fixpoint: the fixed point.
      :arg matrix_like matrix: the matrix.
      :returns: a new :ref:`Quad`. This a wrapper of the same-named quad method. If infinite, the infinite quad is returned.

   .. method:: norm()

      * New in version 1.16.0
      
      Return the Euclidean norm of the rectangle treated as a vector of four numbers.

   .. method:: normalize()

      Make the rectangle finite. This is done by shuffling rectangle corners. After this, the bottom right corner will indeed be south-eastern to the top left one. See :ref:`Rect` for a more details.

   .. attribute:: top_left

   .. attribute:: tl

      Equals *Point(x0, y0)*.

      :type: :ref:`Point`

   .. attribute:: top_right

   .. attribute:: tr

      Equals *Point(x1, y0)*.

      :type: :ref:`Point`

   .. attribute:: bottom_left

   .. attribute:: bl

      Equals *Point(x0, y1)*.

      :type: :ref:`Point`

   .. attribute:: bottom_right

   .. attribute:: br

      Equals *Point(x1, y1)*.

      :type: :ref:`Point`

   .. attribute:: rect

      The :ref:`Rect` with the same coordinates as floats.

      :type: :ref:`Rect`

   .. attribute:: quad

      The quadrilateral *Quad(irect.tl, irect.tr, irect.bl, irect.br)*.

      :type: :ref:`Quad`

   .. attribute:: width

      Contains the width of the bounding box. Equals *abs(x1 - x0)*.

      :type: int

   .. attribute:: height

      Contains the height of the bounding box. Equals *abs(y1 - y0)*.

      :type: int

   .. attribute:: x0

      X-coordinate of the left corners.

      :type: int

   .. attribute:: y0

      Y-coordinate of the top corners.

      :type: int

   .. attribute:: x1

      X-coordinate of the right corners.

      :type: int

   .. attribute:: y1

      Y-coordinate of the bottom corners.

      :type: int

   .. attribute:: is_infinite

      *True* if rectangle is infinite, *False* otherwise.

      :type: bool

   .. attribute:: is_empty

      *True* if rectangle is empty, *False* otherwise.

      :type: bool


.. note::

   * This class adheres to the Python sequence protocol, so components can be accessed via their index, too. Also refer to :ref:`SequenceTypes`.
   * Rectangles can be used with arithmetic operators -- see chapter :ref:`Algebra`.

.. include:: footer.rst

