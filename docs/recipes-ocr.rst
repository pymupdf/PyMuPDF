.. include:: header.rst

.. _RecipesOCR:


.. |toggleStart| raw:: html

   <details>
   <summary><a>See code</a></summary>

.. |toggleEnd| raw:: html

   </details>

====================================
OCR - Optical Character Recognition
====================================

|PyMuPDF| has integrated support for OCR (Optical Character Recognition). It is possible to use OCR for both, images (via the :ref:`Pixmap` class) and for document pages.

The feature is currently based on Tesseract-OCR which must be installed as a separate application -- see the :ref:`installation_ocr`.

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


.. include:: footer.rst
