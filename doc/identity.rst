.. raw:: pdf

    PageBreak

.. _Identity:

============
Identity
============

Identity is just a :ref:`Matrix` that performs no action, to be used whenever the syntax requires a :ref:`Matrix`, but no actual transformation should take place.

Identity is a constant, an "immutable" object. So, all of its matrix properties are read-only and its methods are disabled.

If you need a do-nothing matrix as a starting point, use ``fitz.Matrix(1, 1)`` or ``fitz.Matrix(0)`` instead, like so:
::
 >>> fitz.Matrix(0).preTranslate(2, 5)
 fitz.Matrix(1.0, 0.0, -0.0, 1.0, 2.0, 5.0)

