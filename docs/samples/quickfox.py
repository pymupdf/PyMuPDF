"""
This is a demo script using PyMuPDF's Story class to output text as a PDF with
a two-column page layout.

The script demonstrates the following features:
* How to fill columns or table cells of complex page layouts
* How to embed images
* How to modify existing, given HTML sources for output (text indent, font size)
* How to use fonts defined in package "pymupdf-fonts"
* How to use ZIP files as Archive

--------------
The example is taken from the somewhat modified Wikipedia article
https://en.wikipedia.org/wiki/The_quick_brown_fox_jumps_over_the_lazy_dog.
--------------
"""

import io
import os
import zipfile
import fitz


thisdir = os.path.dirname(os.path.abspath(__file__))
myzip = zipfile.ZipFile(os.path.join(thisdir, "quickfox.zip"))
arch = fitz.Archive(myzip)

if fitz.fitz_fontdescriptors:
    # we want to use the Ubuntu fonts for sans-serif and for monospace
    CSS = fitz.css_for_pymupdf_font("ubuntu", archive=arch, name="sans-serif")
    CSS = fitz.css_for_pymupdf_font("ubuntm", CSS=CSS, archive=arch, name="monospace")
else:
    # No pymupdf-fonts available.
    CSS=""

docname = __file__.replace(".py", ".pdf")  # output PDF file name

HTML = myzip.read("quickfox.html").decode()

# make the Story object
story = fitz.Story(HTML, user_css=CSS, archive=arch)

# --------------------------------------------------------------
# modify the DOM somewhat
# --------------------------------------------------------------
body = story.body  # access HTML body
body.set_properties(font="sans-serif")  # and give it our font globally

# modify certain nodes
para = body.find("p", None, None)  # find relevant nodes (here: paragraphs)
while para != None:
    para.set_properties(  # method MUST be used for existing nodes
        indent=15,
        fontsize=13,
    )
    para = para.find_next("p", None, None)

# choose PDF page size
MEDIABOX = fitz.paper_rect("letter")
# text appears only within this subrectangle
WHERE = MEDIABOX + (36, 36, -36, -36)

# --------------------------------------------------------------
# define page layout within the WHERE rectangle
# --------------------------------------------------------------
COLS = 2  # layout: 2 cols 1 row
ROWS = 1
TABLE = fitz.make_table(WHERE, cols=COLS, rows=ROWS)
# fill the cells of each page in this sequence:
CELLS = [TABLE[i][j] for i in range(ROWS) for j in range(COLS)]

fileobject = io.BytesIO()  # let DocumentWriter write to memory
writer = fitz.DocumentWriter(fileobject)  # define the writer

more = 1
while more:  # loop until all input text has been written out
    dev = writer.begin_page(MEDIABOX)  # prepare a new output page
    for cell in CELLS:
        # content may be complete after any cell, ...
        if more:  # so check this status first
            more, _ = story.place(cell)
            story.draw(dev)
    writer.end_page()  # finish the PDF page

writer.close()  # close DocumentWriter output

# for housekeeping work re-open from memory
doc = fitz.open("pdf", fileobject)
doc.ez_save(docname)
