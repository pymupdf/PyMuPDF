.. include:: header.rst

.. _RecipesText:

==============================
Text
==============================


.. _RecipesText_A:

How to Extract all Document Text
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This script will take a document filename and generate a text file from all of its text.

The document can be any :ref:`supported type<Supported_File_Types>`.

The script works as a command line tool which expects the document filename supplied as a parameter. It generates one text file named "filename.txt" in the script directory. Text of pages is separated by a form feed character::

    import sys, pathlib, fitz
    fname = sys.argv[1]  # get document filename
    with fitz.open(fname) as doc:  # open document
        text = chr(12).join([page.get_text() for page in doc])
    # write as a binary file to support non-ASCII characters
    pathlib.Path(fname + ".txt").write_bytes(text.encode())

The output will be plain text as it is coded in the document. No effort is made to prettify in any way. Specifically for PDF, this may mean output not in usual reading order, unexpected line breaks and so forth.

You have many options to rectify this -- see chapter :ref:`Appendix2`. Among them are:

1. Extract text in HTML format and store it as a HTML document, so it can be viewed in any browser.
2. Extract text as a list of text blocks via *Page.get_text("blocks")*. Each item of this list contains position information for its text, which can be used to establish a convenient reading order.
3. Extract a list of single words via *Page.get_text("words")*. Its items are words with position information. Use it to determine text contained in a given rectangle -- see next section.

See the following two sections for examples and further explanations.


.. index::
   triple: lookup;text;key-value


.. _RecipesText_A1:

How to Extract Key-Value Pairs from a Page
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
If the layout of a page is *"predictable"* in some sense, then there is a simple way to find the values for a given set of keywords fast and easily -- without using regular expressions. Please see `this <https://github.com/pymupdf/PyMuPDF-Utilities/tree/master/text-extraction/lookup-keywords.py>`_ example script.

"Predictable" in this context means:

* Every keyword is followed by its value -- no other text is present in between them.
* The bottom of the value's boundary box is **not above** the one of the keyword.
* There are **no other restrictions**: the page layout may or may not be fixed, and the text may also have been stored as one string. Key and value may have any distance from each other.

For example, the following five key-value pairs will be correctly identified::

   key1               value1
   key2
   value2
   key3
          value3 blah, blah, blah key4 value4 some other text key5 value5 ...


.. index::
   triple: extract;text;rectangle


.. _RecipesText_B:

How to Extract Text from within a Rectangle
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
There is now (v1.18.0) more than one way to achieve this. We therefore have created a `folder <https://github.com/pymupdf/PyMuPDF-Utilities/tree/master/textbox-extraction>`_ in the PyMuPDF-Utilities repository specifically dealing with this topic.

----------

.. index::
    pair: text;reading order

.. _RecipesText_C:

How to Extract Text in Natural Reading Order
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

One of the common issues with PDF text extraction is, that text may not appear in any particular reading order.

This is the responsibility of the PDF creator (software or a human). For example, page headers may have been inserted in a separate step -- after the document had been produced. In such a case, the header text will appear at the end of a page text extraction (although it will be correctly shown by PDF viewer software). For example, the following snippet will add some header and footer lines to an existing PDF::

    doc = fitz.open("some.pdf")
    header = "Header"  # text in header
    footer = "Page %i of %i"  # text in footer
    for page in doc:
        page.insert_text((50, 50), header)  # insert header
        page.insert_text(  # insert footer 50 points above page bottom
            (50, page.rect.height - 50),
            footer % (page.number + 1, doc.page_count),
        )

The text sequence extracted from a page modified in this way will look like this:

1. original text
2. header line
3. footer line

PyMuPDF has several means to re-establish some reading sequence or even to re-generate a layout close to the original:

1. Use `sort` parameter of :meth:`Page.get_text`. It will sort the output from top-left to bottom-right (ignored for XHTML, HTML and XML output).
2. Use the `fitz` module in CLI: `python -m fitz gettext ...`, which produces a text file where text has been re-arranged in layout-preserving mode. Many options are available to control the output.

You can also use the above mentioned `script <https://github.com/pymupdf/PyMuPDF/wiki/How-to-extract-text-from-a-rectangle>`_ with your modifications.

----------

.. _RecipesText_D:

How to :index:`Extract Table Content <pair: extract; table>` from Documents
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
If you see a table in a document, you are normally not looking at something like an embedded Excel or other identifiable object. It usually is just normal, standard text, formatted to appear as tabular data.

Extracting tabular data from such a page area therefore means that you must find a way to **identify** the table area (i.e. its boundary box), then **(1)** graphically indicate table and column borders, and **(2)** then extract text based on this information.

This can be a very complex task, depending on details like the presence or absence of lines, rectangles or other supporting vector graphics.

Method :meth:`Page.find_tables` does all that for you, with a high table detection precision. Its great advantage is that there are no external library dependencies, nor the need to employ artificial intelligence or machine learning technologies. It also provides an integrated interface to the well-known Python package for data analysis `pandas <https://pypi.org/project/pandas/>`_.

Please have a look at example `Jupyter notebooks <https://github.com/pymupdf/PyMuPDF-Utilities/tree/master/table-analysis>`_, which cover standard situations like multiple tables on one page or joining table fragments across multiple pages.

----------

.. _RecipesText_E:

How to Mark Extracted Text
~~~~~~~~~~~~~~~~~~~~~~~~~~
There is a standard search function to search for arbitrary text on a page: :meth:`Page.search_for`. It returns a list of :ref:`Rect` objects which surround a found occurrence. These rectangles can for example be used to automatically insert annotations which visibly mark the found text.

This method has advantages and drawbacks. Pros are:

* The search string can contain blanks and wrap across lines
* Upper or lower case characters are treated equal
* Word hyphenation at line ends is detected and resolved
* Return may also be a list of :ref:`Quad` objects to precisely locate text that is **not parallel** to either axis -- using :ref:`Quad` output is also recommended, when page rotation is not zero.

But you also have other options::

 import sys
 import fitz

 def mark_word(page, text):
     """Underline each word that contains 'text'.
     """
     found = 0
     wlist = page.get_text("words", delimiters=None)  # make the word list
     for w in wlist:  # scan through all words on page
         if text in w[4]:  # w[4] is the word's string
             found += 1  # count
             r = fitz.Rect(w[:4])  # make rect from word bbox
             page.add_underline_annot(r)  # underline
     return found

 fname = sys.argv[1]  # filename
 text = sys.argv[2]  # search string
 doc = fitz.open(fname)

 print("underlining words containing '%s' in document '%s'" % (word, doc.name))

 new_doc = False  # indicator if anything found at all

 for page in doc:  # scan through the pages
     found = mark_word(page, text)  # mark the page's words
     if found:  # if anything found ...
         new_doc = True
         print("found '%s' %i times on page %i" % (text, found, page.number + 1))

 if new_doc:
     doc.save("marked-" + doc.name)

This script uses `Page.get_text("words")` to look for a string, handed in via cli parameter. This method separates a page's text into "words" using white spaces as delimiters. Further remarks:

* If found, the **complete word containing the string** is marked (underlined) -- not only the search string.
* The search string may **not contain word delimiters**. By default, word delimiters are white spaces and the non-breaking space `chr(0xA0)`. If you use extra delimiting characters like `page.get_text("words", delimiters="./,")` then none of these characters should be included in your search string either.
* As shown here, upper / lower cases are **respected**. But this can be changed by using the string method *lower()* (or even regular expressions) in function *mark_word*.
* There is **no upper limit**: all occurrences will be detected.
* You can use **anything** to mark the word: 'Underline', 'Highlight', 'StrikeThrough' or 'Square' annotations, etc.
* Here is an example snippet of a page of this manual, where "MuPDF" has been used as the search string. Note that all strings **containing "MuPDF"** have been completely underlined (not just the search string).

.. image:: images/img-markedpdf.*
   :scale: 60

----------------------------------------------


.. _RecipesText_F:

How to Mark Searched Text
~~~~~~~~~~~~~~~~~~~~~~~~~~
This script searches for text and marks it::

    # -*- coding: utf-8 -*-
    import fitz

    # the document to annotate
    doc = fitz.open("tilted-text.pdf")

    # the text to be marked
    needle = "¡La práctica hace el campeón!"

    # work with first page only
    page = doc[0]

    # get list of text locations
    # we use "quads", not rectangles because text may be tilted!
    rl = page.search_for(needle, quads=True)

    # mark all found quads with one annotation
    page.add_squiggly_annot(rl)

    # save to a new PDF
    doc.save("a-squiggly.pdf")

The result looks like this:

.. image:: images/img-textmarker.*
   :scale: 80

----------------------------------------------


.. _RecipesText_G:

How to Mark Non-horizontal Text
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The previous section already shows an example for marking non-horizontal text, that was detected by text **searching**.

But text **extraction** with the "dict" / "rawdict" options of :meth:`Page.get_text` may also return text with a non-zero angle to the x-axis. This is indicated by the value of the line dictionary's `"dir"` key: it is the tuple `(cosine, sine)` for that angle. If `line["dir"] != (1, 0)`, then the text of all its spans is rotated by (the same) angle != 0.

The "bboxes" returned by the method however are rectangles only -- not quads. So, to mark span text correctly, its quad must be recovered from the data contained in the line and span dictionary. Do this with the following utility function (new in v1.18.9)::

    span_quad = fitz.recover_quad(line["dir"], span)
    annot = page.add_highlight_annot(span_quad)  # this will mark the complete span text

If you want to **mark the complete line** or a subset of its spans in one go, use the following snippet (works for v1.18.10 or later)::

    line_quad = fitz.recover_line_quad(line, spans=line["spans"][1:-1])
    page.add_highlight_annot(line_quad)

.. image:: images/img-linequad.*

The `spans` argument above may specify any sub-list of `line["spans"]`. In the example above, the second to second-to-last span are marked. If omitted, the complete line is taken.

------------------------------

.. _RecipesText_H:

How to Analyze Font Characteristics
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
To analyze the characteristics of text in a PDF use this elementary script as a starting point:

.. literalinclude:: samples/text-lister.py
   :language: python

Here is the PDF page and the script output:

.. image:: images/img-pdftext.*
   :scale: 80

-----------------------------------------


.. _RecipesText_I:

How to Insert Text
~~~~~~~~~~~~~~~~~~~~
PyMuPDF provides ways to insert text on new or existing PDF pages with the following features:

* choose the font, including built-in fonts and fonts that are available as files
* choose text characteristics like bold, italic, font size, font color, etc.
* position the text in multiple ways:

    - either as simple line-oriented output starting at a certain point,
    - or fitting text in a box provided as a rectangle, in which case text alignment choices are also available,
    - choose whether text should be put in foreground (overlay existing content),
    - all text can be arbitrarily "morphed", i.e. its appearance can be changed via a :ref:`Matrix`, to achieve effects like scaling, shearing or mirroring,
    - independently from morphing and in addition to that, text can be rotated by integer multiples of 90 degrees.

All of the above is provided by three basic :ref:`Page`, resp. :ref:`Shape` methods:

* :meth:`Page.insert_font` -- install a font for the page for later reference. The result is reflected in the output of :meth:`Document.get_page_fonts`. The font can be:

    - provided as a file,
    - via :ref:`Font` (then use :attr:`Font.buffer`)
    - already present somewhere in **this or another** PDF, or
    - be a **built-in** font.

* :meth:`Page.insert_text` -- write some lines of text. Internally, this uses :meth:`Shape.insert_text`.

* :meth:`Page.insert_textbox` -- fit text in a given rectangle. Here you can choose text alignment features (left, right, centered, justified) and you keep control as to whether text actually fits. Internally, this uses :meth:`Shape.insert_textbox`.

.. note:: Both text insertion methods automatically install the font as necessary.


.. _RecipesText_I_a:

How to Write Text Lines
^^^^^^^^^^^^^^^^^^^^^^^^^^
Output some text lines on a page::

    import fitz
    doc = fitz.open(...)  # new or existing PDF
    page = doc.new_page()  # new or existing page via doc[n]
    p = fitz.Point(50, 72)  # start point of 1st line

    text = "Some text,\nspread across\nseveral lines."
    # the same result is achievable by
    # text = ["Some text", "spread across", "several lines."]

    rc = page.insert_text(p,  # bottom-left of 1st char
                         text,  # the text (honors '\n')
                         fontname = "helv",  # the default font
                         fontsize = 11,  # the default font size
                         rotate = 0,  # also available: 90, 180, 270
                         )
    print("%i lines printed on page %i." % (rc, page.number))

    doc.save("text.pdf")

With this method, only the **number of lines** will be controlled to not go beyond page height. Surplus lines will not be written and the number of actual lines will be returned. The calculation uses a line height calculated from the :data:`fontsize` and 36 points (0.5 inches) as bottom margin.

Line **width is ignored**. The surplus part of a line will simply be invisible.

However, for built-in fonts there are ways to calculate the line width beforehand - see :meth:`get_text_length`.

Here is another example. It inserts 4 text strings using the four different rotation options, and thereby explains, how the text insertion point must be chosen to achieve the desired result::

    import fitz
    doc = fitz.open()
    page = doc.new_page()
    # the text strings, each having 3 lines
    text1 = "rotate=0\nLine 2\nLine 3"
    text2 = "rotate=90\nLine 2\nLine 3"
    text3 = "rotate=-90\nLine 2\nLine 3"
    text4 = "rotate=180\nLine 2\nLine 3"
    red = (1, 0, 0) # the color for the red dots
    # the insertion points, each with a 25 pix distance from the corners
    p1 = fitz.Point(25, 25)
    p2 = fitz.Point(page.rect.width - 25, 25)
    p3 = fitz.Point(25, page.rect.height - 25)
    p4 = fitz.Point(page.rect.width - 25, page.rect.height - 25)
    # create a Shape to draw on
    shape = page.new_shape()

    # draw the insertion points as red, filled dots
    shape.draw_circle(p1,1)
    shape.draw_circle(p2,1)
    shape.draw_circle(p3,1)
    shape.draw_circle(p4,1)
    shape.finish(width=0.3, color=red, fill=red)

    # insert the text strings
    shape.insert_text(p1, text1)
    shape.insert_text(p3, text2, rotate=90)
    shape.insert_text(p2, text3, rotate=-90)
    shape.insert_text(p4, text4, rotate=180)

    # store our work to the page
    shape.commit()
    doc.save(...)

This is the result:

.. image:: images/img-inserttext.*
   :scale: 33



------------------------------------------

.. _RecipesText_I_b:

How to Fill a Text Box
^^^^^^^^^^^^^^^^^^^^^^^^^^
This script fills 4 different rectangles with text, each time choosing a different rotation value::

    import fitz
    doc = fitz.open(...)  # new or existing PDF
    page = doc.new_page()  # new page, or choose doc[n]
    r1 = fitz.Rect(50,100,100,150)  # a 50x50 rectangle
    disp = fitz.Rect(55, 0, 55, 0)  # add this to get more rects
    r2 = r1 + disp  # 2nd rect
    r3 = r1 + disp * 2  # 3rd rect
    r4 = r1 + disp * 3  # 4th rect
    t1 = "text with rotate = 0."  # the texts we will put in
    t2 = "text with rotate = 90."
    t3 = "text with rotate = -90."
    t4 = "text with rotate = 180."
    red  = (1,0,0)  # some colors
    gold = (1,1,0)
    blue = (0,0,1)
    """We use a Shape object (something like a canvas) to output the text and
    the rectangles surrounding it for demonstration.
    """
    shape = page.new_shape()  # create Shape
    shape.draw_rect(r1)  # draw rectangles
    shape.draw_rect(r2)  # giving them
    shape.draw_rect(r3)  # a yellow background
    shape.draw_rect(r4)  # and a red border
    shape.finish(width = 0.3, color = red, fill = gold)
    # Now insert text in the rectangles. Font "Helvetica" will be used
    # by default. A return code rc < 0 indicates insufficient space (not checked here).
    rc = shape.insert_textbox(r1, t1, color = blue)
    rc = shape.insert_textbox(r2, t2, color = blue, rotate = 90)
    rc = shape.insert_textbox(r3, t3, color = blue, rotate = -90)
    rc = shape.insert_textbox(r4, t4, color = blue, rotate = 180)
    shape.commit()  # write all stuff to page /Contents
    doc.save("...")

Several default values were used above: font "Helvetica", font size 11 and text alignment "left". The result will look like this:

.. image:: images/img-textbox.*
   :scale: 50

------------------------------------------

.. _RecipesText_I_c:

How to Use Non-Standard Encoding
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Since v1.14, MuPDF allows Greek and Russian encoding variants for the :data:`Base14_Fonts`. In PyMuPDF this is supported via an additional *encoding* argument. Effectively, this is relevant for Helvetica, Times-Roman and Courier (and their bold / italic forms) and **characters outside the ASCII code range only**. ASCII characters remain Latin!

.. note:: Please keep in mind that the Base-14 fonts only support characters with `ord(c) < 256`. The `encoding` parameter does not change that. So only characters with `ord(c) > 128` are under the influence of `encoding`.
    
    To avoid these restrictions, we strongly recommend to use the file-based font variants, which are available via the :ref:`Font` class. These fonts do not require (and ignore) the encoding parameter. Your text can also be any mixture of standard Latin, Cyrillic, Greek and other characters. `fitz.Font("helv")` for example support 654 glyphs - not just 256. The only consideration is that your PDF file size will grow because now a font file will be embedded.
    
    Choosing any font from `pymupf-fonts <https://pypi.org/project/pymupdf-fonts/>`_ will provide you with the best of all worlds: nice and rich fonts that are also subsettable via :meth:`Document.subset_fonts()`. This limits your file sizes significantly. `fitz.Font("figo")` for example supports 4577 glyphs. But still, after using :meth:`Document.subset_fonts()`, the file size increase will probably be something like 10 or 12 KB -- and not 43 KB as with `fitz.Font("helv")`.

Here is how to request Russian encoding with the standard font Helvetica::

    page.insert_text(point, russian_text, encoding=fitz.TEXT_ENCODING_CYRILLIC)

The valid encoding values are TEXT_ENCODING_LATIN (0), TEXT_ENCODING_GREEK (1), and TEXT_ENCODING_CYRILLIC (2, Russian) with Latin being the default. Encoding can be specified by all relevant font and text insertion methods.

By the above statement, the fontname *helv* is automatically connected to the Russian font variant of Helvetica. Any subsequent text insertion with **this fontname** will use the Russian Helvetica encoding.

If you change the fontname just slightly, you can also achieve an **encoding "mixture"** for the **same base font** on the same page::

    import fitz
    doc=fitz.open()
    page = doc.new_page()
    shape = page.new_shape()
    t="Sômé tèxt wìth nöñ-Lâtîn characterß."
    shape.insert_text((50,70), t, fontname="helv", encoding=fitz.TEXT_ENCODING_LATIN)
    shape.insert_text((50,90), t, fontname="HElv", encoding=fitz.TEXT_ENCODING_GREEK)
    shape.insert_text((50,110), t, fontname="HELV", encoding=fitz.TEXT_ENCODING_CYRILLIC)
    shape.commit()
    doc.save("t.pdf")

The result:

.. image:: images/img-encoding.*
   :scale: 50

The snippet above indeed leads to three different copies of the Helvetica font in the PDF. Each copy is uniquely identified (and referenceable) by using the correct upper-lower case spelling of the reserved word "helv"::

    for f in doc.get_page_fonts(0): print(f)

    [6, 'n/a', 'Type1', 'Helvetica', 'helv', 'WinAnsiEncoding']
    [7, 'n/a', 'Type1', 'Helvetica', 'HElv', 'WinAnsiEncoding']
    [8, 'n/a', 'Type1', 'Helvetica', 'HELV', 'WinAnsiEncoding']

.. include:: footer.rst
