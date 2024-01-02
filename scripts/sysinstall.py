#! /usr/bin/env python3

'''
Test for Linux system install of MuPDF and PyMuPDF.

We build and install MuPDF and PyMuPDF into a fake root directory, then run
PyMuPDF's pytest tests with LD_PRELOAD_PATH and PYTHONPATH set.

We install required packages with `sudo apt install ...`

[As of 2024-01-04 we are not yet able to test a real system install (e.g. into
/usr/local/) due to pip refusing to do such an install, referencing PEP-668.]

Args:

    --mupdf-dir <mupdf_dir>
        Path of MuPDF checkout; default is 'mupdf'.
    --mupdf-git <git_args>
        Get or update `mupdf_dir` using git. If `mupdf_dir` already
        exists we run `git pull` in it; otherwise we run `git
        clone` with `git_args`. For example:
            --mupdf-git "--branch master https://github.com/ArtifexSoftware/mupdf.git"
    --mupdf-packages 0|1
        If 1 (the default) we install system packages required by MuPDF, using
        `sudo apt install`.
    --pymupdf-dir <pymupdf_dir>
        Path of PyMuPDF checkout; default is 'PyMuPDF'.
    --prefix:
        Directory within `root`; default is `/usr/local`. Must start with `/`.
    --root <root>
        Root of install directory; default is `/`.
    --tesseract5 0|1
        If 1 (the default), we force installation of libtesseract-dev version
        5 (which is not available as a default package in Ubuntu-22.04) from
        package repository ppa:alex-p/tesseract-ocr-devel.
    --test-venv <venv_path>
        Run tests in specified venv; the default is a hard-coded venv name. The
        venv will be created and required packages installed using `pip`. If
        `venv-path` is empty string, we do not create or use a venv, and will
        instead attempt to install required packages with `pip` in the current
        Python environment.
    -m 0|1
        If 1 (the default) we build and install MuPDF, otherwise we just show
        what command we would have run.
    -p 0|1
        If 1 (the default) we build and install PyMuPDF, otherwise we just show
        what command we would have run.
    -t 0|1
        If 1 (the default) we run PyMuPDF's pytest tests, otherwise we just
        show what command we would have run.

To only show what commands would be run, but not actually run them, specify `-m
0 -p 0 -t 0`.
'''

import os
import platform
import subprocess
import sys


def main():
    
    if 1:
        print(f'## {__file__}: Starting.')
        print(f'{sys.executable=}')
        print(f'{platform.python_version()=}')
        print(f'{__file__=}')
        print(f'{sys.argv=}')
    
    # Set default behaviour.
    #
    mupdf = True
    mupdf_dir = 'mupdf'
    mupdf_git = None
    mupdf_packages = True
    prefix = '/usr/local'
    pymupdf = True
    pymupdf_dir = os.path.abspath( f'{__file__}/../..')
    root = 'sysinstall_test'
    tesseract5 = True
    test = True
    test_venv = 'venv-pymupdf-sysinstall-test'
    
    # Parse command-line.
    #
    args = iter(sys.argv[1:])
    while 1:
        try:
            arg = next(args)
        except StopIteration:
            break
        if arg in ('-h', '--help'):
            print(__doc__)
            return
        elif arg == '--mupdf-dir':      mupdf_dir = next(args)
        elif arg == '--mupdf-git':      mupdf_git = next(args)
        elif arg == '--mupdf-packages': mupdf_packages = next(args)
        elif arg == '--prefix':         prefix = next(args)
        elif arg == '--pymupdf-dir':    pymupdf_dir = next(args)
        elif arg == '--root':           root = next(args)
        elif arg == '--tesseract5':     tesseract5 = int(next(args))
        elif arg == '--test-venv':      test_venv = next(args)
        elif arg == '-m':               mupdf = int(next(args))
        elif arg == '-p':               pymupdf = int(next(args))
        elif arg == '-t':               test = int(next(args))
        else:
            assert 0, f'Unrecognised arg: {arg!r}'
    
    assert prefix.startswith('/')
    root = os.path.abspath(root)
    root_prefix = f'{root}{prefix}'.replace('//', '/')
    
    # Get MuPDF from git if specified.
    #
    if mupdf_git:
        # Update existing checkout or do `git clone`.
        if os.path.exists(mupdf_dir):
            print(f'## Update MuPDF checkout {mupdf_dir}.')
            run_command(f'cd {mupdf_dir} && git pull && git submodule update --init')
        else:
            # No existing git checkout, so do a fresh clone.
            print(f'## Clone MuPDF into {mupdf_dir}.')
            run_command(f'git clone --recursive --depth 1 --shallow-submodules {mupdf_git} {mupdf_dir}')
    
    # Install required system packages. We assume a Debian package system.
    #
    print('## Install system packages required by MuPDF.')
    def run(command):
        return run_command(command, doit=mupdf_packages)
    run_command(f'sudo apt update')
    sys_packages = [
            'libfreetype-dev',
            'libgumbo-dev',
            'libharfbuzz-dev',
            'libjbig2dec-dev',
            'libjpeg-dev',
            'libleptonica-dev',
            'libopenjp2-7-dev',
            ]
    run_command(f'sudo apt install {" ".join(sys_packages)}')
    # Ubuntu-22.04 has freeglut3-dev, not libglut-dev.
    run(f'sudo apt install libglut-dev | sudo apt install freeglut3-dev')
    if tesseract5:
        print(f'## Force installation of libtesseract-dev version 5.')
        # https://stackoverflow.com/questions/76834972/how-can-i-run-pytesseract-python-library-in-ubuntu-22-04
        #
        run('sudo apt install -y software-properties-common')
        run('sudo add-apt-repository ppa:alex-p/tesseract-ocr-devel')
        run('sudo apt update')
        run('sudo apt install -y libtesseract-dev')
    else:
        run('sudo apt install libtesseract-dev')
    
    # Build+install MuPDF. We use mupd:Makefile's install-shared-python target.
    #
    print('## Build and install MuPDF.')
    def run(command):
        return run_command(command, doit=mupdf)
    if 1:
        # Current MuPDF creates softlinks with `ln -s` which breaks if there
        # was a previous build; it should do `ln -sf`. We make things work by
        # deleting any existing softlinks here.
        run(f'rm {root_prefix}/lib/libmupdf.so || true')
        run(f'rm {root_prefix}/lib/libmupdfcpp.so || true')
    command = f'cd {mupdf_dir}'
    command += f' && make'
    #command += f' EXE_LDFLAGS=-Wl,--trace' # Makes linker generate diagnostics as it runs.
    command += f' DESTDIR={root}'
    command += f' HAVE_LEPTONICA=yes'
    command += f' HAVE_TESSERACT=yes'
    command += f' USE_SYSTEM_LIBS=yes'
    command += f' build_prefix=system-libs-'
    command += f' prefix={prefix}'
    command += f' verbose=yes'
    command += f' install-shared-python'
    run( command)
    
    # Build+install PyMuPDF.
    #
    print('## Build and install PyMuPDF.')
    def run(command):
        return run_command(command, doit=pymupdf)
    flags_freetype2 = run_command('pkg-config --cflags freetype2', capture_output=1).stdout.strip()
    compile_flags = f'-I {root_prefix}/include {flags_freetype2}'
    link_flags = f'-L {root_prefix}/lib'
    env = ''
    env += f'CFLAGS="{compile_flags}" '
    env += f'CXXFLAGS="{compile_flags}" '
    env += f'LDFLAGS="-L {root}/{prefix}/lib" '
    env += f'PYMUPDF_SETUP_MUPDF_BUILD= '       # Use system MuPDF.
    env += f'PYMUPDF_SETUP_IMPLEMENTATIONS=b'   # Only build the rebased implementation.
    command = f'{env} pip install -vv --root {root} {os.path.abspath(pymupdf_dir)}'
    run( command)
        
    # Run pytest tests.
    #
    print('## Run PyMuPDF pytest tests.')
    def run(command):
        return run_command(command, doit=test)
    import gh_release
    # Create and venv and install
    run(f'{sys.executable} -m venv {test_venv}')
    # Install required packages.
    command = f'. {test_venv}/bin/activate'
    command += f' && pip install --upgrade pip'
    command += f' && pip install --upgrade {gh_release.test_packages}'
    run(command)
    # Run pytest.
    #
    # We need to set PYTHONPATH and LD_LIBRARY_PATH. In particular we
    # use pipcl.install_dir() to find where pipcl will have installed
    # PyMuPDF.
    sys.path.insert(0, pymupdf_dir)
    import pipcl
    del sys.path[0]
    command = f'. {test_venv}/bin/activate'
    command += f' && LD_LIBRARY_PATH={root_prefix}/lib PYTHONPATH={pipcl.install_dir(root)}'
    command += f' pytest -k "not test_color_count" {pymupdf_dir}'
    run(command)


def run_command(command, capture_output=False, check=True, doit=True):
    if doit:
        print(f'## Running: {command}')
        sys.stdout.flush()
        return subprocess.run(command, shell=1, check=check, text=1, capture_output=capture_output)
    else:
        print(f'## Would have run: {command}')


if __name__ == '__main__':
    main()
