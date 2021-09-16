"""
Ensure equality of bboxes and transformation matrices computed via
* page.get_image_rects()
and
* page.get_image_info()
"""
import os

import fitz

scriptdir = os.path.abspath(os.path.dirname(__file__))
filename = os.path.join(scriptdir, "resources", "image-file1.pdf")
doc = fitz.open(filename)


def test_image_bbox():
    page = doc[0]
    imglist = page.get_images(True)
    img_rect_list = set()
    img_info_list = set()
    for item in imglist:
        for bbox, transform in page.get_image_rects(item, transform=True):
            img_rect_list.add((tuple(bbox), tuple(transform)))
    for im in page.get_image_info(xrefs=True):
        bbox = im["bbox"]
        transform = im["transform"]
        img_info_list.add((tuple(bbox), tuple(transform)))
    assert img_rect_list == img_info_list
