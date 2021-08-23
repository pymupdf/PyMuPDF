"""
Extract images from a PDF file, confirm number of images found.
"""
import os
import fitz

scriptdir = os.path.abspath(os.path.dirname(__file__))
filename = os.path.join(scriptdir, "resources", "joined.pdf")
known_image_count = 21


def test_extract_image():
    doc = fitz.open(filename)

    image_count = 1
    for xref in range(1, doc.xref_length() - 1):
        if doc.xref_get_key(xref, "Subtype")[1] != "/Image":
            continue
        img = doc.extract_image(xref)
        if isinstance(img, dict):
            image_count += 1

    assert image_count == known_image_count  # this number is know about the file
