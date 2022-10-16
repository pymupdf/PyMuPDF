"""
Demo of Story class in PyMuPDF
-------------------------------

This script demonstrates how the results of a fitz.Story output can be
placed in a rectangle of an existing (!) PDF page.

"""
import io

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
        done, _ = story.place(mediabox)
        story.draw(device)
        writer.end_page()
        if done == 0:
            break
    writer.close()
    return matrix


# -------------------------------------------------------------
# We want to put this in a given rectangle of an existing page
# -------------------------------------------------------------
HTML = (
    '<div style="margin-left:-12px;margin-right:-12px">Der (Große) '
    "<b>Schwertwal</b> <i>(Orcinus orca)</i>, auch <b>Mörderwal</b>, "
    "<b>Killerwal</b>, <b>Orca</b> oder <b>Butzkopf</b> (auch Butskopf) genannt,"
    " ist eine Art der Wale aus der Familie der Delfine <i>(Delphinidae)</i>. "
    "Die Art ist weltweit verbreitet, bewohnt jedoch bevorzugt küstennahe "
    "Gewässer in höheren Breiten.</div>"
)

# Make a PDF page for demo purposes
doc = fitz.open()
page = doc.new_page()
page.insert_text(  # store some header on the page
    (72, 50),
    "Red rectangle: WHERE",
    fontname="hebo",
    color=(1, 0, 0),
    fontsize=14,
)

WHERE = fitz.Rect(100, 100, 300, 300)  # target rectangle on existing page

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

# debug: wrap rectangles with borders
page.draw_rect(WHERE, color=(1, 0, 0), width=0.3)
doc.ez_save(__file__.replace(".py", ".pdf"))
