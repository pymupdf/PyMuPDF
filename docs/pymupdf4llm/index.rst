
.. include:: ../header.rst

.. _pymupdf4llm:


.. raw:: html

    <script>
        document.getElementById("headerSearchWidget").action = '../search.html';
    </script>


PyMuPDF4LLM
===========================================================================

|PyMuPDF4LLM| is a lightweight extension for |PyMuPDF| that turns PDFs into clean, structured data with minimal setup. It includes layout analysis *without* any GPU requirement.


|PyMuPDF4LLM| makes it easy to extract document content in the format you need for **LLM** & **RAG** environments. It supports structured data extraction to :ref:`Markdown <extracting_as_md>`, :ref:`JSON <extracting_as_json>` and :ref:`TXT <extracting_as_txt>`, as well as :ref:`LlamaIndex <integration_with_llamaindex>` and :ref:`LangChain <integration_with_langchain>` integration.


.. important::

    You can also extend the supported file types to also include **Office** document formats (DOC/DOCX, XLS/XLSX, PPT/PPTX, HWP/HWPX) by :ref:`using PyMuPDF Pro with PyMuPDF4LLM <using_pymupdf4llm_with_pymupdfpro>`.

Features
-------------------------------

    - Support for Markdown, JSON and plain text output formats.
    - Support for multi-column pages.
    - Support for image and vector graphics extraction.
    - Layout analysis for better semantic understanding of document structure.
    - Support for page chunking output.
    - Automatic detection of pages which profit from OCR and support for various OCR engines.
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



OCR
--------

PyMuPDF4LLM includes built-in OCR support for scanned documents and image-based PDFs. By default, OCR runs **automatically** when needed — you don't have to opt in. For more control, you can force OCR on specific pages, disable it entirely, or swap in a different OCR engine using the adaptor interface.

.. note::

   If you want to use an OCR engine other than Tesseract, see :ref:`OCR Adaptors <ocr-adaptors>` for details on how to plug in your own OCR function.


Hybrid OCR strategy
~~~~~~~~~~~~~~~~~~~~~~~~~

PyMuPDF4LLM applies OCR only when it is genuinely required to obtain the complete text of a PDF page. If a page already contains sufficient extractable text, OCR is skipped entirely — avoiding unnecessary work and eliminating the risk of degrading high-quality digital text.

When OCR is needed, PyMuPDF4LLM automatically selects the most suitable OCR plugin available in the runtime environment, balancing detection accuracy with processing speed.

Its built-in OCR plugins implement a Hybrid OCR strategy: only those regions lacking extractable, legible text are passed to the OCR engine. This selective approach typically reduces OCR processing time by around 50% while improving recognition accuracy, since the engine focuses exclusively on the problematic regions. The recognized text is then merged back into the original page, enriching it without disturbing existing digital content.


----


Auto-OCR Behaviour
~~~~~~~~~~~~~~~~~~~~~~~~~~

PyMuPDF4LLM inspects each page before extracting text. If a page contains **no selectable text** — meaning all content is rasterised into images — OCR is triggered automatically for that page.

Pages that contain native text are never sent through OCR, even if they also contain embedded images. This keeps processing fast and avoids degrading already-clean text.

.. code-block:: python

   import pymupdf4llm

   # OCR runs automatically on any page with no selectable text
   md_text = pymupdf4llm.to_markdown("scanned-document.pdf")

The resulting Markdown is seamless — pages extracted via OCR and pages extracted natively are combined into a single output with no distinction between them.

----

How OCR is Triggered
~~~~~~~~~~~~~~~~~~~~~~~~~~

There are two scenarios where OCR is applied automatically:

**No text at all** — if a page contains roughly no text but is covered with images or many character-sized vectors, PyMuPDF4LLM checks whether text is *probably* detectable on the page. This distinguishes image-based text (e.g. a scanned document) from ordinary pictures like photographs.

**Garbled text** — if a page does contain text but too many characters are unreadable (e.g. ``"�����"``), OCR is applied **for the affected text areas only**, not the full page. This preserves already-readable text, images, and vectors while recovering only what is broken.


----

Forcing OCR
~~~~~~~~~~~~~

In some cases you may want to force OCR even on pages that contain selectable text — for example, when the native text layer is corrupt, misencoded, or misaligned with the visual content.

Use ``force_ocr=True`` to bypass the auto-detection check entirely:

.. code-block:: python

   md_text = pymupdf4llm.to_markdown("document.pdf", force_ocr=True)

.. warning::

   Forcing OCR on clean, text-based PDFs will slow down processing significantly and may reduce output quality. Only use ``force_ocr=True`` when you have reason to distrust the native text layer.

You can also force OCR on specific pages rather than the whole document:

.. code-block:: python

   md_text = pymupdf4llm.to_markdown(
       "document.pdf",
       pages=[2, 3, 4],
       force_ocr=True
   )

----

Disabling OCR
~~~~~~~~~~~~~

To prevent OCR from running at all — even on pages with no selectable text — set ``use_ocr=False``:

.. code-block:: python

   md_text = pymupdf4llm.to_markdown("document.pdf", use_ocr=False)

Pages with no selectable text will return empty strings in this mode. This is useful when you know your documents are always text-based, or when you want to handle OCR yourself in a downstream step.

----

.. _ocr-adaptors:

OCR Engines
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Other OCR Engines (OCR Adaptors or Plugins) can be used with PyMuPDF4LLM.

See :doc:`ocr-plugins` for details on how to use different OCR engines with PyMuPDF4LLM, including Tesseract, RapidOCR, and how to implement your own custom OCR function.



OCR Language Support
~~~~~~~~~~~~~~~~~~~~~~~~~~

When using the default Tesseract adaptor, you can specify one or more languages using Tesseract's language codes.

Specify the language to be used by the Tesseract OCR engine. Default is ``"eng"`` (English). Make sure that the respective language data files are installed. Remember to use correct Tesseract language codes. Multiple languages can be specified by concatenating the respective codes with a plus sign ``"+"``, for example ``"eng+deu"`` for English and German.

.. code-block:: python

   md_text = pymupdf4llm.to_markdown("multilingual.pdf",
                                      ocr_language="eng+deu")

Tesseract language packs must be installed separately on your system. For example, on Ubuntu:

.. code-block:: bash

   sudo apt install tesseract-ocr-deu tesseract-ocr-fra

See the page on :ref:`installing Tesseract language packs <tesseract-language-packs>` for further details.

----

Performance Tips
~~~~~~~~~~~~~~~~~~~~~~~~~~

OCR is the most compute-intensive part of the extraction pipeline. A few ways to keep it fast:

- **Process only the pages you need** using the ``pages`` parameter to avoid running OCR on the entire document.
- **Cache results** — write the output to disk after the first run so you don't re-process the same file.
- **Use** ``force_ocr=False`` (the default) so clean pages skip OCR entirely.
- **Resize images before passing to OCR** — very high DPI scans can slow Tesseract down without improving accuracy.

----


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
