import os
import platform
import textwrap

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
        if pymupdf.mupdf_version_tuple < (1, 25, 4):
            tail = 'OCR initialisation failed'
        else:
            tail = 'Tesseract language initialisation failed'
        e_expected = f'code=3: {tail}'
        if platform.system() == 'OpenBSD':
            # 2023-12-12: For some reason the SWIG catch code only catches
            # the exception as FzErrorBase.
            e_expected_type = pymupdf.mupdf.FzErrorBase
            print(f'OpenBSD workaround - expecting FzErrorBase, not FzErrorLibrary.')
        else:
            e_expected_type = pymupdf.mupdf.FzErrorLibrary
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
            if pymupdf.mupdf_version_tuple < (1, 25, 4):
                assert wt == (
                        'UNHANDLED EXCEPTION!\n'
                        'library error: Tesseract initialisation failed'
                        )
            else:
                assert not wt
        

def test_3842b():
    # Check Tesseract failure when given a bogus languages.
    #
    # Note that Tesseract seems to output its own diagnostics.
    #
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
                if pymupdf.mupdf_version_tuple < (1, 25, 4):
                    assert 'OCR initialisation failed' in str(e)
                    wt = pymupdf.TOOLS.mupdf_warnings()
                    assert wt == 'UNHANDLED EXCEPTION!\nlibrary error: Tesseract initialisation failed\nUNHANDLED EXCEPTION!\nlibrary error: Tesseract initialisation failed', \
                            f'Unexpected {wt=}'
                else:
                    assert 'Tesseract language initialisation failed' in str(e)


def test_3842():
    path = os.path.normpath(f'{__file__}/../../tests/resources/test_3842.pdf')
    with pymupdf.open(path) as document:
        page = document[6]
        try:
            partial_tp = page.get_textpage_ocr(flags=0, full=False)
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
            
            # 2024-11-29: This is the current incorrect output. We use
            # underscores for lines containing entirely whitespace (which
            # textwrap.dedent() unfortunately replaces with empty lines).
            text_expected = textwrap.dedent('''
                    NIST SP 800-223  
                    _
                    High-Performance Computing Security 
                    February 2024 
                    _
                    __
                    iii 
                    Table of Contents 
                    1. Introduction ...................................................................................................................................1 
                    2. HPC System Reference Architecture and Main Components ............................................................2 
                    2.1.1. Components of the High-Performance Computing Zone ............................................................. 3 
                    2.1.2. Components of the Data Storage Zone ........................................................................................ 4 
                    2.1.3. Parallel File System ....................................................................................................................... 4 
                    2.1.4. Archival and Campaign Storage .................................................................................................... 5 
                    2.1.5. Burst Buffer .................................................................................................................................. 5 
                    2.1.6. Components of the Access Zone .................................................................................................. 6 
                    2.1.7. Components of the Management Zone ....................................................................................... 6 
                    2.1.8. General Architecture and Characteristics .................................................................................... 6 
                    2.1.9. Basic Services ................................................................................................................................ 7 
                    2.1.10. Configuration Management ....................................................................................................... 7 
                    2.1.11. HPC Scheduler and Workflow Management .............................................................................. 7 
                    2.1.12. HPC Software .............................................................................................................................. 8 
                    2.1.13. User Software ............................................................................................................................. 8 
                    2.1.14. Site-Provided Software and Vendor Software ........................................................................... 8 
                    2.1.15. Containerized Software in HPC .................................................................................................. 9 
                    3. HPC Threat Analysis...................................................................................................................... 10 
                    3.2.1. Access Zone Threats ................................................................................................................... 11 
                    3.2.2. Management Zone Threats ........................................................................................................ 11 
                    3.2.3. High-Performance Computing Zone Threats .............................................................................. 12 
                    3.2.4. Data Storage Zone Threats ......................................................................................................... 12 
                    4. HPC Security Posture, Challenges, and Recommendations ............................................................. 14 
                    5. Conclusions .................................................................................................................................. 19 
                    ''',
                    )[1:].replace('_', ' ')
            print(f'text_expected:\n{text_expected!r}')
            assert text == text_expected
