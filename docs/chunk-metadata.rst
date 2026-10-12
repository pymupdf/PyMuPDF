.. include:: header.rst

.. _ChunkMetadata:

================
ChunkMetadata
================

* New in v2.0

.. class:: ChunkMetadata

    Payload-ready metadata associated with a :doc:`chunk`. Included in the :attr:`Chunk.metadata` object.

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


.. include:: footer.rst
