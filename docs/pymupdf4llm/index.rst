
.. include:: ../header.rst

.. _pymupdf4llm:


.. raw:: html

    <script>
        document.getElementById("headerSearchWidget").action = '../search.html';
    </script>


PyMuPDF4LLM
===========================================================================

|PyMuPDF4LLM| is a lightweight extension for |PyMuPDF| that turns PDFs into clean, structured data with minimal setup. It includes layout analysis *without* any GPU requirement.


|PyMuPDF4LLM| is aimed to make it easier to extract document content in the format you need for **LLM** & **RAG** environments. It supports :ref:`Markdown <extracting_as_md>`, :ref:`JSON <extracting_as_json>` and :ref:`TXT <extracting_as_txt>` extraction, as well as :ref:`LlamaIndex <integration_with_llamaindex>` and :ref:`LangChain <integration_with_langchain>` integration.


.. important::

    You can also extend the supported file types to also include **Office** document formats (DOC/DOCX, XLS/XLSX, PPT/PPTX, HWP/HWPX) by :ref:`using PyMuPDF Pro with PyMuPDF4LLM <using_pymupdf4llm_with_pymupdfpro>`.

Features
-------------------------------

    - Support for Markdown, JSON and plain text output formats.
    - Support for multi-column pages.
    - Support for image and vector graphics extraction.
    - Layout analysis for better semantic understanding of document structure.
    - Support for page chunking output.
    - Integration with :ref:`LlamaIndex <integration_with_llamaindex>` & :ref:`LangChain <integration_with_langchain>`.

API
-------

See: :doc:`api`.


Installation
----------------


Install the package via **pip** with:


.. code-block:: bash

    pip install pymupdf4llm


Extracting
-------------------------------


.. _extracting_as_md:

As **Markdown**
~~~~~~~~~~~~~~~~~~~~~~~

To retrieve your document content in **Markdown** use the :meth:`to_markdown` method as follows:

.. code-block:: python

    import pymupdf4llm
    md = pymupdf4llm.to_markdown("input.pdf")



.. _extracting_as_json: 

As **JSON**
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To retrieve your document content in **JSON** use the :meth:`to_json` method as follows:

.. code-block:: python

    import pymupdf4llm
    json = pymupdf4llm.to_json("input.pdf")

The JSON export will give you bounding box information and layout data for each element on the page. This can be used to create your own custom output formats or to simply have more detailed information about the document structure for RAG workflows & LLM integrations.


.. _extracting_as_txt:

As **TXT**
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To retrieve your document content in **TXT** use the :meth:`to_text` method as follows:

.. code-block:: python

    import pymupdf4llm
    txt = pymupdf4llm.to_text("input.pdf")



----

.. note::
    Instead of using filename strings as above, one can also provide a :ref:`PyMuPDF Document <Document>`.

    Finally we can save the output to an external file as follows::

        from pathlib import Path
        suffix = ".md" # or ".json" or ".txt"
        Path(doc.name).with_suffix(suffix).write_bytes(md.encode())

Headers & Footers
~~~~~~~~~~~~~~~~~~~~~~~


Many documents will have header and footer information on each page of a PDF which you may or may not want to include. This information can be repetitive and simply not needed ( e.g. the same logo and document title or page number information is not always required when it comes to extracting the document content ).

|PyMuPDF4LLM| is trained in detecting these typical document elements and able to omit them.

So in this case we can adjust our API calls to ignore these elements as follows::

    md = pymupdf4llm.to_markdown(doc, header=False, footer=False)


.. note::

    Please note that page ``header`` / ``footer`` exclusion is not applicable to JSON output as it aims to always represent all data for the included pages. Please refer to :doc:`api` for more.


Integrations
-------------------------------

.. _integration_with_llamaindex:

With **LlamaIndex**
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

|PyMuPDF4LLM| supports direct conversion to a **LlamaIndex** document. A document is first converted into **Markdown** format and then a **LlamaIndex** document is returned as follows:


.. code-block:: python

    import pymupdf4llm
    llama_reader = pymupdf4llm.LlamaMarkdownReader()
    llama_docs = llama_reader.load_data("input.pdf") 


.. _integration_with_langchain:

With **LangChain** 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

|PyMuPDF4LLM| also supports **LangChain** integration, see the `PyMuPDF4LLM Document Loader`_ for more details.


.. _using_pymupdf4llm_with_pymupdfpro:

Using with |PyMuPDF Pro|
---------------------------


For **Office** document support, |PyMuPDF4LLM| works seamlessly with |PyMuPDF Pro|. Assuming you have :doc:`../pymupdf-pro/index` installed you will be able to work with **Office** documents as expected:


.. code-block:: python

    import pymupdf4llm
    import pymupdf.pro
    pymupdf.pro.unlock()
    md = pymupdf4llm.to_markdown("sample.doc")


.. _pymupdf4llm_and_layout:

PyMuPDF4LLM & PyMuPDF Layout
-----------------------------------

By default |PyMuPDF4LLM| includes a `layout analysis module`_ to enhance output results. To disable this module you can do so by calling the :meth:`use_layout` method.


Further Resources
-------------------


Sample code
~~~~~~~~~~~~~~~

- `Command line RAG Chatbot with PyMuPDF <https://github.com/pymupdf/RAG/tree/main/examples/country-capitals>`_
- `Example of a Browser Application using LangChain and PyMuPDF <https://github.com/pymupdf/RAG/tree/main/examples/GUI>`_


Blogs
~~~~~~~~~~~~~~

- `RAG/LLM and PDF: Enhanced Text Extraction <https://artifex.com/blog/rag-llm-and-pdf-enhanced-text-extraction>`_
- `Creating a RAG Chatbot with ChatGPT and PyMuPDF <https://artifex.com/blog/creating-a-rag-chatbot-with-chatgpt-and-pymupdf>`_
- `Building a RAG Chatbot GUI with the ChatGPT API and PyMuPDF <https://artifex.com/blog/building-a-rag-chatbot-gui-with-the-chatgpt-api-and-pymupdf>`_
- `RAG/LLM and PDF: Conversion to Markdown Text with PyMuPDF <https://artifex.com/blog/rag-llm-and-pdf-conversion-to-markdown-text-with-pymupdf>`_

.. include:: ../footer.rst


PyMuPDF4LLM Document Loader

.. _PyMuPDF4LLM Document Loader: https://docs.langchain.com/oss/python/integrations/providers/pymupdf4llm/

.. _layout analysis module: https://pypi.org/project/pymupdf-layout/
