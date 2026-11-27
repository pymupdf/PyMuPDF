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
    if pymupdf.mupdf_version_tuple >= (1, 28):
        path_text_expected = os.path.normpath(f'{__file__}/../../tests/resources/test_3842_expected_1.28.txt')
        path_text_expected_alternative = os.path.normpath(f'{__file__}/../../tests/resources/test_3842_expected_1.28_older_tesseract.txt')
    else:
        path_text_expected = os.path.normpath(f'{__file__}/../../tests/resources/test_3842_partial.txt')
    text_expected = pathlib.Path(path_text_expected).read_text()
    text_expected_alternative = pathlib.Path(path_text_expected_alternative).read_text()
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
            with open(os.path.normpath(f'{__file__}/../../tests/resources/test_3842_out'), 'w') as f:
                f.write(text)
            print()
            print(text)
            print(f'text:\n{text!r}')
            print(f'text_expected:\n{text_expected!r}')
            print(f'text_expected_alternative:\n{text_expected_alternative!r}')
            assert text == text_expected or text == text_expected_alternative


def test_5295():
    # get_textpage_ocr(full=True) must not drop text on /Rotate 90 and 270
    # pages whose width and height differ. We make an image-only A4 "scan"
    # filed with a landscape MediaBox and /Rotate, as a landscape scanner
    # does, with one line of text near the top and one near the bottom of
    # the page as seen. Before the fix one of them was lost.
    if os.environ.get('PYODIDE_ROOT'):
        print('test_5295(): not running on Pyodide - cannot run child processes.')
        return

    lines = {'Topline': 80, 'Bottomline': 780}
    seen = pymupdf.open()
    seen_page = seen.new_page(width=595, height=842)
    for text, y in lines.items():
        seen_page.insert_text((72, y), text, fontsize=20)
    pix = seen_page.get_pixmap(dpi=150)

    for rotation in (90, 270):
        with pymupdf.open() as document:
            page = document.new_page(width=842, height=595)
            page.set_rotation(rotation)
            page.insert_image(page.rect * page.derotation_matrix, pixmap=pix, rotate=rotation)
            try:
                tp = page.get_textpage_ocr(full=True, dpi=150)
            except Exception as e:
                print(f'test_5295(): received exception: {e}', flush=1)
                if 'No tessdata specified and Tesseract is not installed' in str(e):
                    return
                if 'Tesseract language initialisation failed' in str(e):
                    return
                raise
            text = page.get_text(textpage=tp)
            print(f'test_5295(): {rotation=} {text=}')
            for line in lines:
                assert line in text, f'{line!r} not found with /Rotate {rotation}: {text=}'
