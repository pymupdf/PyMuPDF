"""
This is a demo script using PyMuPDF's Story class to output text as a PDF with
a two-column page layout.

The script demonstrates the following features:
* Layout text around images of an existing ("target") PDF.
* Based on a few global parameters, areas on each page are identified, that
  can be used to receive text layouted by a Story.
* These global parameters are not stored anywhere in the target PDF and
  must therefore be provided in some way.
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

Note:
--------------
This script version uses just image positions to derive "No-Go areas" for
layouting the text. Other PDF objects types are detectable by PyMuPDF and may
be taken instead or in addition, without influencing the layouting.
The following are candidates for other such "No-Go areas". Each can be detected
and located by PyMuPDF:
* Annotations
* Drawings
* Existing text

--------------
The text and images are taken from the somewhat modified Wikipedia article
https://en.wikipedia.org/wiki/The_quick_brown_fox_jumps_over_the_lazy_dog.
--------------
"""

import io
import os
import zipfile
import fitz


thisdir = os.path.dirname(os.path.abspath(__file__))
myzip = zipfile.ZipFile(os.path.join(thisdir, "quickfox.zip"))

docname = os.path.join(thisdir, "image-no-go.pdf")  # "no go" input PDF file name
outname = os.path.join(thisdir, "quickfox-image-no-go.pdf")  # output PDF file name
BORDER = 36  # global parameter
FONTSIZE = 12.5  # global parameter
COLS = 2  # number of text columns, global parameter


def analyze_page(page):
    """Compute MediaBox and rectangles on page that are free to receive text.

    Notes:
        Assume a BORDER around the page, make 2 columns of the resulting
        sub-rectangle and extract the rectangles of all images on page.
        For demo purposes, the image rectangles are taken as "NO-GO areas"
        on the page when writing text with the Story.
        The function returns free areas for each of the columns.

    Returns:
        (page.number, mediabox, CELLS), where CELLS is a list of free cells.
    """
    prect = page.rect  # page rectangle - will be our MEDIABOX later
    where = prect + (BORDER, BORDER, -BORDER, -BORDER)
    TABLE = fitz.make_table(where, rows=1, cols=COLS)

    # extract rectangles covered by images on this page
    IMG_RECTS = sorted(  # image rects on page (sort top-left to bottom-right)
        [fitz.Rect(item["bbox"]) for item in page.get_image_info()],
        key=lambda b: (b.y1, b.x0),
    )

    def free_cells(column):
        """Return free areas in this column."""
        free_stripes = []  # y-value pairs wrapping a free area stripe
        # intersecting images: block complete intersecting column stripe
        col_imgs = [(b.y0, b.y1) for b in IMG_RECTS if abs(b & column) > 0]
        s_y0 = column.y0  # top y-value of column
        for y0, y1 in col_imgs:  # an image stripe
            if y0 > s_y0 + FONTSIZE:  # image starts below last free btm value
                free_stripes.append((s_y0, y0))  # store as free stripe
            s_y0 = y1  # start of next free stripe

        if s_y0 + FONTSIZE < column.y1:  # enough room to column bottom
            free_stripes.append((s_y0, column.y1))

        if free_stripes == []:  # covers "no image in this column"
            free_stripes.append((column.y0, column.y1))

        # make available cells of this column
        CELLS = [fitz.Rect(column.x0, y0, column.x1, y1) for (y0, y1) in free_stripes]
        return CELLS

    # collection of available Story rectangles on page
    CELLS = []
    for i in range(COLS):
        CELLS.extend(free_cells(TABLE[0][i]))

    return page.number, prect, CELLS


HTML = myzip.read("quickfox.html").decode()

# --------------------------------------------------------------
# Make the Story object
# --------------------------------------------------------------
story = fitz.Story(HTML)

# modify the DOM somewhat
body = story.body  # access HTML body
body.set_properties(font="sans-serif")  # and give it our font globally

# modify certain nodes
para = body.find("p", None, None)  # find relevant nodes (here: paragraphs)
while para != None:
    para.set_properties(  # method MUST be used for existing nodes
        indent=15,
        fontsize=FONTSIZE,
    )
    para = para.find_next("p", None, None)

# we remove all image references, because the target PDF already has them
img = body.find("img", None, None)
while img != None:
    next_img = img.find_next("img", None, None)
    img.remove()
    img = next_img

page_info = {}  # contains MEDIABOX and free CELLS per page
doc = fitz.open(docname)
for page in doc:
    pno, mediabox, cells = analyze_page(page)
    page_info[pno] = (mediabox, cells)
doc.close()  # close target PDF for now - re-open later

fileobject = io.BytesIO()  # let DocumentWriter write to memory
writer = fitz.DocumentWriter(fileobject)  # define output writer

more = 1  # stop if this ever becomes zero
pno = 0  # count output pages
while more:  # loop until all HTML text has been written
    try:
        MEDIABOX, CELLS = page_info[pno]
    except KeyError:  # too much text space required: reduce fontsize?
        raise ValueError("text does not fit on target PDF")
    dev = writer.begin_page(MEDIABOX)  # prepare a new output page
    for cell in CELLS:  # iterate over free cells on this page
        if not more:  # need to check this for every cell
            continue
        more, _ = story.place(cell)
        story.draw(dev)
    writer.end_page()  # finish the PDF page
    pno += 1

writer.close()  # close DocumentWriter output

# Re-open writer output, read its pages and overlay target pages with them.
# The generated pages have same dimension as their targets.
src = fitz.open("pdf", fileobject)
doc = fitz.open(doc.name)
for page in doc:  # overlay every target page with the prepared text
    if page.number >= src.page_count:
        print(f"Text only uses {src.page_count} target pages!")
        continue  # story did not need all target pages?

    # overlay target page
    page.show_pdf_page(page.rect, src, page.number)

    # DEBUG start --- draw the text rectangles
    # mb, cells = page_info[page.number]
    # for cell in cells:
    #     page.draw_rect(cell, color=(1, 0, 0))
    # DEBUG stop ---

doc.ez_save(outname)
