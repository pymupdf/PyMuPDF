"""
Confirm image mask detection in TextPage extractions. 
"""

import os

import pymupdf

scriptdir = os.path.abspath(os.path.dirname(__file__))
filename1 = os.path.join(scriptdir, "resources", "img-regular.pdf")
filename2 = os.path.join(scriptdir, "resources", "img-transparent.pdf")


def test_imagemask1():
    doc = pymupdf.open(filename1)
    page = doc[0]
    blocks = page.get_text("dict")["blocks"]
    img = blocks[0]
    assert img["mask"] is None
    img = page.get_image_info()[0]
    assert img["has-mask"] is False


def test_imagemask2():
    doc = pymupdf.open(filename2)
    page = doc[0]
    blocks = page.get_text("dict")["blocks"]
    img = blocks[0]
    assert type(img["mask"]) is bytes
    img = page.get_image_info()[0]
    assert img["has-mask"] is True
