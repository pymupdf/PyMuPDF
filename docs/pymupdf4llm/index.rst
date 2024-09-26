
.. include:: ../header.rst

.. _pymupdf4llm


PyMuPDF4LLM
===========================================================================

|PyMuPDF4LLM| is aimed to make it easier to extract **PDF** content in the format you need for **LLM** & **RAG** environments. It supports :ref:`Markdown extraction <extracting_as_md>` as well as :ref:`LlamaIndex document output <extracting_as_llamaindex>`.

.. important::

    You can extend the supported file types to also include **Office** document formats (DOC/DOCX, XLS/XLSX, PPT/PPTX, HWP/HWPX) by :ref:`using PyMuPDF Pro with PyMuPDF4LLM <using_pymupdf4llm_withpymupdfpro>`.

Features
-------------------------------

    - Support for multi-column pages
    - Support for image and vector graphics extraction (and inclusion of references in the MD text)
    - Support for page chunking output.
    - Direct support for output as :ref:`LlamaIndex Documents <extracting_as_llamaindex>`.


Functionality
--------------------

- This package converts the pages of a file to text in **Markdown** format using |PyMuPDF|.

- Standard text and tables are detected, brought in the right reading sequence and then together converted to **GitHub**-compatible **Markdown** text.

- Header lines are identified via the font size and appropriately prefixed with one or more `#` tags.

- Bold, italic, mono-spaced text and code blocks are detected and formatted accordingly. Similar applies to ordered and unordered lists.

- By default, all document pages are processed. If desired, a subset of pages can be specified by providing a list of `0`-based page numbers.


Installation
----------------


Install the package via **pip** with:


.. code-block:: bash

    pip install pymupdf4llm


.. _extracting_as_md:

Extracting a file as **Markdown**
--------------------------------------------------------------

To retrieve your document content in **Markdown** simply install the package and then use a couple of lines of **Python** code to get results.



Then in your **Python** script do:


.. code-block:: python

    import pymupdf4llm
    md_text = pymupdf4llm.to_markdown("input.pdf")


.. note::

    Instead of the filename string as above, one can also provide a :ref:`PyMuPDF Document <Document>`. A second parameter may be a list of `0`-based page numbers, e.g. `[0,1]` would just select the first and second pages of the document.


If you want to store your **Markdown** file, e.g. store as a UTF8-encoded file, then do:


.. code-block:: python

    import pathlib
    pathlib.Path("output.md").write_bytes(md_text.encode())



.. _extracting_as_llamaindex:

Extracting a file as a **LlamaIndex** document
--------------------------------------------------------------

|PyMuPDF4LLM| supports direct conversion to a **LLamaIndex** document. A document is first converted into **Markdown** format and then a **LlamaIndex** document is returned as follows:



.. code-block:: python

    import pymupdf4llm
    llama_reader = pymupdf4llm.LlamaMarkdownReader()
    llama_docs = llama_reader.load_data("input.pdf")


.. _using_pymupdf4llm_withpymupdfpro:

Using with |PyMuPDF Pro|
---------------------------


For **Office** document support, |PyMuPDF4LLM| works seamlessly with |PyMuPDF Pro|. Assuming you have :doc:`../pymupdf-pro` installed you will be able to work with **Office** documents as expected:


.. code-block:: python

    import pymupdf4llm
    import pymupdf.pro
    pymupdf.pro.unlock()
    md_text = pymupdf4llm.to_markdown("sample.doc")


As you can see |PyMuPDF Pro| functionality will be available within the |PyMuPDF4LLM| context!



API
-------

See :ref:`the PyMuPDF4LLM API <pymupdf4llm-api>`.

Further Resources
-------------------


Sample code
~~~~~~~~~~~~~~~

- `Command line RAG Chatbot with PyMuPDF <https://github.com/pymupdf/RAG/tree/main/examples/country-capitals>`_
- `Example of a Browser Application using Langchain and PyMuPDF <https://github.com/pymupdf/RAG/tree/main/examples/GUI>`_


Blogs
~~~~~~~~~~~~~~

- `RAG/LLM and PDF: Enhanced Text Extraction <https://artifex.com/blog/rag-llm-and-pdf-enhanced-text-extraction>`_
- `Creating a RAG Chatbot with ChatGPT and PyMuPDF <https://artifex.com/blog/creating-a-rag-chatbot-with-chatgpt-and-pymupdf>`_
- `Building a RAG Chatbot GUI with the ChatGPT API and PyMuPDF <https://artifex.com/blog/building-a-rag-chatbot-gui-with-the-chatgpt-api-and-pymupdf>`_
- `RAG/LLM and PDF: Conversion to Markdown Text with PyMuPDF <https://artifex.com/blog/rag-llm-and-pdf-conversion-to-markdown-text-with-pymupdf>`_







.. include:: ../footer.rst
