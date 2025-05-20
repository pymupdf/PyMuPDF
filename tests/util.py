import os
import subprocess


def download(url, name, size=None):
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
        r = requests.get(url, path, timeout=10)
        r.raise_for_status()
        if size is not None:
            assert len(r.content) == size
        os.makedirs(os.path.dirname(path), exist_ok=1)
        with open(path, 'wb') as f:
            f.write(r.content)
    return path
