.. raw:: pdf

    PageBreak

============
Functions
============
The following are miscellaneous functions either directly available under the binding name, i.e. can be invoked as ``fitz.function``, or to be used by the experienced PDF programmer.

==================================== ==============================================
**Function**                         **Short Description**
==================================== ==============================================
:meth:`getPointDistance`             calculates the distance between two points
:meth:`Document._getPageObjNumber()` returns a pages XREF and generation number
:meth:`Document._getPageXREF()`      synonym of ``_getPageObjNumber()``
:meth:`Document._getObjectString()`  returns the string representing an object
:meth:`Document._getNewXref()`       creates and returns a new entry in the XREF
:meth:`Document._updateObject()`     inserts or updates a PDF object
:meth:`Document._getXrefLength()`    returns the length of the PDF XREF
:meth:`Document._getXrefStream()`    returns the the content of the stream
:meth:`Document._getOLRootNumber()`  returns / creates the outline root XREF
==================================== ==============================================


   .. method:: getPointDistance(p1, p2, unit = "pt")

      Calculates the distance between two points in either pixel points "pt" (default) or millimeters "mm". ``fitz.getPointDistance(p1, p2) == fitz.getPointDistance(p2, p1)`` always evaluates to ``True``.

      :param `p1`: First point
      :type `p1`: Point

      :param `p2`: Second point
      :type `p2`: Point

      :param `unit`: Unit specification, "pt" or "mm"
      :type `unit`: str

      :rtype: float

   .. method:: Document._getPageObjNumber(pno)

      PDF documents only: Returns the XREF and generation number for a given page.

      :param `pno`: Page number (zero-baed).
      :type `pno`: int.

      :rtype: list
      :returns: XREF and generation number of page ``pno`` as a list ``[xref, gen]``.

   .. method:: Document._getObjectString(xref)

      PDF documents only: Returns the string representing an arbitrary object. For stream objects, only the non-stream part is returned. To get the stream content, use ``_getXrefStream()`` (see below).

      :param `xref`: XREF number.
      :type `xref`: int.

      :rtype: string
      :returns: the string defining the object identified by ``xref``.

   .. method:: Document._getNewXref()

      PDF documents only: Increases the XREF by one entry and returns the entry's number.

      :rtype: int
      :returns: the number of the new XREF entry.

   .. method:: Document._updateObject(xref, obj_str)

      PDF documents only: Associates the object identified by string ``obj_str`` with the XREF number ``xref``. If ``xref`` already pointed to an object, it will be replaced by the new object.

      :param `xref`: XREF number.
      :type `xref`: int.

      :param `obj_str`: a string containing a valid PDF object definition.
      :type `obj_str`: str.

      :rtype: int
      :returns: zero if successful, otherwise an exception will be raised.

   .. method:: Document._getXrefLength()

      PDF documents only: Returns the length of the XREF table.

      :rtype: int
      :returns: the number of entries in the XREF table.

   .. method:: Document._getXrefStream(xref)

      PDF documents only: Returns the content stream of the object referenced by ``xref``. If the object has / is no stream, an exception is raised.

      :param `xref`: XREF number.
      :type `xref`: int.
      
      :rtype: str or bytes
      :returns: the (decompressed) stream of the object. This is a string in Python 2 and a ``bytes`` object in Python 3.

   .. method:: Document._getOLRootNumber()

      PDF documents only:  Returns the XREF number of the /Outlines root object (this is **not** the first outline entry!). If this object does not exist, a new one will be created.

      :rtype: int
      :returns: XREF number of the **/Outlines** root object.
