import os

import pymupdf

root = os.path.abspath(f'{__file__}/../..')

def test_2548():
    """Text extraction should fail because of PDF structure cycle.

    Old MuPDF version did not detect the loop.
    """
    print(f'test_2548(): {pymupdf.mupdf_version_tuple=}')
    if pymupdf.mupdf_version_tuple < (1, 23, 4):
        print(f'test_2548(): Not testing #2548 because infinite hang before mupdf-1.23.4.')
        return
    pymupdf.TOOLS.mupdf_warnings(reset=True)
    doc = pymupdf.open(f'{root}/tests/resources/test_2548.pdf')
    e = False
    for page in doc:
        try:
            _ = page.get_text()
        except Exception as ee:
            print(f'test_2548: {ee=}')
            if hasattr(pymupdf, 'mupdf'):
                # Rebased.
                expected = "RuntimeError('code=2: cycle in structure tree')"
            else:
                # Classic.
                expected = "RuntimeError('cycle in structure tree')"
            assert repr(ee) == expected, f'Expected {expected=} but got {repr(ee)=}.'
            e = True
    wt = pymupdf.TOOLS.mupdf_warnings()
    print(f'test_2548(): {wt=}')

    # This checks that PyMuPDF 1.23.7 fixes this bug, and also that earlier
    # versions with updated MuPDF also fix the bug.
    rebased = hasattr(pymupdf, 'mupdf')
    if pymupdf.mupdf_version_tuple >= (1, 23, 7):    
        if pymupdf.mupdf_version_tuple >= (1, 25):
            expected = 'format error: cycle in structure tree\nstructure tree broken, assume tree is missing'
        elif pymupdf.mupdf_version_tuple >= (1, 24):
            expected = 'Loop found in structure tree. Ignoring structure.'
        else:
            expected = 'structure tree broken, assume tree is missing: cycle in structure tree'
        if rebased:
            assert wt == expected, f'expected:\n    {expected!r}\nwt:\n    {wt!r}\n'
        assert not e
    else:
        assert e
        if rebased:
            assert not wt
