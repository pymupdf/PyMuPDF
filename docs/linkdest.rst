.. include:: header.rst

.. _linkDest:

================
linkDest
================
Class representing the `dest` property of an outline entry or a link. Describes the destination to which such entries point.

.. note:: Up to MuPDF v1.9.0 this class existed inside MuPDF and was dropped in version 1.10.0. For backward compatibility, PyMuPDF is still maintaining it, although some of its attributes are no longer backed by data actually available via MuPDF.

=========================== ====================================
**Attribute**               **Short Description**
=========================== ====================================
:attr:`linkDest.dest`       destination
:attr:`linkDest.fileSpec`   file specification (path, filename)
:attr:`linkDest.flags`      descriptive flags
:attr:`linkDest.isMap`      is this a MAP?
:attr:`linkDest.isUri`      is this a URI?
:attr:`linkDest.kind`       kind of destination
:attr:`linkDest.lt`         top left coordinates
:attr:`linkDest.named`      name if named destination
:attr:`linkDest.newWindow`  name of new window
:attr:`linkDest.page`       page number
:attr:`linkDest.rb`         bottom right coordinates
:attr:`linkDest.uri`        URI
=========================== ====================================

**Class API**

.. class:: linkDest

   .. attribute:: dest

      Target destination name if :attr:`linkDest.kind` is :data:`LINK_GOTOR` and :attr:`linkDest.page` is *-1*.

      :type: str

   .. attribute:: fileSpec

      Contains the filename and path this link points to, if :attr:`linkDest.kind` is :data:`LINK_GOTOR` or :data:`LINK_LAUNCH`.

      :type: str

   .. attribute:: flags

      A bitfield describing the validity and meaning of the different aspects of the destination. As far as possible, link destinations are constructed such that e.g. :attr:`linkDest.lt` and :attr:`linkDest.rb` can be treated as defining a bounding box. But the flags indicate which of the values were actually specified, see :ref:`linkDest Flags`.

      :type: int

   .. attribute:: isMap

      This flag specifies whether to track the mouse position when the URI is resolved. Default value: False.

      :type: bool

   .. attribute:: isUri

      Specifies whether this destination is an internet resource (as opposed to e.g. a local file specification in URI format).

      :type: bool

   .. attribute:: kind

      Indicates the type of this destination, like a place in this document, a URI, a file launch, an action or a place in another file. Look at :ref:`linkDest Kinds` to see the names and numerical values.

      :type: int

   .. attribute:: lt

      The top left :ref:`Point` of the destination.

      :type: :ref:`Point`

   .. attribute:: named

      This destination refers to some named action to perform (e.g. a javascript, see :ref:`AdobeManual`). Standard actions provided are *NextPage*, *PrevPage*, *FirstPage*,  and *LastPage*.

      :type: str

   .. attribute:: newWindow

      If true, the destination should be launched in a new window.

      :type: bool

   .. attribute:: page

      The page number (in this or the target document) this destination points to. Only set if :attr:`linkDest.kind` is :data:`LINK_GOTOR` or :data:`LINK_GOTO`. May be *-1* if :attr:`linkDest.kind` is :data:`LINK_GOTOR`. In this case :attr:`linkDest.dest` contains the **name** of a destination in the target document.

      :type: int

   .. attribute:: rb

      The bottom right :ref:`Point` of this destination.

      :type: :ref:`Point`

   .. attribute:: uri

      The name of the URI this destination points to.

      :type: str

.. include:: footer.rst
