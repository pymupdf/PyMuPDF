import fitz

import os
import sys

def test_2904():
    print(f'test_2904(): {fitz.mupdf_version_tuple=}.')
    path = os.path.abspath(f'{__file__}/../../tests/resources/test_2904.pdf')
    pdf_docs = fitz.open(path)
    for page_id, page in enumerate(pdf_docs):
        page_imgs = page.get_images()
        for i, img in enumerate(page_imgs):
            if page_id == 75:
                #print(f'{page_id=} {i=} {type(img)=} {img=}')
                sys.stdout.flush()
            e = None
            try:
                recs = page.get_image_rects(img, transform=True)
            except Exception as ee:
                print(f'Exception: {page_id=} {i=} {img=}: {ee}')
                if 0 and hasattr(fitz, 'mupdf'):
                    print(f'fitz.exception_info:')
                    fitz.exception_info()
                    sys.stdout.flush()
                e = ee
            if page_id == 75:
                print(f'{fitz.mupdf_version_tuple=}: {page_id=} {i=} {e=} {img=}:')
            if fitz.mupdf_version_tuple >= (1, 24):
                # 2023-12-20: current mupdf master has a bug here that causes
                # one corrupt image to provoke errors for all images on the
                # same page.
                if page_id == 75:
                    assert e
            else:
                if page_id == 75 and i==3:
                    assert e
                    if hasattr(fitz, 'mupdf') and fitz.mupdf_version_tuple >= (1, 23, 7):
                        assert str(e) == 'code=4: Failed to read JPX header'
                    else:
                        assert str(e) == 'Failed to read JPX header'
                else:
                    assert not e
                
