"""
Tests:
    * Convert some image to a PDF
    * Insert it rotated in some rectangle of a PDF page
    * Assert PDF Form XObject has been created
    * Assert that image contained in inserted PDF is inside given retangle
"""
import os

import fitz

scriptdir = os.path.abspath(os.path.dirname(__file__))
imgfile = os.path.join(scriptdir, "resources", "nur-ruhig.jpg")


def test_insert():
    doc = fitz.open()
    page = doc.new_page()
    rect = fitz.Rect(50, 50, 100, 100)  # insert in here
    img = fitz.open(imgfile)  # open image
    tobytes = img.convert_to_pdf()  # get its PDF version (bytes object)
    src = fitz.open("pdf", tobytes)  # open as PDF
    xref = page.show_pdf_page(rect, src, 0, rotate=-23)  # insert in rectangle
    # extract just inserted image info
    img = page.get_images(True)[0]
    assert img[-1] == xref  # xref of Form XObject!
    img = page.get_image_info()[0]  # read the page's images

    # Multiple computations may have lead to rounding deviations, so we need
    # some generosity here: enlarge rect by 1 point in each direction.
    assert img["bbox"] in rect + (-1, -1, 1, 1)
