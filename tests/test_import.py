import os
import subprocess
import sys
import textwrap


def test_import():
    root = os.path.abspath(f'{__file__}/../../')
    p = f'{root}/tests/resources_test_import.py'
    with open(p, 'w') as f:
        f.write(textwrap.dedent(
                '''
                from pymupdf.utils import *
                from pymupdf.table import *
                from pymupdf import *
                '''
                ))
    subprocess.run(f'{sys.executable} {p}', shell=1, check=1)
