.. include:: header.rst

.. _Chunk:

================
Chunk
================

* New in v2.0

.. class:: Chunk

    A finalized, retrieval-ready portion of a document, returned as an item in :class:`ChunkedDocument`. Treat chunks returned by :meth:`Document.to_chunks` as read-only. Mutating ``text`` or ``metadata`` after reading ``content_hash`` can leave that cached hash, and caches on the owning :class:`ChunkedDocument`, out of date. To change chunk boundaries, use :meth:`ChunkedDocument.reassemble_chunks`; keep application-specific data separately, keyed by the chunk id.

    .. attribute:: id

        The chunk id, formatted as ``c{n}``, where ``n`` is its position in this :class:`ChunkedDocument`. Chunk ids are local to the result and may change when chunks are reassembled with different parameters.

    .. attribute:: text

        The chunk's Markdown text, rendered from its layout content.

    .. attribute:: tagged_content

        Context-enriched text for embedding. It includes the chunk's section path, page, and non-paragraph content types where available, followed by its Markdown text. This is separate from ``text`` and is included by default in :meth:`ChunkedDocument.to_dicts` and :meth:`ChunkedDocument.to_json`.

    .. attribute:: metadata

        A :doc:`chunk-metadata` instance containing page, layout, structure, token-count, and provenance information for this chunk.

    .. attribute:: content_hash

        A lazily computed SHA-256 hash of ``text`` after runs of whitespace have been collapsed to one space and leading and trailing whitespace has been removed. The hash is cached. It is stable across rendering-only whitespace changes, but changes when the normalized text changes.



.. include:: footer.rst
