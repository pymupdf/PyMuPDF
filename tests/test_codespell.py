import pymupdf

import os
import shlex
import subprocess
import sys


def test_codespell():
    '''
    Check rebased Python code with codespell.
    '''
    if not hasattr(pymupdf, 'mupdf'):
        print('Not running codespell with classic implementation.')
        return
    root = os.path.abspath(f'{__file__}/../..')
    sys.path.append(root)
    try:
        import pipcl
    finally:
        del sys.path[0]
    # careful: I don't think paths like `docs/locales` works
    skips = "*.pdf,src_classic/*,locales,prism.js,tests"
    command = f'cd {root} && codespell --skip {shlex.quote(skips)} --count'
    command += f' --ignore-words-list re-use,flate,thirdparty'
    #command += f' --ignore-regex ".*# codespell:ignore-line$"
    command += ' --ignore-regex "^.*[<][!]-- codespell:ignore-line --[>].*$"'
    # `(?s:.)` matches any character including newline.
    command += ' --ignore-regex "codespell:ignore-begin(?s:.)*codespell:ignore-end"'
    for p in pipcl.git_items(root):
        _, ext = os.path.splitext(p)
        if ext in ('.png', '.pdf'):
            pass
        else:
            command += f' {p}'
    print(f'test_codespell(): Running: {command}')
    subprocess.run(command, shell=1, check=1)
    print('test_codespell(): codespell succeeded.')
