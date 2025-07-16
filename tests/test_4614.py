import pymupdf
import os


def test_4614():
    script_dir = os.path.dirname(__file__)
    filename = os.path.join(script_dir, "resources", "test_4614.pdf")
    src = pymupdf.open(filename)
    doc = pymupdf.open()
    doc.insert_pdf(src)
