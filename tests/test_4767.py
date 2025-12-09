import shutil
import os
import platform
import pymupdf
import subprocess
import sys


def test_4767():
    '''
    Check handling of unsafe paths in `pymupdf embed-extract`.
    '''
    if os.environ.get('PYODIDE_ROOT'):
        print('test_4767(): not running on Pyodide - cannot run child processes.')
        return
    
    if (1
            and platform.system() == 'Windows'
            and os.environ.get('GITHUB_ACTIONS') == 'true'
            and os.environ.get('CIBUILDWHEEL') == '1'
            ):
        print(f'test_4767(): not running because known to fail on Github/Windows/Cibuildwheel.')
        # Using -unsafe makes pymupdf return 0 but does not seem to create
        # output file.
        return
        
    with pymupdf.open() as document:
        document.new_page() 
        document.embfile_add(
                'evil_entry',
                b'poc:traversal test\n',
                filename="../../test.txt",
                ufilename="../../test.txt",
                desc="poc",
                )
        document.embfile_add(
                'evil_entry2',
                b'poc:traversal test\n',
                filename="test2.txt",
                ufilename="test2.txt",
                desc="poc",
                )
        path = os.path.abspath(f'{__file__}/../../tests/test_4767.pdf')
        document.save(path)
    testdir = os.path.abspath(f'{__file__}/../../tests/test_4767_dir').replace('\\', '/')
    shutil.rmtree(testdir, ignore_errors=1)
    os.makedirs(f'{testdir}/one/two', exist_ok=1)
    
    def run(command, *, check=0, capture=1):
        print(f'Running: {command}')
        cp = subprocess.run(
                command, shell=1,
                text=1,
                check=check,
                stdout=subprocess.PIPE if capture else None,
                stderr=subprocess.STDOUT if capture else None,
                )
        print(cp.stdout)
        return cp
    
    def get_paths():
        paths = list()
        for dirpath, dirnames, filenames in os.walk(testdir):
            for filename in filenames:
                path = f'{dirpath}/{filename}'.replace('\\', '/')
                paths.append(path)
        return paths
    
    cp = run(f'cd {testdir}/one/two && {sys.executable} -m pymupdf embed-extract {path} -name evil_entry')
    print(cp.stdout)
    assert cp.returncode
    assert cp.stdout == 'refusing to write stored name outside current directory: ../../test.txt\n'
    assert not get_paths()
    
    cp = run(f'cd {testdir}/one/two && {sys.executable} -m pymupdf embed-extract {path} -name evil_entry -unsafe')
    assert cp.returncode == 0
    assert cp.stdout == "saved entry 'evil_entry' as '../../test.txt'\n"
    paths = get_paths()
    print(f'{paths=}')
    assert paths == [f'{testdir}/test.txt']
    
    cp = run(f'cd {testdir}/one/two && {sys.executable} -m pymupdf embed-extract {path} -name evil_entry2')
    assert not cp.returncode
    assert cp.stdout == "saved entry 'evil_entry2' as 'test2.txt'\n"
    paths = get_paths()
    print(f'{paths=}')
    assert paths == [f'{testdir}/test.txt', f'{testdir}/one/two/test2.txt']
    
    cp = run(f'cd {testdir}/one/two && {sys.executable} -m pymupdf embed-extract {path} -name evil_entry2')
    assert cp.returncode
    assert cp.stdout == "refusing to overwrite existing file with stored name: test2.txt\n"
    paths = get_paths()
    print(f'{paths=}')
    assert paths == [f'{testdir}/test.txt', f'{testdir}/one/two/test2.txt']
    
    cp = run(f'cd {testdir}/one/two && {sys.executable} -m pymupdf embed-extract {path} -name evil_entry2 -unsafe')
    assert not cp.returncode
    assert cp.stdout == "saved entry 'evil_entry2' as 'test2.txt'\n"
    paths = get_paths()
    print(f'{paths=}')
    assert paths == [f'{testdir}/test.txt', f'{testdir}/one/two/test2.txt']
