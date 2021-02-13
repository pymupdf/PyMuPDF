.. _Font:

================
Font
================

*(New in v1.16.18)* This class represents a font as defined in MuPDF (*fz_font_s* structure). It is required for the new class :ref:`TextWriter` and the new :meth:`Page.write_text`. Currently, it has no connection to how fonts are used in methods :meth:`Page.insert_text` or :meth:`Page.insert_textbox`, respectively.

A Font object also contains useful general information, like the font bbox, the number of defined glyphs, glyph names or the bbox of a single glyph.


==================================== ============================================
**Method / Attribute**               **Short Description**
==================================== ============================================
:meth:`~Font.glyph_advance`          Width of a character
:meth:`~Font.glyph_bbox`             Glyph rectangle
:meth:`~Font.glyph_name_to_unicode`  Get unicode from glyph name
:meth:`~Font.has_glyph`              Return glyph id of unicode
:meth:`~Font.text_length`            Compute text length under a fontsize
:meth:`~Font.unicode_to_glyph_name`  Get glyph name of a unicode
:meth:`~Font.valid_codepoints`       Array of supported unicodes
:attr:`~Font.ascender`               Font ascender
:attr:`~Font.descender`              Font descender
:attr:`~Font.bbox`                   Font rectangle
:attr:`~Font.buffer`                 Copy of the font's binary image
:attr:`~Font.flags`                  Collection of font properties
:attr:`~Font.glyph_count`            Number of supported glyphs
:attr:`~Font.name`                   Name of font
:attr:`~Font.is_writable`            Font usable with :ref:`TextWriter`
==================================== ============================================


**Class API**

.. class:: Font

   .. method:: __init__(self, fontname=None, fontfile=None,
                  fontbuffer=None, script=0, language=None, ordering=-1, is_bold=0,
                  is_italic=0, is_serif=0)

      Font constructor. The large number of parameters are used to locate font, which most closely resembles the requirements. Not all parameters are ever required -- see the below pseudo code explaining the logic how the parameters are evaluated.

      :arg str fontname: one of the :ref:`Base-14-Fonts` or CJK fontnames. Also possible are a select few other names like (watch the correct spelling): "Arial", "Times", "Times Roman".
      
         *(Changed in v1.17.5)*

         If you have installed `pymupdf-fonts <https://pypi.org/project/pymupdf-fonts/>`_, there are also new "reserved" fontnames available, which are listed in :attr:`fitz_fonts` and in the table further down.

      :arg str filename: the filename of a fontfile somewhere on your system [#f1]_.
      :arg bytes,bytearray,io.BytesIO fontbuffer: a fontfile loaded in memory [#f1]_.
      :arg in script: the number of a UCDN script. Currently supported in PyMuPDF are numbers 24, and 32 through 35.
      :arg str language: one of the values "zh-Hant" (traditional Chinese), "zh-Hans" (simplified Chinese), "ja" (Japanese) and "ko" (Korean). Otherwise, all ISO 639 codes from the subsets 1, 2, 3 and 5 are also possible, but are currently documentary only.
      :arg int ordering: an alternative selector for one of the CJK fonts.
      :arg bool is_bold: look for a bold font.
      :arg bool is_italic: look for an italic font.
      :arg bool is_serif: look for a serifed font.

      :returns: a MuPDF font if successful. This is the overall sequence of checks to determine an appropriate font:

         =========== ============================================================
         Argument    Action
         =========== ============================================================
         fontfile?   Create font from file, exception if failure.
         fontbuffer? Create font from buffer, exception if failure.
         ordering>=0 Create universal font, always succeeds.
         fontname?   Create a Base-14 font, universal font, or font
                     provided by `pymupdf-fonts <https://pypi.org/project/pymupdf-fonts/>`_. See table below.
         =========== ============================================================


      .. note::

        With the usual reserved names "helv", "tiro", etc., you will create fonts with the expected names "Helvetica", "Times-Roman" and so on. **However**, and in contrast to :meth:`Page.insert_font` and friends,

         * a font file will **always** be embedded in your PDF,
         * Greek and Cyrillic characters are supported without needing the *encoding* parameter.

        Using *ordering >= 0*, or fontnames "cjk", "china-t", "china-s", "japan" or "korea" will **always create the same "universal"** font **"Droid Sans Fallback Regular"**. This font supports **all CJK and all Latin characters**, including Greek and Cyrillic.

        Actually, you would rarely ever need another font than **"Droid Sans Fallback Regular"**. **Except** that this font file is relatively large and adds about 1.65 MB (compressed) to your PDF file size. If you do not need CJK support, stick with specifying "helv", "tiro" etc., and you will get away with about 35 KB compressed.

        If you **know** you have a mixture of CJK and Latin text, consider just using ``Font("cjk")`` because this supports everything and also significantly (by a factor of two to three) speeds up execution: MuPDF will always find any character in this single font and need not check fallbacks.

        But if you do specify a Base-14 fontname, you will still be able to also write CJK characters: MuPDF detects this situation and silently falls back to the universal font (which will then of course also be embedded in your PDF).

        *(New in v1.17.5)* Optionally, some new "reserved" fontname codes become available if you install `pymupdf-fonts <https://pypi.org/project/pymupdf-fonts/>`_. **"Fira Mono"** is a nice mono-spaced sans font set and **FiraGO** is another non-serifed "universal" font, set which supports all Latin (including Cyrillic and Greek) plus Thai, Arabian, Hewbrew and Devanagari -- but none of the CJK languages. The size of a FiraGO font is only a quarter of the "Droid Sans Fallback" size (compressed 400 KB vs. 1.65 MB) -- **and** it provides the weight bold, italic, bold-italic -- which the universal font doesn't.

        **"Space Mono"** is another nice and small mono-spaced font from Google Fonts, which supports Latin Extended characters and comes with all 4 important weights.

        The following table maps a fontname code to the corresponding font:

            =========== =========================== ======= =============================
            Code        Fontname                    New in  Comment
            =========== =========================== ======= =============================
            figo        FiraGO Regular              v1.0.0  narrower than Helvetica
            figbo       FiraGO Bold                 v1.0.0
            figit       FiraGO Italic               v1.0.0
            figbi       FiraGO Bold Italic          v1.0.0
            fimo        Fira Mono Regular           v1.0.0
            fimbo       Fira Mono Bold              v1.0.0
            spacemo     Space Mono Regular          v1.0.1
            spacembo    Space Mono Bold             v1.0.1
            spacemit    Space Mono Italic           v1.0.1
            spacembi    Space Mono Bold-Italic      v1.0.1
            math        Noto Sans Math Regular      v1.0.2  math symbols
            music       Noto Music Regular          v1.0.2  musical symbols
            symbol1     Noto Sans Symbols Regular   v1.0.2  replacement for "symb"
            symbol2     Noto Sans Symbols2 Regular  v1.0.2  extended symbol set
            notos       Noto Sans Regular           v1.0.3  alternative to Helvetica
            notosit     Noto Sans Italic            v1.0.3
            notosbo     Noto Sans Bold              v1.0.3
            notosbi     Noto Sans BoldItalic        v1.0.3
            =========== =========================== ======= =============================


   .. method:: has_glyph(chr, language=None, script=0, fallback=False)

      Check whether the unicode *chr* exists in the font or some fallback font. May be used to check whether any "TOFU" symbols will appear on output.

      :arg int chr: the unicode of the character (i.e. *ord()*).
      :arg str language: the language -- currently unused.
      :arg int script: the UCDN script number.
      :arg bool fallback: *(new in v1.17.5)* perform an extended search in fallback fonts or restrict to current font (default).
      :returns: *(changed in 1.17.7)* the glyph number. Zero indicates no glyph found.

   .. method:: valid_codepoints()

      *(New in v1.17.5)*

      Return an array of unicodes supported by this font.

      :returns: an *array.array* [#f2]_ of length at most :attr:`Font.glyph_count`. I.e. *chr()* of every item in this array has a glyph in the font without using fallbacks. This is an example display of the supported glyphs:

         >>> import fitz
         >>> font = fitz.Font("math")
         >>> vuc = font.valid_codepoints()
         >>> for i in vuc:
               print("%04X %s (%s)" % (i, chr(i), font.unicode_to_glyph_name(i)))
         0000
         000D   (CR)
         0020   (space)
         0021 ! (exclam)
         0022 " (quotedbl)
         0023 # (numbersign)
         0024 $ (dollar)
         0025 % (percent)
         ...
         00AC ¬ (logicalnot)
         00B1 ± (plusminus)
         ...
         21D0 ⇐ (arrowdblleft)
         21D1 ⇑ (arrowdblup)
         21D2 ⇒ (arrowdblright)
         21D3 ⇓ (arrowdbldown)
         21D4 ⇔ (arrowdblboth)
         ...
         221E ∞ (infinity)
         ...

      .. note:: This method only returns meaningful data for fonts having a CMAP (character map, charmap, the `/ToUnicode` PDF key). Otherwise, this array will have length 1 and contain zero only.

   .. method:: glyph_advance(chr, language=None, script=0, wmode=0)

      Calculate the "width" of the character's glyph (visual representation).

      :arg int chr: the unicode number of the character. Use *ord()*, not the character itself. Again, this should normally work even if a character is not supported by that font, because fallback fonts will be checked where necessary.
      :arg int wmode: write mode, 0 = horizontal, 1 = vertical.

      The other parameters are not in use currently.

      :returns: a float representing the glyph's width relative to **fontsize 1**.

   .. method:: glyph_name_to_unicode(name)

      Return the unicode value for a given glyph name. Use it in conjunction with ``chr()`` if you want to output e.g. a certain symbol.

      :arg str name: The name of the glyph.

      :returns: The unicode integer, or 65533 = 0xFFFD if the name is unknown. Examples: ``font.glyph_name_to_unicode("Sigma") = 931``, ``font.glyph_name_to_unicode("sigma") = 963``. Refer to the `Adobe Glyph List <https://github.com/adobe-type-tools/agl-aglfn/blob/master/glyphlist.txt>`_ publication for a list of glyph names and their unicode numbers. Example:

         >>> font = fitz.Font("helv")
         >>> font.has_glyph(font.glyph_name_to_unicode("infinity"))
         True

   .. method:: glyph_bbox(chr, language=None, script=0)

      The glyph rectangle relative to fontsize 1.

      :arg int chr: *ord()* of the character.

      :returns: a :ref:`Rect`.


   .. method:: unicode_to_glyph_name(ch)

      Show the name of the character's glyph.

      :arg int ch: the unicode number of the character. Use *ord()*, not the character itself.

      :returns: a string representing the glyph's name. E.g. ``font.glyph_name(ord("#")) = "numbersign"``. For an invalid code ".notfound" is returned.
      
        .. note:: *(Changed in v1.18.0)* This method and :meth:`Font.glyph_name_to_unicode` no longer depend on a font and instead retrieve information from the **Adobe Glyph List**. Also available as ``fitz.unicode_to_glyph_name()`` and resp. ``fitz.glyph_name_to_unicode()``.

   .. method:: text_length(text, fontsize=11)

      Calculate the length of a unicode string.

      :arg str text: a text string -- UTF-8 encoded.

      :arg float fontsize: the fontsize.

      :rtype: float

      :returns: the length of the string when stored in the PDF. Internally :meth:`glyph_advance` is used on a by-character level. If the font does not have a character, it will automatically be looked up in a fallback font.

   .. attribute:: buffer

      *(New in v1.17.6)*

      Copy of the binary font file content.
      
      :rtype: bytes

   .. attribute:: flags

      A dictionary with various font properties, each represented as bools. Example for Helvetica::

         >>> pprint(font.flags)
         {'bold': 0,
         'fake-bold': 0,
         'fake-italic': 0,
         'invalid-bbox': 0,
         'italic': 0,
         'mono': 0,
         'opentype': 0,
         'serif': 1,
         'stretch': 0,
         'substitute': 0}

      :rtype: dict

   .. attribute:: name

      :rtype: str

      Name of the font. May be "" or "(null)".

   .. attribute:: bbox

      The font bbox. This is the maximum of its glyph bboxes.

      :rtype: :ref:`Rect`

   .. attribute:: glyph_count

      :rtype: int

      The number of glyphs defined in the font.

   .. attribute:: ascender

      *(New in v1.18.0)*

      The ascender value of the font, see `here <https://en.wikipedia.org/wiki/Ascender_(typography)>`_ for details.

      :rtype: float

   .. attribute:: descender

      *(New in v1.18.0)*

      The descender value of the font, see `here <https://en.wikipedia.org/wiki/Descender>`_ for details.

      :rtype: float

   .. attribute:: is_writable

      *(New in v1.18.0)*

      Indicates whether this font can be used with :ref:`TextWriter`.

      :rtype: bool

.. rubric:: Footnotes

.. [#f1] MuPDF does not support all fontfiles with this feature and will raise exceptions like *"mupdf: FT_New_Memory_Face((null)): unknown file format"*, if it encounters issues. The :ref:`TextWriter` methods check :attr:`Font.is_writable`.

.. [#f2] The built-in module *array* has been chosen for its speed and its compact representation of values.
