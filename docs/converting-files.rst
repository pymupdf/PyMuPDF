.. include:: header.rst

.. _ConvertingFiles:

==============================
Converting Files
==============================



Files to PDF
~~~~~~~~~~~~~~~~~~

:ref:`Document types supported by PyMuPDF<HowToOpenAFile>` can easily be converted to |PDF| by using the :meth:`Document.convert_to_pdf` method. This method returns a buffer of data which can then be utilized by |PyMuPDF| to create a new |PDF|.



**Example**

.. code-block:: python

    import pymupdf

    xps = pymupdf.open("input.xps")
    pdfbytes = xps.convert_to_pdf()
    pdf = pymupdf.open("pdf", pdfbytes)
    pdf.save("output.pdf")



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
