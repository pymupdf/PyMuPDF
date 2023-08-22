#! /usr/bin/env python3

'''
Overview:

    Build script for PyMuPDF.

    We hard-code the URL of the MuPDF .tar.gz file that we require. This
    generally points to a particular source release on mupdf.com.

    Default behaviour:

        Building an sdist:
            We download the MuPDF .tar.gz file and embed within the sdist.

        Building PyMuPDF:
            If we are not in an sdist we first download the mupdf .tar.gz file.

            Then we extract and build MuPDF locally, before setuptools builds
            PyMuPDF. So PyMuPDF will always be built with the exact MuPDF
            release that we require.

Environmental variables:

    PYMUPDF_SETUP_IMPLEMENTATIONS
        Must be one of 'a', 'b', 'ab'. If unset we use 'ab'.
        If contains 'a' we build original implementation.
        If contains 'b' we build rebased implementation.
    
    PYMUPDF_SETUP_DEVENV
        Location of devenv.com on Windows. If unset we search for it - see
        wdev.py. if that fails we use just 'devenv.com'.

    PYMUPDF_SETUP_FLAVOUR
        Control building of separate wheels for PyMuPDF.
        
        Must be unset or one of: 'pb', 'p', 'b'.
        
        'pb' or unset:
            Build complete wheel `PyMuPDF` with all Python and shared
            libraries.
        
        'p':
            Wheel `PyMuPDF` excludes all shared libraries that are not
            specific to a particular Python version - e.g. on Linux this
            will exclude `libmupdf.so` and `libmupdfcpp.so`.

            This wheel will require the corresponding PyMuPDFb wheel
            - `PyMuPDF-<version>.dist-info/METADATA` will contain
            `Requires-Dist: PyMuPDFb ==<version>`.
        
        'b':
            Build wheel called `PyMuPDFb` containing only shared libraries
            that are not specific to a particular Python version - e.g.
            on Linux this will be `libmupdf.so` and `libmupdfcpp.so`.
        
    PYMUPDF_SETUP_MUPDF_BUILD
        If set, overrides location of MuPDF when building PyMuPDF:
            Empty string:
                Build PyMuPDF with the system MuPDF.
            A string starting with 'git:':
                Use `git clone` to get a MuPDF checkout. We use the
                string in the git clone command; it must contain the git
                URL from which to clone, and can also contain other `git
                clone` args, for example:
                    PYMUPDF_SETUP_MUPDF_BUILD="git:--branch master https://github.com/ArtifexSoftware/mupdf.git"
            Otherwise:
                Location of mupdf directory.
    
    PYMUPDF_SETUP_MUPDF_BUILD_TYPE
        Unix only. Controls build type of MuPDF. Supported values are:
            debug
            memento
            release (default)

    PYMUPDF_SETUP_MUPDF_CLEAN
        Unix only. If '1', we do a clean MuPDF build.

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

    PYMUPDF_SETUP_REBUILD_GIT_DETAILS
        If '0' we do not rebuild if only fitz/helper-git-versions.i has
        changed.

    PYMUPDF_SETUP_SKELETON
        If '1' we build minimal wheel for testing.
    
    WDEV_VS_YEAR
        If set, we use as Visual Studio year, for example '2019' or '2022'.

    WDEV_VS_GRADE
        If set, we use as Visual Studio grade, for example 'Community' or
        'Professional' or 'Enterprise'.

Known build failures:
    Linux:
        *musllinux*.
    Windows:
        pp*:
            fitz_wrap.obj : error LNK2001: unresolved external symbol PyUnicode_DecodeRawUnicodeEscape

    When using cibuildwheel, one can avoid building these failing wheels with:
        CIBW_SKIP='*musllinux* pp*'
'''

import glob
import io
import os
import textwrap
import time
import platform
import shlex
import shutil
import stat
import subprocess
import sys
import tarfile
import urllib.request
import zipfile

import pipcl

_log_prefix = None
def log( text):
    global _log_prefix
    if not _log_prefix:
        p = os.path.abspath( __file__)
        p, p1 = os.path.split( p)
        p, p0 = os.path.split( p)
        _log_prefix = os.path.join( p0, p1)
    print(f'{_log_prefix}: {text}', file=sys.stdout)
    sys.stdout.flush()


if 1:
    # For debugging.
    log(f'### Starting.')
    log(f'__name__: {__name__!r}')
    log(f'platform.platform(): {platform.platform()!r}')
    log(f'platform.python_version(): {platform.python_version()!r}')
    log(f'sys.executable: {sys.executable!r}')
    log(f'CPU bits: {32 if sys.maxsize == 2**31 - 1 else 64} {sys.maxsize=}')
    log(f'__file__: {__file__!r}')
    log(f'os.getcwd(): {os.getcwd()!r}')
    log(f'sys.argv ({len(sys.argv)}):')
    for i, arg in enumerate(sys.argv):
        log(f'    {i}: {arg!r}')
    log(f'os.environ ({len(os.environ)}):')
    for k in sorted( os.environ.keys()):
        v = os.environ[ k]
        log( f'    {k}: {v!r}')


g_flavour = os.environ.get( 'PYMUPDF_SETUP_FLAVOUR', 'pb')
assert g_flavour in ('p', 'b', 'pb'), \
        f'Unrecognised {g_flavour=} should be one of: "p", "b", "pb"'

g_root = os.path.abspath( f'{__file__}/..')

# setuptools seems to require current directory to be PyMuPDF.
#
assert os.path.abspath( os.getcwd()) == g_root, \
        f'Current directory must be the PyMuPDF directory'


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


def run(command, check=1):
    log(f'Running: {command}')
    subprocess.run( command, shell=1, check=check)


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
            assert prefix == prefix_actual, f'prefix={prefix} prefix_actual={prefix_actual}'
        for item in items[1:]:
            assert item.startswith( prefix_actual), f'prefix_actual={prefix_actual!r} != item={item!r}'
    return prefix_actual


def tar_extract(path, mode='r:gz', prefix=None, exists='raise'):
    '''
    Extracts tar file.
    
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


def get_gitfiles( directory, submodules=False):
    '''
    Returns list of all files known to git in <directory>; <directory> must be
    somewhere within a git checkout.

    Returned names are all relative to <directory>.

    If <directory>.git exists we use git-ls-files and write list of files to
    <directory>/jtest-git-files.

    Otherwise we require that <directory>/jtest-git-files already exists.
    '''
    def is_within_git_checkout( d):
        while 1:
            #log( 'd={d!r}')
            if not d:
                break
            if os.path.isdir( f'{d}/.git'):
                return True
            d = os.path.dirname( d)

    if is_within_git_checkout( directory):
        command = 'cd ' + directory + ' && git ls-files'
        if submodules:
            command += ' --recurse-submodules'
        command += ' > jtest-git-files'
        log( f'Running: {command}')
        subprocess.run( command, shell=True, check=True)

    with open( '%s/jtest-git-files' % directory, 'r') as f:
        text = f.read()
    ret = text.strip().split( '\n')
    return ret


def get_git_id( directory):
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
    log(f'get_git_id(): directory={directory!r} returning branch={branch!r} sha={sha!r} comment={comment!r}')
    return sha, comment, diff, branch


mupdf_tgz = os.path.abspath( f'{__file__}/../mupdf.tgz')

def get_mupdf_tgz():
    '''
    Creates file called <mupdf_tgz> containing MuPDF source, for inclusion in
    an sdist.
    
    What we do depends on environmental variable PYMUPDF_SETUP_MUPDF_TGZ; see
    docs at start of this file for details.

    Returns name of top-level directory within the .tgz file.
    '''
    mupdf_url_or_local = os.environ.get(
            'PYMUPDF_SETUP_MUPDF_TGZ',
            'https://mupdf.com/downloads/archive/mupdf-1.23.0-source.tar.gz',
            )
    log( f'mupdf_url_or_local={mupdf_url_or_local!r}')
    if mupdf_url_or_local == '':
        # No mupdf in sdist.
        log( 'mupdf_url_or_local is empty string so removing any mupdf_tgz={mupdf_tgz}')
        _fs_remove( mupdf_tgz)
        return
    
    if '://' in mupdf_url_or_local:
        # Download from URL into <mupdf_tgz>.
        mupdf_url = mupdf_url_or_local
        mupdf_url_leaf = os.path.basename( mupdf_url)
        leaf = '.tar.gz'
        assert mupdf_url_leaf.endswith(leaf), f'Unrecognised suffix in mupdf_url={mupdf_url!r}'
        mupdf_local = mupdf_url_leaf[ : -len(leaf)]
        assert mupdf_local.startswith( 'mupdf-')
        if os.path.exists(mupdf_url_leaf):
            try:
                tar_check(mupdf_url_leaf, 'r:gz', prefix=f'{mupdf_local}/')
            except Exception as e:
                log(f'Not using existing file {mupdf_url_leaf} because invalid tar data: {e}')
                _fs_remove( mupdf_url_leaf)
        if os.path.exists(mupdf_url_leaf):
            log(f'Not downloading from {mupdf_url} because already present.')
        else:
            log(f'Downloading from {mupdf_url} to {mupdf_url_leaf}')
            urllib.request.urlretrieve( mupdf_url, mupdf_url_leaf)
            assert os.path.exists( mupdf_url_leaf)
            tar_check( mupdf_url_leaf, 'r:gz', prefix=f'{mupdf_local}/')
        if mupdf_url_leaf != mupdf_tgz:
            _fs_remove( mupdf_tgz)
            shutil.copy2( mupdf_url_leaf, mupdf_tgz)
        return mupdf_local
    
    else:
        # Create archive <mupdf_tgz> contining local mupdf directory's git
        # files.
        mupdf_local = mupdf_url_or_local
        if mupdf_local.endswith( '/'):
            mupdf_local = mupdf_local[:-1]
        assert os.path.isdir( mupdf_local), f'Not a directory: {mupdf_local!r}'
        log( f'Creating .tgz from git files in: {mupdf_local}')
        _fs_remove( mupdf_tgz)
        with tarfile.open( mupdf_tgz, 'w:gz') as f:
            for name in get_gitfiles( mupdf_local, submodules=True):
                path = os.path.join( mupdf_local, name)
                if os.path.isfile( path):
                    f.add( path, f'mupdf/{name}', recursive=False)
        return mupdf_local


def get_mupdf():
    '''
    Downloads and/or extracts mupdf and returns location of mupdf directory.

    Exact behaviour depends on environmental variable
    PYMUPDF_SETUP_MUPDF_BUILD; see docs at start of this file for details.
    '''
    
    # 2023-07-11: For now we default to mupdf master.
    path = os.environ.get( 'PYMUPDF_SETUP_MUPDF_BUILD')
    if 0:
        # 2023-08-18: default to specific sha.
        path = 'git:--recursive --depth 1 --shallow-submodules --branch master https://github.com/ArtifexSoftware/mupdf.git'
        sha = 'a6aaf0b1162a'    # Makerules scripts/wrap/__main__.py: fix cross-building to arm64 on MacOS.
    else:
        sha = None
    log( f'PYMUPDF_SETUP_MUPDF_BUILD={path!r}')
    if path is None:
        # Default.
        if os.path.exists( mupdf_tgz):
            log( f'mupdf_tgz already exists: {mupdf_tgz}')
        else:
            get_mupdf_tgz()
        path = tar_extract( mupdf_tgz, exists='return')
    
    elif path == '':
        # Use system mupdf.
        log( f'PYMUPDF_SETUP_MUPDF_BUILD="", using system mupdf')
        path = None
    
    else:
        git_prefix = 'git:'
        if path.startswith( git_prefix):
            # Get git clone of mupdf.
            #
            # `mupdf_url_or_local` is taken to be portion of a `git clone` command,
            # for example:
            #
            #   PYMUPDF_SETUP_MUPDF_BUILD="git:--branch master git://git.ghostscript.com/mupdf.git"
            #   PYMUPDF_SETUP_MUPDF_BUILD="git:--branch 1.20.x https://github.com/ArtifexSoftware/mupdf.git"
            #   PYMUPDF_SETUP_MUPDF_BUILD="git:--branch master https://github.com/ArtifexSoftware/mupdf.git"
            #
            # One would usually also set PYMUPDF_SETUP_MUPDF_TGZ= (empty string) to
            # avoid the need to download a .tgz into an sdist.
            #
            command_suffix = path[ len(git_prefix):]
            path = 'mupdf'
            
            # Remove any existing directory to avoid the clone failing. (We
            # could assume any existing directory is a git checkout, and do
            # `git pull` or similar, but that's complicated and fragile.)
            #
            _fs_remove(path)
            
            command = (''
                    + f'git clone'
                    + f' --recursive'
                    + f' --depth 1'
                    + f' --shallow-submodules'
                    + f' {command_suffix}'
                    + f' {path}'
                    )
            log( f'Running: {command}')
            subprocess.run( command, shell=True, check=True)

            # Show sha of checkout.
            command = f'cd {path} && git show --pretty=oneline|head -n 1'
            log( f'Running: {command}')
            subprocess.run( command, shell=True, check=False)
            
            if sha:
                command = f'cd mupdf && git checkout {sha}'
                log( f'Running: {command}')
                subprocess.run( command, shell=True)

        # Use custom mupdf directory.
        log( f'Using custom mupdf directory from $PYMUPDF_SETUP_MUPDF_BUILD: {path}')
        assert os.path.isdir( path), f'$PYMUPDF_SETUP_MUPDF_BUILD is not a directory: {path}'
    
    if path:
        path = os.path.abspath( path)
        if path.endswith( '/'):
            path = path[:-1]
    return path


linux = sys.platform.startswith( 'linux') or 'gnu' in sys.platform
openbsd = sys.platform.startswith( 'openbsd')
freebsd = sys.platform.startswith( 'freebsd')
darwin = sys.platform.startswith( 'darwin')
windows = platform.system() == 'Windows' or platform.system().startswith('CYGWIN')
wasm = os.environ.get('OS') in ('wasm', 'wasm-mt')


def _implementations():
    v = os.environ.get( 'PYMUPDF_SETUP_IMPLEMENTATIONS', 'ab')
    assert v in ('a', 'b', 'ab')
    return v

def build():
    '''
    pipcl.py `build_fn()` callback.
    '''
    skeleton = os.environ.get( 'PYMUPDF_SETUP_SKELETON')
    log( f'{skeleton=}')
    if skeleton == '1':
        ret = list()
        log( f'{g_flavour=}')
        run( f'ls -l wheelhouse', check=0)
        if 'b' in g_flavour:
            with open( 'foo.c', 'w') as f:
                f.write( textwrap.dedent( '''
                        int foo(int x)
                        {
                            return x+1;
                        }
                        '''))
                run(f'cc -fPIC -shared -o {g_root}/libfoo.so foo.c')
            ret.append( f'{g_root}/libfoo.so')
            ret.append( (f'{g_root}/READMErb.md', '$dist-info/README.md'))
        if 'p' in g_flavour:
            with open( 'bar.c', 'w') as f:
                f.write( textwrap.dedent( '''
                        int bar(int x)
                        {
                            return x+1;
                        }
                        '''))
                run(f'cc -fPIC -shared -o {g_root}/_bar.so bar.c')
            with open( 'bar.py', 'w') as f:
                f.write( textwrap.dedent( '''
                        def bar(x):
                            return x - 1
                        '''))
            ret.append( f'{g_root}/bar.py')
            ret.append( f'{g_root}/_bar.so')
            ret.append( (f'{g_root}/README.md', '$dist-info/README.md'))
        return ret
    
    elif skeleton == '2':
        os.makedirs( 'src-skeleton2', exist_ok=True)
        ret = list()
        #cc, pythonflags = pipcl.base_compiler()
        #ld, pythonflags = pipcl.base_linker()
        if 1:
            # Build minimal libmupdf.so.
            cc, _ = pipcl.base_compiler()
            with open( 'src-skeleton2/mupdf.c', 'w') as f:
                f.write( textwrap.dedent('''
                        int foo(int x)
                        {
                            return x + 1;
                        }
                        '''))
            # Use of rpath here is Linux/OpenBSD-specific.
            run(f'{cc} -o src-skeleton2/libmupdf.so src-skeleton2/mupdf.c -fPIC -shared -Wl,-rpath,\'$ORIGIN\',-z,origin')
            ret.append( ('src-skeleton2/libmupdf.so', ''))
        if 'p' in g_flavour:
            # Build extension module `fitz`.
            with open( 'src-skeleton2/fitz.i', 'w') as f:
                f.write( textwrap.dedent('''
                        %module fitz
                        
                        %{
                        int foo(int x);
                        int bar(int x)
                        {
                            return foo(x) * 2;
                        }
                        %}
                        
                        int bar(int x);
                        '''))
            path_so_leaf_a = pipcl.build_extension(
                    name = 'fitz',
                    path_i = 'src-skeleton2/fitz.i',
                    outdir = 'src-skeleton2',
                    cpp = False,
                    libpaths = ['src-skeleton2'],
                    libs = ['mupdf'],
                    )
    
            with open( 'src-skeleton2/fitz.i', 'w') as f:
                f.write( textwrap.dedent('''
                        %module fitz_new
                        
                        %{
                        int foo(int x);
                        int bar(int x)
                        {
                            return foo(x) * 2;
                        }
                        %}
                        
                        int bar(int x);
                        '''))
            path_so_leaf_b = pipcl.build_extension(
                    name = 'fitz_new',
                    path_i = 'src-skeleton2/fitz.i',
                    outdir = 'src-skeleton2',
                    cpp = False,
                    libpaths = ['src-skeleton2'],
                    libs = ['mupdf'],
                    )
            ret.append( (f'src-skeleton2/{path_so_leaf_a}', ''))
            ret.append( (f'src-skeleton2/fitz.py', ''))
            ret.append( (f'src-skeleton2/{path_so_leaf_b}', ''))
            ret.append( (f'src-skeleton2/fitz_new.py', ''))
            ret.append( (f'{g_root}/README.md', '$dist-info/README.md'))
        return ret
    
    
    # Download MuPDF.
    #
    mupdf_local = get_mupdf()

    build_type = os.environ.get( 'PYMUPDF_SETUP_MUPDF_BUILD_TYPE', 'release')
    assert build_type in ('debug', 'memento', 'release'), \
            f'Unrecognised build_type={build_type!r}'
    
    # Copy our config header on top of MuPDF's config.h.
    #
    env_extra = dict()
    if mupdf_local:
        from_ = f'{g_root}/fitz/_config.h'
        to_ = f'{mupdf_local}/include/mupdf/fitz/config.h'
        if os.environ.get('PYMUPDF_SETUP_MUPDF_OVERWRITE_CONFIG') == '0':
            # Use MuPDF default config.
            log( f'Not copying {from_} to {to_}.')
        else:
            # Use our special config in MuPDF.
            log( f'Copying {from_} to {to_}.')
            shutil.copy2( from_, to_)
            # Tell the MuPDF shared-library build to exclude large unused font
            # files such as resources/fonts/han/SourceHanSerif-Regular.ttc.
            env_extra[ 'XCFLAGS'] = '-DTOFU_CJK_EXT'
        s = os.stat( f'{to_}')
        log( f'{to_}: {s} mtime={time.strftime("%F-%T", time.gmtime(s.st_mtime))}')
    
    # Build MuPDF shared libraries.
    #
    if windows:
        mupdf_build_dir = build_mupdf_windows( mupdf_local, env_extra, build_type)
    else:
        mupdf_build_dir = build_mupdf_unix( mupdf_local, env_extra, build_type)
    log( f'build(): mupdf_build_dir={mupdf_build_dir!r}')
    
    # Build rebased `extra` module and/or PyMuPDF `fitz` module.
    #
    path_so_leaf_a, path_so_leaf_b = _build_extensions(
            mupdf_local,
            mupdf_build_dir,
            build_type,
            )
    
    for d in (
            mupdf_build_dir,
            f'{g_root}/fitz',
            f'{g_root}/src',
            ):
        command = f'ls -l {d}'
        log(f'Running: {command}')
        os.system(command)
    
    # Generate lists of (from, to) items to return to pipcl. We put MuPDF
    # shared libraries in a separate list so that we can build specific wheels
    # as determined by g_flavour.
    #
    ret_p = list()  # For PyMuPDF.
    ret_b = list()  # For PyMuPDFb.
    def add( ret, from_, to_):
        ret.append( (from_, to_))
    
    if path_so_leaf_a:
        # Add classic implementation files.
        to_dir = 'fitz/'
        add( ret_p, f'{g_root}/fitz/__init__.py', to_dir)
        add( ret_p, f'{g_root}/fitz/__main__.py', to_dir)
        add( ret_p, f'{g_root}/fitz/fitz.py', to_dir)
        add( ret_p, f'{g_root}/fitz/table.py', to_dir)
        add( ret_p, f'{g_root}/fitz/utils.py', to_dir)
        add( ret_p, f'{g_root}/fitz/{path_so_leaf_a}', to_dir)

        if mupdf_local:
            # Add mupdf shared library next to `path_so_leaf_a` so it will be
            # found at runtime. Would prefer to embed a softlink to mupdfpy's
            # file but wheels do not seem to support them.
            if windows:
                wp = pipcl.wdev.WindowsPython()
                add( ret_b, f'{mupdf_build_dir}/mupdfcpp{wp.cpu.windows_suffix}.dll', to_dir)
            elif darwin:
                add( ret_b, f'{mupdf_build_dir}/libmupdf.dylib', f'{to_dir}libmupdf.dylib')
            elif wasm:
                add( ret_b, f'{mupdf_build_dir}/libmupdf.so', 'PyMuPDF.libs/')
            else:
                add( ret_b, f'{mupdf_build_dir}/libmupdf.so', to_dir)

    if path_so_leaf_b:
        # Add rebased implementation files.
        to_dir = 'fitz_new/'
        add( ret_p, f'{g_root}/src/__init__.py', to_dir)
        add( ret_p, f'{g_root}/src/__main__.py', to_dir)
        add( ret_p, f'{g_root}/src/fitz.py', to_dir)
        add( ret_p, f'{g_root}/fitz/table.py', to_dir)
        add( ret_p, f'{g_root}/src/utils.py', to_dir)
        add( ret_p, f'{g_root}/src/extra.py', to_dir)
        add( ret_p, f'{g_root}/src/{path_so_leaf_b}', to_dir)
        
        if mupdf_local:
            add( ret_p, f'{mupdf_build_dir}/mupdf.py', to_dir)
            
            if windows:
                wp = pipcl.wdev.WindowsPython()
                add( ret_p, f'{mupdf_build_dir}/_mupdf.pyd', to_dir)
                add( ret_b, f'{mupdf_build_dir}/mupdfcpp{wp.cpu.windows_suffix}.dll', to_dir)
            elif darwin:
                add( ret_p, f'{mupdf_build_dir}/_mupdf.so', to_dir)
                add( ret_b, f'{mupdf_build_dir}/libmupdfcpp.so', to_dir)
                add( ret_b, f'{mupdf_build_dir}/libmupdf.dylib', f'{to_dir}libmupdf.dylib')
            else:
                add( ret_p, f'{mupdf_build_dir}/_mupdf.so', to_dir)
                add( ret_b, f'{mupdf_build_dir}/libmupdfcpp.so', to_dir)
                add( ret_b, f'{mupdf_build_dir}/libmupdf.so', to_dir)
    
    if g_flavour == 'pb':
        ret = ret_p + ret_b
    elif g_flavour == 'p':
        ret = ret_p
    elif g_flavour == 'b':
        ret = ret_b
    else:
        assert 0
    
    if g_flavour == 'b':
        add( ret, f'{g_root}/READMErb.md', '$dist-info/README.md')
    else:
        add( ret, f'{g_root}/README.md', '$dist-info/README.md')
    
    for f, t in ret:
        log( f'build(): {f} => {t}')
    return ret


def env_add(env, name, value, sep=' ', prefix=False, verbose=False):
    '''
    Appends/prepends `<value>` to `env[name]`.
    '''
    v = env.get(name)
    if verbose:
        log(f'Initally: {name}={v!r}')
    if v is None:
        env[ name] = value
    else:
        if prefix:
            env[ name] =  f'{value}{sep}{v}'
        else:
            env[ name] =  f'{v}{sep}{value}'
    if verbose:
        log(f'Returning with {name}={env[name]!r}')


def build_mupdf_windows( mupdf_local, env, build_type):
    
    assert mupdf_local

    wp = pipcl.wdev.WindowsPython()
    windows_build_tail = f'build\\shared-{build_type}-x{wp.cpu.bits}-py{wp.version}'
    windows_build_dir = f'{mupdf_local}\\{windows_build_tail}'
    #log( f'Building mupdf.')
    devenv = os.environ.get('PYMUPDF_SETUP_DEVENV')
    if not devenv:
        vs = pipcl.wdev.WindowsVS()
        devenv = vs.devenv
    if not devenv:
        devenv = 'devenv.com'
        log( f'Cannot find devenv.com in default locations, using: {devenv!r}')
    command = f'cd {mupdf_local} && {sys.executable} ./scripts/mupdfwrap.py'
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
    command += f' -d {windows_build_tail} -b --refcheck-if "#if 1" --devenv "{devenv}" '
    if 'b' in _implementations():
        command += 'all'
    else:
        command += '01' # No need for C++/Python bindings.
    env2 = os.environ.copy()
    env2.update(env)
    if os.environ.get( 'PYMUPDF_SETUP_MUPDF_REBUILD') == '0':
        log( f'PYMUPDF_SETUP_MUPDF_REBUILD is "0" so not building MuPDF; would have run with env={env!r}: {command}')
    else:
        log( f'Building MuPDF by running with {env}={env!r}: {command}')
        subprocess.run( command, shell=True, check=True, env=env2)
        log( f'Finished building mupdf.')
    
    return windows_build_dir


def build_mupdf_unix( mupdf_local, env, build_type):
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

    flags = 'HAVE_X11=no HAVE_GLFW=no HAVE_GLUT=no HAVE_LEPTONICA=yes HAVE_TESSERACT=yes'
    flags += ' verbose=yes'
    env = env.copy()
    if openbsd or freebsd:
        env_add(env, 'CXX', 'clang++', ' ')

    # Add extra flags for MacOS cross-compilation, where ARCHFLAGS can be
    # '-arch arm64'.
    #
    archflags = os.environ.get( 'ARCHFLAGS')
    if archflags:
        env_add(env, 'XCFLAGS', archflags)
        env_add(env, 'XLIBS', archflags)

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
    build_prefix = f'PyMuPDF-'
    if wasm:
        build_prefix += 'wasm-'
    else:
        build_prefix += f'{platform.machine()}-'
    build_prefix_extra = os.environ.get( '_PYTHON_HOST_PLATFORM')
    if build_prefix_extra:
        build_prefix += f'{build_prefix_extra}-'
    build_prefix += 'shared-'
    unix_build_dir = f'{mupdf_local}/build/{build_prefix}{build_type}'

    # We need MuPDF's Python bindings, so we build MuPDF with
    # `mupdf/scripts/mupdfwrap.py` instead of running `make`.
    #
    env_string = ''
    for n, v in env.items():
        env_string += f' {n}={shlex.quote(v)}'
    command = f'cd {mupdf_local} &&{env_string} {sys.executable} ./scripts/mupdfwrap.py -d build/{build_prefix}{build_type} -b '
    if 'b' in _implementations() and 'p' in g_flavour:
        command += 'all'
    else:
        command += 'm01'    # No need for C++/Python bindings.
    command += f' && echo {unix_build_dir}:'
    command += f' && ls -l {unix_build_dir}'

    if os.environ.get( 'PYMUPDF_SETUP_MUPDF_REBUILD') == '0':
        log( f'PYMUPDF_SETUP_MUPDF_REBUILD is "0" so not building MuPDF; would have run: {command}')
    else:
        log( f'Building MuPDF by running: {command}')
        subprocess.run( command, shell=True, check=True)
        log( f'Finished building mupdf.')
    
    return unix_build_dir


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
    

def _build_extensions( mupdf_local, mupdf_build_dir, build_type):
    '''
    Builds Python extension module `extra` and `_fitz`.

    Returns (path_so_leaf_a, path_so_leaf_b), the leafnames of the generated
    shared libraries within mupdf_build_dir.
    '''
    compiler_extra = ''
    if build_type == 'memento':
        compiler_extra += ' -DMEMENTO'
    mupdf_build_dir_flags = os.path.basename( mupdf_build_dir).split( '-')
    optimise = 'release' in mupdf_build_dir_flags
    debug = 'debug' in mupdf_build_dir_flags
    if windows:
        defines = ('FZ_DLL_CLIENT',)
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
        linker_extra = ''
    else:
        defines = None
        libpaths = (mupdf_build_dir,)
        libs = ['mupdf']
        libraries = f'{mupdf_build_dir}/{libs[0]}'
        compiler_extra += (
                ' -Wall'
                ' -Wno-deprecated-declarations'
                ' -Wno-unused-const-variable'
                )
        if openbsd:
            compiler_extra += ' -Wno-deprecated-declarations'
        linker_extra = ''
    
    path_so_leaf_a = None
    path_so_leaf_b = None
    
    if 'a' in _implementations():
        # Build PyMuPDF original implementation.
        log('Building PyMuPDF classic.')
        if mupdf_local:
            includes = (
                    f'{mupdf_local}/include',
                    f'{mupdf_local}/include/mupdf',
                    f'{mupdf_local}/thirdparty/freetype/include',
                    )
        else:
            includes = None
        
        # Update helper-git-versions.i.
        f = io.StringIO()
        f.write('%pythoncode %{\n')
        def repr_escape(text):
            text = repr(text)
            text = text.replace('{', '{{')
            text = text.replace('}', '}}')
            text = text.replace('%', '{chr(37)})')  # Avoid confusing swig.
            return 'f' + text
        def write_git(name, directory):
            sha, comment, diff, branch = get_git_id(directory)
            f.write(f'{name}_git_sha = \'{sha}\'\n')
            f.write(f'{name}_git_comment = {repr_escape(comment)}\n')
            f.write(f'{name}_git_diff = {repr_escape(diff)}\n')
            f.write(f'{name}_git_branch = {repr_escape(branch)}\n')
            f.write('\n')
        write_git('pymupdf', '.')
        if mupdf_local:
            write_git('mupdf', mupdf_local)
        f.write('%}\n')
        _fs_update( f.getvalue(), 'fitz/helper-git-versions.i')

        if windows:
            compiler_extra_c = ''
        else:
            compiler_extra_c = (
                    ' -Wno-incompatible-pointer-types'
                    ' -Wno-pointer-sign'
                    ' -Wno-sign-compare'
                    )
        prerequisites_swig = glob.glob( f'{g_root}/fitz/*.i')
        if os.environ.get( 'PYMUPDF_SETUP_REBUILD_GIT_DETAILS') == '0':
            # Remove helper-git-versions.i from prerequisites_swig so
            # it doesn't force rebuild on its own. [Cannot easily use
            # prerequisites_swig.remove() because / vs \ on Windows.]
            #
            for i, p in enumerate( prerequisites_swig):
                if p.endswith( 'helper-git-versions.i'):
                    del prerequisites_swig[i]
                    break
            else:
                assert 0, f'Cannot find *helper-git-versions.i in prerequisites_swig: {prerequisites_swig}'
        
        path_so_leaf_a = pipcl.build_extension(
                name = 'fitz',
                path_i = f'{g_root}/fitz/fitz.i',
                outdir = f'{g_root}/fitz',
                includes = includes,
                defines = defines,
                libpaths = libpaths,
                libs = libs,
                compiler_extra = compiler_extra + compiler_extra_c,
                linker_extra = linker_extra,
                optimise = optimise,
                debug = debug,
                cpp = False,
                prerequisites_swig = prerequisites_swig,
                prerequisites_compile = f'{mupdf_local}/include',
                prerequisites_link = libraries,
                )

    if mupdf_local:
        includes = (
                f'{mupdf_local}/platform/c++/include',
                f'{mupdf_local}/include',
                )
    else:
        includes = None
    if 'b' in _implementations():
        # Build rebased extension module.
        log('Building PyMuPDF rebased.')
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
        path_so_leaf_b = pipcl.build_extension(
                name = 'extra',
                path_i = f'{g_root}/src/extra.i',
                outdir = f'{g_root}/src',
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
                )
    
    return path_so_leaf_a, path_so_leaf_b
    

def sdist():
    ret = list()
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
    if get_mupdf_tgz():
        ret.append(mupdf_tgz)
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

with open( f'{g_root}/README.md', encoding='utf-8') as f:
    readme_ = f.read()

with open( f'{g_root}/READMErb.md', encoding='utf-8') as f:
    readme_rb = f.read()

# We generate different wheels depending on g_flavour.
#

version = '1.23.0'

tag_python = None
requires_dist = None,

if g_flavour == 'pb':
    name = 'PyMuPDF'
    summary = 'Rebased Python bindings for the PDF toolkit and renderer MuPDF'
    readme = readme_
elif g_flavour == 'p':
    name = 'PyMuPDF'
    summary = 'Rebased Python bindings for the PDF toolkit and renderer MuPDF - without shared libraries'
    readme = readme_
    requires_dist = f'PyMuPDFb =={version}'
elif g_flavour == 'b':
    name = 'PyMuPDFb'
    summary = 'Rebased Python bindings for the PDF toolkit and renderer MuPDF - shared libraries only'
    readme = readme_rb
    tag_python = 'py3'  # Works with any Python version.
else:
    assert 0, f'Unrecognised flavour: {g_flavour}'

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
        requires_python = '>=3.8',
        license = 'GNU AFFERO GPL 3.0',
        project_url = [
            ('Documentation, https://pymupdf.readthedocs.io/'),
            ('Source, https://github.com/pymupdf/pymupdf'),
            ('Tracker, https://github.com/pymupdf/PyMuPDF/issues'),
            ('Changelog, https://pymupdf.readthedocs.io/en/latest/changes.html'),
            ],
        fn_build=build,
        fn_sdist=sdist,
        
        tag_python=tag_python,

        # 30MB: 9 ZIP_DEFLATED
        # 28MB: 9 ZIP_BZIP2
        # 23MB: 9 ZIP_LZMA
        #wheel_compression = zipfile.ZIP_DEFLATED if (darwin or wasm) else zipfile.ZIP_LZMA,
        wheel_compresslevel = 9,
        )

build_wheel = p.build_wheel
build_sdist = p.build_sdist


import sys
if __name__ == '__main__':
    p.handle_argv(sys.argv)
