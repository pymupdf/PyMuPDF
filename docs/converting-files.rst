.. include:: header.rst

.. _ConvertingFiles:

==============================
Converting Files
==============================



Files to PDF
~~~~~~~~~~~~~~~~~~

:ref:`Document types supported by PyMuPDF <HowToOpenAFile>` can easily be converted to |PDF| by using the :meth:`Document.convert_to_pdf` method. This method returns a buffer of data which can then be utilized by |PyMuPDF| to create a new |PDF|.



**Example**

.. code-block:: python

    import pymupdf
    
    # Convert Markdown to PDF
    md_doc = pymupdf.open("example.md")
    pdfdata = md_doc.convert_to_pdf()
    pdf_doc = pymupdf.open(stream=pdfdata)
    pdf_doc.save("example.pdf")

    # Convert XPS to PDF
    xps = pymupdf.open("input.xps")
    pdfdata = xps.convert_to_pdf()
    pdf = pymupdf.open(stream=pdfdata)
    pdf.save("output.pdf")

.. _Markdown_to_PDF:

Markdown to PDF
~~~~~~~~~~~~~~~~~

As Markdown files are supported input files they can be easily converted to PDF using the :meth:`Document.convert_to_pdf` method.

In the simplest case you can just open the Markdown file and call the method to get a PDF representation of the content. 


Defining paper size
"""""""""""""""""""

The default paper size is 400 x 600 :doc:`rect` but you can specify a custom paper size if you wish, to do this just send through the `rect` parameter as required, for example:

.. code-block:: python

    md_doc = pymupdf.open("example.md", rect=pymupdf.paper_rect("A4")) # A4 size


Defining CSS
""""""""""""

By default, the Markdown content will be converted to PDF using a default CSS stylesheet. However, you can specify your own CSS stylesheet to customize the appearance of the resulting PDF. To do this, define your `css` and apply it.

For example, to make all ``h1`` headers red (The single ``#`` symbol in Markdown), you could do the following:

.. code-block:: python

    md_doc = pymupdf.open(  # open the Markdown document in A4 size
        "example.md",
        rect=pymupdf.paper_rect("A4")
    )
     
    css = "h1 {color:red;}"
    md_doc.apply_css(css)

    pdf_doc = pymupdf.open(stream=md_doc.convert_to_pdf())
    pdf_doc.ez_save("red-colored-header.pdf")

.. note::

    The :ref:`support for CSS <CSS_Support>` is currently limited.


Using CSS Custom Element Selectors
""""""""""""""""""""""""""""""""""

Markdown input supports custom element selectors in the CSS, so you can define your own tags in the Markdown and then refer to them in the CSS.

In this way you can specify custom styles for specific elements in the Markdown content. For example, you could define a custom tag called ``mytag`` in the Markdown and then refer to it in the CSS to make it red:

.. code-block:: python

    css = """
    mytag {
        color: red;
    }
    """

And the corresponding Markdown:

.. code-block:: markdown

    # This is a header

    This is some text.

    <mytag>This text will be red.</mytag>

This is particularly useful for defining image sizes. For example, you could define a custom class called ``my_image_class`` in the CSS and then refer to it in the Markdown to style images:

.. code-block:: python

    css = """
    my_image_class img {
        width: 100px;
        height: 100px;
    }
    """

With the corresponding Markdown:

.. code-block:: markdown

    # This is a header

    This is some text.

    <my_image_class><img src="pie-chart.png" /></my_image_class>


Defining Fonts
"""""""""""""""""

Fonts can be defined by using the `archive` parameter to provide a custom :ref:`Archive` containing the font files.

The fonts must exist in an archive which is provided to the `archive` parameter when opening the Markdown file. The CSS can then refer to these fonts by their names as defined in the archive.

For example, assuming you have access to the source files for the "Comic Sans" font for all text, you could do the following:

.. code-block:: python

    # Global CSS instructions to use the "Comic Sans" font for all text. The font files must be provided in the archive.
    css = """
    @font-face {font-family: sans-serif; src: url(comic.ttf);}
    @font-face {font-family: sans-serif; src: url(comicbd.ttf); font-weight: bold;}
    @font-face {font-family: sans-serif; src: url(comicz.ttf); font-weight: bold; font-style: italic;}
    @font-face {font-family: sans-serif; src: url(comici.ttf); font-style: italic;}
    """

    archive = pymupdf.Archive("C:/Windows/Fonts")  # the fonts are here
    archive.add(".")  # we've stored the archive image in this script's folder

    md_file = "sample.md"
    md_doc = pymupdf.open(  # open the Markdown document
        md_file,
        archive=archive,  # where to look for resources (fonts, images)
        rect=pymupdf.paper_rect("A4"),  # page dimension ISO A4
    )

    md_doc.apply_css(css) 





PDF to Markdown
~~~~~~~~~~~~~~~~~

By utlilizing the :doc:`PyMuPDF4LLM API <pymupdf4llm/api>` we are able to convert PDF to a Markdown representation.

**Example**

.. code-block:: python

    import pymupdf4llm
    import pathlib

    md_text = pymupdf4llm.to_markdown("test.pdf")
    print(md_text)

    pathlib.Path("4llm-output.md").write_bytes(md_text.encode())


PDF to SVG
~~~~~~~~~~~~~~~~~~

Technically, as SVG files cannot be multipage, we must export each page as an SVG.

To get an SVG representation of a page use the :meth:`Page.get_svg_image` method.

**Example**

.. code-block:: python

    import pymupdf

    doc = pymupdf.open("input.pdf")
    page = doc[0]

    # Convert page to SVG
    svg_content = page.get_svg_image()

    # Save to file
    with open("output.svg", "w", encoding="utf-8") as f:
        f.write(svg_content)

    doc.close()

PDF to DOCX
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use the pdf2docx_ library which uses |PyMuPDF| to provide document conversion from |PDF| to **DOCX** format.



**Example**

.. code-block:: python

    from pdf2docx import Converter

    pdf_file = 'input.pdf'
    docx_file = 'output.docx'

    # convert pdf to docx
    cv = Converter(pdf_file)
    cv.convert(docx_file) # all pages by default
    cv.close()


.. include:: footer.rst
