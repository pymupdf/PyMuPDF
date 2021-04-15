"""
* Insert same image in two places of a page.
* Extract bboxes and transformation matrices via different methods
* Assert equality of bboxes and transformations
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
    page.insert_image(r2, filename=imgfile)
    imglist = page.get_images(True)
    assert len(imglist) == 2
    bbox1, transform1 = page.get_image_bbox(imglist[0], transform=True)
    bbox2, transform2 = page.get_image_bbox(imglist[1], transform=True)
    assert bbox1 in r1
    assert bbox2 in r2
    info_list = page.get_image_info()
    assert len(info_list) == 2
    bbox3, transform3 = fitz.Rect(info_list[0]["bbox"]), fitz.Matrix(
        info_list[0]["transform"]
    )
    bbox4, transform4 = fitz.Rect(info_list[1]["bbox"]), fitz.Matrix(
        info_list[1]["transform"]
    )
    assert abs(bbox3 - bbox1) < fitz.EPSILON
    assert abs(bbox4 - bbox2) < fitz.EPSILON
    assert abs(transform3 - transform1) < fitz.EPSILON
    assert abs(transform4 - transform2) < fitz.EPSILON
