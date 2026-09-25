
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

..
    .. raw:: html

    <button id="pymupdf4llmButton" class="cta orange" style="text-transform: none;" onclick="window.location='pymupdf4llm/'">Try PyMuPDF4LLM</button>
    <p></p>

    <script>
        let lang = document.getElementsByTagName('html')[0].getAttribute('lang');

        if (lang=="ja") {
            document.getElementById("pymupdf4llmButton").innerHTML = "PyMuPDF4LLM を試してみる";
        }

    </script>


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

todo


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








.. include:: footer.rst