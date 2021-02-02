.. _Pixmap:

================
Pixmap
================

Pixmaps ("pixel maps") are objects at the heart of MuPDF's rendering capabilities. They represent plane rectangular sets of pixels. Each pixel is described by a number of bytes ("components") defining its color, plus an optional alpha byte defining its transparency.

In PyMuPDF, there exist several ways to create a pixmap. Except the first one, all of them are available as overloaded constructors. A pixmap can be created ...

1. from a document page (method :meth:`Page.get_pixmap`)
2. empty, based on :ref:`Colorspace` and :ref:`IRect` information
3. from a file
4. from an in-memory image
5. from a memory area of plain pixels
6. from an image inside a PDF document
7. as a copy of another pixmap

.. note:: A number of image formats is supported as input for points 3. and 4. above. See section :ref:`ImageFiles`.

Have a look at the :ref:`FAQ` section to see some pixmap usage "at work".

============================= ===================================================
**Method / Attribute**        **Short Description**
============================= ===================================================
:meth:`Pixmap.clearWith`      clear parts of a pixmap
:meth:`Pixmap.copyPixmap`     copy parts of another pixmap
:meth:`Pixmap.gammaWith`      apply a gamma factor to the pixmap
:meth:`Pixmap.getImageData`   return a memory area in a variety of formats
:meth:`Pixmap.getPNGData`     return a PNG as a memory area
:meth:`Pixmap.invertIRect`    invert the pixels of a given area
:meth:`Pixmap.pillowWrite`    save as image using pillow (experimental)
:meth:`Pixmap.pillowData`     write image stream using pillow (experimental)
:meth:`Pixmap.pixel`          return the value of a pixel
:meth:`Pixmap.setAlpha`       set alpha values
:meth:`Pixmap.setPixel`       set the color of a pixel
:meth:`Pixmap.setRect`        set the color of a rectangle
:meth:`Pixmap.setResolution`  set the image resolution
:meth:`Pixmap.setOrigin`      set pixmap x,y values
:meth:`Pixmap.shrink`         reduce size keeping proportions
:meth:`Pixmap.tintWith`       tint a pixmap with a color
:meth:`Pixmap.writeImage`     save a pixmap in a variety of formats
:meth:`Pixmap.writePNG`       save a pixmap as a PNG file
:attr:`Pixmap.alpha`          transparency indicator
:attr:`Pixmap.colorspace`     pixmap's :ref:`Colorspace`
:attr:`Pixmap.height`         pixmap height
:attr:`Pixmap.interpolate`    interpolation method indicator
:attr:`Pixmap.irect`          :ref:`IRect` of the pixmap
:attr:`Pixmap.n`              bytes per pixel
:attr:`Pixmap.samples`        pixel area
:attr:`Pixmap.size`           pixmap's total length
:attr:`Pixmap.stride`         size of one image row
:attr:`Pixmap.width`          pixmap width
:attr:`Pixmap.x`              X-coordinate of top-left corner
:attr:`Pixmap.xres`           resolution in X-direction
:attr:`Pixmap.y`              Y-coordinate of top-left corner
:attr:`Pixmap.yres`           resolution in Y-direction
============================= ===================================================

**Class API**

.. class:: Pixmap

   .. method:: __init__(self, colorspace, irect, alpha)

      **New empty pixmap:** Create an empty pixmap of size and origin given by the rectangle. So, *irect.top_left* designates the top left corner of the pixmap, and its width and height are *irect.width* resp. *irect.height*. Note that the image area is **not initialized** and will contain crap data -- use eg. :meth:`clearWith` or :meth:`setRect` to be sure.

      :arg colorspace: colorspace.
      :type colorspace: :ref:`Colorspace`

      :arg irect_like irect: Tte pixmap's position and dimension.

      :arg bool alpha: Specifies whether transparency bytes should be included. Default is *False*.

   .. method:: __init__(self, colorspace, source)

      **Copy and set colorspace:** Copy *source* pixmap converting colorspace. Any colorspace combination is possible, but source colorspace must not be *None*.

      :arg colorspace: desired **target** colorspace. This **may also be** *None*. In this case, a "masking" pixmap is created: its :attr:`Pixmap.samples` will consist of the source's alpha bytes only.
      :type colorspace: :ref:`Colorspace`

      :arg source: the source pixmap.
      :type source: *Pixmap*

   .. method:: __init__(self, source, width, height, [clip])

      **Copy and scale:** Copy *source* pixmap, scaling new width and height values -- the image will appear stretched or shrunk accordingly. Supports partial copying. The source colorspace may be *None*.

      :arg source: the source pixmap.
      :type source: *Pixmap*

      :arg float width: desired target width.

      :arg float height: desired target height.

      :arg irect_like clip: restrict the resulting pixmap to this region of the **scaled** pixmap.

      .. note:: If width or height are not *de facto* integers (i.e. *float(int(value) != value*), then the resulting pixmap will have an alpha channel.

   .. method:: __init__(self, source, alpha=1)

      **Copy and add or drop alpha:** Copy *source* and add or drop its alpha channel. Identical copy if *alpha* equals *source.alpha*. If an alpha channel is added, its values will be set to 255.

      :arg source: source pixmap.
      :type source: *Pixmap*

      :arg bool alpha: whether the target will have an alpha channel, default and mandatory if source colorspace is *None*.

      .. note:: A typical use includes separation of color and transparency bytes in separate pixmaps. Some applications require this like e.g. *wx.Bitmap.FromBufferAndAlpha()* of *wxPython*:

         >>> # 'pix' is an RGBA pixmap
         >>> pixcolors = fitz.Pixmap(pix, 0)    # extract the RGB part (drop alpha)
         >>> pixalpha = fitz.Pixmap(None, pix)  # extract the alpha part
         >>> bm = wx.Bitmap.FromBufferAndAlpha(pix.widht, pix.height, pixcolors.samples, pixalpha.samples)


   .. method:: __init__(self, filename)

      **From a file:** Create a pixmap from *filename*. All properties are inferred from the input. The origin of the resulting pixmap is *(0, 0)*.

      :arg str filename: Path of the image file.

   .. method:: __init__(self, stream)

      **From memory:** Create a pixmap from a memory area. All properties are inferred from the input. The origin of the resulting pixmap is *(0, 0)*.

      :arg bytes,bytearray,BytesIO stream: Data containing a complete, valid image. Could have been created by e.g. *stream = bytearray(open('image.file', 'rb').read())*. Type *bytes* is supported in **Python 3 only**, because *bytes == str* in Python 2 and the method will interpret the stream as a filename.

         *Changed in version 1.14.13:* *io.BytesIO* is now also supported.


   .. method:: __init__(self, colorspace, width, height, samples, alpha)

      **From plain pixels:** Create a pixmap from *samples*. Each pixel must be represented by a number of bytes as controlled by the *colorspace* and *alpha* parameters. The origin of the resulting pixmap is *(0, 0)*. This method is useful when raw image data are provided by some other program -- see :ref:`FAQ`.

      :arg colorspace: Colorspace of image.
      :type colorspace: :ref:`Colorspace`

      :arg int width: image width

      :arg int height: image height

      :arg bytes,bytearray,BytesIO samples:  an area containing all pixels of the image. Must include alpha values if specified.

         *Changed in version 1.14.13:* (1) *io.BytesIO* can now also be used. (2) Data are now **copied** to the pixmap, so may safely be deleted or become unavailable.

      :arg bool alpha: whether a transparency channel is included.

      .. note::

         1. The following equation **must be true**: *(colorspace.n + alpha) * width * height == len(samples)*.
         2. Starting with version 1.14.13, the samples data are **copied** to the pixmap.


   .. method:: __init__(self, doc, xref)

      **From a PDF image:** Create a pixmap from an image **contained in PDF** *doc* identified by its :data:`xref`. All pimap properties are set by the image. Have a look at `extract-img1.py <https://github.com/pymupdf/PyMuPDF/tree/master/demo/extract-img1.py>`_ and `extract-img2.py <https://github.com/pymupdf/PyMuPDF/tree/master/demo/extract-img2.py>`_ to see how this can be used to recover all of a PDF's images.

      :arg doc: an opened **PDF** document.
      :type doc: :ref:`Document`

      :arg int xref: the :data:`xref` of an image object. For example, you can make a list of images used on a particular page with :meth:`Document.get_page_images`, which also shows the :data:`xref` numbers of each image.

   .. method:: clearWith([value [, irect]])

      Initialize the samples area.

      :arg int value: if specified, values from 0 to 255 are valid. Each color byte of each pixel will be set to this value, while alpha will be set to 255 (non-transparent) if present. If omitted, then all bytes (including any alpha) are cleared to *0x00*.

      :arg irect_like irect: the area to be cleared. Omit to clear the whole pixmap. Can only be specified, if *value* is also specified.

   .. method:: tintWith(red, green, blue)

      Colorize (tint) a pixmap with a color provided as an integer triple (red, green, blue). Only colorspaces :data:`CS_GRAY` and :data:`CS_RGB` are supported, others are ignored with a warning.

      If the colorspace is :data:`CS_GRAY`, *(red + green + blue)/3* will be taken as the tint value.

      :arg int red: *red* component.

      :arg int green: *green* component.

      :arg int blue: *blue* component.

   .. method:: gammaWith(gamma)

      Apply a gamma factor to a pixmap, i.e. lighten or darken it. Pixmaps with colorspace *None* are ignored with a warning.

      :arg float gamma: *gamma = 1.0* does nothing, *gamma < 1.0* lightens, *gamma > 1.0* darkens the image.

   .. method:: shrink(n)

      Shrink the pixmap by dividing both, its width and height by 2\ :sup:`n`.

      :arg int n: determines the new pixmap (samples) size. For example, a value of 2 divides width and height by 4 and thus results in a size of one 16\ :sup:`th` of the original. Values less than 1 are ignored with a warning.

      .. note:: Use this methods to reduce a pixmap's size retaining its proportion. The pixmap is changed "in place". If you want to keep original and also have more granular choices, use the resp. copy constructor above.

   .. method:: pixel(x, y)

      *New in version:: 1.14.5:* Return the value of the pixel at location (x, y) (column, line).

      :arg int x: the column number of the pixel. Must be in *range(pix.width)*.
      :arg int y: the line number of the pixel, Must be in *range(pix.height)*.

      :rtype: list
      :returns: a list of color values and, potentially the alpha value. Its length and content depend on the pixmap's colorspace and the presence of an alpha. For RGBA pixmaps the result would e.g. be *[r, g, b, a]*. All items are integers in *range(256)*.

   .. method:: setPixel(x, y, color)

      *New in version 1.14.7:* Set the color of the pixel at location (x, y) (column, line).

      :arg int x: the column number of the pixel. Must be in *range(pix.width)*.
      :arg int y: the line number of the pixel. Must be in *range(pix.height)*.
      :arg sequence color: the desired color given as a sequence of integers in *range(256)*. The length of the sequence must equal :attr:`Pixmap.n`, which includes any alpha byte.

   .. method:: setRect(irect, color)

      *New in version 1.14.8:* Set the pixels of a rectangle to a color.

      :arg irect_like irect: the rectangle to be filled with the color. The actual area is the intersection of this parameter and :attr:`Pixmap.irect`. For an empty intersection (or an invalid parameter), no change will happen.
      :arg sequence color: the desired color given as a sequence of integers in *range(256)*. The length of the sequence must equal :attr:`Pixmap.n`, which includes any alpha byte.

      :rtype: bool
      :returns: *False* if the rectangle was invalid or had an empty intersection with :attr:`Pixmap.irect`, else *True*.

      .. note::

         1. This method is equivalent to :meth:`Pixmap.setPixel` executed for each pixel in the rectangle, but is obviously **very much faster** if many pixels are involved.
         2. This method can be used similar to :meth:`Pixmap.clearWith` to initialize a pixmap with a certain color like this: *pix.setRect(pix.irect, (255, 255, 0))* (RGB example, colors the complete pixmap with yellow).

   .. method:: setOrigin(x, y)

      *(New in v1.17.7)* Set the x and y values.

      :arg int x: x coordinate
      :arg int y: y coordinate


   .. method:: setResolution(xres, yres)

      *(New in v1.16.17)* Set the resolution (dpi) in x and y direction.

      *(Changed in v1.18.0)* When saving as a PNG image, these values will be stored now.

      :arg int xres: resolution in x direction.
      :arg int yres: resolution in y direction.


   .. method:: setAlpha([alphavalues])

      Change the alpha values. The pixmap must have an alpha channel.

      :arg bytes,bytearray,BytesIO alphavalues: the new alpha values. If provided, its length must be at least *width * height*. If omitted, all alpha values are set to 255 (no transparency).

         *Changed in version 1.14.13:* *io.BytesIO* is now also supported.


   .. method:: invertIRect([irect])

      Invert the color of all pixels in :ref:`IRect` *irect*. Will have no effect if colorspace is *None*.

      :arg irect_like irect: The area to be inverted. Omit to invert everything.

   .. method:: copyPixmap(source, irect)

      Copy the *irect* part of the *source* pixmap into the corresponding area of this one. The two pixmaps may have different dimensions and can each have :data:`CS_GRAY` or :data:`CS_RGB` colorspaces, but they currently **must** have the same alpha property [#f2]_. The copy mechanism automatically adjusts discrepancies between source and target like so:

      If copying from :data:`CS_GRAY` to :data:`CS_RGB`, the source gray-shade value will be put into each of the three rgb component bytes. If the other way round, *(r + g + b) / 3* will be taken as the gray-shade value of the target.

      Between *irect* and the target pixmap's rectangle, an "intersection" is calculated at first. This takes into account the rectangle coordinates and the current attribute values *source.x* and *source.y* (which you are free to modify for this purpose). Then the corresponding data of this intersection are copied. If the intersection is empty, nothing will happen.

      :arg source: source pixmap.
      :type source: :ref:`Pixmap`

      :arg irect_like irect: The area to be copied.

   .. method:: writeImage(filename, output=None)

      Save pixmap as an image file. Depending on the output chosen, only some or all colorspaces are supported and different file extensions can be chosen. Please see the table below. Since MuPDF v1.10a the *savealpha* option is no longer supported and will be silently ignored.

      :arg str filename: The filename to save to. The filename's extension determines the image format, if not overriden by the output parameter.

      :arg str output: The requested image format. The default is the filename's extension. If not recognized, *png* is assumed. For other possible values see :ref:`PixmapOutput`.

   .. method:: writePNG(filename)

      Equal to *pix.writeImage(filename, "png")*.

   .. method:: getImageData(output="png")

      *New in version 1.14.5:* Return the pixmap as a *bytes* memory object of the specified format -- similar to :meth:`writeImage`.

      :arg str output: The requested image format. The default is "png" for which this function equals :meth:`getPNGData`. For other possible values see :ref:`PixmapOutput`.

      :rtype: bytes

   .. method:: getPNGdata()

   .. method:: getPNGData()

      Equal to *pix.getImageData("png")*.

      :rtype: bytes

   ..  method:: pillowWrite(*args, **kwargs)

      *(New in v1.17.3)*

      Write the pixmap as an image file using Pillow. Use this method for image formats or extended image features not supported by MuPDF. Examples are

      * Formats JPEG, JPX, J2K, WebP, etc.
      * Storing EXIF information.
      * If you do not provide dpi information, the values *xres*, *yres* stored with the pixmap are automatically used.

      A simple example: ``pix.pillowWrite("some.jpg", optimize=True, dpi=(150, 150))``. For details on other parameters see the Pillow documentation.

      .. note:: *(Changed in v1.18.0)* :meth:`Pixmap.writeImage` and :meth:`Pixmap.writePNG` now also set resolution / dpi from *xres* / *yres* automatically, when saving a PNG image.

   ..  method:: pillowData(*args, **kwargs)

      *(New in v1.17.3)*

      Return an image as a bytes object in the specified format using Pillow. For example ``stream = pix.pillowData(format="JPEG", optimize=True)``. Also see above. For details on other parameters see the Pillow documentation.


   .. attribute:: alpha

      Indicates whether the pixmap contains transparency information.

      :type: bool

   .. attribute:: colorspace

      The colorspace of the pixmap. This value may be *None* if the image is to be treated as a so-called *image mask* or *stencil mask* (currently happens for extracted PDF document images only).

      :type: :ref:`Colorspace`

   .. attribute:: stride

      Contains the length of one row of image data in :attr:`Pixmap.samples`. This is primarily used for calculation purposes. The following expressions are true:

      * *len(samples) == height * stride*
      * *width * n == stride*.

      :type: int

   .. attribute:: irect

      Contains the :ref:`IRect` of the pixmap.

      :type: :ref:`IRect`

   .. attribute:: samples

      The color and (if :attr:`Pixmap.alpha` is true) transparency values for all pixels. It is an area of *width * height * n* bytes. Each n bytes define one pixel. Each successive n bytes yield another pixel in scanline order. Subsequent scanlines follow each other with no padding. E.g. for an RGBA colorspace this means, *samples* is a sequence of bytes like *..., R, G, B, A, ...*, and the four byte values R, G, B, A define one pixel.

      This area can be passed to other graphics libraries like PIL (Python Imaging Library) to do additional processing like saving the pixmap in other image formats.

      .. note::
         * The underlying data is a typically **large** memory area from which a *bytes* copy is made for this attribute: for example an RGB-rendered letter page has a samples size of almost 1.4 MB. So consider assigning a new variable if you repeatedly use it.
         * Any changes to the underlying data are available only after again accessing this attribute.

      :type: bytes

   .. attribute:: size

      Contains *len(pixmap)*. This will generally equal *len(pix.samples)* plus some platform-specific value for defining other attributes of the object.

      :type: int

   .. attribute:: width

   .. attribute:: w

      Width of the region in pixels.

      :type: int

   .. attribute:: height

   .. attribute:: h

      Height of the region in pixels.

      :type: int

   .. attribute:: x

      X-coordinate of top-left corner

      :type: int

   .. attribute:: y

      Y-coordinate of top-left corner

      :type: int

   .. attribute:: n

      Number of components per pixel. This number depends on colorspace and alpha. If colorspace is not *None* (stencil masks), then *Pixmap.n - Pixmap.aslpha == pixmap.colorspace.n* is true. If colorspace is *None*, then *n == alpha == 1*.

      :type: int

   .. attribute:: xres

      Horizontal resolution in dpi (dots per inch). Please also see :data:`resolution`.

      :type: int

   .. attribute:: yres

      Vertical resolution in dpi. Please also see :data:`resolution`.

      :type: int

   .. attribute:: interpolate

      An information-only boolean flag set to *True* if the image will be drawn using "linear interpolation". If *False* "nearest neighbour sampling" will be used.

      :type: bool

.. _ImageFiles:

Supported Input Image Formats
-----------------------------------------------
The following file types are supported as **input** to construct pixmaps: **BMP, JPEG, GIF, TIFF, JXR, JPX**, **PNG**, **PAM** and all of the **Portable Anymap** family (**PBM, PGM, PNM, PPM**). This support is two-fold:

1. Directly create a pixmap with *Pixmap(filename)* or *Pixmap(byterray)*. The pixmap will then have properties as determined by the image.

2. Open such files with *fitz.open(...)*. The result will then appear as a document containing one single page. Creating a pixmap of this page offers all the options available in this context: apply a matrix, choose colorspace and alpha, confine the pixmap to a clip area, etc.

**SVG images** are only supported via method 2 above, not directly as pixmaps. But remember: the result of this is a **raster image** as is always the case with pixmaps [#f1]_.

.. _PixmapOutput:

Supported Output Image Formats
---------------------------------------------------------------------------
A number of image **output** formats are supported. You have the option to either write an image directly to a file (:meth:`Pixmap.writeImage`), or to generate a bytes object (:meth:`Pixmap.getImageData`). Both methods accept a 3-letter string identifying the desired format (**Format** column below). Please note that not all combinations of pixmap colorspace, transparency support (alpha) and image format are possible.

========== =============== ========= ============== ===========================
**Format** **Colorspaces** **alpha** **Extensions** **Description**
========== =============== ========= ============== ===========================
pam        gray, rgb, cmyk yes       .pam           Portable Arbitrary Map
pbm        gray, rgb       no        .pbm           Portable Bitmap
pgm        gray, rgb       no        .pgm           Portable Graymap
png        gray, rgb       yes       .png           Portable Network Graphics
pnm        gray, rgb       no        .pnm           Portable Anymap
ppm        gray, rgb       no        .ppm           Portable Pixmap
ps         gray, rgb, cmyk no        .ps            Adobe PostScript Image
psd        gray, rgb, cmyk yes       .psd           Adobe Photoshop Document
========== =============== ========= ============== ===========================

.. note::
    * Not all image file types are supported (or at least common) on all OS platforms. E.g. PAM and the Portable Anymap formats are rare or even unknown on Windows.
    * Especially pertaining to CMYK colorspaces, you can always convert a CMYK pixmap to an RGB pixmap with *rgb_pix = fitz.Pixmap(fitz.csRGB, cmyk_pix)* and then save that in the desired format.
    * As can be seen, MuPDF's image support range is different for input and output. Among those supported both ways, PNG is probably the most popular. We recommend using Pillow whenever you face a support gap.
    * We also recommend using "ppm" formats as input to tkinter's *PhotoImage* method like this: *tkimg = tkinter.PhotoImage(data=pix.getImageData("ppm"))* (also see the tutorial). This is **very** fast (**60 times** faster than PNG) and will work under Python 2 or 3.



.. rubric:: Footnotes

.. [#f1] If you need a **vector image** from the SVG, you must first convert it to a PDF. Try :meth:`Document.convert_to_pdf`. If this is not good enough, look for other SVG-to-PDF conversion tools like the Python packages `svglib <https://pypi.org/project/svglib>`_, `CairoSVG <https://pypi.org/project/cairosvg>`_, `Uniconvertor <https://sk1project.net/modules.php?name=Products&product=uniconvertor&op=download>`_ or the Java solution `Apache Batik <https://github.com/apache/batik>`_. Have a look at our Wiki for more examples.

.. [#f2] To also set the alpha property, add an additional step to this method by dropping or adding an alpha channel to the result.
