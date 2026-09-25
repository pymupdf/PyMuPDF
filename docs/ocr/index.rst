
.. include:: ../header.rst

.. raw:: html

    <script>
        document.getElementById("headerSearchWidget").action = '../search.html';
    </script>

.. _ocr-index:

OCR
===

.. meta::
   :description: How automatic OCR works in PyMuPDF, when to force it, and how to swap in a different OCR engine.

Overview
-------- 

|PyMuPDF| includes built-in OCR support for scanned documents and image-based PDFs. By default, OCR runs **automatically** when needed — you don't have to opt in. For more control, you can force OCR on specific pages, disable it entirely, or swap in a different OCR engine using the adaptor interface.

.. note::

   OCR requires a working Tesseract installation. See `OCR Installation <installation_ocr>` for setup instructions.

----

Auto-OCR Behaviour
------------------

PyMuPDF inspects each page before extracting text. If a page contains **no selectable text** — meaning all content is rasterised into images — OCR is triggered automatically for that page.

Pages that contain native text are never sent through OCR, even if they also contain embedded images. This keeps processing fast and avoids degrading already-clean text.

.. code-block:: python

   import pymupdf

   # OCR runs automatically on any page with no selectable text
   doc = pymupdf.open("scanned-document.pdf")
   md_text = doc.to_markdown()

The resulting Markdown is seamless — pages extracted via OCR and pages extracted natively are combined into a single output with no distinction between them.

----

How OCR is Triggered
--------------------

There are two scenarios where OCR is applied automatically:

**No text at all** — if a page contains roughly no text but is covered with images or many character-sized vectors, PyMuPDF uses `OpenCV <https://pypi.org/project/opencv-python/>`_ to check whether text is *probably* detectable on the page. This distinguishes image-based text (e.g. a scanned document) from ordinary pictures like photographs.

**Garbled text** — if a page does contain text but too many characters are unreadable (e.g. ``"�����"``), OCR is applied **for the affected text areas only**, not the full page. This preserves already-readable text, images, and vectors while recovering only what is broken.

.. note::

   For these heuristics to work, both a `Tesseract installation <installation_ocr>` and `OpenCV <https://pypi.org/project/opencv-python/>`_ must be available in your Python environment. If either is missing, no OCR is attempted.

----

Decision Tree
~~~~~~~~~~~~~

OCR is applied only when all four of the following conditions are met:

1. **PyMuPDF Layout is imported** — The Layout analysis module must be active. This is ``True`` by default.
2. **use_ocr is enabled** — The ``use_ocr`` parameter in the PyMuPDF API must be ``True``. This is the default value.
3. **Tesseract is installed** — Tesseract must be correctly installed on your system. See `OCR installation <installation_ocr>`.
4. **OpenCV is available** — The ``opencv-python`` package must be available in your Python environment.

----

Forcing OCR
-----------

In some cases you may want to force OCR even on pages that contain selectable text — for example, when the native text layer is corrupt, misencoded, or misaligned with the visual content.

Use ``force_ocr=True`` to bypass the auto-detection check entirely:

.. code-block:: python

   doc = pymupdf.open("document.pdf")
   md_text = doc.to_markdown(force_ocr=True)

.. warning::

   Forcing OCR on clean, text-based PDFs will slow down processing significantly and may reduce output quality. Only use ``force_ocr=True`` when you have reason to distrust the native text layer.

You can also force OCR on specific pages rather than the whole document:

.. code-block:: python
   
   doc = pymupdf.open("document.pdf")
   md_text = doc.to_markdown(
       pages=[2, 3, 4],
       force_ocr=True
   )

----

Disabling OCR
-------------

To prevent OCR from running at all — even on pages with no selectable text — set ``use_ocr=False``:

.. code-block:: python

   doc = pymupdf.open("document.pdf")
   md_text = doc.to_markdown(use_ocr=False)

Pages with no selectable text will return empty strings in this mode. This is useful when you know your documents are always text-based, or when you want to handle OCR yourself in a downstream step.

----

OCR Adaptors
------------

By default, PyMuPDF uses **Tesseract** and **OpenCV** for image pre-processing. If you need a different OCR engine — for higher accuracy, language support, or cloud-based processing — you can plug in a custom adaptor.

Built-in Adaptors
~~~~~~~~~~~~~~~~~

RapidOCR
^^^^^^^^

If `RapidOCR <https://github.com/RapidAI/RapidOCR?tab=readme-ov-file>`_ and the RapidOCR ONNX Runtime are available, you can use a pre-made callable OCR function for it, which is provided in the ``PyMuPDF.ocr`` module as ``rapidocr_api.exec_ocr``.

**Example**

.. code-block:: python

   from pymupdf.ocr import rapidocr_api

   doc = pymupdf.open("document.pdf")
   md = doc.to_markdown(
       ocr_function=rapidocr_api.exec_ocr,
       force_ocr=True
   )

In this way RapidOCR can be used as an alternative OCR engine to Tesseract for all pages (if ``force_ocr=True``) or just for those pages which meet the default criteria for applying OCR (if ``force_ocr=False`` or omitted).

RapidOCR & Tesseract Side-by-Side
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you want to use both OCR engines side-by-side, you can do so by implementing a custom OCR function which calls both OCR engines — one for bbox recognition (RapidOCR) and the other for text recognition (Tesseract) — and then combines their results.

This pre-made callable OCR function can be found in the ``PyMuPDF.ocr`` module as ``rapidtess_api.exec_ocr``.

**Example**

.. code-block:: python

   from pymupdf.ocr import rapidtess_api

   doc = pymupdf.open("document.pdf")
   md = doc.to_markdown(
       ocr_function=rapidtess_api.exec_ocr,
       force_ocr=True
   )

.. list-table::
   :header-rows: 1
   :widths: 35 25 40

   * - Adaptor
     - Engines
     - Notes
   * - ``rapidocr_api.exec_ocr``
     - RapidOCR
     - Requires RapidOCR and ONNX Runtime
   * - ``rapidtess_api.exec_ocr``
     - RapidOCR & Tesseract
     - Better accuracy for bounding box detection and text recognition


.. _ocr_custom_adaptor:

Writing a Custom Adaptor
~~~~~~~~~~~~~~~~~~~~~~~~

An OCR adaptor can be defined by passing your own Python ``ocr_function`` method which follows a protocol as follows:

.. code-block:: python

   def exec_ocr(page, dpi=300, pixmap=None):
       """
       Custom OCR function to replace the default Tesseract-based implementation.

       Parameters:
       - page: The PyMuPDF page object being processed.
       - dpi: The resolution at which to render the page for OCR.
       - pixmap: An optional pre-rendered pixmap of the page, if available.

       If a Pixmap is provided, the DPI parameter is ignored. Otherwise, an RGB
       Pixmap is created from the page at the specified DPI.
       """

       # Your custom OCR logic here.
       # The method should render the OCR'ed text onto the page
       # so that PyMuPDF can extract it as usual.

       ...

.. tip::

   Custom adaptors receive a page or image object and must render what they "see" onto the source document.
   PyMuPDF handles interpretation — your adaptor needs to handle the text recognition & rendering step.

----

OCR Language Support
--------------------

When using the default Tesseract adaptor, you can specify one or more languages using Tesseract's language codes.

Specify the language to be used by the Tesseract OCR engine. Default is ``"eng"`` (English). Make sure that the respective language data files are installed. Remember to use correct Tesseract language codes. Multiple languages can be specified by concatenating the respective codes with a plus sign ``"+"``, for example ``"eng+deu"`` for English and German.

.. code-block:: python
   
   doc = pymupdf.open("multilingual.pdf")
   md_text = doc.to_markdown(ocr_language="eng+deu")

Tesseract language packs must be installed separately on your system. For example, on Ubuntu:

.. code-block:: bash

   sudo apt install tesseract-ocr-deu tesseract-ocr-fra

See the page on :ref:`installing Tesseract language packs <tesseract-language-packs>` for further details.

----


How to OCR an Image 
--------------------
A supported image must first be converted to a :ref:`Pixmap`. The Pixmap can then be saved to a 1-page PDF. This page will look like the original image with the same width and height. It will contain a layer of text as recognized by Tesseract.

The PDF can be generated via one of the methods :meth:`Pixmap.pdfocr_save` or :meth:`Pixmap.pdfocr_tobytes`, as a file on disk or as a PDF in memory.

The text can be extracted and searched with the usual text extraction and search methods (:meth:`Page.get_text`, :meth:`Page.search_for`, etc.). Please also note the following important facts and prerequisites:

* When converting the image to a Pixmap, please confirm that the color space is RGB and alpha is `False` (no transparency). Convert the original Pixmap if necessary.
* All text is written as "hidden" with Tesseract's own `GlyphLessFont`, a mono-spaced font with metrics comparable to Courier.
* All text has the properties regular and black (i.e. no bold, no italic, no information about the original fonts).
* Tesseract does not recognize vector graphics (i.e. no drawings / line-art).

This approach is also recommended to OCR a complete scanned PDF:

* Render each page to a :ref:`Pixmap` with desired resolution
* Append the resulting 1-page PDF to the output PDF

How to OCR a Document Page
----------------------------
Any supported document page can be OCR-ed -- either the complete page or only the image areas on it.

Because optical character recognition is about one thousand times slower than standard text extraction, we make sure to do OCR only once per page and store the result in a :ref:`TextPage`. Using this TextPage for all subsequent extractions and text searches will then happen with |PyMuPDF|'s usual top speed.

To OCR a document page, follow this approach:

1. Determine whether OCR is needed / beneficial at all. A number of criteria can be used for this decision, like:

  * page is completely covered by an image
  * no text exists on the page
  * thousands of small vector graphics (indicating *simulated* text)

2. OCR the page and store result in a :ref:`TextPage` object using an instruction like `tp = page.get_textpage_ocr(...)`.

3. Refer to the produced :ref:`TextPage` in all subsequent text extractions and searches via the `textpage=tp` parameter.

----

Performance Tips
----------------

OCR is the most compute-intensive part of the extraction pipeline. A few ways to keep it fast:

- **Process only the pages you need** using the ``pages`` parameter to avoid running OCR on the entire document.
- **Cache results** — write the output to disk after the first run so you don't re-process the same file.
- **Use** ``force_ocr=False`` (the default) so clean pages skip OCR entirely.
- **Resize images before passing to OCR** — very high DPI scans can slow Tesseract down without improving accuracy.

----

.. include:: ../footer.rst