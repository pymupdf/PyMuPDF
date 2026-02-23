import copy
import os
import platform
import subprocess
import sys

import pytest

# Install required packages. There doesn't seem to be any official way for
# us to programmatically specify required test packages in setup.py, or in
# pytest. Doing it here seems to be the least ugly approach.
#
# However our diagnostics do not show up so this can cause an unfortunate pause
# before tests start to run.
#
def install_required_packages():
    PYODIDE_ROOT = os.environ.get('PYODIDE_ROOT')
    if PYODIDE_ROOT:
        # We can't run child processes, so rely on required test packages
        # already being installed, e.g. in our wheel's <requires_dist>.
        return
    packages = 'pytest fontTools pymupdf-fonts flake8 pylint codespell mypy'
    if platform.system() == 'Windows' and int.bit_length(sys.maxsize+1) == 32:
        # No pillow wheel available, and doesn't build easily.
        pass
    elif platform.python_implementation() == 'GraalVM':
        pass
    else:
        packages += ' pillow'
    if platform.system().startswith('MSYS_NT-'):
        # psutil not available on msys2.
        pass
    else:
        packages += ' psutil'
    command = f'pip install --upgrade {packages}'
    print(f'{__file__}:install_required_packages)(): Running: {command}', flush=1)
    subprocess.run(command, shell=1, check=1)

install_required_packages()


@pytest.fixture(scope="session", autouse=True)
def log_global_env_facts(record_testsuite_property):
    record_testsuite_property('platform.python_version()', platform.python_version())

# Need to import pymupdf only after we've installed pymupdf-fonts above,
# because pymupdf imports pymupdf_fonts, and copes with import failure.
import pymupdf


PYMUPDF_PYTEST_RESUME = os.environ.get('PYMUPDF_PYTEST_RESUME')

@pytest.fixture(autouse=True)
def wrap(request):
    '''
    Check that tests return with empty MuPDF warnings buffer. For example this
    detects failure to call fz_close_output() before fz_drop_output(), which
    (as of 2024-4-12) generates a warning from MuPDF.
    
    As of 2024-09-12 we also detect whether tests leave fds open; but for now
    do not fail tests, because many tests need fixing.
    '''
    global PYMUPDF_PYTEST_RESUME
    if PYMUPDF_PYTEST_RESUME:
        # Skip all tests until we reach a matching name.
        if PYMUPDF_PYTEST_RESUME == request.function.__name__:
            print(f'### {PYMUPDF_PYTEST_RESUME=}: resuming at {request.function.__name__=}.')
            PYMUPDF_PYTEST_RESUME = None
        else:
            print(f'### {PYMUPDF_PYTEST_RESUME=}: Skipping {request.function.__name__=}.')
            return
    
    wt = pymupdf.TOOLS.mupdf_warnings()
    assert not wt, f'{wt=}'
    if platform.python_implementation() == 'GraalVM':
        pymupdf.TOOLS.set_small_glyph_heights()
    else:
        assert not pymupdf.TOOLS.set_small_glyph_heights()
    next_fd_before = os.open(__file__, os.O_RDONLY)
    os.close(next_fd_before)
    
    if platform.system() == 'Linux' and platform.python_implementation() != 'GraalVM':
        test_fds = True
    else:
        test_fds = False
        
    if test_fds:
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
    
    def get_members(a):
        ret = dict()
        for n in dir(a):
            if not n.startswith('_'):
                v = getattr(a, n)
                ret[n] = v
        return ret
        
    # Allow post-test checking that pymupdf._globals has not changed.
    _globals_pre = get_members(pymupdf._globals)
    
    testsfailed_before = request.session.testsfailed
    
    # Run the test.
    rep = yield
    
    sys.stdout.flush()
    
    # This seems the only way for us to tell that a test has failed. In
    # particular, <rep> is always None. We're implicitly relying on tests not
    # being run in parallel.
    #
    failed = request.session.testsfailed - testsfailed_before
    assert failed in (0, 1)
    
    if failed:
        # Do not check post-test conditions if the test as failed. This avoids
        # additional confusing `ERROR` status for failed tests.
        return
    
    # Test has run; check it did not create any MuPDF warnings etc.
    wt = pymupdf.TOOLS.mupdf_warnings()
    if not hasattr(pymupdf, 'mupdf'):
        print(f'Not checking mupdf_warnings on classic.')
    else:
        assert not wt, f'Warnings text not empty: {wt=}'
    
    assert not pymupdf.TOOLS.set_small_glyph_heights()
    
    _globals_post = get_members(pymupdf._globals)
    if _globals_post != _globals_pre:
        print(f'Test has changed pymupdf._globals from {_globals_pre=} to {_globals_post=}')
        assert 0
    
    log_items = pymupdf._log_items()
    assert not log_items, f'log() was called; {len(log_items)=}.'
    
    assert pymupdf.JM_annot_id_stem == JM_annot_id_stem, \
            f'pymupdf.JM_annot_id_stem has changed from {JM_annot_id_stem!r} to {pymupdf.JM_annot_id_stem!r}'
    
    if test_fds:
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
    
    if test_fds and next_fd_after != next_fd_before:
        print(f'Test has leaked fds, {next_fd_before=} {next_fd_after=}.')
        #assert 0, f'Test has leaked fds, {next_fd_before=} {next_fd_after=}. {args=} {kwargs=}.'
    
    if 0:
        # This code can be useful to track down test failures caused by other
        # tests modifying global state.
        #
        # We run a particular test menually after each test returns.
        sys.path.insert(0, os.path.dirname(__file__))
        try:
            import test_tables
        finally:
            del sys.path[0]
        print(f'### Calling test_tables.test_md_styles().')
        try:
            test_tables.test_md_styles()
        except Exception as e:
            print(f'### test_tables.test_md_styles() failed: {e}')
            raise
        else:
            print(f'### test_tables.test_md_styles() passed.')
