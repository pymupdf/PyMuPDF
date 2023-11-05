import os

import fitz

root = os.path.abspath(f'{__file__}/../..')

def test_2548():
    """Text extraction should fail because of PDF structure cycle.

    Old MuPDF version did not detect the loop.
    """
    if fitz.mupdf_version_tuple < (1, 23, 4):
        print(f'Not testing #2548 because infinite hang before mupdf-1.23.4.')
        return
    fitz.TOOLS.mupdf_warnings(reset=True)
    doc = fitz.open(f'{root}/tests/resources/test_2548.pdf')
    e = False
    for page in doc:
        try:
            _ = page.get_text()
        except Exception as ee:
            print(f'test_2548: {ee=}')
            if hasattr(fitz, 'mupdf'):
                # Rebased.
                expected = "RuntimeError('code=2: cycle in structure tree')"
            else:
                # Classic.
                expected = "RuntimeError('cycle in structure tree')"
            assert repr(ee) == expected, f'Expected {expected=} but got {repr(ee)=}.'
            e = True
    # After 2023-11-05 mupdf master no longer raises an exception, but does
    # write a warning.
    wt = fitz.TOOLS.mupdf_warnings()
    print(f'{wt=}')
    assert wt == 'structure tree broken, assume tree is missing: cycle in structure tree'
    assert not e
