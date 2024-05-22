import pymupdf

import os
import subprocess


def test_codespell():
    '''
    Check rebased Python code with flake8.
    '''
    if not hasattr(pymupdf, 'mupdf'):
        print('Not running codespell with classic implementation.')
        return
    root = os.path.abspath(f'{__file__}/../..')
    def run(command):
        print(f'test_codespell(): Running: {command}')
        prev_workdir = os.getcwd()
        os.chdir(root)
        subprocess.run(command, shell=1, check=1)
        os.chdir(prev_workdir)
    # careful: I don't think paths like `docs/locales` works
    skips = "*.pdf,src_classic,locales,prism.js,tests"
    run(f'codespell -x .codespell-ignorelines -I .codespell-ignorewords --skip {skips}')
    print('test_codespell(): codespell succeeded.')
