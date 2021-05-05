"""
Pixmap tests
* make pixmap of a page and assert bbox size
* make pixmap from a PDF xref and compare with extracted image
* pixmap from file and from binary image and compare
"""
import os

import fitz

scriptdir = os.path.abspath(os.path.dirname(__file__))
epub = os.path.join(scriptdir, "resources", "Bezier.epub")
pdf = os.path.join(scriptdir, "resources", "001003ED.pdf")
imgfile = os.path.join(scriptdir, "resources", "nur-ruhig.jpg")


def test_pagepixmap():
    # pixmap from an EPUB page
    doc = fitz.open(epub)
    page = doc[0]
    pix = page.get_pixmap()
    assert pix.irect == page.rect.irect
    pix = page.get_pixmap(alpha=True)
    assert pix.alpha
    assert pix.n == pix.colorspace.n + pix.alpha


def test_pdfpixmap():
    # pixmap from xref in a PDF
    doc = fitz.open(pdf)
    # take first image item of first page
    img = doc.get_page_images(0)[0]
    # make pixmap of it
    pix = fitz.Pixmap(doc, img[0])
    # assert pixmap properties
    assert pix.width == img[2]
    assert pix.height == img[3]
    # extract image and compare metadata
    extractimg = doc.extract_image(img[0])
    assert extractimg["width"] == pix.width
    assert extractimg["height"] == pix.height


def test_filepixmap():
    # pixmaps from file and from stream
    # should lead to same result
    pix1 = fitz.Pixmap(imgfile)
    stream = open(imgfile, "rb").read()
    pix2 = fitz.Pixmap(stream)
    assert repr(pix1) == repr(pix2)
    assert pix1.samples == pix2.samples
