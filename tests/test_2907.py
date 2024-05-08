import pymupdf

import os.path
import pathlib

def test_2907():
    # This test is for a bug in classic 'segfault trying to call clean_contents
    # on certain pdfs with python 3.12', which we are not going to fix.
    if not hasattr(pymupdf, 'mupdf'):
        print('test_2907(): not running on classic because known to fail.')
        return
    path = os.path.abspath(f'{__file__}/../../tests/resources/test_2907.pdf')
    pdf_file = pathlib.Path(path).read_bytes()
    fitz_document = pymupdf.open(stream=pdf_file, filetype="application/pdf")

    pdf_pages = list(fitz_document.pages())
    (page,) = pdf_pages
    page.clean_contents()
    if pymupdf.mupdf_version_tuple < (1, 24, 2):
        # We expect 'dropping unclosed PDF processor' warnings.
        wt = pymupdf.TOOLS.mupdf_warnings()
        assert wt
