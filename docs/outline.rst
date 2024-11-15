.. include:: header.rst

.. _Outline:

================
Outline
================

*outline* (or "bookmark"), is a property of *Document*. If not *None*, it stands for the first outline item of the document. Its properties in turn define the characteristics of this item and also point to other outline items in "horizontal" or downward direction. The full tree of all outline items for e.g. a conventional table of contents (TOC) can be recovered by following these "pointers".

============================ ==================================================
**Method / Attribute**       **Short Description**
============================ ==================================================
:attr:`Outline.down`         next item downwards
:attr:`Outline.next`         next item same level
:attr:`Outline.page`         page number (0-based)
:attr:`Outline.title`        title
:attr:`Outline.uri`          string further specifying outline target
:attr:`Outline.is_external`  target outside document
:attr:`Outline.is_open`      whether sub-outlines are open or collapsed
:attr:`Outline.dest`         points to destination details object
============================ ==================================================

**Class API**

.. class:: Outline

   .. attribute:: down

      The next outline item on the next level down. Is *None* if the item has no children.

      :type: :ref:`Outline`

   .. attribute:: next

      The next outline item at the same level as this item. Is *None* if this is the last one in its level.

      :type: `Outline`

   .. attribute:: page

      The page number (0-based) this bookmark points to.

      :type: int

   .. attribute:: title

      The item's title as a string or *None*.

      :type: str

   .. attribute:: is_open

      Indicator showing whether any sub-outlines should be expanded (*True*) or be collapsed (*False*). This information is interpreted by PDF reader software.

      :type: bool

   .. attribute:: is_external

      A bool specifying whether the target is outside (*True*) of the current document.

      :type: bool

   .. attribute:: uri

      A string specifying the link target. The meaning of this property should
      be evaluated in conjunction with property `is_external`:
      
      *
        `is_external` is true: ``uri`` points to some target outside the current
        PDF, which may be an internet resource (``uri`` starts with ``http://`` or
        similar), another file (``uri`` starts with ``file:`` or ``file://``) or some
        other service like an e-mail address (``uri`` starts with ``mailto:``).

      *
        `is_external` is false: ``uri`` will be `None` or point to an
        internal location. In case of PDF documents, this should either be
        *#nnnn* to indicate a 1-based (!) page number *nnnn*, or a named
        location. The format varies for other document types, for example
        "../FixedDoc.fdoc#PG_2_LNK_1" for page number 2 (1-based) in an XPS
        document.

      :type: str

   .. attribute:: dest

      The link destination details object.

      :type: :ref:`linkDest`

.. include:: footer.rst
