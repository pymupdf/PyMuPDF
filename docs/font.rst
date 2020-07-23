.. _Font:

================
Font
================

*(New in v1.16.18)* This class represents a font as defined in MuPDF (*fz_font_s* structure). It is required for the new class :ref:`TextWriter` and the new :meth:`Page.writeText`. Currently, it has no connection to how fonts are used in methods ``insertText`` or insertTextbox``, respectively.

A Font object also contains useful general information, like the font bbox, the number of defined glyphs, glyph names or the bbox of a single glyph.

**Class API**

.. class:: Font

   .. method:: __init__(self, fontname=None, fontfile=None,
                  fontbuffer=None, script=0, language=None, ordering=-1, is_bold=0,
                  is_italic=0, is_serif=0)

      Font constructor. The large number of parameters are used to locate font, which most closely resembles the requirements. Not all parameters are ever required -- see the below pseudo code explaining the logic how the parameters are evaluated.

      :arg str fontname: one of the :ref:`Base-14-Fonts` or CJK fontnames. Also possible are a select few of other names like (watch the correct spelling): "Arial", "Times", "Times Roman".
      
         *(Changed in v1.17.4)*

         If you have installed `pymupdf-fonts <https://pypi.org/project/pymupdf-fonts/>`_, you can also use the following new "reserved" fontnames: "figo", "figbo", "figit", "figbi", "fimo", and "fimbo". This will provide one of the "FiraGo" or resp. "FiraMono" fonts, created by Mozilla.org.

      :arg str filename: the filename of a fontfile somewhere on your system [#f1]_.
      :arg bytes,bytearray,io.BytesIO fontbuffer: a fontfile loaded in memory [#f1]_.
      :arg in script: the number of a UCDN script. Currently supported in PyMuPDF are numbers 24, and 32 through 35.
      :arg str language: one of the values "zh-Hant" (traditional Chinese), "zh-Hans" (simplified Chinese), "ja" (Japanese) and "ko" (Korean). Otherwise, all ISO 639 codes from the subsets 1, 2, 3 and 5 are also possible, but are currently documentary only.
      :arg int ordering: an alternative selector for one of the CJK fonts.
      :arg bool is_bold: look for a bold font.
      :arg bool is_italic: look for an italic font.
      :arg bool is_serif: look for a serifed font.

      :returns: a MuPDF font if successful. This is the overall logic, how an appropriate font is located::

         if fontfile:
            create font from it ignoring other arguments
            if not successful -> exception
         if fonbuffer:
            create font from it ignoring other arguments
            if not successful -> exception
         if ordering >= 0:
            load **"universal"** font ignoring other parameters
            # this will always be successful
         if fontname:
            create a Base14 font, or resp. **"universal"** font, ignoring other parameters
            # note: values "Arial", "Times", "Times Roman" are also possible
            if not successful -> exception
         Finally try to load a "NOTO" font using *script* and *language* parameters.
         if not successful:
            look for fallback font

      .. note::

        With the usual abbreviations "helv", "tiro", etc., you will create fonts with the expected names "Helvetica", "Times-Roman" and so on.

        Using *ordering >= 0*, or fontnames starting with "china", "japan" or "korea" will always create the same **"universal"** font **"Droid Sans Fallback Regular"**. This font supports **all CJK and all Latin characters**.

        Actually, you would rarely ever need another font than **"Droid Sans Fallback Regular"**. **Except** that this font file is relatively large and adds about 1.65 MB (compressed) to your PDF file size. If you do not need CJK support, stick with specifying "helv", "tiro" etc., and you will get away with about 35 KB compressed.

        If you **know** you have a mixture of CJK and Latin text, consider just using ``Font(ordering=0)`` because this supports everything and also significantly (by a factor of two to three) speeds up execution: MuPDF will always find any character in this single font and need not check fallbacks.

        But if you do specify a Base-14 fontname, you will still be able to also write CJK characters! MuPDF automatically detects this situation and silently falls back to the universal font (which will then of course also be embedded in your PDF).

        *(New in v1.17.4)* Optionally, a set of new "reserved" fontnames becomes available if you install `pymupdf-fonts <https://pypi.org/project/pymupdf-fonts/>`_. The currently available fonts are from the Fira fonts family created by Mozilla. "Fira Mono" is a nice mono-spaced sans font set and FiraGO is another non-serifed "universal" font, set which supports all European languages (including Cyrillic and Greek) plus Thai, Arabian, Hewbrew and Devanagari -- however none of the CJK languages. The size of a FiraGO font is only a quarter of the "Droid Sans Fallback" size (compressed 400 KB vs. 1.65 MB) -- and the style variants bold and italic are available..The following table maps a fontname to the corresponding font:

            =========== =======================================
            Fontname    Font
            =========== =======================================
            figo        FiraGO Regular
            figbo       FiraGO Bold
            figit       FiraGO Italic
            figbi       FiraGO Bold Italic
            fimo        Fira Mono Regular
            fimbo       Fira Mono Bold
            =========== =======================================

        **All fonts mentioned here** also support Greek and Cyrillic letters.

   .. method:: has_glyph(chr, language=None, script=0)

      Check whether the unicode *chr* exists in the font or some fallback. May be used to check whether any "TOFU" symbols will appear on output.

      :arg int chr: the unicode of the character (i.e. *ord()*).
      :arg str language: the language -- currently unused.
      :arg int script: the UCDN script number.
      :returns: *True* or *False*.

   .. method:: glyph_advance(chr, language=None, script=0, wmode=0)

      Calculate the "width" of the character's glyph (visual representation).

      :arg int chr: the unicode number of the character. Use ``ord(c)``, not the character itself. Again, this should normally work even if a character is not supported by that font, because fallback fonts will be checked where necessary.

      The other parameters are not in use currently. This especially means that only horizontal text writing is supported.

      :returns: a float representing the glyph's width relative to **fontsize 1**.

   .. method:: glyph_name_to_unicode(name)

      Return the unicode for a given glyph name. Use it in conjunction with ``chr()`` if you want to output e.g. a certain symbol.

      :arg str name: The name of the glyph.

      :returns: The unicode integer, or 65533 = 0xFFFD if the name is unknown. Examples: ``font.glyph_name_to_unicode("Sigma") = 931``, ``font.glyph_name_to_unicode("sigma") = 963``. Refer to e.g. `this <https://github.com/adobe-type-tools/agl-aglfn/blob/master/glyphlist.txt>`_ publication for a list of glyph names and their unicode numbers.

   .. method:: unicode_to_glyph_name(chr, language=None, script=0, wmode=0)

      Show the name of the character's glyph.

      :arg int chr: the unicode number of the character. Use ``ord(c)``, not the character itself.

      :returns: a string representing the glyph's name. E.g. ``font.glyph_name(ord("#")) = "numbersign"``. Depending on how this font was built, the string may be empty, ".notfound" or some generated name.

   .. method:: text_length(text, fontsize=11)

      Calculate the length of a unicode string.

      :arg str text: a text string -- UTF-8 encoded. For Python 2, you must use unicode here.

      :arg float fontsize: the fontsize.

      :returns: a float representing the length of the string when stored in the PDF. Internally :meth:`glyph_advance` is used on a by-character level. If the font does not have a character, it will automatically be looked up in a fallback font.

   .. attribute:: flags

      A dictionary with various font properties, each represented as bools.

   .. attribute:: name

      Name of the font. May be "" or "(null)".

   .. attribute:: glyph_count

      The number of glyphs defined in the font.

.. rubric:: Footnotes

.. [#f1] MuPDF does not support all fontfiles with this feature and will raise exceptions like *"mupdf: FT_New_Memory_Face((null)): unknown file format"*, if encounters issues.
