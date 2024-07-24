.. include:: header.rst

.. _Appendix1:

======================================
Appendix 1: Details on Text Extraction
======================================
This chapter provides background on the text extraction methods of PyMuPDF.

Information of interest are

* what do they provide?
* what do they imply (processing time / data sizes)?

General structure of a TextPage
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
:ref:`TextPage` is one of (Py-) MuPDF's classes. It is normally created (and destroyed again) behind the curtain, when :ref:`Page` text extraction methods are used, but it is also available directly and can be used as a persistent object. Other than its name suggests, images may optionally also be part of a text page::

 <page>
     <text block>
         <line>
             <span>
                 <char>
     <image block>
         <img>

A **text page** consists of blocks (= roughly paragraphs).

A **block** consists of either lines and their characters, or an image.

A **line** consists of spans.

A **span** consists of adjacent characters with identical font properties: name, size, flags and color.

Plain Text
~~~~~~~~~~

Function :meth:`TextPage.extractText` (or *Page.get_text("text")*) extracts a page's plain **text in original order** as specified by the creator of the document.

An example output::

    >>> print(page.get_text("text"))
    Some text on first page.

.. note:: The output may not equal an accustomed "natural" reading order. However, you can request a reordering following the scheme "top-left to bottom-right" by executing `page.get_text("text", sort=True)`.


BLOCKS
~~~~~~~~~~

Function :meth:`TextPage.extractBLOCKS` (or *Page.get_text("blocks")*) extracts a page's text blocks as a list of items like::

    (x0, y0, x1, y1, "lines in block", block_no, block_type)

Where the first 4 items are the float coordinates of the block's bbox. The lines within each block are concatenated by a new-line character.

This is a high-speed method, which by default also extracts image meta information: Each image appears as a block with one text line, which contains meta information. The image itself is not shown.

As with simple text output above, the `sort` argument can be used as well to obtain a reading order.

Example output::

    >>> print(page.get_text("blocks", sort=False))
    [(50.0, 88.17500305175781, 166.1709747314453, 103.28900146484375,
    'Some text on first page.', 0, 0)]


WORDS
~~~~~~~~~~

Function :meth:`TextPage.extractWORDS` (or *Page.get_text("words")*) extracts a page's text **words** as a list of items like::

    (x0, y0, x1, y1, "word", block_no, line_no, word_no)

Where the first 4 items are the float coordinates of the words's bbox. The last three integers provide some more information on the word's whereabouts.

This is a high-speed method. As with the previous methods, argument `sort=True` will reorder the words.

Example output::

    >>> for word in page.get_text("words", sort=False):
            print(word)
    (50.0, 88.17500305175781, 78.73200225830078, 103.28900146484375,
    'Some', 0, 0, 0)
    (81.79000091552734, 88.17500305175781, 99.5219955444336, 103.28900146484375,
    'text', 0, 0, 1)
    (102.57999420166016, 88.17500305175781, 114.8119888305664, 103.28900146484375,
    'on', 0, 0, 2)
    (117.86998748779297, 88.17500305175781, 135.5909881591797, 103.28900146484375,
    'first', 0, 0, 3)
    (138.64898681640625, 88.17500305175781, 166.1709747314453, 103.28900146484375,
    'page.', 0, 0, 4)

HTML
~~~~

:meth:`TextPage.extractHTML` (or *Page.get_text("html")* output fully reflects the structure of the page's *TextPage* -- much like DICT / JSON below. This includes images, font information and text positions. If wrapped in HTML header and trailer code, it can readily be displayed by an internet browser. Our above example::

    >>> for line in page.get_text("html").splitlines():
            print(line)

    <div id="page0" style="position:relative;width:300pt;height:350pt;
    background-color:white">
    <p style="position:absolute;white-space:pre;margin:0;padding:0;top:88pt;
    left:50pt"><span style="font-family:Helvetica,sans-serif;
    font-size:11pt">Some text on first page.</span></p>
    </div>


.. _HTMLQuality:

Controlling Quality of HTML Output
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
While HTML output has improved a lot in MuPDF v1.12.0, it is not yet bug-free: we have found problems in the areas **font support** and **image positioning**.

* HTML text contains references to the fonts used of the original document. If these are not known to the browser (a fat chance!), it will replace them with others; the results will probably look awkward. This issue varies greatly by browser -- on my Windows machine, MS Edge worked just fine, whereas Firefox looked horrible.

* For PDFs with a complex structure, images may not be positioned and / or sized correctly. This seems to be the case for rotated pages and pages, where the various possible page bbox variants do not coincide (e.g. *MediaBox != CropBox*). We do not know yet, how to address this -- we filed a bug at MuPDF's site.

To address the font issue, you can use a simple utility script to scan through the HTML file and replace font references. Here is a little example that replaces all fonts with one of the :ref:`Base-14-Fonts`: serifed fonts will become "Times", non-serifed "Helvetica" and monospaced will become "Courier". Their respective variations for "bold", "italic", etc. are hopefully done correctly by your browser::

 import sys
 filename = sys.argv[1]
 otext = open(filename).read()                 # original html text string
 pos1 = 0                                      # search start poition
 font_serif = "font-family:Times"              # enter ...
 font_sans  = "font-family:Helvetica"          # ... your choices ...
 font_mono  = "font-family:Courier"            # ... here
 found_one  = False                            # true if search successful

 while True:
     pos0 = otext.find("font-family:", pos1)   # start of a font spec
     if pos0 < 0:                              # none found - we are done
         break
     pos1 = otext.find(";", pos0)              # end of font spec
     test = otext[pos0 : pos1]                 # complete font spec string
     testn = ""                                # the new font spec string
     if test.endswith(",serif"):               # font with serifs?
         testn = font_serif                    # use Times instead
     elif test.endswith(",sans-serif"):        # sans serifs font?
         testn = font_sans                     # use Helvetica
     elif test.endswith(",monospace"):         # monospaced font?
         testn = font_mono                     # becomes Courier

     if testn != "":                           # any of the above found?
         otext = otext.replace(test, testn)    # change the source
         found_one = True
         pos1 = 0                              # start over

 if found_one:
     ofile = open(filename + ".html", "w")
     ofile.write(otext)
     ofile.close()
 else:
     print("Warning: could not find any font specs!")



DICT (or JSON)
~~~~~~~~~~~~~~~~

:meth:`TextPage.extractDICT` (or *Page.get_text("dict", sort=False)*) output fully reflects the structure of a *TextPage* and provides image content and position detail (*bbox* -- boundary boxes in pixel units) for every block, line and span. Images are stored as *bytes* for DICT output and base64 encoded strings for JSON output.

For a visualization of the dictionary structure have a look at :ref:`textpagedict`.

Here is how this looks like::

    {
        "width": 300.0,
        "height": 350.0,
        "blocks": [{
            "type": 0,
            "bbox": (50.0, 88.17500305175781, 166.1709747314453, 103.28900146484375),
            "lines": ({
                "wmode": 0,
                "dir": (1.0, 0.0),
                "bbox": (50.0, 88.17500305175781, 166.1709747314453, 103.28900146484375),
                "spans": ({
                    "size": 11.0,
                    "flags": 0,
                    "font": "Helvetica",
                    "color": 0,
                    "origin": (50.0, 100.0),
                    "text": "Some text on first page.",
                    "bbox": (50.0, 88.17500305175781, 166.1709747314453, 103.28900146484375)
                })
            }]
        }]
    }

RAWDICT (or RAWJSON)
~~~~~~~~~~~~~~~~~~~~~
:meth:`TextPage.extractRAWDICT` (or *Page.get_text("rawdict", sort=False)*) is an **information superset of DICT** and takes the detail level one step deeper. It looks exactly like the above, except that the *"text"* items (*string*) in the spans are replaced by the list *"chars"*. Each *"chars"* entry is a character *dict*. For example, here is what you would see in place of item *"text": "Text in black color."* above::

    "chars": [{
        "origin": (50.0, 100.0),
        "bbox": (50.0, 88.17500305175781, 57.336997985839844, 103.28900146484375),
        "c": "S"
    }, {
        "origin": (57.33700180053711, 100.0),
        "bbox": (57.33700180053711, 88.17500305175781, 63.4530029296875, 103.28900146484375),
        "c": "o"
    }, {
        "origin": (63.4530029296875, 100.0),
        "bbox": (63.4530029296875, 88.17500305175781, 72.61600494384766, 103.28900146484375),
        "c": "m"
    }, {
        "origin": (72.61600494384766, 100.0),
        "bbox": (72.61600494384766, 88.17500305175781, 78.73200225830078, 103.28900146484375),
        "c": "e"
    }, {
        "origin": (78.73200225830078, 100.0),
        "bbox": (78.73200225830078, 88.17500305175781, 81.79000091552734, 103.28900146484375),
        "c": " "
    < ... deleted ... >
    }, {
        "origin": (163.11297607421875, 100.0),
        "bbox": (163.11297607421875, 88.17500305175781, 166.1709747314453, 103.28900146484375),
        "c": "."
    }],


XML
~~~

The :meth:`TextPage.extractXML` (or *Page.get_text("xml")*) version extracts text (no images) with the detail level of RAWDICT::

    >>> for line in page.get_text("xml").splitlines():
        print(line)

    <page id="page0" width="300" height="350">
    <block bbox="50 88.175 166.17098 103.289">
    <line bbox="50 88.175 166.17098 103.289" wmode="0" dir="1 0">
    <font name="Helvetica" size="11">
    <char quad="50 88.175 57.336999 88.175 50 103.289 57.336999 103.289" x="50"
    y="100" color="#000000" c="S"/>
    <char quad="57.337 88.175 63.453004 88.175 57.337 103.289 63.453004 103.289" x="57.337"
    y="100" color="#000000" c="o"/>
    <char quad="63.453004 88.175 72.616008 88.175 63.453004 103.289 72.616008 103.289" x="63.453004"
    y="100" color="#000000" c="m"/>
    <char quad="72.616008 88.175 78.732 88.175 72.616008 103.289 78.732 103.289" x="72.616008"
    y="100" color="#000000" c="e"/>
    <char quad="78.732 88.175 81.79 88.175 78.732 103.289 81.79 103.289" x="78.732"
    y="100" color="#000000" c=" "/>

    ... deleted ...

    <char quad="163.11298 88.175 166.17098 88.175 163.11298 103.289 166.17098 103.289" x="163.11298"
    y="100" color="#000000" c="."/>
    </font>
    </line>
    </block>
    </page>

.. note:: We have successfully tested `lxml <https://pypi.org/project/lxml/>`_ to interpret this output.

XHTML
~~~~~
:meth:`TextPage.extractXHTML` (or *Page.get_text("xhtml")*) is a variation of TEXT but in HTML format, containing the bare text and images ("semantic" output)::

    <div id="page0">
    <p>Some text on first page.</p>
    </div>

.. _text_extraction_flags:

Text Extraction Flags Defaults
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
* New in version 1.16.2: Method :meth:`Page.get_text` supports a keyword parameter *flags* *(int)* to control the amount and the quality of extracted data. The following table shows the defaults settings (flags parameter omitted or None) for each extraction variant. If you specify flags with a value other than *None*, be aware that you must set **all desired** options. A description of the respective bit settings can be found in :ref:`TextPreserve`.

* New in v1.19.6: The default combinations in the following table are now available as Python constants: :data:`TEXTFLAGS_TEXT`, :data:`TEXTFLAGS_WORDS`, :data:`TEXTFLAGS_BLOCKS`, :data:`TEXTFLAGS_DICT`, :data:`TEXTFLAGS_RAWDICT`, :data:`TEXTFLAGS_HTML`, :data:`TEXTFLAGS_XHTML`, :data:`TEXTFLAGS_XML`, and :data:`TEXTFLAGS_SEARCH`. You can now easily modify a default flag, e.g.

    - **include** images in a "blocks" output:
    
    `flags = TEXTFLAGS_BLOCKS | TEXT_PRESERVE_IMAGES`
    
    - **exclude** images from a "dict" output:
    
    `flags = TEXTFLAGS_DICT & ~TEXT_PRESERVE_IMAGES`
    
    - set **dehyphenation off** in text searches:
    
    `flags = TEXTFLAGS_SEARCH & ~TEXT_DEHYPHENATE`


========================= ==== ==== ===== === ==== ======= ===== ====== ======
Indicator                 text html xhtml xml dict rawdict words blocks search
========================= ==== ==== ===== === ==== ======= ===== ====== ======
preserve ligatures        1    1    1     1   1    1       1     1       0
preserve whitespace       1    1    1     1   1    1       1     1       1
preserve images           n/a  1    1     n/a 1    1       n/a   0       0
inhibit spaces            0    0    0     0   0    0       0     0       0
dehyphenate               0    0    0     0   0    0       0     0       1
clip to mediabox          1    1    1     1   1    1       1     1       1
use CID instead of U+FFFD 1    1    1     1   1    1       1     1       0
========================= ==== ==== ===== === ==== ======= ===== ====== ======

* **search** refers to the text search function.
* **"json"** is handled exactly like **"dict"** and is hence left out.
* **"rawjson"** is handled exactly like **"rawdict"** and is hence left out.
* An "n/a" specification means a value of 0 and setting this bit never has any effect on the output (but an adverse effect on performance).
* If you are not interested in images when using an output variant which includes them by default, then by all means set the respective bit off: You will experience a better performance and much lower space requirements.

To show the effect of `TEXT_INHIBIT_SPACES` have a look at this example::

    >>> print(page.get_text("text"))
    H a l l o !
    Mo r e  t e x t
    i s  f o l l o w i n g
    i n  E n g l i s h
    . . .  l e t ' s  s e e
    w h a t  h a p p e n s .
    >>> print(page.get_text("text", flags=pymupdf.TEXT_INHIBIT_SPACES))
    Hallo!
    More text
    is following
    in English
    ... let's see
    what happens.
    >>>


Performance
~~~~~~~~~~~~
The text extraction methods differ significantly both: in terms of information they supply, and in terms of resource requirements and runtimes. Generally, more information of course means, that more processing is required and a higher data volume is generated.

.. note:: Especially images have a **very significant** impact. Make sure to exclude them (via the *flags* parameter) whenever you do not need them. To process the below mentioned 2'700 total pages with default flags settings required 160 seconds across all extraction methods. When all images where excluded, less than 50% of that time (77 seconds) were needed.

To begin with, all methods are **very fast** in relation to other products out there in the market. In terms of processing speed, we are not aware of a faster (free) tool. Even the most detailed method, RAWDICT, processes all 1'310 pages of the :ref:`AdobeManual` in less than 5 seconds (simple text needs less than 2 seconds here).

The following table shows average relative speeds ("RSpeed", baseline 1.00 is TEXT), taken across ca. 1400 text-heavy and 1300 image-heavy pages.

======= ====== ===================================================================== ==========
Method  RSpeed Comments                                                               no images
======= ====== ===================================================================== ==========
TEXT     1.00  no images, **plain** text, line breaks                                 1.00
BLOCKS   1.00  image bboxes (only), **block** level text with bboxes, line breaks     1.00
WORDS    1.02  no images, **word** level text with bboxes                             1.02
XML      2.72  no images, **char** level text, layout and font details                2.72
XHTML    3.32  **base64** images, **span** level text, no layout info                 1.00
HTML     3.54  **base64** images, **span** level text, layout and font details        1.01
DICT     3.93  **binary** images, **span** level text, layout and font details        1.04
RAWDICT  4.50  **binary** images, **char** level text, layout and font details        1.68
======= ====== ===================================================================== ==========

As mentioned: when excluding image extraction (last column), the relative speeds are changing drastically: except RAWDICT and XML, the other methods are almost equally fast, and RAWDICT requires 40% less execution time than the **now slowest XML**.

Look at chapter **Appendix 1** for more performance information.

.. include:: footer.rst
