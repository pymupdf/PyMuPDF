"""
Tests:
    * Convert some image to a PDF
    * Insert it rotated in some rectangle of a PDF page
    * Assert PDF Form XObject has been created
    * Assert that image contained in inserted PDF is inside given retangle
"""
import os

import pymupdf

scriptdir = os.path.abspath(os.path.dirname(__file__))
imgfile = os.path.join(scriptdir, "resources", "nur-ruhig.jpg")


def test_insert():
    doc = pymupdf.open()
    page = doc.new_page()
    rect = pymupdf.Rect(50, 50, 100, 100)  # insert in here
    img = pymupdf.open(imgfile)  # open image
    tobytes = img.convert_to_pdf()  # get its PDF version (bytes object)
    src = pymupdf.open("pdf", tobytes)  # open as PDF
    xref = page.show_pdf_page(rect, src, 0, rotate=-23)  # insert in rectangle
    # extract just inserted image info
    img = page.get_images(True)[0]
    assert img[-1] == xref  # xref of Form XObject!
    img = page.get_image_info()[0]  # read the page's images

    # Multiple computations may have lead to rounding deviations, so we need
    # some generosity here: enlarge rect by 1 point in each direction.
    assert img["bbox"] in rect + (-1, -1, 1, 1)

def test_2742():
    dest = pymupdf.open()
    destpage = dest.new_page(width=842, height=595)

    a5 = pymupdf.Rect(0, 0, destpage.rect.width / 3, destpage.rect.height)
    shiftright = pymupdf.Rect(destpage.rect.width/3, 0, destpage.rect.width/3, 0)

    src = pymupdf.open(os.path.abspath(f'{__file__}/../../tests/resources/test_2742.pdf'))

    destpage.show_pdf_page(a5, src, 0)
    destpage.show_pdf_page(a5 + shiftright, src, 0)
    destpage.show_pdf_page(a5 + shiftright + shiftright, src, 0)

    dest.save(os.path.abspath(f'{__file__}/../../tests/test_2742-out.pdf'))
    print("The end!")
    
    rebased = hasattr(pymupdf, 'mupdf')
    if rebased:
        wt = pymupdf.TOOLS.mupdf_warnings()
        assert wt == (
                'Circular dependencies! Consider page cleaning.\n'
                '... repeated 3 times...'
                ), f'{wt=}'
