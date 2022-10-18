.. _RecipesStories:


.. |toggleStart| raw:: html

   <details>
   <summary><a>See recipe</a></summary>

.. |toggleEnd| raw:: html

   </details>

==============================
Recipes: Stories
==============================

This document showcases some typical use cases for :ref:`Stories<WorkingWithStories>`.

As mentioned in the :ref:`tutorial<WorkingWithStories>`, stories may be created using up to three input sources: HTML, CSS and Archives -- all of which are optional and which, respectively, can be provided programmatically.

The following examples will showcase combinations for using these inputs.

.. note::

        Many of these recipe's source code are included as examples in the ``docs`` folder.

How to add a line of text with some formatting
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here is the inevitable "Hello World" example. We will show two variants:

1. Create using existing HTML source, that may come from anywhere.
2. Create using the Python API.

-----

Variant using an existing HTML source -- which in this case is defined as a constant in the script::

    import fitz

    HTML = """
    <p style="font-family: sans-serif;color: blue">Hello World!</p>
    """

    MEDIABOX = fitz.paper_rect("letter")  # output page format: Letter
    WHERE = MEDIABOX + (36, 36, -36, -36)  # leave borders of 0.5 inches

    story = fitz.Story(html=HTML)  # create story from HTML
    writer = fitz.DocumentWriter("output.pdf")  # create the writer
    
    more = 1  # will indicate end of input once it is set to 0

    while more:  # loop outputting the story
        device = writer.begin_page(MEDIABOX)  # make new page
        more, _ = story.place(WHERE)  # layout into allowed rectangle
        story.draw(device)  # write on page
        writer.end_page()  # finish page
    
    writer.close()  # close output file

.. note::
    
    The above effect (sanf-serif and blue text) could have been achieved by using a separate CSS source like so::

        import fitz

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
        story = fitz.Story(html=HTML, user_css=CSS)


-----

The Python API variant -- everything is created programmatically::

    import fitz
    
    MEDIABOX = fitz.paper_rect("letter")
    WHERE = MEDIABOX + (36, 36, -36, -36)

    story = fitz.Story()  # create an empty story
    body = story.body  # access the body of its DOM
    with body.add_paragraph() as para:  # store desired content
        para.set_font("sans-serif").set_color("blue").add_text("Hello World!")

    writer = fitz.DocumentWriter("output.pdf")
    
    more = 1

    while more:
        device = writer.begin_page(MEDIABOX)
        more, _ = story.place(WHERE)
        story.draw(device)
        writer.end_page()

    writer.close()

Both variants will produce the same output PDF.

-----

How to use images
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Images can be referenced in the provided HTML source, or the reference to a desired image can also be stored via the Python API. In any case, this requires using an :ref:`Archive`, which refers to the place where the image can be found.

.. note:: Images with the binary content embedded in the HTML source are **not supported** by stories.

We extend our "Hello World" example from above and display an image of our planet right after the text. Assuming the image has the name "world.jpg" and is present in the script's folder, then this is the modified version of the above Python API variant::

    import fitz

    MEDIABOX = fitz.paper_rect("letter")
    WHERE = MEDIABOX + (36, 36, -36, -36)

    # create story, let it look at script folder for resources
    story = fitz.Story(archive=".")
    body = story.body  # access the body of its DOM

    with body.add_paragraph() as para:
        # store desired content
        para.set_font("sans-serif").set_color("blue").add_text("Hello World!")

    # another paragraph for our image:
    with body.add_paragraph() as para:
        # store image in another paragraph
        para.add_image("world.jpg")

    writer = fitz.DocumentWriter("output.pdf")

    more = 1

    while more:
        device = writer.begin_page(MEDIABOX)
        more, _ = story.place(WHERE)
        story.draw(device)
        writer.end_page()

    writer.close()


-----


Reading External HTML and CSS for a Story
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These cases are fairly straightforward.

As a general recommendation, HTML and CSS sources should be **read as binary files** and decoded before using them in a story. The Python ``pathlib.Path`` provides convenient ways to do this::

    import pathlib
    import fitz

    htmlpath = pathlib.Path("myhtml.html")
    csspath = pathlib.Path("mycss.css")

    HTML = htmlpath.read_bytes().decode()
    CSS = csspath.read_bytes().decode()

    story = fitz.Story(html=HTML, user_css=CSS)


-----


How to Output Database Content with Story Templates 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This script demonstrates how to report SQL database content using an **HTML template**.



The example SQL database contains two tables:

1. Table "films" contains one row per film with the fields **"title"**, **"director"** and (release) **"year"**.
2. Table "actors" contains one row per actor and film title (fields (actor) **"name"** and (film) **"title"**).

The story DOM consists of a template for one film, which reports film data together with a list of casted actors.

``docs/`` files ``filmfestival-sql.py`` & ``filmfestival-sql.db``.


|toggleStart|

.. literalinclude:: filmfestival-sql.py

|toggleEnd|


-----


How to integrate with existing PDFs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Because a :ref:`DocumentWriter` can only write to a new file, stories cannot be placed on existing pages. This script demonstrates a circumvention of this restriction.

The basic idea is letting :ref:`DocumentWriter` output to a PDF in memory. Once the story has finished, we re-open this memory PDF and put its pages to desired locations on **existing** pages via method :meth:`Page.show_pdf_page`.

``docs/`` file ``showpdf-page.py``.

|toggleStart|

.. literalinclude:: showpdf-page.py

|toggleEnd|


-----


How to Make Multi-Columned Layouts and Access Fonts from Package `pymupdf-fonts <https://github.com/pymupdf/pymupdf-fonts>`_
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This script outputs an article (taken from Wikipedia) that contains text and multiple images and uses a 2-column page layout.

In addition, two "Ubuntu" font families from package `pymupdf-fonts <https://github.com/pymupdf/pymupdf-fonts>`_ are used instead of defaulting to Base-14 fonts.

Yet another feature used here is that all data -- the images and the article HTML -- are jointly stored in a ZIP file.


``docs/`` files ``quickfox.py`` & ``quickfox.zip``.


|toggleStart|

.. literalinclude:: quickfox.py

|toggleEnd|


-----


How to output a table
~~~~~~~~~~~~~~~~~~~~~~~~

Support for HTML tables is yet not complete in MuPDF. It is however possible to output tables with equal column widths that do not cross page boundaries.

This script reflects existing features.

``docs/`` file ``table01.py``.

|toggleStart|

.. literalinclude:: table01.py

|toggleEnd|


-----


How to Generate a Table of Contents
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This script lists the source code of all Python scripts that live in the script's directory.

``docs/`` file ``code-printer.py``.

|toggleStart|

.. literalinclude:: code-printer.py

|toggleEnd|


It features the following capabilities:

* Automatic generation of a Table of Contents (TOC) on separately numbered pages at the start of the document - using a specialized :ref:`Story`.

* Use of 3 separate :ref:`Story` objects per page: header story, footer story and the story for printing the Python sources.

    - The page **footer is automatically changed** to show the name of the current Python file.

* Use of :meth:`Story.element_positions` to collect the data for the TOC and for the dynamic adjustment of page footers. This is an example of a **bidirectional communication** between the story output process and the script.

* The main PDF with the Python sources is being written to memory by its :ref:`DocumentWriter`. Another :ref:`Story` / :ref:`DocumentWriter` pair is then used to create a (memory) PDF for the TOC pages. Finally, both these PDFs are joined and the result stored to disk.

