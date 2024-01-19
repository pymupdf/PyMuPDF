'''
Test sample scripts in docs/samples/.
'''

import glob
import os
import pytest
import runpy

# We only look at sample scripts that can run standalone (i.e. don't require
# sys.argv).
#
root = os.path.abspath(f'{__file__}/../..')
samples = []
for p in glob.glob(f'{root}/docs/samples/*.py'):
    if os.path.basename(p) in (
             'make-bold.py',    # Needs sys.argv[1].
             'multiprocess-gui.py', # GUI.
             'multiprocess-render.py',  # Needs sys.argv[1].
             'text-lister.py',  # Needs sys.argv[1].
            ):
        print(f'Not testing: {p}')
    else:
        samples.append(p)

def _test_all():
    # Allow runnings tests directly without pytest.
    import subprocess
    import sys
    e = 0
    for sample in samples:
        print( f'Running: {sample}', flush=1)
        try:
            if 0:
                # Curiously this fails in an odd way when testing compound
                # package with $PYTHONPATH set.
                print( f'os.environ is:')
                for n, v in os.environ.items():
                    print( f'    {n}: {v!r}')
                command = f'{sys.executable} {sample}'
                print( f'command is: {command!r}')
                sys.stdout.flush()
                subprocess.check_call( command, shell=1, text=1)
            else:
                runpy.run_path(sample)
        except Exception:
            print( f'Failed: {sample}')
            e += 1
    if e:
        raise Exception( f'Errors: {e}')

# We use pytest.mark.parametrize() to run sample scripts via a fn, which
# ensures that pytest treats each script as a test.
#
@pytest.mark.parametrize('sample', samples)
def test_docs_samples(sample):
    runpy.run_path(sample)
