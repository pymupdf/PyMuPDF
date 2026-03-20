.. include:: ../header.rst


Default OCR Functions
======================

PyMuPDF4LLM supports default OCR functions. They come in the form of plugins that are present in its `ocr` subpackage. They are based on currently 3 popular OCR engines, Tesseract OCR, RapidOCR and PaddleOCR. Some engines can be combined to make use of their strengths and mitigate their weaknesses. For example, Tesseract OCR is very good at **recognizing** text, while RapidOCR is better at **detecting** text bounding boxes in images with complex backgrounds. By combining the two engines, we can achieve better overall OCR results while at the same time also reducing the overall OCR processing time.

Here is an overview of the available default plugins:

============== ========================= =================================================================================
Plugin Name    Engines                   Description
============== ========================= =================================================================================
rapidocr_api   RapidOCR                  Uses RapidOCR for both text **detection** and text **recognition**
paddleocr_api  PaddleOCR                 Uses PaddleOCR for both text **detection** and text **recognition**
tesseract_api  Tesseract OCR             Uses Tesseract OCR for both text **detection** and text **recognition**
rapidtess_api  RapidOCR + Tesseract OCR  Uses RapidOCR for text **detection** and Tesseract OCR for text **recognition**
paddletess_api PaddleOCR + Tesseract OCR Uses PaddleOCR for text **detection** and Tesseract OCR for text **recognition**
============== ========================= =================================================================================

If not explicitly selected via the `ocr_function` parameter, PyMuPDF4LLM will check the availability of the three OCR engines and pick one of the above plugins in the following order of preference:

1. `rapidtess_api` (if both RapidOCR and Tesseract OCR are available)
2. `paddletess_api` (if both PaddleOCR and Tesseract OCR are available)
3. `rapidocr_api` (if RapidOCR is available, but not Tesseract OCR)
4. `paddleocr_api` (if PaddleOCR is available, but not Tesseract OCR)
5. `tesseract_api` (if Tesseract OCR is available, but neither RapidOCR nor PaddleOCR are available)

If none of these engines is available (and no own plugin is provided), no OCR will be performed at all. If the `force_ocr` parameter is ``True``, an error will be raised. Otherwise, the document will be processed without OCR and a warning will be displayed.

The chosen plugin is displayed as an information message.

How Default Plugins Work
------------------------

The provided default plugins use the following **"hybrid"** OCR approach:

1. Each page is cleaned from any existing standard text content.
2. The remaining page is rendered as an image and passed to the OCR engine for text detection and recognition.
3. Only the detected text is inserted back into the original page as standard text content.

In this way, all original content (text and other elements) is preserved and only **augmented** with the newly recognized text. This allows for a more accurate and complete text extraction while also preserving the original document structure and formatting as much as possible. It also allows for a more efficient OCR processing since only the non-extractable text is processed by the OCR engine. This can significantly reduce the overall processing time.

It also increases the chances for a successful layout detection, because other original content like vectors remain intact and will not be rendered to pixels.

Forcing the Choice of a Default Plugin
---------------------------------------
The default plugins are designed to be used as is, without any need for configuration. However, if you want to use a specific plugin, you can do so by using the following approach (which enforces for instance using RapidOCR and skipping above selection process). Please note that all plugins have a function named `exec_ocr` that does the actual OCR::

    import pymupdf4llm
    from pymupdf4llm.ocr import rapidocr_api

    my_ocr_function = rapidocr_api.exec_ocr

    # Use my_ocr_function as the OCR function in PyMuPDF4LLM
    md_text = pymupdf4llm.to_markdown("input.pdf", ocr_function=my_ocr_function)


Providing your Own Plugin
-------------------------

If you want to use your own OCR function, you can do so as follows::

    import pymupdf4llm

    def my_ocr_function(page, pixmap=None, dpi=300, language="eng"):
        # Your OCR implementation here
        return None

    # Use my_ocr_function as the OCR function in PyMuPDF4LLM
    md_text = pymupdf4llm.to_markdown("input.pdf", ocr_function=my_ocr_function)

Your plugin must accept at least the ``page`` parameter which is a PyMuPDF Page object. The other parameters are optional. The plugin must create (or extend) the text of the passed-in page object by simply inserting text (using any of PyMuPDF's text insertion methods). No return values expected.

Be prepared to accept ``None`` or a PyMuPDF Pixmap object as the `pixmap` parameter, which is the rendered image of the page if provided. Parameters ``dpi`` and ``language`` are passed through from the respective function parameters.


Selecting Pages for OCR
------------------------

Usually in document processing, the vast majority of pages contain extractable text and do not require OCR. PyMuPDF4LLM contains logic that analyzes the content based on a number of criteria including (but not restricted to) the following:

* Presence of extractable and legible (!) text
* Presence of images that appear to contain text
* Presence of vector graphics that simulate text
* Presence of text generated by previous OCR activities

The OCR decision is internally based on the results of the following function::

    from pymupdf4llm.helpers.utils import analyze_page

    analysis = analyze_page(page)

The result ``analysis`` is a dictionary with the following keys and values. The area-related float values are computed as fractions of the total covered area.

* "covered": pymupdf.Rect, page area covered by content
* "img_joins": float, fraction of area of the joined images
* "img_area": float, fraction of **sum** of image area sizes
* "txt_joins": float, fraction of area of the joined text spans
* "txt_area": float, fraction of **sum** of text span bbox area sizes
* "vec_joins": float, fraction of area of the joined vector characters
* "vec_area": float, fraction of **sum** of vector character area sizes
* "chars_total": int, count of visible characters
* "chars_bad": int, count of Replacement Unicode characters
* "ocr_spans": int, count: text spans with ignored text (render mode 3)
* "img_var": float, area-weighted image variance
* "img_edges": float, area-weighted image edge energy
* "vec_suspicious": int, minimum number of suspected vector-based glyphs
* "reason": str, reason for the OCR decision, else ``None``
* "needs_ocr": bool, OCR decision (recommendation)

The reason is one of the following values:
* "chars_bad": more than 10% of all characters are illegible (i.e. Replacement Unicode characters)
* "ocr_spans": there exist text spans created from previous OCR executions (render mode 3)
* "vec_text": there exist suspected vector-based glyphs
* "img_text": there exist images which (probably) contain recognizable text

Based on this analysis, PyMuPDF4LLM will decide whether to invoke or skip OCR for a page. This is done to optimize processing time and resource usage by only performing OCR when it is likely to yield additional text content that cannot be extracted by other means.

You can override this logic in the following ways:

1. By setting `force_ocr=True` in the output functions (`to_markdown`, `to_text`, `to_json`). All pages will then be OCRed with the selected or provided OCR function regardless of their content. This will obviously have a massive impact on your execution time: expect several seconds duration per each page.

2. Do as before, but add your own selection logic to the OCR plugin::

    import pymupdf4llm
    from pymupdf4llm.ocr import rapidocr_api
    from pymupdf4llm.helpers.utils import analyze_page

    def my_ocr_function(page, pixmap=None, dpi=300, language="eng"):
        # analyze the page content and perform OCR only if necessary
        analysis = analyze_page(page)

        # inspect the items of the analysis dictionary to make your own
        # decision about whether to perform OCR or not, e.g.:
        if not analysis["needs_ocr"]:
            # accept decision NOT to perform OCR:
            return None

        # if OCR is recommended, you can decide differently based on
        # your own insights, e.g. we might want to accept previous OCR
        # results and skip OCR if there are already text spans created
        # from previous OCR executions (render mode 3):
        if analysis["reason"] == "ocr_spans":
            return None

        # execute desired OCR engine
        rapidocr_api.exec_ocr(page, pixmap=pixmap, dpi=dpi, language=language)
        return None

    md_text = pymupdf4llm.to_markdown("input.pdf", force_ocr=True, ocr_function=my_ocr_function, ...)

.. include:: ../footer.rst
