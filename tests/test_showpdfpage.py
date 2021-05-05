"""
Tests:
    * Convert some image to a PDF
    * Insert it in a PDF page in given rectangle
    * Assert PDF Form XObject has been created
    * Assert inserted PDF is inside given retangle
"""
import os

import fitz

scriptdir = os.path.abspath(os.path.dirname(__file__))
imgfile = os.path.join(scriptdir, "resources", "nur-ruhig.jpg")


def test_insert():
    doc = fitz.open()
    page = doc.new_page()
    r1 = fitz.Rect(50, 50, 100, 100)  # insert in here
    img = fitz.open(imgfile)  # open image
    tobytes = img.convert_to_pdf()  # get its PDF version (bytes object)
    src = fitz.open("pdf", tobytes)  # open as PDF
    page.show_pdf_page(r1, src, 0)  # insert in rectangle
    img = page.get_images(True)[0]  # make full image list of the page
    assert img[-1] > 0  # xref of Form XObject!
    img = page.get_image_info()[0]  # read the page's images

    # Multiple comutations may lead to rounding issues, so we need
    # some generosity here:
    bbox = list(map(lambda x: round(x, 2), img["bbox"]))
    assert bbox in r1
