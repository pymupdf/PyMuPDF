
.. include:: header.rst


PyMuPDF, LLM & RAG
============================


Integrating |PyMuPDF| into your :title:`Large Language Model (LLM)` framework and overall :title:`RAG (Retrieval-Augmented Generation`) solution provides the fastest and most reliable way to deliver document data.

If you need to export to :title:`Markdown`, structured |JSON| or |TXT| formats, |PyMuPDF| provides the necessary tools to achieve this efficiently in the :class:`Document` object.


Converting to |Markdown|
-------------------------------------
 

.. code-block:: python

    doc = pymupdf.open("input.pdf")
    md = doc.to_markdown()

See the API at: :meth:`Document.to_markdown`.

Converting to |JSON|
-------------------------------------


.. code-block:: python

    doc = pymupdf.open("input.pdf")
    json = doc.to_json()

See the API at :meth:`Document.to_json`.

Converting to |TXT|
-------------------------------------

.. code-block:: python

    doc = pymupdf.open("input.pdf")
    txt = doc.to_text()

See the API at: :meth:`Document.to_text`.


Batch conversion
-------------------------------------

You can convert multiple documents in a batch by iterating over them and applying the conversion methods accordingly. For example:

.. code-block:: python

    from pymupdf import convert_batch
    
    inputs = ["report.pdf", "invoice.pdf", "manual.pdf"]
    results = convert_batch(
        inputs,
        out_dir="./out",
        workers=1,
        backend="md"
    )
    for r in results:
        status = "OK" if r.success else f"FAILED: {r.error}"
        print(f"{r.input.name}: {status}")


Integration with :title:`LangChain`
-------------------------------------

It is simple to integrate directly with :title:`LangChain` by using their dedicated loader as follows:


.. code-block:: python

    from langchain_community.document_loaders import PyMuPDFLoader
    loader = PyMuPDFLoader("example.pdf")
    data = loader.load()


See `LangChain Using PyMuPDF <https://python.langchain.com/docs/modules/data_connection/document_loaders/pdf/#using-pymupdf>`_ for full details.


Integration with :title:`LlamaIndex`
---------------------------------------


Use the dedicated `PyMuPDFReader` from :title:`LlamaIndex` 🦙 to manage your document loading.

.. code-block:: python

    from llama_index.readers.file import PyMuPDFReader
    loader = PyMuPDFReader()
    documents = loader.load(file_path="example.pdf")

See `Building RAG from Scratch <https://docs.llamaindex.ai/en/stable/examples/low_level/oss_ingestion_retrieval>`_ for more.


Preparing Data for Chunking
-----------------------------

You can efficiently prepare your documents for chunking and subsequent processing with your :title:`LLM` byt using the :meth:`Document.to_chunks` method.

Create chunked documents as follows:

.. code-block:: python
    
    doc = pymupdf.open("input.pdf")
    chunked_document = doc.to_chunks()

Basic queries with chunked documents can be made as follows:

.. code-block:: python

    len(chunked_document) # Count the number of Chunks
    chunked_document[0], chunked_document[2:5] # a Chunk, a list of Chunks
    chunked_document.index(chunked_document[3]) # 3 (Sequence protocol: iteration, slicing, index)
    chunked_document.chunks  # the same chunks as a tuple
    chunked_document.text # all chunk text joined (lazy)
    chunked_document.get("c0") # get chunk by any public id: c{n}, t{n}, f{n}, s{n}, p{page}.b{box}

.. note::

    **API reference**

    - :meth:`Document.to_chunks`
    - :doc:`chunked-document`
    - :doc:`chunk`
    - :doc:`chunk-metadata`
    
    



.. _using_pymupdf_with_pymupdf_office:

Using with |PyMuPDF Office|
---------------------------


For **Office** document support, |PyMuPDF| works seamlessly with |PyMuPDF Office|. Assuming you have :doc:`../pymupdf-office/index` installed you will be able to work with **Office** documents as expected:


.. code-block:: python

    import pymupdf
    import pymupdf.office
    pymupdf.office.unlock()
    md = pymupdf.office.to_markdown("sample.doc")


.. _pymupdf_and_layout:

PyMuPDF & PyMuPDF Layout
-----------------------------------

By default |PyMuPDF| includes a `layout analysis module`_ to enhance output results. To disable this module you can do so by calling the :meth:`use_layout` method.




Related Blogs
-----------------------------

Methodologies to Extract Text
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- `Enhanced Text Extraction <https://artifex.com/blog/rag-llm-and-pdf-enhanced-text-extraction>`_
- `Conversion to Markdown Text with PyMuPDF <https://artifex.com/blog/rag-llm-and-pdf-conversion-to-markdown-text-with-pymupdf>`_



Create a Chatbot to connect with your documents
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- `Make a simple command line Chatbot <https://artifex.com/blog/creating-a-rag-chatbot-with-chatgpt-and-pymupdf>`_
- `Make a Chatbot GUI <https://artifex.com/blog/building-a-rag-chatbot-gui-with-the-chatgpt-api-and-pymupdf>`_




.. _PyMuPDF4LLM Document Loader: https://docs.langchain.com/oss/python/integrations/providers/pymupdf4llm/

.. _layout analysis module: https://pymupdf.io/use-cases/layout/?utm_source=rtd-pymupdf&utm_medium=rtd&utm_content=inline_link




.. include:: footer.rst