.. include:: ../header.rst


PyMuPDF4LLM Change Log
===========================================================================

Changes in version 0.0.10
--------------------------

Fixes:
~~~~~~~

* `73 <https://github.com/pymupdf/RAG/issues/73>`_ "bug in to_markdown internal function"
* `74 <https://github.com/pymupdf/RAG/issues/74>`_ "minimum area for images & vector graphics"
* `75 <https://github.com/pymupdf/RAG/issues/75>`_ "Poor Markdown Generation for Particular PDF"
* `76 <https://github.com/pymupdf/RAG/issues/76>`_ "suggestion on useful api parameters"


Improvements:
~~~~~~~~~~~~~~
* Improved recognition of "insignificant" vector graphics. Graphics like text highlights or borders will be ignored.
* The format of saved images can now be controlled via new parameter `image_format`.
* Images can be stored in a specific folder via the new parameter `image_path`.
* Images are **not stored if contained** in another image on same page.
* Images are **not stored if too small:** if width or height are less than 5% of corresponding page dimension.
* All text is always written. If `write_images=True`, text on images / graphics can be suppressed by setting `force_text=False`.


Changes in version 0.0.9
--------------------------

Fixes:
~~~~~~~

* `71 <https://github.com/pymupdf/RAG/issues/71>`_ "Unexpected results in pymupdf4llm but pymupdf works"
* `68 <https://github.com/pymupdf/RAG/issues/68>`_ "Issue with text extraction near footer of page"


Improvements:
~~~~~~~~~~~~~~
* Improved identification of scattered text span particles. This should address most issues with out-of-sequence situations.
* We now correctly process rotated pages (see issue #68).


Changes in version 0.0.8
--------------------------

Fixes:
~~~~~~~

* `65 <https://github.com/pymupdf/RAG/issues/65>`_ Fix typo in `pymupdf_rag.py`.


Changes in version 0.0.7
--------------------------

Fixes:
~~~~~~~

* `54 <https://github.com/pymupdf/RAG/issues/54>`_ "Mistakes in orchestrating sentences". Additional fix: text extraction no longer uses the TEXT_DEHYPHNATE flag bit.

Improvements:
~~~~~~~~~~~~~~~~

* Improved the algorithm dealing with vector graphics. Vector graphics are now more reliably classified as irrelevant: We now detect when "strokes" only exist in the neighborhood of the graphics boundary box border itself. This is quite often the case for code snippets.


Changes in version 0.0.6
--------------------------

Fixes:
~~~~~~~

* `55 <https://github.com/pymupdf/RAG/issues/55>`_ "Bug in helpers/multi_column.py - IndexError: list index out of range"
* `54 <https://github.com/pymupdf/RAG/issues/54>`_ "Mistakes in orchestrating sentences"
* `52 <https://github.com/pymupdf/RAG/issues/52>`_ "Chunking of text files"
* Partial fix for `41 <https://github.com/pymupdf/RAG/issues/41>`_ / `40 <https://github.com/pymupdf/RAG/issues/40>`_. Improved page column detection, but still no silver bullet for overly complex page layouts.

Improvements:
~~~~~~~~~~~~~~~~

* New parameter `dpi` to specify the resolution of images.
* New parameters `page_width` / `page_height` for easily processing reflowable documents (Text, Office, e-books).
* New parameter `graphics_limit` to avoid spending runtimes for value-less content.
* New parameter `table_strategy` to directly control the table detection strategy.

.. include:: ../footer.rst

