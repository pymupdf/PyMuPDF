import os
import subprocess


def download(url, name, *, timeout=10, size=None, headers=None):
    '''
    Downloads from <url> to a local file and returns its path. 
    
    If file already exists and matches <size> we do not re-download it.
    
    We put local files within a `cache/` directory so that it is not deleted by
    `git clean` (unless `-d` is specified).
    '''
    path = os.path.normpath(f'{__file__}/../../tests/cache/{name}')
    if os.path.isfile(path) and (not size or os.stat(path).st_size == size):
        print(f'Using existing file {path=}.')
    else:
        print(f'Downloading from {url=}.')
        subprocess.run(f'pip install -U requests', check=1, shell=1)
        import requests
        r = requests.get(url, path, timeout=10, headers=headers)
        r.raise_for_status()
        if size is not None:
            assert len(r.content) == size
        os.makedirs(os.path.dirname(path), exist_ok=1)
        with open(path, 'wb') as f:
            f.write(r.content)
    return path

def skip_slow_tests(test_name):
    PYMUPDF_TEST_QUICK = os.environ.get('PYMUPDF_TEST_QUICK')
    if PYMUPDF_TEST_QUICK == '1':
        print(f'{test_name}(): skipping test because {PYMUPDF_TEST_QUICK=}.')
        return True


def _use_layout():
    '''
    Returns true if we expect pymupdf to be using layout by default.

    We do not look at pymupdf._layout for this because this would not detect
    a situation where pymupdf's import of layout failed unexpectedly. Instead
    we default to returning true (the new default with 2.0) and treat
    PYMUPDF_TEST_USE_LAYOUT=0 as meaning that layout should not have been
    imported.
    '''
    if os.environ.get('PYMUPDF_TEST_USE_LAYOUT') == '0':
        return False
    else:
        return True


def _use_4llm():
    if os.environ.get('PYMUPDF_TEST_USE_4LLM') == '0':
        return False
    else:
        return True
