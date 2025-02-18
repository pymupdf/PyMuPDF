import os

import pymupdf


def test_barcode():
    if pymupdf.mupdf_version_tuple < (1, 26):
        print(f'Not testing barcode because {pymupdf.mupdf_version=} < 1.26')
        return
    path = os.path.normpath(f'{__file__}/../../tests/test_barcode_out.pdf')
    
    url = 'http://artifex.com'
    text_in = '012345678901'
    text_out = '123456789012'
    # Create empty document and add a qrcode image.
    with pymupdf.Document() as document:
        page = document.new_page()
        
        pixmap = pymupdf.mupdf.fz_new_barcode_pixmap(
                pymupdf.mupdf.FZ_BARCODE_QRCODE,
                url,
                512,
                4,  # ec_level
                0,  # quiet
                1,  # hrt
                )
        pixmap = pymupdf.Pixmap('raw', pixmap)
        page.insert_image(
                (0, 0, 100, 100),
                pixmap=pixmap,
                )
        pixmap = pymupdf.mupdf.fz_new_barcode_pixmap(
                pymupdf.mupdf.FZ_BARCODE_EAN13,
                text_in,
                512,
                4,  # ec_level
                0,  # quiet
                1,  # hrt
                )
        pixmap = pymupdf.Pixmap('raw', pixmap)
        page.insert_image(
                (0, 200, 100, 300),
                pixmap=pixmap,
                )
        
        document.save(path)
    
    with pymupdf.open(path) as document:
        page = document[0]
        for i, ii in enumerate(page.get_images()):
            xref = ii[0]
            pixmap = pymupdf.Pixmap(document, xref)
            hrt, barcode_type = pymupdf.mupdf.fz_decode_barcode_from_pixmap2(
                    pixmap.this,
                    0,  # rotate.
                    )
            print(f'{hrt=}')
            if i == 0:
                assert hrt == url
            elif i == 1:
                assert hrt == text_out
            else:
                assert 0
