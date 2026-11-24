
.. include:: ../header.rst

.. raw:: html

    <script>
        document.getElementById("headerSearchWidget").action = '../search.html';
    </script>

.. _chunking-index:

Chunking
=============


:meth:`Document.to_chunks` splits a PDF into retrieval-friendly chunks using PDF-native layout signals (box boundaries, font changes, vertical gaps, page breaks) and returns a :class:`ChunkedDocument` — a sequence of chunks plus the document's structure: an element registry, table/figure/section views, a section hierarchy, and ingestion diagnostics.


Quick Start
-----------

.. code:: python

   import pymupdf

   doc = pymupdf.open("examples/country-capitals/national-capitals.pdf")
   cd = doc.to_chunks()

   for c in cd:
       print(c.id, c.metadata.types, c.text.splitlines()[0])
   # -> c0 ['heading', 'paragraph', 'table'] # **World Capital Cities**
   #    c1 ['table'] |**Country**|**Capital**|**Population**|**%**|**Year**|
   #    ...

Chunk Parameters
-----------------

See below for the available chunk parameters:

+----------------------------+----------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Parameter                  | Default        | Description                                                                                                                                                                                                                                                                                                                |
+============================+================+============================================================================================================================================================================================================================================================================================================================+
| ``max_tokens``             | ``400``        | Target tokens per chunk. The default is a starting point sized for common embedding inputs; larger budgets are typical for long-context synthesis or section-shaped retrieval — compare sizes with :ref:`recipe 5 <5-compare-chunk-sizes-and-expand-search-results>` and check final inputs against your model's tokenizer |
+----------------------------+----------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``min_tokens``             | ``120``        | Budget-merge floor: neighbouring chunks combine only while one of them is below this size. ``0`` disables the floor; ``min_tokens=max_tokens`` packs greedily up to the budget                                                                                                                                             |
+----------------------------+----------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``breakpoint_threshold``   | ``0.5``        | Boundary score threshold for splitting                                                                                                                                                                                                                                                                                     |
+----------------------------+----------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``merge_small_chunks``     | ``True``       | Merge undersized chunks with neighbors                                                                                                                                                                                                                                                                                     |
+----------------------------+----------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``table_mode``             | ``"preserve"`` | ``"preserve"``: table = one chunk; ``"isolate"``: tables never budget-merge                                                                                                                                                                                                                                                |
+----------------------------+----------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``respect_section_starts`` | ``True``       | Never budget-merge a section-opening chunk into the previous section's tail — chunk boundaries respect detected headings. Set ``False`` for pure token packing                                                                                                                                                             |
+----------------------------+----------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``header_footer_mode``     | ``"exclude"``  | ``"exclude"`` / ``"auto"`` (repeat detection) / ``"include"``                                                                                                                                                                                                                                                              |
+----------------------------+----------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``sentence_splitter``      | ``"default"``  | ``"default"`` (English) or ``"multilingual"`` (CJK support)                                                                                                                                                                                                                                                                |
+----------------------------+----------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``tokenizer``              | ``None``       | tiktoken encoding name (unknown names raise ``ValueError``), a ``callable(text) -> int``, or ``None`` (character estimate)                                                                                                                                                                                                 |
+----------------------------+----------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``weights``                | ``None``       | Boundary-score weight overrides                                                                                                                                                                                                                                                                                            |
+----------------------------+----------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

For API reference refer to :meth:`Document.to_chunks`, returns a :class:`ChunkedDocument`.

Choosing a budget
~~~~~~~~~~~~~~~~~

The 400-token default is a starting point, not a recommendation for every task: place useful sizes for retrieval roughly between ~200 and ~1024 tokens depending on the task and the embedding model.
On layout-rich documents most chunk boundaries here come from headings, tables, and boxes rather than from the budget cap. Evaluate candidate sizes on your own corpus and retrieval task; meth:`reassemble_chunks()` exists so that comparison costs seconds instead of a re-parse (recipes :ref:`5 <5-compare-chunk-sizes-and-expand-search-results>` and :ref:`6 <6-browse-and-search-by-section>`).

Token counting
--------------

Chunk budgets sum precomputed per-unit token counts (no re-tokenizing of joined text), so ``metadata.token_count`` can differ slightly from tokenizing the final chunk text — budgets are targets, not guarantees. Pass ``tokenizer="cl100k_base"`` (tiktoken) or a callable to count with your own tokenizer; the default is a 4-chars-per-token estimate. An unknown tiktoken encoding name raises ``ValueError`` rather than silently falling back. When enforcing a hard model input limit, tokenize the exact final input you send, including any tags or prefixes you add.

The resulting total is exposed as ``metadata.token_count``, and on the ``TableChunk`` / ``SectionChunk`` views as ``token_count``.


IDs Are a Contract
------------------

======= ================== ========================================================
Kind    Format             Example
======= ================== ========================================================
chunk   ``c{n}``           ``c12``
table   ``t{n}``           ``t0``
figure  ``f{n}``           ``f3`` (same ``n`` as ``[Figure f3: WxH]`` placeholders)
section ``s{n}``           ``s2``
element ``p{page}.b{box}`` ``p5.b7`` (1-based page, 0-based box)
======= ================== ========================================================

**Scope**: element ids are stable for the same *(document bytes, package version, parse options)*. Parse modes that re-split boxes (e.g. HTML table rendering) change box indices — never cache ids across parse-option changes.

**Chunk ids are positions.** ``c{n}`` is the n-th chunk in reading order, so ``cd.get("c3") is cd[3]``. They are local to one ``ChunkedDocument``: a ``reassemble_chunks()`` result numbers its own chunks from ``c0`` again. Table, figure, section and element ids do not depend on the budget.

``cd.get(id)`` resolves any of these; raises ``KeyError`` for an unknown id unless you pass ``default=``.


to_dicts() schema
~~~~~~~~~~~~~~~~~

The method :meth:`ChunkedDocument.to_dicts` returns one dict per chunk; ``metadata`` carries every :doc:`../chunk-metadata` field as-is, for example:

.. code:: text

   {
       "id": "c0",
       "text": "...",
       "content_hash": "6adc89bf...",
       "tagged_content": "...",          # omitted with include_tagged=False
       "metadata": {
           "page_start": 1, "page_end": 1, "bboxes": [...],
           "types": ["heading", "paragraph", "table"],
           "section_id": "s0", "section_path": ["World Capital Cities"],
           "token_count": 351, "element_ids": ["p1.b0", "p1.b1", "p1.b2"],
           "table_ids": ["t0"], "figure_ids": [], "lists": [], "ocr": false,
           "file_path": "...", "page_count": 6
       }
   }

diagnostics
~~~~~~~~~~~

:attr:`ChunkedDocument.diagnostics` reports facts about the parse so you can check extraction results before indexing; your pipeline owns the thresholds, see  :ref:`recipe 2 <2-check-extraction-results-before-indexing>`.

For example:

.. code:: text

   {
       "chunk_count": 6, "element_count": 14, "table_count": 6, "figure_count": 0,
       "section_count": 1, "page_count": 6,
       "pages_without_chunks": [],      # 1-based pages no chunk covers
       "zero_chunk_causes": [],         # only when chunk_count == 0: "no_text_extracted",
                                        # "all_units_header_footer" or "all_units_filtered"
       "figures_without_text": [],      # figure ids with no extractable text (OCR candidates)
       "degenerate_tables": [],         # table ids whose rendering is empty
       "header_footer_excluded": 6      # units dropped by header_footer_mode
   }

Views
~~~~~

:attr:`ChunkedDocument.tables`, :attr:`ChunkedDocument.figures` and :attr:`ChunkedDocument.sections` are lists of these objects; each links back to the chunk that holds it (``chunk_id``), and the chunk links forward via ``metadata.table_ids`` / ``figure_ids`` / ``section_id``:

.. code:: text

   TableChunk:   id                # "t{n}"
                 chunk_id          # id of the chunk holding this table ("c{n}")
                 element_id, page, bbox
                 markdown | html   # mutually exclusive by parse mode
                 headers           # header cell texts from <th>; [] on markdown parses
                 caption, caption_element_id
                 section_id        # innermost section ("s{n}")
                 token_count
                 text              # canonical rendering for the parse mode

   FigureChunk:  id                # "f{n}"
                 chunk_id          # id of the chunk holding this figure
                 element_id, page, bbox, boxclass
                 ocr_text          # extracted text; None → OCR candidate
                 placeholder       # "[Figure f{n}: WxH]" when there's no text
                 caption, caption_element_id
                 section_id        # innermost section ("s{n}")
                 image             # bytes when extract_images=True
                 has_text          # bool(ocr_text and ocr_text.strip())

   SectionChunk: id                # "s{n}"
                 title, level, page_start, page_end
                 heading_element_id
                 path              # titles, root → self
                 element_span      # [start, end) into ChunkedDocument.elements
                 child_chunk_ids   # chunks under this section, subtree included
                 token_count       # sum over child chunks
                 text              # lazy, assembled from the element registry


**Sections have a single source of truth**: the layout-detected heading boxes (``section-header``/``title``). The ``sections`` view, ``hierarchy``, and ``chunk.metadata.section_path`` (= the innermost owning section's ``path``) all derive from that same heading walk — the PDF TOC is never consulted, so a document without bookmarks still gets a fully populated ``section_path``, always consistent with the views. Chunk boundaries also respect this structure: with ``respect_section_starts=True`` (default) a section-opening chunk is never budget-merged into the previous section's tail.

**Sections nest.** ``SectionChunk.level`` is the engine's font-statistics heading level — the same value the renderers use for ``#``/``##``/``###`` depth — so big headings contain small ones: a level-4 section's ``path`` carries all its ancestors, and ``cd.hierarchy`` exposes the same nesting as a ``SectionNode`` tree (root level 0). The section tree therefore always matches the heading depth visible in the rendered markdown.

- **Ownership is innermost.** Content attaches at whatever depth it appears: the ``Corresponding Author`` heading and the e-mail line under it form chunk ``c13`` with ``section_id="s3"`` and ``section_path=[..., "AUTHOR INFORMATION", "Corresponding Author"]``, one unambiguous address per chunk.
- **Heading-only sections** still exist in the tree, owning just their own heading chunk (``s2`` owns ``c12``, the 6-token ``### **AUTHOR INFORMATION**`` line) until a same-or-shallower heading closes them; the content lives in the child sections ``s3`` and ``s4``.
- **Ancestors aggregate.** ``child_chunk_ids`` and ``token_count`` cover the whole subtree (``s2`` rolls up ``["c12", "c13", "c14"]``, 43 tokens), and ``element_span``\ s nest: ``s2`` ``(34, 39)`` contains ``s3`` ``(35, 37)``. Feed a whole branch to an LLM via ``SectionChunk.text`` (see: :ref:`recipe 6 <6-browse-and-search-by-section>`).
- **Before the first heading**, chunks stay unowned: ``section_id=None``, ``section_path=[]`` (a cover-page figure, for instance; a document with no headings at all has ``cd.sections == []`` and every chunk unowned).

Cookbook
--------

These examples show how to prepare chunks for search, inspect extraction results, and add context to search results. Run the setup below from the repository root before using a recipe. Each recipe then stands on its own. :ref:`Recipe 7 <7-export-to-langchain-or-llamaindex>` also requires the framework packages it uses.

The examples build ordinary Python dictionaries and lists. Connect these to your own embedding model, search index, or application as needed.

.. code:: python

   from pathlib import Path
   from hashlib import sha256

   import pymupdf

   doc = pymupdf.open("examples/country-capitals/national-capitals.pdf")
   cd = doc.to_chunks(doc, max_tokens=400)

.. _1-prepare-chunks-for-indexing:

1. Prepare chunks for indexing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use ``chunk.text`` for the extracted Markdown. Use ``chunk.tagged_content`` when you also want section titles, page numbers, and content types in the text sent to your embedding model. Choose the input that works best for your retrieval task, and apply any formatting your model requires.

Chunk IDs such as ``c0`` belong to one :class:`ChunkedDocument`. For a shared index, combine them with a document ID, document version, and processing version. The processing version should identify the package versions, parse options, chunk settings, and embedding setup you used.

.. code:: python

   document_id = "national-capitals"
   document_version = sha256(Path(pdf_path).read_bytes()).hexdigest()
   index_version = "layout-400-v1"        # your processing configuration version
   embedding_config = "my-model-v1"      # include model and input-format settings

   records = {}
   for chunk, payload in zip(cd, cd.to_dicts()):
       record_id = f"{document_id}:{document_version}:{index_version}:{chunk.id}"
       embedding_text = chunk.tagged_content
       records[record_id] = {
           **payload,
           "embedding_text": embedding_text,
           "embedding_config": embedding_config,
           "embedding_input_hash": sha256(embedding_text.encode("utf-8")).hexdigest(),
           "citation": {
               "section": " > ".join(chunk.metadata.section_path),
               "pages": [chunk.metadata.page_start, chunk.metadata.page_end],
           },
       }

   print(len(records))

Send each record's ``embedding_text`` to your model, then save the returned vector with the record's ID and metadata. Adding a record with an existing ID should replace that record. Some databases call this operation ``upsert``.

To reuse an existing embedding, compare both ``embedding_config`` and ``embedding_input_hash`` with the values saved previously. Hash the exact text sent to the model, after adding any required prefix or other formatting. ``chunk.content_hash`` covers only whitespace-normalized ``chunk.text``, so it does not detect changes to the section or page information in ``tagged_content``. Refresh citation metadata even when an embedding is reused.

When replacing a document in your index, also remove its previous records that are no longer current. Saving new records alone does not remove old chunks after a document or configuration change. If you retain multiple versions, search only the version you intend to use.

.. _2-check-extraction-results-before-indexing:

2. Check extraction results before indexing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``cd.diagnostics`` lists potential gaps in the extracted content. Use these details to decide whether to index the document, inspect it, or request OCR. An empty page or a figure without text may be expected, so adapt the checks to your documents.

.. code:: python

   diagnostics = cd.diagnostics

   if diagnostics["chunk_count"] == 0:
       print("No chunks to index:", diagnostics["zero_chunk_causes"])
   else:
       print("Chunks available:", diagnostics["chunk_count"])

   if diagnostics["pages_without_chunks"]:
       print("Check these pages:", diagnostics["pages_without_chunks"])
   if diagnostics["degenerate_tables"]:
       print("Check these empty tables:", diagnostics["degenerate_tables"])
   if diagnostics["figures_without_text"]:
       print("Figures to consider for OCR:", diagnostics["figures_without_text"])

.. _3-retrieve-and-cite-tables-and-figures:

3. Retrieve and cite tables and figures
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Tables and figures have their own IDs and source locations. This lets you index a table separately while keeping its surrounding chunk as context, or locate a figure that may need OCR.

.. code:: python
   
   doc = pymupdf.open("tests/test_tablulate_bug.pdf")
   cd_t = doc.to_chunks()

   table_records = {}
   for table in cd_t.tables:
       table_records[table.id] = {
           "text": table.text,
           "headers": table.headers,
           "page": table.page,
           "bbox": table.bbox,
           "context": cd_t.get(table.chunk_id).text,
       }

   figures_to_check = [
       {"id": figure.id, "page": figure.page, "bbox": figure.bbox}
       for figure in cd_t.figures
       if not figure.has_text
   ]

   print(table_records.keys())
   print(figures_to_check)

The IDs in these local dictionaries also need document and version scopes before being used in a shared index, as in recipe 1.

Use ``table_output="html"`` when you need HTML table structure, including merged cells.

.. code:: python

   doc = pymupdf.open("tests/test_sce_150_1.pdf")
   cd_h = doc.to_chunks(table_output="html")
   for table in cd_h.tables:
       print(table.id, table.headers, table.text[:100])

.. _4-add-neighboring-chunks-to-a-search-result:

4. Add neighboring chunks to a search result
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A :class:`ChunkedDocument` is a sequence in reading order. Given a chunk ID returned by your search, select nearby chunks to provide more context. This example uses ``c3`` as the search result.

.. code:: python

   hit = cd.get("c3")
   position = cd.index(hit)
   neighbors = cd[max(0, position - 2):position + 3]
   context = "\n\n".join(chunk.text for chunk in neighbors)

   print([chunk.id for chunk in neighbors])
   print(context[:200])

This includes up to two chunks before and after the hit. The slice stops at the document edges; it may cross section boundaries. Use :ref:`recipe 6 <6-browse-and-search-by-section>` when you want context from the hit's section instead.

.. _5-compare-chunk-sizes-and-expand-search-results:

5. Compare chunk sizes and expand search results
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:meth:`ChunkedDocument.reassemble_chunks()` creates new chunks from the layout already extracted. You can compare sizes without parsing the PDF again. Choose a size based on your retrieval results and the model's input limit.

.. code:: python

   for budget in (200, 400, 800):
       candidate = cd.reassemble_chunks(max_tokens=budget)
       largest = max((chunk.metadata.token_count for chunk in candidate), default=0)
       print("Target:", budget, "Chunks:", len(candidate), "Largest:", largest)

Token budgets are targets. A preserved table or an indivisible text unit can exceed the target, and ``metadata.token_count`` sums the per-unit counts. Check the final input with your model's tokenizer when enforcing an input limit, including any context tags you add.

You can also search smaller chunks and use larger chunks for context. The two results share source element IDs. Find all larger chunks that share an element with the search result:

.. code:: python

   larger = cd.reassemble_chunks(max_tokens=1200)
   hit = cd.get("c1")                    # an example result from the original index
   source_elements = set(hit.metadata.element_ids)

   matches = [
       chunk for chunk in larger
       if source_elements.intersection(chunk.metadata.element_ids)
   ]
   context = "\n\n".join(chunk.text for chunk in matches)

   print("Search result:", hit.id)
   print("Larger chunks:", [chunk.id for chunk in matches])

Element IDs identify layout boxes, not individual sentences. A long box can span several chunks, so the first match may not contain the hit's text. Collecting all matches avoids that omission, but can produce a large context. Use neighboring chunks or the owning section when you need a different expansion rule. Chunk IDs themselves cannot be matched across sizes because each result starts numbering at ``c0``.

.. _6-browse-and-search-by-section:

6. Browse and search by section
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use a larger token budget when you want longer passages. With ``respect_section_starts=True``, the default, a section-opening chunk is not merged backward into the previous section during the budget merge.

.. code:: python

   doc = pymupdf.open("tests/test_370.pdf")
   cd_p = doc.to_chunks()
   longer = cd_p.reassemble_chunks(max_tokens=2000)

   chunks_by_section = {}
   for chunk in longer:
       chunks_by_section.setdefault(chunk.metadata.section_id, []).append(chunk.id)

   print(chunks_by_section)

For a section browser or a keyword index, ``cd.sections`` also provides complete section text and title paths:

.. code:: python

   section_records = {
       section.id: {
           "title": section.title,
           "path": " > ".join(section.path),
           "text": section.text,
           "pages": [section.page_start, section.page_end],
       }
       for section in cd_p.sections
   }

   print(section_records.keys())

Section text includes its nested sections. Indexing both a parent and its children therefore repeats some content; choose the section levels your application needs. If a section is too long, use its chunks instead of dropping its content from the index.

To expand a search result to its owning section:

.. code:: python

   hit = cd_p.get("c11")
   section_id = hit.metadata.section_id
   section = cd_p.get(section_id) if section_id is not None else None
   context = section.text if section is not None else hit.text

   print(context[:200])

Chunks before the first detected heading, or in documents without detected headings, have no owning section. Check the final section text against your model's input limit before using it as context.

.. _7-export-to-langchain-or-llamaindex:

7. Export to LangChain or LlamaIndex
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Install the package for the framework you use, then call its export method. Pass ``doc_id`` when the exported objects will share an index with other documents; exported IDs then become ``"{doc_id}:{chunk.id}"``, which keeps them unique across documents. Without it, IDs are the local chunk IDs, and two documents both start at ``c0``.

.. code:: python

   # Requires langchain-core.
   documents = cd.to_langchain_documents(doc_id="national-capitals")

.. code:: python

   # Requires llama-index-core.
   nodes = cd.to_llama_nodes(doc_id="national-capitals")

Both methods export ``chunk.text`` and the fields in :class:`ChunkMetadata`. They do not use ``tagged_content`` as the document text. The original local chunk ID is always available as ``metadata["chunk_id"]``, so a search result maps back to this document through ``cd.get()``.



.. include:: ../footer.rst
