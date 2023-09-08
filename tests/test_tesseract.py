import os
import fitz

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
    doc = fitz.open( path)
    page = doc[5]
    e_expected = (
            'OCR initialisation failed',
            'code=2: OCR initialisation failed',
            )
    tessdata_prefix = os.environ.get('TESSDATA_PREFIX')
    if tessdata_prefix:
        tp = page.get_textpage_ocr(full=True)
        print(f'test_tesseract(): page.get_textpage_ocr() succeeded')
    else:
        try:
            tp = page.get_textpage_ocr(full=True, tessdata='/foo/bar')
        except Exception as e:
            ee = str(e)
            print(f'Received expected exception: {e}')
            assert ee in e_expected, f'Unexpected exception: {ee!r}'
        else:
            assert 0, f'Expected exception {e_expected!r}'
