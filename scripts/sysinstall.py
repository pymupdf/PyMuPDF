#! /usr/bin/env python3

'''
Test script for system install of mupdf and pymupdf.

Args:

    -h
    --help
        Show this help.
    
    -m <mupdf_location>.
        Set location of mupdf. Default is 'git:'.
        
        If <mupdf_location> starts with 'git:', we clone/fetch to local
        directory `sysinstall_mupdf/`.
            Examples:
                git:-b 1.28.x
                    Get branch 1.28.x.
                git:
                    Get branch master.
        Otherwise <mupdf_location> is assumed to be a local mupdf checkout.
    
    -p <pytest_flags>
        Additional flags to pass to pytest.

Notes:

* We terminate with an error if run in a venv,
  because this would cause mupdf to install its libraries in the wrong place within our test tree.
* We assume we are running on a Debian-based system.
* We run `sudo apt update` and `sudo apt install ...` commands.
* We create the following directories:
  * ./pymupdf_sysinstall_test_root/
  * ./pymupdf_sysinstall_test_mupdf/
  * ./pymupdf_sysinstall_test_venv/
'''


import multiprocessing
import os
import platform
import shutil
import subprocess
import sys


g_pymupdf_root = os.path.normpath(f'{__file__}/../..')


def log(text=''):
    print(text, flush=1)
   
    
def run(command, capture=False):
    log(f'Running: {command}')
    if capture:
        cp = subprocess.run(command, shell=1, check=1, stdout=subprocess.PIPE)
        return cp.stdout
    else:
        subprocess.run(command, shell=1, check=1)


def fs_remove(path):
    '''
    Removes file or directory, without raising exception if it doesn't exist.

    We assert-fail if the path still exists when we return, in case of
    permission problems etc.
    '''
    try:
        os.remove(path)
    except Exception:
        pass
    shutil.rmtree(path, ignore_errors=1)
    assert not os.path.exists(path), f'Path still exists after deletion: {path!r}.'


def git_get(local, **kwargs):
    '''
    Behaves like pipcl.git_get().

    But because we don't want to run sysinstall.py itself in a venv (because
    this messes up where mupdf installs its libraries), we internally create
    a separate venv in which we install pipcl and run some python code (in a
    child process) that calls pipcl.git_get().
    '''
    log()
    log(f'## Running pipcl.git_get() in venv.')
    venv = 'pymupdf_sysinstall_test_venv'
    run(f'{sys.executable} -m venv {venv}')
    kwargs2 = [f'{n} = {v!r}' for (n, v) in kwargs.items()]
    kwargs2_str = ', '.join(kwargs2)
    run(f'. {venv}/bin/activate && pip install pipcl && python -c "import pipcl; pipcl.git_get({local!r}, {kwargs2_str})"')
    return os.path.abspath(local)


def main():
    log('## Sysinstall testing.')
    
    if sys.prefix != sys.base_prefix:
        log(f'Error: we must not be run in a venv.')
        return 1
    
    mupdf_location = 'git:'
    pytest_flags = ''
    
    args = iter(sys.argv[1:])
    while 1:
        try:
            arg = next(args)
        except StopIteration:
            break
        if arg in ('-h', '--help'):
            print(__doc__)
            return
        elif arg == '-m':
            mupdf_location = next(args)
        elif arg == '-p':
            pytest_flags = next(args)
        else:
            assert 0, f'Unrecognised {arg=}.'
    
    assert mupdf_location, f'Need `-m <mupdf_location>'
    if mupdf_location.startswith('git:'):
        mupdf_dir = git_get(
                'pymupdf_sysinstall_test_mupdf',
                remote='https://github.com/ArtifexSoftware/mupdf.git',
                branch='master',
                text=mupdf_location,
                )
    else:
        mupdf_dir = mupdf_location
    
    install_root = os.path.abspath('pymupdf_sysinstall_test_root')
    install_prefix = '/usr/local'
    
    log()
    log('## Initial settings.')
    log(f'{mupdf_dir=}.')
    log(f'{install_root=}.')
    log(f'{install_prefix=}.')
    
    # Set environment variables so that <install_root> will be used when
    # importing python modules and loading shared libraries.
    #
    log()
    log('## Setting environment variables.')
    # We guess the site-packages and dist-packages directories that python will
    # use when mupdf installs python libraries and we use `pip install` to
    # install pymupdf.
    #
    python_version_str = '.'.join(platform.python_version_tuple()[:2])
    install_python_site_packages = f'{install_root}{install_prefix}/lib/python{python_version_str}/site-packages'
    install_python_dist_packages = f'{install_root}{install_prefix}/lib/python{python_version_str}/dist-packages'
    os.environ['LD_LIBRARY_PATH'] = f'{install_root}{install_prefix}/lib'
    os.environ['PATH'] = f'{install_root}{install_prefix}/bin' + os.pathsep + os.environ['PATH']
    os.environ['PYTHONPATH'] = install_python_site_packages + os.pathsep + install_python_dist_packages
    log(f'LD_LIBRARY_PATH={os.environ["LD_LIBRARY_PATH"]}')
    log(f'PATH={os.environ["PATH"]}')
    log(f'PYTHONPATH={os.environ["PYTHONPATH"]}')
    
    if 1:
        log()
        log(f'## Deleting any existing {install_root=}.')
        fs_remove(install_root)
    
    if 1:
        log()
        log('## Installing system packages required by MuPDF.')
        sys_packages = [
                'libfreetype-dev',
                'libgumbo-dev',
                'libharfbuzz-dev',
                'libjbig2dec-dev',
                'libjpeg-dev',
                'libleptonica-dev',
                'libopenjp2-7-dev',
                ]
        run(f'sudo apt update')
        run(f'sudo apt install {" ".join(sys_packages)}')
        # Ubuntu-22.04 has freeglut3-dev, not libglut-dev.
        run(f'sudo apt install libglut-dev | sudo apt install freeglut3-dev')
        run(f'sudo apt install libtesseract-dev')
    
    if 1:
        log()
        log('## Installing python packages.')
        run(f'{sys.executable} -m pip install --root {install_root} libclang swig')
    
    if 1:
        log()
        log('## Building and installing MuPDF.')
        run(f'cd {os.path.abspath(mupdf_dir)} && make'
                f' -j {multiprocessing.cpu_count()}'
                f' barcode=yes'
                f' build_prefix=system-libs-'
                f' prefix={install_prefix}'
                f' verbose=yes'
                f' DESTDIR={install_root}'
                f' HAVE_LEPTONICA=yes'
                f' HAVE_TESSERACT=yes'
                f' INSTALL_MODE=755'
                f' USE_SYSTEM_LIBS=yes'
                f' USE_SYSTEM_ZXINGCPP=no'  # Github Ubuntu's zxingcpp too old for mupdf.
                f' VENV_FLAG='
                f' install-shared-python'
                )
    
    if 1:
        log()
        log('## Building and installing PyMuPDF.')
        compile_flags = f'-I {install_root}{install_prefix}/include'
        link_flags = f'-L {install_root}{install_prefix}/lib'
        env = ''
        env += f'CFLAGS="{compile_flags}" '
        env += f'CXXFLAGS="{compile_flags}" '
        env += f'LDFLAGS="{link_flags}" '
        env += f'PYMUPDF_SETUP_MUPDF_BUILD= '   # Use system MuPDF.
        
        command = f'{env} pip install -v --target {install_python_dist_packages} {os.path.abspath(g_pymupdf_root)}'
        run( command)
    
    if 1:
        log()
        log('## Running tests.')
        run(f'pip install --root {install_root} pytest')
        run(
                f'PYMUPDF_TEST_USE_4LLM=0 '
                    f'PYMUPDF_TEST_USE_LAYOUT=0 '
                    f'PYMUPDF_SYSINSTALL_ROOT={install_root} '
                    f'pytest {pytest_flags} {g_pymupdf_root}/tests'
                )


if __name__ == '__main__':
    e = main()
    sys.exit(e)
