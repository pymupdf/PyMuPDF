"""
Ensure equality of bboxes computed via
* page.get_image_bbox()
* page.get_image_info()
* page.get_bboxlog()

"""
import os

import fitz

scriptdir = os.path.abspath(os.path.dirname(__file__))
filename = os.path.join(scriptdir, "resources", "image-file1.pdf")
image = os.path.join(scriptdir, "resources", "img-transparent.png")
doc = fitz.open(filename)


def test_image_bbox():
    page = doc[0]
    imglist = page.get_images(True)
    bbox_list = []
    for item in imglist:
        bbox_list.append(page.get_image_bbox(item, transform=False))
    infos = page.get_image_info(xrefs=True)
    for im in infos:
        bbox1 = im["bbox"]
        match = False
        for bbox2 in bbox_list:
            abs_bbox = (bbox2 - bbox1).norm()
            if abs_bbox < 1e-4:
                match = True
                break
    assert match


def test_bboxlog():
    doc = fitz.open()
    page = doc.new_page()
    xref = page.insert_image(page.rect, filename=image)
    img_info = page.get_image_info(xrefs=True)
    assert len(img_info) == 1
    info = img_info[0]
    assert info["xref"] == xref
    bbox_log = page.get_bboxlog()
    assert len(bbox_log) == 1
    box_type, bbox = bbox_log[0]
    assert box_type == "fill-image"
    assert bbox == info["bbox"]
