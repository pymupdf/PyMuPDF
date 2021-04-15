"""
Tests:
    * Convert some image to a PDF
    * Insert it in a PDF page in a given rectangle
    * Ensure PDF Form XObject has been created
    * Ensure inserted PDF is inside given retangle
"""
import os

import fitz

scriptdir = os.path.abspath(os.path.dirname(__file__))
imgfile = os.path.join(scriptdir, "resources", "nur-ruhig.jpg")


def test_insert():
    doc = fitz.open()
    page = doc.new_page()
    r1 = fitz.Rect(50, 50, 100, 100)
    img = fitz.open(imgfile)
    tobytes = img.convert_to_pdf()
    src = fitz.open("pdf", tobytes)
    page.show_pdf_page(r1, src, 0)
    img = page.get_images(True)[0]
    assert img[-1] > 0
    img = page.get_image_info()[0]
    # we need to round somewhat here:
    bbox = list(map(lambda x: round(x, 2), img["bbox"]))
    assert bbox in r1
