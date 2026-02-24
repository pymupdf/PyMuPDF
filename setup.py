#! /usr/bin/env python3

'''
Overview:

    Build script for PyMuPDF, supporting PEP-517 and simple command-line usage.

    We hard-code the URL of the MuPDF .tar.gz file that we require. This
    generally points to a particular source release on mupdf.com.

    Default behaviour:

        Building an sdist:
            As of 2024-002-28 we no longer download the MuPDF .tar.gz file and
            embed it within the sdist. Instead it will be downloaded at build
            time.

        Building PyMuPDF:
            We first download the hard-coded mupdf .tar.gz file.

            Then we extract and build MuPDF locally, before building PyMuPDF
            itself. So PyMuPDF will always be built with the exact MuPDF
            release that we require.


Environmental variables:

    If building with system MuPDF (PYMUPDF_SETUP_MUPDF_BUILD is empty string):
    
        CFLAGS
        CXXFLAGS
        LDFLAGS
            Added to c, c++, and link commands.
        
        PYMUPDF_INCLUDES
            Colon-separated extra include paths.
        
        PYMUPDF_MUPDF_LIB
            Directory containing MuPDF libraries, (libmupdf.so,
            libmupdfcpp.so).
    
    PIPCL_SHOW_ENV
        If '0', we do not show environment variables on startup.
    
    PYMUPDF_SETUP_DEVENV
        Location of devenv.com on Windows. If unset we search for it - see
        wdev.py. if that fails we use just 'devenv.com'.

    PYMUPDF_SETUP_DUMMY
        If 1, we build dummy sdist and wheel with no files.
    
    PYMUPDF_SETUP_FLAVOUR
        Control building of separate wheels for PyMuPDF.
        
        Must be unset or a combination of 'p', 'b' and 'd'.
        
        Default is 'pbd'.
        
        'p':
            Generated wheel contains PyMuPDF code.
        'b':
            Generated wheel contains MuPDF libraries; these are independent of
            the Python version.
        'd':
            Generated wheel contains includes and libraries for MuPDF.
        
        If 'p' is included, the generated wheel is called PyMuPDF.
        Otherwise if 'b' is included the generated wheel is called PyMuPDFb.
        Otherwise if 'd' is included the generated wheel is called PyMuPDFd.
        
        For example:
        
            'pb': a `PyMuPDF` wheel with PyMuPDF runtime files and MuPDF
            runtime shared libraries.
            
            'b': a `PyMuPDFb` wheel containing MuPDF runtime shared libraries.
            
            'pbd' a `PyMuPDF` wheel with PyMuPDF runtime files and MuPDF
            runtime shared libraries, plus MuPDF build-time files (includes,
            *.lib files on Windows).
            
            'd': a `PyMuPDFd` wheel containing MuPDF build-time files
            (includes, *.lib files on Windows).
    
    PYMUPDF_SETUP_LIBCLANG
        For internal testing.
        
    PYMUPDF_SETUP_MUPDF_BUILD
        If unset or '-', use internal hard-coded default MuPDF location.
        Otherwise overrides location of MuPDF when building PyMuPDF:
            Empty string:
                Build PyMuPDF with the system MuPDF.
            A string starting with 'git:':
                We use `git` commands to clone/update a local MuPDF checkout.
                Should match `git:[--branch <branch>][--tag <tag>][<remote>]`.
                If <remote> is omitted we use a default.
                For example:
                    PYMUPDF_SETUP_MUPDF_BUILD="git:--branch master"
                Passed as <text> arg to pipcl.git_get().
            Otherwise:
                Location of mupdf directory.
    
    PYMUPDF_SETUP_MUPDF_BSYMBOLIC
        If '0' we do not link libmupdf.so with -Bsymbolic.
    
    PYMUPDF_SETUP_MUPDF_TESSERACT
        If '0' we build MuPDF without Tesseract.
    
    PYMUPDF_SETUP_MUPDF_BUILD_TYPE
        Unix only. Controls build type of MuPDF. Supported values are:
            debug
            memento
            release (default)

    PYMUPDF_SETUP_MUPDF_CLEAN
        Unix only. If '1', we do a clean MuPDF build.

    PYMUPDF_SETUP_MUPDF_REFCHECK_IF
        Should be preprocessor statement to enable MuPDF reference count
        checking.
        
        As of 2024-09-27, MuPDF default is `#ifndef NDEBUG`.

    PYMUPDF_SETUP_MUPDF_TRACE_IF
        Should be preprocessor statement to enable MuPDF runtime diagnostics in
        response to environment variables such as MUPDF_trace.
        
        As of 2024-09-27, MuPDF default is `#ifndef NDEBUG`.

    PYMUPDF_SETUP_MUPDF_THIRD
        If '0' and we are building on Linux with the system MuPDF
        (i.e. PYMUPDF_SETUP_MUPDF_BUILD=''), then don't link with
        `-lmupdf-third`.
    
    PYMUPDF_SETUP_MUPDF_VS_UPGRADE
        If '1' we run mupdf `scripts/mupdfwrap.py` with `--vs-upgrade 1` to
        help Windows builds work with Visual Studio versions newer than 2019.

    PYMUPDF_SETUP_MUPDF_TGZ
        If set, overrides location of MuPDF .tar.gz file:
            Empty string:
                Do not download MuPDF .tar.gz file. Sdist's will not contain
                MuPDF.

            A string containing '://':
                The URL from which to download the MuPDF .tar.gz file. Leaf
                must match mupdf-*.tar.gz.

            Otherwise:
                The path of local mupdf git checkout. We put all files in this
                checkout known to git into a local tar archive.

    PYMUPDF_SETUP_MUPDF_OVERWRITE_CONFIG
        If '0' we do not overwrite MuPDF's include/mupdf/fitz/config.h with
        PyMuPDF's own configuration file, before building MuPDF.
    
    PYMUPDF_SETUP_MUPDF_REBUILD
        If 0 we do not (re)build mupdf.
    
    PYMUPDF_SETUP_PY_LIMITED_API
        If not '0', we build for current Python's stable ABI.
    
    PYMUPDF_SETUP_URL_WHEEL
        If set, we use an existing wheel instead of building a new wheel.
        
        If starts with `http://` or `https://`:
            If ends with '/', we append our wheel name and download. Otherwise
            we download directly.
        
        If starts with `file://`:
            If ends with '/' we look for a matching wheel name, `using
            pipcl.wheel_name_match()` to cope with differing platform tags,
            for example our `manylinux2014_x86_64` will match with an existing
            wheel with `manylinux2014_x86_64.manylinux_2_17_x86_64`.
        
        Any other prefix is an error.

    PYMUPDF_SETUP_SWIG
        If set, we use this instead of `swig`.
    
    WDEV_VS_YEAR
        If set, we use as Visual Studio year, for example '2019' or '2022'.

    WDEV_VS_GRADE
        If set, we use as Visual Studio grade, for example 'Community' or
        'Professional' or 'Enterprise'.
'''

import glob
import io
import os
import textwrap
import time
import platform
import re
import shlex
import shutil
import stat
import subprocess
import sys
import tarfile
import traceback
import urllib.request
import zipfile

import pipcl


log = pipcl.log0

run = pipcl.run


if 1:
    # For debugging.
    log(f'### Starting.')
    pipcl.show_system()


PYMUPDF_SETUP_FLAVOUR = os.environ.get( 'PYMUPDF_SETUP_FLAVOUR', 'pbd')
for i in PYMUPDF_SETUP_FLAVOUR:
    assert i in 'pbd', f'Unrecognised flag "{i} in {PYMUPDF_SETUP_FLAVOUR=}. Should be one of "p", "b", "d"'

g_root = os.path.abspath( f'{__file__}/..')

# Name of file that identifies that we are in a PyMuPDF sdist.
g_pymupdfb_sdist_marker = 'pymupdfb_sdist'

python_version_tuple = tuple(int(x) for x in platform.python_version_tuple()[:2])

PYMUPDF_SETUP_PY_LIMITED_API = os.environ.get('PYMUPDF_SETUP_PY_LIMITED_API')
assert PYMUPDF_SETUP_PY_LIMITED_API in (None, '', '0', '1'), \
        f'Should be "", "0", "1" or undefined: {PYMUPDF_SETUP_PY_LIMITED_API=}.'
g_py_limited_api = (PYMUPDF_SETUP_PY_LIMITED_API != '0')

PYMUPDF_SETUP_URL_WHEEL =  os.environ.get('PYMUPDF_SETUP_URL_WHEEL')
log(f'{PYMUPDF_SETUP_URL_WHEEL=}')

PYMUPDF_SETUP_DUMMY = os.environ.get('PYMUPDF_SETUP_DUMMY')
log(f'{PYMUPDF_SETUP_DUMMY=}')

PYMUPDF_SETUP_SWIG = os.environ.get('PYMUPDF_SETUP_SWIG')

def _fs_remove(path):
    '''
    Removes file or directory, without raising exception if it doesn't exist.

    We assert-fail if the path still exists when we return, in case of
    permission problems etc.
    '''
    # First try deleting `path` as a file.
    try:
        os.remove( path)
    except Exception as e:
        pass
    
    if os.path.exists(path):
        # Try deleting `path` as a directory. Need to use
        # shutil.rmtree() callback to handle permission problems; see:
        # https://docs.python.org/3/library/shutil.html#rmtree-example
        #
        def error_fn(fn, path, excinfo):
            # Clear the readonly bit and reattempt the removal.
            os.chmod(path, stat.S_IWRITE)
            fn(path)
        shutil.rmtree( path, onerror=error_fn)
    
    assert not os.path.exists( path)


def _git_get_branch( directory):
    command = f'cd {directory} && git branch --show-current'
    log( f'Running: {command}')
    p = subprocess.run(
            command,
            shell=True,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            )
    ret = None
    if p.returncode == 0:
        ret = p.stdout.strip()
        log( f'Have found MuPDF git branch: ret={ret!r}')
    return ret


def tar_check(path, mode='r:gz', prefix=None, remove=False):
    '''
    Checks items in tar file have same <top-directory>, or <prefix> if not None.

    We fail if items in tar file have different top-level directory names.

    path:
        The tar file.
    mode:
        As tarfile.open().
    prefix:
        If not None, we fail if tar file's <top-directory> is not <prefix>.
    
    Returns the directory name (which will be <prefix> if not None).
    '''
    with tarfile.open( path, mode) as t:
        items = t.getnames()
        assert items
        item = items[0]
        assert not item.startswith('./') and not item.startswith('../')
        s = item.find('/')
        if s == -1:
            prefix_actual = item + '/'
        else:
            prefix_actual = item[:s+1]
        if prefix:
            assert prefix == prefix_actual, f'{path=} {prefix=} {prefix_actual=}'
        for item in items[1:]:
            assert item.startswith( prefix_actual), f'prefix_actual={prefix_actual!r} != item={item!r}'
    return prefix_actual


def tar_extract(path, mode='r:gz', prefix=None, exists='raise'):
    '''
    Extracts tar file into single local directory.
    
    We fail if items in tar file have different <top-directory>.

    path:
        The tar file.
    mode:
        As tarfile.open().
    prefix:
        If not None, we fail if tar file's <top-directory> is not <prefix>.
    exists:
        What to do if <top-directory> already exists:
            'raise': raise exception.
            'remove': remove existing file/directory before extracting.
            'return': return without extracting.
    
    Returns the directory name (which will be <prefix> if not None, with '/'
    appended if not already present).
    '''
    prefix_actual = tar_check( path, mode, prefix)
    if os.path.exists( prefix_actual):
        if exists == 'raise':
            raise Exception( f'Path already exists: {prefix_actual!r}')
        elif exists == 'remove':
            remove( prefix_actual)
        elif exists == 'return':
            log( f'Not extracting {path} because already exists: {prefix_actual}')
            return prefix_actual
        else:
            assert 0, f'Unrecognised exists={exists!r}'
    assert not os.path.exists( prefix_actual), f'Path already exists: {prefix_actual}'
    log( f'Extracting {path}')
    with tarfile.open( path, mode) as t:
        t.extractall()
    return prefix_actual


def git_info( directory):
    '''
    Returns `(sha, comment, diff, branch)`, all items are str or None if not
    available.

    directory:
        Root of git checkout.
    '''
    sha, comment, diff, branch = '', '', '', ''
    cp = subprocess.run(
            f'cd {directory} && (PAGER= git show --pretty=oneline|head -n 1 && git diff)',
            capture_output=1,
            shell=1,
            text=1,
            )
    if cp.returncode == 0:
        sha, _ = cp.stdout.split(' ', 1)
        comment, diff = _.split('\n', 1)
    cp = subprocess.run(
            f'cd {directory} && git rev-parse --abbrev-ref HEAD',
            capture_output=1,
            shell=1,
            text=1,
            )
    if cp.returncode == 0:
        branch = cp.stdout.strip()
    log(f'git_info(): directory={directory!r} returning branch={branch!r} sha={sha!r} comment={comment!r}')
    return sha, comment, diff, branch


def git_patch(directory, patch, hard=False):
    '''
    Applies string <patch> with `git patch` in <directory>.
    
    If <hard> is true we clean the tree with `git checkout .` and then apply
    the patch.

    Otherwise we apply patch only if it is not already applied; this might fail
    if there are conflicting changes in the tree.
    '''
    log(f'Applying patch in {directory}:\n{textwrap.indent(patch, "    ")}')
    if not patch:
        return
    # Carriage returns break `git apply` so we use `newline='\n'` in open().
    path = os.path.abspath(f'{directory}/pymupdf_patch.txt')
    with open(path, 'w', newline='\n') as f:
        f.write(patch)
    log(f'Using patch file: {path}')
    if hard:
        run(f'cd {directory} && git checkout .')
        run(f'cd {directory} && git apply {path}')
        log(f'Have applied patch in {directory}.')
    else:
        e = run( f'cd {directory} && git apply --check --reverse {path}', check=0)
        if e == 0:
            log(f'Not patching {directory} because already patched.')
        else:
            run(f'cd {directory} && git apply {path}')
            log(f'Have applied patch in {directory}.')
    run(f'cd {directory} && git diff')


mupdf_tgz = os.path.abspath( f'{__file__}/../mupdf.tgz')

def get_mupdf_internal(out, location=None, local_tgz=None):
    '''
    Gets MuPDF as either a .tgz or a local directory.
    
    Args:
        out:
            Either 'dir' (we return name of local directory containing mupdf) or 'tgz' (we return
            name of local .tgz file containing mupdf).
        location:
            First, if None we set to hard-coded default URL or git location.
            If starts with 'git:', should be remote git location.
            Otherwise if containing '://' should be URL for .tgz.
            Otherwise should path of local mupdf checkout.
        local_tgz:
            If not None, must be local .tgz file.
    Returns:
        (path, location):
            `path` is absolute path of local directory or .tgz containing
            MuPDF, or None if we are to use system MuPDF.

            `location_out` is `location` if not None, else the hard-coded
            default location.
                
    '''
    log(f'get_mupdf_internal(): {out=} {location=}')
    assert out in ('dir', 'tgz')
    if location is None:
        location = f'https://mupdf.com/downloads/archive/mupdf-{version_mupdf}-source.tar.gz'
        #location = 'git:--branch master https://github.com/ArtifexSoftware/mupdf.git'
    
    if location == '':
        # Use system mupdf.
        return None, location
    
    local_dir = None
    if local_tgz:
        assert os.path.isfile(local_tgz)
    elif location.startswith( 'git:'):
        local_dir = 'mupdf-git'
        pipcl.git_get(local_dir, text=location, remote='https://github.com/ArtifexSoftware/mupdf.git')
        
        # Show sha of checkout.
        run(
                f'cd {local_dir} && git show --pretty=oneline|head -n 1',
                check = False,
                prefix = 'mupdf git id: ',
                )
    elif '://' in location:
        # Download .tgz.
        local_tgz = os.path.basename( location)
        suffix = '.tar.gz'
        assert location.endswith(suffix), f'Unrecognised suffix in remote URL {location=}.'
        name = local_tgz[:-len(suffix)]
        log( f'Download {location=} {local_tgz=} {name=}')
        if os.path.exists(local_tgz):
            try:
                tar_check(local_tgz, 'r:gz', prefix=f'{name}/')
            except Exception as e:
                log(f'Not using existing file {local_tgz} because invalid tar data: {e}')
                _fs_remove( local_tgz)
        if os.path.exists(local_tgz):
            log(f'Not downloading from {location} because already present: {local_tgz!r}')
        else:
            log(f'Downloading from {location=} to {local_tgz=}.')
            urllib.request.urlretrieve( location, local_tgz + '-')
            os.rename(local_tgz + '-', local_tgz)
            assert os.path.exists( local_tgz)
            tar_check( local_tgz, 'r:gz', prefix=f'{name}/')
    else:
        assert os.path.isdir(location), f'Local MuPDF does not exist: {location=}'
        local_dir = location
    
    assert bool(local_dir) != bool(local_tgz)
    if out == 'dir':
        if not local_dir:
            assert local_tgz
            local_dir = tar_extract( local_tgz, exists='return')
        return os.path.abspath( local_dir), location
    elif out == 'tgz':
        if not local_tgz:
            # Create .tgz containing git files in `local_dir`.
            assert local_dir
            if local_dir.endswith( '/'):
                local_dir = local_dir[:-1]
            top = os.path.basename(local_dir)
            local_tgz = f'{local_dir}.tgz'
            log( f'Creating .tgz from git files. {top=} {local_dir=} {local_tgz=}')
            _fs_remove( local_tgz)
            with tarfile.open( local_tgz, 'w:gz') as f:
                for name in pipcl.git_items( local_dir, submodules=True):
                    path = os.path.join( local_dir, name)
                    if os.path.isfile( path):
                        path2 = f'{top}/{name}'
                        log(f'Adding {path=} {path2=}.')
                        f.add( path, path2, recursive=False)
        return os.path.abspath( local_tgz), location
    else:
        assert 0, f'Unrecognised {out=}'
            
        

def get_mupdf_tgz():
    '''
    Creates .tgz file called containing MuPDF source, for inclusion in an
    sdist.
    
    What we do depends on environmental variable PYMUPDF_SETUP_MUPDF_TGZ; see
    docs at start of this file for details.

    Returns name of top-level directory within the .tgz file.
    '''
    name, location = get_mupdf_internal( 'tgz', os.environ.get('PYMUPDF_SETUP_MUPDF_TGZ'))
    return name, location


def get_mupdf(path=None, sha=None):
    '''
    Downloads and/or extracts mupdf and returns (path, location) where `path`
    is the local mupdf directory and `location` is where it came from.

    Exact behaviour depends on environmental variable
    PYMUPDF_SETUP_MUPDF_BUILD; see docs at start of this file for details.
    '''
    m = os.environ.get('PYMUPDF_SETUP_MUPDF_BUILD')
    if m == '-':
        # This allows easy specification in Github actions.
        m = None
    if m is None and os.path.isfile(mupdf_tgz):
        # This makes us use tgz inside sdist.
        log(f'Using local tgz: {mupdf_tgz=}')
        return get_mupdf_internal('dir', local_tgz=mupdf_tgz)
    return get_mupdf_internal('dir', m)


linux = sys.platform.startswith( 'linux') or 'gnu' in sys.platform
openbsd = sys.platform.startswith( 'openbsd')
freebsd = sys.platform.startswith( 'freebsd')
darwin = sys.platform.startswith( 'darwin')
windows = platform.system() == 'Windows' or platform.system().startswith('CYGWIN')
msys2 = platform.system().startswith('MSYS_NT-')

if os.environ.get('PYODIDE') == '1':
    if os.environ.get('OS') != 'pyodide':
        log('PYODIDE=1, setting OS=pyodide.')
        os.environ['OS'] = 'pyodide'

pyodide = os.environ.get('OS') == 'pyodide'

def build():
    '''
    pipcl.py `build_fn()` callback.
    '''
    #pipcl.show_sysconfig()
    
    if PYMUPDF_SETUP_DUMMY == '1':
        log(f'{PYMUPDF_SETUP_DUMMY=} Building dummy wheel with no files.')
        return list()
    
    # Download MuPDF.
    #
    mupdf_local, mupdf_location = get_mupdf()
    if mupdf_local:
        mupdf_version_tuple = get_mupdf_version(mupdf_local)
    # else we cannot determine version this way and do not use it

    build_type = os.environ.get( 'PYMUPDF_SETUP_MUPDF_BUILD_TYPE', 'release')
    assert build_type in ('debug', 'memento', 'release'), \
            f'Unrecognised build_type={build_type!r}'
    
    overwrite_config = os.environ.get('PYMUPDF_SETUP_MUPDF_OVERWRITE_CONFIG', '1') == '1'
    
    PYMUPDF_SETUP_MUPDF_REFCHECK_IF = os.environ.get('PYMUPDF_SETUP_MUPDF_REFCHECK_IF')
    PYMUPDF_SETUP_MUPDF_TRACE_IF = os.environ.get('PYMUPDF_SETUP_MUPDF_TRACE_IF')
    
    # Build MuPDF shared libraries.
    #
    if windows:
        mupdf_build_dir = build_mupdf_windows(
                mupdf_local,
                build_type,
                overwrite_config,
                g_py_limited_api,
                PYMUPDF_SETUP_MUPDF_REFCHECK_IF,
                PYMUPDF_SETUP_MUPDF_TRACE_IF,
                )
    else:
        if 'p' not in PYMUPDF_SETUP_FLAVOUR and 'b' not in PYMUPDF_SETUP_FLAVOUR:
            # We only need MuPDF headers, so no point building MuPDF.
            log(f'Not building MuPDF because not Windows and {PYMUPDF_SETUP_FLAVOUR=}.')
            mupdf_build_dir = None
        else:
            mupdf_build_dir = build_mupdf_unix(
                    mupdf_local,
                    build_type,
                    overwrite_config,
                    g_py_limited_api,
                    PYMUPDF_SETUP_MUPDF_REFCHECK_IF,
                    PYMUPDF_SETUP_MUPDF_TRACE_IF,
                    PYMUPDF_SETUP_SWIG,
                    )
    log( f'build(): mupdf_build_dir={mupdf_build_dir!r}')
    
    # Build `extra` module.
    #
    if 'p' in PYMUPDF_SETUP_FLAVOUR:
        path_so_leaf = _build_extension(
                mupdf_local,
                mupdf_build_dir,
                build_type,
                g_py_limited_api,
                )
    else:
        log(f'Not building extension.')
        path_so_leaf = None
    
    # Generate list of (from, to) items to return to pipcl. What we add depends
    # on PYMUPDF_SETUP_FLAVOUR.
    #
    ret = list()    
    def add(flavour, from_, to_):
        assert flavour in 'pbd'
        if flavour in PYMUPDF_SETUP_FLAVOUR:
            ret.append((from_, to_))
    
    to_dir = 'pymupdf/'
    to_dir_d = f'{to_dir}/mupdf-devel'
    
    # Add implementation files.
    add('p', f'{g_root}/src/__init__.py', to_dir)
    add('p', f'{g_root}/src/__main__.py', to_dir)
    add('p', f'{g_root}/src/pymupdf.py', to_dir)
    add('p', f'{g_root}/src/table.py', to_dir)
    add('p', f'{g_root}/src/utils.py', to_dir)
    add('p', f'{g_root}/src/_wxcolors.py', to_dir)
    add('p', f'{g_root}/src/_apply_pages.py', to_dir)
    add('p', f'{g_root}/src/build/extra.py', to_dir)
    add('p', b'', f'{to_dir}/py.typed')
    if path_so_leaf:
        add('p', f'{g_root}/src/build/{path_so_leaf}', to_dir)

    # Add support for `fitz` backwards compatibility.
    add('p', f'{g_root}/src/fitz___init__.py', 'fitz/__init__.py')
    add('p', f'{g_root}/src/fitz_table.py', 'fitz/table.py')
    add('p', f'{g_root}/src/fitz_utils.py', 'fitz/utils.py')

    if mupdf_local:
        # Add MuPDF Python API.
        add('p', f'{mupdf_build_dir}/mupdf.py', to_dir)

        # Add MuPDF shared libraries.
        if windows:
            wp = pipcl.wdev.WindowsPython()
            add('p', f'{mupdf_build_dir}/_mupdf.pyd', to_dir)
            add('b', f'{mupdf_build_dir}/mupdfcpp{wp.cpu.windows_suffix}.dll', to_dir)

            # Add Windows .lib files.
            mupdf_build_dir2 = _windows_lib_directory(mupdf_local, build_type)
            add('d', f'{mupdf_build_dir2}/mupdfcpp{wp.cpu.windows_suffix}.lib', f'{to_dir_d}/lib/')
            # MuPDF-1.25+ language bindings build also builds libmuthreads.
            add('d', f'{mupdf_build_dir2}/libmuthreads.lib', f'{to_dir_d}/lib/')
        elif darwin:
            add('p', f'{mupdf_build_dir}/_mupdf.so', to_dir)
            add('b', f'{mupdf_build_dir}/libmupdfcpp.so', to_dir)
            add('b', f'{mupdf_build_dir}/libmupdf.dylib', to_dir)
            add('d', f'{mupdf_build_dir}/libmupdf-threads.a', f'{to_dir_d}/lib/')
        elif pyodide:
            add('p', f'{mupdf_build_dir}/_mupdf.so', to_dir)
            add('b', f'{mupdf_build_dir}/libmupdfcpp.so', to_dir)
            add('b', f'{mupdf_build_dir}/libmupdf.so', to_dir)
        else:
            add('p', f'{mupdf_build_dir}/_mupdf.so', to_dir)
            add('b', pipcl.get_soname(f'{mupdf_build_dir}/libmupdfcpp.so'), to_dir)
            add('b', pipcl.get_soname(f'{mupdf_build_dir}/libmupdf.so'), to_dir)
            add('d', f'{mupdf_build_dir}/libmupdf-threads.a', f'{to_dir_d}/lib/')

        if 'd' in PYMUPDF_SETUP_FLAVOUR:
            # Add MuPDF C and C++ headers to `ret_d`. Would prefer to use
            # pipcl.git_items() but hard-coded mupdf tree is not a git
            # checkout.
            #
            for root in (
                    f'{mupdf_local}/include',
                    f'{mupdf_local}/platform/c++/include',
                    ):
                for dirpath, dirnames, filenames in os.walk(root):
                    for filename in filenames:
                        if not filename.endswith('.h'):
                            continue
                        header_abs = os.path.join(dirpath, filename)
                        assert header_abs.startswith(root)
                        header_rel = header_abs[len(root)+1:]
                        add('d', f'{header_abs}', f'{to_dir_d}/include/{header_rel}')
    
    # Add a .py file containing location of MuPDF.
    try:
        sha, comment, diff, branch = git_info(g_root)
    except Exception as e:
        log(f'Failed to get git information: {e}')
        sha, comment, diff, branch = (None, None, None, None)
    swig = PYMUPDF_SETUP_SWIG or 'swig'
    swig_version_text = run(f'{swig} -version', capture=1)
    m = re.search('\nSWIG Version ([^\n]+)', swig_version_text)
    log(f'{swig_version_text=}')
    assert m, f'Unrecognised {swig_version_text=}'
    swig_version = m.group(1)
    def int_or_0(text):
        try:
            return int(text)
        except Exception:
            return 0
    swig_version_tuple = tuple(int_or_0(i) for i in swig_version.split('.'))
    version_p_tuple = tuple(int_or_0(i) for i in version_p.split('.'))
    log(f'{swig_version=}')
    text = ''
    text += f'mupdf_location = {mupdf_location!r}\n'
    text += f'pymupdf_version = {version_p!r}\n'
    text += f'pymupdf_version_tuple = {version_p_tuple!r}\n'
    text += f'pymupdf_git_sha = {sha!r}\n'
    text += f'pymupdf_git_diff = {diff!r}\n'
    text += f'pymupdf_git_branch = {branch!r}\n'
    text += f'swig_version = {swig_version!r}\n'
    text += f'swig_version_tuple = {swig_version_tuple!r}\n'
    log(f'_build.py is:\n{textwrap.indent(text, "    ")}')
    add('p', text.encode(), f'{to_dir}/_build.py')
    
    # Add single README file.
    if 'p' in PYMUPDF_SETUP_FLAVOUR:
        add('p', f'{g_root}/README.md', '$dist-info/README.md')
    elif 'b' in PYMUPDF_SETUP_FLAVOUR:
        add('b', f'{g_root}/READMEb.md', '$dist-info/README.md')
    elif 'd' in PYMUPDF_SETUP_FLAVOUR:
        add('d', f'{g_root}/READMEd.md', '$dist-info/README.md')
    
    return ret


def env_add(env, name, value, sep=' ', prepend=False, verbose=False):
    '''
    Appends/prepends `<value>` to `env[name]`.
    
    If `name` is not in `env`, we use os.environ[name] if it exists.
    '''
    v = env.get(name)
    if verbose:
        log(f'Initally: {name}={v!r}')
    if v is None:
        v = os.environ.get(name)
    if v is None:
        env[ name] = value
    else:
        if prepend:
            env[ name] =  f'{value}{sep}{v}'
        else:
            env[ name] =  f'{v}{sep}{value}'
    if verbose:
        log(f'Returning with {name}={env[name]!r}')


def build_mupdf_windows(
        mupdf_local,
        build_type,
        overwrite_config,
        g_py_limited_api,
        PYMUPDF_SETUP_MUPDF_REFCHECK_IF,
        PYMUPDF_SETUP_MUPDF_TRACE_IF,
        ):
    
    assert mupdf_local
    mupdf_version_tuple = get_mupdf_version(mupdf_local)
    log(f'{overwrite_config=}')
    log(f'{mupdf_version_tuple=}')
    wp = pipcl.wdev.WindowsPython()
    tesseract = '' if os.environ.get('PYMUPDF_SETUP_MUPDF_TESSERACT') == '0' else 'tesseract-'
    windows_build_tail = f'build\\shared-{tesseract}{build_type}'
    
    if overwrite_config:
        if mupdf_version_tuple >= (1, 28):
            # Tell mupdf build to use, for example, `/Build "ReleaseTofuCjkExt|x64"`.
            # This avoids the need for us to modify mupdf's config.h.
            windows_build_tail += '-TOFU_CJK_EXT'
            log(f'Appending, {windows_build_tail=}')
        else:
            log(f'modifying mupdf:include/mupdf/fitz/config.h')
            mupdf_config_h = f'{mupdf_local}/include/mupdf/fitz/config.h'
            prefix = '#define TOFU_CJK_EXT 1 /* PyMuPDF override. */\n'
            with open(mupdf_config_h) as f:
                text = f.read()
            if text.startswith(prefix):
                log(f'Not modifying {mupdf_config_h} because already has prefix {prefix!r}.')
            else:
                log(f'Prefixing {mupdf_config_h} with {prefix!r}.')
                text = prefix + text
                st = os.stat(mupdf_config_h)
                with open(mupdf_config_h, 'w') as f:
                    f.write(text)
                os.utime(mupdf_config_h, (st.st_atime, st.st_mtime))
    
    if g_py_limited_api:
        windows_build_tail += f'-Py_LIMITED_API_{pipcl.current_py_limited_api()}'
    windows_build_tail += f'-x{wp.cpu.bits}-py{wp.version}'
    windows_build_dir = f'{mupdf_local}\\{windows_build_tail}'
    #log( f'Building mupdf.')
    devenv = os.environ.get('PYMUPDF_SETUP_DEVENV')
    if not devenv:
        try:
            # Prefer VS-2022 as that is what Github provide in windows-2022.
            log(f'Looking for Visual Studio 2022.')
            vs = pipcl.wdev.WindowsVS(year=2022)
        except Exception as e:
            log(f'Failed to find VS-2022:\n'
                    f'{textwrap.indent(traceback.format_exc(), "    ")}'
                    )
            log(f'Looking for any Visual Studio.')
            vs = pipcl.wdev.WindowsVS()
        log(f'vs:\n{vs.description_ml("    ")}')
        devenv = vs.devenv
    if not devenv:
        devenv = 'devenv.com'
        log( f'Cannot find devenv.com in default locations, using: {devenv!r}')
    command = f'cd "{mupdf_local}" && "{sys.executable}" ./scripts/mupdfwrap.py'
    if os.environ.get('PYMUPDF_SETUP_MUPDF_VS_UPGRADE') == '1':
        command += ' --vs-upgrade 1'
        
    # Would like to simply do f'... --devenv {shutil.quote(devenv)}', but
    # it looks like if `devenv` has spaces then `shutil.quote()` puts it
    # inside single quotes, which then appear to be ignored when run by
    # subprocess.run().
    #
    # So instead we strip any enclosing quotes and the enclose with
    # double-quotes.
    #
    if len(devenv) >= 2:
        for q in '"', "'":
            if devenv.startswith( q) and devenv.endswith( q):
                devenv = devenv[1:-1]
    command += f' -d {windows_build_tail}'
    command += f' -b'
    if PYMUPDF_SETUP_MUPDF_REFCHECK_IF:
        command += f' --refcheck-if "{PYMUPDF_SETUP_MUPDF_REFCHECK_IF}"'
    if PYMUPDF_SETUP_MUPDF_TRACE_IF:
        command += f' --trace-if "{PYMUPDF_SETUP_MUPDF_TRACE_IF}"'
    command += f' --devenv "{devenv}"'
    command += f' all'
    if os.environ.get( 'PYMUPDF_SETUP_MUPDF_REBUILD') == '0':
        log( f'PYMUPDF_SETUP_MUPDF_REBUILD is "0" so not building MuPDF; would have run: {command}')
    else:
        log( f'Building MuPDF by running: {command}')
        subprocess.run( command, shell=True, check=True)
        log( f'Finished building mupdf.')
    
    return windows_build_dir


def _windows_lib_directory(mupdf_local, build_type):
    ret = f'{mupdf_local}/platform/win32/'
    if _cpu_bits() == 64:
        ret += 'x64/'
    if build_type == 'release':
        ret += 'Release/'
    elif build_type == 'debug':
        ret += 'Debug/'
    else:
        assert 0, f'Unrecognised {build_type=}.'
    return ret


def _cpu_bits():
    if sys.maxsize == 2**31 - 1:
        return 32
    return 64


def build_mupdf_unix(
        mupdf_local,
        build_type,
        overwrite_config,
        g_py_limited_api,
        PYMUPDF_SETUP_MUPDF_REFCHECK_IF,
        PYMUPDF_SETUP_MUPDF_TRACE_IF,
        PYMUPDF_SETUP_SWIG,
        ):
    '''
    Builds MuPDF.

    Args:
        mupdf_local:
            Path of MuPDF directory or None if we are using system MuPDF.
    
    Returns the absolute path of build directory within MuPDF, e.g.
    `.../mupdf/build/pymupdf-shared-release`, or `None` if we are using the
    system MuPDF.
    '''    
    if not mupdf_local:
        log( f'Using system mupdf.')
        return None

    env = dict()
    if overwrite_config:
        # By predefining TOFU_CJK_EXT here, we don't need to modify
        # MuPDF's include/mupdf/fitz/config.h.
        log( f'Setting XCFLAGS and XCXXFLAGS to predefine TOFU_CJK_EXT.')
        env_add(env, 'XCFLAGS', '-DTOFU_CJK_EXT')
        env_add(env, 'XCXXFLAGS', '-DTOFU_CJK_EXT')

    if openbsd or freebsd:
        env_add(env, 'CXX', 'c++', ' ')
    
    if darwin and os.environ.get('GITHUB_ACTIONS') == 'true':
        if os.environ.get('ImageOS') == 'macos13':
            # On Github macos13 we need to use Clang/LLVM (Homebrew) 15.0.7,
            # otherwise mupdf:thirdparty/tesseract/src/api/baseapi.cpp fails to
            # compile with:
            #
            #   thirdparty/tesseract/src/api/baseapi.cpp:150:25: error: 'recursive_directory_iterator' is unavailable: introduced in macOS 10.15
            #
            # See:
            #   https://github.com/actions/runner-images/blob/main/images/macos/macos-13-Readme.md
            #
            log(f'Using llvm@15 clang and clang++')
            cl15 = pipcl.run(f'brew --prefix llvm@15', capture=1)
            log(f'{cl15=}')
            cl15 = cl15.strip()
            pipcl.run(f'ls -lL {cl15}')
            pipcl.run(f'ls -lL {cl15}/bin')
            cc = f'{cl15}/bin/clang'
            cxx = f'{cl15}/bin/clang++'
            env['CC'] = cc
            env['CXX'] = cxx
    
    # Show compiler versions.
    cc = env.get('CC', 'cc')
    cxx = env.get('CXX', 'c++')
    pipcl.run(f'{cc} --version')
    pipcl.run(f'{cxx} --version')

    # Add extra flags for MacOS cross-compilation, where ARCHFLAGS can be
    # '-arch arm64'.
    #
    archflags = os.environ.get( 'ARCHFLAGS')
    if archflags:
        env_add(env, 'XCFLAGS', archflags)
        env_add(env, 'XLIBS', archflags)

    mupdf_version_tuple = get_mupdf_version(mupdf_local)
    
    # We specify a build directory path containing 'pymupdf' so that we
    # coexist with non-PyMuPDF builds (because PyMuPDF builds have a
    # different config.h).
    #
    # We also append further text to try to allow different builds to
    # work if they reuse the mupdf directory.
    #
    # Using platform.machine() (e.g. 'amd64') ensures that different
    # builds of mupdf on a shared filesystem can coexist. Using
    # $_PYTHON_HOST_PLATFORM allows cross-compiled cibuildwheel builds
    # to coexist, e.g. on github.
    #
    # Have experimented with looking at getconf_ARG_MAX to decide whether to
    # omit `PyMuPDF-` from the build directory, to avoid command-too-long
    # errors with mupdf-1.26. But it seems that `getconf ARG_MAX` returns
    # a system limit, not the actual limit of the current shell, and there
    # doesn't seem to be a way to find the current shell's limit.
    #
    # Avoid link command length problems seen on musllinux.
    build_prefix = ''
    if pyodide:
        build_prefix += 'pyodide-'
    else:
        build_prefix += f'{platform.machine()}-'
    build_prefix_extra = os.environ.get( '_PYTHON_HOST_PLATFORM')
    if build_prefix_extra:
        build_prefix += f'{build_prefix_extra}-'
    build_prefix += 'shared-'
    if msys2:
        # Error in mupdf/scripts/tesseract/endianness.h:
        # #error "I don't know what architecture this is!"
        log(f'msys2: building MuPDF without tesseract.')
    elif os.environ.get('PYMUPDF_SETUP_MUPDF_TESSERACT') == '0':
        log(f'PYMUPDF_SETUP_MUPDF_TESSERACT=0 so building mupdf without tesseract.')
    else:
        build_prefix += 'tesseract-'
    if (
            linux
            and os.environ.get('PYMUPDF_SETUP_MUPDF_BSYMBOLIC', '1') == '1'
            ):
        log(f'Appending `bsymbolic-` to MuPDF build path.')
        build_prefix += 'bsymbolic-'
    log(f'{g_py_limited_api=}')
    if g_py_limited_api:
        build_prefix += f'Py_LIMITED_API_{pipcl.current_py_limited_api()}-'
    unix_build_dir = f'{mupdf_local}/build/{build_prefix}{build_type}'
    PYMUPDF_SETUP_MUPDF_CLEAN = os.environ.get('PYMUPDF_SETUP_MUPDF_CLEAN')
    if PYMUPDF_SETUP_MUPDF_CLEAN == '1':
        log(f'{PYMUPDF_SETUP_MUPDF_CLEAN=}, deleting {unix_build_dir=}.')
        shutil.rmtree(unix_build_dir, ignore_errors=1)
    # We need MuPDF's Python bindings, so we build MuPDF with
    # `mupdf/scripts/mupdfwrap.py` instead of running `make`.
    #
    command = f'cd {mupdf_local} &&'
    for n, v in env.items():
        command += f' {n}={shlex.quote(v)}'
    command += f' {sys.executable} ./scripts/mupdfwrap.py'
    if PYMUPDF_SETUP_SWIG:
        command += f' --swig {shlex.quote(PYMUPDF_SETUP_SWIG)}'
    command += f' -d build/{build_prefix}{build_type} -b'
    if sys.implementation.name == 'graalpy':
        # Force rerun of swig.
        pipcl.run(f'ls -l {mupdf_local}/platform/python/')
        for p in glob.glob(f'{mupdf_local}/platform/python/mupdfcpp*.i.cpp'):
            pipcl.log(f'Graal, deleting: {p!r}')
            pipcl.fs_remove(p)
    if PYMUPDF_SETUP_MUPDF_REFCHECK_IF:
        command += f' --refcheck-if "{PYMUPDF_SETUP_MUPDF_REFCHECK_IF}"'
    if PYMUPDF_SETUP_MUPDF_TRACE_IF:
        command += f' --trace-if "{PYMUPDF_SETUP_MUPDF_TRACE_IF}"'
    if 'p' in PYMUPDF_SETUP_FLAVOUR:
        command += ' all'
    else:
        command += ' m01'    # No need for C++/Python bindings.
    command += f' && echo {unix_build_dir}:'
    command += f' && ls -l {unix_build_dir}'

    if os.environ.get( 'PYMUPDF_SETUP_MUPDF_REBUILD') == '0':
        log( f'PYMUPDF_SETUP_MUPDF_REBUILD is "0" so not building MuPDF; would have run: {command}')
    else:
        log( f'Building MuPDF by running: {command}')
        subprocess.run( command, shell=True, check=True)
        log( f'Finished building mupdf.')
    
    return unix_build_dir


def get_mupdf_version(mupdf_dir):
    path = f'{mupdf_dir}/include/mupdf/fitz/version.h'
    with open(path) as f:
        text = f.read()
    v0 = re.search('#define FZ_VERSION_MAJOR ([0-9]+)', text)
    v1 = re.search('#define FZ_VERSION_MINOR ([0-9]+)', text)
    v2 = re.search('#define FZ_VERSION_PATCH ([0-9]+)', text)
    assert v0 and v1 and v2, f'Cannot find MuPDF version numbers in {path=}.'
    v0 = int(v0.group(1))
    v1 = int(v1.group(1))
    v2 = int(v2.group(1))
    return v0, v1, v2

def _fs_update(text, path):
    try:
        with open( path) as f:
            text0 = f.read()
    except OSError:
        text0 = None
    print(f'path={path!r} text==text0={text==text0!r}')
    if text != text0:
        with open( path, 'w') as f:
            f.write( text)
    

def _build_extension( mupdf_local, mupdf_build_dir, build_type, g_py_limited_api):
    '''
    Builds Python extension module `_extra`.

    Returns leafname of the generated shared libraries within mupdf_build_dir.
    '''
    (compiler_extra, linker_extra, includes, defines, optimise, debug, libpaths, libs, libraries) \
        = _extension_flags( mupdf_local, mupdf_build_dir, build_type)
    log(f'_build_extension(): {g_py_limited_api=} {defines=}')
    if mupdf_local:
        includes = (
                f'{mupdf_local}/platform/c++/include',
                f'{mupdf_local}/include',
                )
    
    log('Building PyMuPDF extension.')
    compile_extra_cpp = ''
    if darwin:
        # Avoids `error: cannot pass object of non-POD type
        # 'std::nullptr_t' through variadic function; call will abort at
        # runtime` when compiling `mupdf::pdf_dict_getl(..., nullptr)`.
        compile_extra_cpp += ' -Wno-non-pod-varargs'
        # Avoid errors caused by mupdf's C++ bindings' exception classes
        # not having `nothrow` to match the base exception class.
        compile_extra_cpp += ' -std=c++14'
    if windows:
        wp = pipcl.wdev.WindowsPython()
        libs = f'mupdfcpp{wp.cpu.windows_suffix}.lib'
    else:
        libs = ('mupdf', 'mupdfcpp')
        libraries = [
                f'{mupdf_build_dir}/libmupdf.so'
                f'{mupdf_build_dir}/libmupdfcpp.so'
                ]
    
    path_so_leaf = pipcl.build_extension(
            name = 'extra',
            path_i = f'{g_root}/src/extra.i',
            outdir = f'{g_root}/src/build',
            includes = includes,
            defines = defines,
            libpaths = libpaths,
            libs = libs,
            compiler_extra = compiler_extra + compile_extra_cpp,
            linker_extra = linker_extra,
            optimise = optimise,
            debug = debug,
            prerequisites_swig = None,
            prerequisites_compile = f'{mupdf_local}/include',
            prerequisites_link = libraries,
            py_limited_api = g_py_limited_api,
            swig = PYMUPDF_SETUP_SWIG,
            )
    
    return path_so_leaf


def _extension_flags( mupdf_local, mupdf_build_dir, build_type):
    '''
    Returns various flags to pass to pipcl.build_extension().
    '''
    compiler_extra = ''
    linker_extra = ''
    if build_type == 'memento':
        compiler_extra += ' -DMEMENTO'
    if mupdf_build_dir:
        mupdf_build_dir_flags = os.path.basename( mupdf_build_dir).split( '-')
    else:
        mupdf_build_dir_flags = [build_type]
    optimise = 'release' in mupdf_build_dir_flags
    debug = 'debug' in mupdf_build_dir_flags
    r_extra = ''
    defines = list()
    if windows:
        defines.append('FZ_DLL_CLIENT')
        wp = pipcl.wdev.WindowsPython()
        if os.environ.get('PYMUPDF_SETUP_MUPDF_VS_UPGRADE') == '1':
            # MuPDF C++ build uses a parallel build tree with updated VS files.
            infix = 'win32-vs-upgrade'
        else:
            infix = 'win32'
        build_type_infix = 'Debug' if debug else 'Release'
        libpaths = (
                f'{mupdf_local}\\platform\\{infix}\\{wp.cpu.windows_subdir}{build_type_infix}',
                f'{mupdf_local}\\platform\\{infix}\\{wp.cpu.windows_subdir}{build_type_infix}Tesseract',
                )
        libs = f'mupdfcpp{wp.cpu.windows_suffix}.lib'
        libraries = f'{mupdf_local}\\platform\\{infix}\\{wp.cpu.windows_subdir}{build_type_infix}\\{libs}'
        compiler_extra = ''
    else:
        libs = ['mupdf']
        compiler_extra += (
                ' -Wall'
                ' -Wno-deprecated-declarations'
                ' -Wno-unused-const-variable'
                )
        if mupdf_local:
            libpaths = (mupdf_build_dir,)
            libraries = f'{mupdf_build_dir}/{libs[0]}'
            if openbsd:
                compiler_extra += ' -Wno-deprecated-declarations'
        else:
            libpaths = os.environ.get('PYMUPDF_MUPDF_LIB')
            libraries = None
            if libpaths:
                libpaths = libpaths.split(':')
    
    if mupdf_local:
        includes = (
                f'{mupdf_local}/include',
                f'{mupdf_local}/include/mupdf',
                f'{mupdf_local}/thirdparty/freetype/include',
                )
    else:
        # Use system MuPDF.
        includes = list()
        pi = os.environ.get('PYMUPDF_INCLUDES')
        if pi:
            includes += pi.split(':')
        pmi = os.environ.get('PYMUPDF_MUPDF_INCLUDE')
        if pmi:
            includes.append(pmi)
        ldflags = os.environ.get('LDFLAGS')
        if ldflags:
            linker_extra += f' {ldflags}'
        cflags = os.environ.get('CFLAGS')
        if cflags:
            compiler_extra += f' {cflags}'
        cxxflags = os.environ.get('CXXFLAGS')
        if cxxflags:
            compiler_extra += f' {cxxflags}'

    return compiler_extra, linker_extra, includes, defines, optimise, debug, libpaths, libs, libraries, 


def clean(all_):
    pipcl.log(f'{all_=}')
    ret = list()
    ret.append(f'{g_root}/src/build')
    
    path_mupdf, _ = get_mupdf()
    
    # We remove mupdf directories directly with shutil.rmtree() instead of
    # returning them to pipcl, because pipcl will deliberately fail if asked to
    # remove things that are outside our checkout.
    shutil.rmtree(f'{path_mupdf}/platform/c++', ignore_errors=True)
    shutil.rmtree(f'{path_mupdf}/platform/python', ignore_errors=True)
    
    if all_:
        # Clean mupdf C library.
        shutil.rmtree(f'{path_mupdf}/build', ignore_errors=True)
        shutil.rmtree(f'{path_mupdf}/platform/win32', ignore_errors=True)
        shutil.rmtree(f'{path_mupdf}/platform/win32/Release', ignore_errors=True)
        shutil.rmtree(f'{path_mupdf}/platform/win32/x64', ignore_errors=True)
    
    pipcl.log(f'Returning: {ret=}')
    return ret


def sdist():
    ret = list()
    if PYMUPDF_SETUP_DUMMY == '1':
        return ret
    
    if PYMUPDF_SETUP_FLAVOUR == 'b':
        # Create a minimal sdist that will build/install a dummy PyMuPDFb.
        for p in (
                'setup.py',
                'pipcl.py',
                'wdev.py',
                'pyproject.toml',
                ):
            ret.append(p)
        ret.append(
                (
                    b'This file indicates that we are a PyMuPDFb sdist and should build/install a dummy PyMuPDFb package.\n',
                    g_pymupdfb_sdist_marker,
                    )
                )
        return ret
        
    for p in pipcl.git_items( g_root):
        if p.startswith(
                (
                    'docs/',
                    'signatures/',
                    '.',
                )
                ):
            pass
        else:
            ret.append(p)
    if 0:
        tgz, mupdf_location = get_mupdf_tgz()
        if tgz:
            ret.append((tgz, mupdf_tgz))
    else:
        log(f'Not including MuPDF .tgz in sdist.')
    return ret


classifier = [
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Operating System :: MacOS',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: C',
        'Programming Language :: C++',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Utilities',
        'Topic :: Multimedia :: Graphics',
        'Topic :: Software Development :: Libraries',
        ]

# We generate different wheels depending on PYMUPDF_SETUP_FLAVOUR.
#

# PyMuPDF version.
version_p = '1.27.1'

version_mupdf = '1.27.1'

# PyMuPDFb version. This is the PyMuPDF version whose PyMuPDFb wheels we will
# (re)use if generating separate PyMuPDFb wheels. Though as of PyMuPDF-1.24.11
# (2024-10-03) we no longer use PyMuPDFb wheels so this is actually unused.
#
version_b = '1.26.3'

if os.path.exists(f'{g_root}/{g_pymupdfb_sdist_marker}'):
    
    # We are in a PyMuPDFb sdist. We specify a dummy package so that pip builds
    # from sdists work - pip's build using PyMuPDF's sdist will already create
    # the required binaries, but pip will still see `requires_dist` set to
    # 'PyMuPDFb', so will also download and build PyMuPDFb's sdist.
    #
    log(f'Specifying dummy PyMuPDFb wheel.')
    
    def get_requires_for_build_wheel(config_settings=None):
        return list()
    
    p = pipcl.Package(
            'PyMuPDFb',
            version_b,
            summary = 'Dummy PyMuPDFb wheel',
            description = '',
            author = 'Artifex',
            author_email = 'support@artifex.com',
            license = 'GNU AFFERO GPL 3.0',
            tag_python = 'py3',
            )

else:
    # A normal PyMuPDF package.
    
    with open( f'{g_root}/README.md', encoding='utf-8') as f:
        readme_p = f.read()

    with open( f'{g_root}/READMEb.md', encoding='utf-8') as f:
        readme_b = f.read()

    with open( f'{g_root}/READMEd.md', encoding='utf-8') as f:
        readme_d = f.read()

    tag_python = None
    requires_dist = list()
    entry_points = None
    
    if 'p' in PYMUPDF_SETUP_FLAVOUR:
        version = version_p
        name = 'PyMuPDF'
        readme = readme_p
        summary = 'A high performance Python library for data extraction, analysis, conversion & manipulation of PDF (and other) documents.'
        if 'b' not in PYMUPDF_SETUP_FLAVOUR:
            requires_dist.append(f'PyMuPDFb =={version_b}')
        # Create a `pymupdf` command.
        entry_points = textwrap.dedent('''
                [console_scripts]
                pymupdf = pymupdf.__main__:main
                ''')
    elif 'b' in PYMUPDF_SETUP_FLAVOUR:
        version = version_b
        name = 'PyMuPDFb'
        readme = readme_b
        summary = 'MuPDF shared libraries for PyMuPDF.'
        tag_python = 'py3'
    elif 'd' in PYMUPDF_SETUP_FLAVOUR:
        version = version_b
        name = 'PyMuPDFd'
        readme = readme_d
        summary = 'MuPDF build-time files for PyMuPDF.'
        tag_python = 'py3'
    else:
        assert 0, f'Unrecognised {PYMUPDF_SETUP_FLAVOUR=}.'
    
    if os.environ.get('PYODIDE_ROOT'):
        # We can't pip install pytest on pyodide, so specify it here.
        requires_dist.append('pytest')

    p = pipcl.Package(
            name,
            version,
            summary = summary,
            description = readme,
            description_content_type = 'text/markdown',
            classifier = classifier,
            author = 'Artifex',
            author_email = 'support@artifex.com',
            requires_dist = requires_dist,
            requires_python = '>=3.10',
            license = 'Dual Licensed - GNU AFFERO GPL 3.0 or Artifex Commercial License',
            project_url = [
                ('Documentation, https://pymupdf.readthedocs.io/'),
                ('Source, https://github.com/pymupdf/pymupdf'),
                ('Tracker, https://github.com/pymupdf/PyMuPDF/issues'),
                ('Changelog, https://pymupdf.readthedocs.io/en/latest/changes.html'),
                ],
        
            entry_points = entry_points,
        
            fn_build=build,
            fn_clean=clean,
            fn_sdist=sdist,
        
            tag_python=tag_python,
            py_limited_api=g_py_limited_api,

            # 30MB: 9 ZIP_DEFLATED
            # 28MB: 9 ZIP_BZIP2
            # 23MB: 9 ZIP_LZMA
            #wheel_compression = zipfile.ZIP_DEFLATED if (darwin or pyodide) else zipfile.ZIP_LZMA,
            wheel_compresslevel = 9,
            )

    def get_requires_for_build_wheel(config_settings=None):
        '''
        Adds to pyproject.toml:[build-system]:requires, allowing programmatic
        control over what packages we require.
        '''
        def platform_release_tuple():
            r = platform.release()
            r = r.split('.')
            r = tuple(int(i) for i in r)
            log(f'platform_release_tuple() returning {r=}.')
            return r
            
        ret = list()
        libclang = os.environ.get('PYMUPDF_SETUP_LIBCLANG')
        if libclang:
            print(f'Overriding to use {libclang=}.')
            ret.append(libclang)
        elif openbsd:
            print(f'OpenBSD: libclang not available via pip; assuming `pkg_add py3-llvm`.')
        elif darwin and platform_release_tuple() < (18,):
            # There are still of problems when building on old macos.
            ret.append('libclang==14.0.6')
        else:
            ret.append('libclang')
        if msys2:
            print(f'msys2: pip install of swig does not build; assuming `pacman -S swig`.')
        elif openbsd:
            print(f'OpenBSD: pip install of swig does not build; assuming `pkg_add swig`.')
        elif PYMUPDF_SETUP_SWIG:
            pass
        elif darwin or os.environ.get('PYODIDE_ROOT'):
            # 2025-10-27: new swig-4.4.0 fails badly at runtime on macos.
            # 2025-11-06: similar for pyodide.
            # 2026-02-24: Stil fails badly on macos with swig 4.4.1.
            ret.append('swig==4.3.1')
        else:
            ret.append('swig')
        return ret


if PYMUPDF_SETUP_URL_WHEEL:
    def build_wheel(
            wheel_directory,
            config_settings=None,
            metadata_directory=None,
            p=p,
            ):
        '''
        Instead of building wheel, we look for and copy a wheel from location
        specified by PYMUPDF_SETUP_URL_WHEEL.
        '''
        log(f'{PYMUPDF_SETUP_URL_WHEEL=}')
        log(f'{p.wheel_name()=}')
        url = PYMUPDF_SETUP_URL_WHEEL
        if url.startswith(('http://', 'https://')):
            leaf = p.wheel_name()
            out_path = f'{wheel_directory}{leaf}'
            out_path_temp = out_path + '-'
            if url.endswith('/'):
                url += leaf
            log(f'Downloading from {url=} to {out_path_temp=}.')
            urllib.request.urlretrieve(url, out_path_temp)
        elif url.startswith(f'file://'):
            in_path = url[len('file://'):]
            log(f'{in_path=}')
            if in_path.endswith('/'):
                # Look for matching wheel within this directory.
                wheels = glob.glob(f'{in_path}*.whl')
                log(f'{len(wheels)=}')
                for in_path in wheels:
                    log(f'{in_path=}')
                    leaf = os.path.basename(in_path)
                    if p.wheel_name_match(leaf):
                        log(f'Match: {in_path=}')
                        break
                else:
                    message = f'Cannot find matching for {p.wheel_name()=} in ({len(wheels)=}):\n'
                    wheels_text = ''
                    for wheel in wheels:
                        wheels_text += f'    {wheel}\n'
                    assert 0, f'Cannot find matching for {p.wheel_name()=} in:\n{wheels_text}'
            else:
                leaf = os.path.basename(in_path)
            out_path = os.path.join(wheel_directory, leaf)
            out_path_temp = out_path + '-'
            log(f'Copying from {in_path=} to {out_path_temp=}.')
            shutil.copy2(in_path, out_path_temp)
        else:
            assert 0, f'Unrecognised prefix in {PYMUPDF_SETUP_URL_WHEEL=}.'
        
        log(f'Renaming from:\n    {out_path_temp}\nto:\n    {out_path}.')
        os.rename(out_path_temp, out_path)
        return os.path.basename(out_path)
else:
    build_wheel = p.build_wheel

build_sdist = p.build_sdist


if __name__ == '__main__':
    p.handle_argv(sys.argv)
