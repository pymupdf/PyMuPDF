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

# We use pytest.mark.parametrize() to run sample scripts via a fn, which
# ensures that pytest treats each script as a test.
#
@pytest.mark.parametrize('sample', samples)
def test_docs_samples(sample):
    runpy.run_path(sample)
