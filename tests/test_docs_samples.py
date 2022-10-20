'''
Test sample scripts in docs/samples/.
'''

import os
import pytest
import runpy

# We only look at sample scripts that can run standalone (i.e. don't require
# sys.argv).
#
root = os.path.abspath(f'{__file__}/../..')
samples = []
for p in (
        'docs/samples/code-printer.py',
        'docs/samples/filmfestival-sql.py',
        'docs/samples/new-annots.py',
        'docs/samples/quickfox.py',
        'docs/samples/showpdf-page.py',
        'docs/samples/table01.py',
        ):
    p = os.path.relpath(f'{root}/{p}')
    samples.append(p)

# We use pytest.mark.parametrize() to run sample scripts via a fn, which
# ensures that pytest treats each script as a test.
#
@pytest.mark.parametrize('sample', samples)
def test_docs_samples(sample):
    runpy.run_path(sample)
