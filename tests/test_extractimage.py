"""
Extract images from a PDF file, confirm number of images found.
"""
import os
import pymupdf

scriptdir = os.path.abspath(os.path.dirname(__file__))
filename = os.path.join(scriptdir, "resources", "joined.pdf")
known_image_count = 21


def test_extract_image():
    doc = pymupdf.open(filename)

    image_count = 1
    for xref in range(1, doc.xref_length() - 1):
        if doc.xref_get_key(xref, "Subtype")[1] != "/Image":
            continue
        img = doc.extract_image(xref)
        if isinstance(img, dict):
            image_count += 1

    assert image_count == known_image_count  # this number is know about the file

def test_2348():
    
    pdf_path = f'{scriptdir}/test_2348.pdf'
    document = pymupdf.open()
    page = document.new_page(width=500, height=842)
    rect = pymupdf.Rect(20, 20, 480, 820)
    page.insert_image(rect, filename=f'{scriptdir}/resources/nur-ruhig.jpg')
    page = document.new_page(width=500, height=842)
    page.insert_image(rect, filename=f'{scriptdir}/resources/img-transparent.png')
    document.ez_save(pdf_path)
    document.close()

    document = pymupdf.open(pdf_path)
    page = document[0]
    imlist = page.get_images()
    image = document.extract_image(imlist[0][0])
    jpeg_extension = image['ext']

    page = document[1]
    imlist = page.get_images()
    image = document.extract_image(imlist[0][0])
    png_extension = image['ext']
    
    print(f'jpeg_extension={jpeg_extension!r} png_extension={png_extension!r}')
    assert jpeg_extension == 'jpeg'
    assert png_extension == 'png'

def test_delete_image():

    doc = pymupdf.open(os.path.abspath(f'{__file__}/../../tests/resources/test_delete_image.pdf'))
    page = doc[0]
    xref = page.get_images()[0][0]
    page.delete_image(xref)
