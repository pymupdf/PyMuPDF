import os
import platform
import textwrap
import pathlib
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
    tail = 'Tesseract language initialisation failed'
    if os.environ.get('PYODIDE_ROOT'):
        e_expected = 'code=6: No OCR support in this build'
        e_expected_type = pymupdf.mupdf.FzErrorUnsupported
    else:
        e_expected = f'code=3: {tail}'
        if platform.system() == 'OpenBSD':
            # 2023-12-12: For some reason the SWIG catch code only catches
            # the exception as FzErrorBase.
            e_expected_type = pymupdf.mupdf.FzErrorBase
            print(f'OpenBSD workaround - expecting FzErrorBase, not FzErrorLibrary.')
        else:
            e_expected_type = pymupdf.mupdf.FzErrorLibrary
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
        

def test_3842b():
    # Check Tesseract failure when given a bogus languages.
    #
    # Note that Tesseract seems to output its own diagnostics.
    #
    if os.environ.get('PYODIDE_ROOT'):
        print('test_3842b(): not running on Pyodide - cannot run child processes.')
        return
        
    path = os.path.normpath(f'{__file__}/../../tests/resources/test_3842.pdf')
    with pymupdf.open(path) as document:
        page = document[6]
        try:
            partial_tp = page.get_textpage_ocr(flags=0, full=False, language='qwerty')
        except Exception as e:
            print(f'test_3842b(): received exception: {e}')
            if 'No tessdata specified and Tesseract is not installed' in str(e):
                pass
            else:
                assert 'Tesseract language initialisation failed' in str(e)


def test_3842():
    if os.environ.get('PYODIDE_ROOT'):
        print('test_3842(): not running on Pyodide - cannot run child processes.')
        return
        
    path = os.path.normpath(f'{__file__}/../../tests/resources/test_3842.pdf')
    path_text = os.path.normpath(f'{__file__}/../../tests/resources/test_3842_partial.txt')
    text_expected = pathlib.Path(path_text).read_text()
    with pymupdf.open(path) as document:
        page = document[6]
        try:
            partial_tp = page.get_textpage_ocr(flags=0, full=False, dpi=300)
        except Exception as e:
            print(f'test_3842(): received exception: {e}', flush=1)
            if 'No tessdata specified and Tesseract is not installed' in str(e):
                pass
            elif 'Tesseract language initialisation failed' in str(e):
                pass
            else:
                assert 0, f'Unexpected exception text: {str(e)=}'
        else:
            text = page.get_text(textpage=partial_tp)
            print()
            print(text)
            print(f'text:\n{text!r}')
            print(f'text_expected:\n{text_expected!r}')
            assert text == text_expected
