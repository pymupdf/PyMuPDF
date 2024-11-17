import pymupdf

import os
import sys

def test_2904():
    print(f'test_2904(): {pymupdf.mupdf_version_tuple=}.')
    path = os.path.abspath(f'{__file__}/../../tests/resources/test_2904.pdf')
    pdf_docs = pymupdf.open(path)
    for page_id, page in enumerate(pdf_docs):
        page_imgs = page.get_images()
        for i, img in enumerate(page_imgs):
            if page_id == 5:
                #print(f'{page_id=} {i=} {type(img)=} {img=}')
                sys.stdout.flush()
            e = None
            try:
                recs = page.get_image_rects(img, transform=True)
            except Exception as ee:
                print(f'Exception: {page_id=} {i=} {img=}: {ee}')
                if 0 and hasattr(pymupdf, 'mupdf'):
                    print(f'pymupdf.exception_info:')
                    pymupdf.exception_info()
                    sys.stdout.flush()
                e = ee
            if page_id == 5:
                print(f'{pymupdf.mupdf_version_tuple=}: {page_id=} {i=} {e=} {img=}:')
            if page_id == 5 and i==3:
                assert e
                if hasattr(pymupdf, 'mupdf'):
                    # rebased.
                    if pymupdf.mupdf_version_tuple >= (1, 24):
                        assert str(e) == 'code=8: Failed to read JPX header'
                    else:
                        assert str(e) == 'code=4: Failed to read JPX header'
                else:
                    # classic
                    assert str(e) == 'Failed to read JPX header'
            else:
                assert not e
    
    # Clear warnings, as we will have generated many.
    pymupdf.TOOLS.mupdf_warnings()     
