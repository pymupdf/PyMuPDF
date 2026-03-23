import pymupdf

import os
import platform
import shlex
import subprocess
import sys
import textwrap


def test_codespell():
    '''
    Check Python code with codespell.
    '''
    if os.environ.get('PYODIDE_ROOT'):
        print('test_codespell(): not running on Pyodide - cannot run child processes.')
        return
        
    if platform.system() == 'Windows':
        # Git commands seem to fail on Github Windows runners.
        print(f'test_codespell(): Not running on Windows')
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
    
    command_args_path = os.path.normpath(f'{__file__}/../test_codespell_args.txt')
    command += f'    @{command_args_path}'
    
    with open(command_args_path, 'w') as f:
    
        for p in git_files:
            _, ext = os.path.splitext(p)
            if ext in ('.png', '.pdf', '.jpg', '.svg'):
                pass
            else:
                #command += f'    {p}\n'
                print(p, file=f)
    
    if platform.system() != 'Windows':
        command = command.replace('\n', ' \\\n')
    if 0:
        with open(command_args_path) as f:
            command_args_path_contents = f.read()
        print(f'command_args_path:{command_args_path_contents}')
    print(f'Running codespell: {command}')
    subprocess.run(command, shell=1, check=1)
    print('test_codespell(): codespell succeeded.')
