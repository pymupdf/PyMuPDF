#! /usr/bin/env python3

'''Simple build/test script for PyMuPDF.

Unlike gh_release.py, we build directly, not with cibuildwheel.

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
    --build-isolation 0|1
    -h
    --help
        Show help.
    --mupdf <location>
        Location of local mupdf/ directory or 'git:...' to be used by
        subsequent build* args. Used to set PYMUPDF_SETUP_MUPDF_BUILD for
        PyMuPDF/setup.py. If not specifed PyMuPDF will download its default
        mupdf .tgz.
    --valgrind 0|1
        Use valgrind in subsequent `test` or `buildtest`.
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

    build_isolation = None
    valgrind = False
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
        elif arg == '--build-isolation':
            build_isolation = int(next(args))
        elif arg == '--valgrind':
            valgrind = int(next(args))
        elif arg == 'build':
            build(build_isolation=build_isolation)
        elif arg == 'test':
            test(valgrind=valgrind)
        elif arg == 'buildtest':
            build(build_isolation=build_isolation)
            test(valgrind=valgrind)
        else:
            assert 0, f'Unrecognised arg: {arg=}.'


def build(build_isolation=None):
    print(f'{build_isolation=}')
    if platform.system() == 'OpenBSD':
        # libclang not available on pypi.org, so we need to force use of system
        # package py3-llvm with --no-build-isolation, manually installing other
        # required packages.
        if build_isolation is None:
            build_isolation = False    
    if not build_isolation:
        if platform.system() == 'OpenBSD':
            gh_release.run(f'pip install swig setuptools psutil')
        else:
            gh_release.run(f'pip install libclang swig setuptools psutil')
    build_isolation_text = '' if build_isolation else ' --no-build-isolation'
    gh_release.run(f'pip install{build_isolation_text} -vv {pymupdf_dir}')


def test(valgrind):
    if os.getcwd() == pymupdf_dir:
        gh_release.log('Changing into parent directory to avoid confusion from `fitz/` directory.')
        os.chdir(os.path.dirname(pymupdf_dir))
    gh_release.run(f'pip install {gh_release.test_packages}')
    if valgrind:
        gh_release.log('Installing valgrind.')
        gh_release.run(f'sudo apt update')
        gh_release.run(f'sudo apt install valgrind')
        gh_release.run(f'valgrind --version')
        
        gh_release.log('Running PyMuPDF tests under valgrind.')
        gh_release.run(
                f'{sys.executable} {pymupdf_dir}/tests/run_compound.py'
                    f' valgrind --suppressions={pymupdf_dir}/valgrind.supp --error-exitcode=100 --errors-for-leak-kinds=none --fullpath-after='
                    f' pytest -s -vv {pymupdf_dir}/tests'
                    ,
                env_extra=dict(
                    PYTHONMALLOC='malloc',
                    PYMUPDF_RUNNING_ON_VALGRIND='1',
                    ),
                )
    elif platform.system() == 'OpenBSD':
        # On OpenBSD `pip install pytest` doesn't seem to install the pytest
        # command, so we use `python -m pytest ...`. (This doesn't work on
        # Windows for some reason so we don't use it all the time.)
        gh_release.run(f'{sys.executable} {pymupdf_dir}/tests/run_compound.py python -m pytest -s {pymupdf_dir}')
    else:
        gh_release.run(f'{sys.executable} {pymupdf_dir}/tests/run_compound.py pytest -s {pymupdf_dir}')


if __name__ == '__main__':
    main(sys.argv)
