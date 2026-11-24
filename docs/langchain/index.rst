
.. include:: ../header.rst

.. _langchain-pymupdf-layout:

.. raw:: html

    <script>
        document.getElementById("headerSearchWidget").action = '../search.html';
    </script>


PyMuPDF and Langchain
=====================

PyMuPDF provides a document loader for LangChain via the `langchain-pymupdf-layout <https://pypi.org/project/langchain-pymupdf-layout/>`_ package on PyPI.

This loader allows you to extract structured data from PDFs and other documents using :ref:`PyMuPDF's layout analysis <pymupdf_and_layout>`, and then use it within LangChain for various AI applications.

Features
--------

- 📚 Structured data extraction from your documents
- 🧐 Advanced document page layout understanding, including semantic markup for titles, headings, headers, footers, tables, images and text styling
- 🔍 Detect and isolate header and footer patterns on each page
- 📍 One LangChain document per layout element or per section, each with its page and position in the PDF, or optionally the whole PDF as one Markdown document

Requirements
------------

- Python 3.11 or higher
- LangChain Core v1.5.2 or higher
- PyMuPDF v2.1 or higher

Installation
------------

Install the package using pip to start using the Document Loader:

.. code-block:: bash

    pip install -U langchain-pymupdf-layout

Usage
-----

The loader uses PyMuPDF Layout to find the headings, paragraphs, lists, tables and other elements on each page.

By default (``mode="json"``) it uses this layout analysis, from :meth:`Document.to_json`, to return many small LangChain documents: one per element, or one per section. Each document records where its content is in the PDF, so you can:

- show or highlight the exact source of an answer
- filter by element type, for example index only body text and tables
- keep tables whole, as Markdown tables, rather than letting a text splitter cut through them

Use ``layout_chunking`` to choose how the content is grouped.

If you'd rather have one document containing the whole PDF as Markdown, use ``mode="markdown"``. See :ref:`one Markdown document <langchain-pymupdf-layout-markdown>`.


One document per layout element
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``layout_chunking="box"`` (the default) returns one document per heading, paragraph, list item, table, caption and so on. Pictures that contain no text are skipped.

.. code-block:: python

    from langchain_pymupdf_layout import PyMuPDFLayoutLoader

    loader = PyMuPDFLayoutLoader(
        file_path="https://arxiv.org/pdf/2607.11276",
        layout_chunking="box",
    )

    for document in loader.lazy_load():
        m = document.metadata
        print(m["page"], m["category"], (m["x0"], m["y0"], m["x1"], m["y1"]))
        print(document.page_content)

Each document's metadata includes:

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Key
     - Description
   * - ``page``
     - Page number, starting from 0
   * - ``category``
     - The element type: ``title``, ``section-header``, ``text``, ``list-item``, ``table``, ``picture``, ``caption``, ``formula``, ``footnote``, ``page-header`` or ``page-footer``
   * - ``header_level``
     - The heading level for headings, otherwise ``0``
   * - ``x0``, ``y0``, ``x1``, ``y1``
     - The element's position on the page, in PDF points, with the origin at the top-left corner
   * - ``page_width``, ``page_height``
     - The page size, in PDF points


One document per section
~~~~~~~~~~~~~~~~~~~~~~~~

``layout_chunking="section"`` returns one document per section: each heading together with everything under it, up to the next heading. The content is written as Markdown. This usually gives better chunks for retrieval than single elements, which can be very small (a heading on its own, for example).

.. code-block:: python

    import json

    loader = PyMuPDFLayoutLoader(
        file_path="https://arxiv.org/pdf/2607.11276",
        layout_chunking="section",
    )

    for document in loader.lazy_load():
        m = document.metadata
        print(f"{m['heading']} (pages {m['page']}-{m['page_end']})")

        # The position of every element in the section
        for region in json.loads(m["regions"]):
            print(region["page"], region["category"], region["bbox"])

Each document's metadata includes:

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Key
     - Description
   * - ``page``, ``page_end``
     - The first and last page of the section, starting from 0
   * - ``category``
     - Always ``section``
   * - ``heading``
     - The section's heading text. Empty for any content before the first heading
   * - ``header_level``
     - The level of the section's heading
   * - ``regions``
     - A JSON string listing the ``page``, ``category`` and ``bbox`` (``[x0, y0, x1, y1]``) of every element in the section

``regions`` is stored as a JSON string, rather than a list, because some vector stores only accept plain text and number values in metadata.


.. _langchain-pymupdf-layout-markdown:

One Markdown document
~~~~~~~~~~~~~~~~~~~~~

With ``mode="markdown"`` the loader returns one document per PDF, containing the whole PDF as Markdown. You can then split it into chunks yourself.

The example below uses ``RecursiveCharacterTextSplitter`` to chunk the document. In LangChain v1.0+ the text splitters are a separate package, which is not installed with ``langchain``, so install it first, either with the ``examples`` extra:

.. code-block:: bash

    pip install -U "langchain-pymupdf-layout[examples]"

or directly:

.. code-block:: bash

    pip install -U langchain-text-splitters

.. code-block:: python

    from langchain_pymupdf_layout import version

    print(version())  # Output: version number

    from langchain_text_splitters import RecursiveCharacterTextSplitter

    from langchain_pymupdf_layout import PyMuPDFLayoutLoader

    loader = PyMuPDFLayoutLoader(
        file_path="https://arxiv.org/pdf/2607.11276",
        mode="markdown",
    )

    documents = loader.load()

    # Chunk
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    chunks = text_splitter.split_documents(documents)

    print(f"Loaded {len(documents)} document(s)")
    print(f"Created {len(chunks)} chunk(s)")

    content = chunks[0].page_content
    print(f"\ncontent:\n{content}")

In Markdown mode, any other keyword arguments are passed to :meth:`Document.to_markdown`. For example, ``header=False`` and ``footer=False`` leave out page headers and footers, and ``pages=[0, 1]`` converts only the first two pages.


Notes
-----

- In both modes, every document also has the PDF's own metadata, such as ``source``, ``total_pages`` and ``creationdate``.
- ``header=False`` and ``footer=False`` work in JSON mode too: they leave out page headers and footers.
- Other keyword arguments are passed to :meth:`Document.to_json` (for example ``pages``, ``use_ocr``, ``force_ocr`` and ``ocr_language``). Options that only apply to Markdown output are ignored in JSON mode.
- See `layout_test.py <https://github.com/pymupdf/langchain-pymupdf-layout/blob/main/tests/layout_test.py>`__ for a full example, including drawing an element's position onto the PDF page.




.. include:: ../footer.rst
