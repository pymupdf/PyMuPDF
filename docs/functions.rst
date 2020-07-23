============
Functions
============
The following are miscellaneous functions and attributes on a fairly low-level technical detail.

Some functions provide detail access to PDF structures. Others are stripped-down, high performance versions of other functions which provide more information.

Yet others are handy, general-purpose utilities.


==================================== ==============================================================
**Function**                         **Short Description**
==================================== ==============================================================
:meth:`Annot._cleanContents`         PDF only: clean the annot's :data:`contents` objects
:meth:`Annot.setAPNMatrix`           PDF only: set the matrix of the appearance object
:meth:`Annot.setAPNMatrix`           PDF only: set the matrix of the appearance object
:attr:`Annot.APNMattrix`             PDF only: the matrix of the appearance object
:attr:`Annot.APNBBox`                PDF only: bbox of the appearance object
:meth:`ConversionHeader`             return header string for *getText* methods
:meth:`ConversionTrailer`            return trailer string for *getText* methods
:meth:`Document._delXmlMetadata`     PDF only: remove XML metadata
:meth:`Document._deleteObject`       PDF only: delete an object
:meth:`Document._getNewXref`         PDF only: create and return a new :data:`xref` entry
:meth:`Document._getOLRootNumber`    PDF only: return / create :data:`xref` of */Outline*
:meth:`Document._getPDFroot`         PDF only: return the :data:`xref` of the catalog
:meth:`Document._getPageObjNumber`   PDF only: return :data:`xref` and generation number of a page
:meth:`Document._getPageXref`        PDF only: same as *_getPageObjNumber()*
:meth:`Document._getTrailerString`   PDF only: return the PDF file trailer string
:meth:`Document._getXmlMetadataXref` PDF only: return XML metadata :data:`xref` number
:meth:`Document._getXrefLength`      PDF only: return length of :data:`xref` table
:meth:`Document._getXrefStream`      PDF only: return content of a stream object
:meth:`Document._getXrefString`      PDF only: return object definition "source"
:meth:`Document._make_page_map`      PDF only: create a fast-access array of page numbers
:meth:`Document._updateObject`       PDF only: insert or update a PDF object
:meth:`Document._updateStream`       PDF only: replace the stream of an object
:meth:`Document.extractFont`         PDF only: extract embedded font
:meth:`Document.extractImage`        PDF only: extract embedded image
:meth:`Document.getCharWidths`       PDF only: return a list of glyph widths of a font
:meth:`Document.isStream`            PDF only: check whether an :data:`xref` is a stream object
:attr:`Document.FontInfos`           PDF only: information on inserted fonts
:meth:`ImageProperties`              return a dictionary of basic image properties
:meth:`getPDFnow`                    return the current timestamp in PDF format
:meth:`getPDFstr`                    return PDF-compatible string
:meth:`getTextlength`                return string length for a given font & fontsize
:meth:`Page.cleanContents`           PDF only: clean the page's :data:`contents` objects
:meth:`Page._getContents`            PDF only: return a list of content numbers
:meth:`Page._setContents`            PDF only: set page's :data:`contents` to some :data:`xref`
:meth:`Page.getDisplayList`          create the page's display list
:meth:`Page.getTextBlocks`           extract text blocks as a Python list
:meth:`Page.getTextWords`            extract text words as a Python list
:meth:`Page.run`                     run a page through a device
:meth:`Page.readContents`            PDF only: get complete, concatenated /Contents source
:meth:`Page.wrapContents`            wrap contents with stacking commands
:attr:`Page._isWrapped`              check whether contents wrapping is present
:meth:`planishLine`                  matrix to map a line to the x-axis
:meth:`PaperSize`                    return width, height for a known paper format
:meth:`PaperRect`                    return rectangle for a known paper format
:meth:`sRGB_to_pdf`                  return PDF RGB color tuple from a sRGB integer
:meth:`sRGB_to_rgb`                  return (R, G, B) color tuple from a sRGB integer
:meth:`make_table`                   return list of table cells for a given rectangle
:attr:`paperSizes`                   dictionary of pre-defined paper formats
==================================== ==============================================================

   .. method:: PaperSize(s)

      Convenience function to return width and height of a known paper format code. These values are given in pixels for the standard resolution 72 pixels = 1 inch.

      Currently defined formats include **'A0'** through **'A10'**, **'B0'** through **'B10'**, **'C0'** through **'C10'**, **'Card-4x6'**, **'Card-5x7'**, **'Commercial'**, **'Executive'**, **'Invoice'**, **'Ledger'**, **'Legal'**, **'Legal-13'**, **'Letter'**, **'Monarch'** and **'Tabloid-Extra'**, each in either portrait or landscape format.

      A format name must be supplied as a string (case **in** \sensitive), optionally suffixed with "-L" (landscape) or "-P" (portrait). No suffix defaults to portrait.

      :arg str s: any format name from above (upper or lower case), like *"A4"* or *"letter-l"*.

      :rtype: tuple
      :returns: *(width, height)* of the paper format. For an unknown format *(-1, -1)* is returned. Esamples: *fitz.PaperSize("A4")* returns *(595, 842)* and *fitz.PaperSize("letter-l")* delivers *(792, 612)*.

-----

   .. method:: PaperRect(s)

      Convenience function to return a :ref:`Rect` for a known paper format.

      :arg str s: any format name supported by :meth:`PaperSize`.

      :rtype: :ref:`Rect`
      :returns: *fitz.Rect(0, 0, width, height)* with *width, height=fitz.PaperSize(s)*.

      >>> import fitz
      >>> fitz.PaperRect("letter-l")
      fitz.Rect(0.0, 0.0, 792.0, 612.0)
      >>>

-----

   .. method:: sRGB_to_pdf(srgb)

      *New in v1.17.4*

      Convenience function returning a PDF color triple (red, green, blue) for a given sRGB color integer as it occurs in :meth:`Page.getText` dictionaries "dict" and "rawdict".

      :arg int srgb: an integer of format RRGGBB, where each color component is an integer in range(255).

      :returns: a tuple (red, green, blue) with float items in intervall *0 <= item <= 1* representing the same color.

-----

   .. method:: sRGB_to_rgb(srgb)

      *New in v1.17.4*

      Convenience function returning a color (red, green, blue) for a given sRGB color integer .

      :arg int srgb: an integer of format RRGGBB, where each color component is an integer in range(255).

      :returns: a tuple (red, green, blue) with integer items in intervall *0 <= item <= 255* representing the same color.

-----

   .. method:: make_table(rect=(0, 0, 1, 1), cols=1, rows=1)

      *New in v1.17.4*

      Convenience function returning a list of <rows x cols> :ref:`Rect` objects representing equal sized table cells for the given rectangle.

      :arg rect_like rect: the rectangle to contain the table.
      :arg int cols: the desired number of columns.
      :arg int rows: the desired number of rows.
      :returns: a list of :ref:`Rect` objects of equal size, whose union equals *rect*::

         [
            [cell00, cell01, ...]  # row 0
            ...
            [...]  # last row
         ]

-----

   .. method:: planishLine(p1, p2)

      *(New in version 1.16.2)*
      
      Return a matrix which maps the line from p1 to p2 to the x-axis such that p1 will become (0,0) and p2 a point with the same distance to (0,0).

      :arg point_like p1: starting point of the line.
      :arg point_like p2: end point of the line.

      :rtype: :ref:`Matrix`
      :returns:
         
         a matrix which combines a rotation and a translation::

            p1 = fitz.Point(1, 1)
            p2 = fitz.Point(4, 5)
            abs(p2 - p1)  # distance of points
            5.0
            m = fitz.planishLine(p1, p2)
            p1 * m
            Point(0.0, 0.0)
            p2 * m
            Point(5.0, -5.960464477539063e-08)
            # distance of the resulting points
            abs(p2 * m - p1 * m)
            5.0
 

         .. image:: images/img-planish.png
            :scale: 40


-----

   .. attribute:: paperSizes

      A dictionary of pre-defines paper formats. Used as basis for :meth:`PaperSize`.

-----

   .. method:: getPDFnow()

      Convenience function to return the current local timestamp in PDF compatible format, e.g. *D:20170501121525-04'00'* for local datetime May 1, 2017, 12:15:25 in a timezone 4 hours westward of the UTC meridian.

      :rtype: str
      :returns: current local PDF timestamp.

-----

   .. method:: getTextlength(text, fontname="helv", fontsize=11, encoding=TEXT_ENCODING_LATIN)

      *(New in version 1.14.7)*
      
      Calculate the length of text on output with a given **builtin** font, fontsize and encoding.

      :arg str text: the text string.
      :arg str fontname: the fontname. Must be one of either the :ref:`Base-14-Fonts` or the CJK fonts, identified by their "reserved" fontnames (see table in :meth.`Page.insertFont`).
      :arg float fontsize: size of the font.
      :arg int encoding: the encoding to use. Besides 0 = Latin, 1 = Greek and 2 = Cyrillic (Russian) are available. Relevant for Base-14 fonts "Helvetica", "Courier" and "Times" and their variants only. Make sure to use the same value as in the corresponding text insertion.
      :rtype: float
      :returns: the length in points the string will have (e.g. when used in :meth:`Page.insertText`).

      .. note:: This function will only do the calculation -- it won't insert font or text.

      .. warning:: If you use this function to determine the required rectangle width for the (:ref:`Page` or :ref:`Shape`) *insertTextbox* methods, be aware that they calculate on a **by-character level**. Because of rounding effects, this will mostly lead to a slightly larger number: *sum([fitz.getTextlength(c) for c in text]) > fitz.getTextlength(text)*. So either (1) do the same, or (2) use something like *fitz.getTextlength(text + "'")* for your calculation.

-----

   .. method:: getPDFstr(text)

      Make a PDF-compatible string: if the text contains code points *ord(c) > 255*, then it will be converted to UTF-16BE with BOM as a hexadecimal character string enclosed in "<>" brackets like *<feff...>*. Otherwise, it will return the string enclosed in (round) brackets, replacing any characters outside the ASCII range with some special code. Also, every "(", ")" or backslash is escaped with an additional backslash.

      :arg str text: the object to convert

      :rtype: str
      :returns: PDF-compatible string enclosed in either *()* or *<>*.

-----

   .. method:: ImageProperties(stream)

      *(New in version 1.14.14)*

      Return a number of basic properties for an image.

      :arg bytes|bytearray|BytesIO|file stream: an image either in memory or an **opened** file. A memory resident image maybe any of the formats *bytes*, *bytearray* or *io.BytesIO*.

      :returns: a dictionary with the following keys (an empty dictionary for any error):

         ========== ====================================================
         **Key**    **Value**
         ========== ====================================================
         width      (int) width in pixels
         height     (int) height in pixels
         colorspace (int) colorspace.n (e.g. 3 = RGB)
         bpc        (int) bits per component (usually 8)
         format     (int) image format in *range(15)*
         ext        (str) image file extension indicating the format
         size       (int) length of the image in bytes
         ========== ====================================================

      Example:

      >>> fitz.ImageProperties(open("img-clip.jpg","rb"))
      {'bpc': 8, 'format': 9, 'colorspace': 3, 'height': 325, 'width': 244, 'ext': 'jpeg', 'size': 14161}
      >>>


-----

   .. method:: ConversionHeader("text", filename="UNKNOWN")

      Return the header string required to make a valid document out of page text outputs.

      :arg str output: type of document. Use the same as the output parameter of *getText()*.

      :arg str filename: optional arbitrary name to use in output types "json" and "xml".

      :rtype: str

-----

   .. method:: ConversionTrailer(output)

      Return the trailer string required to make a valid document out of page text outputs. See :meth:`Page.getText` for an example.

      :arg str output: type of document. Use the same as the output parameter of *getText()*.

      :rtype: str

-----

   .. method:: Document._deleteObject(xref)

      PDF only: Delete an object given by its cross reference number.

      :arg int xref: the cross reference number. Must be within the document's valid :data:`xref` range.

      .. warning:: Only use with extreme care: this may make the PDF unreadable.

-----

   .. method:: Document._delXmlMetadata()

      Delete an object containing XML-based metadata from the PDF. (Py-) MuPDF does not support XML-based metadata. Use this if you want to make sure that the conventional metadata dictionary will be used exclusively. Many thirdparty PDF programs insert their own metadata in XML format and thus may override what you store in the conventional dictionary. This method deletes any such reference, and the corresponding PDF object will be deleted during next garbage collection of the file.

-----

   .. method:: Document._getTrailerString(compressed=False)

      *(New in version 1.14.9)*
      
      Return the trailer of the PDF (UTF-8), which is usually located at the PDF file's end. If not a PDF or the PDF has no trailer (because of irrecoverable errors), *None* is returned.

      :arg bool compressed: *(ew in version 1.14.14)* whether to generate a compressed output or one with nice indentations to ease reading (default).

      :returns: a string with the PDF trailer information. This is the analogous method to :meth:`Document._getXrefString` except that the trailer has no identifying :data:`xref` number. As can be seen here, the trailer object points to other important objects:

      >>> doc=fitz.open("adobe.pdf")
      >>> # compressed output
      >>> print(doc._getTrailerString(True))
      <</Size 334093/Prev 25807185/XRefStm 186352/Root 333277 0 R/Info 109959 0 R
      /ID[(\\227\\366/gx\\016ds\\244\\207\\326\\261\\\\\\305\\376u)
      (H\\323\\177\\346\\371pkF\\243\\262\\375\\346\\325\\002)]>>
      >>> # non-compressed otput:
      >>> print(doc._getTrailerString(False))
      <<
         /Size 334093
         /Prev 25807185
         /XRefStm 186352
         /Root 333277 0 R
         /Info 109959 0 R
         /ID [ (\227\366/gx\016ds\244\207\326\261\\\305\376u) (H\323\177\346\371pkF\243\262\375\346\325\002) ]
      >>

      .. note:: MuPDF is capable of recovering from a number of damages a PDF may have. This includes re-generating a trailer, where the end of a file has been lost (e.g. because of incomplete downloads). If however *None* is returned for a PDF, then the recovery mechanisms were unsuccessful and you should check for any error messages (:attr:`Document.openErrCode`, :attr:`Document.openErrMsg`, :attr:`Tools.fitz_stderr`).


-----

   .. method:: Document._make_page_map()

      Create an internal array of page numbers, which significantly speeds up page lookup (:meth:`Document.loadPage`). If this array exists, finding a page object will be up to two times faster. Functions which change the PDF's page layout (copy, delete, move, select pages) will destroy this array again.

-----

   .. method:: Document._getXmlMetadataXref()

      Return the XML-based metadata :data:`xref` of the PDF if present -- also refer to :meth:`Document._delXmlMetadata`. You can use it to retrieve the content via :meth:`Document._getXrefStream` and then work with it using some XML software.

      :rtype: int
      :returns: :data:`xref` of PDF file level XML metadata.

-----

   .. method:: Document._getPageObjNumber(pno)

      or

   .. method:: Document._getPageXref(pno)

       Return the :data:`xref` and generation number for a given page.

      :arg int pno: Page number (zero-based).

      :rtype: list
      :returns: :data:`xref` and generation number of page *pno* as a list *[xref, gen]*.

-----

   .. method:: Document._getPDFroot()

       Return the :data:`xref` of the PDF catalog.

      :rtype: int
      :returns: :data:`xref` of the PDF catalog -- a central :data:`dictionary` pointing to many other PDF information.

-----

   .. method:: Page.run(dev, transform)

      Run a page through a device.

      :arg dev: Device, obtained from one of the :ref:`Device` constructors.
      :type dev: :ref:`Device`

      :arg transform: Transformation to apply to the page. Set it to :ref:`Identity` if no transformation is desired.
      :type transform: :ref:`Matrix`

-----

   .. method:: Page.wrapContents

      Put string pair "q" / "Q" before, resp. after a page's */Contents* object(s) to ensure that any "geometry" changes are **local** only.

      Use this method as an alternative, minimalistic version of :meth:`Page.cleanContents`. Its advantage is a small footprint in terms of processing time and impact on incremental saves.

-----

   .. attribute:: Page._isWrapped

      Indicate whether :meth:`Page.wrapContents` may be required for object insertions in standard PDF geometry. Please note that this is a quick, basic check only: a value of *False* may still be a false alarm.

-----

   .. method:: Page.getTextBlocks(flags=None)

      Deprecated wrapper for :meth:`TextPage.extractBLOCKS`.

-----

   .. method:: Page.getTextWords(flags=None)

      Deprecated wrapper for :meth:`TextPage.extractWORDS`.

-----

   .. method:: Page.getDisplayList()

      Run a page through a list device and return its display list.

      :rtype: :ref:`DisplayList`
      :returns: the display list of the page.

-----

   .. method:: Page._getContents()

      Return a list of :data:`xref` numbers of :data:`contents` objects belonging to the page.

      :rtype: list
      :returns: a list of :data:`xref` integers.

      Each page may have zero to many associated contents objects (:data:`stream` \s) which contain some operator syntax describing what appears where and how on the page (like text or images, etc. See the :ref:`AdobeManual`, chapter "Operator Summary", page 985). This function only enumerates the number(s) of such objects. To get the actual stream source, use function :meth:`Document._getXrefStream` with one of the numbers in this list. Use :meth:`Document._updateStream` to replace the content.

-----

   .. method:: Page._setContents(xref)

      PDF only: Set a given object (identified by its :data:`xref`) as the page's one and only :data:`contents` object. Useful for joining mutiple :data:`contents` objects as in the following snippet::

         >>> c = b""
         >>> xreflist = page._getContents()
         >>> for xref in xreflist:
                 c += doc._getXrefStream(xref)
         >>> doc._updateStream(xreflist[0], c)
         >>> page._setContents(xreflist[0])
         >>> # doc.save(..., garbage=1) will remove the unused objects

      :arg int xref: the cross reference number of a :data:`contents` object. An exception is raised if outside the valid :data:`xref` range or not a stream object.

-----

   .. method:: Page.cleanContents()

      Clean and concatenate all :data:`contents` objects associated with this page. "Cleaning" includes syntactical corrections, standardizations and "pretty printing" of the contents stream. Discrepancies between :data:`contents` and :data:`resources` objects will also be corrected. See :meth:`Page._getContents` for more details.

      Changed in version 1.16.0 Annotations are no longer implicitely cleaned by this method. Use :meth:`Annot._cleanContents` separately.

      .. warning:: This is a complex function which may generate large amounts of new data and render other data unused. It is **not recommended** using it together with the **incremental save** option. Also note that the resulting singleton new */Contents* object is **uncompressed**. So you should save to a **new file** using options *"deflate=True, garbage=3"*.

-----

   .. method:: Page.readContents()

      *New in version 1.17.0.*
      Return the concatenation of all :data:`contents` objects associated with the page -- without cleaning or otherwise modifying them. Use this method whenever you need to parse this source in its entirety whithout having to bother how many separate contents objects exist.


-----

   .. method:: Annot._cleanContents()

      Clean the :data:`contents` streams associated with the annotation. This is the same type of action which :meth:`Page._cleanContents` performs -- just restricted to this annotation.


-----

   .. method:: Document.getCharWidths(xref=0, limit=256)

      Return a list of character glyphs and their widths for a font that is present in the document. A font must be specified by its PDF cross reference number :data:`xref`. This function is called automatically from :meth:`Page.insertText` and :meth:`Page.insertTextbox`. So you should rarely need to do this yourself.

      :arg int xref: cross reference number of a font embedded in the PDF. To find a font :data:`xref`, use e.g. *doc.getPageFontList(pno)* of page number *pno* and take the first entry of one of the returned list entries.

      :arg int limit: limits the number of returned entries. The default of 256 is enforced for all fonts that only support 1-byte characters, so-called "simple fonts" (checked by this method). All :ref:`Base-14-Fonts` are simple fonts.

      :rtype: list
      :returns: a list of *limit* tuples. Each character *c* has an entry  *(g, w)* in this list with an index of *ord(c)*. Entry *g* (integer) of the tuple is the glyph id of the character, and float *w* is its normalized width. The actual width for some fontsize can be calculated as *w * fontsize*. For simple fonts, the *g* entry can always be safely ignored. In all other cases *g* is the basis for graphically representing *c*.

      This function calculates the pixel width of a string called *text*::

       def pixlen(text, widthlist, fontsize):
       try:
           return sum([widthlist[ord(c)] for c in text]) * fontsize
       except IndexError:
           m = max([ord(c) for c in text])
           raise ValueError:("max. code point found: %i, increase limit" % m)

-----

   .. method:: Document._getXrefString(xref, compressed=False)

      Return the string ("source code") representing an arbitrary object. For :data:`stream` objects, only the non-stream part is returned. To get the stream data, use :meth:`_getXrefStream`.

      :arg int xref: :data:`xref` number.
      :arg bool compressed: *(new in version 1.14.14)* whether to generate a compressed output or one with nice indentations to ease reading or parsing (default).

      :rtype: string
      :returns: the string defining the object identified by :data:`xref`. Example:

      >>> doc = fitz.open("Adobe PDF Reference 1-7.pdf")  # the PDF
      >>> page = doc[100]  # some page in it
      >>> print(doc._getXrefString(page.xref, compressed=True))
      <</CropBox[0 0 531 666]/Annots[4795 0 R 4794 0 R 4793 0 R 4792 0 R 4797 0 R 4796 0 R]
      /Parent 109820 0 R/StructParents 941/Contents 229 0 R/Rotate 0/MediaBox[0 0 531 666]
      /Resources<</Font<</T1_0 3914 0 R/T1_1 3912 0 R/T1_2 3957 0 R/T1_3 3913 0 R/T1_4 4576 0 R
      /T1_5 3931 0 R/T1_6 3944 0 R>>/ProcSet[/PDF/Text]/ExtGState<</GS0 333283 0 R>>>>
      /Type/Page>>
      >>> print(doc._getXrefString(page.xref, compressed=False))
      <<
         /CropBox [ 0 0 531 666 ]
         /Annots [ 4795 0 R 4794 0 R 4793 0 R 4792 0 R 4797 0 R 4796 0 R ]
         /Parent 109820 0 R
         /StructParents 941
         /Contents 229 0 R
         /Rotate 0
         /MediaBox [ 0 0 531 666 ]
         /Resources <<
            /Font <<
               /T1_0 3914 0 R
               /T1_1 3912 0 R
               /T1_2 3957 0 R
               /T1_3 3913 0 R
               /T1_4 4576 0 R
               /T1_5 3931 0 R
               /T1_6 3944 0 R
            >>
            /ProcSet [ /PDF /Text ]
            /ExtGState <<
               /GS0 333283 0 R
            >>
         >>
         /Type /Page
      >>

-----

   .. method:: Document.isStream(xref)

      *(New in version 1.14.14)*
      
      PDF only: Check whether the object represented by :data:`xref` is a :data:`stream` type. Return is *False* if not a PDF or if the number is outside the valid xref range.

      :arg int xref: :data:`xref` number.

      :returns: *True* if the object definition is followed by data wrapped in keyword pair *stream*, *endstream*.

-----

   .. method:: Document._getNewXref()

      Increase the :data:`xref` by one entry and return that number. This can then be used to insert a new object.

      :rtype: int
      :returns: the number of the new :data:`xref` entry.

-----

   .. method:: Document._updateObject(xref, obj_str, page=None)

      Associate the object identified by string *obj_str* with *xref*, which must already exist. If *xref* pointed to an existing object, this will be replaced with the new object. If a page object is specified, links and other annotations of this page will be reloaded after the object has been updated.

      :arg int xref: :data:`xref` number.

      :arg str obj_str: a string containing a valid PDF object definition.

      :arg page: a page object. If provided, indicates, that annotations of this page should be refreshed (reloaded) to reflect changes incurred with links and / or annotations.
      :type page: :ref:`Page`

      :rtype: int
      :returns: zero if successful, otherwise an exception will be raised.

-----

   .. method:: Document._getXrefLength()

      Return length of :data:`xref` table.

      :rtype: int
      :returns: the number of entries in the :data:`xref` table.

-----

   .. method:: Document._getXrefStream(xref)

      Return the decompressed stream of the object referenced by *xref*. For non-stream objects *None* is returned.

      :arg int xref: :data:`xref` number.

      :rtype: bytes
      :returns: the (decompressed) stream of the object.

-----

   .. method:: Document._updateStream(xref, stream, new=False)

      Replace the stream of an object identified by *xref*. If the object has no stream, an exception is raised unless *new=True* is used. The function automatically performs a compress operation ("deflate") where beneficial.

      :arg int xref: :data:`xref` number.

      :arg bytes|bytearray|BytesIO stream: the new content of the stream.

         *(Changed in version 1.14.13:)* *io.BytesIO* objects are now also supported.

      :arg bool new: whether to force accepting the stream, and thus **turning it into a stream object**.

      This method is intended to manipulate streams containing PDF operator syntax (see pp. 985 of the :ref:`AdobeManual`) as it is the case for e.g. page content streams.

      If you update a contents stream, you should use save parameter *clean=True*. This ensures consistency between PDF operator source and the object structure.

      Example: Let us assume that you no longer want a certain image appear on a page. This can be achieved by deleting the respective reference in its contents source(s) -- and indeed: the image will be gone after reloading the page. But the page's :data:`resources` object would still show the image as being referenced by the page. This save option will clean up any such mismatches.

-----

   .. method:: Document._getOLRootNumber()

       Return :data:`xref` number of the /Outlines root object (this is **not** the first outline entry!). If this object does not exist, a new one will be created.

      :rtype: int
      :returns: :data:`xref` number of the **/Outlines** root object.

   .. method:: Document.extractImage(xref)

      PDF Only: Extract data and meta information of an image stored in the document. The output can directly be used to be stored as an image file, as input for PIL, :ref:`Pixmap` creation, etc. This method avoids using pixmaps wherever possible to present the image in its original format (e.g. as JPEG).

      :arg int xref: :data:`xref` of an image object. If this is not in *range(1, doc.xrefLength())*, or the object is no image or other errors occur, *None* is returned and no exception is raised.

      :rtype: dict
      :returns: a dictionary with the following keys

        * *ext* (*str*) image type (e.g. *'jpeg'*), usable as image file extension
        * *smask* (*int*) :data:`xref` number of a stencil (/SMask) image or zero
        * *width* (*int*) image width
        * *height* (*int*) image height
        * *colorspace* (*int*) the image's *colorspace.n* number.
        * *cs-name* (*str*) the image's *colorspace.name*.
        * *xres* (*int*) resolution in x direction. Please also see :data:`resolution`.
        * *yres* (*int*) resolution in y direction. Please also see :data:`resolution`.
        * *image* (*bytes*) image data, usable as image file content

      >>> d = doc.extractImage(1373)
      >>> d
      {'ext': 'png', 'smask': 2934, 'width': 5, 'height': 629, 'colorspace': 3, 'xres': 96,
      'yres': 96, 'cs-name': 'DeviceRGB',
      'image': b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x05\ ...'}
      >>> imgout = open("image." + d["ext"], "wb")
      >>> imgout.write(d["image"])
      102
      >>> imgout.close()

      .. note:: There is a functional overlap with *pix = fitz.Pixmap(doc, xref)*, followed by a *pix.getPNGData()*. Main differences are that extractImage, **(1)** does not only deliver PNG image formats, **(2)** is **very** much faster with non-PNG images, **(3)** usually results in much less disk storage for extracted images, **(4)** returns *None* in error cases (generates no exception). Look at the following example images within the same PDF.

         * xref 1268 is a PNG -- Comparable execution time and identical output::

            In [23]: %timeit pix = fitz.Pixmap(doc, 1268);pix.getPNGData()
            10.8 ms ± 52.4 µs per loop (mean ± std. dev. of 7 runs, 100 loops each)
            In [24]: len(pix.getPNGData())
            Out[24]: 21462

            In [25]: %timeit img = doc.extractImage(1268)
            10.8 ms ± 86 µs per loop (mean ± std. dev. of 7 runs, 100 loops each)
            In [26]: len(img["image"])
            Out[26]: 21462

         * xref 1186 is a JPEG -- :meth:`Document.extractImage` is **many times faster** and produces a **much smaller** output (2.48 MB vs. 0.35 MB)::

            In [27]: %timeit pix = fitz.Pixmap(doc, 1186);pix.getPNGData()
            341 ms ± 2.86 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)
            In [28]: len(pix.getPNGData())
            Out[28]: 2599433

            In [29]: %timeit img = doc.extractImage(1186)
            15.7 µs ± 116 ns per loop (mean ± std. dev. of 7 runs, 100000 loops each)
            In [30]: len(img["image"])
            Out[30]: 371177

   .. method:: Document.extractFont(xref, info_only=False)

      PDF Only: Return an embedded font file's data and appropriate file extension. This can be used to store the font as an external file. The method does not throw exceptions (other than via checking for PDF and valid :data:`xref`).

      :arg int xref: PDF object number of the font to extract.
      :arg bool info_only: only return font information, not the buffer. To be used for information-only purposes, avoids allocation of large buffer areas.

      :rtype: tuple
      :returns: a tuple *(basename, ext, subtype, buffer)*, where *ext* is a 3-byte suggested file extension (*str*), *basename* is the font's name (*str*), *subtype* is the font's type (e.g. "Type1") and *buffer* is a bytes object containing the font file's content (or *b""*). For possible extension values and their meaning see :ref:`FontExtensions`. Return details on error:

            * *("", "", "", b"")* -- invalid xref or xref is not a (valid) font object.
            * *(basename, "n/a", "Type1", b"")* -- *basename* is one of the :ref:`Base-14-Fonts`, which cannot be extracted.

      Example:

      >>> # store font as an external file
      >>> name, ext, buffer = doc.extractFont(4711)
      >>> # assuming buffer is not None:
      >>> ofile = open(name + "." + ext, "wb")
      >>> ofile.write(buffer)
      >>> ofile.close()

      .. warning:: The basename is returned unchanged from the PDF. So it may contain characters (such as blanks) which may disqualify it as a filename for your operating system. Take appropriate action.

      .. note: The returned *basename* in general is **not** the original file name, but it probably has some similarity.

   .. attribute:: Document.FontInfos

       Contains following information for any font inserted via :meth:`Page.insertFont` in **this** session of PyMuPDF:

       * xref *(int)* -- XREF number of the */Type/Font* object.
       * info *(dict)* -- detail font information with the following keys:

            * name *(str)* -- name of the basefont
            * idx *(int)* -- index number for multi-font files
            * type *(str)* -- font type (like "TrueType", "Type0", etc.)
            * ext *(str)* -- extension to be used, when font is extracted to a file (see :ref:`FontExtensions`).
            * glyphs (*list*) -- list of glyph numbers and widths (filled by textinsertion methods).

      :rtype: list

