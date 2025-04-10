.. include:: ../header.rst



.. _pymupdf4llm-api:


API
===========================================================================

The |PyMuPDF4LLM| API
--------------------------


.. property:: version

    Prints the version of the library.

.. method:: to_markdown(doc: pymupdf.Document | str, *, pages: list | range | None = None, hdr_info: Any = None, write_images: bool = False, embed_images: bool = False, ignore_images: bool = False, ignore_graphics: bool = False, dpi: int = 150, filename=None, image_path="", image_format="png", image_size_limit=0.05, force_text=True, margins=0, page_chunks: bool = False, page_width: float = 612, page_height: float = None, table_strategy="lines_strict", graphics_limit: int = None, ignore_code: bool = False, extract_words: bool = False, show_progress: bool = False, use_glyphs=False) -> str | list[dict]

    Read the pages of the file and outputs the text of its pages in |Markdown| format. How this should happen in detail can be influenced by a number of parameters. Please note that there exists **support for building page chunks** from the |Markdown|  text.

    :arg Document,str doc: the file, to be specified either as a file path string, or as a |PyMuPDF| Document (created via `pymupdf.open`). In order to use `pathlib.Path` specifications, Python file-like objects, documents in memory etc. you **must** use a |PyMuPDF| Document.

    :arg list pages: optional, the pages to consider for output (caution: specify 0-based page numbers). If omitted all pages are processed.

    :arg hdr_info: optional. Use this if you want to provide your own header detection logic. This may be a callable or an object having a method named `get_header_id`. It must accept a text span (a span dictionary as contained in :meth:`~.extractDICT`) and a keyword parameter "page" (which is the owning :ref:`Page <page>` object). It must return a string "" or up to 6 "#" characters followed by 1 space. If omitted, a full document scan will be performed to find the most popular font sizes and derive header levels based on them. To completely avoid this behavior specify `hdr_info=lambda s, page=None: ""` or `hdr_info=False`.

    :arg bool write_images: when encountering images or vector graphics, images will be created from the respective page area and stored in the specified folder. Markdown references will be generated pointing to these images. Any text contained in these areas will not be included in the text output (but appear as part of the images). Therefore, if for instance your document has text written on full page images, make sure to set this parameter to `False`.

    :arg bool embed_images: like `write_images`, but images will be included in the markdown text as base64-encoded strings. Ignores `write_images` and `image_path` if used. This may drastically increase the size of your markdown text.

    :arg bool ignore_images: (New in v.0.0.20) Disregard images on the page. This may help detecting text correctly when pages are very crowded (often the case for documents representing presentation slides). Also speeds up processing time.

    :arg bool ignore_graphics: (New in v.0.0.20) Disregard vector graphics on the page. This may help detecting text correctly when pages are very crowded (often the case for documents representing presentation slides). Also speeds up processing time. Vector graphics are still used for table detection.

    :arg float image_size_limit: this must be a positive value less than 1. Images are ignored if `width / page.rect.width <= image_size_limit` or `height / page.rect.height <= image_size_limit`. For instance, the default value 0.05 means that to be considered for inclusion, an image's width and height must be larger than 5% of the page's width and height, respectively.

    :arg int dpi: specify the desired image resolution in dots per inch. Relevant only if `write_images=True`. Default value is 150.

    :arg str image_path: store images in this folder. Relevant if `write_images=True`. Default is the path of the script directory.

    :arg str image_format: specify the desired image format via its extension. Default is "png" (portable network graphics). Another popular format may be "jpg". Possible values are all :ref:`supported output formats <Supported_File_Types>`.

    :arg bool force_text: generate text output even when overlapping images / graphics. This text then appears after the respective image. If `write_images=True` this parameter may be `False` to suppress repetition of text on images.

    :arg float,list margins: a float or a sequence of 2 or 4 floats specifying page borders. Only objects inside the margins will be considered for output.

        * `margin=f` yields `(f, f, f, f)` for `(left, top, right, bottom)`.
        * `(top, bottom)` yields  `(0, top, 0, bottom)`.
        * To always read full pages **(default)**, use `margins=0`.

    :arg bool page_chunks: if `True` the output will be a list of `Document.page_count` dictionaries (one per page). Each dictionary has the following structure:

        - **"metadata"** - a dictionary consisting of the document's metadata :attr:`Document.metadata`, enriched with additional keys **"file_path"** (the file name), **"page_count"** (number of pages in document), and **"page_number"** (1-based page number).

        - **"toc_items"** - a list of Table of Contents items pointing to this page. Each item of this list has the format `[lvl, title, pagenumber]`, where `lvl` is the hierarchy level, `title` a string and `pagenumber` as a 1-based page number.

        - **"tables"** - a list of tables on this page. Each item is a dictionary with keys "bbox", "row_count" and "col_count". Key "bbox" is a `pymupdf.Rect` in tuple format of the table's position on the page.

        - **"images"** - a list of images on the page. This a copy of page method :meth:`Page.get_image_info`.

        - **"graphics"** - a list of vector graphics rectangles on the page. This is a list of boundary boxes of clustered vector graphics as delivered by method :meth:`Page.cluster_drawings`.

        - **"text"** - page content as |Markdown| text.

        - **"words"** - if `extract_words=True` was used. This is a list of tuples `(x0, y0, x1, y1, "wordstring", bno, lno, wno)` as delivered by `page.get_text("words")`. The **sequence** of these tuples however is the same as produced in the markdown text string and thus honors multi-column text. This is also true for text in tables: words are extracted in the sequence of table row cells.

    :arg str filename: (New in v.0.0.19) Overwrites or sets the desired image file name of written images. Useful when the document is provided as a memory object (which has no inherent file name).
    
    :arg float page_width: specify a desired page width. This is ignored for documents with a fixed page width like PDF, XPS etc. **Reflowable** documents however, like e-books, office [#f2]_ or text files have no fixed page dimensions and by default are assumed to have Letter format width (612) and an **"infinite"** page height. This means that the **full document is treated as one large page.**

    :arg float page_height: specify a desired page height. For relevance see the `page_width` parameter. If using the default `None`, the document will appear as one large page with a width of `page_width`. Consequently in this case, no markdown page separators will occur (except the final one), respectively only one page chunk will be returned.

    :arg str table_strategy: `table detection strategy <https://pymupdf.readthedocs.io/en/latest/page.html#Page.find_tables>`_. Default is `"lines_strict"` which ignores background colors. In some occasions, other strategies may be more successful, for example `"lines"` which uses all vector graphics objects for detection.  **Changed in v0.0.19:** A value of `None` will not perform any table detection at all. This may be useful when you know that your document contains no tables. Execution time savings can be significant.

    :arg int graphics_limit: use this to limit dealing with excess amounts of vector graphics elements. Scientific documents, or pages simulating text via graphics commands may contain tens of thousands of these objects. As vector graphics are analyzed for multiple purposes, runtime may quickly become intolerable. With this parameter, all vector graphics will be ignored if their count exceeds the threshold. **Changed in v0.0.19:** The page will still be processed, and text, tables and images should be extracted.

    :arg bool ignore_code: if `True` then mono-spaced text does not receive special formatting. Code blocks will no longer be generated. This value is set to `True` if `extract_words=True` is used.

    :arg bool extract_words: a value of `True` enforces `page_chunks=True` and adds key "words" to each page dictionary. Its value is a list of words as delivered by PyMuPDF's `Page` method `get_text("words")`. The sequence of the words in this list is the same as the extracted text.

    :arg bool show_progress: Default is `False`. A value of `True` displays a text-based progress bar as pages are being converted to Markdown. It will look similar to the following::

        Processing input.pdf...
        [====================                    ] (148/291)

    :arg bool use_glyphs: (New in v.0.0.19) Default is `False`. A value of `True` will use the glyph number of the characters instead of the character itself.
    
    :returns: Either a string of the combined text of all selected document pages, or a list of dictionaries.

.. method:: LlamaMarkdownReader(*args, **kwargs)

    Create a `pdf_markdown_reader.PDFMarkdownReader` using the `LlamaIndex`_ package. Please note that this package will **not automatically be installed** when installing **pymupdf4llm**.

    For details on the possible arguments, please consult the LlamaIndex documentation [#f1]_.

    :raises: `NotImplementedError`: Please install required `LlamaIndex`_ package.
    :returns: a `pdf_markdown_reader.PDFMarkdownReader` and issues message "Successfully imported LlamaIndex". Please note that this method needs several seconds to execute. For details on using the markdown reader please see below.

----


.. class:: IdentifyHeaders

    .. method:: __init__(self, doc: pymupdf.Document | str, *, pages: list | range | None = None, body_limit: float = 11, max_levels: int = 6)

        Create an object which maps text font sizes to the respective number of '#' characters which are used by Markdown syntax to indicate header levels. The object is created by scanning the document for font size "popularity". The most popular font size and all smaller sizes are used for body text. Larger font sizes are mapped to the respective header levels - which correspond to the HTML tags `<h1>` to `<h6>`.

        All font sizes are rounded to integer values.

        If more than 6 header levels would be required, then the largest number smaller than the `<h6>` font size is used for body text.

        Please note that creating the object will read and inspect the text of the entire document - independently of reading the document again in the `to_markdown()` method subsequently. Method `to_markdown()` by default **will create this object** if you do not override its `hdr_info=None` parameter.
        

        :arg Document,str doc: the file, to be specified either as a file path string, or as a |PyMuPDF| Document (created via `pymupdf.open`). In order to use `pathlib.Path` specifications, Python file-like objects, documents in memory etc. you **must** use a |PyMuPDF| Document.

        :arg list pages: optional, the pages to consider. If omitted all pages are processed.

        :arg float body_limit: the default font size limit for body text. Only used when the document scan does not deliver valid information.

        :arg int max_levels: the maximum number of header levels to be used. Valid values are in `range(1, 7)`. The default is 6, which corresponds to the HTML tags `<h1>` to `<h6>`. A smaller value will limit the number of generated header levels. For instance, a value of 3 will only generate header tags "#", "##" and "###". Body text will be assumed for all font sizes smaller than the one corresponding to "###".


    .. method:: get_header_id(self, span: dict, page=None) -> str
    
        Return appropriate markdown header prefix. This is either "" or a string of "#" characters followed by a space.

        Given a text span from a "dict"" extraction, determine the
        markdown header prefix string of 0 to n concatenated '#' characters.

        :arg dict span: a dictionary containing the text span information. This is the same dictionary as returned by `page.get_text("dict")`.

        :arg Page page: the owning page object. This can be used when additional information needs to be extracted.

        :returns: a string of "#" characters followed by a space.

    .. attribute:: header_id
    
        A dictionary mapping (integer) font sizes to Markdown header strings like ``{14: '# ', 12: '## '}``. The dictionary is created by the `IdentifyHeaders` constructor. The keys are the font sizes of the text spans in the document. The values are the respective header strings.

     .. attribute:: body_limit

        An integer value indicating the font size limit for body text. This is computed as ``min(header_id.keys()) - 1``. In the above example, body_limit would be 11.


    **How to limit header levels (example)**
    
    Limit the generated header levels to 3::

        import pymupdf, pymupdf4llm

        filename = "input.pdf"
        doc = pymupdf.open(filename)  # use a Document for subsequent processing
        my_headers = pymupdf4llm.IdentifyHeaders(doc, max_levels=3)  # generate header info
        md_text = pymupdf4llm.to_markdown(doc, hdr_info=my_headers)


    **How to provide your own header logic (example 1)**
    
    Provide your own function which uses pre-determined, fixed font sizes::

        import pymupdf, pymupdf4llm

        filename = "input.pdf"
        doc = pymupdf.open(filename)  # use a Document for subsequent processing

        def my_headers(span, page=None):
            """
            Provide some custom header logic.
            This is a callable which accepts a text span and the page.
            Could be extended to check for other properties of the span, for
            instance the font name, text color and other attributes.
            """
            # header level is h1 if font size is larger than 14
            # header level is h2 if font size is larger than 10
            # otherwise it is body text
            if span["size"] > 14:
                return "# "
            elif span["size"] > 10:
                return "## "
            else:
                return ""
        
        # this will *NOT* scan the document for font sizes!
        md_text = pymupdf4llm.to_markdown(doc, hdr_info=my_headers)

    **How to provide your own header logic (example 2)**
    
    This user function uses the document's Table of Contents -- under the assumption that the bookmark text is also present as a header line on the page (which certainly need not be the case!)::

        import pymupdf, pymupdf4llm

        filename = "input.pdf"
        doc = pymupdf.open(filename)  # use a Document for subsequent processing
        TOC = doc.get_toc()  # use the table of contents for determining headers

        def my_headers(span, page=None):
            """
            Provide some custom header logic (experimental!).
            This callable checks whether the span text matches any of the
            TOC titles on this page.
            If so, use TOC hierarchy level as header level.
            """
            # TOC items on this page:
            toc = [t for t in TOC if t[-1] == page.number + 1]

            if not toc:  # no TOC items on this page
                return ""

            # look for a match in the TOC items
            for lvl, title, _ in toc:
                if span["text"].startswith(title):
                    return "#" * lvl + " "
                if title.startswith(span["text"]):
                    return "#" * lvl + " "
            
            return ""
        
        # this will *NOT* scan the document for font sizes!
        md_text = pymupdf4llm.to_markdown(doc, hdr_info=my_headers)

----


.. class:: pdf_markdown_reader.PDFMarkdownReader

    .. method:: load_data(file_path: Union[Path, str], extra_info: Optional[Dict] = None, **load_kwargs: Any) -> List[LlamaIndexDocument]

        This is the only method of the markdown reader you should currently use to extract markdown data. Please in any case ignore methods `aload_data()` and `lazy_load_data()`. Other methods like `use_doc_meta()` may or may not make sense. For more information, please consult the LlamaIndex documentation [#f1]_.

        Under the hood the method will execute `to_markdown()`.

        :returns: a list of `LlamaIndexDocument` documents - one for each page.

-----

For a list of changes, please see file `CHANGES.md <https://github.com/pymupdf/RAG/blob/main/CHANGES.md>`_.

.. rubric:: Footnotes

.. [#f1] `LlamaIndex documentation <https://docs.llamaindex.ai/en/stable/>`_

.. [#f2] When using PyMuPDF-Pro, supported office documents are converted internally into a PDF-like format. Therefore, they **will have fixed page dimensions** and be no longer "reflowable". Consequently, the page width and page height specifications will be ignored as well in these cases.




.. include:: ../footer.rst

.. _LlamaIndex: https://pypi.org/project/llama-index/



