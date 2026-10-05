.. include:: ../header.rst


.. |PyMuPDFLayoutMode_Ignored| raw:: html

    <cite style="font-size:12px;color:#c0c0c0;background:transparent;border:1px solid #c0c0c0;border-radius:5px;padding:3px;"><a href="#pymupdf4llm-api-layout">use_layout()</a> must be <span style="font-family:monospace;">False</span></cite>

.. |PyMuPDFLayoutMode_Valid| raw:: html

    <span></span>

.. |PyMuPDFLayoutMode_EmptyList| raw:: html

    <cite style="font-size:12px;color:#c0c0c0;background:transparent;border:1px solid #c0c0c0;border-radius:5px;padding:3px;">Only if <a href="#pymupdf4llm-api-layout">use_layout()</a> is <span style="font-family:monospace;">False</span></cite>

.. |PyMuPDFLayoutMode_Unavailable| raw:: html

    <cite style="font-size:12px;color:#c0c0c0;background:transparent;border:1px solid #c0c0c0;border-radius:5px;padding:3px;">Only if <a href="#pymupdf4llm-api-layout">use_layout()</a> is <span style="font-family:monospace;">False</span></cite>

.. _pymupdf4llm-api:




The PyMuPDF4LLM API
===========================================================================


.. property:: version

    Prints the version of the library.


.. method:: to_markdown(doc: pymupdf.Document | str, *, \
    detect_bg_color: bool = True, \
    dpi: int = 150, \
    embed_images: bool = False, \
    extract_words: bool = False, \
    filename: str | None = None, \
    fontsize_limit: float = 3, \
    footer: bool = True, \
    force_ocr: bool = False, \
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
    margins: float | list = 0, \
    ocr_dpi: int = 300, \
    ocr_function: callable = None, \
    ocr_language: str = "eng", \
    page_chunks: bool = False, \
    page_height: float = None, \
    page_separators: bool = False, \
    page_width: float = 612, \
    pages: list | range | None = None, \
    show_progress: bool = False, \
    table_strategy: str = "lines_strict", \
    use_glyphs: bool = False, \
    use_ocr: bool = True, \
    write_images: bool = False) -> str | list[dict]

    Reads the pages of the file and outputs the text of its pages in |Markdown| format. How this should happen in detail can be influenced by a number of parameters. Please note that **support for building page chunks** from the |Markdown| text is supported.

    :arg Document,str doc: the file, to be specified either as a file path string, or as a |PyMuPDF| :class:`Document` (created via `pymupdf.open`). In order to use `pathlib.Path` specifications, Python file-like objects, documents in memory etc. you **must** use a |PyMuPDF| :class:`Document`.

    :arg bool detect_bg_color: |PyMuPDFLayoutMode_Ignored| does a simple check for the general background color of the pages (default is ``True``). If any text or vector has this color it will be ignored. May increase detection accuracy.

    :arg int dpi: specify the desired image resolution in dots per inch. Relevant only if `write_images=True` or `embed_images=True`. Default value is 150.

    :arg bool embed_images: like `write_images`, but images will be included in the markdown text as base64-encoded strings. Mutually exclusive with `write_images` and ignores `image_path`. This may drastically increase the size of your markdown text.

    :arg bool extract_words: |PyMuPDFLayoutMode_Ignored| a value of `True` enforces `page_chunks=True` and adds key "words" to each page dictionary. Its value is a list of words as delivered by PyMuPDF's `Page` method `get_text("words")`. The sequence of the words in this list is the same as the extracted text.

    :arg str filename: Overwrites or sets the desired image file name of written images. Useful when the document is provided as a memory object (which has no inherent file name).

    :arg float fontsize_limit: |PyMuPDFLayoutMode_Ignored| limit the font size to consider for text extraction. If the font size is lower than what is set then the text won't be considered for extraction. Default is `3`, meaning only text with a font size `>= 3` will be considered for extraction.

    :arg bool footer: |PyMuPDFLayoutMode_Valid| boolean to switch on/off page footer content. This parameter controls whether to include or omit footer text from all the document pages. Useful if the document has repetitive footer content which doesn't add any value to the overall extraction data. Default is `True` meaning that footer content will be considered.

    :arg bool force_ocr: |PyMuPDFLayoutMode_Valid| if `True`, OCR will be applied to all pages regardless of their content.
        
        This may be useful for documents which are known to be image-based and thus profit from OCR, but which do not meet the default criteria for applying OCR. Default is `False` meaning that OCR will only be applied to pages which meet the default criteria.

        .. warning:: 
            Requires that either one of the default supported OCR engines is installed or `ocr_function` specifies a callable OCR function. Otherwise, an exception will be raised.

    :arg bool force_text: generate text output even when overlapping images / graphics. This text then appears after the respective image.

    :arg int graphics_limit: |PyMuPDFLayoutMode_Ignored| use this to limit dealing with excess amounts of vector graphics elements. Scientific documents, or pages simulating text via graphics commands may contain tens of thousands of these objects. As vector graphics are analyzed for multiple purposes, runtime may quickly become intolerable. With this parameter, all vector graphics will be ignored if their count exceeds the threshold.

    :arg hdr_info: |PyMuPDFLayoutMode_Ignored| use this if you want to provide your own header detection logic. This may be a callable or an object having a method named `get_header_id`. It must accept a text span (a span dictionary as contained in :meth:`~.extractDICT`) and a keyword parameter "page" (which is the owning :ref:`Page <page>` object). It must return a string "" or up to 6 "#" characters followed by 1 space. If omitted (`None`), a full document scan will be performed to find the most popular font sizes and derive header levels based on them. To completely avoid this behavior specify `hdr_info=lambda s, page=None: ""` or `hdr_info=False`.

    :arg bool header: |PyMuPDFLayoutMode_Valid| boolean to switch on/off page header content. This parameter controls whether we want to include or omit the header content from all the document pages. Useful if the document has repetitive header content which doesn't add any value to the overall extraction data. Default is `True` meaning that header content will be considered.

    :arg bool ignore_alpha: |PyMuPDFLayoutMode_Ignored| if ``True`` includes text even when completely transparent. Default is ``False``: transparent text will be ignored which usually increases detection accuracy.

    :arg bool ignore_code: if `True` then mono-spaced text lines do not receive special formatting. Code blocks will no longer be generated. This value is set to `True` if `extract_words=True` is used.

    :arg bool ignore_graphics: |PyMuPDFLayoutMode_Ignored| (New in v.0.0.20) Disregard vector graphics on the page. This may help detecting text correctly when pages are very crowded (often the case for documents representing presentation slides). Also speeds up processing time. This automatically prevents table detection.

    :arg bool ignore_images: |PyMuPDFLayoutMode_Ignored| (New in v.0.0.20) Disregard images on the page. This may help detecting text correctly when pages are very crowded (often the case for documents representing presentation slides). Also speeds up processing time.

    :arg str image_format: specify the desired image format via its extension. Default is "png" (portable network graphics). Another popular format may be "jpg". Possible values are all :ref:`supported output formats <Supported_File_Types>`.

    :arg str image_path: store images in this folder. Relevant if `write_images=True`. Default is the path of the script directory.

    :arg float image_size_limit: |PyMuPDFLayoutMode_Ignored| this must be a ``0 <= value < 1``. Images are ignored if `width / page.rect.width <= image_size_limit` or `height / page.rect.height <= image_size_limit`. For instance, the default value 0.05 means that to be considered for inclusion, an image's width and height must be larger than 5% of the page's width and height, respectively.

    :arg float,list margins: |PyMuPDFLayoutMode_Ignored| a float or a sequence of 2 or 4 floats specifying page borders. Only objects inside the margins will be considered for output.

        * `margin=f` yields `(f, f, f, f)` for `(left, top, right, bottom)`.
        * `(top, bottom)` yields  `(0, top, 0, bottom)`.
        * To always read full pages **(default)**, use `margins=0`.

    :arg int ocr_dpi: |PyMuPDFLayoutMode_Valid| specify the desired image resolution in dots per inch for applying OCR to the intermediate image of the page. Default value is 300. Only relevant if the page has been determined to profit from OCR (no or few text, most of the page covered by images or character-like vectors, etc.). Larger values do not usually increase the OCR precision. There also is a risk of over-sharpening the image which may decrease OCR precision. So the default value should probably be sufficiently high - in many cases you should see satisfactory results already with values of 150 or 200. Be aware that processing time and memory requirements grow quadratically with this value (an O(ocr_dpi²) impact). 

    :arg callable ocr_function: |PyMuPDFLayoutMode_Valid| if you want to provide your own :ref:`OCR function <pymupdf_layout_ocr_engines>`, specify it here. If omitted (`None`), one of the available built-in OCR engines will be used.

    :arg str ocr_language: |PyMuPDFLayoutMode_Valid| specify the language to be used by the Tesseract OCR engine. Default is "eng" (English). Make sure that the respective language data files are installed. Remember to use correct Tesseract language codes. Multiple languages can be specified by concatenating the respective codes with a plus sign "+", for example "eng+deu" for English and German.

    :arg bool page_chunks: if `True` the output will be a list of `Document.page_count` dictionaries (one per page). Each dictionary has the following structure:

        - **"metadata"** - a dictionary consisting of the document's metadata :attr:`Document.metadata`, enriched with additional keys **"file_path"** (the file name), **"page_count"** (number of pages in document), and **"page_number"** (1-based page number).

        - **"toc_items"** - a list of Table of Contents items pointing to this page. Each item of this list has the format `[lvl, title, pagenumber]`, where `lvl` is the hierarchy level, `title` a string and `pagenumber` as a 1-based page number.

        - **"tables"** - |PyMuPDFLayoutMode_EmptyList| a list of tables on this page. Each item is a dictionary with keys "bbox", "row_count" and "col_count". Key "bbox" is a `pymupdf.Rect` in tuple format of the table's position on the page.

        - **"images"** - |PyMuPDFLayoutMode_EmptyList| a list of images on the page. This a copy of page method :meth:`Page.get_image_info`.

        - **"graphics"** - |PyMuPDFLayoutMode_EmptyList| a list of vector graphics rectangles on the page. This is a list of boundary boxes of clustered vector graphics as delivered by method :meth:`Page.cluster_drawings`.

        - **"text"** - page content as |Markdown| text.

        - **"words"** - |PyMuPDFLayoutMode_EmptyList| if `extract_words=True` was used. This is a list of tuples `(x0, y0, x1, y1, "wordstring", bno, lno, wno)` as delivered by `page.get_text("words")`. The **sequence** of these tuples however is the same as produced in the markdown text string and thus honors multi-column text. This is also true for text in tables: words are extracted in the sequence of table row cells.

        - **"text"** - page content as |Markdown| text.

        - **"page_boxes"** - |PyMuPDFLayoutMode_Valid| a list of dictionaries representing the layout boundary boxes. Each dictionary has the following structure::

            {
                "index": int,              # 0-based integer index of the box in reading sequence
                "class": str,              # one of "text", "picture", "table", etc.
                "bbox": [x0, y0, x1, y1],  # boundary box coordinates
                "pos": (start, stop),      # 0-based integers: bbox_text = chunk["text"][start:stop]
            }

          See: :ref:`box classes <pymupdf4llm-api-boxclasses>`

    :arg float page_height: specify a desired page height. For relevance see the `page_width` parameter. If using the default `None`, the document will appear as one large page with a width of `page_width`. Consequently in this case, no markdown page separators will occur (except the final one), respectively only one page chunk will be returned.

    :arg bool page_separators: if ``True`` inserts a string ``--- end of page=n ---`` at the end of each page output. Intended for debugging purposes. The page number is 0-based. The separator string is wrapped with line breaks. Default is ``False``.

    :arg float page_width: specify a desired page width. This is ignored for documents with a fixed page width like PDF, XPS etc. **Reflowable** documents however, like e-books, office [#f2]_ or text files have no fixed page dimensions. They by default are assumed to have Letter format width (612) and an **unlimited** page height. This means that the **full document is treated as one large page.**

    :arg list pages: optional, the pages to consider for output (caution: specify 0-based page numbers). If omitted (`None`) all pages are processed. Any Python sequence with integer items is accepted. The sequence is sorted and processed to only contain unique items.

    :arg bool show_progress: Default is `False`. A value of `True` displays a progress bar as pages are being converted. Package `tqdm <https://pypi.org/project/tqdm/>`_ is used if installed, otherwise the built-in text based progress bar is used.

    :arg str table_strategy: |PyMuPDFLayoutMode_Ignored| see: :meth:`table detection strategy <Page.find_tables>`. Default is `"lines_strict"` which ignores background colors. In some occasions, other strategies may be more successful, for example `"lines"` which uses all vector graphics objects for detection.

    :arg bool use_glyphs: |PyMuPDFLayoutMode_Ignored| (New in v.0.0.19) Default is `False`. A value of `True` will use the glyph number of the characters instead of the character itself if the font does not store the Unicode value.

    :arg bool use_ocr: |PyMuPDFLayoutMode_Valid| use :ref:`OCR capability <pymupdf_layout_ocr_support>` to help analyse the page. This will OCR pages as determined by the default criteria.

    :arg bool write_images: when encountering images or vector graphics, images will be created from the respective page area and stored in the specified folder. |Markdown| references will be generated pointing to these images. Any text contained in these areas will not be included in the text output (but appear as part of the images). Therefore, if for instance your document has text written on full page images, make sure to set this parameter to `False`.

        If using :ref:`PyMuPDF Layout <pymupdf-layout>`, boundary boxes that are classified as "picture" by the layout module will be treated as images - independent from the mixture of text, images or vector graphics they may be covering. If `force_text=True` is used, text will still be extracted from these areas and included in the output  after the respective image reference.

    :returns: Either a string of the combined text of all selected document pages, or a list of dictionaries if `page_chunks=True`.




.. method:: to_json(doc: pymupdf.Document | str, *, **kwargs) -> str

    Parses the document and the specified pages and converts the result into a `JSON formatted string <https://docs.pdf4llm.com/python/reference/JSON-schema>`_.

    :arg Document,str doc: the file, to be specified either as a file path string, or as a |PyMuPDF| :class:`Document` (created via `pymupdf.open`). In order to use `pathlib.Path` specifications, Python file-like objects, documents in memory etc. you **must** use a |PyMuPDF| :class:`Document`.

    :arg bool use_ocr: |PyMuPDFLayoutMode_Valid| use :ref:`OCR capability <pymupdf_layout_ocr_support>` to help analyse the page.

    :arg str ocr_language: |PyMuPDFLayoutMode_Valid| specify the language to be used by the Tesseract OCR engine. Default is "eng" (English). Make sure that the respective language data files are installed. Remember to use correct Tesseract language codes. Multiple languages can be specified by concatenating the respective codes with a plus sign "+", for example "eng+deu" for English and German.

    :arg int ocr_dpi: |PyMuPDFLayoutMode_Valid| specify the desired image resolution in dots per inch for applying OCR to the intermediate image of the page. Default value is 400. Only relevant if the page has been determined to profit from OCR (no or few text, most of the page covered by images or character-like vectors, etc.). Large values may increase the OCR precision but increase memory requirements and processing time. There also is a risk of over-sharpening the image which may decrease OCR precision. So the default value should probably be sufficiently high.

    :arg int image_dpi: specify the desired image resolution in dots per inch. Default value is 150. Only relevant if one of the parameters `write_images=True` or `embed_images=True` is used.

    :arg str image_format: specify the desired image format via its extension. Default is "png" (portable network graphics). Another popular format may be "jpg". Possible values are all :ref:`supported output formats <Supported_File_Types>`. Only relevant if one of the parameters `write_images=True` or `embed_images=True` is used.

    :arg str image_path: store images in this folder. Relevant if `write_images=True`. Default is the path of the script directory. Page areas classified as "picture" will be written as image files to the specified location. The image file names will be of the format `{image_path}/{filename}-pagenumber-image_number.{image_format}`.

    :arg bool force_text: generate text output for text that is written upon areas that are classified as "picture" by the layout module. This may be especially be useful when picture content is not stored.

    :arg bool show_progress: display a progress bar during processing.

    :arg bool embed_images: store image binaries for "picture" boundary boxes. Base64-encoded images are included in the JSON output. Ignores `image_path` if used. This may drastically increase the size of your JSON text.

    :arg bool write_images: store image files "picture" boundary boxes. When encountering images, image files will be created from the respective page area and stored in the specified folder. Any text contained in these areas will still be included in the text output.

    :arg list pages: optional, the pages to consider for output (caution: specify 0-based page numbers). If omitted (`None`) all pages are processed. Specify any valid Python sequence containing integers between `0` and `page_count - 1`.

    :rtype: str

    See `JSON Schema <https://docs.pdf4llm.com/python/reference/JSON-schema>`_ for the structure of the output JSON string.



.. method:: to_text(doc: pymupdf.Document | str, *, **kwargs) -> str

    Reads the pages of the file and outputs the text of its pages in plain text (|TXT|) format.

    :arg Document,str doc: the file, to be specified either as a file path string, or as a |PyMuPDF| :class:`Document` (created via `pymupdf.open`). In order to use `pathlib.Path` specifications, Python file-like objects, documents in memory etc. you **must** use a |PyMuPDF| :class:`Document`.

    :arg bool use_ocr: |PyMuPDFLayoutMode_Valid| use :ref:`OCR capability <pymupdf_layout_ocr_support>` to help analyse the page.

    :arg str ocr_language: |PyMuPDFLayoutMode_Valid| specify the language to be used by the Tesseract OCR engine. Default is "eng" (English). Make sure that the respective language data files are installed. Remember to use correct Tesseract language codes. Multiple languages can be specified by concatenating the respective codes with a plus sign "+", for example "eng+deu" for English and German.

    :arg int ocr_dpi: |PyMuPDFLayoutMode_Valid| specify the desired image resolution in dots per inch for applying OCR to the intermediate image of the page. Default value is 400. Only relevant if the page has been determined to profit from OCR (no or few text, most of the page covered by images or character-like vectors, etc.). Large values may increase the OCR precision but increase memory requirements and processing time. There also is a risk of over-sharpening the image which may decrease OCR precision. So the default value should probably be sufficiently high.

    :arg bool header: boolean to switch on/off page header content. This parameter controls whether to include or omit the header content from all the document pages. Useful if the document has repetitive header content which doesn't add any value to the overall extraction data. Default is `True` meaning that header content will be written.

    :arg bool footer: boolean to switch on/off page footer content. This parameter controls whether to include or omit the footer content from all the document pages. Useful if the document has repetitive footer content which doesn't add any value to the overall extraction data. Default is `True` meaning that footer content will be written.

    :arg bool ignore_code: if `True` then mono-spaced text lines do not receive special formatting. No blocks will be written and text lines will be written continuously.

    :arg list pages: optional, the pages to consider for output (caution: specify 0-based page numbers). If omitted (`None`) all pages are processed. Any Python sequence with integer items is accepted. The sequence is sorted and processed to only contain unique items.

    :arg bool force_text: generate text output also when overlapping images / graphics. This text then appears after the respective image reference. Images (i.e. "picture" areas) however will not be written to the text output but appear as a text line in the output like `==> picture [width x height] <==`.

    :arg bool show_progress: Default is `False`. A value of `True` displays a progress bar as pages are being converted. Package `tqdm <https://pypi.org/project/tqdm/>`_ is used if installed, otherwise the built-in text based progress bar is used.
    
    :arg bool page_chunks: if `True` the output will be a list of `Document.page_count` dictionaries (one per page). Each dictionary has the following structure:

        - **"metadata"** - a dictionary consisting of the document's metadata :attr:`Document.metadata`, enriched with additional keys **"file_path"** (the file name), **"page_count"** (number of pages in document), and **"page_number"** (1-based page number).

        - **"toc_items"** - a list of Table of Contents items pointing to this page. Each item of this list has the format `[lvl, title, pagenumber]`, where `lvl` is the hierarchy level, `title` a string and `pagenumber` as a 1-based page number.

        - **"tables"** - empty list.
        - **"images"** - empty list.
        - **"graphics"** - empty list.
        - **"words"** - empty list.

        - **"text"** - page content as plain text.

        - **"page_boxes"** - a list of dictionaries representing the layout boundary boxes. Each dictionary has the following structure::

            {
                "index": int,              # 0-based integer index of the box in reading sequence
                "class": str,              # one of "text", "picture", "table", etc.
                "bbox": [x0, y0, x1, y1],  # boundary box coordinates
                "pos": (start, stop),      # 0-based integers: bbox_text = chunk["text"][start:stop]
            }
          
          See: :ref:`box classes <pymupdf4llm-api-boxclasses>`


.. _pymupdf4llm-api-to-chunks:

.. method:: to_chunks(doc: pymupdf.Document | str, **kwargs) -> ChunkedDocument

    Creates retrieval-oriented chunks from a document.

    Chunk boundaries are determined from layout information, including box boundaries, page breaks, vertical gaps, font changes, and structural hints. Token limits guide chunk assembly but are not guarantees: indivisible content, such as a preserved table, may exceed ``max_tokens``.

    :arg int max_tokens: target maximum number of tokens per chunk. Default is ``400``.

    :arg int min_tokens: minimum size used when merging small neighboring chunks. Default is ``120``. A value of ``0`` disables this minimum-size behavior.

    :arg float breakpoint_threshold: boundary score threshold used when splitting chunks. Default is ``0.5``.

    :arg bool merge_small_chunks: whether to merge chunks that are below ``min_tokens`` with neighboring chunks. Default is ``True``.

    :arg str table_mode: ``"preserve"`` keeps table content together as one chunk; ``"isolate"`` prevents tables from being merged into neighboring chunks. Default is ``"preserve"``.

    :arg bool respect_section_starts: whether to keep a chunk starting a detected section separate from the preceding section when merging to meet token budgets. Default is ``True``.

    :arg str header_footer_mode: controls handling of page headers and footers. ``"exclude"`` omits them from chunk text, ``"auto"`` omits repeated headers and footers, and ``"include"`` retains them. Default is ``"exclude"``. The element registry in the result retains the parsed layout elements in all modes.

    :arg str sentence_splitter: sentence splitting mode: ``"default"`` or ``"multilingual"`` (for additional CJK support). Default is ``"default"``.

    :arg tokenizer: token-counting strategy. Use ``None`` for the default character-based estimate, a callable accepting text and returning an integer token count, or a ``tiktoken`` encoding name. Default is ``None``.

    :arg dict weights: optional overrides for the layout boundary-score weights. The default ``None`` uses the built-in weights for box boundaries, box classes, page breaks, vertical and horizontal gaps, font changes, headings, headers and footers, lists, tables, and captions.

    The enum-valued arguments accept only the values listed above. ``max_tokens`` must be a positive integer and ``min_tokens`` a non-negative integer; unknown keyword arguments raise :exc:`TypeError` and invalid values raise :exc:`ValueError`.

    :returns: a :class:`ChunkedDocument`, a sequence of :class:`Chunk` objects with document-level element, table, figure, and section views. It also provides joined text, ID-based lookup, diagnostics, JSON-safe export, and reassembly with different chunk-budget parameters.


.. class:: ChunkedDocument

    Retrieval-ready chunks and document-level structure returned by :meth:`to_chunks`. This object implements the sequence protocol over its chunks: use ``len(cd)``, integer indexing, iteration, or slicing. Integer indexing returns a chunk; slicing returns a list of chunks. Chunk ids are ``c{n}`` in reading order, so ``cd.get("c3")`` addresses the same chunk as ``cd[3]``.

    The object also keeps layout elements and table, figure, and section views. These views are linked to their owning chunks through ids. Element ids have the form ``p{page}.b{box}`` (1-based page number and 0-based box index). The ``hierarchy`` property represents sections as a tree; its root has level 0.

    .. attribute:: chunks

        The chunks as a tuple, equivalent to ``tuple(cd)``.

    .. attribute:: text

        All chunk text joined in reading order with blank lines between chunks. The value is computed lazily and cached.

    .. attribute:: elements

        A list containing every parsed layout box, including headers and footers excluded from chunk text. Each element has an id, page and box indices, box class, bounding box, canonical text, and a flag indicating whether it is a header or footer.

    .. attribute:: tables

        A list of table views. Each table is linked to its owning chunk when one exists, and provides its id, source element id, page, bounding box, canonical text, optional caption and section id, and token count. The canonical text is Markdown or HTML according to the table output mode.

    .. attribute:: figures

        A list of figure and formula views, linked to their owning chunk when one exists. Views include source location, extracted text when available, caption and section links, and image data when it was extracted.

    .. attribute:: sections

        A list of section views with title, heading level, page range, path, child chunk ids, token count, and section body text.

    .. attribute:: hierarchy

        Sections arranged as a tree of section nodes. The root node has level 0 and no section id.

    .. attribute:: params

        A read-only mapping of the parameters used to create this object.

    .. attribute:: diagnostics

        A dictionary of extraction and ingestion facts: chunk, element, table, figure, section, and page counts; pages without chunks; reasons for an empty result; figures without extracted text; degenerate tables; and the number of excluded header/footer units. This reports facts only; consumers decide how to act on them.

    .. method:: get(id: str, default=...)

        Return a chunk, table, figure, section, or element by its public id: ``c{n}``, ``t{n}``, ``f{n}``, ``s{n}``, or ``p{page}.b{box}``. Raises :exc:`KeyError` if the id is unknown and no default is provided; otherwise returns ``default`` for an unknown id.

    .. method:: to_dicts(*, include_tagged: bool = True) -> list[dict]

        Return the chunks as flat, JSON-safe dictionaries. Each dictionary contains ``id``, ``text``, ``content_hash``, and ``metadata``; it also contains ``tagged_content`` unless ``include_tagged=False``.

    .. method:: to_json(*, include_tagged: bool = True, **json_kwargs) -> str

        Serialize the result of :meth:`to_dicts` as JSON. ``include_tagged`` controls whether tagged content is included; additional keyword arguments are passed to :func:`json.dumps`.

    .. method:: reassemble_chunks(**params) -> ChunkedDocument

        Create a new ``ChunkedDocument`` by assembling chunks again from the retained parsed units; the document does not need to be parsed again. Accepts only ``max_tokens``, ``min_tokens``, ``breakpoint_threshold``, ``table_mode``, ``merge_small_chunks``, and ``respect_section_starts``. Other chunking parameters and parse options raise :exc:`ValueError` because they require a new :meth:`to_chunks` call. The original object is unchanged.

    .. method:: to_langchain_documents(*, doc_id: str | None = None)

        Return the chunks as LangChain ``Document`` objects. Requires the optional ``langchain-core`` package. If ``doc_id`` is provided, it is prefixed to each exported chunk id to make ids unique across documents.

    .. method:: to_llama_nodes(*, doc_id: str | None = None)

        Return the chunks as LlamaIndex ``TextNode`` objects. Requires the optional ``llama-index-core`` package. If ``doc_id`` is provided, it is prefixed to each exported chunk id to make ids unique across documents; the original chunk id is retained in node metadata.


.. class:: Chunk

    A finalized, retrieval-ready portion of a document, returned as an item in :class:`ChunkedDocument`. Treat chunks returned by :meth:`to_chunks` as read-only. Mutating ``text`` or ``metadata`` after reading ``content_hash`` can leave that cached hash, and caches on the owning ``ChunkedDocument``, out of date. To change chunk boundaries, use :meth:`ChunkedDocument.reassemble_chunks`; keep application-specific data separately, keyed by the chunk id.

    .. attribute:: id

        The chunk id, formatted as ``c{n}``, where ``n`` is its position in this ``ChunkedDocument``. Chunk ids are local to the result and may change when chunks are reassembled with different parameters.

    .. attribute:: text

        The chunk's Markdown text, rendered from its layout content.

    .. attribute:: tagged_content

        Context-enriched text for embedding. It includes the chunk's section path, page, and non-paragraph content types where available, followed by its Markdown text. This is separate from ``text`` and is included by default in :meth:`ChunkedDocument.to_dicts` and :meth:`ChunkedDocument.to_json`.

    .. attribute:: metadata

        A :class:`ChunkMetadata` instance containing page, layout, structure, token-count, and provenance information for this chunk.

    .. attribute:: content_hash

        A lazily computed SHA-256 hash of ``text`` after runs of whitespace have been collapsed to one space and leading and trailing whitespace has been removed. The hash is cached. It is stable across rendering-only whitespace changes, but changes when the normalized text changes.

.. class:: ChunkMetadata

    Payload-ready metadata associated with a :class:`Chunk`. Its fields are also included in the ``metadata`` object returned by :meth:`ChunkedDocument.to_dicts` and :meth:`ChunkedDocument.to_json`.

    .. attribute:: page_start

        1-based number of the first page contributing content to the chunk.

    .. attribute:: page_end

        1-based number of the last page contributing content to the chunk.

    .. attribute:: bboxes

        List of bounding boxes in ``(page, x0, y0, x1, y1)`` form. Page numbers are 1-based.

    .. attribute:: types

        Content types present in the chunk, in reading order, such as ``"heading"``, ``"paragraph"``, ``"table"``, ``"list"``, ``"figure"``, or ``"caption"``.

    .. attribute:: section_id

        Id of the innermost detected section containing the chunk, in ``s{n}`` form, or ``None`` when the chunk is not associated with a section.

    .. attribute:: section_path

        List of section titles from the document's section hierarchy to the innermost section. Empty when no section applies.

    .. attribute:: token_count

        Token count used by the chunk assembler. Depending on the tokenizer and the final rendered text, this can differ slightly from a separate tokenization of ``text``; token budgets are targets rather than hard limits.

    .. attribute:: element_ids

        Ids of the source layout elements contributing to the chunk, formatted as ``p{page}.b{box}`` (1-based page number, 0-based box index).

    .. attribute:: table_ids

        Ids of table views associated with the chunk, formatted as ``t{n}``.

    .. attribute:: figure_ids

        Ids of figure or formula views associated with the chunk, formatted as ``f{n}``.

    .. attribute:: lists

        List groups found in the chunk. Each group contains ``items`` with item text, page number, and bounding box, and ``bboxes`` for the group.

    .. attribute:: ocr

        ``True`` if content contributing to this chunk came from a page processed by OCR; otherwise ``False``.

    .. attribute:: file_path

        Source document path, or ``None`` when no path is available.

    .. attribute:: page_count

        Number of pages in the source document, or ``None`` when unavailable.




.. _pymupdf4llm-api-layout:


.. method:: use_layout(yes: bool = True)

    Switch on/off the use of the :ref:`PyMuPDF Layout module <pymupdf4llm_and_layout>`. 
    
    If `yes=True` (default), the layout module will be used for page analysis for optimal results. If `yes=False`, the layout module will not be used.


.. method:: get_key_values(doc: pymupdf.Document | str) -> list[dict]

    Parse the document if it is a **Form PDF** and extract key-value pairs from all form fields (widgets).
    
    Please note that this method is only relevant for PDF documents that contain widgets. Otherwise, an empty list will be returned.

    The function is always available -- independently of whether you are using the PyMuPDF Layout module or not.

    Each dictionary item has the following structure::

        {
            "field_name": str,      # the full name of the form field, components separated by dots
            {
                "value": str,       # the field value as string
                "pages": list,      # list of 0-based page numbers where the field appears
            }
        }    

.. method:: LlamaMarkdownReader(*args, **kwargs)

    Create a `pdf_markdown_reader.PDFMarkdownReader` using the `LlamaIndex`_ package. Please note that this package will **not automatically be installed** when installing **pymupdf4llm**.

    For details on the possible arguments, please consult the LlamaIndex documentation [#f1]_.

    :raises: `NotImplementedError`: Please install required `LlamaIndex`_ package.
    :returns: a `pdf_markdown_reader.PDFMarkdownReader` and issues message "Successfully imported LlamaIndex". Please note that this method needs several seconds to execute. For details on using the markdown reader please see below.

----


.. class:: IdentifyHeaders

    .. note:: |PyMuPDFLayoutMode_Unavailable|


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

    .. note:: |PyMuPDFLayoutMode_Unavailable|

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



.. _pymupdf4llm-api-boxclasses:

.. note::

    **About box classes**

    If `page_chunks = True` the return objects for `to_markdown` & `to_text` contains a list of dictionaries representing the layout boundary boxes `page_boxes`, within that a key ``class`` indicates the type of box content therein.

    The return object for `to_json` contains a similar key called ``boxclass``.

    The possible string values are for this ``class`` / ``boxclass`` key are:

    .. code-block:: bash

        text
        picture
        table
        caption
        title
        section-header
        page-header
        page-footer
        list-item
        footnote
        formula

-----

For a list of changes, please see file `CHANGES.md <https://github.com/pymupdf/pymupdf4llm/blob/main/CHANGES.md>`_.

.. rubric:: Footnotes

.. [#f1] `LlamaIndex documentation <https://docs.llamaindex.ai/en/stable/>`_

.. [#f2] When using PyMuPDF-Pro, supported office documents are converted internally into a PDF-like format. Therefore, they **will have fixed page dimensions** and be no longer "reflowable". Consequently, the page width and page height specifications will be ignored as well in these cases.




.. include:: ../footer.rst

.. _LlamaIndex: https://pypi.org/project/llama-index/


.. raw:: html

    /* this script is used to adjust the search widget and to add line breaks after parameters in the signature blocks for better readability */
    <script>
        document.getElementById("headerSearchWidget").action = '../search.html';
        const params = document.querySelectorAll('.sig-param')
        
        params.forEach((param, index) => {
            const next = param.nextSibling;
            if (next && next.nodeType === 3) { // 3 = text node
                const span = document.createElement('span');
                if (index === params.length - 1) {
                    span.className = 'sig-comma-last';
                } else {
                    param.classList.add('has-comma');
                    span.className = 'sig-comma';
                }
                span.textContent = next.textContent;
                next.replaceWith(span);
            }    
        });
    </script>

    <style>
        .sig-comma {
            display: none;
        }
        dt .sig-param.has-comma::after {
            content: ",\A";
            white-space: pre;
        }
    </style>


