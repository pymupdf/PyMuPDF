import os
import platform
import sys

import pymupdf

import pytest

@pytest.fixture(autouse=True)
def wrap(*args, **kwargs):
    '''
    Check that tests return with empty MuPDF warnings buffer. For example this
    detects failure to call fz_close_output() before fz_drop_output(), which
    (as of 2024-4-12) generates a warning from MuPDF.
    
    As of 2024-09-12 we also detect whether tests leave fds open; but for now
    do not fail tests, because many tests need fixing.
    '''
    wt = pymupdf.TOOLS.mupdf_warnings()
    assert not wt, f'{wt=}'
    assert not pymupdf.TOOLS.set_small_glyph_heights()
    next_fd_before = os.open(__file__, os.O_RDONLY)
    os.close(next_fd_before)
    
    if platform.system() == 'Linux':
        # Gather detailed information about leaked fds.
        def get_fds():
            import subprocess
            path = 'PyMuPDF-linx-fds'
            path_l = 'PyMuPDF-linx-fds-l'
            command = f'ls /proc/{os.getpid()}/fd > {path}'
            command_l = f'ls -l /proc/{os.getpid()}/fd > {path_l}'
            subprocess.run(command, shell=1)
            subprocess.run(command_l, shell=1)
            with open(path) as f:
                ret = f.read()
                ret = ret.replace('\n', ' ')
            with open(path_l) as f:
                ret_l = f.read()
            return ret, ret_l
        open_fds_before, open_fds_before_l = get_fds()
    
    pymupdf._log_items_clear()
    pymupdf._log_items_active(True)
    
    JM_annot_id_stem = pymupdf.JM_annot_id_stem
    
    # Run the test.
    rep = yield
    
    sys.stdout.flush()
    
    # Test has run; check it did not create any MuPDF warnings etc.
    wt = pymupdf.TOOLS.mupdf_warnings()
    if not hasattr(pymupdf, 'mupdf'):
        print(f'Not checking mupdf_warnings on classic.')
    else:
        assert not wt, f'Warnings text not empty: {wt=}'
    
    assert not pymupdf.TOOLS.set_small_glyph_heights()
    
    log_items = pymupdf._log_items()
    assert not log_items, f'log() was called; {len(log_items)=}.'
    
    assert pymupdf.JM_annot_id_stem == JM_annot_id_stem, \
            f'pymupdf.JM_annot_id_stem has changed from {JM_annot_id_stem!r} to {pymupdf.JM_annot_id_stem!r}'
    
    if platform.system() == 'Linux':
        # Show detailed information about leaked fds.
        open_fds_after, open_fds_after_l = get_fds()
        if open_fds_after != open_fds_before:
            import textwrap
            print(f'Test has changed process fds:')
            print(f'    {open_fds_before=}')
            print(f'     {open_fds_after=}')
            print(f'open_fds_before_l:')
            print(textwrap.indent(open_fds_before_l, '    '))
            print(f'open_fds_after_l:')
            print(textwrap.indent(open_fds_after_l, '    '))
            #assert 0
    
    next_fd_after = os.open(__file__, os.O_RDONLY)
    os.close(next_fd_after)
    if next_fd_after != next_fd_before:
        print(f'Test has leaked fds, {next_fd_before=} {next_fd_after=}. {args=} {kwargs=}.')
        #assert 0, f'Test has leaked fds, {next_fd_before=} {next_fd_after=}. {args=} {kwargs=}.'
