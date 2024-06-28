import pymupdf

import os
import platform
import shlex
import subprocess
import sys
import textwrap


def test_codespell():
    '''
    Check rebased Python code with codespell.
    '''
    if not hasattr(pymupdf, 'mupdf'):
        print('Not running codespell with classic implementation.')
        return
    
    if platform.system() == 'Windows':
        # Git commands seem to fail on Github Windows runners.
        print(f'test_codespell(): Not running on Widows')
        return
        
    root = os.path.abspath(f'{__file__}/../..')
    
    # For now we ignore files that we would ideally still look at, because it
    # is difficult to exclude some text sections.
    skips = textwrap.dedent('''
            *.pdf
            changes.txt
            docs/_static/prism/prism.js
            docs/_static/prism/prism.js
            docs/locales/ja/LC_MESSAGES/changes.po
            docs/locales/ja/LC_MESSAGES/recipes-common-issues-and-their-solutions.po
            docs/recipes-common-issues-and-their-solutions.rst
            docs/recipes-text.rst
            docs/samples/national-capitals.py
            locales
            src_classic/*
            tests
            tests/test_story.py
            tests/test_textbox.py
            tests/test_textextract.py
            ''')
    skips = skips.strip().replace('\n', ',')
    
    command = f'cd {root} && codespell --skip {shlex.quote(skips)} --count'
    command += f' --ignore-words-list re-use,flate,thirdparty'
    
    sys.path.append(root)
    try:
        import pipcl
    finally:
        del sys.path[0]
    git_files = pipcl.git_items(root)
    
    for p in git_files:
        _, ext = os.path.splitext(p)
        if ext in ('.png', '.pdf'):
            pass
        else:
            command += f' {p}'
    
    print(f'test_codespell(): Running: {command}')
    subprocess.run(command, shell=1, check=1)
    print('test_codespell(): codespell succeeded.')
