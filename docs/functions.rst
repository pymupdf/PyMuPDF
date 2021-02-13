============
Functions
============
The following are miscellaneous functions and attributes on a fairly low-level technical detail.

Some functions provide detail access to PDF structures. Others are stripped-down, high performance versions of other functions which provide more information.

Yet others are handy, general-purpose utilities.


==================================== ==============================================================
**Function**                         **Short Description**
==================================== ==============================================================
:meth:`Annot.clean_contents`         PDF only: clean the annot's :data:`contents` object
:meth:`Annot.set_apn_matrix`         PDF only: set the matrix of the appearance object
:meth:`Annot.set_apn_bbox`           PDF only: set the bbox of the appearance object
:attr:`Annot.apn_matrix`             PDF only: the matrix of the appearance object
:attr:`Annot.apn_bbox`               PDF only: bbox of the appearance object
:meth:`ConversionHeader`             return header string for *get_text* methods
:meth:`ConversionTrailer`            return trailer string for *get_text* methods
:meth:`Document.del_xml_metadata`    PDF only: remove XML metadata
:meth:`Document.delete_object`       PDF only: delete an object
:meth:`Document.get_new_xref`        PDF only: create and return a new :data:`xref` entry
:meth:`Document._getOLRootNumber`    PDF only: return / create :data:`xref` of */Outline*
:meth:`Document.xml_metadata_xref`   PDF only: return XML metadata :data:`xref` number
:meth:`Document.xref_length`         PDF only: return length of :data:`xref` table
:meth:`Document.extract_font`        PDF only: extract embedded font
:meth:`Document.extract_image`       PDF only: extract embedded image
:meth:`Document.get_char_widths`     PDF only: return a list of glyph widths of a font
:meth:`Document.is_stream`           PDF only: check whether an :data:`xref` is a stream object
:attr:`Document.FontInfos`           PDF only: information on inserted fonts
:meth:`ImageProperties`              return a dictionary of basic image properties
:meth:`getPDFnow`                    return the current timestamp in PDF format
:meth:`getPDFstr`                    return PDF-compatible string
:meth:`getTextlength`                return string length for a given font & fontsize
:meth:`Page.clean_contents`          PDF only: clean the page's :data:`contents` objects
:meth:`Page.get_contents`            PDF only: return a list of content :data:`xref` numbers
:meth:`Page.set_contents`            PDF only: set page's :data:`contents` to some :data:`xref`
:meth:`Page.get_displaylist`         create the page's display list
:meth:`Page.get_text_blocks`         extract text blocks as a Python list
:meth:`Page.get_text_words`          extract text words as a Python list
:meth:`Page.run`                     run a page through a device
:meth:`Page.read_contents`           PDF only: get complete, concatenated /Contents source
:meth:`Page.wrap_contents`           wrap contents with stacking commands
:attr:`Page.is_wrapped`              check whether contents wrapping is present
:meth:`planishLine`                  matrix to map a line to the x-axis
:meth:`PaperSize`                    return width, height for a known paper format
:meth:`PaperRect`                    return rectangle for a known paper format
:meth:`sRGB_to_pdf`                  return PDF RGB color tuple from a sRGB integer
:meth:`sRGB_to_rgb`                  return (R, G, B) color tuple from a sRGB integer
:meth:`glyph_name_to_unicode`        return unicode from a glyph name
:meth:`unicode_to_glyph_name`        return glyph name from a unicode
:meth:`make_table`                   split rectangle in sub-rectangles
:meth:`adobe_glyph_names`            list of glyph names defined in **Adobe Glyph List**
:meth:`adobe_glyph_unicodes`         list of unicodes defined in **Adobe Glyph List**
:attr:`paperSizes`                   dictionary of pre-defined paper formats
:attr:`fitz_fontdescriptors`         dictionary of available supplement fonts
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

      Convenience function returning a PDF color triple (red, green, blue) for a given sRGB color integer as it occurs in :meth:`Page.get_text` dictionaries "dict" and "rawdict".

      :arg int srgb: an integer of format RRGGBB, where each color component is an integer in range(255).

      :returns: a tuple (red, green, blue) with float items in intervall *0 <= item <= 1* representing the same color.

-----

   .. method:: glyph_name_to_unicode(name)

      *New in v1.18.0*

      Return the unicode number of a glyph name based on the **Adobe Glyph List**.

      :arg str name: the name of some glyph. The function is based on the `Adobe Glyph List <https://github.com/adobe-type-tools/agl-aglfn/blob/master/glyphlist.txt>`_.

      :rtype: int
      :returns: the unicode. Invalid *name* entries return ``0xfffd (65533)``.

      .. note:: A similar functionality is provided by package `fontTools <https://pypi.org/project/fonttools/>`_ in its *agl* sub-package.

-----

   .. method:: unicode_to_glyph_name(ch)

      *New in v1.18.0*

      Return the glyph name of a unicode number, based on the **Adobe Glyph List**.

      :arg int che: the unicode given by e.g. ``ord("ß")``. The function is based on the `Adobe Glyph List <https://github.com/adobe-type-tools/agl-aglfn/blob/master/glyphlist.txt>`_.

      :rtype: str
      :returns: the glyph name. E.g. ``fitz.unicode_to_glyph_name(ord("Ä"))`` returns ``'Adieresis'``.

      .. note:: A similar functionality is provided by package `fontTools <https://pypi.org/project/fonttools/>`_: in its *agl* sub-package.

-----

   .. method:: adobe_glyph_names()

      *New in v1.18.0*

      Return a list of glyph names defined in the **Adobe Glyph List**.

      :rtype: list
      :returns: list of strings.

      .. note:: A similar functionality is provided by package `fontTools <https://pypi.org/project/fonttools/>`_ in its *agl* sub-package.

-----

   .. method:: adobe_glyph_unicodes()

      *New in v1.18.0*

      Return a list of unicodes for there exists a glyph name in the **Adobe Glyph List**.

      :rtype: list
      :returns: list of integers.

      .. note:: A similar functionality is provided by package `fontTools <https://pypi.org/project/fonttools/>`_ in its *agl* sub-package.

-----

   .. method:: sRGB_to_rgb(srgb)

      *New in v1.17.4*

      Convenience function returning a color (red, green, blue) for a given *sRGB* color integer .

      :arg int srgb: an integer of format RRGGBB, where each color component is an integer in range(255).

      :returns: a tuple (red, green, blue) with integer items in intervall *0 <= item <= 255* representing the same color.

-----

   .. method:: make_table(rect, cols=1, rows=1)

      *New in v1.17.4*

      Convenience function to split a rectangle into sub-rectangles. Returns a list of *rows* lists, each containing *cols* :ref:`Rect` items. Each sub-rectangle can then be addressed by its row and column index.

      :arg rect_like rect: the rectangle to split.
      :arg int cols: the desired number of columns.
      :arg int rows: the desired number of rows.
      :returns: a list of :ref:`Rect` objects of equal size, whose union equals *rect*. Here is the layout of a 3x4 table created by ``cell = fitz.make_table(rect, cols=4, rows=3)``:

      .. image:: images/img-make-table.*
         :scale: 60


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

   .. attribute:: fitz_fontdescriptors

      *(New in v1.17.5)*

      A dictionary of usable fonts from repository `pymupdf-fonts <https://pypi.org/project/pymupdf-fonts/>`_. Items are keyed by their reserved fontname and provide information like this::

         In [2]: fitz.fitz_fontdescriptors.keys()
         Out[2]: dict_keys(['figbo', 'figo', 'figbi', 'figit', 'fimbo', 'fimo',
         'spacembo', 'spacembi', 'spacemit', 'spacemo', 'math', 'music', 'symbol1',
         'symbol2'])
         In [3]: fitz.fitz_fontdescriptors["fimo"]
         Out[3]:
         {'name': 'Fira Mono Regular',
         'size': 125712,
         'mono': True,
         'bold': False,
         'italic': False,
         'serif': True,
         'glyphs': 1485}
         

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
      :arg str fontname: the fontname. Must be one of either the :ref:`Base-14-Fonts` or the CJK fonts, identified by their "reserved" fontnames (see table in :meth.`Page.insert_font`).
      :arg float fontsize: size of the font.
      :arg int encoding: the encoding to use. Besides 0 = Latin, 1 = Greek and 2 = Cyrillic (Russian) are available. Relevant for Base-14 fonts "Helvetica", "Courier" and "Times" and their variants only. Make sure to use the same value as in the corresponding text insertion.
      :rtype: float
      :returns: the length in points the string will have (e.g. when used in :meth:`Page.insert_text`).

      .. note:: This function will only do the calculation -- it won't insert font or text.

      .. warning:: If you use this function to determine the required rectangle width for the (:ref:`Page` or :ref:`Shape`) *insert_textbox* methods, be aware that they calculate on a **by-character level**. Because of rounding effects, this will mostly lead to a slightly larger number: *sum([fitz.getTextlength(c) for c in text]) > fitz.getTextlength(text)*. So either (1) do the same, or (2) use something like *fitz.getTextlength(text + "'")* for your calculation.

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

      :arg str output: type of document. Use the same as the output parameter of *get_text()*.

      :arg str filename: optional arbitrary name to use in output types "json" and "xml".

      :rtype: str

-----

   .. method:: ConversionTrailer(output)

      Return the trailer string required to make a valid document out of page text outputs. See :meth:`Page.get_text` for an example.

      :arg str output: type of document. Use the same as the output parameter of *get_text()*.

      :rtype: str

-----

   .. method:: Document.delete_object(xref)

      PDF only: Delete an object given by its cross reference number.

      :arg int xref: the cross reference number. Must be within the document's valid :data:`xref` range.

      .. warning:: Only use with extreme care: this may make the PDF unreadable.

-----

   .. method:: Document.del_xml_metadata()

      Delete an object containing XML-based metadata from the PDF. (Py-) MuPDF does not support XML-based metadata. Use this if you want to make sure that the conventional metadata dictionary will be used exclusively. Many thirdparty PDF programs insert their own metadata in XML format and thus may override what you store in the conventional dictionary. This method deletes any such reference, and the corresponding PDF object will be deleted during next garbage collection of the file.

-----

   .. method:: Document.xml_metadata_xref()

      Return the XML-based metadata :data:`xref` of the PDF if present -- also refer to :meth:`Document._delXmlMetadata`. You can use it to retrieve the content via :meth:`Document.xref_stream` and then work with it using some XML software.

      :rtype: int
      :returns: :data:`xref` of PDF file level XML metadata -- or 0 if none exists.

-----

   .. method:: Page.run(dev, transform)

      Run a page through a device.

      :arg dev: Device, obtained from one of the :ref:`Device` constructors.
      :type dev: :ref:`Device`

      :arg transform: Transformation to apply to the page. Set it to :ref:`Identity` if no transformation is desired.
      :type transform: :ref:`Matrix`

-----

   .. method:: Page.wrap_contents

      Put string pair "q" / "Q" before, resp. after a page's */Contents* object(s) to ensure that any "geometry" changes are **local** only.

      Use this method as an alternative, minimalistic version of :meth:`Page.clean_contents`. Its advantage is a small footprint in terms of processing time and impact on the data size of incremental saves.

-----

   .. attribute:: Page.is_wrapped

      Indicate whether :meth:`Page.wrap_contents` may be required for object insertions in standard PDF geometry. Please note that this is a quick, basic check only: a value of *False* may still be a false alarm.

-----

   .. method:: Page.get_text_blocks(flags=None)

      Deprecated wrapper for :meth:`TextPage.extractBLOCKS`.  Use :meth:`Page.getText` with the "blocks" option instead.

-----

   .. method:: Page.get_text_words(flags=None)

      Deprecated wrapper for :meth:`TextPage.extractWORDS`. Use :meth:`Page.getText` with the "words" option instead.

-----

   .. method:: Page.get_displaylist()

      Run a page through a list device and return its display list.

      :rtype: :ref:`DisplayList`
      :returns: the display list of the page.

-----

   .. method:: Page.get_contents()

      PDF only: Retrieve a list of :data:`xref` of :data:`contents` objects of a page. May be empty or contain multiple integers. If the page is cleaned (:meth:`Page.clean_contents`), it will be one entry at most. The "source" of each `/Contents` object can be individually read by :meth:`Document.xref_stream` using an item of this list. Method :meth:`Page.read_contents` in contrast walks through this list and concatenates the corresponding sources into one ``bytes`` object.

-----

   .. method:: Page.clean_contents(sanitize=True)

      *(Changed in v1.17.6)*
      
      PDF only: Clean and concatenate all :data:`contents` objects associated with this page. "Cleaning" includes syntactical corrections, standardizations and "pretty printing" of the contents stream. Discrepancies between :data:`contents` and :data:`resources` objects will also be corrected if sanitize is true. See :meth:`Page.get_contents` for more details.

      Changed in version 1.16.0 Annotations are no longer implicitely cleaned by this method. Use :meth:`Annot._cleanContents` separately.

      :arg bool sanitize: *(new in v1.17.6)* if true, synchronization between resources and their actual use in the contents object is snychronized. For example, if a font is not actually used for any text of the page, then it will be deleted from the ``/Resources/Font`` object.

      .. warning:: This is a complex function which may generate large amounts of new data and render old data unused. It is **not recommended** using it together with the **incremental save** option. Also note that the resulting singleton new */Contents* object is **uncompressed**. So you should save to a **new file** using options *"deflate=True, garbage=3"*.

-----

   .. method:: Page.read_contents()

      *New in version 1.17.0.*
      Return the concatenation of all :data:`contents` objects associated with the page -- without cleaning or otherwise modifying them. Use this method whenever you need to parse this source in its entirety whithout having to bother how many separate contents objects exist.


-----

   .. method:: Annot.clean_contents(sanitize=True)

      Clean the :data:`contents` streams associated with the annotation. This is the same type of action which :meth:`Page.clean_contents` performs -- just restricted to this annotation.


-----

   .. method:: Document.get_char_widths(xref=0, limit=256)

      Return a list of character glyphs and their widths for a font that is present in the document. A font must be specified by its PDF cross reference number :data:`xref`. This function is called automatically from :meth:`Page.insert_text` and :meth:`Page.insert_textbox`. So you should rarely need to do this yourself.

      :arg int xref: cross reference number of a font embedded in the PDF. To find a font :data:`xref`, use e.g. *doc.get_page_fonts(pno)* of page number *pno* and take the first entry of one of the returned list entries.

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

   .. method:: Document.is_stream(xref)

      *(New in version 1.14.14)*
      
      PDF only: Check whether the object represented by :data:`xref` is a :data:`stream` type. Return is *False* if not a PDF or if the number is outside the valid xref range.

      :arg int xref: :data:`xref` number.

      :returns: *True* if the object definition is followed by data wrapped in keyword pair *stream*, *endstream*.

-----

   .. method:: Document.get_new_xref()

      Increase the :data:`xref` by one entry and return that number. This can then be used to insert a new object.

      :rtype: int
      :returns: the number of the new :data:`xref` entry.

-----

   .. method:: Document.xref_length()

      Return length of :data:`xref` table.

      :rtype: int
      :returns: the number of entries in the :data:`xref` table.

-----

   .. method:: Document.extract_image(xref)

      PDF Only: Extract data and meta information of an image stored in the document. The output can directly be used to be stored as an image file, as input for PIL, :ref:`Pixmap` creation, etc. This method avoids using pixmaps wherever possible to present the image in its original format (e.g. as JPEG).

      :arg int xref: :data:`xref` of an image object. If this is not in *range(1, doc.xref_length())*, or the object is no image or other errors occur, *None* is returned and no exception is raised.

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

      >>> d = doc.extract_image(1373)
      >>> d
      {'ext': 'png', 'smask': 2934, 'width': 5, 'height': 629, 'colorspace': 3, 'xres': 96,
      'yres': 96, 'cs-name': 'DeviceRGB',
      'image': b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x05\ ...'}
      >>> imgout = open("image." + d["ext"], "wb")
      >>> imgout.write(d["image"])
      102
      >>> imgout.close()

      .. note:: There is a functional overlap with *pix = fitz.Pixmap(doc, xref)*, followed by a *pix.getPNGData()*. Main differences are that extract_image, **(1)** does not always deliver PNG image formats, **(2)** is **very** much faster with non-PNG images, **(3)** usually results in much less disk storage for extracted images, **(4)** returns *None* in error cases (generates no exception). Look at the following example images within the same PDF.

         * xref 1268 is a PNG -- Comparable execution time and identical output::

            In [23]: %timeit pix = fitz.Pixmap(doc, 1268);pix.getPNGData()
            10.8 ms ± 52.4 µs per loop (mean ± std. dev. of 7 runs, 100 loops each)
            In [24]: len(pix.getPNGData())
            Out[24]: 21462

            In [25]: %timeit img = doc.extract_image(1268)
            10.8 ms ± 86 µs per loop (mean ± std. dev. of 7 runs, 100 loops each)
            In [26]: len(img["image"])
            Out[26]: 21462

         * xref 1186 is a JPEG -- :meth:`Document.extract_image` is **many times faster** and produces a **much smaller** output (2.48 MB vs. 0.35 MB)::

            In [27]: %timeit pix = fitz.Pixmap(doc, 1186);pix.getPNGData()
            341 ms ± 2.86 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)
            In [28]: len(pix.getPNGData())
            Out[28]: 2599433

            In [29]: %timeit img = doc.extract_image(1186)
            15.7 µs ± 116 ns per loop (mean ± std. dev. of 7 runs, 100000 loops each)
            In [30]: len(img["image"])
            Out[30]: 371177

   .. method:: Document.extract_font(xref, info_only=False)

      PDF Only: Return an embedded font file's data and appropriate file extension. This can be used to store the font as an external file. The method does not throw exceptions (other than via checking for PDF and valid :data:`xref`).

      :arg int xref: PDF object number of the font to extract.
      :arg bool info_only: only return font information, not the buffer. To be used for information-only purposes, avoids allocation of large buffer areas.

      :rtype: tuple
      :returns: a tuple *(basename, ext, subtype, buffer)*, where *ext* is a 3-byte suggested file extension (*str*), *basename* is the font's name (*str*), *subtype* is the font's type (e.g. "Type1") and *buffer* is a bytes object containing the font file's content (or *b""*). For possible extension values and their meaning see :ref:`FontExtensions`. Return details on error:

            * *("", "", "", b"")* -- invalid xref or xref is not a (valid) font object.
            * *(basename, "n/a", "Type1", b"")* -- *basename* is one of the :ref:`Base-14-Fonts`, which cannot be extracted.

      Example:

      >>> # store font as an external file
      >>> name, ext, buffer = doc.extract_font(4711)
      >>> # assuming buffer is not None:
      >>> ofile = open(name + "." + ext, "wb")
      >>> ofile.write(buffer)
      >>> ofile.close()

      .. warning:: The basename is returned unchanged from the PDF. So it may contain characters (such as blanks) which may disqualify it as a filename for your operating system. Take appropriate action.

      .. note: The returned *basename* in general is **not** the original file name, but it probably has some similarity.

   .. attribute:: Document.FontInfos

       Contains following information for any font inserted via :meth:`Page.insert_font` in **this** session of PyMuPDF:

       * xref *(int)* -- XREF number of the */Type/Font* object.
       * info *(dict)* -- detail font information with the following keys:

            * name *(str)* -- name of the basefont
            * idx *(int)* -- index number for multi-font files
            * type *(str)* -- font type (like "TrueType", "Type0", etc.)
            * ext *(str)* -- extension to be used, when font is extracted to a file (see :ref:`FontExtensions`).
            * glyphs (*list*) -- list of glyph numbers and widths (filled by textinsertion methods).

      :rtype: list

