import os
import platform

import pymupdf

def test_tesseract():
    '''
    This checks that MuPDF has been built with tesseract support.

    By default we don't supply a valid `tessdata` directory, and just assert
    that attempting to use Tesseract raises the expected error (which checks
    that MuPDF is built with Tesseract support).

    But if TESSDATA_PREFIX is set in the environment, we assert that
    FzPage.get_textpage_ocr() succeeds.
    '''
    path = os.path.abspath( f'{__file__}/../resources/2.pdf')
    doc = pymupdf.open( path)
    page = doc[5]
    if hasattr(pymupdf, 'mupdf'):
        # rebased.
        if pymupdf.mupdf_version_tuple >= (1, 24):
            e_expected = 'code=3: OCR initialisation failed'
            if platform.system() == 'OpenBSD':
                # 2023-12-12: For some reason the SWIG catch code only catches
                # the exception as FzErrorBase.
                e_expected_type = pymupdf.mupdf.FzErrorBase
                print(f'OpenBSD workaround - expecting FzErrorBase, not FzErrorLibrary.')
            else:
                e_expected_type = pymupdf.mupdf.FzErrorLibrary
        else:
            e_expected = 'code=2: OCR initialisation failed'
            e_expected_type = None
    else:
        # classic.
        e_expected = 'OCR initialisation failed'
        e_expected_type = None
    tessdata_prefix = os.environ.get('TESSDATA_PREFIX')
    if tessdata_prefix:
        tp = page.get_textpage_ocr(full=True)
        print(f'test_tesseract(): page.get_textpage_ocr() succeeded')
    else:
        try:
            tp = page.get_textpage_ocr(full=True, tessdata='/foo/bar')
        except Exception as e:
            e_text = str(e)
            print(f'Received exception as expected.')
            print(f'{type(e)=}')
            print(f'{e_text=}')
            assert e_text == e_expected, f'Unexpected exception: {e_text!r}'
            if e_expected_type:
                print(f'{e_expected_type=}')
                assert type(e) == e_expected_type, f'{type(e)=} != {e_expected_type=}.'
        else:
            assert 0, f'Expected exception {e_expected!r}'
        rebased = hasattr(pymupdf, 'mupdf')
        if rebased:
            wt = pymupdf.TOOLS.mupdf_warnings()
            if pymupdf.mupdf_version_tuple < (1, 25):
                assert wt
            else:
                assert wt == (
                        'UNHANDLED EXCEPTION!\n'
                        'library error: Tesseract initialisation failed\n'
                        'dropping unclosed output'
                        )
        
