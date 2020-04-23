.. _TextWriter:

================
TextWriter
================

*(New in v1.16.18)* This class represents a MuPDF *text* object. It can be thought of as a store of text spans -- each span having its own position, font and font size. It is an elegant alternative for writing text to PDF pages, when compared with methods :meth:`Page.insertText` and friends:

* **Improved text positioning:** The position of the last inserted character is returned, as well as the combined rectangle of text stored so far.
* **Automatic fallback fonts:** If a character is not represented by the chosen font, alternative fonts are automatically checked. This significantly reduces the risk of seeing unprintable symbols in the output, so-called "TOFUs". PyMuPDF now also comes with a **"universal"** font, which supports **all Latin** characters (incuding Cyrillic and Greek), and **all CJK** characters (Chinese, Japanese, Korean).
* **Reusability:** A TextWriter exists independent from any page. The same text can be written multiple times, to the same or other pages, same or different PDFs, choosing different colors or transparency.
* **Transparency support:** Parameter *opacity* is supported. This offers a handy way to write watermark-style text.
* **Justified text:** Supported for any font -- not just simple fonts as in :meth:`Page.insertText`.

Using this object entails three steps:

1. When **created**, a TextWriter object requires a fixed **page rectangle** in relation to which it calculates text positions. Pages with different dimensions cannot use this TextWriter object.
2. Store text in the TextWriter using method either :meth:`TextWriter.append` or :meth:`TextWriter.fillTextbox`.
3. Output the stored text on any PDF page with the same rectangle. This is the only point, where pages are referenced.

TextWriters do not support text rotation. But the new method :meth:`Page.writeText` is able to combine one or more TextWriters and jointly write them to **any rectangle** and with **any rotation angle** -- much like :meth:`Page.showPDFpage`.

**Class API**

.. class:: TextWriter

   .. method:: __init__(self, rect, opacity=1, color=None)

      :arg rect-like rect: rectangle internally used for text positioning computations.
      :arg float opacity: sets the transparency for the text to store here. Values outside the interval ``[0, 1)`` will be ignored. A value of e.g. 0.5 means 50% transparency.
      :arg float,sequ color: the color of the text. All colors are specified as floats *0 <= color <= 1*. A single float represents some gray level, a sequence implies the colorspace via its length.


   .. method:: append(pos, text, font=None, fontsize=11, language=None)

      Add new text, usually (but not necessarily) representing a text span.

      :arg point_like pos: start position of the text, the bottom left point of the first character.
      :arg str text: a string (Python 2: unicode is mandatory!) of arbitrary length. It will be written starting at position "pos".
      :arg font: a :ref:`Font`. If omitted, ``fitz.Font("helv")`` will be used.
      :arg float fontsize: the fontsize, a positive number, default 11.
      :arg str language: the language to use, e.g. "en" for English. Meaningful values should be compliant with the ISO 639 standards 1, 2, 3 or 5. Reserved for future use: currently has no effect as far as we know.

      :returns: :attr:`textRect` and :attr:`lastPoint` after this text has been added.


   .. method:: fillTextbox(rect, text, font="helv", fontsize=11, align=0, warn=True)

      Fill a given rectangle with text. This is a convenience method to use instead of :meth:`append` (which is internally invoked).

      :arg rect_like rect: the area to fill. No part of the text will appear outside of this.
      :arg str,sequ text: the text. Can be specified as a (UTF-8) string or a list / tuple of strings. A string will first be converted to a list using *splitlines()*. Every list item will begin on a new line (forced line breaks).
      :arg font: the :ref:`Font`
      :arg float fontsize: the fontsize.
      :arg int align: text alignment. Use one of TEXT_ALIGN_LEFT, TEXT_ALIGN_CENTER, TEXT_ALIGN_RIGHT or TEXT_ALIGN_JUSTIFY.
      :arg bool warn: print a warning if the area is too small, or raise an exception.

   .. method:: writeText(page, opacity=None, color=None, overlay=True)

      Write the accumulated text to the page.

      :arg page: write to this :ref:`Page`.
      :arg float opacity: overwrite the value of the TextWriter for this output.
      :arg sequ color: overwrite the value of the TextWriter for this output.
      :arg bool overlay: put in foreground (default) or background.


   .. attribute:: textRect

      The area currently occupied. This value changes when more text is added.

   .. attribute:: lastPoint

      The "cursor position" after the last written character.

   .. attribute:: opacity

      The text opacity (modifyable).

   .. attribute:: color

      The text color (modifyable).

   .. attribute:: rect

      The rectangle for which this TextWriter was created. Must not be modified.

.. note::

  1. Opacity and color apply to **all the text** in this object. 
  2. If you need different colors / transpareny, you must create a separate TextWriter. Whenever you determine the color should change, simply append the text to the respective TextWriter using the previously returned :attr:`lastPoint` as position for the new text.
  3. Appending items can occur in arbitrary order: only the position parameter controls where text appears.
  4. Font and fontsize can freely vary within the same TextWriter. This can be used to let text with different properties appear on the same displayed line: just specify *pos* accordingly, and e.g. set it to :attr:`lastPoint` of the previously added item.
