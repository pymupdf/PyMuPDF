import os
import fitz

def test_tesseract():
    '''
    This checks that MuPDF has been built with tesseract support. We don't
    (yet) attempt to supply a valid `tessdata` directory.
    '''
    if hasattr(fitz, 'mupdf'):
        print(f'Not running test_tesseract() on rebased because tesseract not yet supported.')
        return
    path = os.path.abspath( f'{__file__}/../resources/2.pdf')
    doc = fitz.open( path)
    page = doc[5]
    e_expected = 'OCR initialisation failed'
    try:
        tp = page.get_textpage_ocr(full=True, tessdata='/foo/bar')
    except Exception as e:
        ee = str(e)
        print(f'Received expected exception: {e}')
        assert ee == e_expected, f'Unexpected exception: {ee!r}'
    else:
        assert 0, f'Expected exception {e_expected!r}'
