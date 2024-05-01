"""
* Insert same image with different rotations in two places of a page.
* Extract bboxes and transformation matrices
* Assert image locations are inside given rectangles
"""
import json
import os

import pymupdf

scriptdir = os.path.abspath(os.path.dirname(__file__))
imgfile = os.path.join(scriptdir, "resources", "nur-ruhig.jpg")


def test_insert():
    doc = pymupdf.open()
    page = doc.new_page()
    r1 = pymupdf.Rect(50, 50, 100, 100)
    r2 = pymupdf.Rect(50, 150, 200, 400)
    page.insert_image(r1, filename=imgfile)
    page.insert_image(r2, filename=imgfile, rotate=270)
    info_list = page.get_image_info()
    assert len(info_list) == 2
    bbox1 = pymupdf.Rect(info_list[0]["bbox"])
    bbox2 = pymupdf.Rect(info_list[1]["bbox"])
    assert bbox1 in r1
    assert bbox2 in r2

def test_compress():
    document = pymupdf.open(f'{scriptdir}/resources/2.pdf')
    document_new = pymupdf.open()
    for page in document:
        pixmap = page.get_pixmap(
                colorspace=pymupdf.csRGB,
                dpi=72,
                annots=False,
                )
        page_new = document_new.new_page(-1)
        page_new.insert_image(rect=page_new.bound(), pixmap=pixmap)
    document_new.save(
            f'{scriptdir}/resources/2.pdf.compress.pdf',
            garbage=3,
            deflate=True,
            deflate_images=True,
            deflate_fonts=True,
            pretty=True,
            )

def test_3087():
    path = os.path.abspath(f'{__file__}/../../tests/resources/test_3087.pdf')
    
    doc = pymupdf.open(path)
    page = doc[0]
    print(page.get_images())
    base = doc.extract_image(5)["image"]
    mask = doc.extract_image(5)["image"]
    page = doc.new_page()
    page.insert_image(page.rect, stream=base, mask=mask)
    
    doc = pymupdf.open(path)
    page = doc[0]
    print(page.get_images())
    base = doc.extract_image(5)["image"]
    mask = doc.extract_image(6)["image"]
    page = doc.new_page()
    page.insert_image(page.rect, stream=base, mask=mask)
