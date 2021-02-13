.. _Link:

================
Link
================
Represents a pointer to somewhere (this document, other documents, the internet). Links exist per document page, and they are forward-chained to each other, starting from an initial link which is accessible by the :attr:`Page.first_link` property.

There is a parent-child relationship between a link and its page. If the page object becomes unusable (closed document, any document structure change, etc.), then so does every of its existing link objects -- an exception is raised saying that the object is "orphaned", whenever a link property or method is accessed.

========================= ============================================
**Attribute**             **Short Description**
========================= ============================================
:meth:`Link.setBorder`    modify border properties
:meth:`Link.setColors`    modify color properties
:attr:`Link.border`       border characteristics
:attr:`Link.colors`       border line color
:attr:`Link.dest`         points to link destination details
:attr:`Link.isExternal`   external link destination?
:attr:`Link.next`         points to next link
:attr:`Link.rect`         clickable area in untransformed coordinates.
:attr:`Link.uri`          link destination
:attr:`Link.xref`         :data:`xref` number of the entry
========================= ============================================

**Class API**

.. class:: Link

   .. method:: setBorder(border=None, width=0, style=None, dashes=None)

      PDF only: Change border width and dashing properties.

      *(Changed in version 1.16.9)* Allow specification without using a dictionary. The direct parameters are used if *border* is not a dictionary.

      :arg dict border: a dictionary as returned by the :attr:`border` property, with keys *"width"* (*float*), *"style"* (*str*) and *"dashes"* (*sequence*). Omitted keys will leave the resp. property unchanged. To e.g. remove dashing use: *"dashes": []*. If dashes is not an empty sequence, "style" will automatically be set to "D" (dashed).

      :arg float width: see above.
      :arg str style: see above.
      :arg sequence dashes: see above.

   .. method:: setColors(colors=None, stroke=None, fill=None)

      Changes the "stroke" and "fill" colors.

      *(Changed in version 1.16.9)* Allow colors to be directly set. These parameters are used if *colors* is not a dictionary.

      :arg dict colors: a dictionary containing color specifications. For accepted dictionary keys and values see below. The most practical way should be to first make a copy of the *colors* property and then modify this dictionary as required.
      :arg sequence stroke: see above.
      :arg sequence fill: see above.


   .. attribute:: colors

      Meaningful for PDF only: A dictionary of two lists of floats in range *0 <= float <= 1* specifying the *stroke* and the interior (*fill*) colors. If not a PDF, *None* is returned. The stroke color is used for borders and everything that is actively painted or written ("stroked"). The lengths of these lists implicitely determine the colorspaces used: 1 = GRAY, 3 = RGB, 4 = CMYK. So *[1.0, 0.0, 0.0]* stands for RGB color red. Both lists can be *[]* if no color is specified. The value of each float *f* is mapped to the integer value *i* in range 0 to 255 via the computation *f = i / 255*.

      :rtype: dict

   .. attribute:: border

      Meaningful for PDF only: A dictionary containing border characteristics. It will be *None* for non-PDFs and an empty dictionary if no border information exists. The following keys can occur:

      * *width* -- a float indicating the border thickness in points. The value is -1.0 if no width is specified.

      * *dashes* -- a sequence of integers specifying a line dash pattern. *[]* means no dashes, *[n]* means equal on-off lengths of *n* points, longer lists will be interpreted as specifying alternating on-off length values. See the :ref:`AdobeManual` page 217 for more details.

      * *style* -- 1-byte border style: *S* (Solid) = solid rectangle surrounding the annotation, *D* (Dashed) = dashed rectangle surrounding the link, the dash pattern is specified by the *dashes* entry, *B* (Beveled) = a simulated embossed rectangle that appears to be raised above the surface of the page, *I* (Inset) = a simulated engraved rectangle that appears to be recessed below the surface of the page, *U* (Underline) = a single line along the bottom of the annotation rectangle.

      :rtype: dict
      
   .. attribute:: rect

      The area that can be clicked in untransformed coordinates.

      :type: :ref:`Rect`

   .. attribute:: isExternal

      A bool specifying whether the link target is outside of the current document.

      :type: bool

   .. attribute:: uri

      A string specifying the link target. The meaning of this property should be evaluated in conjunction with property *isExternal*. The value may be *None*, in which case *isExternal == False*. If *uri* starts with *file://*, *mailto:*, or an internet resource name, *isExternal* is *True*. In all other cases *isExternal == False* and *uri* points to an internal location. In case of PDF documents, this should either be *#nnnn* to indicate a 1-based (!) page number *nnnn*, or a named location. The format varies for other document types, e.g. *uri = '../FixedDoc.fdoc#PG_2_LNK_1'* for page number 2 (1-based) in an XPS document.

      :type: str

   .. attribute:: xref

      An integer specifying the PDF :data:`xref`. Zero if not a PDF.

      :type: int

   .. attribute:: next

      The next link or *None*.

      :type: *Link*

   .. attribute:: dest

      The link destination details object.

      :type: :ref:`linkDest`
