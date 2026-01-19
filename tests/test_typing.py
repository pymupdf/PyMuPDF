import os
import subprocess

import pymupdf


def run(command, check=1):
    print(f'Running: {command}')
    subprocess.run(command, shell=1, check=check)

def test_py_typed():

    if os.path.basename(__file__).startswith(f'test_fitz_'):
        # Don't test the `fitz` alias, because mypy complains.
        print(f'test_py_typed(): Not testing with fitz alias.')
        return
    
    if os.environ.get('PYODIDE_ROOT'):
        print('test_py_typed(): not running on Pyodide - cannot run child processes.')
        return
        
    print(f'test_py_typed(): {pymupdf.__path__=}')
    run('pip uninstall -y mypy')
    run('pip install mypy')
    root = os.path.abspath(f'{__file__}/../..')
    
    # Run mypy on this .py file; it will fail at `import pymypdf` if the
    # pymupdf install does not have a py.typed file.
    #
    # This doesn't actually check pymupdf's typing. It looks like
    # we can do that with `mypy -m pymupdf`, but as of 2026-1-18 this
    # gives many errors such as:
    #
    #   ...site-packages/pymupdf/__init__.py:15346: error: point_like? has no attribute "y"  [attr-defined]
    #
    # It's important to use `--no-incremental`, otherwise if one has
    # experimented with `mypy -m pymupdf`, this test will get the
    # same failures, via `.mypy_cache/` directories.
    #
    # We run in sub-directory to avoid spurious mypy errors
    # if there is a local mupdf/ directory.
    #
    run(f'cd {root}/tests && mypy --no-incremental {os.path.abspath(__file__)}')
