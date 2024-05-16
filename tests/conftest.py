import pymupdf
import pytest

@pytest.fixture(autouse=True)
def wrap(*args, **kwargs):
    '''
    Check that tests return with empty MuPDF warnings buffer. For example this
    detects failure to call fz_close_output() before fz_drop_output(), which
    (as of 2024-4-12) generates a warning from MuPDF.
    '''
    wt = pymupdf.TOOLS.mupdf_warnings()
    assert not wt, f'{wt=}'
    assert not pymupdf.TOOLS.set_small_glyph_heights()
    
    pymupdf._log_items_clear()
    pymupdf._log_items_active(True)
    
    # Run the test.
    rep = yield
    
    # Test has run; check it did not create any MuPDF warnings etc.
    wt = pymupdf.TOOLS.mupdf_warnings()
    if not hasattr(pymupdf, 'mupdf'):
        print(f'Not checking mupdf_warnings on classic.')
    else:
        assert not wt, f'Warnings text not empty: {wt=}'
    
    assert not pymupdf.TOOLS.set_small_glyph_heights()
    
    log_items = pymupdf._log_items()
    assert not log_items, f'log() was called; {len(log_items)=}.'
