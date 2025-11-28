.. include:: ../header.rst



.. _pymupdf4llm-api:


API
===========================================================================

The |PyMuPDF4LLM| API
--------------------------


.. property:: version

    Prints the version of the library.

.. method:: to_markdown(doc: pymupdf.Document | str, *, \
    detect_bg_color: bool = True, \
    dpi: int = 150, \
    ocr_dpi: int = 400, \
    embed_images: bool = False, \
    extract_words: bool = False, \
    filename: str | None = None, \
    fontsize_limit: float = 3, \
    footer: bool = True, \
    force_text: bool = True, \
    graphics_limit: int = None, \
    hdr_info: Any = None, \
    header: bool = True, \
    ignore_alpha: bool = False, \
    ignore_code: bool = False, \
    ignore_graphics: bool = False, \
    ignore_images: bool = False, \
    image_format: str = "png", \
    image_path: str = "", \
    image_size_limit: float = 0.05, \
    margins: int = 0, \
    page_chunks: bool = False, \
    page_height: float = None, \
    page_separators: bool = False, \
    page_width: float = 612, \
    pages: list | range | None = None, \
    show_progress: bool = False, \
    table_strategy: str = "lines_strict", \
    use_glyphs: bool = False, \
    write_images: bool = False) -> str | list[dict]

    Reads the pages of the file and outputs the text of its pages in |Markdown| format. How this should happen in detail can be influenced by a number of parameters. Please note that **support for building page chunks** from the |Markdown| text is supported.

    :arg Document,str doc: the file, to be specified either as a file path string, or as a |PyMuPDF| :class:`Document` (created via `pymupdf.open`). In order to use `pathlib.Path` specifications, Python file-like objects, documents in memory etc. you **must** use a |PyMuPDF| :class:`Document`.

    :arg bool detect_bg_color: does a simple check for the general background color of the pages (default is ``True``). If any text or vector has this color it will be ignored. May increase detection accuracy. **Ignored in "layout mode".**

    :arg int dpi: specify the desired image resolution in dots per inch. Relevant only if `write_images=True` or `embed_images=True`. Default value is 150.

    :arg int ocr_dpi: specify the desired image resolution in dots per inch for applying OCR to the intermdeiate image of the page. Default value is 400. Only relevant if the page has been determined to profit from OCR (no or few text, most of the page covered by images or character-like vectors, etc.). Large values may increase the OCR precison but increase memory requirements and processing time. There also is a risk of over-sharpening the image which may decrease OCR precision. So the default value should probably be sufficiently high. **Only valid in "layout mode".**

    :arg bool embed_images: like `write_images`, but images will be included in the markdown text as base64-encoded strings. Mutually exclusive with `write_images` and ignores `image_path`. This may drastically increase the size of your markdown text.

    :arg bool extract_words: a value of `True` enforces `page_chunks=True` and adds key "words" to each page dictionary. Its value is a list of words as delivered by PyMuPDF's `Page` method `get_text("words")`. The sequence of the words in this list is the same as the extracted text. **Ignored in "layout mode".**

    :arg str filename: Overwrites or sets the desired image file name of written images. Useful when the document is provided as a memory object (which has no inherent file name).

    :arg float fontsize_limit: limit the font size to consider for text extraction. If the font size is lower than what is set then the text won't be considered for extraction. Default is `3`, meaning only text with a font size `>= 3` will be considered for extraction. **Ignored in "layout mode".**

    :arg bool footer: boolean to switch on/off page footer content. This parameter controls whether to include or omit footer text from all the document pages. Useful if the document has repetitive footer content which doesn't add any value to the overall extraction data. Default is `True` meaning that footer content will be considered. **Only valid in "layout mode".**

    :arg bool force_text: generate text output even when overlapping images / graphics. This text then appears after the respective image.

    :arg int graphics_limit: use this to limit dealing with excess amounts of vector graphics elements. Scientific documents, or pages simulating text via graphics commands may contain tens of thousands of these objects. As vector graphics are analyzed for multiple purposes, runtime may quickly become intolerable. With this parameter, all vector graphics will be ignored if their count exceeds the threshold. **Ignored in "layout mode".**

    :arg hdr_info: use this if you want to provide your own header detection logic. This may be a callable or an object having a method named `get_header_id`. It must accept a text span (a span dictionary as contained in :meth:`~.extractDICT`) and a keyword parameter "page" (which is the owning :ref:`Page <page>` object). It must return a string "" or up to 6 "#" characters followed by 1 space. If omitted (`None`), a full document scan will be performed to find the most popular font sizes and derive header levels based on them. To completely avoid this behavior specify `hdr_info=lambda s, page=None: ""` or `hdr_info=False`. **Ignored in "layout mode".**

    :arg bool header: boolean to switch on/off page header content. This parameter controls whether we want to include or omit the header content from all the document pages. Useful if the document has repetitive header content which doesn't add any value to the overall extraction data. Default is `True` meaning that header content will be considered. **Only valid in "layout mode".**

    :arg bool ignore_alpha: if ``True`` includes text even when completely transparent. Default is ``False``: transparent text will be ignored which usually increases detection accuracy. **Ignored in "layout mode".**

    :arg bool ignore_code: if `True` then mono-spaced text lines do not receive special formatting. Code blocks will no longer be generated. This value is set to `True` if `extract_words=True` is used.

    :arg bool ignore_graphics: (New in v.0.0.20) Disregard vector graphics on the page. This may help detecting text correctly when pages are very crowded (often the case for documents representing presentation slides). Also speeds up processing time. This automatically prevents table detection. **Ignored in "layout mode".**

    :arg bool ignore_images: (New in v.0.0.20) Disregard images on the page. This may help detecting text correctly when pages are very crowded (often the case for documents representing presentation slides). Also speeds up processing time. **Ignored in "layout mode".**

    :arg str image_format: specify the desired image format via its extension. Default is "png" (portable network graphics). Another popular format may be "jpg". Possible values are all :ref:`supported output formats <Supported_File_Types>`.

    :arg str image_path: store images in this folder. Relevant if `write_images=True`. Default is the path of the script directory.

    :arg float image_size_limit: this must be a ``0 <= value < 1``. Images are ignored if `width / page.rect.width <= image_size_limit` or `height / page.rect.height <= image_size_limit`. For instance, the default value 0.05 means that to be considered for inclusion, an image's width and height must be larger than 5% of the page's width and height, respectively. **Ignored in "layout mode".**

    :arg float,list margins: a float or a sequence of 2 or 4 floats specifying page borders. Only objects inside the margins will be considered for output. **Ignored in "layout mode".**

        * `margin=f` yields `(f, f, f, f)` for `(left, top, right, bottom)`.
        * `(top, bottom)` yields  `(0, top, 0, bottom)`.
        * To always read full pages **(default)**, use `margins=0`.

    :arg bool page_chunks: if `True` the output will be a list of `Document.page_count` dictionaries (one per page). Each dictionary has the following structure:

        - **"metadata"** - a dictionary consisting of the document's metadata :attr:`Document.metadata`, enriched with additional keys **"file_path"** (the file name), **"page_count"** (number of pages in document), and **"page_number"** (1-based page number).

        - **"toc_items"** - a list of Table of Contents items pointing to this page. Each item of this list has the format `[lvl, title, pagenumber]`, where `lvl` is the hierarchy level, `title` a string and `pagenumber` as a 1-based page number.

        - **"tables"** - a list of tables on this page. Each item is a dictionary with keys "bbox", "row_count" and "col_count". Key "bbox" is a `pymupdf.Rect` in tuple format of the table's position on the page.

        - **"images"** - a list of images on the page. This a copy of page method :meth:`Page.get_image_info`. **Empty list in "layout mode".**

        - **"graphics"** - a list of vector graphics rectangles on the page. This is a list of boundary boxes of clustered vector graphics as delivered by method :meth:`Page.cluster_drawings`. **Empty list in "layout mode".**

        - **"text"** - page content as |Markdown| text.

        - **"words"** - if `extract_words=True` was used. This is a list of tuples `(x0, y0, x1, y1, "wordstring", bno, lno, wno)` as delivered by `page.get_text("words")`. The **sequence** of these tuples however is the same as produced in the markdown text string and thus honors multi-column text. This is also true for text in tables: words are extracted in the sequence of table row cells. **Empty list in "layout mode".**

    :arg float page_height: specify a desired page height. For relevance see the `page_width` parameter. If using the default `None`, the document will appear as one large page with a width of `page_width`. Consequently in this case, no markdown page separators will occur (except the final one), respectively only one page chunk will be returned.

    :arg bool page_separators: if ``True`` inserts a string ``--- end of page=n ---`` at the end of each page output. Intended for debugging purposes. The page number is 0-based. The separator string is wrapped with line breaks. Default is ``False``.

    :arg float page_width: specify a desired page width. This is ignored for documents with a fixed page width like PDF, XPS etc. **Reflowable** documents however, like e-books, office [#f2]_ or text files have no fixed page dimensions. They by default are assumed to have Letter format width (612) and an **unlimited** page height. This means that the **full document is treated as one large page.**

    :arg list pages: optional, the pages to consider for output (caution: specify 0-based page numbers). If omitted (`None`) all pages are processed. Any Python sequence with integer items is accepted. The sequence is sorted and processed to only contain unique items.

    :arg bool show_progress: Default is `False`. A value of `True` displays a progress bar as pages are being converted. Package `tqdm <https://pypi.org/project/tqdm/>`_ is used if installed, otherwise the built-in text based progress bar is used.

    :arg str table_strategy: see: :meth:`table detection strategy <Page.find_tables>`. Default is `"lines_strict"` which ignores background colors. In some occasions, other strategies may be more successful, for example `"lines"` which uses all vector graphics objects for detection. **Ignored in "layout mode".**

    :arg bool use_glyphs: (New in v.0.0.19) Default is `False`. A value of `True` will use the glyph number of the characters instead of the character itself if the font does not store the Unicode value. **Ignored in "layout mode".**

    :arg bool write_images: when encountering images or vector graphics, images will be created from the respective page area and stored in the specified folder. |Markdown| references will be generated pointing to these images. Any text contained in these areas will not be included in the text output (but appear as part of the images). Therefore, if for instance your document has text written on full page images, make sure to set this parameter to `False`.

        In "layout mode", boundary boxes that are classified as "picture" by the layout module will be treated as images - independent from the mixture of text, images or vector graphics they may be covering. If `force_text=True` is used, text will still be extracted from these areas and included in the output  after the respective image reference.

    :returns: Either a string of the combined text of all selected document pages, or a list of dictionaries if `page_chunks=True`.


.. method:: to_text(doc: pymupdf.Document | str, *, **kwargs) -> str


    Reads the pages of the file and outputs the text of its pages in |TXT| format.

    .. important:: This method is only available in "layout mode", i.e. if the import of pymupdf4llm has happened **after** the statement ``import pymupdf.layout`` 

    :arg Document,str doc: the file, to be specified either as a file path string, or as a |PyMuPDF| :class:`Document` (created via `pymupdf.open`). In order to use `pathlib.Path` specifications, Python file-like objects, documents in memory etc. you **must** use a |PyMuPDF| :class:`Document`.

    :arg bool header: boolean to switch on/off page header content. This parameter controls whether to include or omit the header content from all the document pages. Useful if the document has repetitive header content which doesn't add any value to the overall extraction data. Default is `True` meaning that header content will be written.

    :arg bool footer: boolean to switch on/off page footer content. This parameter controls whether to include or omit the footer content from all the document pages. Useful if the document has repetitive footer content which doesn't add any value to the overall extraction data. Default is `True` meaning that footer content will be written.

    :arg bool ignore_code: if `True` then mono-spaced text lines do not receive special formatting. No blocks will be written and text lines will be written continuously.

    :arg list pages: optional, the pages to consider for output (caution: specify 0-based page numbers). If omitted (`None`) all pages are processed. Any Python sequence with integer items is accepted. The sequence is sorted and processed to only contain unique items.

    :arg bool force_text: generate text output also when overlapping images / graphics. This text then appears after the respective image reference. Images (i.e. "picture" areas) however will not be written to the text output but appear as a text line in the output like `==> picture [width x height] <==`.

    :arg bool show_progress: Default is `False`. A value of `True` displays a progress bar as pages are being converted. Package `tqdm <https://pypi.org/project/tqdm/>`_ is used if installed, otherwise the built-in text based progress bar is used.
    

.. method:: to_json(doc: pymupdf.Document | str, *, **kwargs) -> str

    Parses the document and the specified pages and converts the result into a |JSON|-formatted string.
    
    .. important:: This method is only available in "layout mode", i.e. if the import of pymupdf4llm has happened **after** the statement ``import pymupdf.layout`` 

    :arg Document,str doc: the file, to be specified either as a file path string, or as a |PyMuPDF| :class:`Document` (created via `pymupdf.open`). In order to use `pathlib.Path` specifications, Python file-like objects, documents in memory etc. you **must** use a |PyMuPDF| :class:`Document`.

    :arg int image_dpi: specify the desired image resolution in dots per inch. Default value is 150. Only relevant if one of the parameters `write_images=True` or `embed_images=True` is used.

    :arg str image_format: specify the desired image format via its extension. Default is "png" (portable network graphics). Another popular format may be "jpg". Possible values are all :ref:`supported output formats <Supported_File_Types>`. Only relevant if one of the parameters `write_images=True` or `embed_images=True` is used.

    :arg str image_path: store images in this folder. Relevant if `write_images=True`. Default is the path of the script directory. Page areas classified as "picture" will be written as image files to the specified location. The image file names will be of the format `{image_path}/{filename}-pagenumber-image_number.{image_format}`.

    :arg bool force_text: generate text output for text that is written upon areas that are classified as "picture" by the layout module. This may be especially be useful when picture content is not stored.

    :arg bool show_progress: display a progress bar during processing.

    :arg bool embed_images: store image binaries for "picture" boundary boxes. Base64-encoded images are included in the JSON output. Ignores `image_path` if used. This may drastically increase the size of your JSON text.

    :arg bool write_images: store image files "picture" boundary boxes.when encountering images, image files will be created from the respective page area and stored in the specified folder. Any text contained in these areas will still be included in the text output.

    :arg list pages: optional, the pages to consider for output (caution: specify 0-based page numbers). If omitted (`None`) all pages are processed. Specify any valid Python sequence containing integers between `0` and `page_count - 1`.


.. note::

    Please see `this site <https://github.com/pymupdf/pymupdf4llm/discussions/327>`_ for more background and the current status of further improvements regarding layout mode.


.. method:: LlamaMarkdownReader(*args, **kwargs)

    Create a `pdf_markdown_reader.PDFMarkdownReader` using the `LlamaIndex`_ package. Please note that this package will **not automatically be installed** when installing **pymupdf4llm**.

    For details on the possible arguments, please consult the LlamaIndex documentation [#f1]_.

    :raises: `NotImplementedError`: Please install required `LlamaIndex`_ package.
    :returns: a `pdf_markdown_reader.PDFMarkdownReader` and issues message "Successfully imported LlamaIndex". Please note that this method needs several seconds to execute. For details on using the markdown reader please see below.

----


.. class:: IdentifyHeaders

    .. note:: This class is not available in "layout mode", i.e. if the import of pymupdf4llm has happened **after** the statement ``import pymupdf.layout``.

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

        Given a text span from a "dict" extraction, determine the markdown header prefix string of 0 to n concatenated '#' characters.

        :arg dict span: a dictionary containing the text span information. This is the same dictionary as returned by `page.get_text("dict")`.

        :arg Page page: the owning page object. This can be used when additional information needs to be extracted.

        :returns: a string of "#" characters followed by a space.

    .. attribute:: header_id
    
        A dictionary mapping (integer) font sizes to Markdown header strings like ``{14: '# ', 12: '## '}``. The dictionary is created by the :class:`IdentifyHeaders` constructor. The keys are the font sizes of the text spans in the document. The values are the respective header strings.

    .. attribute:: body_limit

        An integer value indicating the font size limit for body text. This is computed as ``min(header_id.keys()) - 1``. In the above example, body_limit would be 11.


----


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


.. class:: TocHeaders

    .. note:: This class is not available in "layout mode", i.e. if the import of pymupdf4llm has happened **after** the statement ``import pymupdf.layout``.

    .. method:: __init__(self, doc: pymupdf.Document | str)

        Create an object which uses the document's Table of Contents (TOC) to determine header levels. Upon object creation, the table of contents is read via the `Document.get_toc()` method. The TOC data is then used to determine header levels in the `to_markdown()` method.

        This is an alternative to :class:`IdentifyHeaders`. Instead of running through the full document to identify font sizes, it uses the document's Table Of Contents (TOC) to identify headers on pages. Like :class:`IdentifyHeaders`, this also is no guarantee to find headers, but for well-built Table of Contents, there is a good chance for more correctly identifying header lines on document pages than the font-size-based approach.

        It also has the advantage of being much faster than the font-size-based approach, as it does not execute a full document scan or even access any of the document pages.

        Examples where this approach works very well are the Adobe's files on PDF documentation.

        Please note that this feature **does not read document pages** where the table of contents may exist as normal standard text. It only accesses data as provided by the `Document.get_toc()` method. It will not identify any headers for documents where the table of contents is not available as a collection of bookmarks.

    .. method:: get_header_id(self, span: dict, page=None) -> str
    
        Return appropriate markdown header prefix. This is either an empty string or a string of "#" characters followed by a space.

        Given a text span from a "dict" extraction variant, determine the markdown header prefix string of 0 to n concatenated "#" characters.

        :arg dict span: a dictionary containing the text span information. This is the same dictionary as returned by `page.get_text("dict")`.

        :arg Page page: the owning page object. This can be used when additional information needs to be extracted.

        :returns: a string of "#" characters followed by a space.



**How to use class TocHeaders**

This is a version of previous **example 2** that uses :class:`TocHeaders` for header identification::

    import pymupdf, pymupdf4llm

    filename = "input.pdf"

    doc = pymupdf.open(filename)  # use a Document for subsequent processing
    my_headers = pymupdf4llm.TocHeaders(doc)  # use the table of contents for determining headers
    
    # this will *NOT* scan the document for font sizes!
    md_text = pymupdf4llm.to_markdown(doc, hdr_info=my_headers)

-----

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



