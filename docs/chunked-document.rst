.. include:: header.rst

.. _ChunkedDocument:

================
ChunkedDocument
================

* New in v2.0

.. class:: ChunkedDocument

    Retrieval-ready chunks and document-level structure returned by :meth:`Document.to_chunks`. This object implements the sequence protocol over its chunks: use ``len(cd)``, integer indexing, iteration, or slicing. Integer indexing returns a chunk; slicing returns a list of chunks. Chunk ids are ``c{n}`` in reading order, so ``cd.get("c3")`` addresses the same chunk as ``cd[3]``.

    The object also keeps layout elements and table, figure, and section views. These views are linked to their owning chunks through ids. Element ids have the form ``p{page}.b{box}`` (1-based page number and 0-based box index). The ``hierarchy`` property represents sections as a tree; its root has level 0.

    .. attribute:: chunks

        The chunks as a tuple, equivalent to ``tuple(cd)``. See: :doc:`chunk`.

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

        Create a new :class:`ChunkedDocument` by assembling chunks again from the retained parsed units; the document does not need to be parsed again. Accepts only ``max_tokens``, ``min_tokens``, ``breakpoint_threshold``, ``table_mode``, ``merge_small_chunks``, and ``respect_section_starts``. Other chunking parameters and parse options raise :exc:`ValueError` because they require a new :meth:`Document.to_chunks` call. The original object is unchanged.

    .. method:: to_langchain_documents(*, doc_id: str | None = None)

        Return the chunks as LangChain ``Document`` objects. Requires the optional ``langchain-core`` package. If ``doc_id`` is provided, it is prefixed to each exported chunk id to make ids unique across documents.

    .. method:: to_llama_nodes(*, doc_id: str | None = None)

        Return the chunks as LlamaIndex ``TextNode`` objects. Requires the optional ``llama-index-core`` package. If ``doc_id`` is provided, it is prefixed to each exported chunk id to make ids unique across documents; the original chunk id is retained in node metadata.







.. include:: footer.rst
