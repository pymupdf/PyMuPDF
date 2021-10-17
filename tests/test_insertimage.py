"""
* Insert same image with different rotations in two places of a page.
* Extract bboxes and transformation matrices
* Assert image locations are inside given rectangles
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
    page.insert_image(r1, filename=imgfile)
    page.insert_image(r2, filename=imgfile, rotate=270)
    info_list = page.get_image_info()
    assert len(info_list) == 2
    bbox1 = fitz.Rect(info_list[0]["bbox"])
    bbox2 = fitz.Rect(info_list[1]["bbox"])
    assert bbox1 in r1
    assert bbox2 in r2
