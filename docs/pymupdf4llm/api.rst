.. include:: ../header.rst



.. _pymupdf4llm-api:


API
===========================================================================

The |PyMuPDF4LLM| API
--------------------------

.. property:: version

    Prints the version of the library.

.. method:: to_markdown(doc: pymupdf.Document | str, *, pages: list | range | None = None, hdr_info: Any = None, write_images: bool = False, margins=(0, 50, 0, 50), page_chunks: bool = False) -> str | list[dict]

    Read the pages of the file and outputs the text of its pages in |Markdown| format. How this should happen in detail can be influenced by a number of parameters. Please note that there exists support for building page chunks from the |Markdown|  text.

    :arg Document,str doc: the file, to be specified either as a file path string, or as a |PyMuPDF| Document (created via `pymupdf.open`).

    :arg list,range pages: optional, the pages to consider for output. If omitted all pages are processed.

    :arg hdr_info: optional, a callable (or an object having a method named `hdr_info`) which accepts a text span and delivers a string of 0 up to 6 "#" characters which should be used to identify headers in the markdown text. If omitted, a full document scan will be performed to find the most popular font sizes and derive header levels based on this. For instance, to avoid generating any lines tagged as headers specify `hdr_info=lambda s: ""`.

    :arg bool write_images: when encountering images or vector graphics, PNG images will be generated from the respective page area. Markdown references will be generated pointing to these images. Any text contained in these areas will not be included in the output. Therefore, if your document has text written on full page images, make sure to set this parameter to `False`.

    :arg float,list margins: a float or a list of up to 4 floats specifying page borders. If 4 floats are provided, they are assumed to be the values left, top, right, bottom, in this sequence. Only content below top and above bottom, etc. will be considered for processing. If a single float value is provided, it will be taken as the value for all 4 border values. A pair of numbers is assumed to specify top and bottom.
    
    :arg bool page_chunks: if `True` the output will be a list of `Document.page_count` dictionaries (one per page). Each dictionary has the following structure:

        - **"metadata"** - a dictionary consisting of the document's metadata `Document.metadata <https://pymupdf.readthedocs.io/en/latest/document.html#Document.metadata>`_, enriched with additional keys **"file_path"** (the file name), **"page_count"** (number of pages in document), and **"page_number"** (1-based page number).

        - **"toc_items"** - a list of Table of Contents items pointing to this page. Each item of this list has the format `[lvl, title, pagenumber]`, where `lvl` is the hierachy level, `title` a string and `pagenumber` the 12-based page number.

        - **"tables"** - a list of tables on this page. Each item is a dictionary with keys "bbox", "row_count" and "col_count". Key "bbox" is a `pymupdf.Rect` in tuple format of the table's position on the page.

        - **"images"** - a list of images on the page. This a copy of page method :meth:`Page.get_image_info`.

        - **"graphics"** - a list of vector graphics rectangles on the page. This is a list of boundary boxes of clustered vector graphics as delivered by method :meth:`Page.cluster_drawings`.

        - **"text"** - page content as |Markdown| text.

    :returns: Either a string of the combined text of all selected document pages or a list of dictionaries.

.. method:: LlamaMarkdownReader(*args, **kwargs)

    Create a `pdf_markdown_reader.PDFMarkdownReader` using the `LlamaIndex`_ package. Please note that this package will **not automatically be installed** when installing **pymupdf4llm**.

    For details on the possible arguments, please consult the LlamaIndex documentation [#f1]_.

    :raises: `NotImplementedError`: Please install required `LlamaIndex`_ package.
    :returns: a `pdf_markdown_reader.PDFMarkdownReader` and issues message "Successfully imported LlamaIndex". Please note that this method needs several seconds to execute. For details on using the markdown reader please see below.

----


.. class:: pdf_markdown_reader.PDFMarkdownReader
   
    .. method:: load_data(file_path: Union[Path, str], extra_info: Optional[Dict] = None, **load_kwargs: Any) -> List[LlamaIndexDocument]

        This is the only method of the markdown reader you should currently use to extract markdown data. Please in any case ignore methods `aload_data()` and `lazy_load_data()`. Other methods like `use_doc_meta()` may or may not make sense. For more information, please consult the LlamaIndex documentation [#f1]_.

        Under the hood the method will execute `to_markdown()`.

        :returns: a list of `LlamaIndexDocument` documents - one for each page.


.. rubric:: Footnotes

.. [#f1] `LlamaIndex documentation <https://docs.llamaindex.ai/en/stable/>`_



.. include:: ../footer.rst

.. _LlamaIndex: https://pypi.org/project/llama-index/



