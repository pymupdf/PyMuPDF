import fitz
import pytest

@pytest.fixture(autouse=True)
def wrap(*args, **kwargs):
    '''
    Check that tests return with empty MuPDF warnings buffer. For example this
    detects failure to call fz_close_output() before fz_drop_output(), which
    (as of 2024-4-12) generates a warning from MuPDF.
    '''
    wt = fitz.TOOLS.mupdf_warnings()
    assert not wt, f'{wt=}'
    
    # Run the test.
    rep = yield
    
    # Test has run; check it did not create any MuPDF warnings.
    wt = fitz.TOOLS.mupdf_warnings()
    if not hasattr(fitz, 'mupdf'):
        print(f'Not checking mupdf_warnings on classic.')
    else:
        assert not wt, f'Warnings text not empty: {wt=}'
