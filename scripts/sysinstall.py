#! /usr/bin/env python3

'''
Test for Linux system install of MuPDF and PyMuPDF.

We build and install MuPDF and PyMuPDF into a root directory, then use
scripts/test.py to run PyMuPDF's pytest tests with LD_PRELOAD_PATH and
PYTHONPATH set.

PyMuPDF itself is installed using `python -m install` with a wheel created with
`pip wheel`.

We run install commands with `sudo` if `--root /` is used.

Note that we run some commands with sudo; it's important that these use the
same python as non-sudo, otherwise things can be build and installed for
different python versions. For example when we are run from a github action, it
should not do `- uses: actions/setup-python@v2` but instead use whatever system
python is already defined.

Args:

    --mupdf-dir <mupdf_dir>
        Path of MuPDF checkout; default is 'mupdf'.
    --mupdf-do 0|1
        Whether to build and install mupdf.
    --mupdf-git <git_args>
        Get or update `mupdf_dir` using git. If `mupdf_dir` already
        exists we run `git pull` in it; otherwise we run `git
        clone` with `<git_args> <mupdf_dir>`. For example:
            --mupdf-git "--branch master https://github.com/ArtifexSoftware/mupdf.git"
    --mupdf-so-mode <mode>
        Used with `install -m <mode> ...` when installing MuPDF. For example
        `--mupdf-so-mode 744`.
    --packages 0|1
        If 1 (the default) we install required system packages such as
        `libfreetype-dev`.
    --pip 0|venv|sudo
        Whether/how to install Python packages.
        If '0' we assume required packages are already available.
        If 'sudo' we install required Python packages using `sudo pip install
        ...`.
        If 'venv' (the default) we install Python packages and run installer
        and test commands inside venv's.
    --prefix:
        Directory within `root`; default is `/usr/local`. Must start with `/`.
    --pymupdf-dir <pymupdf_dir>
        Path of PyMuPDF checkout; default is 'PyMuPDF'.
    --pymupdf-do 0|1
        Whether to build and install pymupdf.
    --root <root>
        Root of install directory; default is `/`.
    --tesseract5 0|1
        If 1 (the default), we force installation of libtesseract-dev version
        5 (which is not available as a default package in Ubuntu-22.04) from
        package repository ppa:alex-p/tesseract-ocr-devel.
    --test-venv <test_venv>
        Set the name of the venv in which we run tests (only with `--pip
        venv`); the default is a hard-coded venv name. The venv will be
        created, and required packages installed using `pip`.
    --use-installer 0|1
        If 1 (the default), we use `python -m installer` to install PyMuPDF
        from a generated wheel. [Otherwise we use `pip install`, which refuses
        to do a system install with `--root /`, referencing PEP-668.]
    -i <implementations>
        Passed through to scripts/test.py.
    -f <test-fitz>
        Passed through to scripts/test.py.
    -p <pytest-options>
        Passed through to scripts/test.py.
    -t <names>
        Passed through to scripts/test.py.

To only show what commands would be run, but not actually run them, specify `-m
0 -p 0 -t 0`.
'''

import glob
import multiprocessing
import os
import platform
import shlex
import subprocess
import sys
import sysconfig

import test as test_py

# Requirements for a system build and install:
#
# system packages (Debian names):
#
g_sys_packages = [
        'libfreetype-dev',
        'libgumbo-dev',
        'libharfbuzz-dev',
        'libjbig2dec-dev',
        'libjpeg-dev',
        'libleptonica-dev',
        'libopenjp2-7-dev',
        ]
# We also need libtesseract-dev version 5.
#


def main():
    
    if 1:
        print(f'## {__file__}: Starting.')
        print(f'{sys.executable=}')
        print(f'{platform.python_version()=}')
        print(f'{__file__=}')
        print(f'{sys.argv=}')
        print(f'{sysconfig.get_path("platlib")=}')
        run_command(f'python -V', check=0)
        run_command(f'python3 -V', check=0)
        run_command(f'sudo python -V', check=0)
        run_command(f'sudo python3 -V', check=0)
        run_command(f'sudo PATH={os.environ["PATH"]} python -V', check=0)
        run_command(f'sudo PATH={os.environ["PATH"]} python3 -V', check=0)
    
    # Set default behaviour.
    #
    use_installer = True
    mupdf_do = True
    mupdf_dir = 'mupdf'
    mupdf_git = None
    mupdf_so_mode = None
    packages = True
    prefix = '/usr/local'
    pymupdf_do = True
    pymupdf_dir = os.path.abspath( f'{__file__}/../..')
    root = 'sysinstall_test'
    tesseract5 = True
    pytest_args = None
    pytest_do = True
    pytest_name = None
    test_venv = 'venv-pymupdf-sysinstall-test'
    pip = 'venv'
    test_fitz = None
    test_implementations = None
    
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
        elif arg == '--mupdf-do':       mupdf_do = int(next(args))
        elif arg == '--mupdf-dir':      mupdf_dir = next(args)
        elif arg == '--mupdf-git':      mupdf_git = next(args)
        elif arg == '--mupdf-so-mode':  mupdf_so_mode = next(args)
        elif arg == '--packages':       packages = int(next(args))
        elif arg == '--prefix':         prefix = next(args)
        elif arg == '--pymupdf-do':     pymupdf_do = int(next(args))
        elif arg == '--pymupdf-dir':    pymupdf_dir = next(args)
        elif arg == '--root':           root = next(args)
        elif arg == '--tesseract5':     tesseract5 = int(next(args))
        elif arg == '--pytest-do':      pytest_do = int(next(args))
        elif arg == '--test-venv':      test_venv = next(args)
        elif arg == '--use-installer':  use_installer = int(next(args))
        elif arg == '--pip':            pip = next(args)
        elif arg == '-f':               test_fitz = next(args)
        elif arg == '-i':               test_implementations = next(args)
        elif arg == '-p':               pytest_args = next(args)
        elif arg == '-t':               pytest_name = next(args)
        else:
            assert 0, f'Unrecognised arg: {arg!r}'
    
    assert prefix.startswith('/')
    pip_values = ('0', 'sudo', 'venv')
    assert pip in pip_values, f'Unrecognised --pip value {pip!r} should be one of: {pip_values!r}'
    root = os.path.abspath(root)
    root_prefix = f'{root}{prefix}'.replace('//', '/')
    
    sudo = ''
    if root == '/':
        sudo = f'sudo PATH={os.environ["PATH"]} '
    def run(command):
        return run_command(command, doit=mupdf_do)
    # Get MuPDF from git if specified.
    #
    if mupdf_git:
        # Update existing checkout or do `git clone`.
        if os.path.exists(mupdf_dir):
            print(f'## Update MuPDF checkout {mupdf_dir}.')
            run(f'cd {mupdf_dir} && git pull && git submodule update --init')
        else:
            # No existing git checkout, so do a fresh clone.
            print(f'## Clone MuPDF into {mupdf_dir}.')
            run(f'git clone --recursive --depth 1 --shallow-submodules {mupdf_git} {mupdf_dir}')
    
    if packages:
        # Install required system packages. We assume a Debian package system.
        #
        print('## Install system packages required by MuPDF.')
        run(f'sudo apt update')
        run(f'sudo apt install {" ".join(g_sys_packages)}')
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
    if pip == 'sudo':
        print('## Installing Python packages required for building MuPDF and PyMuPDF.')
        run(f'sudo pip install --upgrade pip')
        names = test_py.wrap_get_requires_for_build_wheel(f'{__file__}/../..')
        run(f'sudo pip install {names}')
    
    print('## Build and install MuPDF.')
    command = f'cd {mupdf_dir}'
    command += f' && {sudo}make'
    command += f' -j {multiprocessing.cpu_count()}'
    #command += f' EXE_LDFLAGS=-Wl,--trace' # Makes linker generate diagnostics as it runs.
    command += f' DESTDIR={root}'
    command += f' HAVE_LEPTONICA=yes'
    command += f' HAVE_TESSERACT=yes'
    command += f' USE_SYSTEM_LIBS=yes'
    command += f' VENV_FLAG={"--venv" if pip == "venv" else ""}'
    if mupdf_so_mode:
        command += f' SO_INSTALL_MODE={mupdf_so_mode}'
    command += f' build_prefix=system-libs-'
    command += f' prefix={prefix}'
    command += f' verbose=yes'
    command += f' install-shared-python'
    command += f' INSTALL_MODE=755'
    run( command)
    
    # Build+install PyMuPDF.
    #
    print('## Build and install PyMuPDF.')
    def run(command):
        return run_command(command, doit=pymupdf_do)
    flags_freetype2 = run_command('pkg-config --cflags freetype2', capture_output=1).stdout.strip()
    compile_flags = f'-I {root_prefix}/include {flags_freetype2}'
    link_flags = f'-L {root_prefix}/lib'
    env = ''
    env += f'CFLAGS="{compile_flags}" '
    env += f'CXXFLAGS="{compile_flags}" '
    env += f'LDFLAGS="-L {root}/{prefix}/lib" '
    env += f'PYMUPDF_SETUP_MUPDF_BUILD= '       # Use system MuPDF.
    if use_installer:
        print(f'## Building wheel.')
        if pip == 'venv':
            venv_name = 'venv-pymupdf-sysinstall'
        run(f'pwd')
        run(f'rm dist/* || true')
        if pip == 'venv':
            run(f'{sys.executable} -m venv {venv_name}')
            run(f'. {venv_name}/bin/activate && pip install --upgrade pip')
            run(f'. {venv_name}/bin/activate && pip install --upgrade installer')
            run(f'{env} {venv_name}/bin/python -m pip wheel -vv -w dist {os.path.abspath(pymupdf_dir)}')
        elif pip == 'sudo':
            run(f'sudo pip install --upgrade pip')
            run(f'sudo pip install installer')
            run(f'{env} pip wheel -vv -w dist {os.path.abspath(pymupdf_dir)}')
        else:
            log(f'Not installing "installer" because {pip=}.')
        wheel = glob.glob(f'dist/*')
        assert len(wheel) == 1, f'{wheel=}'
        wheel = wheel[0]
        print(f'## Installing wheel using `installer`.')
        pv = '.'.join(platform.python_version_tuple()[:2])
        p = f'{root_prefix}/lib/python{pv}'
        # `python -m installer` fails to overwrite existing files.
        run(f'{sudo}rm -r {p}/site-packages/pymupdf || true')
        run(f'{sudo}rm -r {p}/site-packages/pymupdf.py || true')
        run(f'{sudo}rm -r {p}/site-packages/fitz || true')
        run(f'{sudo}rm -r {p}/site-packages/fitz.py || true')
        run(f'{sudo}rm -r {p}/site-packages/PyMuPDF-*.dist-info || true')
        run(f'{sudo}rm -r {root_prefix}/bin/pymupdf || true')
        if pip == 'venv':
            run(f'{sudo}{venv_name}/bin/python -m installer --destdir {root} --prefix {prefix} {wheel}')
        else:
            run(f'{sudo}{sys.executable} -m installer --destdir {root} --prefix {prefix} {wheel}')
        # It seems that MuPDF Python bindings are installed into
        # `.../dist-packages` (from mupdf:Mafile's call of `$(shell python3
        # -c "import sysconfig; print(sysconfig.get_path('platlib'))")` while
        # `python -m installer` installs PyMuPDF into `.../site-packages`.
        #
        # This might be because `sysconfig.get_path('platlib')` returns
        # `.../site-packages` if run in a venv, otherwise `.../dist-packages`.
        #
        # And on github ubuntu-latest, sysconfig.get_path("platlib") is
        #   /opt/hostedtoolcache/Python/3.11.7/x64/lib/python3.11/site-packages
        #
        # So we set pythonpath (used later) to import from all
        # `pythonX.Y/site-packages/` and `pythonX.Y/dist-packages` directories
        # within `root_prefix`:
        #
        pv = platform.python_version().split('.')
        pv = f'python{pv[0]}.{pv[1]}'
        pythonpath = list()
        for dirpath, dirnames, filenames in os.walk(root_prefix):
            if os.path.basename(dirpath) == pv:
                for leaf in 'site-packages', 'dist-packages':
                    if leaf in dirnames:
                        pythonpath.append(os.path.join(dirpath, leaf))
        pythonpath = ':'.join(pythonpath)
        print(f'{pythonpath=}')
    else:
        command = f'{env} pip install -vv --root {root} {os.path.abspath(pymupdf_dir)}'
        run( command)
        sys.path.insert(0, pymupdf_dir)
        import pipcl
        del sys.path[0]
        pythonpath = pipcl.install_dir(root)
    
    # Show contents of installation directory. This is very slow on github,
    # where /usr/local contains lots of things.
    #run(f'find {root_prefix}|sort')
        
    # Run pytest tests.
    #
    print('## Run PyMuPDF pytest tests.')
    def run(command):
        return run_command(command, doit=pytest_do)
    import gh_release
    if pip == 'venv':
        # Create venv.
        run(f'{sys.executable} -m venv {test_venv}')
        # Install required packages.
        command = f'. {test_venv}/bin/activate'
        command += f' && pip install --upgrade pip'
        command += f' && pip install --upgrade {gh_release.test_packages}'
        run(command)
    elif pip == 'sudo':
        run(f'sudo pip install --upgrade {gh_release.test_packages}')
    else:
        log(f'Not installing packages for testing because {pip=}.')
    # Run pytest.
    #
    # We need to set PYTHONPATH and LD_LIBRARY_PATH. In particular we
    # use pipcl.install_dir() to find where pipcl will have installed
    # PyMuPDF.
    command = ''
    if pip == 'venv':
        command += f'. {test_venv}/bin/activate &&'
    command += f' LD_LIBRARY_PATH={root_prefix}/lib PYTHONPATH={pythonpath} PATH=$PATH:{root_prefix}/bin'
    run(f'ls -l {root_prefix}/bin/')
    # 2024-03-20: Not sure whether/where `pymupdf` binary is installed, so we
    # disable the test_cli* tests.
    command += f' {pymupdf_dir}/scripts/test.py'
    command += f' -v 0'
    if pytest_name is None:
        excluded_tests = (
                'test_color_count',
                'test_3050',
                'test_cli',
                'test_cli_out',
                'test_pylint',
                'test_textbox3',
                'test_3493',
                )
        excluded_tests = ' and not '.join(excluded_tests)
        if not pytest_args:
            pytest_args = ''
        pytest_args += f' -k \'not {excluded_tests}\''
    else:
        command += f' -t {pytest_name}'
    if test_fitz:
        command += f' -f {test_fitz}'
    if test_implementations:
        command += f' -i {test_implementations}'
    if pytest_args:
        command += f' -p {shlex.quote(pytest_args)}'
    if pytest_do:
        command += ' test'
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
