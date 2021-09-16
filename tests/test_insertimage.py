"""
* Insert same image with different rotations in two places of a page.
* Extract bboxes and transformation matrices via different methods.
* Assert image locations are inside given rectangles.
"""
import json
import os

import fitz

scriptdir = os.path.abspath(os.path.dirname(__file__))
imgfile = os.path.join(scriptdir, "resources", "nur-ruhig.jpg")


def test_insert():
    doc = fitz.open()
    page = doc.new_page()
    r1 = fitz.Rect(50, 50, 100, 100)
    r2 = fitz.Rect(50, 150, 200, 400)
    rects = (r1, r2)
    xref = page.insert_image(r1, filename=imgfile)
    xref = page.insert_image(r2, filename=imgfile, rotate=270, xref=xref)

    for i, bbox in enumerate(page.get_image_rects(xref)):
        assert bbox in rects[i]
