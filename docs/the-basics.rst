.. include:: header.rst

.. _TheBasics:


==============================
The Basics
==============================

.. _Supported_File_Types:

Supported File Types
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:title:`PyMuPDF` supports the following file types:

.. raw:: html

    <style>

        table {
            border-style: hidden;
        }

        #feature-matrix th {
            border: 1px #999 solid;
            padding: 10px;
            background-color: #007aff;
            color: white;
        }

        #feature-matrix tr {

        }

        #feature-matrix td {
            border: 1px #999 solid;
            padding: 10px;
        }

        #feature-matrix tr td.yes {
            background-color: #83e57c !important;
            color: #000;
        }

        #feature-matrix tr td.yes::before {
            content: "✔︎ ";
        }

        #feature-matrix tr td.no {
            background-color: #e5887c !important;
            color: #000;
        }

        #feature-matrix tr td.no::before {
            content: "✕ ";
        }

        #feature-matrix tr td.limited {
            background-color: #e4c07b !important;
            color: #000;
        }

        #feature-matrix .icon-holder {
            line-height: 40px;
        }

        #feature-matrix .icon {
            text-indent: 45px;
            line-height: 40px;
            width: 100px;
            height: 40px;
        }

        #feature-matrix .icon.pdf {
            background: url("_images/icon-pdf.svg") 0 0 transparent no-repeat;
            background-size: 40px 40px;
        }

        #feature-matrix .icon.xps {
            background: url("_images/icon-xps.svg") 0 0 transparent no-repeat;
            background-size: 40px 40px;
        }

        #feature-matrix .icon.epub {
            background: url("_images/icon-epub.svg") 0 0 transparent no-repeat;
            background-size: 40px 40px;
        }

        #feature-matrix .icon.mobi {
            background: url("_images/icon-mobi.svg") 0 0 transparent no-repeat;
            background-size: 40px 40px;
        }

        #feature-matrix .icon.fb2 {
            background: url("_images/icon-fb2.svg") 0 0 transparent no-repeat;
            background-size: 40px 40px;
        }

        #feature-matrix .icon.cbz {
            background: url("_images/icon-cbz.svg") 0 0 transparent no-repeat;
            background-size: 40px 40px;
        }

        #feature-matrix .icon.svg {
            background: url("_images/icon-svg.svg") 0 0 transparent no-repeat;
            background-size: 40px 40px;
        }

        #feature-matrix .icon.image {
            background: url("_images/icon-image.svg") 0 0 transparent no-repeat;
            background-size: 40px 40px;
        }

    </style>



    <table id="feature-matrix" border="0" cellpadding="0" cellspacing="0">
        <tr>
            <th style="width:20%;"></th>
            <th style="width:20%;"><div id="trans1"></div></th>
        </tr>

        <tr>
            <td><cite><div id="trans2"></div></cite></td>
            <td>
                <span class="icon pdf"><cite>PDF</cite></span>
                <span class="icon xps"><cite>XPS</cite></span>
                <span class="icon epub"><cite>EPUB</cite></span>
                <span class="icon mobi"><cite>MOBI</cite></span>
                <span class="icon fb2"><cite>FB2</cite></span>
                <span class="icon cbz"><cite>CBZ</cite></span>
                <span class="icon svg"><cite>SVG</cite></span>
            </td>
        </tr>

        <tr>
            <td><cite><div id="trans3"></div></cite></td>
            <td>
                <span class="icon image"></span>
                <div><u><div id="trans4"></div></u> <cite>JPG/JPEG, PNG, BMP, GIF, TIFF, PNM, PGM, PBM, PPM, PAM, JXR, JPX/JP2, PSD</cite></div>
                <div><u><div id="trans5"></div></u> <cite>JPG/JPEG, PNG, PNM, PGM, PBM, PPM, PAM, PSD, PS</cite></div>
            </td>
        </tr>

    </table>

    <script>

        let lang = document.getElementsByTagName('html')[0].getAttribute('lang');

        function getTranslation(str) {
            if (lang == "ja") {
                if (str=="File type") {
                    return "ファイルタイプ";
                } else if (str=="Document Formats") {
                    return "文書のフォーマット";
                } else if (str=="Image Formats") {
                    return "画像のフォーマット";
                } else if (str=="Input formats") {
                    return "入力フォーマット";
                } else if (str=="Output formats") {
                    return "出力フォーマット";
                }

            }

            return str;
        }

        document.getElementById("trans1").innerHTML = getTranslation("File type");
        document.getElementById("trans2").innerHTML = getTranslation("Document Formats");
        document.getElementById("trans3").innerHTML = getTranslation("Image Formats");
        document.getElementById("trans4").innerHTML = getTranslation("Input formats");
        document.getElementById("trans5").innerHTML = getTranslation("Output formats");

    </script>


.. _The_Basics_Opening_Files:

Opening a File
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


To open a file, do the following:

.. raw:: html

    <pre>
        <code class="language-python" data-prismjs-copy="Copy">
            import fitz

            doc = fitz.open("a.pdf") # open a document
        </code>
    </pre>


Opening with :index:`a Wrong File Extension <pair: wrong; file extension>`
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

If you have a document with a wrong file extension for its type, you can still correctly open it.

Assume that *"some.file"* is actually an XPS. Open it like so:

.. raw:: html

    <pre>
        <code class="language-python" data-prismjs-copy="Copy">
            import fitz

            doc = fitz.open("some.file", filetype="xps")
        </code>
    </pre>



.. note::

    **Taking it further**

    There are many file types beyond :title:`PDF` which can be opened by :title:`PyMuPDF`, for more details see the list of :ref:`supported file types<Supported_File_Types>`.

    :title:`PyMuPDF` itself does not try to determine the file type from the file contents. **You** are responsible for supplying the filetype info in some way -- either implicitly via the file extension, or explicitly as shown. There are pure :title:`Python` packages like `filetype <https://pypi.org/project/filetype/>`_ that help you doing this. Also consult the :ref:`Document` chapter for a full description.

    If :title:`PyMuPDF` encounters a file with an unknown / missing extension, it will try to open it as a :title:`PDF`. So in these cases there is no need for additional precautions. Similarly, for memory documents, you can just specify `doc=fitz.open(stream=mem_area)` to open it as a :title:`PDF` document.

    If you attempt to open an unsupported file then :title:`PyMuPDF` will throw a file data error.

----------


.. _The_Basics_Extracting_Text:

Extract text from a :title:`PDF`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To extract all the text from a :title:`PDF` file, do the following:

.. raw:: html

    <pre>
        <code class="language-python" data-prismjs-copy="Copy">
            import fitz

            doc = fitz.open("a.pdf") # open a document
            out = open("output.txt", "wb") # create a text output
            for page in doc: # iterate the document pages
                text = page.get_text().encode("utf8") # get plain text (is in UTF-8)
                out.write(text) # write text of page
                out.write(bytes((12,))) # write page delimiter (form feed 0x0C)
            out.close()
        </code>
    </pre>

.. note::

    **Taking it further**

    There are many more examples which explain how to extract text from specific areas or how to extract tables from documents. Please refer to the :ref:`How to Guide for Text<RecipesText>`.

    **API reference**

    - :meth:`Page.get_text`

----------


.. _The_Basics_Extracting_Images:

Extract images from a :title:`PDF`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To extract all the images from a :title:`PDF` file, do the following:

.. raw:: html

    <pre>
        <code class="language-python" data-prismjs-copy="Copy">
            import fitz

            doc = fitz.open("test.pdf") # open a document

            for page_index in range(len(doc)): # iterate over pdf pages
                page = doc[page_index] # get the page
                image_list = page.get_images()

                # print the number of images found on the page
                if image_list:
                    print(f"Found {len(image_list)} images on page {page_index}")
                else:
                    print("No images found on page", page_index)

                for image_index, img in enumerate(image_list, start=1): # enumerate the image list
                    xref = img[0] # get the XREF of the image
                    pix = fitz.Pixmap(doc, xref) # create a Pixmap

                    if pix.n - pix.alpha > 3: # CMYK: convert to RGB first
                        pix = fitz.Pixmap(fitz.csRGB, pix)

                    pix.save("page_%s-image_%s.png" % (page_index, image_index)) # save the image as png
                    pix = None
        </code>
    </pre>


.. note::

    **Taking it further**

    There are many more examples which explain how to extract text from specific areas or how to extract tables from documents. Please refer to the :ref:`How to Guide for Text<RecipesText>`.

    **API reference**

    - :meth:`Page.get_images`
    - :ref:`Pixmap<Pixmap>`


----------

.. _The_Basics_Merging_PDF:
.. _merge PDF:
.. _join PDF:

Merging :title:`PDF` files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To merge :title:`PDF` files, do the following:

.. raw:: html

    <pre>
        <code class="language-python" data-prismjs-copy="Copy">
            import fitz

            doc_a = fitz.open("a.pdf") # open the 1st document
            doc_b = fitz.open("b.pdf") # open the 2nd document

            doc_a.insert_pdf(doc_b) # merge the docs
            doc_a.save("a+b.pdf") # save the merged document with a new filename
        </code>
    </pre>


Merging :title:`PDF` files with other types of file
"""""""""""""""""""""""""""""""""""""""""""""""""""""

With :meth:`Document.insert_file` you can invoke the method to merge :ref:`supported files<Supported_File_Types>` with :title:`PDF`. For example:

.. raw:: html

    <pre>
        <code class="language-python" data-prismjs-copy="Copy">
            import fitz

            doc_a = fitz.open("a.pdf") # open the 1st document
            doc_b = fitz.open("b.svg") # open the 2nd document

            doc_a.insert_file(doc_b) # merge the docs
            doc_a.save("a+b.pdf") # save the merged document with a new filename
        </code>
    </pre>



.. note::

    **Taking it further**

    It is easy to join PDFs with :meth:`Document.insert_pdf` & :meth:`Document.insert_file`. Given open :title:`PDF` documents, you can copy page ranges from one to the other. You can select the point where the copied pages should be placed, you can revert the page sequence and also change page rotation. This Wiki `article <https://github.com/pymupdf/PyMuPDF/wiki/Inserting-Pages-from-other-PDFs>`_ contains a full description.

    The GUI script `join.py <https://github.com/pymupdf/PyMuPDF-Utilities/blob/master/examples/join-documents/join.py>`_ uses this method to join a list of files while also joining the respective table of contents segments. It looks like this:

    .. image:: images/img-pdfjoiner.*
       :scale: 60

    **API reference**

    - :meth:`Document.insert_pdf`
    - :meth:`Document.insert_file`


----------


.. _The_Basics_Watermarks:

Adding a watermark to a :title:`PDF`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To add a watermark to a :title:`PDF` file, do the following:

.. raw:: html

    <pre>
        <code class="language-python" data-prismjs-copy="Copy">
            import fitz

            doc = fitz.open("document.pdf") # open a document

            for page_index in range(len(doc)): # iterate over pdf pages
                page = doc[page_index] # get the page

                # insert an image watermark from a file name to fit the page bounds
                page.insert_image(page.bound(),filename="watermark.png", overlay=False)

            doc.save("watermarked-document.pdf") # save the document with a new filename
        </code>
    </pre>

.. note::

    **Taking it further**

    Adding watermarks is essentially as simple as adding an image at the base of each :title:`PDF` page. You should ensure that the image has the required opacity and aspect ratio to make it look the way you need it to.

    In the example above a new image is created from each file reference, but to be more performant (by saving memory and file size) this image data should be referenced only once - see the code example and explanation on :meth:`Page.insert_image` for the implementation.

    **API reference**

    - :meth:`Page.bound`
    - :meth:`Page.insert_image`


----------


.. _The_Basics_Images:

Adding an image to a :title:`PDF`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To add an image to a :title:`PDF` file, for example a logo, do the following:

.. raw:: html

    <pre>
        <code class="language-python" data-prismjs-copy="Copy">
            import fitz

            doc = fitz.open("document.pdf") # open a document

            for page_index in range(len(doc)): # iterate over pdf pages
                page = doc[page_index] # get the page

                # insert an image logo from a file name at the top left of the document
                page.insert_image(fitz.Rect(0,0,50,50),filename="my-logo.png")

            doc.save("logo-document.pdf") # save the document with a new filename
        </code>
    </pre>

.. note::

    **Taking it further**

    As with the watermark example you should ensure to be more performant by only referencing the image once if possible - see the code example and explanation on :meth:`Page.insert_image`.

    **API reference**

    - :ref:`Rect<Rect>`
    - :meth:`Page.insert_image`


----------


.. _The_Basics_Rotating:

Rotating a :title:`PDF`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To add a rotation to a page, do the following:

.. raw:: html

    <pre>
        <code class="language-python" data-prismjs-copy="Copy">
            import fitz

            doc = fitz.open("test.pdf") # open document
            page = doc[0] # get the 1st page of the document
            page.set_rotation(90) # rotate the page
            doc.save("rotated-page-1.pdf")
        </code>
    </pre>


.. note::

    **API reference**

    - :meth:`Page.set_rotation`


----------

.. _The_Basics_Cropping:

Cropping a :title:`PDF`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To crop a page to a defined :ref:`Rect<Rect>`, do the following:

.. raw:: html

    <pre>
        <code class="language-python" data-prismjs-copy="Copy">
            import fitz

            doc = fitz.open("test.pdf") # open document
            page = doc[0] # get the 1st page of the document
            page.set_cropbox(fitz.Rect(100, 100, 400, 400)) # set a cropbox for the page
            doc.save("cropped-page-1.pdf")
        </code>
    </pre>


.. note::

    **API reference**

    - :meth:`Page.set_cropbox`


----------


.. _The_Basics_Attaching_Files:

:index:`Attaching Files <triple: attach;embed;file>`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To attach another file to a page, do the following:

.. raw:: html

  <pre>
    <code class="language-python" data-prismjs-copy="Copy">
        import fitz

        doc = fitz.open("test.pdf") # open main document
        attachment = fitz.open("my-attachment.pdf") # open document you want to attach

        page = doc[0] # get the 1st page of the document
        point = fitz.Point(100, 100) # create the point where you want to add the attachment
        attachment_data = attachment.tobytes() # get the document byte data as a buffer

        # add the file annotation with the point, data and the file name
        file_annotation = page.add_file_annot(point, attachment_data, "attachment.pdf")

        doc.save("document-with-attachment.pdf") # save the document
    </code>
  </pre>

.. note::

    **Taking it further**

    When adding the file with :meth:`Page.add_file_annot` note that the third parameter for the `filename` should include the actual file extension. Without this the attachment possibly will not be able to be recognized as being something which can be opened. For example, if the `filename` is just *"attachment"* when view the resulting PDF and attempting to open the attachment you may well get an error. However, with *"attachment.pdf"* this can be recognized and opened by PDF viewers as a valid file type.

    The default icon for the attachment is by default a "push pin", however you can change this by setting the `icon` parameter.

    **API reference**

    - :ref:`Point<Point>`
    - :meth:`Document.tobytes`
    - :meth:`Page.add_file_annot`


----------


.. _The_Basics_Embedding_Files:

:index:`Embedding Files <triple: attach;embed;file>`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To embed a file to a document, do the following:

.. raw:: html

  <pre>
    <code class="language-python" data-prismjs-copy="Copy">
        import fitz

        doc = fitz.open("test.pdf") # open main document
        embedded_doc = fitz.open("my-embed.pdf") # open document you want to embed

        embedded_data = embedded_doc.tobytes() # get the document byte data as a buffer

        # embed with the file name and the data
        doc.embfile_add("my-embedded_file.pdf", embedded_data)

        doc.save("document-with-embed.pdf") # save the document
    </code>
  </pre>




.. note::

    **Taking it further**

    As with :ref:`attaching files<The_Basics_Attaching_Files>`, when adding the file with :meth:`Document.embfile_add` note that the first parameter for the `filename` should include the actual file extension.

    **API reference**

    - :meth:`Document.tobytes`
    - :meth:`Document.embfile_add`


----------



.. _The_Basics_Deleting_Pages:

Deleting Pages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To delete a page from a document, do the following:

.. raw:: html

  <pre>
    <code class="language-python" data-prismjs-copy="Copy">
        import fitz

        doc = fitz.open("test.pdf") # open a document
        doc.delete_page(0) # delete the 1st page of the document
        doc.save("test-deleted-page-one.pdf") # save the document

    </code>
  </pre>


To delete a multiple pages from a document, do the following:

.. raw:: html

  <pre>
    <code class="language-python" data-prismjs-copy="Copy">
        import fitz

        doc = fitz.open("test.pdf") # open a document
        doc.delete_pages(from_page=9, to_page=14) # delete a page range from the document
        doc.save("test-deleted-pages.pdf") # save the document

    </code>
  </pre>


.. note::

    **Taking it further**

    The page index is zero-based, so to delete page 10 of a document you would do the following `doc.delete_page(9)`.

    Similarly, `doc.delete_pages(from_page=9, to_page=14)` will delete pages 10 - 15 inclusive.


    **API reference**

    - :meth:`Document.delete_page`
    - :meth:`Document.delete_pages`

----------


.. _The_Basics_Rearrange_Pages:

Re-Arranging Pages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To re-arrange pages, do the following:

.. raw:: html

  <pre>
    <code class="language-python" data-prismjs-copy="Copy">
        import fitz

        doc = fitz.open("test.pdf") # open a document
        doc.move_page(1,0) # move the 2nd page of the document to the start of the document
        doc.save("test-page-moved.pdf") # save the document
    </code>
  </pre>

.. note::

    **API reference**

    - :meth:`Document.move_page`

----------



.. _The_Basics_Copying_Pages:

Copying Pages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


To copy pages, do the following:


.. raw:: html

  <pre>
    <code class="language-python" data-prismjs-copy="Copy">
        import fitz

        doc = fitz.open("test.pdf") # open a document
        doc.copy_page(0) # copy the 1st page and puts it at the end of the document
        doc.save("test-page-copied.pdf") # save the document
    </code>
  </pre>

.. note::

    **API reference**

    - :meth:`Document.copy_page`


----------

.. _The_Basics_Selecting_Pages:

Selecting Pages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


To select pages, do the following:

.. raw:: html

  <pre>
    <code class="language-python" data-prismjs-copy="Copy">
        import fitz

        doc = fitz.open("test.pdf") # open a document
        doc.select([0, 1]) # select the 1st & 2nd page of the document
        doc.save("just-page-one-and-two.pdf") # save the document
    </code>
  </pre>

.. note::

    **Taking it further**

    With :title:`PyMuPDF` you have all options to copy, move, delete or re-arrange the pages of a :title:`PDF`. Intuitive methods exist that allow you to do this on a page-by-page level, like the :meth:`Document.copy_page` method.

    Or you alternatively prepare a complete new page layout in form of a :title:`Python` sequence, that contains the page numbers you want, in the sequence you want, and as many times as you want each page. The following may illustrate what can be done with :meth:`Document.select`

    .. raw:: html

      <pre>
        <code class="language-python" data-prismjs-copy="Copy">
            doc.select([1, 1, 1, 5, 4, 9, 9, 9, 0, 2, 2, 2])
        </code>
      </pre>


    Now let's prepare a PDF for double-sided printing (on a printer not directly supporting this):

    The number of pages is given by `len(doc)` (equal to `doc.page_count`). The following lists represent the even and the odd page numbers, respectively:

    .. raw:: html

      <pre>
        <code class="language-python" data-prismjs-copy="Copy">
            p_even = [p in range(doc.page_count) if p % 2 == 0]
            p_odd  = [p in range(doc.page_count) if p % 2 == 1]
        </code>
      </pre>


    This snippet creates the respective sub documents which can then be used to print the document:

    .. raw:: html

      <pre>
        <code class="language-python" data-prismjs-copy="Copy">
            doc.select(p_even) # only the even pages left over
            doc.save("even.pdf") # save the "even" PDF
            doc.close() # recycle the file
            doc = fitz.open(doc.name) # re-open
            doc.select(p_odd) # and do the same with the odd pages
            doc.save("odd.pdf")
        </code>
      </pre>

    For more information also have a look at this Wiki `article <https://github.com/pymupdf/PyMuPDF/wiki/Rearranging-Pages-of-a-PDF>`_.


    The following example will reverse the order of all pages (**extremely fast:** sub-second time for the 756 pages of the :ref:`AdobeManual`):

    .. raw:: html

      <pre>
        <code class="language-python" data-prismjs-copy="Copy">
            lastPage = doc.page_count - 1
            for i in range(lastPage):
                doc.move_page(lastPage, i) # move current last page to the front
        </code>
      </pre>


    This snippet duplicates the PDF with itself so that it will contain the pages *0, 1, ..., n, 0, 1, ..., n* **(extremely fast and without noticeably increasing the file size!)**:

    .. raw:: html

      <pre>
        <code class="language-python" data-prismjs-copy="Copy">
            page_count = len(doc)
            for i in range(page_count):
                doc.copy_page(i) # copy this page to after last page
        </code>
      </pre>


    **API reference**

    - :meth:`Document.select`

----------


.. _The_Basics_Adding_Blank_Pages:




Adding Blank Pages
~~~~~~~~~~~~~~~~~~~~~

To add a blank page, do the following:

.. raw:: html

  <pre>
    <code class="language-python" data-prismjs-copy="Copy">
        import fitz

        doc = fitz.open(...) # some new or existing PDF document
        page = doc.new_page(-1, # insertion point: end of document
                            width = 595, # page dimension: A4 portrait
                            height = 842)
        doc.save("doc-with-new-blank-page.pdf") # save the document
    </code>
  </pre>

.. note::

    **Taking it further**

    Use this to create the page with another pre-defined paper format:

    .. raw:: html
        <pre>
            <code class="language-python" data-prismjs-copy="Copy">
                w, h = fitz.paper_size("letter-l")  # 'Letter' landscape
                page = doc.new_page(width = w, height = h)
            </code>
        </pre>

    The convenience function :meth:`paper_size` knows over 40 industry standard paper formats to choose from. To see them, inspect dictionary :attr:`paperSizes`. Pass the desired dictionary key to :meth:`paper_size` to retrieve the paper dimensions. Upper and lower case is supported. If you append "-L" to the format name, the landscape version is returned.

    Here is a 3-liner that creates a :title:`PDF`: with one empty page. Its file size is 460 bytes:

    .. raw:: html
        <pre>
            <code class="language-python" data-prismjs-copy="Copy">
                doc = fitz.open()
                doc.new_page()
                doc.save("A4.pdf")
            </code>
        </pre>


    **API reference**

    - :meth:`Document.new_page`
    - :attr:`paperSizes`


----------


.. _The_Basics_Inserting_Pages:

Inserting Pages with Text Content
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Using the :meth:`Document.insert_page` method also inserts a new page and accepts the same `width` and `height` parameters. But it lets you also insert arbitrary text into the new page and returns the number of inserted lines.

.. raw:: html

  <pre>
    <code class="language-python" data-prismjs-copy="Copy">
        import fitz

        doc = fitz.open(...)  # some new or existing PDF document
        n = doc.insert_page(-1, # default insertion point
                            text = "The quick brown fox jumped over the lazy dog",
                            fontsize = 11,
                            width = 595,
                            height = 842,
                            fontname = "Helvetica", # default font
                            fontfile = None, # any font file name
                            color = (0, 0, 0)) # text color (RGB)
    </code>
  </pre>



.. note::

    **Taking it further**

    The text parameter can be a (sequence of) string (assuming UTF-8 encoding). Insertion will start at :ref:`Point` (50, 72), which is one inch below top of page and 50 points from the left. The number of inserted text lines is returned.

    **API reference**

    - :meth:`Document.insert_page`



----------



.. _The_Basics_Spliting_Single_Pages:

Splitting Single Pages
~~~~~~~~~~~~~~~~~~~~~~~~~~

This deals with splitting up pages of a :title:`PDF` in arbitrary pieces. For example, you may have a :title:`PDF` with *Letter* format pages which you want to print with a magnification factor of four: each page is split up in 4 pieces which each going to a separate :title:`PDF` page in *Letter* format again.



.. raw:: html

  <pre>
    <code class="language-python" data-prismjs-copy="Copy">
        import fitz

        src = fitz.open("test.pdf")
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
    </code>
  </pre>


Example:

.. image:: images/img-posterize.png

.. note::

    **API reference**

    - :meth:`Page.cropbox_position`
    - :meth:`Page.show_pdf_page`


--------------------------


.. _The_Basics_Combining_Single_Pages:


Combining Single Pages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This deals with joining :title:`PDF` pages to form a new :title:`PDF` with pages each combining two or four original ones (also called "2-up", "4-up", etc.). This could be used to create booklets or thumbnail-like overviews.


.. raw:: html

  <pre>
    <code class="language-python" data-prismjs-copy="Copy">
        import fitz

        src = fitz.open("test.pdf")
        doc = fitz.open()  # empty output PDF

        width, height = fitz.paper_size("a4")  # A4 portrait output page format
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
        doc.save("4up.pdf", garbage=3, deflate=True)
    </code>
  </pre>

Example:

.. image:: images/img-4up.png


.. note::

    **API reference**

    - :meth:`Page.cropbox_position`
    - :meth:`Page.show_pdf_page`

--------------------------


.. _The_Basics_Encryption_and_Decryption:


:title:`PDF` Encryption & Decryption
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Starting with version 1.16.0, :title:`PDF` decryption and encryption (using passwords) are fully supported. You can do the following:

* Check whether a document is password protected / (still) encrypted (:attr:`Document.needs_pass`, :attr:`Document.is_encrypted`).
* Gain access authorization to a document (:meth:`Document.authenticate`).
* Set encryption details for PDF files using :meth:`Document.save` or :meth:`Document.write` and

    - decrypt or encrypt the content
    - set password(s)
    - set the encryption method
    - set permission details

.. note:: A PDF document may have two different passwords:

   * The **owner password** provides full access rights, including changing passwords, encryption method, or permission detail.
   * The **user password** provides access to document content according to the established permission details. If present, opening the :title:`PDF` in a viewer will require providing it.

   Method :meth:`Document.authenticate` will automatically establish access rights according to the password used.

The following snippet creates a new :title:`PDF` and encrypts it with separate user and owner passwords. Permissions are granted to print, copy and annotate, but no changes are allowed to someone authenticating with the user password.


.. raw:: html

  <pre>
    <code class="language-python" data-prismjs-copy="Copy">
        import fitz

        text = "some secret information" # keep this data secret
        perm = int(
            fitz.PDF_PERM_ACCESSIBILITY # always use this
            | fitz.PDF_PERM_PRINT # permit printing
            | fitz.PDF_PERM_COPY # permit copying
            | fitz.PDF_PERM_ANNOTATE # permit annotations
        )
        owner_pass = "owner" # owner password
        user_pass = "user" # user password
        encrypt_meth = fitz.PDF_ENCRYPT_AES_256 # strongest algorithm
        doc = fitz.open() # empty pdf
        page = doc.new_page() # empty page
        page.insert_text((50, 72), text) # insert the data
        doc.save(
            "secret.pdf",
            encryption=encrypt_meth, # set the encryption method
            owner_pw=owner_pass, # set the owner password
            user_pw=user_pass, # set the user password
            permissions=perm, # set permissions
        )
    </code>
  </pre>


.. note::

    **Taking it further**

    Opening this document with some viewer (Nitro Reader 5) reflects these settings:

    .. image:: images/img-encrypting.*

    **Decrypting** will automatically happen on save as before when no encryption parameters are provided.

    To **keep the encryption method** of a PDF save it using `encryption=fitz.PDF_ENCRYPT_KEEP`. If `doc.can_save_incrementally() == True`, an incremental save is also possible.

    To **change the encryption method** specify the full range of options above (`encryption`, `owner_pw`, `user_pw`, `permissions`). An incremental save is **not possible** in this case.

    **API reference**

    - :meth:`Document.save`

--------------------------



.. _The_Basics_Extracting_Tables:

Extracting Tables from a :title:`Page`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Tables can be found and extracted from any document :ref:`Page`.

.. raw:: html

    <pre>
        <code class="language-python" data-prismjs-copy="Copy">
            import fitz
            from pprint import pprint

            doc = fitz.open("test.pdf") # open document
            page = doc[0] # get the 1st page of the document
            tabs = page.find_tables() # locate and extract any tables on page
            print(f"{len(tabs.tables)} found on {page}") # display number of found tables
            if tabs.tables:  # at least one table found?
               pprint(tabs[0].extract())  # print content of first table
        </code>
    </pre>


.. note::

    **API reference**

    - :meth:`Page.find_tables`



.. _The_Basics_Get_Page_Links:

Getting Page Links
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Links can be extracted from a :ref:`Page` to return :ref:`Link` objects.


.. raw:: html

    <pre>
        <code class="language-python" data-prismjs-copy="Copy">
            import fitz

            for page in doc: # iterate the document pages
                link = page.first_link  # a `Link` object or `None`

                while link: # iterate over the links on page
                    # do something with the link, then:
                    link = link.next # get next link, last one has `None` in its `next`
        </code>
    </pre>


.. note::

    **API reference**

    - :meth:`Page.first_link`


.. include:: footer.rst
