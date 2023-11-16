#! /usr/bin/env python3

'''Simple build/test script for PyMuPDF.

Examples:

    ./PyMuPDF/scripts/test.py --mupdf mupdf buildtest
        Build and test with pre-existing local mupdf/ checkout.

    ./PyMuPDF/scripts/test.py buildtest
        Build and test with default internal download of mupdf.

    ./PyMuPDF/scripts/test.py --mupdf 'git:https://git.ghostscript.com/mupdf.git' buildtest
        Build and test with internal checkout of mupdf master.

    ./PyMuPDF/scripts/test.py --mupdf 'git:--branch 1.23.x https://github.com/ArtifexSoftware/mupdf.git' buildtest
        Build and test using internal checkout of mupdf 1.23.x branch from Github.

Args:
    -h
    --help
        Show help.
    --mupdf <location>
        Location of local mupdf/ directory or 'git:...' to be used by
        subsequent build* args. Used to set PYMUPDF_SETUP_MUPDF_BUILD for
        PyMuPDF/setup.py. If not specifed PyMuPDF will download its default
        mupdf .tgz.
    build
        Builds and installs using `pip install .../PyMuPDF`.
    buildtest
        Same as 'build test'.
    test
        Runs PyMuPDF's pytest tests, testing classic, rebased and unoptimised
        rebased.

If not running inside a Python venv, we automatically create a venv and rerun
ourselves inside it.
'''

import gh_release

import os
import platform
import sys


pymupdf_dir = os.path.abspath( f'{__file__}/../..')


def main(argv):

    if len(argv) >= 2 and argv[1] in ('-h', '--help'):
        print(__doc__)
        return

    # We always want to run inside a venv.
    if sys.prefix == sys.base_prefix:
        # Not running in a venv.
        gh_release.venv( ['python'] + argv)
        return

    args = iter( argv[1:])
    while 1:
        try:
            arg = next(args)
        except StopIteration:
            break
        if arg == '--mupdf':
            mupdf = next(args)
            if not mupdf.startswith('git:'):
                assert os.path.isdir(mupdf), f'Not a directory: {mupdf=}.'
                mupdf = os.path.abspath(mupdf)
            os.environ['PYMUPDF_SETUP_MUPDF_BUILD'] = mupdf
        elif arg == 'build':
            build()
        elif arg == 'test':
            test()
        elif arg == 'buildtest':
            build()
            test()
        else:
            assert 0, f'Unrecognised arg: {arg=}.'


def build():
    nbi = ''
    if platform.system() == 'OpenBSD':
        # libclang not available on pypi.org, so we need to force use of system
        # package py3-llvm with --no-build-isolation, manually installing other
        # required packages.
        gh_release.run(f'pip install swig setuptools psutil')
        gh_release.run(f'pip install --no-build-isolation -vv {pymupdf_dir}')
    else:
        gh_release.run(f'pip install{nbi} -vv {pymupdf_dir}')


def test():
    gh_release.run(f'pip install pytest fontTools psutil')
    if platform.system() == 'OpenBSD':
        # On OpenBSD `pip install pytest` doesn't seem to install the pytest
        # command, so we use `python -m pytest ...`. (This doesn't work on
        # Windows for some reason so we don't use it all the time.)
        gh_release.run(f'{sys.executable} {pymupdf_dir}/tests/run_compound.py python -m pytest -s {pymupdf_dir}')
    else:
        gh_release.run(f'{sys.executable} {pymupdf_dir}/tests/run_compound.py pytest -s {pymupdf_dir}')


if __name__ == '__main__':
    main(sys.argv)
