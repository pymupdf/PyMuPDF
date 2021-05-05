"""
Ensure equality of bboxes and transformation matrices computed via
* page.get_image_bbox()
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
    bbox_list = []
    for item in imglist:
        bbox_list.append(page.get_image_bbox(item, transform=True))
    infos = page.get_image_info(xrefs=True)
    for im in infos:
        bbox1 = im["bbox"]
        transform1 = im["transform"]
        match = False
        for bbox2, transform2 in bbox_list:
            abs_bbox = (bbox2 - bbox1).norm()
            abs_matrix = (transform2 - transform1).norm()
            if abs_bbox < 1e-4 and abs_matrix < 1e-4:
                match = True
                break
    assert match
