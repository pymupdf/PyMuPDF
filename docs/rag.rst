
.. include:: header.rst


PyMuPDF, LLM & RAG
============================


Integrating |PyMuPDF| into your :title:`Large Language Model (LLM)` framework and overall :title:`RAG (Retrieval-Augmented Generation`) solution provides the fastest and most reliable way to deliver document data.

There are a few well known :title:`LLM` solutions which have their own interfaces with |PyMuPDF| - it is a fast growing area, so please let us know if you discover any more!

If you need to export to :title:`Markdown` or obtain a :title:`LlamaIndex` Document from a file:

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

Chunking (or splitting) data is essential to give context to your :title:`LLM` data and with :title:`Markdown` output now supported by |PyMuPDF| this means that `Level 3 chunking <https://medium.com/@anuragmishra_27746/five-levels-of-chunking-strategies-in-rag-notes-from-gregs-video-7b735895694d#b123>`_ is supported.



.. _rag_outputting_as_md:

Outputting as :title:`Markdown`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In order to export your document in :title:`Markdown` format you will need a separate helper. Package :doc:`pymupdf4llm/index` is a high-level wrapper of |PyMuPDF| functions which for each page outputs standard and table text in an integrated Markdown-formatted string across all document pages:


.. code-block:: python

    # convert the document to markdown
    import pymupdf4llm
    md_text = pymupdf4llm.to_markdown("input.pdf")

    # Write the text to some file in UTF8-encoding
    import pathlib
    pathlib.Path("output.md").write_bytes(md_text.encode())


For further information please refer to: :doc:`pymupdf4llm/index`.


How to use :title:`Markdown` output
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once you have your data in :title:`Markdown` format you are ready to chunk/split it and supply it to your :title:`LLM`, for example, if this is :title:`LangChain` then do the following:

.. code-block:: python

    import pymupdf4llm
    from langchain.text_splitter import MarkdownTextSplitter

    # Get the MD text
    md_text = pymupdf4llm.to_markdown("input.pdf")  # get markdown for all pages

    splitter = MarkdownTextSplitter(chunk_size=40, chunk_overlap=0)

    splitter.create_documents([md_text])



For more see `5 Levels of Text Splitting <https://github.com/FullStackRetrieval-com/RetrievalTutorials/blob/main/tutorials/LevelsOfTextSplitting/5_Levels_Of_Text_Splitting.ipynb>`_


Related Blogs
--------------------

To find out more about |PyMuPDF|, :title:`LLM` & :title:`RAG` check out our blogs for implementations & tutorials.


Methodologies to Extract Text
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- `Enhanced Text Extraction <https://artifex.com/blog/rag-llm-and-pdf-enhanced-text-extraction>`_
- `Conversion to Markdown Text with PyMuPDF <https://artifex.com/blog/rag-llm-and-pdf-conversion-to-markdown-text-with-pymupdf>`_



Create a Chatbot to discuss your documents
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- `Make a simple command line Chatbot <https://artifex.com/blog/creating-a-rag-chatbot-with-chatgpt-and-pymupdf>`_
- `Make a Chatbot GUI <https://artifex.com/blog/building-a-rag-chatbot-gui-with-the-chatgpt-api-and-pymupdf>`_








.. include:: footer.rst