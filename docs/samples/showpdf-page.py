"""
Demo of Story class in PyMuPDF
-------------------------------

This script demonstrates how to the results of a fitz.Story output can be
placed in a rectangle of an existing (!) PDF page.

"""
import io
import os

import fitz


def make_pdf(fileptr, text, rect, font="sans-serif", archive=None):
    """Make a memory DocumentWriter from HTML text and a rect.

    Args:
        fileptr: a Python file object. For example an io.BytesIO().
        text: the text to output (HTML format)
        rect: the target rectangle. Will use its width / height as mediabox
        font: (str) font family name, default sans-serif
        archive: fitz.Archive parameter. To be used if e.g. images or special
                fonts should be used.
    Returns:
        The matrix to convert page rectangles of the created PDF back
        to rectangle coordinates in the parameter "rect".
        Normal use will expect to fit all the text in the given rect.
        However, if an overflow occurs, this function will output multiple
        pages, and the caller may decide to either accept or retry with
        changed parameters.
    """
    # use input rectangle as the page dimension
    mediabox = fitz.Rect(0, 0, rect.width, rect.height)
    # this matrix converts mediabox back to input rect
    matrix = mediabox.torect(rect)

    story = fitz.Story(text, archive=archive)
    body = story.body
    body.set_properties(font=font)
    writer = fitz.DocumentWriter(fileptr)
    while True:
        device = writer.begin_page(mediabox)
        more, _ = story.place(mediabox)
        story.draw(device)
        writer.end_page()
        if not more:
            break
    writer.close()
    return matrix


# -------------------------------------------------------------
# We want to put this in a given rectangle of an existing page
# -------------------------------------------------------------
HTML = """
<p>PyMuPDF is a great package! And it still improves significantly from one version to the next one!</p>
<p>It is a Python binding for <b>MuPDF</b>, a lightweight PDF, XPS, and E-book viewer, renderer, and toolkit.<br> Both are maintained and developed by Artifex Software, Inc.</p>
<p>Via MuPDF it can access files in PDF, XPS, OpenXPS, CBZ, EPUB, MOBI and FB2 (e-books) formats,<br> and it is known for its top
<b><i>performance</i></b> and <b><i>rendering quality.</p>"""

# Make a PDF page for demo purposes
root = os.path.abspath( f"{__file__}/..")
doc = fitz.open(f"{root}/mupdf-title.pdf")
page = doc[0]

WHERE = fitz.Rect(50, 100, 250, 500)  # target rectangle on existing page

fileptr = io.BytesIO()  # let DocumentWriter use this as its file

# -------------------------------------------------------------------
# call DocumentWriter and Story to fill our rectangle
matrix = make_pdf(fileptr, HTML, WHERE)
# -------------------------------------------------------------------
src = fitz.open("pdf", fileptr)  # open DocumentWriter output PDF
if src.page_count > 1:  # target rect was too small
    raise ValueError("target WHERE too small")

# its page 0 contains our result
page.show_pdf_page(WHERE, src, 0)

doc.ez_save(f"{root}/mupdf-title-after.pdf")
