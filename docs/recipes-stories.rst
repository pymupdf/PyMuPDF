.. include:: header.rst

.. _RecipesStories:

.. role:: htmlTag(emphasis)

.. |toggleStart| raw:: html

   <details>
   <summary><a>See recipe</a></summary>

.. |toggleEnd| raw:: html

   </details>

==============================
Stories
==============================

This document showcases some typical use cases for :ref:`Stories<WorkingWithStories>`.

As mentioned in the :ref:`tutorial<WorkingWithStories>`, stories may be created using up to three input sources: HTML, CSS and Archives -- all of which are optional and which, respectively, can be provided programmatically.

The following examples will showcase combinations for using these inputs.

.. note::

        Many of these recipe's source code are included as examples in the `docs` folder.


.. _RecipesStories_A:

How to Add a Line of Text with Some Formatting
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here is the inevitable "Hello World" example. We will show two variants:

1. Create using existing HTML source [#f1]_, that may come from anywhere.
2. Create using the Python API.

-----

Variant using an existing HTML source [#f1]_ -- which in this case is defined as a constant in the script::

    import pymupdf

    HTML = """
    <p style="font-family: sans-serif;color: blue">Hello World!</p>
    """

    MEDIABOX = pymupdf.paper_rect("letter")  # output page format: Letter
    WHERE = MEDIABOX + (36, 36, -36, -36)  # leave borders of 0.5 inches

    story = pymupdf.Story(html=HTML)  # create story from HTML
    writer = pymupdf.DocumentWriter("output.pdf")  # create the writer
    
    more = 1  # will indicate end of input once it is set to 0

    while more:  # loop outputting the story
        device = writer.begin_page(MEDIABOX)  # make new page
        more, _ = story.place(WHERE)  # layout into allowed rectangle
        story.draw(device)  # write on page
        writer.end_page()  # finish page
    
    writer.close()  # close output file

.. note::
    
    The above effect (sans-serif and blue text) could have been achieved by using a separate CSS source like so::

        import pymupdf

        CSS = """
        body {
            font-family: sans-serif;
            color: blue;
        }
        """

        HTML = """
        <p>Hello World!</p>
        """

        # the story would then be created like this:
        story = pymupdf.Story(html=HTML, user_css=CSS)


-----

The Python API variant -- everything is created programmatically::

    import pymupdf
    
    MEDIABOX = pymupdf.paper_rect("letter")
    WHERE = MEDIABOX + (36, 36, -36, -36)

    story = pymupdf.Story()  # create an empty story
    body = story.body  # access the body of its DOM
    with body.add_paragraph() as para:  # store desired content
        para.set_font("sans-serif").set_color("blue").add_text("Hello World!")

    writer = pymupdf.DocumentWriter("output.pdf")
    
    more = 1

    while more:
        device = writer.begin_page(MEDIABOX)
        more, _ = story.place(WHERE)
        story.draw(device)
        writer.end_page()

    writer.close()

Both variants will produce the same output PDF.

-----

.. _RecipesStories_B:


How to use Images
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Images can be referenced in the provided HTML source, or the reference to a desired image can also be stored via the Python API. In any case, this requires using an :ref:`Archive`, which refers to the place where the image can be found.

.. note:: Images with the binary content embedded in the HTML source are **not supported** by stories.

We extend our "Hello World" example from above and display an image of our planet right after the text. Assuming the image has the name "world.jpg" and is present in the script's folder, then this is the modified version of the above Python API variant::

    import pymupdf

    MEDIABOX = pymupdf.paper_rect("letter")
    WHERE = MEDIABOX + (36, 36, -36, -36)

    # create story, let it look at script folder for resources
    story = pymupdf.Story(archive=".")
    body = story.body  # access the body of its DOM

    with body.add_paragraph() as para:
        # store desired content
        para.set_font("sans-serif").set_color("blue").add_text("Hello World!")

    # another paragraph for our image:
    with body.add_paragraph() as para:
        # store image in another paragraph
        para.add_image("world.jpg")

    writer = pymupdf.DocumentWriter("output.pdf")

    more = 1

    while more:
        device = writer.begin_page(MEDIABOX)
        more, _ = story.place(WHERE)
        story.draw(device)
        writer.end_page()

    writer.close()


-----


.. _RecipesStories_C:


How to Read External HTML and CSS for a Story
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These cases are fairly straightforward.

As a general recommendation, HTML and CSS sources should be **read as binary files** and decoded before using them in a story. The Python `pathlib.Path` provides convenient ways to do this::

    import pathlib
    import pymupdf

    htmlpath = pathlib.Path("myhtml.html")
    csspath = pathlib.Path("mycss.css")

    HTML = htmlpath.read_bytes().decode()
    CSS = csspath.read_bytes().decode()

    story = pymupdf.Story(html=HTML, user_css=CSS)


-----


.. _RecipesStories_D:


How to Output Database Content with Story Templates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This script demonstrates how to report SQL database content using an **HTML template**.



The example SQL database contains two tables:

1. Table "films" contains one row per film with the fields **"title"**, **"director"** and (release) **"year"**.
2. Table "actors" contains one row per actor and film title (fields (actor) **"name"** and (film) **"title"**).

The story DOM consists of a template for one film, which reports film data together with a list of casted actors.

**Files:**

* `docs/samples/filmfestival-sql.py`
* `docs/samples/filmfestival-sql.db`


|toggleStart|

.. literalinclude:: samples/filmfestival-sql.py

|toggleEnd|


-----


.. _RecipesStories_E:

How to Integrate with Existing PDFs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Because a :ref:`DocumentWriter` can only write to a new file, stories cannot be placed on existing pages. This script demonstrates a circumvention of this restriction.

The basic idea is letting :ref:`DocumentWriter` output to a PDF in memory. Once the story has finished, we re-open this memory PDF and put its pages to desired locations on **existing** pages via method :meth:`Page.show_pdf_page`.

**Files:**

* `docs/samples/showpdf-page.py`

|toggleStart|

.. literalinclude:: samples/showpdf-page.py

|toggleEnd|


-----


.. _RecipesStories_F:

How to Make Multi-Columned Layouts and Access Fonts from Package `pymupdf-fonts`_
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This script outputs an article (taken from Wikipedia) that contains text and multiple images and uses a 2-column page layout.

In addition, two "Ubuntu" font families from package `pymupdf-fonts`_ are used instead of defaulting to Base-14 fonts.

Yet another feature used here is that all data -- the images and the article HTML -- are jointly stored in a ZIP file.


**Files:**

* `docs/samples/quickfox.py`
* `docs/samples/quickfox.zip`


|toggleStart|

.. literalinclude:: samples/quickfox.py

|toggleEnd|


-----


.. _RecipesStories_G:

How to Make a Layout which Wraps Around a Predefined "no go area" Layout
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


This is a demo script using PyMuPDF's Story class to output text as a PDF with
a two-column page layout.

The script demonstrates the following features:

* Layout text around images of an existing ("target") PDF.
* Based on a few global parameters, areas on each page are identified, that
  can be used to receive text layouted by a Story.
* These global parameters are not stored anywhere in the target PDF and
  must therefore be provided in some way:

  - The width of the border(s) on each page.
  - The fontsize to use for text. This value determines whether the provided
    text will fit in the empty spaces of the (fixed) pages of target PDF. It
    cannot be predicted in any way. The script ends with an exception if
    target PDF has not enough pages, and prints a warning message if not all
    pages receive at least some text. In both cases, the FONTSIZE value
    can be changed (a float value).
  - Use of a 2-column page layout for the text.
* The layout creates a temporary (memory) PDF. Its produced page content
  (the text) is used to overlay the corresponding target page. If text
  requires more pages than are available in target PDF, an exception is raised.
  If not all target pages receive at least some text, a warning is printed.
* The script reads "image-no-go.pdf" in its own folder. This is the "target" PDF.
  It contains 2 pages with each 2 images (from the original article), which are
  positioned at places that create a broad overall test coverage. Otherwise the
  pages are empty.
* The script produces "quickfox-image-no-go.pdf" which contains the original pages
  and image positions, but with the original article text laid out around them.

**Files:**

* `docs/samples/quickfox-image-no-go.py`
* `docs/samples/quickfox-image-no-go.pdf`
* `docs/samples/quickfox.zip`


|toggleStart|

.. literalinclude:: samples/quickfox-image-no-go.py

|toggleEnd|


-----


.. _RecipesStories_H:

How to Output an HTML Table
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Outputting HTML tables is supported as follows:

* Flat table layouts are supported ("rows x columns"), no support of the "colspan" / "rowspan" attributes.
* Table header tag :htmlTag:`th` supports attribute "scope" with values "row" or "col". Applicable text will be bold by default.
* Column widths are computed automatically based on column content. They cannot be directly set.
* Table **cells may contain images** which will be considered in the column width calculation magic.
* Row heights are computed automatically based on row content - leading to multi-line rows where needed.
* The potentially multiple lines of a table row will always be kept together on one page (respectively "where" rectangle) and not be split.
* Table header rows are only **shown on the first page / "where" rectangle.**
* The "style" attribute is ignored when given directly in HTML table elements. Styling for a table and its elements must happen separately, in CSS source or within the :htmlTag:`style` tag.
* Styling for :htmlTag:`tr` elements is not supported and ignored. Therefore, a table-wide grid or alternating row background colors are not supported. One of the following example scripts however shows an easy way to deal with this limitation.

**Files:**

* `docs/samples/table01.py` This script reflects basic features.

|toggleStart|

.. literalinclude:: samples/table01.py

|toggleEnd|

* `docs/samples/national-capitals.py` Advanced script extending table output options using simple additional code:

    - Multi-page output simulating **repeating header rows**
    - Alternating table row background colors
    - Table rows and columns delimited by gridlines
    - Table rows dynamically generated / filled with data from an SQL database

|toggleStart|

.. literalinclude:: samples/national-capitals.py

|toggleEnd|


-----


.. _RecipesStories_I:

How to Create a Simple Grid Layout
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By creating a sequence of :ref:`Story` objects within a grid created via the :ref:`make_table<Functions_make_table>` function a developer can create grid layouts as required.

**Files:**

* `docs/samples/simple-grid.py`

|toggleStart|

.. literalinclude:: samples/simple-grid.py

|toggleEnd|


-----


.. _RecipesStories_J:

How to Generate a Table of Contents
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This script lists the source code of all Python scripts that live in the script's directory.

**Files:**

* `docs/samples/code-printer.py`

|toggleStart|

.. literalinclude:: samples/code-printer.py

|toggleEnd|


It features the following capabilities:

* Automatic generation of a Table of Contents (TOC) on separately numbered pages at the start of the document - using a specialized :ref:`Story`.

* Use of 3 separate :ref:`Story` objects per page: header story, footer story and the story for printing the Python sources.

    - The page **footer is automatically changed** to show the name of the current Python file.

* Use of :meth:`Story.element_positions` to collect the data for the TOC and for the dynamic adjustment of page footers. This is an example of a **bidirectional communication** between the story output process and the script.

* The main PDF with the Python sources is being written to memory by its :ref:`DocumentWriter`. Another :ref:`Story` / :ref:`DocumentWriter` pair is then used to create a (memory) PDF for the TOC pages. Finally, both these PDFs are joined and the result stored to disk.


-----


.. _RecipesStories_K:

How to Display a List from JSON Data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This example takes some JSON data input which it uses to populate a :ref:`Story`. It also contains some visual text formatting and shows how to add links.


**Files:**

* `docs/samples/json-example.py`

|toggleStart|

.. literalinclude:: samples/json-example.py

|toggleEnd|



-----


.. _RecipesStories_L:

Using the Alternative :meth:`Story.write*()` functions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :meth:`Story.write*()` functions provide a different way to use the
:ref:`Story` functionality, removing the need for calling code to implement
a loop that calls :meth:`Story.place()` and :meth:`Story.draw()` etc, at the
expense of having to provide at least a `rectfn()` callback.


.. _RecipesStories_L_a:

How to do Basic Layout with :meth:`Story.write()`
-------------------------------------------------

This script lays out multiple copies of its own source code, into four
rectangles per page.

**Files:**

* `docs/samples/story-write.py`

|toggleStart|

.. literalinclude:: samples/story-write.py

|toggleEnd|


-----


.. _RecipesStories_L_b:

How to do Iterative Layout for a Table of Contents with :meth:`Story.write_stabilized()`
----------------------------------------------------------------------------------------

This script creates html content dynamically, adding a contents section based
on :ref:`ElementPosition` items that have non-zero `.heading` values.

The contents section is at the start of the document, so modifications to the
contents can change page numbers in the rest of the document, which in turn can
cause page numbers in the contents section to be incorrect.

So the script uses :meth:`Story.write_stabilized()` to repeatedly lay things
out until things are stable.


**Files:**

* `docs/samples/story-write-stabilized.py`

|toggleStart|

.. literalinclude:: samples/story-write-stabilized.py

|toggleEnd|



-----

.. _RecipesStories_L_c:

How to do Iterative Layout and Create PDF Links with :meth:`Story.write_stabilized_links()`
-------------------------------------------------------------------------------------------

This script is similar to the one described in "How to use
:meth:`Story.write_stabilized()`" above, except that the generated PDF also
contains links that correspond to the internal links in the original html.

This is done by using :meth:`Story.write_stabilized_links()`; this is slightly
different from :meth:`Story.write_stabilized()`:

* It does not take a :ref:`DocumentWriter` `writer` arg.
* It returns a PDF :ref:`Document` instance.

[The reasons for this are a little involved; for example a
:ref:`DocumentWriter` is not necessarily a PDF writer, so doesn't really work
in a PDF-specific API.]


**Files:**

* `docs/samples/story-write-stabilized-links.py`

|toggleStart|

.. literalinclude:: samples/story-write-stabilized-links.py

|toggleEnd|



-----


.. rubric:: Footnotes

.. [#f1] HTML & CSS support

    .. note::

        At the time of writing the HTML engine for Stories is fairly basic and supports a subset of CSS2 attributes.

    Some important CSS support to consider:

    - The only available layout is relative layout.
    - `background` is unavailable, use `background-color` instead.
    - `float` is unavailable.


.. include:: footer.rst

.. External Links:

.. _pymupdf-fonts: https://github.com/pymupdf/pymupdf-fonts



