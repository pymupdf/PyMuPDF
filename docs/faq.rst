.. _FAQ:

==============================
Collection of Recipes
==============================

.. highlight:: python

A collection of recipes in "How-To" format for using PyMuPDF. We aim to extend this section over time. Where appropriate we will refer to the corresponding `Wiki <https://github.com/pymupdf/PyMuPDF/wiki>`_ pages, but some duplication may still occur.

----------

Images
-------

----------

How to Make Images from Document Pages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This little script will take a document filename and generate a PNG file from each of its pages.

The document can be any supported type like PDF, XPS, etc.

The script works as a command line tool which expects the filename being supplied as a parameter. The generated image files (1 per page) are stored in the directory of the script::

    import sys, fitz  # import the binding
    fname = sys.argv[1]  # get filename from command line
    doc = fitz.open(fname)  # open document
    for page in doc:  # iterate through the pages
        pix = page.get_pixmap(alpha = False)  # render page to an image
        pix.writePNG("page-%i.png" % page.number)  # store image as a PNG

The script directory will now contain PNG image files named *page-0.png*, *page-1.png*, etc. Pictures have the dimension of their pages, e.g. 595 x 842 pixels for an A4 portrait sized page. They will have a resolution of 72 dpi in x and y dimension and have no transparency. You can change all that -- for how to do this, read the next sections.

----------

How to Increase :index:`Image Resolution <pair: image; resolution>`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The image of a document page is represented by a :ref:`Pixmap`, and the simplest way to create a pixmap is via method :meth:`Page.get_pixmap`.

This method has many options for influencing the result. The most important among them is the :ref:`Matrix`, which lets you :index:`zoom`, rotate, distort or mirror the outcome.

:meth:`Page.get_pixmap` by default will use the :ref:`Identity` matrix, which does nothing.

In the following, we apply a :index:`zoom factor <pair: resolution;zoom>` of 2 to each dimension, which will generate an image with a four times better resolution for us (and also about 4 times the size)::

    zoom_x = 2.0  # horizontal zoom
    zomm_y = 2.0  # vertical zoom
    mat = fitz.Matrix(zoom_x, zomm_y)  # zoom factor 2 in each dimension
    pix = page.get_pixmap(matrix=mat)  # use 'mat' instead of the identity matrix


----------

How to Create :index:`Partial Pixmaps` (Clips)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
You do not always need the full image of a page. This may be the case e.g. when you display the image in a GUI and would like to zoom into a part of the page.

Let's assume your GUI window has room to display a full document page, but you now want to fill this room with the bottom right quarter of your page, thus using a four times better resolution.

To achieve this, we define a rectangle equal to the area we want to appear in the GUI and call it "clip". One way of constructing rectangles in PyMuPDF is by providing two diagonally opposite corners, which is what we are doing here.

.. image:: images/img-clip.*
   :scale: 80

::

    mat = fitz.Matrix(2, 2)  # zoom factor 2 in each direction
    rect = page.rect  # the page rectangle
    mp = (rect.tl + rect.br) / 2  # its middle point, becomes top-left of clip
    clip = fitz.Rect(mp, rect.br)  # the area we want
    pix = page.get_pixmap(matrix=mat, clip=clip)

In the above we construct *clip* by specifying two diagonally opposite points: the middle point *mp* of the page rectangle, and its bottom right, *rect.br*.

----------

How to Create or Suppress Annotation Images
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Normally, the pixmap of a page also shows the page's annotations. Occasionally, this may not be desirable.

To suppress the annotation images on a rendered page, just specify *annots=False* in :meth:`Page.get_pixmap`.

You can also render annotations separately: :ref:`Annot` objects have their own :meth:`Annot.get_pixmap` method. The resulting pixmap has the same dimensions as the annotation rectangle.

----------

.. index::
   triple: extract;image;non-PDF
   pair: convert_to_pdf;examples

How to Extract Images: Non-PDF Documents
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In contrast to the previous sections, this section deals with **extracting** images **contained** in documents, so they can be displayed as part of one or more pages.

If you want recreate the original image in file form or as a memory area, you have basically two options:

1. Convert your document to a PDF, and then use one of the PDF-only extraction methods. This snippet will convert a document to PDF::

    >>> pdfbytes = doc.convert_to_pdf()  # this a bytes object
    >>> pdf = fitz.open("pdf", pdfbytes)  # open it as a PDF document
    >>> # now use 'pdf' like any PDF document

2. Use :meth:`Page.get_text` with the "dict" parameter. This will extract all text and images shown on the page, formatted as a Python dictionary. Every image will occur in an image block, containing meta information and the binary image data. For details of the dictionary's structure, see :ref:`TextPage`. The method works equally well for PDF files. This creates a list of all images shown on a page::

    >>> d = page.get_text("dict")
    >>> blocks = d["blocks"]
    >>> imgblocks = [b for b in blocks if b["type"] == 1]

Each item if "imgblocks" is a dictionary which looks like this::

    {"type": 1, "bbox": (x0, y0, x1, y1), "width": w, "height": h, "ext": "png", "image": b"..."}

----------

.. index::
   triple: extract;image;PDF
   pair: extract_image;examples

How to Extract Images: PDF Documents
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Like any other "object" in a PDF, images are identified by a cross reference number (:data:`xref`, an integer). If you know this number, you have two ways to access the image's data:

1. **Create** a :ref:`Pixmap` of the image with instruction *pix = fitz.Pixmap(doc, xref)*. This method is **very** fast (single digit micro-seconds). The pixmap's properties (width, height, ...) will reflect the ones of the image. In this case there is no way to tell which image format the embedded original has.

2. **Extract** the image with *img = doc.extract_image(xref)*. This is a dictionary containing the binary image data as *img["image"]*. A number of meta data are also provided -- mostly the same as you would find in the pixmap of the image. The major difference is string *img["ext"]*, which specifies the image format: apart from "png", strings like "jpeg", "bmp", "tiff", etc. can also occur. Use this string as the file extension if you want to store to disk. The execution speed of this method should be compared to the combined speed of the statements *pix = fitz.Pixmap(doc, xref);pix.getPNGData()*. If the embedded image is in PNG format, the speed of :meth:`Document.extract_image` is about the same (and the binary image data are identical). Otherwise, this method is **thousands of times faster**, and the **image data is much smaller**.

The question remains: **"How do I know those 'xref' numbers of images?"**. There are two answers to this:

a. **"Inspect the page objects:"** Loop through the items of :meth:`Page.get_images`. It is a list of list, and its items look like *[xref, smask, ...]*, containing the :data:`xref` of an image. This :data:`xref` can then be used with one of the above methods. Use this method for **valid (undamaged)** documents. Be wary however, that the same image may be referenced multiple times (by different pages), so you might want to provide a mechanism avoiding multiple extracts.
b. **"No need to know:"** Loop through the list of **all xrefs** of the document and perform a :meth:`Document.extract_image` for each one. If the returned dictionary is empty, then continue -- this :data:`xref` is no image. Use this method if the PDF is **damaged (unusable pages)**. Note that a PDF often contains "pseudo-images" ("stencil masks") with the special purpose of defining the transparency of some other image. You may want to provide logic to exclude those from extraction. Also have a look at the next section.

For both extraction approaches, there exist ready-to-use general purpose scripts:

`extract-imga.py <https://github.com/JorjMcKie/PyMuPDF-Utilities/blob/master/extract-imga.py>`_ extracts images page by page:

.. image:: images/img-extract-imga.*
   :scale: 80

and `extract-imgb.py <https://github.com/JorjMcKie/PyMuPDF-Utilities/blob/master/extract-imgb.py>`_ extracts images by xref table:

.. image:: images/img-extract-imgb.*
   :scale: 80

----------

How to Handle Stencil Masks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Some images in PDFs are accompanied by **stencil masks**. In their simplest form stencil masks represent alpha (transparency) bytes stored as separate images. In order to reconstruct the original of an image, which has a stencil mask, it must be "enriched" with transparency bytes taken from its stencil mask.

Whether an image does have such a stencil mask can be recognized in one of two ways in PyMuPDF:

1. An item of :meth:`Document.get_page_images` has the general format *[xref, smask, ...]*, where *xref* is the image's :data:`xref` and *smask*, if positive, is the :data:`xref` of a stencil mask.
2. The (dictionary) results of :meth:`Document.extract_image` have a key *"smask"*, which also contains any stencil mask's :data:`xref` if positive.

If *smask == 0* then the image encountered via :data:`xref` can be processed as it is.

To recover the original image using PyMuPDF, the procedure depicted as follows must be executed:

.. image:: images/img-stencil.*
   :scale: 60

>>> pix1 = fitz.Pixmap(doc, xref)    # (1) pixmap of image w/o alpha
>>> pix2 = fitz.Pixmap(doc, smask)   # (2) stencil pixmap
>>> pix = fitz.Pixmap(pix1)          # (3) copy of pix1, empty alpha channel added
>>> pix.setAlpha(pix2.samples)       # (4) fill alpha channel

Step (1) creates a pixmap of the "netto" image. Step (2) does the same with the stencil mask. Please note that the :attr:`Pixmap.samples` attribute of *pix2* contains the alpha bytes that must be stored in the final pixmap. This is what happens in step (3) and (4).

The scripts `extract-imga.py <https://github.com/JorjMcKie/PyMuPDF-Utilities/blob/master/extract-imga.py>`_, and `extract-imgb.py <https://github.com/JorjMcKie/PyMuPDF-Utilities/blob/master/extract-imgb.py>`_ above also contain this logic.

----------

.. index::
   triple: picture;embed;PDF
   pair: show_pdf_page;examples
   pair: insert_image;examples
   pair: embfile_add;examples
   pair: addFileAnnot;examples

How to Make one PDF of all your Pictures (or Files)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
We show here **three scripts** that take a list of (image and other) files and put them all in one PDF.

**Method 1: Inserting Images as Pages**

The first one converts each image to a PDF page with the same dimensions. The result will be a PDF with one page per image. It will only work for supported image file formats::

 import os, fitz
 import PySimpleGUI as psg  # for showing a progress bar
 doc = fitz.open()  # PDF with the pictures
 imgdir = "D:/2012_10_05"  # where the pics are
 imglist = os.listdir(imgdir)  # list of them
 imgcount = len(imglist)  # pic count

 for i, f in enumerate(imglist):
     img = fitz.open(os.path.join(imgdir, f))  # open pic as document
     rect = img[0].rect  # pic dimension
     pdfbytes = img.convert_to_pdf()  # make a PDF stream
     img.close()  # no longer needed
     imgPDF = fitz.open("pdf", pdfbytes)  # open stream as PDF
     page = doc.new_page(width = rect.width,  # new page with ...
                        height = rect.height)  # pic dimension
     page.show_pdf_page(rect, imgPDF, 0)  # image fills the page
     psg.EasyProgressMeter("Import Images",  # show our progress
         i+1, imgcount)

 doc.save("all-my-pics.pdf")

This will generate a PDF only marginally larger than the combined pictures' size. Some numbers on performance:

The above script needed about 1 minute on my machine for 149 pictures with a total size of 514 MB (and about the same resulting PDF size).

.. image:: images/img-import-progress.*
   :scale: 80

Look `here <https://github.com/JorjMcKie/PyMuPDF-Utilities/blob/master/all-my-pics-inserted.py>`_ for a more complete source code: it offers a directory selection dialog and skips unsupported files and non-file entries.

.. note:: We might have used :meth:`Page.insert_image` instead of :meth:`Page.show_pdf_page`, and the result would have been a similar looking file. However, depending on the image type, it may store **images uncompressed**. Therefore, the save option *deflate = True* must be used to achieve a reasonable file size, which hugely increases the runtime for large numbers of images. So this alternative **cannot be recommended** here.

**Method 2: Embedding Files**

The second script **embeds** arbitrary files -- not only images. The resulting PDF will have just one (empty) page, required for technical reasons. To later access the embedded files again, you would need a suitable PDF viewer that can display and / or extract embedded files::

 import os, fitz
 import PySimpleGUI as psg  # for showing progress bar
 doc = fitz.open()  # PDF with the pictures
 imgdir = "D:/2012_10_05"  # where my files are

 imglist = os.listdir(imgdir)  # list of pictures
 imgcount = len(imglist)  # pic count
 imglist.sort()  # nicely sort them

 for i, f in enumerate(imglist):
     img = open(os.path.join(imgdir,f), "rb").read()  # make pic stream
     doc.embfile_add(img, f, filename=f,  # and embed it
                         ufilename=f, desc=f)
     psg.EasyProgressMeter("Embedding Files",  # show our progress
         i+1, imgcount)

 page = doc.new_page()  # at least 1 page is needed

 doc.save("all-my-pics-embedded.pdf")

.. image:: images/img-embed-progress.*
   :scale: 80

This is by far the fastest method, and it also produces the smallest possible output file size. The above pictures needed 20 seconds on my machine and yielded a PDF size of 510 MB. Look `here <https://github.com/JorjMcKie/PyMuPDF-Utilities/blob/master/all-my-pics-embedded.py>`_ for a more complete source code: it offers a directory selection dialog and skips non-file entries.

**Method 3: Attaching Files**

A third way to achieve this task is **attaching files** via page annotations see `here <https://github.com/JorjMcKie/PyMuPDF-Utilities/blob/master/all-my-pics-attached.py>`_ for the complete source code.

This has a similar performance as the previous script and it also produces a similar file size. It will produce PDF pages which show a 'FileAttachment' icon for each attached file.

.. image:: images/img-attach-result.*

.. note:: Both, the **embed** and the **attach** methods can be used for **arbitrary files** -- not just images.

.. note:: We strongly recommend using the awesome package `PySimpleGUI <https://pypi.org/project/PySimpleGUI/>`_ to display a progress meter for tasks that may run for an extended time span. It's pure Python, uses Tkinter (no additional GUI package) and requires just one more line of code!

----------

.. index::
   triple: vector;image;SVG
   pair: show_pdf_page;examples
   pair: insert_image;examples
   pair: embfile_add;examples

How to Create Vector Images
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The usual way to create an image from a document page is :meth:`Page.get_pixmap`. A pixmap represents a raster image, so you must decide on its quality (i.e. resolution) at creation time. It cannot be changed later.

PyMuPDF also offers a way to create a **vector image** of a page in SVG format (scalable vector graphics, defined in XML syntax). SVG images remain precise across zooming levels (of course with the exception of any raster graphic elements embedded therein).

Instruction *svg = page.get_svg_image(matrix=fitz.Identity)* delivers a UTF-8 string *svg* which can be stored with extension ".svg".

----------

.. index::
   pair: writeImage;examples
   pair: getImageData;examples
   pair: Photoshop;examples
   pair: Postscript;examples
   pair: JPEG;examples
   pair: PhotoImage;examples

How to Convert Images
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Just as a feature among others, PyMuPDF's image conversion is easy. It may avoid using other graphics packages like PIL/Pillow in many cases.

Notwithstanding that interfacing with Pillow is almost trivial.

================= ================== =========================================
**Input Formats** **Output Formats** **Description**
================= ================== =========================================
BMP               .                  Windows Bitmap
JPEG              .                  Joint Photographic Experts Group
JXR               .                  JPEG Extended Range
JPX               .                  JPEG 2000
GIF               .                  Graphics Interchange Format
TIFF              .                  Tagged Image File Format
PNG               PNG                Portable Network Graphics
PNM               PNM                Portable Anymap
PGM               PGM                Portable Graymap
PBM               PBM                Portable Bitmap
PPM               PPM                Portable Pixmap
PAM               PAM                Portable Arbitrary Map
.                 PSD                Adobe Photoshop Document
.                 PS                 Adobe Postscript
================= ================== =========================================

The general scheme is just the following two lines::

    pix = fitz.Pixmap("input.xxx")  # any supported input format
    pix.writeImage("output.yyy")  # any supported output format

**Remarks**

1. The **input** argument of *fitz.Pixmap(arg)* can be a file or a bytes / io.BytesIO object containing an image.
2. Instead of an output **file**, you can also create a bytes object via *pix.getImageData("yyy")* and pass this around.
3. As a matter of course, input and output formats must be compatible in terms of colorspace and transparency. The *Pixmap* class has batteries included if adjustments are needed.

.. note::
        **Convert JPEG to Photoshop**::

          pix = fitz.Pixmap("myfamily.jpg")
          pix.writeImage("myfamily.psd")


.. note::
        **Save to JPEG** using PIL/Pillow::

          from PIL import Image
          pix = fitz.Pixmap(...)
          img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
          img.save("output.jpg", "JPEG")

.. note::
        Convert **JPEG to Tkinter PhotoImage**. Any **RGB / no-alpha** image works exactly the same. Conversion to one of the **Portable Anymap** formats (PPM, PGM, etc.) does the trick, because they are supported by all Tkinter versions::

          if str is bytes:  # this is Python 2!
              import Tkinter as tk
          else:  # Python 3 or later!
              import tkinter as tk
          pix = fitz.Pixmap("input.jpg")  # or any RGB / no-alpha image
          tkimg = tk.PhotoImage(data=pix.getImageData("ppm"))

.. note::
        Convert **PNG with alpha** to Tkinter PhotoImage. This requires **removing the alpha bytes**, before we can do the PPM conversion::

          if str is bytes:  # this is Python 2!
              import Tkinter as tk
          else:  # Python 3 or later!
              import tkinter as tk
          pix = fitz.Pixmap("input.png")  # may have an alpha channel
          if pix.alpha:  # we have an alpha channel!
              pix = fitz.Pixmap(pix, 0)  # remove it
          tkimg = tk.PhotoImage(data=pix.getImageData("ppm"))

----------

.. index::
   pair: copyPixmap;examples

How to Use Pixmaps: Gluing Images
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This shows how pixmaps can be used for purely graphical, non-document purposes. The script reads an image file and creates a new image which consist of 3 * 4 tiles of the original::

 import fitz
 src = fitz.Pixmap("img-7edges.png")      # create pixmap from a picture
 col = 3                                  # tiles per row
 lin = 4                                  # tiles per column
 tar_w = src.width * col                  # width of target
 tar_h = src.height * lin                 # height of target

 # create target pixmap
 tar_pix = fitz.Pixmap(src.colorspace, (0, 0, tar_w, tar_h), src.alpha)

 # now fill target with the tiles
 for i in range(col):
     for j in range(lin):
         src.setOrigin(src.width * i, src.height * j)
         tar_pix.copyPixmap(src, src.irect) # copy input to new loc

 tar_pix.writePNG("tar.png")

This is the input picture:

.. image:: images/img-7edges.png
   :scale: 33

Here is the output:

.. image:: images/img-target.png
   :scale: 33

----------

.. index::
   pair: setRect;examples
   pair: invertIRect;examples
   pair: copyPixmap;examples
   pair: writeImage;examples

How to Use Pixmaps: Making a Fractal
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here is another Pixmap example that creates **Sierpinski's Carpet** -- a fractal generalizing the **Cantor Set** to two dimensions. Given a square carpet, mark its 9 sub-suqares (3 times 3) and cut out the one in the center. Treat each of the remaining eight sub-squares in the same way, and continue *ad infinitum*. The end result is a set with area zero and fractal dimension 1.8928...

This script creates a approximate image of it as a PNG, by going down to one-pixel granularity. To increase the image precision, change the value of n (precision)::

    import fitz, time
    if not list(map(int, fitz.VersionBind.split("."))) >= [1, 14, 8]:
        raise SystemExit("need PyMuPDF v1.14.8 for this script")
    n = 6                             # depth (precision)
    d = 3**n                          # edge length

    t0 = time.perf_counter()
    ir = (0, 0, d, d)                 # the pixmap rectangle

    pm = fitz.Pixmap(fitz.csRGB, ir, False)
    pm.setRect(pm.irect, (255,255,0)) # fill it with some background color

    color = (0, 0, 255)               # color to fill the punch holes

    # alternatively, define a 'fill' pixmap for the punch holes
    # this could be anything, e.g. some photo image ...
    fill = fitz.Pixmap(fitz.csRGB, ir, False) # same size as 'pm'
    fill.setRect(fill.irect, (0, 255, 255))   # put some color in

    def punch(x, y, step):
        """Recursively "punch a hole" in the central square of a pixmap.
        
        Arguments are top-left coords and the step width.

        Some alternative punching methods are commented out.
        """
        s = step // 3                 # the new step
        # iterate through the 9 sub-squares
        # the central one will be filled with the color
        for i in range(3):
            for j in range(3):
                if i != j or i != 1:  # this is not the central cube
                    if s >= 3:        # recursing needed?
                        punch(x+i*s, y+j*s, s)       # recurse
                else:                 # punching alternatives are:
                    pm.setRect((x+s, y+s, x+2*s, y+2*s), color)     # fill with a color
                    #pm.copyPixmap(fill, (x+s, y+s, x+2*s, y+2*s))  # copy from fill
                    #pm.invertIRect((x+s, y+s, x+2*s, y+2*s))       # invert colors

        return

    #==============================================================================
    # main program
    #==============================================================================
    # now start punching holes into the pixmap
    punch(0, 0, d)
    t1 = time.perf_counter()
    pm.writeImage("sierpinski-punch.png")
    t2 = time.perf_counter()
    print ("%g sec to create / fill the pixmap" % round(t1-t0,3))
    print ("%g sec to save the image" % round(t2-t1,3))

The result should look something like this:

.. image:: images/img-sierpinski.png
   :scale: 33

----------

How to Interface with NumPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This shows how to create a PNG file from a numpy array (several times faster than most other methods)::

 import numpy as np
 import fitz
 #==============================================================================
 # create a fun-colored width * height PNG with fitz and numpy
 #==============================================================================
 height = 150
 width  = 100
 bild = np.ndarray((height, width, 3), dtype=np.uint8)

 for i in range(height):
     for j in range(width):
         # one pixel (some fun coloring)
         bild[i, j] = [(i+j)%256, i%256, j%256]

 samples = bytearray(bild.tostring())    # get plain pixel data from numpy array
 pix = fitz.Pixmap(fitz.csRGB, width, height, samples, alpha=False)
 pix.writePNG("test.png")


----------

How to Add Images to a PDF Page
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There are two methods to add images to a PDF page: :meth:`Page.insert_image` and :meth:`Page.show_pdf_page`. Both methods have things in common, but there also exist differences.

============================== ===================================== =========================================
**Criterion**                  :meth:`Page.insert_image`              :meth:`Page.show_pdf_page`
============================== ===================================== =========================================
displayable content            image file, image in memory, pixmap   PDF page
display resolution             image resolution                      vectorized (except raster page content)
rotation                       multiple of 90 degrees                any angle
clipping                       no (full image only)                  yes
keep aspect ratio              yes (default option)                  yes (default option)
transparency (water marking)   depends on image                      yes
location / placement           scaled to fit target rectangle        scaled to fit target rectangle
performance                    automatic prevention of duplicates;   automatic prevention of duplicates;
                               MD5 calculation on every execution    faster than :meth:`Page.insert_image`
multi-page image support       no                                    yes
ease of use                    simple, intuitive;                    simple, intuitive;
                               performance considerations apply      **usable for all document types**
                               for multiple insertions of same image (including images!) after conversion to
                                                                     PDF via :meth:`Document.convert_to_pdf`
============================== ===================================== =========================================

Basic code pattern for :meth:`Page.insert_image`. **Exactly one** of the parameters **filename / stream / pixmap** must be given::

    page.insert_image(
        rect,                  # where to place the image (rect-like)
        filename=None,         # image in a file
        stream=None,           # image in memory (bytes)
        pixmap=None,           # image from pixmap
        rotate=0,              # rotate (int, multiple of 90)
        keep_proportion=True,  # keep aspect ratio
        overlay=True,          # put in foreground
    )

Basic code pattern for :meth:`Page.show_pdf_page`. Source and target PDF must be different :ref:`Document` objects (but may be opened from the same file)::

    page.show_pdf_page(
        rect,                  # where to place the image (rect-like)
        src,                   # source PDF
        pno=0,                 # page number in source PDF
        clip=None,             # only display this area (rect-like)
        rotate=0,              # rotate (float, any value)
        keep_proportion=True,  # keep aspect ratio
        overlay=True,          # put in foreground
    )

Text
-----

----------

How to Extract all Document Text
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This script will take a document filename and generate a text file from all of its text.

The document can be any supported type like PDF, XPS, etc.

The script works as a command line tool which expects the document filename supplied as a parameter. It generates one text file named "filename.txt" in the script directory. Text of pages is separated by a form feed character::

    import sys, fitz
    fname = sys.argv[1]  # get document filename
    doc = fitz.open(fname)  # open document
    out = open(fname + ".txt", "wb")  # open text output
    for page in doc:  # iterate the document pages
        text = page.get_text().encode("utf8")  # get plain text (is in UTF-8)
        out.write(text)  # write text of page
        out.write(bytes((12,)))  # write page delimiter (form feed 0x0C)
    out.close()

The output will be plain text as it is coded in the document. No effort is made to prettify in any way. Specifically for PDF, this may mean output not in usual reading order, unexpected line breaks and so forth.

You have many options to cure this -- see chapter :ref:`Appendix2`. Among them are:

1. Extract text in HTML format and store it as a HTML document, so it can be viewed in any browser.
2. Extract text as a list of text blocks via *Page.get_text("blocks")*. Each item of this list contains position information for its text, which can be used to establish a convenient reading order.
3. Extract a list of single words via *Page.get_text("words")*. Its items are words with position information. Use it to determine text contained in a given rectangle -- see next section.

See the following two section for examples and further explanations.


.. index::
   triple: extract;text;rectangle

How to Extract Text from within a Rectangle
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
There is now (v1.18.0) more than one way to achieve this. We therefore have created a `folder <https://github.com/pymupdf/PyMuPDF-Utilities/tree/master/textbox-extraction>`_ in the PyMuPDF-Utilities repository specifically dealing with this topic.

----------

.. index::
    pair: text;reading order

How to Extract Text in Natural Reading Order
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

One of the common issues with PDF text extraction is, that text may not appear in any particular reading order.

Responsible for this effect is the PDF creator (software or a human). For example, page headers may have been inserted in a separate step -- after the document had been produced. In such a case, the header text will appear at the end of a page text extraction (although it will be correctly shown by PDF viewer software). For example, the following snippet will add some header and footer lines to an existing PDF::

    doc = fitz.open("some.pdf")
    header = "Header"  # text in header
    footer = "Page %i of %i"  # text in footer
    for page in doc:
        page.insert_text((50, 50), header)  # insert header
        page.insert_text(  # insert footer 50 points above page bottom
            (50, page.rect.height - 50),
            footer % (page.number + 1, len(doc)),
        )

The text sequence extracted from a page modified in this way will look like this:

1. original text
2. header line
3. footer line

PyMuPDF has several means to re-establish some reading sequence or even to re-generate a layout close to the original.

As a starting point take the above mentioned `script <https://github.com/pymupdf/PyMuPDF/wiki/How-to-extract-text-from-a-rectangle>`_ and then use the full page rectangle.

On rare occasions, when the PDF creator has been "over-creative", extracted text does not even keep the correct reading sequence of **single letters**: instead of the two words "DELUXE PROPERTY" you might sometimes get an anagram, consisting of 8 words like "DEL", "XE" , "P", "OP", "RTY", "U", "R" and "E".

Such a PDF is also not searchable by all PDF viewers, but it is displayed correctly and looks harmless.

In those cases, the following function will help composing the original words of the page. The resulting list is also searchable and can be used to deliver rectangles for the found text locations::

    from operator import itemgetter
    from itertools import groupby
    import fitz

    def recover(words, rect):
        """ Word recovery.

        Notes:
            Method 'get_textWords()' does not try to recover words, if their single
            letters do not appear in correct lexical order. This function steps in
            here and creates a new list of recovered words.
        Args:
            words: list of words as created by 'get_textWords()'
            rect: rectangle to consider (usually the full page)
        Returns:
            List of recovered words. Same format as 'get_text_words', but left out
            block, line and word number - a list of items of the following format:
            [x0, y0, x1, y1, "word"]
        """
        # build my sublist of words contained in given rectangle
        mywords = [w for w in words if fitz.Rect(w[:4]) in rect]

        # sort the words by lower line, then by word start coordinate
        mywords.sort(key=itemgetter(3, 0))  # sort by y1, x0 of word rectangle

        # build word groups on same line
        grouped_lines = groupby(mywords, key=itemgetter(3))

        words_out = []  # we will return this

        # iterate through the grouped lines
        # for each line coordinate ("_"), the list of words is given
        for _, words_in_line in grouped_lines:
            for i, w in enumerate(words_in_line):
                if i == 0:  # store first word
                    x0, y0, x1, y1, word = w[:5]
                    continue

                r = fitz.Rect(w[:4])  # word rect

                # Compute word distance threshold as 20% of width of 1 letter.
                # So we should be safe joining text pieces into one word if they
                # have a distance shorter than that.
                threshold = r.width / len(w[4]) / 5
                if r.x0 <= x1 + threshold:  # join with previous word
                    word += w[4]  # add string
                    x1 = r.x1  # new end-of-word coordinate
                    y0 = max(y0, r.y0)  # extend word rect upper bound
                    continue

                # now have a new word, output previous one
                words_out.append([x0, y0, x1, y1, word])

                # store the new word
                x0, y0, x1, y1, word = w[:5]

            # output word waiting for completion
            words_out.append([x0, y0, x1, y1, word])

        return words_out

    def search_for(text, words):
        """ Search for text in items of list of words

        Notes:
            Can be adjusted / extended in obvious ways, e.g. using regular
            expressions, or being case insensitive, or only looking for complete
            words, etc.
        Args:
            text: string to be searched for
            words: list of items in format delivered by 'get_text_words()'.
        Returns:
            List of rectangles, one for each found locations.
        """
        rect_list = []
        for w in words:
            if text in w[4]:
                rect_list.append(fitz.Rect(w[:4]))

        return rect_list


----------

How to :index:`Extract Tables <pair: extract; table>` from Documents
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
If you see a table in a document, you are not normally looking at something like an embedded Excel or other identifiable object. It usually is just text, formatted to appear as appropriate.

Extracting a tabular data from such a page area therefore means that you must find a way to **(1)** graphically indicate table and column borders, and **(2)** then extract text based on this information.

The wxPython GUI script `wxTableExtract.py <https://github.com/pymupdf/PyMuPDF-Utilities/tree/master/examples/wxTableExtract.py>`_ strives to exactly do that. You may want to have a look at it and adjust it to your liking.

----------

How to Mark Extracted Text
~~~~~~~~~~~~~~~~~~~~~~~~~~
There is a standard search function to search for arbitrary text on a page: :meth:`Page.search_for`. It returns a list of :ref:`Rect` objects which surround a found occurrence. These rectangles can for example be used to automatically insert annotations which visibly mark the found text.

This method has advantages and drawbacks. Pros are

* The search string can contain blanks and wrap across lines
* Upper or lower case characters are treated equal
* Word hyphenation at line ends is detected and resolved
* return may also be a list of :ref:`Quad` objects to precisely locate text that is **not parallel** to either axis -- using :ref:`Quad` output is also recommend, when page rotation is not zero.

But you also have other options::

 import sys
 import fitz

 def mark_word(page, text):
     """Underline each word that contains 'text'.
     """
     found = 0
     wlist = page.getTex("words")  # make the word list
     for w in wlist:  # scan through all words on page
         if text in w[4]:  # w[4] is the word's string
             found += 1  # count
             r = fitz.Rect(w[:4])  # make rect from word bbox
             page.addUnderlineAnnot(r)  # underline
     return found

 fname = sys.argv[1]  # filename
 text = sys.argv[2]  # search string
 doc = fitz.open(fname)

 print("underlining words containing '%s' in document '%s'" % (word, doc.name))

 new_doc = False  # indicator if anything found at all

 for page in doc:  # scan through the pages
     found = mark_word(page, text)  # mark the page's words
     if found:  # if anything found ...
         new_doc = True
         print("found '%s' %i times on page %i" % (text, found, page.number + 1))

 if new_doc:
     doc.save("marked-" + doc.name)

This script uses :meth:`Page.get_text("words")` to look for a string, handed in via cli parameter. This method separates a page's text into "words" using spaces and line breaks as delimiters. Therefore the words in this lists do not contain these characters. Further remarks:

* If found, the **complete word containing the string** is marked (underlined) -- not only the search string.
* The search string may **not contain spaces** or other white space.
* As shown here, upper / lower cases are **respected**. But this can be changed by using the string method *lower()* (or even regular expressions) in function *mark_word*.
* There is **no upper limit**: all occurrences will be detected.
* You can use **anything** to mark the word: 'Underline', 'Highlight', 'StrikeThrough' or 'Square' annotations, etc.
* Here is an example snippet of a page of this manual, where "MuPDF" has been used as the search string. Note that all strings **containing "MuPDF"** have been completely underlined (not just the search string).

.. image:: images/img-markedpdf.*
   :scale: 60

----------------------------------------------

How to Mark Searched Text
~~~~~~~~~~~~~~~~~~~~~~~~~~
This script searches for text and marks it::

    # -*- coding: utf-8 -*-
    import fitz

    # the document to annotate
    doc = fitz.open("tilted-text.pdf")

    # the text to be marked
    t = "¡La práctica hace el campeón!"

    # work with first page only
    page = doc[0]

    # get list of text locations
    # we use "quads", not rectangles because text may be tilted!
    rl = page.search_for(t, quads = True)

    # mark all found quads with one annotation
    page.addSquigglyAnnot(rl)

    # save to a new PDF
    doc.save("a-squiggly.pdf")

The result looks like this:

.. image:: images/img-textmarker.*
   :scale: 80

----------------------------------------------

How to Mark Non-horizontal Text
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The previous section already shows an example for marking non-horizontal text detected by text **searching**.

But text **extraction** with the "dict" option of :meth:`Page.get_text` may also return text with a non-zero angle to the x-axis. This is reflected by the value of the ``"dir"`` key of the line dictionary: it is the tuple ``(cosine, sine)`` of that angle.

Currently, all bboxes returned by the method's are rectangles only -- no quads. So we can mark the span text (correctly) only, if the **angle is 0, 90, 180 or 270 degrees.**

In this case we can convert the span bbox into the right quad by choosing the right sequence of its corners::

    r = fitz.Rect(span["bbox"])

    if line["dir"] == (1, 0):  # rotation 0
        q = fitz.Quad(r)

    elif line["dir"] == (0, -1):  # rotation 90
        q = fitz.Quad(r.bl, r.tl, r.br, r.tr)

    elif line["dir"] == (-1, 0):  # rotation 180
        q = fitz.Quad(r.br, r.bl, r.tr, r.tl)

    elif line["dir"] == (0, 1):  # rotation 270
        q = fitz.Quad(r.tr, r.br, r.tl, r.bl)

    else:
        q = fitz.Quad(r)
        print("warning: unsupported text flow")

    annot = page.addHighlightAnnot(q)


------------------------------

How to Analyze Font Characteristics
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
To analyze the characteristics of text in a PDF use this elementary script as a starting point:

.. literalinclude:: text-lister.py
   :language: python

Here is the PDF page and the script output:

.. image:: images/img-pdftext.*
   :scale: 80

-----------------------------------------

How to Insert Text
~~~~~~~~~~~~~~~~~~~~
PyMuPDF provides ways to insert text on new or existing PDF pages with the following features:

* choose the font, including built-in fonts and fonts that are available as files
* choose text characteristics like bold, italic, font size, font color, etc.
* position the text in multiple ways:

    - either as simple line-oriented output starting at a certain point,
    - or fitting text in a box provided as a rectangle, in which case text alignment choices are also available,
    - choose whether text should be put in foreground (overlay existing content),
    - all text can be arbitrarily "morphed", i.e. its appearance can be changed via a :ref:`Matrix`, to achieve effects like scaling, shearing or mirroring,
    - independently from morphing and in addition to that, text can be rotated by integer multiples of 90 degrees.

All of the above is provided by three basic :ref:`Page`, resp. :ref:`Shape` methods:

* :meth:`Page.insert_font` -- install a font for the page for later reference. The result is reflected in the output of :meth:`Document.get_page_fonts`. The font can be:

    - provided as a file,
    - already present somewhere in **this or another** PDF, or
    - be a **built-in** font.

* :meth:`Page.insert_text` -- write some lines of text. Internally, this uses :meth:`Shape.insert_text`.

* :meth:`Page.insert_textbox` -- fit text in a given rectangle. Here you can choose text alignment features (left, right, centered, justified) and you keep control as to whether text actually fits. Internally, this uses :meth:`Shape.insert_textbox`.

.. note:: Both text insertion methods automatically install the font as necessary.

How to Write Text Lines
^^^^^^^^^^^^^^^^^^^^^^^^^^
Output some text lines on a page::

    import fitz
    doc = fitz.open(...)  # new or existing PDF
    page = doc.new_page()  # new or existing page via doc[n]
    p = fitz.Point(50, 72)  # start point of 1st line

    text = "Some text,\nspread across\nseveral lines."
    # the same result is achievable by
    # text = ["Some text", "spread across", "several lines."]

    rc = page.insert_text(p,  # bottom-left of 1st char
                         text,  # the text (honors '\n')
                         fontname = "helv",  # the default font
                         fontsize = 11,  # the default font size
                         rotate = 0,  # also available: 90, 180, 270
                         )
    print("%i lines printed on page %i." % (rc, page.number))

    doc.save("text.pdf")

With this method, only the **number of lines** will be controlled to not go beyond page height. Surplus lines will not be written and the number of actual lines will be returned. The calculation uses *1.2 * fontsize* as the line height and 36 points (0.5 inches) as bottom margin.

Line **width is ignored**. The surplus part of a line will simply be invisible.

However, for built-in fonts there are ways to calculate the line width beforehand - see :meth:`getTextlength`.

Here is another example. It inserts 4 text strings using the four different rotation options, and thereby explains, how the text insertion point must be chosen to achieve the desired result::

    import fitz
    doc = fitz.open()
    page = doc.new_page()
    # the text strings, each having 3 lines
    text1 = "rotate=0\nLine 2\nLine 3"
    text2 = "rotate=90\nLine 2\nLine 3"
    text3 = "rotate=-90\nLine 2\nLine 3"
    text4 = "rotate=180\nLine 2\nLine 3"
    red = (1, 0, 0) # the color for the red dots
    # the insertion points, each with a 25 pix distance from the corners
    p1 = fitz.Point(25, 25)
    p2 = fitz.Point(page.rect.width - 25, 25)
    p3 = fitz.Point(25, page.rect.height - 25)
    p4 = fitz.Point(page.rect.width - 25, page.rect.height - 25)
    # create a Shape to draw on
    shape = page.new_shape()

    # draw the insertion points as red, filled dots
    shape.draw_circle(p1,1)
    shape.draw_circle(p2,1)
    shape.draw_circle(p3,1)
    shape.draw_circle(p4,1)
    shape.finish(width=0.3, color=red, fill=red)

    # insert the text strings
    shape.insert_text(p1, text1)
    shape.insert_text(p3, text2, rotate=90)
    shape.insert_text(p2, text3, rotate=-90)
    shape.insert_text(p4, text4, rotate=180)

    # store our work to the page
    shape.commit()
    doc.save(...)

This is the result:

.. image:: images/img-inserttext.*
   :scale: 33



------------------------------------------

How to Fill a Text Box
^^^^^^^^^^^^^^^^^^^^^^^^^^
This script fills 4 different rectangles with text, each time choosing a different rotation value::

    import fitz
    doc = fitz.open(...)  # new or existing PDF
    page = doc.new_page()  # new page, or choose doc[n]
    r1 = fitz.Rect(50,100,100,150)  # a 50x50 rectangle
    disp = fitz.Rect(55, 0, 55, 0)  # add this to get more rects
    r2 = r1 + disp  # 2nd rect
    r3 = r1 + disp * 2  # 3rd rect
    r4 = r1 + disp * 3  # 4th rect
    t1 = "text with rotate = 0."  # the texts we will put in
    t2 = "text with rotate = 90."
    t3 = "text with rotate = -90."
    t4 = "text with rotate = 180."
    red  = (1,0,0)  # some colors
    gold = (1,1,0)
    blue = (0,0,1)
    """We use a Shape object (something like a canvas) to output the text and
    the rectangles surrounding it for demonstration.
    """
    shape = page.new_shape()  # create Shape
    shape.draw_rect(r1)  # draw rectangles
    shape.draw_rect(r2)  # giving them
    shape.draw_rect(r3)  # a yellow background
    shape.draw_rect(r4)  # and a red border
    shape.finish(width = 0.3, color = red, fill = gold)
    # Now insert text in the rectangles. Font "Helvetica" will be used
    # by default. A return code rc < 0 indicates insufficient space (not checked here).
    rc = shape.insert_textbox(r1, t1, color = blue)
    rc = shape.insert_textbox(r2, t2, color = blue, rotate = 90)
    rc = shape.insert_textbox(r3, t3, color = blue, rotate = -90)
    rc = shape.insert_textbox(r4, t4, color = blue, rotate = 180)
    shape.commit()  # write all stuff to page /Contents
    doc.save("...")

Several default values were used above: font "Helvetica", font size 11 and text alignment "left". The result will look like this:

.. image:: images/img-textbox.*
   :scale: 50

------------------------------------------

How to Use Non-Standard Encoding
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Since v1.14, MuPDF allows Greek and Russian encoding variants for the :data:`Base14_Fonts`. In PyMuPDF this is supported via an additional *encoding* argument. Effectively, this is relevant for Helvetica, Times-Roman and Courier (and their bold / italic forms) and characters outside the ASCII code range only. Elsewhere, the argument is ignored. Here is how to request Russian encoding with the standard font Helvetica::

    page.insert_text(point, russian_text, encoding=fitz.TEXT_ENCODING_CYRILLIC)

The valid encoding values are TEXT_ENCODING_LATIN (0), TEXT_ENCODING_GREEK (1), and TEXT_ENCODING_CYRILLIC (2, Russian) with Latin being the default. Encoding can be specified by all relevant font and text insertion methods.

By the above statement, the fontname *helv* is automatically connected to the Russian font variant of Helvetica. Any subsequent text insertion with **this fontname** will use the Russian Helvetica encoding.

If you change the fontname just slightly, you can also achieve an **encoding "mixture"** for the **same base font** on the same page::

    import fitz
    doc=fitz.open()
    page = doc.new_page()
    shape = page.new_shape()
    t="Sômé tèxt wìth nöñ-Lâtîn characterß."
    shape.insert_text((50,70), t, fontname="helv", encoding=fitz.TEXT_ENCODING_LATIN)
    shape.insert_text((50,90), t, fontname="HElv", encoding=fitz.TEXT_ENCODING_GREEK)
    shape.insert_text((50,110), t, fontname="HELV", encoding=fitz.TEXT_ENCODING_CYRILLIC)
    shape.commit()
    doc.save("t.pdf")

The result:

.. image:: images/img-encoding.*
   :scale: 50

The snippet above indeed leads to three different copies of the Helvetica font in the PDF. Each copy is uniquely identified (and referenceable) by using the correct upper-lower case spelling of the reserved word "helv"::

    for f in doc.get_page_fonts(0): print(f)

    [6, 'n/a', 'Type1', 'Helvetica', 'helv', 'WinAnsiEncoding']
    [7, 'n/a', 'Type1', 'Helvetica', 'HElv', 'WinAnsiEncoding']
    [8, 'n/a', 'Type1', 'Helvetica', 'HELV', 'WinAnsiEncoding']

-----------------------

Annotations
-----------
In v1.14.0, annotation handling has been considerably extended:

* New annotation type support for 'Ink', 'Rubber Stamp' and 'Squiggly' annotations. Ink annots simulate handwriting by combining one or more lists of interconnected points. Stamps are intended to visually inform about a document's status or intended usage (like "draft", "confidential", etc.). 'Squiggly' is a text marker annot, which underlines selected text with a zigzagged line.

* Extended 'FreeText' support:
    1. all characters from the *Latin* character set are now available,
    2. colors of text, rectangle background and rectangle border can be independently set
    3. text in rectangle can be rotated by either +90 or -90 degrees
    4. text is automatically wrapped (made multi-line) in available rectangle
    5. all Base-14 fonts are now available (*normal* variants only, i.e. no bold, no italic).
* MuPDF now supports line end icons for 'Line' annots (only). PyMuPDF supported that in v1.13.x already -- and for (almost) the full range of applicable types. So we adjusted the appearance of 'Polygon' and 'PolyLine' annots to closely resemble the one of MuPDF for 'Line'.
* MuPDF now provides its own annotation icons where relevant. PyMuPDF switched to using them (for 'FileAttachment' and 'Text' ["sticky note"] so far).
* MuPDF now also supports 'Caret', 'Movie', 'Sound' and 'Signature' annotations, which we may include in PyMuPDF at some later time.

How to Add and Modify Annotations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In PyMuPDF, new annotations can be added via :ref:`Page` methods. Once an annotation exists, it can be modified to a large extent using methods of the :ref:`Annot` class.

In contrast to many other tools, initial insert of annotations happens with a minimum number of properties. We leave it to the programmer to e.g. set attributes like author, creation date or subject.

As an overview for these capabilities, look at the following script that fills a PDF page with most of the available annotations. Look in the next sections for more special situations:

.. literalinclude:: new-annots.py
   :language: python


This script should lead to the following output:

.. image:: images/img-annots.*
   :scale: 80

------------------------------

How to Use FreeText
~~~~~~~~~~~~~~~~~~~~~
This script shows a couple of ways to deal with 'FreeText' annotations::

    # -*- coding: utf-8 -*-
    import fitz

    # some colors
    blue  = (0,0,1)
    green = (0,1,0)
    red   = (1,0,0)
    gold  = (1,1,0)

    # a new PDF with 1 page
    doc = fitz.open()
    page = doc.new_page()

    # 3 rectangles, same size, above each other
    r1 = fitz.Rect(100,100,200,150)
    r2 = r1 + (0,75,0,75)
    r3 = r2 + (0,75,0,75)

    # the text, Latin alphabet
    t = "¡Un pequeño texto para practicar!"

    # add 3 annots, modify the last one somewhat
    a1 = page.addFreetextAnnot(r1, t, color=red)
    a2 = page.addFreetextAnnot(r2, t, fontname="Ti", color=blue)
    a3 = page.addFreetextAnnot(r3, t, fontname="Co", color=blue, rotate=90)
    a3.set_border(width=0)
    a3.update(fontsize=8, fill_color=gold)

    # save the PDF
    doc.save("a-freetext.pdf")

The result looks like this:

.. image:: images/img-freetext.*
   :scale: 80

------------------------------

Using Buttons and JavaScript
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Since MuPDF v1.16, 'FreeText' annotations no longer support bold or italic versions of the Times-Roman, Helvetica or Courier fonts.

A big **thank you** to our user `@kurokawaikki <https://github.com/kurokawaikki>`_, who contributed the following script to **circumvent this restriction**.

.. literalinclude:: make-bold.py
   :language: python

--------------------------

How to Use Ink Annotations
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Ink annotations are used to contain freehand scribbling. A typical example maybe an image of your signature consisting of first name and last name. Technically an ink annotation is implemented as a **list of lists of points**. Each point list is regarded as a continuous line connecting the points. Different point lists represent independent line segments of the annotation.

The following script creates an ink annotation with two mathematical curves (sine and cosine function graphs) as line segments::

    import math
    import fitz

    #------------------------------------------------------------------------------
    # preliminary stuff: create function value lists for sine and cosine
    #------------------------------------------------------------------------------
    w360 = math.pi * 2  # go through full circle
    deg = w360 / 360  # 1 degree as radians
    rect = fitz.Rect(100,200, 300, 300)  # use this rectangle
    first_x = rect.x0  # x starts from left
    first_y = rect.y0 + rect.height / 2.  # rect middle means y = 0
    x_step = rect.width / 360  # rect width means 360 degrees
    y_scale = rect.height / 2.  # rect height means 2
    sin_points = []  # sine values go here
    cos_points = []  # cosine values go here
    for x in range(362):  # now fill in the values
        x_coord = x * x_step + first_x  # current x coordinate
        y = -math.sin(x * deg)  # sine
        p = (x_coord, y * y_scale + first_y)  # corresponding point
        sin_points.append(p)  # append
        y = -math.cos(x * deg)  # cosine
        p = (x_coord, y * y_scale + first_y)  # corresponding point
        cos_points.append(p)  # append

    #------------------------------------------------------------------------------
    # create the document with one page
    #------------------------------------------------------------------------------
    doc = fitz.open()  # make new PDF
    page = doc.new_page()  # give it a page

    #------------------------------------------------------------------------------
    # add the Ink annotation, consisting of 2 curve segments
    #------------------------------------------------------------------------------
    annot = page.addInkAnnot((sin_points, cos_points))
    # let it look a little nicer
    annot.set_border(width=0.3, dashes=[1,])  # line thickness, some dashing
    annot.set_colors(stroke=(0,0,1))  # make the lines blue
    annot.update()  # update the appearance

    page.draw_rect(rect, width=0.3)  # only to demonstrate we did OK

    doc.save("a-inktest.pdf")

This is the result:

.. image:: images/img-inkannot.*
    :scale: 50

------------------------------

Drawing and Graphics
---------------------

PDF files support elementary drawing operations as part of their syntax. This includes basic geometrical objects like lines, curves, circles, rectangles including specifying colors.

The syntax for such operations is defined in "A Operator Summary" on page 985 of the :ref:`AdobeManual`. Specifying these operators for a PDF page happens in its :data:`contents` objects.

PyMuPDF implements a large part of the available features via its :ref:`Shape` class, which is comparable to notions like "canvas" in other packages (e.g. `reportlab <https://pypi.org/project/reportlab/>`_).

A shape is always created as a **child of a page**, usually with an instruction like *shape = page.new_shape()*. The class defines numerous methods that perform drawing operations on the page's area. For example, *last_point = shape.draw_rect(rect)* draws a rectangle along the borders of a suitably defined *rect = fitz.Rect(...)*.

The returned *last_point* **always** is the :ref:`Point` where drawing operation ended ("last point"). Every such elementary drawing requires a subsequent :meth:`Shape.finish` to "close" it, but there may be multiple drawings which have one common *finish()* method.

In fact, :meth:`Shape.finish` *defines* a group of preceding draw operations to form one -- potentially rather complex -- graphics object. PyMuPDF provides several predefined graphics in `shapes_and_symbols.py <https://github.com/JorjMcKie/PyMuPDF-Utilities/blob/master/shapes_and_symbols.py>`_ which demonstrate how this works.

If you import this script, you can also directly use its graphics as in the following example::

    # -*- coding: utf-8 -*-
    """
    Created on Sun Dec  9 08:34:06 2018

    @author: Jorj
    @license: GNU AFFERO GPL V3

    Create a list of available symbols defined in shapes_and_symbols.py

    This also demonstrates an example usage: how these symbols could be used
    as bullet-point symbols in some text.

    """

    import fitz
    import shapes_and_symbols as sas

    # list of available symbol functions and their descriptions
    tlist = [
             (sas.arrow, "arrow (easy)"),
             (sas.caro, "caro (easy)"),
             (sas.clover, "clover (easy)"),
             (sas.diamond, "diamond (easy)"),
             (sas.dontenter, "do not enter (medium)"),
             (sas.frowney, "frowney (medium)"),
             (sas.hand, "hand (complex)"),
             (sas.heart, "heart (easy)"),
             (sas.pencil, "pencil (very complex)"),
             (sas.smiley, "smiley (easy)"),
             ]

    r = fitz.Rect(50, 50, 100, 100)  # first rect to contain a symbol
    d = fitz.Rect(0, r.height + 10, 0, r.height + 10)  # displacement to next rect
    p = (15, -r.height * 0.2)  # starting point of explanation text
    rlist = [r]  # rectangle list

    for i in range(1, len(tlist)):  # fill in all the rectangles
        rlist.append(rlist[i-1] + d)

    doc = fitz.open()  # create empty PDF
    page = doc.new_page()  # create an empty page
    shape = page.new_shape()  # start a Shape (canvas)

    for i, r in enumerate(rlist):
        tlist[i][0](shape, rlist[i])  # execute symbol creation
        shape.insert_text(rlist[i].br + p,  # insert description text
                       tlist[i][1], fontsize=r.height/1.2)

    # store everything to the page's /Contents object
    shape.commit()

    import os
    scriptdir = os.path.dirname(__file__)
    doc.save(os.path.join(scriptdir, "symbol-list.pdf"))  # save the PDF


This is the script's outcome:

.. image:: images/img-symbols.*
   :scale: 50

------------------------------

Extracting Drawings
---------------------

*(New in v1.18.0)*

The drawing commands issued by a page can be extracted. Interestingly, this is possible for **all supported document types** -- not just PDF: so you can use it for XPS, EPUB and others as well.

A new page method, :meth:`Page.get_drawings()` accesses draw commands and converts them into a list of Python dictionaries. Each dictionary -- called a "path" -- represents a separate drawing -- it may be simple like a single line, or a complex combination of lines and curves representing one of the shapes of the previous section.

The *path* dictionary has been designed such that it can easily be used by the :ref:`Shape` class and its methods.

The following is a code snippet which extracts the drawings of a page and re-draws them on a new page::

    import fitz
    doc = fitz.open("some.file")
    page = doc[0]
    paths = page.get_drawings()  # extract existing drawings
    # this is a list of "paths", which can directly be drawn again using Shape
    # -------------------------------------------------------------------------
    #
    # define some output page with the same dimensions
    outpdf = fitz.open()
    outpage = outpdf.new_page(width=page.rect.width, height=page.rect.height)
    shape = outpage.new_shape()  # make a drawing canvas for the output page
    # --------------------------------------
    # loop through the paths and draw them
    # --------------------------------------
    for path in paths:
        # ------------------------------------
        # draw each entry of the 'items' list
        # ------------------------------------
        for item in path["items"]:  # these are the draw commands
            if item[0] == "l":  # line
                shape.draw_line(item[1], item[2])
            elif item[0] == "re":  # rectangle
                shape.draw_rect(item[1])
            elif item[0] == "c":  # curve
                shape.draw_bezier(item[1], item[2], item[3], item[4])
            else:
                raise ValueError("unhandled drawing", item)
        # ------------------------------------------------------
        # all items are drawn, now apply the common properties
        # to finish the path
        # ------------------------------------------------------
        shape.finish(
            fill=path["fill"],  # fill color
            color=path["color"],  # line color
            dashes=path["dashes"],  # line dashing
            even_odd=path["even_odd"],  # control color of overlaps
            closePath=path["closePath"],  # whether to connect last and first point
            lineJoin=path["lineJoin"],  # how line joins should look like
            lineCap=max(path["lineCap"]),  # how line ends should look like
            width=path["width"],  # line width
            stroke_opacity=path["opacity"],  # same value for both
            fill_opacity=path["opacity"],  # opacity parameters
            )
    # all paths processed - commit the shape to its page
    shape.commit()
    outpdf.save("drawings-page-0.pdf")

As can bee seen, there is a high congruence level with the :ref:`Shape` class. With one exception: For technical reasons ``lineCap`` is a tuple of 3 numbers here, whereas it is an integer in :ref:`Shape` (and in PDF). So we simply take the maximum value of that tuple.

Here is a comparison between input and output of an example page, created by the previous script:

.. image:: images/img-getdrawings.png
   :scale: 50

.. note:: The reconstruction of graphics like shown here is not perfect. The following aspects will not be reproduced as of this version:

   * Page definitions can be complex and include instructions for not showing / hiding certain areas to keep them invisible. Things like this are ignored by :meth:`Page.get_drawings` - it will always return all paths.

.. note:: You can use the path list to make your own lists of e.g. all lines or all rectangles on the page, subselect them by criteria like color or position on the page etc.


------------------------------

Multiprocessing
----------------
MuPDF has no integrated support for threading - they call themselves "threading-agnostic". While there do exist tricky possibilities to still use threading with MuPDF, the baseline consequence for **PyMuPDF** is:

**No Python threading support**.

Using PyMuPDF in a Python threading environment will lead to blocking effects for the main thread.

However, there exists the option to use Python's *multiprocessing* module in a variety of ways.

If you are looking to speed up page-oriented processing for a large document, use this script as a starting point. It should be at least twice as fast as the corresponding sequential processing.

.. literalinclude:: multiprocess-render.py
   :language: python

Here is a more complex example involving inter-process communication between a main process (showing a GUI) and a child process doing PyMuPDF access to a document.

.. literalinclude:: multiprocess-gui.py
   :language: python

------------------------------

General
--------

How to Open with :index:`a Wrong File Extension <pair: wrong; file extension>`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
If you have a document with a wrong file extension for its type, you can still correctly open it.

Assume that "some.file" is actually an XPS. Open it like so:

>>> doc = fitz.open("some.file", filetype = "xps")

.. note:: MuPDF itself does not try to determine the file type from the file contents. **You** are responsible for supplying the filetype info in some way -- either implicitly via the file extension, or explicitly as shown. There are pure Python packages like `filetype <https://pypi.org/project/filetype/>`_ that help you doing this. Also consult the :ref:`Document` chapter for a full description.

----------

How to :index:`Embed or Attach Files <triple: attach;embed;file>`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
PDF supports incorporating arbitrary data. This can be done in one of two ways: "embedding" or "attaching". PyMuPDF supports both options.

1. Attached Files: data are **attached to a page** by way of a *FileAttachment* annotation with this statement: *annot = page.addFileAnnot(pos, ...)*, for details see :meth:`Page.addFileAnnot`. The first parameter "pos" is the :ref:`Point`, where a "PushPin" icon should be placed on the page.

2. Embedded Files: data are embedded on the **document level** via method :meth:`Document.embfile_add`.

The basic differences between these options are **(1)** you need edit permission to embed a file, but only annotation permission to attach, **(2)** like all annotations, attachments are visible on a page, embedded files are not.

There exist several example scripts: `embedded-list.py <https://github.com/pymupdf/PyMuPDF-Utilities/tree/master/examples/embedded-list.py>`_, `new-annots.py <https://github.com/pymupdf/PyMuPDF-Utilities/tree/master/demo/new-annots.py>`_.

Also look at the sections above and at chapter :ref:`Appendix 3`.

----------

.. index::
   pair: delete;pages
   pair: rearrange;pages

How to Delete and Re-Arrange Pages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
With PyMuPDF you have all options to copy, move, delete or re-arrange the pages of a PDF. Intuitive methods exist that allow you to do this on a page-by-page level, like the :meth:`Document.copy_page` method.

Or you alternatively prepare a complete new page layout in form of a Python sequence, that contains the page numbers you want, in the sequence you want, and as many times as you want each page. The following may illustrate what can be done with :meth:`Document.select`:

*doc.select([1, 1, 1, 5, 4, 9, 9, 9, 0, 2, 2, 2])*

Now let's prepare a PDF for double-sided printing (on a printer not directly supporting this):

The number of pages is given by *len(doc)* (equal to *doc.page_count*). The following lists represent the even and the odd page numbers, respectively:

>>> p_even = [p in range(len(doc)) if p % 2 == 0]
>>> p_odd  = [p in range(len(doc)) if p % 2 == 1]

This snippet creates the respective sub documents which can then be used to print the document:

>>> doc.select(p_even)  # only the even pages left over
>>> doc.save("even.pdf")  # save the "even" PDF
>>> doc.close()  # recycle the file
>>> doc = fitz.open(doc.name)  # re-open
>>> doc.select(p_odd)  # and do the same with the odd pages
>>> doc.save("odd.pdf")

For more information also have a look at this Wiki `article <https://github.com/pymupdf/PyMuPDF/wiki/Rearranging-Pages-of-a-PDF>`_.


The following example will reverse the order of all pages (**extremely fast:** sub-second time for the 1310 pages of the :ref:`AdobeManual`):

>>> lastPage = len(doc) - 1
>>> for i in range(lastPage):
        doc.move_page(lastPage, i)  # move current last page to the front

This snippet duplicates the PDF with itself so that it will contain the pages *0, 1, ..., n, 0, 1, ..., n* **(extremely fast and without noticeably increasing the file size!)**:

>>> page_count = len(doc)
>>> for i in range(page_count):
        doc.copy_page(i)  # copy this page to after last page

----------

How to Join PDFs
~~~~~~~~~~~~~~~~~~
It is easy to join PDFs with method :meth:`Document.insert_pdf`. Given open PDF documents, you can copy page ranges from one to the other. You can select the point where the copied pages should be placed, you can revert the page sequence and also change page rotation. This Wiki `article <https://github.com/pymupdf/PyMuPDF/wiki/Inserting-Pages-from-other-PDFs>`_ contains a full description.

The GUI script `PDFjoiner.py <https://github.com/pymupdf/PyMuPDF-Utilities/tree/master/examples/PDFjoiner.py>`_ uses this method to join a list of files while also joining the respective table of contents segments. It looks like this:

.. image:: images/img-pdfjoiner.*
   :scale: 60

----------

How to Add Pages
~~~~~~~~~~~~~~~~~~
There two methods for adding new pages to a PDF: :meth:`Document.insert_page` and :meth:`Document.new_page` (and they share a common code base).

**new_page**

:meth:`Document.new_page` returns the created :ref:`Page` object. Here is the constructor showing defaults::

 >>> doc = fitz.open(...)  # some new or existing PDF document
 >>> page = doc.new_page(to = -1,  # insertion point: end of document
                        width = 595,  # page dimension: A4 portrait
                        height = 842)

The above could also have been achieved with the short form *page = doc.new_page()*. The *to* parameter specifies the document's page number (0-based) **in front of which** to insert.

To create a page in *landscape* format, just exchange the width and height values.

Use this to create the page with another pre-defined paper format:

>>> w, h = fitz.PaperSize("letter-l")  # 'Letter' landscape
>>> page = doc.new_page(width = w, height = h)

The convenience function :meth:`PaperSize` knows over 40 industry standard paper formats to choose from. To see them, inspect dictionary :attr:`paperSizes`. Pass the desired dictionary key to :meth:`PaperSize` to retrieve the paper dimensions. Upper and lower case is supported. If you append "-L" to the format name, the landscape version is returned.

.. note:: Here is a 3-liner that creates a PDF with one empty page. Its file size is 470 bytes:

   >>> doc = fitz.open()
   >>> doc.new_page()
   >>> doc.save("A4.pdf")


**insert_page**

:meth:`Document.insert_page` also inserts a new page and accepts the same parameters *to*, *width* and *height*. But it lets you also insert arbitrary text into the new page and returns the number of inserted lines::

 >>> doc = fitz.open(...)  # some new or existing PDF document
 >>> n = doc.insert_page(to = -1,  # default insertion point
                        text = None,  # string or sequence of strings
                        fontsize = 11,
                        width = 595,
                        height = 842,
                        fontname = "Helvetica",  # default font
                        fontfile = None,  # any font file name
                        color = (0, 0, 0))  # text color (RGB)

The text parameter can be a (sequence of) string (assuming UTF-8 encoding). Insertion will start at :ref:`Point` (50, 72), which is one inch below top of page and 50 points from the left. The number of inserted text lines is returned. See the method definition for more details.

----------

How To Dynamically Clean Up Corrupt PDFs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This shows a potential use of PyMuPDF with another Python PDF library (the excellent pure Python package `pdfrw <https://pypi.python.org/pypi/pdfrw>`_ is used here as an example).

If a clean, non-corrupt / decompressed PDF is needed, one could dynamically invoke PyMuPDF to recover from many problems like so::

 import sys
 from io import BytesIO
 from pdfrw import PdfReader
 import fitz

 #---------------------------------------
 # 'Tolerant' PDF reader
 #---------------------------------------
 def reader(fname, password = None):
     idata = open(fname, "rb").read()  # read the PDF into memory and
     ibuffer = BytesIO(idata)  # convert to stream
     if password is None:
         try:
             return PdfReader(ibuffer)  # if this works: fine!
         except:
             pass

     # either we need a password or it is a problem-PDF
     # create a repaired / decompressed / decrypted version
     doc = fitz.open("pdf", ibuffer)
     if password is not None:  # decrypt if password provided
         rc = doc.authenticate(password)
         if not rc > 0:
             raise ValueError("wrong password")
     c = doc.tobytes(garbage=3, deflate=True)
     del doc  # close & delete doc
     return PdfReader(BytesIO(c))  # let pdfrw retry
 #---------------------------------------
 # Main program
 #---------------------------------------
 pdf = reader("pymupdf.pdf", password = None) # include a password if necessary
 print pdf.Info
 # do further processing

With the command line utility *pdftk* (`available <https://www.pdflabs.com/tools/pdftk-the-pdf-toolkit/>`_ for Windows only, but reported to also run under `Wine <https://www.winehq.org/>`_) a similar result can be achieved, see `here <http://www.overthere.co.uk/2013/07/22/improving-pypdf2-with-pdftk/>`_. However, you must invoke it as a separate process via *subprocess.Popen*, using stdin and stdout as communication vehicles.

How to Split Single Pages
~~~~~~~~~~~~~~~~~~~~~~~~~~

This deals with splitting up pages of a PDF in arbitrary pieces. For example, you may have a PDF with *Letter* format pages which you want to print with a magnification factor of four: each page is split up in 4 pieces which each go to a separate PDF page in *Letter* format again::

    """
    Create a PDF copy with split-up pages (posterize)
    ---------------------------------------------------
    License: GNU AFFERO GPL V3
    (c) 2018 Jorj X. McKie

    Usage
    ------
    python posterize.py input.pdf

    Result
    -------
    A file "poster-input.pdf" with 4 output pages for every input page.

    Notes
    -----
    (1) Output file is chosen to have page dimensions of 1/4 of input.

    (2) Easily adapt the example to make n pages per input, or decide per each
        input page or whatever.

    Dependencies
    ------------
    PyMuPDF 1.12.2 or later
    """
    from __future__ import print_function
    import fitz, sys
    infile = sys.argv[1]  # input file name
    src = fitz.open(infile)
    doc = fitz.open()  # empty output PDF

    for spage in src:  # for each page in input
        r = spage.rect  # input page rectangle
        d = fitz.Rect(spage.cropbox_position,  # CropBox displacement if not
                      spage.cropbox_position)  # starting at (0, 0)
        #--------------------------------------------------------------------------
        # example: cut input page into 2 x 2 parts
        #--------------------------------------------------------------------------
        r1 = r / 2  # top left rect
        r2 = r1 + (r1.width, 0, r1.width, 0)  # top right rect
        r3 = r1 + (0, r1.height, 0, r1.height)  # bottom left rect
        r4 = fitz.Rect(r1.br, r.br)  # bottom right rect
        rect_list = [r1, r2, r3, r4]  # put them in a list

        for rx in rect_list:  # run thru rect list
            rx += d  # add the CropBox displacement
            page = doc.new_page(-1,  # new output page with rx dimensions
                               width = rx.width,
                               height = rx.height)
            page.show_pdf_page(
                    page.rect,  # fill all new page with the image
                    src,  # input document
                    spage.number,  # input page number
                    clip = rx,  # which part to use of input page
                )

    # that's it, save output file
    doc.save("poster-" + src.name,
             garbage=3,  # eliminate duplicate objects
             deflate=True,  # compress stuff where possible
    )


This shows what happens to an input page:

.. image:: images/img-posterize.png

--------------------------

How to Combine Single Pages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This deals with joining PDF pages to form a new PDF with pages each combining two or four original ones (also called "2-up", "4-up", etc.). This could be used to create booklets or thumbnail-like overviews::

    '''
    Copy an input PDF to output combining every 4 pages
    ---------------------------------------------------
    License: GNU AFFERO GPL V3
    (c) 2018 Jorj X. McKie

    Usage
    ------
    python 4up.py input.pdf

    Result
    -------
    A file "4up-input.pdf" with 1 output page for every 4 input pages.

    Notes
    -----
    (1) Output file is chosen to have A4 portrait pages. Input pages are scaled
        maintaining side proportions. Both can be changed, e.g. based on input
        page size. However, note that not all pages need to have the same size, etc.

    (2) Easily adapt the example to combine just 2 pages (like for a booklet) or
        make the output page dimension dependent on input, or whatever.

    Dependencies
    -------------
    PyMuPDF 1.12.1 or later
    '''
    from __future__ import print_function
    import fitz, sys
    infile = sys.argv[1]
    src = fitz.open(infile)
    doc = fitz.open()  # empty output PDF

    width, height = fitz.PaperSize("a4")  # A4 portrait output page format
    r = fitz.Rect(0, 0, width, height)

    # define the 4 rectangles per page
    r1 = r / 2  # top left rect
    r2 = r1 + (r1.width, 0, r1.width, 0)  # top right
    r3 = r1 + (0, r1.height, 0, r1.height)  # bottom left
    r4 = fitz.Rect(r1.br, r.br)  # bottom right

    # put them in a list
    r_tab = [r1, r2, r3, r4]

    # now copy input pages to output
    for spage in src:
        if spage.number % 4 == 0:  # create new output page
            page = doc.new_page(-1,
                          width = width,
                          height = height)
        # insert input page into the correct rectangle
        page.show_pdf_page(r_tab[spage.number % 4],  # select output rect
                         src,  # input document
                         spage.number)  # input page number

    # by all means, save new file using garbage collection and compression
    doc.save("4up-" + infile, garbage=3, deflate=True)

Example effect:

.. image:: images/img-4up.png


--------------------------

How to Convert Any Document to PDF
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here is a script that converts any PyMuPDF supported document to a PDF. These include XPS, EPUB, FB2, CBZ and all image formats, including multi-page TIFF images.

It features maintaining any metadata, table of contents and links contained in the source document::

    from __future__ import print_function
    """
    Demo script: Convert input file to a PDF
    -----------------------------------------
    Intended for multi-page input files like XPS, EPUB etc.

    Features:
    ---------
    Recovery of table of contents and links of input file.
    While this works well for bookmarks (outlines, table of contents),
    links will only work if they are not of type "LINK_NAMED".
    This link type is skipped by the script.

    For XPS and EPUB input, internal links however **are** of type "LINK_NAMED".
    Base library MuPDF does not resolve them to page numbers.

    So, for anyone expert enough to know the internal structure of these
    document types, can further interpret and resolve these link types.

    Dependencies
    --------------
    PyMuPDF v1.14.0+
    """
    import sys
    import fitz
    if not (list(map(int, fitz.VersionBind.split("."))) >= [1,14,0]):
        raise SystemExit("need PyMuPDF v1.14.0+")
    fn = sys.argv[1]

    print("Converting '%s' to '%s.pdf'" % (fn, fn))

    doc = fitz.open(fn)

    b = doc.convert_to_pdf()  # convert to pdf
    pdf = fitz.open("pdf", b)  # open as pdf

    toc= doc.het_toc()  # table of contents of input
    pdf.set_toc(toc)  # simply set it for output
    meta = doc.metadata  # read and set metadata
    if not meta["producer"]:
        meta["producer"] = "PyMuPDF v" + fitz.VersionBind

    if not meta["creator"]:
        meta["creator"] = "PyMuPDF PDF converter"
    meta["modDate"] = fitz.getPDFnow()
    meta["creationDate"] = meta["modDate"]
    pdf.set_metadata(meta)

    # now process the links
    link_cnti = 0
    link_skip = 0
    for pinput in doc:  # iterate through input pages
        links = pinput.get_links()  # get list of links
        link_cnti += len(links)  # count how many
        pout = pdf[pinput.number]  # read corresp. output page
        for l in links:  # iterate though the links
            if l["kind"] == fitz.LINK_NAMED:  # we do not handle named links
                print("named link page", pinput.number, l)
                link_skip += 1  # count them
                continue
            pout.insert_link(l)  # simply output the others

    # save the conversion result
    pdf.save(fn + ".pdf", garbage=4, deflate=True)
    # say how many named links we skipped
    if link_cnti > 0:
        print("Skipped %i named links of a total of %i in input." % (link_skip, link_cnti))

--------------------------

How to Deal with Messages Issued by MuPDF
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Since PyMuPDF v1.16.0, **error messages** issued by the underlying MuPDF library are being redirected to the Python standard device *sys.stderr*. So you can handle them like any other output going to this devices.

In addition, these messages go to the internal buffer together with any MuPDF warnings -- see below.

We always prefix these messages with an identifying string *"mupdf:"*.
If you prefer to not see recoverable MuPDF errors at all, issue the command ``fitz.TOOLS.mupdf_display_errors(False)``.

MuPDF warnings continue to be stored in an internal buffer and can be viewed using :meth:`Tools.mupdf_warnings`.

Please note that MuPDF errors may or may not lead to Python exceptions. In other words, you may see error messages from which MuPDF can recover and continue processing.

Example output for a **recoverable error**. We are opening a damaged PDF, but MuPDF is able to repair it and gives us a few information on what happened. Then we illustrate how to find out whether the document can later be saved incrementally. Checking the :attr:`Document.is_dirty` attribute at this point also indicates that the open had to repair the document:

>>> import fitz
>>> doc = fitz.open("damaged-file.pdf")  # leads to a sys.stderr message:
mupdf: cannot find startxref
>>> print(fitz.TOOLS.mupdf_warnings())  # check if there is more info:
cannot find startxref
trying to repair broken xref
repairing PDF document
object missing 'endobj' token
>>> doc.can_save_incrementally()  # this is to be expected:
False
>>> # the following indicates whether there are updates so far
>>> # this is the case because of the repair actions:
>>> doc.is_dirty
True
>>> # the document has nevertheless been created:
>>> doc
fitz.Document('damaged-file.pdf')
>>> # we now know that any save must occur to a new file

Example output for an **unrecoverable error**:

>>> import fitz
>>> doc = fitz.open("does-not-exist.pdf")
mupdf: cannot open does-not-exist.pdf: No such file or directory
Traceback (most recent call last):
  File "<pyshell#1>", line 1, in <module>
    doc = fitz.open("does-not-exist.pdf")
  File "C:\Users\Jorj\AppData\Local\Programs\Python\Python37\lib\site-packages\fitz\fitz.py", line 2200, in __init__
    _fitz.Document_swiginit(self, _fitz.new_Document(filename, stream, filetype, rect, width, height, fontsize))
RuntimeError: cannot open does-not-exist.pdf: No such file or directory
>>>

--------------------------

How to Deal with PDF Encryption
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Starting with version 1.16.0, PDF decryption and encryption (using passwords) are fully supported. You can do the following:

* Check whether a document is password protected / (still) encrypted (:attr:`Document.needs_pass`, :attr:`Document.is_encrypted`).
* Gain access authorization to a document (:meth:`Document.authenticate`).
* Set encryption details for PDF files using :meth:`Document.save` or :meth:`Document.write` and

    - decrypt or encrypt the content
    - set password(s)
    - set the encryption method
    - set permission details

.. note:: A PDF document may have two different passwords:

   * The **owner password** provides full access rights, including changing passwords, encryption method, or permission detail.
   * The **user password** provides access to document content according to the established permission details. If present, opening the PDF in a viewer will require providing it.

   Method :meth:`Document.authenticate` will automatically establish access rights according to the password used.

The following snippet creates a new PDF and encrypts it with separate user and owner passwords. Permissions are granted to print, copy and annotate, but no changes are allowed to someone authenticating with the user password::

    import fitz

    text = "some secret information"  # keep this data secret
    perm = int(
        fitz.PDF_PERM_ACCESSIBILITY  # always use this
        | fitz.PDF_PERM_PRINT  # permit printing
        | fitz.PDF_PERM_COPY  # permit copying
        | fitz.PDF_PERM_ANNOTATE  # permit annotations
    )
    owner_pass = "owner"  # owner password
    user_pass = "user"  # user password
    encrypt_meth = fitz.PDF_ENCRYPT_AES_256  # strongest algorithm
    doc = fitz.open()  # empty pdf
    page = doc.new_page()  # empty page
    page.insert_text((50, 72), text)  # insert the data
    doc.save(
        "secret.pdf",
        encryption=encrypt_meth,  # set the encryption method
        owner_pw=owner_pass,  # set the owner password
        user_pw=user_pass,  # set the user password
        permissions=perm,  # set permissions
    )

Opening this document with some viewer (Nitro Reader 5) reflects these settings:

.. image:: images/img-encrypting.*
   :scale: 50

**Decrypting** will automatically happen on save as before when no encryption parameters are provided.

To **keep the encryption method** of a PDF save it using *encryption=fitz.PDF_ENCRYPT_KEEP*. If *doc.can_save_incrementally() == True*, an incremental save is also possible.

To **change the encryption method** specify the full range of options above (encryption, owner_pw, user_pw, permissions). An incremental save is **not possible** in this case.


--------------------------

Common Issues and their Solutions
---------------------------------

Changing Annotations: Unexpected Behaviour
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Problem
^^^^^^^^^
There are two scenarios:

1. **Updating** an annotation with PyMuPDF which was created by some other software.
2. **Creating** an annotation with PyMuPDF and later changing it with some other software.

In both cases you may experience unintended changes, like a different annotation icon or text font, the fill color or line dashing have disappeared, line end symbols have changed their size or even have disappeared too, etc.

Cause
^^^^^^
Annotation maintenance is handled differently by each PDF maintenance application. Some annotation types may not be supported, or not be supported fully or some details may be handled in a different way than in another application. **There is no standard.**

Almost always a PDF application also comes with its own icons (file attachments, sticky notes and stamps) and its own set of supported text fonts. For example:

* (Py-) MuPDF only supports these 5 basic fonts for 'FreeText' annotations: Helvetica, Times-Roman, Courier, ZapfDingbats and Symbol -- no italics / no bold variations. When changing a 'FreeText' annotation created by some other app, its font will probably not be recognized nor accepted and be replaced by Helvetica.

* PyMuPDF supports all PDF text markers (highlight, underline, strikeout, squiggly), but these types cannot be updated with Adobe Acrobat Reader.

In most cases there also exists limited support for line dashing which causes existing dashes to be replaced by straight lines. For example:

* PyMuPDF fully supports all line dashing forms, while other viewers only accept a limited subset.


Solutions
^^^^^^^^^^
Unfortunately there is not much you can do in most of these cases.

1. Stay with the same software for **creating and changing** an annotation.
2. When using PyMuPDF to change an "alien" annotation, try to **avoid** :meth:`Annot.update`. The following methods **can be used without it,** so that the original appearance should be maintained:

  * :meth:`Annot.set_rect` (location changes)
  * :meth:`Annot.set_flags` (annotation behaviour)
  * :meth:`Annot.set_info` (meta information, except changes to *content*)
  * :meth:`Annot.set_popup` (create popup or change its rect)
  * :meth:`Annot.set_optional_content` (add / remove reference to optional content information)
  * :meth:`Annot.set_open`
  * :meth:`Annot.update_file` (file attachment changes)

Misplaced Item Insertions on PDF Pages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Problem
^^^^^^^^^

You inserted an item (like an image, an annotation or some text) on an existing PDF page, but later you find it being placed at a different location than intended. For example an image should be inserted at the top, but it unexpectedly appears near the bottom of the page.

Cause
^^^^^^

The creator of the PDF has established a non-standard page geometry without keeping it "local" (as they should!). Most commonly, the PDF standard point (0,0) at *bottom-left* has been changed to the *top-left* point. So top and bottom are reversed -- causing your insertion to be misplaced.

The visible image of a PDF page is controlled by commands coded in a special mini-language. For an overview of this language consult "Operator Summary" on pp. 985 of the :ref:`AdobeManual`. These commands are stored in :data:`contents` objects as strings (*bytes* in PyMuPDF).

There are commands in that language, which change the coordinate system of the page for all the following commands. In order to limit the scope of such commands local, they must be wrapped by the command pair *q* ("save graphics state", or "stack") and *Q* ("restore graphics state", or "unstack").

.. highlight:: text

So the PDF creator did this::

    stream
    1 0 0 -1 0 792 cm    % <=== change of coordinate system:
    ...                  % letter page, top / bottom reversed
    ...                  % remains active beyond these lines
    endstream

where they should have done this::

    stream
    q                    % put the following in a stack
    1 0 0 -1 0 792 cm    % <=== scope of this is limited by Q command
    ...                  % here, a different geometry exists
    Q                    % after this line, geometry of outer scope prevails
    endstream

.. note::

   * In the mini-language's syntax, spaces and line breaks are equally accepted token delimiters.
   * Multiple consecutive delimiters are treated as one.
   * Keywords "stream" and "endstream" are inserted automatically -- not by the programmer.

.. highlight:: python

Solutions
^^^^^^^^^^

Since v1.16.0, there is the property :attr:`Page.is_wrapped`, which lets you check whether a page's contents are wrapped in that string pair.

If it is *False* or if you want to be on the safe side, pick one of the following:

1. The easiest way: in your script, do a :meth:`Page.cleanContents` before you do your first item insertion.
2. Pre-process your PDF with the MuPDF command line utility *mutool clean -c ...* and work with its output file instead.
3. Directly wrap the page's :data:`contents` with the stacking commands before you do your first item insertion.

**Solutions 1. and 2.** use the same technical basis and **do a lot more** than what is required in this context: they also clean up other inconsistencies or redundancies that may exist, multiple */Contents* objects will be concatenated into one, and much more.

.. note:: For **incremental saves,** solution 1. has an unpleasant implication: it will bloat the update delta, because it changes so many things and, in addition, stores the **cleaned contents uncompressed**. So, if you use :meth:`Page.cleanContents` you should consider **saving to a new file** with (at least) *garbage=3* and *deflate=True*.

**Solution 3.** is completely under your control and only does the minimum corrective action. There exists a handy low-level utility function which you can use for this. Suggested procedure:

* **Prepend** the missing stacking command by executing *fitz.TOOLS._insert_contents(page, b"q\n", False)*.
* **Append** an unstacking command by executing *fitz.TOOLS._insert_contents(page, b"\nQ", True)*.
* Alternatively, just use :meth:`Page._wrap_contents`, which executes the previous two functions.

.. note:: If small incremental update deltas are a concern, this approach is the most effective. Other contents objects are not touched. The utility method creates two new PDF :data:`stream` objects and inserts them before, resp. after the page's other :data:`contents`. We therefore recommend the following snippet to get this situation under control:

    >>> if not page.is_wrapped:
            page.wrap_contents()
    >>> # start inserting text, images or annotations here

--------------------------

Low-Level Interfaces
---------------------
Numerous methods are available to access and manipulate PDF files on a fairly low level. Admittedly, a clear distinction between "low level" and "normal" functionality is not always possible or subject to personal taste.

It also may happen, that functionality previously deemed low-level is later on assessed as being part of the normal interface. This has happened in v1.14.0 for the class :ref:`Tools` -- you now find it as an item in the Classes chapter.

Anyway -- it is a matter of documentation only: in which chapter of the documentation do you find what. Everything is available always and always via the same interface.

----------------------------------

How to Iterate through the :data:`xref` Table
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
A PDF's :data:`xref` table is a list of all objects defined in the file. This table may easily contain many thousand entries -- the manual :ref:`AdobeManual` for example has over 330'000 objects. Table entry "0" is reserved and must not be touched.
The following script loops through the :data:`xref` table and prints each object's definition::

    >>> xreflen = doc.xref_length()  # length of objects table
    >>> for xref in range(1, xreflen):  # skip item 0!
            print("")
            print("object %i (stream: %s)" % (xref, doc.is_stream(xref)))
            print(doc.xref_object(i, compressed=False))


.. highlight:: text

This produces the following output::

    object 1 (stream: False)
    <<
        /ModDate (D:20170314122233-04'00')
        /PXCViewerInfo (PDF-XChange Viewer;2.5.312.1;Feb  9 2015;12:00:06;D:20170314122233-04'00')
    >>

    object 2 (stream: False)
    <<
        /Type /Catalog
        /Pages 3 0 R
    >>

    object 3 (stream: False)
    <<
        /Kids [ 4 0 R 5 0 R ]
        /Type /Pages
        /Count 2
    >>

    object 4 (stream: False)
    <<
        /Type /Page
        /Annots [ 6 0 R ]
        /Parent 3 0 R
        /Contents 7 0 R
        /MediaBox [ 0 0 595 842 ]
        /Resources 8 0 R
    >>
    ...
    object 7 (stream: True)
    <<
        /Length 494
        /Filter /FlateDecode
    >>
    ...

.. highlight:: python

A PDF object definition is an ordinary ASCII string.

----------------------------------

How to Handle Object Streams
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Some object types contain additional data apart from their object definition. Examples are images, fonts, embedded files or commands describing the appearance of a page.

Objects of these types are called "stream objects". PyMuPDF allows reading an object's stream via method :meth:`Document.xref_stream` with the object's :data:`xref` as an argument. And it is also possible to write back a modified version of a stream using :meth:`Document.updatefStream`.

Assume that the following snippet wants to read all streams of a PDF for whatever reason::

    >>> xreflen = doc.xref_length() # number of objects in file
    >>> for xref in range(1, xreflen): # skip item 0!
            if stream := doc.xref_stream(xref):
                # do something with it (it is a bytes object or None)
                # e.g. just write it back:
                doc.update_stream(xref, stream)

:meth:`Document.xref_stream` automatically returns a stream decompressed as a bytes object -- and :meth:`Document.update_stream` automatically compresses it if beneficial.

----------------------------------

How to Handle Page Contents
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
A PDF page can have zero or multiple :data:`contents` objects. These are stream objects describing **what** appears **where** on a page (like text and images). They are written in a special mini-language described e.g. in chapter "APPENDIX A - Operator Summary" on page 985 of the :ref:`AdobeManual`.

Every PDF reader application must be able to interpret the contents syntax to reproduce the intended appearance of the page.

If multiple :data:`contents` objects are provided, they must be read and interpreted in the specified sequence in exactly the same way as if these streams were provided as a concatenation of the several.

There are good technical arguments for having multiple :data:`contents` objects:

* It is a lot easier and faster to just add new :data:`contents` objects than maintaining a single big one (which entails reading, decompressing, modifying, recompressing, and rewriting it for each change).
* When working with incremental updates, a modified big :data:`contents` object will bloat the update delta and can thus easily negate the efficiency of incremental saves.

For example, PyMuPDF adds new, small :data:`contents` objects in methods :meth:`Page.insert_image`, :meth:`Page.show_pdf_page` and the :ref:`Shape` methods.

However, there are also situations when a **single** :data:`contents` object is beneficial: it is easier to interpret and better compressible than multiple smaller ones.

Here are two ways of combining multiple contents of a page::

    >>> # method 1: use the clean function
    >>> for page in doc:
            page.clean_contents()  # cleans and combines multiple Contents
            xref = page.get_contents()[0]  # only one /Contents now!
            cont = doc.xref_stream(xref)
            # do something with the cleaned, combined contents

    >>> # method 2: concatenate multiple contents yourself
    >>> for page in doc:
            cont = b""              # initialize contents
            for xref in page.get_contents(): # loop through content xrefs
                cont += doc.xref_stream(xref)
            # do something with the combined contents

The clean function :meth:`Page.clean_contents` does a lot more than just glueing :data:`contents` objects: it also corrects and optimizes the PDF operator syntax of the page and removes any inconsistencies with the page's object definition.

----------------------------------

How to Access the PDF Catalog
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
This is a central ("root") object of a PDF. It serves as a starting point to reach important other objects and it also contains some global options for the PDF::

    >>> import fitz
    >>> doc=fitz.open("PyMuPDF.pdf")
    >>> cat = doc.pdf_catalog()  # get xref of the /Catalog
    >>> print(doc.xref_object(cat))  # print object definition
    <<
        /Type/Catalog                 % object type
        /Pages 3593 0 R               % points to page tree
        /OpenAction 225 0 R           % action to perform on open
        /Names 3832 0 R               % points to global names tree
        /PageMode /UseOutlines        % initially show the TOC
        /PageLabels<</Nums[0<</S/D>>2<</S/r>>8<</S/D>>]>> % labels given to pages
        /Outlines 3835 0 R            % points to outline tree
    >>

.. note:: Indentation, line breaks and comments are inserted here for clarification purposes only and will not normally appear. For more information on the PDF catalog see section 3.6.1 on page 137 of the :ref:`AdobeManual`.

----------------------------------

How to Access the PDF File Trailer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The trailer of a PDF file is a :data:`dictionary` located towards the end of the file. It contains special objects, and pointers to important other information. See :ref:`AdobeManual` p. 96. Here is an overview:

======= =========== ===================================================================================
**Key** **Type**    **Value**
======= =========== ===================================================================================
Size    int         Number of entries in the cross-reference table + 1.
Prev    int         Offset to previous :data:`xref` section (indicates incremental updates).
Root    dictionary  (indirect) Pointer to the catalog. See previous section.
Encrypt dictionary  Pointer to encryption object (encrypted files only).
Info    dictionary  (indirect) Pointer to information (metadata).
ID      array       File identifier consisting of two byte strings.
XRefStm int         Offset of a cross-reference stream. See :ref:`AdobeManual` p. 109.
======= =========== ===================================================================================

Access this information via PyMuPDF with :meth:`Document.pdf_trailer`.

    >>> import fitz
    >>> doc=fitz.open("PyMuPDF.pdf")
    >>> print(doc.pdf_trailer())
    <<
    /Type /XRef
    /Index [ 0 8263 ]
    /Size 8263
    /W [ 1 3 1 ]
    /Root 8260 0 R
    /Info 8261 0 R
    /ID [ <4339B9CEE46C2CD28A79EBDDD67CC9B3> <4339B9CEE46C2CD28A79EBDDD67CC9B3> ]
    /Length 19883
    /Filter /FlateDecode
    >>
    >>> 

----------------------------------

How to Access XML Metadata
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
A PDF may contain XML metadata in addition to the standard metadata format. In fact, most PDF viewer or modification software adds this type of information when saving the PDF (Adobe, Nitro PDF, PDF-XChange, etc.).

PyMuPDF has no way to **interpret or change** this information directly, because it contains no XML features. XML metadata is however stored as a :data:`stream` object, so it can be read, modified with appropriate software and written back.

    >>> xmlmetadata = doc.get_xml_metadata()
    >>> print(xmlmetadata)
    <?xpacket begin="\ufeff" id="W5M0MpCehiHzreSzNTczkc9d"?>
    <x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="3.1-702">
    <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    ...
    omitted data
    ...
    <?xpacket end="w"?>

Using some XML package, the XML data can be interpreted and / or modified and then stored back. The following also works, if the PDF previously had no XML metadata::

    >>> # write back modified XML metadata:
    >>> doc.set_xml_metadata(xmlmetadata)
    >>>
    >>> # XML metadata can be deleted like this:
    >>> doc.del_xml_metadata()

----------------------------------

How to Read and Update PDF Objects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. highlight:: python


There also exist granular, elegant ways to access and manipulate selected PDF :data:`dictionary` keys.

* :meth:`Document.xref_get_keys` returns the PDF keys of the object at :data:`xref`::

    In [1]: import fitz
    In [2]: doc = fitz.open("pymupdf.pdf")
    In [3]: page = doc[0]
    In [4]: from pprint import pprint
    In [5]: pprint(doc.xref_get_keys(page.xref))
    ('Type', 'Contents', 'Resources', 'MediaBox', 'Parent')

* Compare with the full object definition::

    In [6]: print(doc.xref_object(page.xref))
    <<
      /Type /Page
      /Contents 1297 0 R
      /Resources 1296 0 R
      /MediaBox [ 0 0 612 792 ]
      /Parent 1301 0 R
    >>

* Single keys can also be accessed directly via :meth:`Document.xref_get_key`. The value **always is a string** together with type information, that helps interpreting it::

    In [7]: doc.xref_get_key(page.xref, "MediaBox")
    Out[7]: ('array', '[0 0 612 792]')

* Here is a full listing of the above page keys::

    In [9]: for key in doc.xref_get_keys(page.xref):
    ...:        print("%s = %s" % (key, doc.xref_get_key(page.xref, key)))
    ...:
    Type = ('name', '/Page')
    Contents = ('xref', '1297 0 R')
    Resources = ('xref', '1296 0 R')
    MediaBox = ('array', '[0 0 612 792]')
    Parent = ('xref', '1301 0 R')

* An undefined key inquiry returns ``('null', 'null')`` -- PDF object type ``null`` corresponds to ``None`` in Python. Similar for the booleans ``true`` and ``false``.
* Let us add a new key to the page definition that sets its rotation to 90 degrees (you are aware that there actually exists :meth:`Page.set_rotation` for this?)::

    In [11]: doc.xref_get_key(page.xref, "Rotate")  # no rotation set:
    Out[11]: ('null', 'null')
    In [12]: doc.xref_set_key(page.xref, "Rotate", "90")  # insert a new key
    In [13]: print(doc.xref_object(page.xref))  # confirm success
    <<
      /Type /Page
      /Contents 1297 0 R
      /Resources 1296 0 R
      /MediaBox [ 0 0 612 792 ]
      /Parent 1301 0 R
      /Rotate 90
    >>

* This method can also be used to remove a key from the :data:`xref` dictionary by setting its value to ``null``: The following will remove the rotation specification from the page: ``doc.xref_set_key(page.xref, "Rotate", "null")``. Similarly, to remove all links, annotations and fields from a page, use ``doc.xref_set_key(page.xref, "Annots", "null")``. Because ``Annots`` by definition is an array, setting en empty array with the statement ``doc.xref_set_key(page.xref, "Annots", "[]")`` would do the same job in this case.

* PDF dictionaries can be hierarchically nested. In the following page object definition both, ``Font`` and ``XObject`` are subdictionaries of ``Resources``::

    In [15]: print(doc.xref_object(page.xref))
    <<
      /Type /Page
      /Contents 1297 0 R
      /Resources <<
        /XObject <<
          /Im1 1291 0 R
        >>
        /Font <<
          /F39 1299 0 R
          /F40 1300 0 R
        >>
      >>
      /MediaBox [ 0 0 612 792 ]
      /Parent 1301 0 R
      /Rotate 90
    >>

* The above situation **is supported** by methods :meth:`Document.xref_set_key` and :meth:`Document.xref_get_key`: use a path-like notation to point at the required key. For example, to retrieve the value of key ``Im1`` above, specify the complete chain of dictionaries "above" it in the key argument: ``"Resources/XObject/Im1"``::

    In [16]: doc.xref_get_key(page.xref, "Resources/XObject/Im1")
    Out[16]: ('xref', '1291 0 R')

* The path notation can also be used to **directly set a value**: use the following to let ``Im1`` point to a different object::

    In [17]: doc.xref_set_key(page.xref, "Resources/XObject/Im1", "9999 0 R")
    In [18]: print(doc.xref_object(page.xref))  # confirm success:
    <<
      /Type /Page
      /Contents 1297 0 R
      /Resources <<
        /XObject <<
          /Im1 9999 0 R
        >>
        /Font <<
          /F39 1299 0 R
          /F40 1300 0 R
        >>
      >>
      /MediaBox [ 0 0 612 792 ]
      /Parent 1301 0 R
      /Rotate 90
    >>

  Be aware, that **no semantic checks** whatsoever will take place here: if the PDF has no xref 9999, it won't be detected at this point.

* If a key does not exist, it will be created by setting its value. Moreover, if any intermediate keys do not exist either, they will also be created as necessary. The following creates an array ``D`` several levels below the existing dictionary ``A``. Intermediate dictionaries ``B`` and ``C`` are automatically created::

    In [5]: print(doc.xref_object(xref))  # some existing PDF object:
    <<
      /A <<
      >>
    >>
    In [6]: # the following will create 'B', 'C' and 'D'
    In [7]: doc.xref_set_key(xref, "A/B/C/D", "[1 2 3 4]")
    In [8]: print(doc.xref_object(xref))  # check out what happened:
    <<
      /A <<
        /B <<
          /C <<
            /D [ 1 2 3 4 ]
          >>
        >>
      >>
    >>

* When setting key values, basic **PDF syntax checking** will be done by MuPDF. For example, new keys can only be created **below a dictionary**. The following tries to create some new string item ``E`` below the previously created array ``D``::

    In [9]: # 'D' is an array, no dictionary!
    In [10]: doc.xref_set_key(xref, "A/B/C/D/E", "(hello)")
    mupdf: not a dict (array)
    --- ... ---
    RuntimeError: not a dict (array)

* It is also **not possible**, to create a key if some higher level key is an **"indirect"** object, i.e. an xref. In other words, xrefs can only be modified directly and not implicitely via other objects referencing them::

    In [13]: # the following object points to an xref
    In [14]: print(doc.xref_object(4))
    <<
      /E 3 0 R
    >>
    In [15]: # 'E' is an indirect object and cannot be modified here!
    In [16]: doc.xref_set_key(4, "E/F", "90")
    mupdf: path to 'F' has indirects
    --- ... ---
    RuntimeError: path to 'F' has indirects

.. caution:: These are expert functions! There are no validations as to whether valid PDF objects, xrefs, etc. are specified. As with other low-level methods there exists the risk to render the PDF, or parts of it unusable.
