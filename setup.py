'''
Overview:

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
    
    PYMUPDF_SETUP_DEVENV
        Location of devenv.com on Windows. If unset we search in some
        hard-coded default locations; if that fails we use just 'devenv.com'.
    
    PYMUPDF_SETUP_MUPDF_BUILD
        If set, overrides location of mupdf when building PyMuPDF:
            Empty string:
                Build PyMuPDF with the system mupdf.
            Otherwise:
                Location of mupdf directory.
    
    PYMUPDF_SETUP_MUPDF_BUILD_TYPE
        Unix only. Controls build type of MuPDF. Supported values are:
            debug
            memento
            release (default)

    PYMUPDF_SETUP_MUPDF_CLEAN
        If '1', we do a clean MuPDF build.

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
    
Building MuPDF:
    When building MuPDF, we overwrite the mupdf's include/mupdf/fitz/config.h
    with fitz/_config.h and do a PyMuPDF-specific build.

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
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import urllib.request

from setuptools import Extension, setup
from setuptools.command.build_py import build_py as build_py_orig


def log( text):
    print(f'PyMuPDF/setup.py: {text}', file=sys.stderr)
    sys.stderr.flush()


if 1:
    # For debugging.
    log(f'sys.argv: {sys.argv}')
    log(f'os.getcwd(): {os.getcwd()}')
    log(f'__file__: {__file__}')
    log(f'$PYTHON_ARCH: {os.environ.get("PYTHON_ARCH")!r}')
    log(f'os.environ ({len(os.environ)}):')
    for k, v in os.environ.items():
        log( f'    {k}: {v}')


def remove(path):
    '''
    Removes file or directory, without raising exception if it doesn't exist.

    We assert-fail if the path still exists when we return, in case of
    permission problems etc.
    '''
    try:
        os.remove( path)
    except Exception:
        pass
    shutil.rmtree( path, ignore_errors=1)
    assert not os.path.exists( path)


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
            return prefix_actual
        else:
            assert 0, f'Unrecognised exists={exists!r}'
    assert not os.path.exists( prefix_actual), f'Path already exists: {prefix_actual}'
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
            #log( '{d=}')
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


def get_git_id_raw( directory):
    if not os.path.isdir( '%s/.git' % directory):
        return
    text = system(
            f'cd {directory} && (PAGER= git show --pretty=oneline|head -n 1 && git diff)',
            out='return',
            )
    return text


def word_size():
    '''
    Returns integer word size (32 or 64) of build.
    '''
    # Looks like on Windows, cibuildwheel runs us with a 64-bit Python
    # interpreter even when building a 32-bit wheel. It appears to set
    # PYTHON_ARCH to indicate word size (this isn't documented anywhere?).
    #
    a = os.environ.get( 'PYTHON_ARCH')
    if a is None:
        if sys.maxsize == 2**31-1:
            return 32
        elif sys.maxsize == 2**63-1:
            return 64
        else:
            assert 0, 'Unrecognised sys.maxsize={sys.maxsize!r}'
    else:
        if a == '32':
            return 32
        elif a == '64':
            return 64
        else:
            assert 0, f'Unrecognised $PYTHON_ARCH={a!r}'


class build_ext_first(build_py_orig):
    """
    custom build_py command which runs build_ext first
    this is necessary because build_py needs the fitz.py which is only generated
    by SWIG in the build_ext step
    """
    def run(self):
        self.run_command("build_ext")
        return super().run()


DEFAULT = [
    "mupdf",
    "mupdf-third",
]

ALPINE = DEFAULT + [
    "jbig2dec",
    "jpeg",
    "openjp2",
    "harfbuzz",
]

ARCH_LINUX = DEFAULT + [
    "jbig2dec",
    "openjp2",
    "jpeg",
    "freetype",
    "gumbo",
]

NIX = ARCH_LINUX + [
    "harfbuzz",
]

OPENSUSE = NIX + [
    "png16",
]

DEBIAN = OPENSUSE + [
    "mujs",
]

FEDORA = NIX + [
    "leptonica",
    "tesseract",
]

LIBRARIES = {
    "default": DEFAULT,
    "ubuntu": DEBIAN,
    "arch": ARCH_LINUX,
    "manjaro": ARCH_LINUX,
    "artix": ARCH_LINUX,
    "opensuse": OPENSUSE,
    "fedora": FEDORA,
    "alpine": ALPINE,
    "nix": NIX,
    "debian": DEBIAN,
}


def load_libraries():
    if os.getenv("NIX_STORE"):
        return LIBRARIES["nix"]

    try:
        import distro

        os_id = distro.id()
    except:
        os_id = ""
    if os_id in list(LIBRARIES.keys()) + ["manjaro", "artix"]:
        return LIBRARIES[os_id]

    filepath = "/etc/os-release"
    if not os.path.exists(filepath):
        return LIBRARIES["default"]
    regex = re.compile("^([\\w]+)=(?:'|\")?(.*?)(?:'|\")?$")
    with open(filepath) as os_release:
        info = {
            regex.match(line.strip()).group(1): re.sub(
                r'\\([$"\'\\`])', r"\1", regex.match(line.strip()).group(2)
            )
            for line in os_release
            if regex.match(line.strip())
        }

    os_id = info["ID"]
    if os_id.startswith("opensuse"):
        os_id = "opensuse"
    if os_id not in LIBRARIES.keys():
        return LIBRARIES["default"]
    return LIBRARIES[os_id]


def get_git_id( directory, allow_none=False):
    '''
    Returns text where first line is '<git-sha> <commit summary>' and remaining
    lines contain output from 'git diff' in <directory>.

    directory:
        Root of git checkout.
    allow_none:
        If true, we return None if <directory> is not a git checkout and
        jtest-git-id file does not exist.
    '''
    filename = f'{directory}/jtest-git-id'
    text = get_git_id_raw( directory)
    if text:
        with open( filename, 'w') as f:
            f.write( text)
    elif os.path.isfile( filename):
        with open( filename) as f:
            text = f.read()
    else:
        if not allow_none:
            raise Exception( f'Not in git checkout, and no file called: {filename}.')
        text = None
    return text


mupdf_tgz = os.path.abspath( f'{__file__}/../mupdf.tgz')

def get_mupdf_tgz():
    '''
    Creates .tgz file containing MuPDF source, for inclusion in an sdist.
    
    What we do depends on environmental variable PYMUPDF_SETUP_MUPDF_TGZ; see
    docs at start of this file for details.

    Returns name of top-level directory within the .tgz file.
    '''
    mupdf_url_or_local = os.environ.get(
            'PYMUPDF_SETUP_MUPDF_TGZ',
            'https://mupdf.com/downloads/archive/mupdf-1.20.0-source.tar.gz',
            )
    log( f'mupdf_url_or_local={mupdf_url_or_local!r}')
    if mupdf_url_or_local == '':
        # No mupdf in sdist.
        remove( mupdf_tgz)
        return
    
    if '://' in mupdf_url_or_local:
        # Download from URL into <mupdf_tgz>.
        mupdf_url = mupdf_url_or_local
        mupdf_url_leaf = os.path.basename( mupdf_url)
        leaf = '.tar.gz'
        assert mupdf_url_leaf.endswith(leaf), f'Unrecognised suffix in mupdf_url={mupdf_url!r}'
        mupdf_local = mupdf_url_leaf[ : -len(leaf)] + '/'
        assert mupdf_local.startswith( 'mupdf-')
        log(f'Downloading from: {mupdf_url}')
        remove( mupdf_url_leaf)
        urllib.request.urlretrieve( mupdf_url, mupdf_url_leaf)
        assert os.path.exists( mupdf_url_leaf)
        tar_check( mupdf_url_leaf, 'r:gz', mupdf_local)
        if mupdf_url_leaf != mupdf_tgz:
            remove( mupdf_tgz)
            os.rename( mupdf_url_leaf, mupdf_tgz)
        return mupdf_local
    
    else:
        # Create archive <mupdf_tgz> contining local mupdf directory's git
        # files.
        mupdf_local = mupdf_url_or_local
        if not mupdf_local.endswith( '/'):
            mupdf_local += '/'
        assert os.path.isdir( mupdf_local), f'Not a directory: {mupdf_local!r}'
        log( f'Creating .tgz from git files in: {mupdf_local}')
        remove( mupdf_tgz)
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
    path = os.environ.get( 'PYMUPDF_SETUP_MUPDF_BUILD')
    if path is None:
        # Default.
        if not os.path.exists( mupdf_tgz):
            get_mupdf_tgz()
        return tar_extract( mupdf_tgz, exists='return')
    
    elif path == '':
        # Use system mupdf.
        log( f'PYMUPDF_SETUP_MUPDF_BUILD="", using system mupdf')
        return None
    
    else:
        # Use custom mupdf directory.
        log( f'Using custom mupdf directory from $PYMUPDF_SETUP_MUPDF_BUILD: {path}')
        assert os.path.isdir( path), f'$PYMUPDF_SETUP_MUPDF_BUILD is not a directory: {path}'
        return path


include_dirs = []
library_dirs = []
libraries = []
extra_link_args = []


if 'sdist' in sys.argv:
    # Create local mupdf.tgz, for inclusion in sdist.
    get_mupdf_tgz()


if ('-h' not in sys.argv and '--help' not in sys.argv
        and ('bdist_wheel' in sys.argv or 'build' in sys.argv or 'bdist' in sys.argv)
        ):

    # Build MuPDF before setuptools runs, so that it can link with the MuPDF
    # libraries.
    #
    mupdf_local = get_mupdf()
    if mupdf_local:
        if not mupdf_local.endswith( '/'):
            mupdf_local += '/'
    unix_build_type = None
    
    # Force clean build of MuPDF.
    #
    if mupdf_local and os.environ.get( 'PYMUPDF_SETUP_MUPDF_CLEAN') == '1':
        remove( f'{mupdf_local}build')

    # Always force clean build of PyMuPDF SWIG files etc, because setuptools
    # doesn't seem to notice when our mupdf headers etc are newer than the
    # SWIG-generated files.
    #
    remove( os.path.abspath( f'{__file__}/../build/'))
    remove( os.path.abspath( f'{__file__}/../install/'))
    
    # Copy PyMuPDF's config file into mupdf. For example this #define's TOFU,
    # which excludes various fonts in the MuPDF binaries.
    if mupdf_local:
        log( f'Building mupdf.')
        shutil.copy2( 'fitz/_config.h', f'{mupdf_local}include/mupdf/fitz/config.h')
    
        if platform.system() == 'Windows' or platform.system().startswith('CYGWIN'):
            # Windows build.
            devenv = os.environ.get('PYMUPDF_SETUP_DEVENV')
            if not devenv:
                # Search for devenv in some known locations.
                devenv = glob.glob('C:/Program Files (x86)/Microsoft Visual Studio/2019/*/Common7/IDE/devenv.com')
                if devenv:
                    devenv = devenv[0]
            if not devenv:
                devenv = 'devenv.com'
                log( f'Cannot find devenv.com in default locations, using: {devenv!r}')
            windows_config = 'Win32' if word_size()==32 else 'x64'
            command = (
                    f'cd {mupdf_local}&&'
                    f'"{devenv}"'
                    f' platform/win32/mupdf.sln'
                    f' /Build "ReleaseTesseract|{windows_config}"'
                    f' /Project mupdf'
                    )
        else:
            # Unix build.
            flags = 'HAVE_X11=no HAVE_GLFW=no HAVE_GLUT=no HAVE_LEPTONICA=yes HAVE_TESSERACT=yes'
            flags += ' verbose=yes'
            env = ''
            make = 'make'
            if os.uname()[0] == 'Linux':
                env += ' CFLAGS="-fPIC"'
            if os.uname()[0] == 'OpenBSD':
                make = 'gmake'
                env += ' CFLAGS="-fPIC" CXX=clang++'
            unix_build_type = os.environ.get( 'PYMUPDF_SETUP_MUPDF_BUILD_TYPE', 'release')
            assert unix_build_type in ('debug', 'memento', 'release')
            flags += f' build={unix_build_type}'
            command = f'cd {mupdf_local} && {env} {make} {flags}'
            command += f' && echo "build/{unix_build_type}:"'
            command += f' && ls -l build/{unix_build_type}'
        
        log( f'Building MuPDF by running: {command}')
        subprocess.run( command, shell=True, check=True)
        log( f'Finished building mupdf.')
    else:
        # Use installed MuPDF.
        log( f'Using system mupdf.')
    
    # Set include and library paths for building PyMuPDF.
    #
    if mupdf_local:
        assert os.path.isdir( mupdf_local), f'Not a directory: {mupdf_local!r}'
        include_dirs.append( f'{mupdf_local}include')
        include_dirs.append( f'{mupdf_local}include/mupdf')
        include_dirs.append( f'{mupdf_local}thirdparty/freetype/include')
        if unix_build_type:
            library_dirs.append( f'{mupdf_local}build/{unix_build_type}')

    if sys.platform.startswith("linux") or "gnu" in sys.platform:
        if not mupdf_local:
            include_dirs.append( '/usr/include/mupdf')
            include_dirs.append( '/usr/local/include/mupdf')

        include_dirs.append( '/usr/include/freetype2')
        libraries = load_libraries()
        extra_link_args = []

    elif sys.platform.startswith(("darwin", "freebsd", "openbsd")):
        if mupdf_local:
            # On OpenBSD this seems to not work, possibly because setuptools'
            # link command includes '-L /usr/local/lib', the resulting library
            # is only 2M, and at runtime we get lots of missing MuPDF symbols.
            #
            # If we manually add ../mupdf/build/release/libmupdf{,-third}.a,
            # the resulting library is 19M but at runtime the Python module
            # 'fitz' fails to load, we don't even get to see missing symbols.
            #
            library_dirs.append(f'{mupdf_local}build/{unix_build_type}')
            
            if sys.platform.startswith('openbsd'):
                # setuptools' link command always seems to put '-L
                # /usr/local/lib' before any <library_dirs> that we specify,
                # so '-l mupdf -l mupdf-third' will end up using the system
                # libmupdf.so (if installed) instead of the one we've built in
                # <mupdf_local>.
                #
                # So we force linking with our mupdf libraries by specifying
                # them in <extra_link_args>.
                #
                extra_link_args.append( f'{mupdf_local}build/{unix_build_type}/libmupdf.a')
                extra_link_args.append( f'{mupdf_local}build/{unix_build_type}/libmupdf-third.a')
                if os.environ.get( 'PYMUPDF_SETUP_MUPDF_BUILD_TYPE') == 'memento':
                    extra_link_args.append( f'-lexecinfo')
            else:
                libraries = [
                        f'mupdf',
                        f'mupdf-third',
                        ]
        else:
            include_dirs.append("/usr/local/include/mupdf")
            include_dirs.append("/usr/local/include")
            include_dirs.append("/opt/homebrew/include/mupdf")
            library_dirs.append("/usr/local/lib")
            libraries = ["mupdf", "mupdf-third"]
            library_dirs.append("/opt/homebrew/lib")
            
        include_dirs.append("/usr/include/freetype2")
        include_dirs.append("/usr/local/include/freetype2")
        include_dirs.append("/usr/X11R6/include/freetype2")
        include_dirs.append("/opt/homebrew/include")
        include_dirs.append("/opt/homebrew/include/freetype2")

        library_dirs.append("/opt/homebrew/lib")

    else:
        # Windows.
        assert mupdf_local
        if word_size() == 32:
            library_dirs.append( f'{mupdf_local}platform/win32/ReleaseTesseract')
            library_dirs.append( f'{mupdf_local}platform/win32/Release')
        else:
            library_dirs.append( f'{mupdf_local}platform/win32/x64/ReleaseTesseract')
            library_dirs.append( f'{mupdf_local}platform/win32/x64/Release')
        libraries = [
            "libmupdf",
            "libresources",
            "libthirdparty",
            #"libleptonica",
            #"libtesseract",
        ]
        extra_link_args = ["/NODEFAULTLIB:MSVCRT"]

    # add any local include and library folders
    pymupdf_dirs = os.environ.get("PYMUPDF_DIRS", None)
    if pymupdf_dirs:
        with open(pymupdf_dirs) as dirfile:
            local_dirs = json.load(dirfile)
            include_dirs += local_dirs.get("include_dirs", [])
            library_dirs += local_dirs.get("library_dirs", [])

    if 1:
        # Diagnostics.
        log( f'library_dirs={library_dirs}')
        log( f'libraries={libraries}')
        log( f'include_dirs={include_dirs}')
        log( f'extra_link_args={extra_link_args}')


module = Extension(
    "fitz._fitz",
    ["fitz/fitz.i"],
    language="c++",
    include_dirs=include_dirs,
    library_dirs=library_dirs,
    libraries=libraries,
    extra_link_args=extra_link_args,
)


setup_py_cwd = os.path.dirname(__file__)
classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "Intended Audience :: Information Technology",
    "Operating System :: MacOS",
    "Operating System :: Microsoft :: Windows",
    "Operating System :: POSIX :: Linux",
    "Programming Language :: C",
    "Programming Language :: Python :: 3 :: Only",
    "Programming Language :: Python :: Implementation :: CPython",
    "Topic :: Utilities",
    "Topic :: Multimedia :: Graphics",
    "Topic :: Software Development :: Libraries",
]
with open(os.path.join(setup_py_cwd, "README.md"), encoding="utf-8") as f:
    readme = f.read()

setup(
    name="PyMuPDF",
    version="1.20.0",
    description="Python bindings for the PDF toolkit and renderer MuPDF",
    long_description=readme,
    long_description_content_type="text/markdown",
    classifiers=classifiers,
    url="https://github.com/pymupdf/PyMuPDF",
    author="Artifex",
    author_email="support@artifex.com",
    cmdclass={"build_py": build_ext_first},
    ext_modules=[module],
    python_requires=">=3.7",
    py_modules=["fitz.fitz", "fitz.utils", "fitz.__main__"],
    license="GNU AFFERO GPL 3.0",
    project_urls={
        "Documentation": "https://pymupdf.readthedocs.io/",
        "Source": "https://github.com/pymupdf/pymupdf",
        "Tracker": "https://github.com/pymupdf/PyMuPDF/issues",
        "Changelog": "https://pymupdf.readthedocs.io/en/latest/changes.html",
    },
)
