======================================
Appendix 2: Details on Text Extraction
======================================
This chapter provides background on the text extraction methods of PyMuPDF.

Information of interest are

* what do they provide?
* what do they imply (processing time / data sizes)?

General structure of a TextPage
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Text information contained in a :ref:`TextPage` adheres to the following hierarchy:
::
 <page> (width and height)
     <block> (its rectangle)
         <line> (its rectangle)
             <span> (its rectangle and font information)
                 <char> (its rectangle, (x, y) coordinates and value)

A **text page** consists of blocks (= roughly paragraphs).

A **block** consists of lines.

A **line** consists of spans.

A **span** consists of characters with the same properties. E.g. a different font will cause a new span.

Output of ``getText(output="text")``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This function extracts a page's plain **text in original order** as specified by the creator of the document (which may not be equal to a natural reading order!).

An example output of this tutorial's PDF version:
::
 Tutorial

 This tutorial will show you the use of MuPDF in Python step by step.

 Because MuPDF supports not only PDF, but also XPS, OpenXPS and EPUB formats, so does PyMuPDF.

 Nevertheless we will only talk about PDF files for the sake of brevity.
 ...

Output of ``getText(output="html")``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

HTML output reflects the structure of the page's ``TextPage`` - without adding much other benefit. Again an example:
::
 <div class="page">
 <div class="block"><p>
 <div class="metaline"><div class="line"><div class="cell" style="width:0%;align:left"><span class="s0">Tutorial</span></div></div>
 </div></p></div>
 <div class="block"><p>
 <div class="line"><div class="cell" style="width:0%;align:left"><span class="s1">This tutorial will show you the use of MuPDF in Python step by step.</span></div></div>
 </div></p></div>
 <div class="block"><p>
 <div class="line"><div class="cell" style="width:0%;align:left"><span class="s1">Because MuPDF supports not only PDF, but also XPS, OpenXPS and EPUB formats, so does PyMuPDF.</span></div></div>
 <div class="line"><div class="cell" style="width:0%;align:left"><span class="s1">Nevertheless we will only talk about PDF files for the sake of brevity.</span></div></div>
 </div></p></div>
 ...

Output of ``getText(output="json")``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

JSON output reflects the structure of a ``TextPage`` and provides position details (``bbox`` - boundary boxes in pixel units) for every block, line and span. This is enough information to present a page's text in any required reading order (e.g. from top-left to bottom-right). The output can obviously be made usable by ``text_dict = json.loads(text)``. Have a look at our example program ``PDF2textJS.py``. Here is how it looks like:
::
 {
  "len":35,"width":595.2756,"height":841.8898,
  "blocks":[
   {"type":"text","bbox":[40.01575, 53.730354, 98.68775, 76.08236],
    "lines":[
       {"bbox":[40.01575, 53.730354, 98.68775, 76.08236],
        "spans":[
          {"bbox":[40.01575, 53.730354, 98.68775, 76.08236],
           "text":"Tutorial"
          }
        ]
       }
    ]
   },
   {"type":"text","bbox":[40.01575, 79.300354, 340.6957, 93.04035],
    "lines":[
       {"bbox":[40.01575, 79.300354, 340.6957, 93.04035],
        "spans":[
          {"bbox":[40.01575, 79.300354, 340.6957, 93.04035],
           "text":"This tutorial will show you the use of MuPDF in Python step by step."
          }
        ]
       }
    ]
   },
 ...


Output of ``getText(output="xml")``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The XML version takes the level of detail even a lot deeper: every single character is provided with its position detail, and every span also contains font information:
::
 <page width="595.2756" height="841.8898">
 <block bbox="40.01575 53.730354 98.68775 76.08236">
 <line bbox="40.01575 53.730354 98.68775 76.08236">
 <span bbox="40.01575 53.730354 98.68775 76.08236" font="Helvetica-Bold" size="16">
 <char bbox="40.01575 53.730354 49.79175 76.08236" x="40.01575" y="70.85036" c="T"/>
 <char bbox="49.79175 53.730354 59.56775 76.08236" x="49.79175" y="70.85036" c="u"/>
 <char bbox="59.56775 53.730354 64.89575 76.08236" x="59.56775" y="70.85036" c="t"/>
 <char bbox="64.89575 53.730354 74.67175 76.08236" x="64.89575" y="70.85036" c="o"/>
 <char bbox="74.67175 53.730354 80.89575 76.08236" x="74.67175" y="70.85036" c="r"/>
 <char bbox="80.89575 53.730354 85.34375 76.08236" x="80.89575" y="70.85036" c="i"/>
 <char bbox="85.34375 53.730354 94.23975 76.08236" x="85.34375" y="70.85036" c="a"/>
 <char bbox="94.23975 53.730354 98.68775 76.08236" x="94.23975" y="70.85036" c="l"/>
 </span>
 </line>
 </block>
 <block bbox="40.01575 79.300354 340.6957 93.04035">
 <line bbox="40.01575 79.300354 340.6957 93.04035">
 <span bbox="40.01575 79.300354 340.6957 93.04035" font="Helvetica" size="10">
 <char bbox="40.01575 79.300354 46.12575 93.04035" x="40.01575" y="90.050354" c="T"/>
 <char bbox="46.12575 79.300354 51.685753 93.04035" x="46.12575" y="90.050354" c="h"/>
 <char bbox="51.685753 79.300354 53.90575 93.04035" x="51.685753" y="90.050354" c="i"/>
 <char bbox="53.90575 79.300354 58.90575 93.04035" x="53.90575" y="90.050354" c="s"/>
 <char bbox="58.90575 79.300354 61.685753 93.04035" x="58.90575" y="90.050354" c=" "/>
 <char bbox="61.685753 79.300354 64.46575 93.04035" x="61.685753" y="90.050354" c="t"/>
 <char bbox="64.46575 79.300354 70.02576 93.04035" x="64.46575" y="90.050354" c="u"/>
 <char bbox="70.02576 79.300354 72.805756 93.04035" x="70.02576" y="90.050354" c="t"/>
 <char bbox="72.805756 79.300354 78.36575 93.04035" x="72.805756" y="90.050354" c="o"/>
 <char bbox="78.36575 79.300354 81.695755 93.04035" x="78.36575" y="90.050354" c="r"/>
 <char bbox="81.695755 79.300354 83.91576 93.04035" x="81.695755" y="90.050354" c="i"/>
 ...

The method's output can be processed by one of Python's XML modules. We have successfully tested ``lxml``. See the demo program ``fontlister.py``. It creates a list of all fonts of a document including font size and where used on pages.

Performance
~~~~~~~~~~~~
The four text extraction methods of a :ref:`TextPage` differ significantly: in terms of information they supply (see above), and in terms of resource requirements. More information of course means that more processing is required and a higher data volume is generated.

To begin with, all four methods are **very** fast in relation to what is there on the market. In terms of processing speed, we couldn't find a faster (free) tool.

Relative to each other, ``xml`` is about 2 times slower than ``text``, the other three range between them. E.g. ``json`` needs about 13% - 14% more time than ``text``.

Look into the previous chapter **Appendix 1** for more performance information.
