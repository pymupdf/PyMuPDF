.. include:: ../header.rst


.. |PyMuPDFLayoutMode_Unavailable| raw:: html

    <cite style="font-size:12px;color:#c0c0c0;background:transparent;border:1px solid #c0c0c0;border-radius:5px;padding:3px;">Only if <span style="font-family:monospace;">use_layout()</span> is <span style="font-family:monospace;">False</span></cite>







The PyMuPDF4LLM API
===========================================================================

.. note::

    As of PyMuPDF version 2.0 the core functionality of this module has been moved into the PyMuPDF Document class.

    As follows:

    :meth:`Document.to_markdown`
    :meth:`Document.to_json`
    :meth:`Document.to_text`
    :meth:`use_layout`

    Although the functions and classes are still available for backward compatibility, we *strongly* advise using the :class:`Document` class instead of the functions and classes provided by this module.


----



.. property:: version

    Prints the version of the library.

.. method:: to_markdown(doc: pymupdf.Document | str, *)

    See :meth:`Document.to_markdown` for further details.

.. method:: to_json(doc: pymupdf.Document | str,  *)

    See :meth:`Document.to_json` for further details.

.. method:: to_text(doc: pymupdf.Document | str,  *)

    See :meth:`Document.to_text` for further details.

.. method:: use_layout()

    See :meth:`use_layout` for further details.


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



.. _pymupdf-boxclasses:

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


