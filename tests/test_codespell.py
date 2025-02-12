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
            docs/_static/prism/prism.js
            docs/_static/prism/prism.js
            docs/locales/ja/LC_MESSAGES/changes.po
            docs/locales/ja/LC_MESSAGES/recipes-common-issues-and-their-solutions.po
            docs/locales/
            src_classic/*
            ''')
    skips = skips.strip().replace('\n', ',')
    
    command = textwrap.dedent(f'''
            cd {root} && codespell
                --skip {shlex.quote(skips)}
                --ignore-words-list re-use,flate,thirdparty,re-using
                --ignore-regex 'https?://[a-z0-9/_.]+'
                --ignore-multiline-regex 'codespell:ignore-begin.*codespell:ignore-end'
            ''')
    
    sys.path.append(root)
    try:
        import pipcl
    finally:
        del sys.path[0]
    git_files = pipcl.git_items(root)
    
    for p in git_files:
        _, ext = os.path.splitext(p)
        if ext in ('.png', '.pdf', '.jpg', '.svg'):
            pass
        else:
            command += f'    {p}\n'
    
    if platform.system() != 'Windows':
        command = command.replace('\n', ' \\\n')
    # Don't print entire command because very long, and will be displayed
    # anyway if there is an error.
    #print(f'test_codespell(): Running: {command}')
    print(f'Running codespell.')
    subprocess.run(command, shell=1, check=1)
    print('test_codespell(): codespell succeeded.')
