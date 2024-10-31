'''
Python packaging operations, including PEP-517 support, for use by a `setup.py`
script.

The intention is to take care of as many packaging details as possible so that
setup.py contains only project-specific information, while also giving as much
flexibility as possible.

For example we provide a function `build_extension()` that can be used to build
a SWIG extension, but we also give access to the located compiler/linker so
that a `setup.py` script can take over the details itself.

Run doctests with: `python -m doctest pipcl.py`
'''

import base64
import glob
import hashlib
import inspect
import io
import os
import platform
import re
import shutil
import site
import subprocess
import sys
import sysconfig
import tarfile
import textwrap
import time
import zipfile

import wdev


class Package:
    '''
    Our constructor takes a definition of a Python package similar to that
    passed to `distutils.core.setup()` or `setuptools.setup()` (name, version,
    summary etc) plus callbacks for building, getting a list of sdist
    filenames, and cleaning.

    We provide methods that can be used to implement a Python package's
    `setup.py` supporting PEP-517.

    We also support basic command line handling for use
    with a legacy (pre-PEP-517) pip, as implemented
    by legacy distutils/setuptools and described in:
    https://pip.pypa.io/en/stable/reference/build-system/setup-py/

    Here is a `doctest` example of using pipcl to create a SWIG extension
    module. Requires `swig`.

    Create an empty test directory:

        >>> import os
        >>> import shutil
        >>> shutil.rmtree('pipcl_test', ignore_errors=1)
        >>> os.mkdir('pipcl_test')

    Create a `setup.py` which uses `pipcl` to define an extension module.

        >>> import textwrap
        >>> with open('pipcl_test/setup.py', 'w') as f:
        ...     _ = f.write(textwrap.dedent("""
        ...             import sys
        ...             import pipcl
        ...
        ...             def build():
        ...                 so_leaf = pipcl.build_extension(
        ...                         name = 'foo',
        ...                         path_i = 'foo.i',
        ...                         outdir = 'build',
        ...                         )
        ...                 return [
        ...                         ('build/foo.py', 'foo/__init__.py'),
        ...                         ('cli.py', 'foo/__main__.py'),
        ...                         (f'build/{so_leaf}', f'foo/'),
        ...                         ('README', '$dist-info/'),
        ...                         (b'Hello world', 'foo/hw.txt'),
        ...                         ]
        ...
        ...             def sdist():
        ...                 return [
        ...                         'foo.i',
        ...                         'bar.i',
        ...                         'setup.py',
        ...                         'pipcl.py',
        ...                         'wdev.py',
        ...                         'README',
        ...                         (b'Hello word2', 'hw2.txt'),
        ...                         ]
        ...
        ...             p = pipcl.Package(
        ...                     name = 'foo',
        ...                     version = '1.2.3',
        ...                     fn_build = build,
        ...                     fn_sdist = sdist,
        ...                     entry_points = (
        ...                         { 'console_scripts': [
        ...                             'foo_cli = foo.__main__:main',
        ...                             ],
        ...                         }),
        ...                     )
        ...
        ...             build_wheel = p.build_wheel
        ...             build_sdist = p.build_sdist
        ...
        ...             # Handle old-style setup.py command-line usage:
        ...             if __name__ == '__main__':
        ...                 p.handle_argv(sys.argv)
        ...             """))

    Create the files required by the above `setup.py` - the SWIG `.i` input
    file, the README file, and copies of `pipcl.py` and `wdev.py`.

        >>> with open('pipcl_test/foo.i', 'w') as f:
        ...     _ = f.write(textwrap.dedent("""
        ...             %include bar.i
        ...             %{
        ...             #include <stdio.h>
        ...             #include <string.h>
        ...             int bar(const char* text)
        ...             {
        ...                 printf("bar(): text: %s\\\\n", text);
        ...                 int len = (int) strlen(text);
        ...                 printf("bar(): len=%i\\\\n", len);
        ...                 fflush(stdout);
        ...                 return len;
        ...             }
        ...             %}
        ...             int bar(const char* text);
        ...             """))

        >>> with open('pipcl_test/bar.i', 'w') as f:
        ...     _ = f.write( '\\n')

        >>> with open('pipcl_test/README', 'w') as f:
        ...     _ = f.write(textwrap.dedent("""
        ...             This is Foo.
        ...             """))

        >>> with open('pipcl_test/cli.py', 'w') as f:
        ...     _ = f.write(textwrap.dedent("""
        ...             def main():
        ...                 print('pipcl_test:main().')
        ...             if __name__ == '__main__':
        ...                 main()
        ...             """))

        >>> root = os.path.dirname(__file__)
        >>> _ = shutil.copy2(f'{root}/pipcl.py', 'pipcl_test/pipcl.py')
        >>> _ = shutil.copy2(f'{root}/wdev.py', 'pipcl_test/wdev.py')

    Use `setup.py`'s command-line interface to build and install the extension
    module into root `pipcl_test/install`.

        >>> _ = subprocess.run(
        ...         f'cd pipcl_test && {sys.executable} setup.py --root install install',
        ...         shell=1, check=1)

    The actual install directory depends on `sysconfig.get_path('platlib')`:

        >>> if windows():
        ...     install_dir = 'pipcl_test/install'
        ... else:
        ...     install_dir = f'pipcl_test/install/{sysconfig.get_path("platlib").lstrip(os.sep)}'
        >>> assert os.path.isfile( f'{install_dir}/foo/__init__.py')

    Create a test script which asserts that Python function call `foo.bar(s)`
    returns the length of `s`, and run it with `PYTHONPATH` set to the install
    directory:

        >>> with open('pipcl_test/test.py', 'w') as f:
        ...     _ = f.write(textwrap.dedent("""
        ...             import sys
        ...             import foo
        ...             text = 'hello'
        ...             print(f'test.py: calling foo.bar() with text={text!r}')
        ...             sys.stdout.flush()
        ...             l = foo.bar(text)
        ...             print(f'test.py: foo.bar() returned: {l}')
        ...             assert l == len(text)
        ...             """))
        >>> r = subprocess.run(
        ...         f'{sys.executable} pipcl_test/test.py',
        ...         shell=1, check=1, text=1,
        ...         stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        ...         env=os.environ | dict(PYTHONPATH=install_dir),
        ...         )
        >>> print(r.stdout)
        test.py: calling foo.bar() with text='hello'
        bar(): text: hello
        bar(): len=5
        test.py: foo.bar() returned: 5
        <BLANKLINE>

    Check that building sdist and wheel succeeds. For now we don't attempt to
    check that the sdist and wheel actually work.

        >>> _ = subprocess.run(
        ...         f'cd pipcl_test && {sys.executable} setup.py sdist',
        ...         shell=1, check=1)

        >>> _ = subprocess.run(
        ...         f'cd pipcl_test && {sys.executable} setup.py bdist_wheel',
        ...         shell=1, check=1)

    Check that rebuild does nothing.

        >>> t0 = os.path.getmtime('pipcl_test/build/foo.py')
        >>> _ = subprocess.run(
        ...         f'cd pipcl_test && {sys.executable} setup.py bdist_wheel',
        ...         shell=1, check=1)
        >>> t = os.path.getmtime('pipcl_test/build/foo.py')
        >>> assert t == t0

    Check that touching bar.i forces rebuild.

        >>> os.utime('pipcl_test/bar.i')
        >>> _ = subprocess.run(
        ...         f'cd pipcl_test && {sys.executable} setup.py bdist_wheel',
        ...         shell=1, check=1)
        >>> t = os.path.getmtime('pipcl_test/build/foo.py')
        >>> assert t > t0

    Check that touching foo.i.cpp does not run swig, but does recompile/link.

        >>> t0 = time.time()
        >>> os.utime('pipcl_test/build/foo.i.cpp')
        >>> _ = subprocess.run(
        ...         f'cd pipcl_test && {sys.executable} setup.py bdist_wheel',
        ...         shell=1, check=1)
        >>> assert os.path.getmtime('pipcl_test/build/foo.py') <= t0
        >>> so = glob.glob('pipcl_test/build/*.so')
        >>> assert len(so) == 1
        >>> so = so[0]
        >>> assert os.path.getmtime(so) > t0

    Check `entry_points` causes creation of command `foo_cli` when we install
    from our wheel using pip. [As of 2024-02-24 using pipcl's CLI interface
    directly with `setup.py install` does not support entry points.]

        >>> print('Creating venv.', file=sys.stderr)
        >>> _ = subprocess.run(
        ...         f'cd pipcl_test && {sys.executable} -m venv pylocal',
        ...         shell=1, check=1)

        >>> print('Installing from wheel into venv using pip.', file=sys.stderr)
        >>> _ = subprocess.run(
        ...         f'. pipcl_test/pylocal/bin/activate && pip install pipcl_test/dist/*.whl',
        ...         shell=1, check=1)

        >>> print('Running foo_cli.', file=sys.stderr)
        >>> _ = subprocess.run(
        ...         f'. pipcl_test/pylocal/bin/activate && foo_cli',
        ...         shell=1, check=1)

    Wheels and sdists

        Wheels:
            We generate wheels according to:
            https://packaging.python.org/specifications/binary-distribution-format/

            * `{name}-{version}.dist-info/RECORD` uses sha256 hashes.
            * We do not generate other `RECORD*` files such as
              `RECORD.jws` or `RECORD.p7s`.
            * `{name}-{version}.dist-info/WHEEL` has:

              * `Wheel-Version: 1.0`
              * `Root-Is-Purelib: false`
            * No support for signed wheels.

        Sdists:
            We generate sdist's according to:
            https://packaging.python.org/specifications/source-distribution-format/
    '''
    def __init__(self,
            name,
            version,
            *,
            platform = None,
            supported_platform = None,
            summary = None,
            description = None,
            description_content_type = None,
            keywords = None,
            home_page = None,
            download_url = None,
            author = None,
            author_email = None,
            maintainer = None,
            maintainer_email = None,
            license = None,
            classifier = None,
            requires_dist = None,
            requires_python = None,
            requires_external = None,
            project_url = None,
            provides_extra = None,

            entry_points = None,

            root = None,
            fn_build = None,
            fn_clean = None,
            fn_sdist = None,
            tag_python = None,
            tag_abi = None,
            tag_platform = None,
            py_limited_api = None,

            wheel_compression = zipfile.ZIP_DEFLATED,
            wheel_compresslevel = None,
            ):
        '''
        The initial args before `root` define the package
        metadata and closely follow the definitions in:
        https://packaging.python.org/specifications/core-metadata/

        Args:

            name:
                A string, the name of the Python package.
            version:
                A string, the version of the Python package. Also see PEP-440
                `Version Identification and Dependency Specification`.
            platform:
                A string or list of strings.
            supported_platform:
                A string or list of strings.
            summary:
                A string, short description of the package.
            description:
                A string. If contains newlines, a detailed description of the
                package. Otherwise the path of a file containing the detailed
                description of the package.
            description_content_type:
                A string describing markup of `description` arg. For example
                `text/markdown; variant=GFM`.
            keywords:
                A string containing comma-separated keywords.
            home_page:
                URL of home page.
            download_url:
                Where this version can be downloaded from.
            author:
                Author.
            author_email:
                Author email.
            maintainer:
                Maintainer.
            maintainer_email:
                Maintainer email.
            license:
                A string containing the license text. Written into metadata
                file `COPYING`. Is also written into metadata itself if not
                multi-line.
            classifier:
                A string or list of strings. Also see:

                * https://pypi.org/pypi?%3Aaction=list_classifiers
                * https://pypi.org/classifiers/

            requires_dist:
                A string or list of strings. Also see PEP-508.
            requires_python:
                A string or list of strings.
            requires_external:
                A string or list of strings.
            project_url:
                A string or list of strings, each of the form: `{name}, {url}`.
            provides_extra:
                A string or list of strings.

            entry_points:
                String or dict specifying *.dist-info/entry_points.txt, for
                example:

                    ```
                    [console_scripts]
                    foo_cli = foo.__main__:main
                    ```

                or:

                    { 'console_scripts': [
                        'foo_cli = foo.__main__:main',
                        ],
                    }

                See: https://packaging.python.org/en/latest/specifications/entry-points/

            root:
                Root of package, defaults to current directory.

            fn_build:
                A function taking no args, or a single `config_settings` dict
                arg (as described in PEP-517), that builds the package.

                Should return a list of items; each item should be a tuple
                `(from_, to_)`, or a single string `path` which is treated as
                the tuple `(path, path)`.

                `from_` can be a string or a `bytes`. If a string it should
                be the path to a file; a relative path is treated as relative
                to `root`. If a `bytes` it is the contents of the file to be
                added.

                `to_` identifies what the file should be called within a wheel
                or when installing. If `to_` ends with `/`, the leaf of `from_`
                is appended to it (and `from_` must not be a `bytes`).

                Initial `$dist-info/` in `_to` is replaced by
                `{name}-{version}.dist-info/`; this is useful for license files
                etc.

                Initial `$data/` in `_to` is replaced by
                `{name}-{version}.data/`. We do not enforce particular
                subdirectories, instead it is up to `fn_build()` to specify
                specific subdirectories such as `purelib`, `headers`,
                `scripts`, `data` etc.

                If we are building a wheel (e.g. `python setup.py bdist_wheel`,
                or PEP-517 pip calls `self.build_wheel()`), we add file `from_`
                to the wheel archive with name `to_`.

                If we are installing (e.g. `install` command in
                the argv passed to `self.handle_argv()`), then
                we copy `from_` to `{sitepackages}/{to_}`, where
                `sitepackages` is the installation directory, the
                default being `sysconfig.get_path('platlib')` e.g.
                `myvenv/lib/python3.9/site-packages/`.

            fn_clean:
                A function taking a single arg `all_` that cleans generated
                files. `all_` is true iff `--all` is in argv.

                For safety and convenience, can also returns a list of
                files/directory paths to be deleted. Relative paths are
                interpreted as relative to `root`. All paths are asserted to be
                within `root`.

            fn_sdist:
                A function taking no args, or a single `config_settings` dict
                arg (as described in PEP517), that returns a list of items to
                be copied into the sdist. The list should be in the same format
                as returned by `fn_build`.

                It can be convenient to use `pipcl.git_items()`.

                The specification for sdists requires that the list contains
                `pyproject.toml`; we enforce this with a diagnostic rather than
                raising an exception, to allow legacy command-line usage.

            tag_python:
                First element of wheel tag defined in PEP-425. If None we use
                `cp{version}`.

                For example if code works with any Python version, one can use
                'py3'.

            tag_abi:
                Second element of wheel tag defined in PEP-425. If None we use
                `none`.

            tag_platform:
                Third element of wheel tag defined in PEP-425. Default
                is `os.environ('AUDITWHEEL_PLAT')` if set, otherwise
                derived from `sysconfig.get_platform()` (was
                `setuptools.distutils.util.get_platform(), before that
                `distutils.util.get_platform()` as specified in the PEP), e.g.
                `openbsd_7_0_amd64`.

                For pure python packages use: `tag_platform=any`

            py_limited_api:
                If true we build wheels that use the Python Limited API. We use
                the version of `sys.executable` to define `Py_LIMITED_API` when
                compiling extensions, and use ABI tag `abi3` in the wheel name
                if argument `tag_abi` is None.

            wheel_compression:
                Used as `zipfile.ZipFile()`'s `compression` parameter when
                creating wheels.

            wheel_compresslevel:
                Used as `zipfile.ZipFile()`'s `compresslevel` parameter when
                creating wheels.

        '''
        assert name
        assert version

        def assert_str( v):
            if v is not None:
                assert isinstance( v, str), f'Not a string: {v!r}'
        def assert_str_or_multi( v):
            if v is not None:
                assert isinstance( v, (str, tuple, list)), f'Not a string, tuple or list: {v!r}'

        assert_str( name)
        assert_str( version)
        assert_str_or_multi( platform)
        assert_str_or_multi( supported_platform)
        assert_str( summary)
        assert_str( description)
        assert_str( description_content_type)
        assert_str( keywords)
        assert_str( home_page)
        assert_str( download_url)
        assert_str( author)
        assert_str( author_email)
        assert_str( maintainer)
        assert_str( maintainer_email)
        assert_str( license)
        assert_str_or_multi( classifier)
        assert_str_or_multi( requires_dist)
        assert_str( requires_python)
        assert_str_or_multi( requires_external)
        assert_str_or_multi( project_url)
        assert_str_or_multi( provides_extra)

        # https://packaging.python.org/en/latest/specifications/core-metadata/.
        assert re.match('([A-Z0-9]|[A-Z0-9][A-Z0-9._-]*[A-Z0-9])$', name, re.IGNORECASE), \
                f'Bad name: {name!r}'

        _assert_version_pep_440(version)

        # https://packaging.python.org/en/latest/specifications/binary-distribution-format/
        if tag_python:
            assert '-' not in tag_python
        if tag_abi:
            assert '-' not in tag_abi
        if tag_platform:
            assert '-' not in tag_platform

        self.name = name
        self.version = version
        self.platform = platform
        self.supported_platform = supported_platform
        self.summary = summary
        self.description = description
        self.description_content_type = description_content_type
        self.keywords = keywords
        self.home_page = home_page
        self.download_url = download_url
        self.author = author
        self.author_email  = author_email
        self.maintainer = maintainer
        self.maintainer_email = maintainer_email
        self.license = license
        self.classifier = classifier
        self.requires_dist = requires_dist
        self.requires_python = requires_python
        self.requires_external = requires_external
        self.project_url = project_url
        self.provides_extra = provides_extra
        self.entry_points = entry_points

        self.root = os.path.abspath(root if root else os.getcwd())
        self.fn_build = fn_build
        self.fn_clean = fn_clean
        self.fn_sdist = fn_sdist
        self.tag_python_ = tag_python
        self.tag_abi_ = tag_abi
        self.tag_platform_ = tag_platform
        self.py_limited_api = py_limited_api

        self.wheel_compression = wheel_compression
        self.wheel_compresslevel = wheel_compresslevel


    def build_wheel(self,
            wheel_directory,
            config_settings=None,
            metadata_directory=None,
            ):
        '''
        A PEP-517 `build_wheel()` function.

        Also called by `handle_argv()` to handle the `bdist_wheel` command.

        Returns leafname of generated wheel within `wheel_directory`.
        '''
        log2(
                f' wheel_directory={wheel_directory!r}'
                f' config_settings={config_settings!r}'
                f' metadata_directory={metadata_directory!r}'
                )

        wheel_name = self.wheel_name()
        path = f'{wheel_directory}/{wheel_name}'

        # Do a build and get list of files to copy into the wheel.
        #
        items = list()
        if self.fn_build:
            items = self._call_fn_build(config_settings)

        log2(f'Creating wheel: {path}')
        os.makedirs(wheel_directory, exist_ok=True)
        record = _Record()
        with zipfile.ZipFile(path, 'w', self.wheel_compression, self.wheel_compresslevel) as z:

            def add(from_, to_):
                if isinstance(from_, str):
                    z.write(from_, to_)
                    record.add_file(from_, to_)
                elif isinstance(from_, bytes):
                    z.writestr(to_, from_)
                    record.add_content(from_, to_)
                else:
                    assert 0

            def add_str(content, to_):
                add(content.encode('utf8'), to_)

            dist_info_dir = self._dist_info_dir()

            # Add the files returned by fn_build().
            #
            for item in items:
                from_, (to_abs, to_rel) = self._fromto(item)
                add(from_, to_rel)

            # Add <name>-<version>.dist-info/WHEEL.
            #
            add_str(
                    f'Wheel-Version: 1.0\n'
                    f'Generator: pipcl\n'
                    f'Root-Is-Purelib: false\n'
                    f'Tag: {self.wheel_tag_string()}\n'
                    ,
                    f'{dist_info_dir}/WHEEL',
                    )
            # Add <name>-<version>.dist-info/METADATA.
            #
            add_str(self._metainfo(), f'{dist_info_dir}/METADATA')

            # Add <name>-<version>.dist-info/COPYING.
            if self.license:
                add_str(self.license, f'{dist_info_dir}/COPYING')

            # Add <name>-<version>.dist-info/entry_points.txt.
            entry_points_text = self._entry_points_text()
            if entry_points_text:
                add_str(entry_points_text, f'{dist_info_dir}/entry_points.txt')

            # Update <name>-<version>.dist-info/RECORD. This must be last.
            #
            z.writestr(f'{dist_info_dir}/RECORD', record.get(f'{dist_info_dir}/RECORD'))

        st = os.stat(path)
        log1( f'Have created wheel size={st.st_size}: {path}')
        if g_verbose >= 2:
            with zipfile.ZipFile(path, compression=self.wheel_compression) as z:
                log2(f'Contents are:')
                for zi in sorted(z.infolist(), key=lambda z: z.filename):
                    log2(f'    {zi.file_size: 10d} {zi.filename}')

        return os.path.basename(path)


    def build_sdist(self,
            sdist_directory,
            formats,
            config_settings=None,
            ):
        '''
        A PEP-517 `build_sdist()` function.

        Also called by `handle_argv()` to handle the `sdist` command.

        Returns leafname of generated archive within `sdist_directory`.
        '''
        log2(
                f' sdist_directory={sdist_directory!r}'
                f' formats={formats!r}'
                f' config_settings={config_settings!r}'
                )
        if formats and formats != 'gztar':
            raise Exception( f'Unsupported: formats={formats}')
        items = list()
        if self.fn_sdist:
            if inspect.signature(self.fn_sdist).parameters:
                items = self.fn_sdist(config_settings)
            else:
                items = self.fn_sdist()

        prefix = f'{self.name}-{self.version}'
        os.makedirs(sdist_directory, exist_ok=True)
        tarpath = f'{sdist_directory}/{prefix}.tar.gz'
        log2(f'Creating sdist: {tarpath}')

        with tarfile.open(tarpath, 'w:gz') as tar:

            names_in_tar = list()
            def check_name(name):
                if name in names_in_tar:
                    raise Exception(f'Name specified twice: {name}')
                names_in_tar.append(name)

            def add(from_, name):
                check_name(name)
                if isinstance(from_, str):
                    log2( f'Adding file: {os.path.relpath(from_)} => {name}')
                    tar.add( from_, f'{prefix}/{name}', recursive=False)
                elif isinstance(from_, bytes):
                    log2( f'Adding: {name}')
                    ti = tarfile.TarInfo(f'{prefix}/{name}')
                    ti.size = len(from_)
                    ti.mtime = time.time()
                    tar.addfile(ti, io.BytesIO(from_))
                else:
                    assert 0

            def add_string(text, name):
                textb = text.encode('utf8')
                return add(textb, name)

            found_pyproject_toml = False
            for item in items:
                from_, (to_abs, to_rel) = self._fromto(item)
                if isinstance(from_, bytes):
                    add(from_, to_rel)
                else:
                    if from_.startswith(f'{os.path.abspath(sdist_directory)}/'):
                        # Source files should not be inside <sdist_directory>.
                        assert 0, f'Path is inside sdist_directory={sdist_directory}: {from_!r}'
                    assert os.path.exists(from_), f'Path does not exist: {from_!r}'
                    assert os.path.isfile(from_), f'Path is not a file: {from_!r}'
                    if to_rel == 'pyproject.toml':
                        found_pyproject_toml = True
                    add(from_, to_rel)

            if not found_pyproject_toml:
                log0(f'Warning: no pyproject.toml specified.')

            # Always add a PKG-INFO file.
            add_string(self._metainfo(), 'PKG-INFO')

            if self.license:
                if 'COPYING' in names_in_tar:
                    log2(f'Not writing .license because file already in sdist: COPYING')
                else:
                    add_string(self.license, 'COPYING')

        log1( f'Have created sdist: {tarpath}')
        return os.path.basename(tarpath)

    def wheel_tag_string(self):
        '''
        Returns <tag_python>-<tag_abi>-<tag_platform>.
        '''
        return f'{self.tag_python()}-{self.tag_abi()}-{self.tag_platform()}'

    def tag_python(self):
        '''
        Get two-digit python version, e.g. 'cp3.8' for python-3.8.6.
        '''
        if self.tag_python_:
            return self.tag_python_
        else:
            return 'cp' + ''.join(platform.python_version().split('.')[:2])

    def tag_abi(self):
        '''
        ABI tag.
        '''
        if self.tag_abi_:
            return self.tag_abi_
        elif self.py_limited_api:
            return 'abi3'
        else:
            return 'none'

    def tag_platform(self):
        '''
        Find platform tag used in wheel filename.
        '''
        ret = self.tag_platform_
        log0(f'From self.tag_platform_: {ret=}.')
        
        if not ret:
            # Prefer this to PEP-425. Appears to be undocumented,
            # but set in manylinux docker images and appears
            # to be used by cibuildwheel and auditwheel, e.g.
            # https://github.com/rapidsai/shared-action-workflows/issues/80
            ret = os.environ.get( 'AUDITWHEEL_PLAT')
            log0(f'From AUDITWHEEL_PLAT: {ret=}.')

        if not ret:
            # Notes:
            #
            # PEP-425. On Linux gives `linux_x86_64` which is rejected by
            # pypi.org.
            #
            # On local MacOS/arm64 mac-mini have seen sysconfig.get_platform()
            # unhelpfully return `macosx-10.9-universal2` if `python3` is the
            # system Python /usr/bin/python3; this happens if we source `.
            # /etc/profile`.
            #
            ret = sysconfig.get_platform()
            ret = ret.replace('-', '_').replace('.', '_').lower()
            log0(f'From sysconfig.get_platform(): {ret=}.')

            # We need to patch things on MacOS.
            #
            # E.g. `foo-1.2.3-cp311-none-macosx_13_x86_64.whl`
            # causes `pip` to fail with: `not a supported wheel on this
            # platform`. We seem to need to add `_0` to the OS version.
            #
            m = re.match( '^(macosx_[0-9]+)(_[^0-9].+)$', ret)
            if m:
                ret2 = f'{m.group(1)}_0{m.group(2)}'
                log0(f'After macos patch, changing from {ret!r} to {ret2!r}.')
                ret = ret2

        log0( f'tag_platform(): returning {ret=}.')
        return ret

    def wheel_name(self):
        return f'{self.name}-{self.version}-{self.tag_python()}-{self.tag_abi()}-{self.tag_platform()}.whl'

    def wheel_name_match(self, wheel):
        '''
        Returns true if `wheel` matches our wheel. We basically require the
        name to be the same, except that we accept platform tags that contain
        extra items (see pep-0600/), for example we return true with:

            self:   foo-cp38-none-manylinux2014_x86_64.whl
            wheel:  foo-cp38-none-manylinux2014_x86_64.manylinux_2_17_x86_64.whl
        '''
        log2(f'{wheel=}')
        assert wheel.endswith('.whl')
        wheel2 = wheel[:-len('.whl')]
        name, version, tag_python, tag_abi, tag_platform = wheel2.split('-')
        
        py_limited_api_compatible = False
        if self.py_limited_api and tag_abi == 'abi3':
            # Allow lower tag_python number.
            m = re.match('cp([0-9]+)', tag_python)
            tag_python_int = int(m.group(1))
            m = re.match('cp([0-9]+)', self.tag_python())
            tag_python_int_self = int(m.group(1))
            if tag_python_int <= tag_python_int_self:
                # This wheel uses Python stable ABI same or older than ours, so
                # we can use it.
                log2(f'py_limited_api; {tag_python=} compatible with {self.tag_python()=}.')
                py_limited_api_compatible = True
            
        log2(f'{self.name == name=}')
        log2(f'{self.version == version=}')
        log2(f'{self.tag_python() == tag_python=} {self.tag_python()=} {tag_python=}')
        log2(f'{py_limited_api_compatible=}')
        log2(f'{self.tag_abi() == tag_abi=}')
        log2(f'{self.tag_platform() in tag_platform.split(".")=}')
        log2(f'{self.tag_platform()=}')
        log2(f'{tag_platform.split(".")=}')
        ret = (1
                and self.name == name
                and self.version == version
                and (self.tag_python() == tag_python or py_limited_api_compatible)
                and self.tag_abi() == tag_abi
                and self.tag_platform() in tag_platform.split('.')
                )
        log2(f'Returning {ret=}.')
        return ret
    
    def _entry_points_text(self):
        if self.entry_points:
            if isinstance(self.entry_points, str):
                return self.entry_points
            ret = ''
            for key, values in self.entry_points.items():
                ret += f'[{key}]\n'
                for value in values:
                    ret += f'{value}\n'
            return ret

    def _call_fn_build( self, config_settings=None):
        assert self.fn_build
        log2(f'calling self.fn_build={self.fn_build}')
        if inspect.signature(self.fn_build).parameters:
            ret = self.fn_build(config_settings)
        else:
            ret = self.fn_build()
        assert isinstance( ret, (list, tuple)), \
                f'Expected list/tuple from {self.fn_build} but got: {ret!r}'
        return ret


    def _argv_clean(self, all_):
        '''
        Called by `handle_argv()`.
        '''
        if not self.fn_clean:
            return
        paths = self.fn_clean(all_)
        if paths:
            if isinstance(paths, str):
                paths = paths,
            for path in paths:
                if not os.path.isabs(path):
                    path = ps.path.join(self.root, path)
                path = os.path.abspath(path)
                assert path.startswith(self.root+os.sep), \
                        f'path={path!r} does not start with root={self.root+os.sep!r}'
                log2(f'Removing: {path}')
                shutil.rmtree(path, ignore_errors=True)


    def install(self, record_path=None, root=None):
        '''
        Called by `handle_argv()` to handle `install` command..
        '''
        log2( f'{record_path=} {root=}')

        # Do a build and get list of files to install.
        #
        items = list()
        if self.fn_build:
            items = self._call_fn_build( dict())

        root2 = install_dir(root)
        log2( f'{root2=}')

        log1( f'Installing into: {root2!r}')
        dist_info_dir = self._dist_info_dir()

        if not record_path:
            record_path = f'{root2}/{dist_info_dir}/RECORD'
        record = _Record()

        def add_file(from_, to_abs, to_rel):
            os.makedirs( os.path.dirname( to_abs), exist_ok=True)
            if isinstance(from_, bytes):
                log2(f'Copying content into {to_abs}.')
                with open(to_abs, 'wb') as f:
                    f.write(from_)
                record.add_content(from_, to_rel)
            else:
                log0(f'{from_=}')
                log2(f'Copying from {os.path.relpath(from_, self.root)} to {to_abs}')
                shutil.copy2( from_, to_abs)
                record.add_file(from_, to_rel)

        def add_str(content, to_abs, to_rel):
            log2( f'Writing to: {to_abs}')
            os.makedirs( os.path.dirname( to_abs), exist_ok=True)
            with open( to_abs, 'w') as f:
                f.write( content)
            record.add_content(content, to_rel)

        for item in items:
            from_, (to_abs, to_rel) = self._fromto(item)
            log0(f'{from_=} {to_abs=} {to_rel=}')
            to_abs2 = f'{root2}/{to_rel}'
            add_file( from_, to_abs2, to_rel)

        add_str( self._metainfo(), f'{root2}/{dist_info_dir}/METADATA', f'{dist_info_dir}/METADATA')

        if self.license:
            add_str( self.license, f'{root2}/{dist_info_dir}/COPYING', f'{dist_info_dir}/COPYING')

        entry_points_text = self._entry_points_text()
        if entry_points_text:
            add_str(
                    entry_points_text,
                    f'{root2}/{dist_info_dir}/entry_points.txt',
                    f'{dist_info_dir}/entry_points.txt',
                    )

        log2( f'Writing to: {record_path}')
        with open(record_path, 'w') as f:
            f.write(record.get())

        log2(f'Finished.')


    def _argv_dist_info(self, root):
        '''
        Called by `handle_argv()`. There doesn't seem to be any documentation
        for `setup.py dist_info`, but it appears to be like `egg_info` except
        it writes to a slightly different directory.
        '''
        if root is None:
            root = f'{self.name}-{self.version}.dist-info'
        self._write_info(f'{root}/METADATA')
        if self.license:
            with open( f'{root}/COPYING', 'w') as f:
                f.write( self.license)


    def _argv_egg_info(self, egg_base):
        '''
        Called by `handle_argv()`.
        '''
        if egg_base is None:
            egg_base = '.'
        self._write_info(f'{egg_base}/.egg-info')


    def _write_info(self, dirpath=None):
        '''
        Writes egg/dist info to files in directory `dirpath` or `self.root` if
        `None`.
        '''
        if dirpath is None:
            dirpath = self.root
        log2(f'Creating files in directory {dirpath}')
        os.makedirs(dirpath, exist_ok=True)
        with open(os.path.join(dirpath, 'PKG-INFO'), 'w') as f:
            f.write(self._metainfo())

        # These don't seem to be required?
        #
        #with open(os.path.join(dirpath, 'SOURCES.txt', 'w') as f:
        #    pass
        #with open(os.path.join(dirpath, 'dependency_links.txt', 'w') as f:
        #    pass
        #with open(os.path.join(dirpath, 'top_level.txt', 'w') as f:
        #    f.write(f'{self.name}\n')
        #with open(os.path.join(dirpath, 'METADATA', 'w') as f:
        #    f.write(self._metainfo())


    def handle_argv(self, argv):
        '''
        Attempt to handles old-style (pre PEP-517) command line passed by
        old releases of pip to a `setup.py` script, and manual running of
        `setup.py`.

        This is partial support at best.
        '''
        global g_verbose
        #log2(f'argv: {argv}')

        class ArgsRaise:
            pass

        class Args:
            '''
            Iterates over argv items.
            '''
            def __init__( self, argv):
                self.items = iter( argv)
            def next( self, eof=ArgsRaise):
                '''
                Returns next arg. If no more args, we return <eof> or raise an
                exception if <eof> is ArgsRaise.
                '''
                try:
                    return next( self.items)
                except StopIteration:
                    if eof is ArgsRaise:
                        raise Exception('Not enough args')
                    return eof

        command = None
        opt_all = None
        opt_dist_dir = 'dist'
        opt_egg_base = None
        opt_formats = None
        opt_install_headers = None
        opt_record = None
        opt_root = None

        args = Args(argv[1:])

        while 1:
            arg = args.next(None)
            if arg is None:
                break

            elif arg in ('-h', '--help', '--help-commands'):
                log0(textwrap.dedent('''
                        Usage:
                            [<options>...] <command> [<options>...]
                        Commands:
                            bdist_wheel
                                Creates a wheel called
                                <dist-dir>/<name>-<version>-<details>.whl, where
                                <dist-dir> is "dist" or as specified by --dist-dir,
                                and <details> encodes ABI and platform etc.
                            clean
                                Cleans build files.
                            dist_info
                                Creates files in <name>-<version>.dist-info/ or
                                directory specified by --egg-base.
                            egg_info
                                Creates files in .egg-info/ or directory
                                directory specified by --egg-base.
                            install
                                Builds and installs. Writes installation
                                information to <record> if --record was
                                specified.
                            sdist
                                Make a source distribution:
                                    <dist-dir>/<name>-<version>.tar.gz
                        Options:
                            --all
                                Used by "clean".
                            --compile
                                Ignored.
                            --dist-dir | -d <dist-dir>
                                Default is "dist".
                            --egg-base <egg-base>
                                Used by "egg_info".
                            --formats <formats>
                                Used by "sdist".
                            --install-headers <directory>
                                Ignored.
                            --python-tag <python-tag>
                                Ignored.
                            --record <record>
                                Used by "install".
                            --root <path>
                                Used by "install".
                            --single-version-externally-managed
                                Ignored.
                            --verbose -v
                                Extra diagnostics.
                        Other:
                            windows-vs [-y <year>] [-v <version>] [-g <grade] [--verbose]
                                Windows only; looks for matching Visual Studio.
                            windows-python [-v <version>] [--verbose]
                                Windows only; looks for matching Python.
                        '''))
                return

            elif arg in ('bdist_wheel', 'clean', 'dist_info', 'egg_info', 'install', 'sdist'):
                assert command is None, 'Two commands specified: {command} and {arg}.'
                command = arg

            elif arg == '--all':                                opt_all = True
            elif arg == '--compile':                            pass
            elif arg == '--dist-dir' or arg == '-d':            opt_dist_dir = args.next()
            elif arg == '--egg-base':                           opt_egg_base = args.next()
            elif arg == '--formats':                            opt_formats = args.next()
            elif arg == '--install-headers':                    opt_install_headers = args.next()
            elif arg == '--python-tag':                         pass
            elif arg == '--record':                             opt_record = args.next()
            elif arg == '--root':                               opt_root = args.next()
            elif arg == '--single-version-externally-managed':  pass
            elif arg == '--verbose' or arg == '-v':             g_verbose += 1

            elif arg == 'windows-vs':
                command = arg
                break
            elif arg == 'windows-python':
                command = arg
                break
            else:
               raise Exception(f'Unrecognised arg: {arg}')

        assert command, 'No command specified'

        log1(f'Handling command={command}')
        if 0:   pass
        elif command == 'bdist_wheel':  self.build_wheel(opt_dist_dir)
        elif command == 'clean':        self._argv_clean(opt_all)
        elif command == 'dist_info':    self._argv_dist_info(opt_egg_base)
        elif command == 'egg_info':     self._argv_egg_info(opt_egg_base)
        elif command == 'install':      self.install(opt_record, opt_root)
        elif command == 'sdist':        self.build_sdist(opt_dist_dir, opt_formats)

        elif command == 'windows-python':
            version = None
            while 1:
                arg = args.next(None)
                if arg is None:
                    break
                elif arg == '-v':
                    version = args.next()
                elif arg == '--verbose':
                    g_verbose += 1
                else:
                    assert 0, f'Unrecognised {arg=}'
            python = wdev.WindowsPython(version=version)
            print(f'Python is:\n{python.description_ml("    ")}')

        elif command == 'windows-vs':
            grade = None
            version = None
            year = None
            while 1:
                arg = args.next(None)
                if arg is None:
                    break
                elif arg == '-g':
                    grade = args.next()
                elif arg == '-v':
                    version = args.next()
                elif arg == '-y':
                    year = args.next()
                elif arg == '--verbose':
                    g_verbose += 1
                else:
                    assert 0, f'Unrecognised {arg=}'
            vs = wdev.WindowsVS(year=year, grade=grade, version=version)
            print(f'Visual Studio is:\n{vs.description_ml("    ")}')

        else:
            assert 0, f'Unrecognised command: {command}'

        log2(f'Finished handling command: {command}')


    def __str__(self):
        return ('{'
            f'name={self.name!r}'
            f' version={self.version!r}'
            f' platform={self.platform!r}'
            f' supported_platform={self.supported_platform!r}'
            f' summary={self.summary!r}'
            f' description={self.description!r}'
            f' description_content_type={self.description_content_type!r}'
            f' keywords={self.keywords!r}'
            f' home_page={self.home_page!r}'
            f' download_url={self.download_url!r}'
            f' author={self.author!r}'
            f' author_email={self.author_email!r}'
            f' maintainer={self.maintainer!r}'
            f' maintainer_email={self.maintainer_email!r}'
            f' license={self.license!r}'
            f' classifier={self.classifier!r}'
            f' requires_dist={self.requires_dist!r}'
            f' requires_python={self.requires_python!r}'
            f' requires_external={self.requires_external!r}'
            f' project_url={self.project_url!r}'
            f' provides_extra={self.provides_extra!r}'

            f' root={self.root!r}'
            f' fn_build={self.fn_build!r}'
            f' fn_sdist={self.fn_sdist!r}'
            f' fn_clean={self.fn_clean!r}'
            f' tag_python={self.tag_python_!r}'
            f' tag_abi={self.tag_abi_!r}'
            f' tag_platform={self.tag_platform_!r}'
            '}'
            )

    def _dist_info_dir( self):
        return f'{self.name}-{self.version}.dist-info'

    def _metainfo(self):
        '''
        Returns text for `.egg-info/PKG-INFO` file, or `PKG-INFO` in an sdist
        `.tar.gz` file, or `...dist-info/METADATA` in a wheel.
        '''
        # 2021-04-30: Have been unable to get multiline content working on
        # test.pypi.org so we currently put the description as the body after
        # all the other headers.
        #
        ret = ['']
        def add(key, value):
            if value is None:
                return
            if isinstance( value, (tuple, list)):
                for v in value:
                    add( key, v)
                return
            if key == 'License' and '\n' in value:
                # This is ok because we write `self.license` into
                # *.dist-info/COPYING.
                #
                log1( f'Omitting license because contains newline(s).')
                return
            assert '\n' not in value, f'key={key} value contains newline: {value!r}'
            if key == 'Project-URL':
                assert value.count(',') == 1, f'For {key=}, should have one comma in {value!r}.'
            ret[0] += f'{key}: {value}\n'
        #add('Description', self.description)
        add('Metadata-Version', '2.1')

        # These names are from:
        # https://packaging.python.org/specifications/core-metadata/
        #
        for name in (
                'Name',
                'Version',
                'Platform',
                'Supported-Platform',
                'Summary',
                'Description-Content-Type',
                'Keywords',
                'Home-page',
                'Download-URL',
                'Author',
                'Author-email',
                'Maintainer',
                'Maintainer-email',
                'License',
                'Classifier',
                'Requires-Dist',
                'Requires-Python',
                'Requires-External',
                'Project-URL',
                'Provides-Extra',
                ):
            identifier = name.lower().replace( '-', '_')
            add( name, getattr( self, identifier))

        ret = ret[0]

        # Append description as the body
        if self.description:
            if '\n' in self.description:
                description_text = self.description.strip()
            else:
                with open(self.description) as f:
                    description_text = f.read()
            ret += '\n' # Empty line separates headers from body.
            ret += description_text
            ret += '\n'
        return ret

    def _path_relative_to_root(self, path, assert_within_root=True):
        '''
        Returns `(path_abs, path_rel)`, where `path_abs` is absolute path and
        `path_rel` is relative to `self.root`.

        Interprets `path` as relative to `self.root` if not absolute.

        We use `os.path.realpath()` to resolve any links.

        if `assert_within_root` is true, assert-fails if `path` is not within
        `self.root`.
        '''
        if os.path.isabs(path):
            p = path
        else:
            p = os.path.join(self.root, path)
        p = os.path.realpath(os.path.abspath(p))
        if assert_within_root:
            assert p.startswith(self.root+os.sep) or p == self.root, \
                    f'Path not within root={self.root+os.sep!r}: {path=} {p=}'
        p_rel = os.path.relpath(p, self.root)
        return p, p_rel

    def _fromto(self, p):
        '''
        Returns `(from_, (to_abs, to_rel))`.

        If `p` is a string we convert to `(p, p)`. Otherwise we assert that
        `p` is a tuple `(from_, to_)` where `from_` is str/bytes and `to_` is
        str. If `from_` is a bytes it is contents of file to add, otherwise the
        path of an existing file; non-absolute paths are assumed to be relative
        to `self.root`. If `to_` is empty or ends with `/`, we append the leaf
        of `from_` (which must be a str).

        If `to_` starts with `$dist-info/`, we replace this with
        `self._dist_info_dir()`.

        If `to_` starts with `$data/`, we replace this with
        `{self.name}-{self.version}.data/`.

        We assert that `to_abs` is `within self.root`.

        `to_rel` is derived from the `to_abs` and is relative to self.root`.
        '''
        ret = None
        if isinstance(p, str):
            p = p, p
        assert isinstance(p, tuple) and len(p) == 2

        from_, to_ = p
        assert isinstance(from_, (str, bytes))
        assert isinstance(to_, str)
        if to_.endswith('/') or to_=='':
            to_ += os.path.basename(from_)
        prefix = '$dist-info/'
        if to_.startswith( prefix):
            to_ = f'{self._dist_info_dir()}/{to_[ len(prefix):]}'
        prefix = '$data/'
        if to_.startswith( prefix):
            to_ = f'{self.name}-{self.version}.data/{to_[ len(prefix):]}'
        if isinstance(from_, str):
            from_, _ = self._path_relative_to_root( from_, assert_within_root=False)
        to_ = self._path_relative_to_root(to_)
        assert isinstance(from_, (str, bytes))
        log2(f'returning {from_=} {to_=}')
        return from_, to_


def build_extension(
        name,
        path_i,
        outdir,
        builddir=None,
        includes=None,
        defines=None,
        libpaths=None,
        libs=None,
        optimise=True,
        debug=False,
        compiler_extra='',
        linker_extra='',
        swig='swig',
        cpp=True,
        prerequisites_swig=None,
        prerequisites_compile=None,
        prerequisites_link=None,
        infer_swig_includes=True,
        py_limited_api=False,
        ):
    '''
    Builds a Python extension module using SWIG. Works on Windows, Linux, MacOS
    and OpenBSD.

    On Unix, sets rpath when linking shared libraries.

    Args:
        name:
            Name of generated extension module.
        path_i:
            Path of input SWIG `.i` file. Internally we use swig to generate a
            corresponding `.c` or `.cpp` file.
        outdir:
            Output directory for generated files:

                * `{outdir}/{name}.py`
                * `{outdir}/_{name}.so`     # Unix
                * `{outdir}/_{name}.*.pyd`  # Windows
            We return the leafname of the `.so` or `.pyd` file.
        builddir:
            Where to put intermediate files, for example the .cpp file
            generated by swig and `.d` dependency files. Default is `outdir`.
        includes:
            A string, or a sequence of extra include directories to be prefixed
            with `-I`.
        defines:
            A string, or a sequence of extra preprocessor defines to be
            prefixed with `-D`.
        libpaths
            A string, or a sequence of library paths to be prefixed with
            `/LIBPATH:` on Windows or `-L` on Unix.
        libs
            A string, or a sequence of library names. Each item is prefixed
            with `-l` on non-Windows.
        optimise:
            Whether to use compiler optimisations.
        debug:
            Whether to build with debug symbols.
        compiler_extra:
            Extra compiler flags. Can be None.
        linker_extra:
            Extra linker flags. Can be None.
        swig:
            Base swig command.
        cpp:
            If true we tell SWIG to generate C++ code instead of C.
        prerequisites_swig:
        prerequisites_compile:
        prerequisites_link:

            [These are mainly for use on Windows. On other systems we
            automatically generate dynamic dependencies using swig/compile/link
            commands' `-MD` and `-MF` args.]

            Sequences of extra input files/directories that should force
            running of swig, compile or link commands if they are newer than
            any existing generated SWIG `.i` file, compiled object file or
            shared library file.

            If present, the first occurrence of `True` or `False` forces re-run
            or no re-run. Any occurrence of None is ignored. If an item is a
            directory path we look for newest file within the directory tree.

            If not a sequence, we convert into a single-item list.

            prerequisites_swig

                We use swig's -MD and -MF args to generate dynamic dependencies
                automatically, so this is not usually required.

            prerequisites_compile
            prerequisites_link

                On non-Windows we use cc's -MF and -MF args to generate dynamic
                dependencies so this is not usually required.
        infer_swig_includes:
            If true, we extract `-I<path>` and `-I <path>` args from
            `compile_extra` (also `/I` on windows) and use them with swig so
            that it can see the same header files as C/C++. This is useful
            when using enviromment variables such as `CC` and `CXX` to set
            `compile_extra.
        py_limited_api:
            If true we build for current Python's limited API / stable ABI.

    Returns the leafname of the generated library file within `outdir`, e.g.
    `_{name}.so` on Unix or `_{name}.cp311-win_amd64.pyd` on Windows.
    '''
    if compiler_extra is None:
        compiler_extra = ''
    if linker_extra is None:
        linker_extra = ''
    if builddir is None:
        builddir = outdir
    includes_text = _flags( includes, '-I')
    defines_text = _flags( defines, '-D')
    libpaths_text = _flags( libpaths, '/LIBPATH:', '"') if windows() else _flags( libpaths, '-L')
    libs_text = _flags( libs, '' if windows() else '-l')
    path_cpp = f'{builddir}/{os.path.basename(path_i)}'
    path_cpp += '.cpp' if cpp else '.c'
    os.makedirs( outdir, exist_ok=True)

    # Run SWIG.

    if infer_swig_includes:
        # Extract include flags from `compiler_extra`.
        swig_includes_extra = ''
        compiler_extra_items = compiler_extra.split()
        i = 0
        while i < len(compiler_extra_items):
            item = compiler_extra_items[i]
            # Swig doesn't seem to like a space after `I`.
            if item == '-I' or (windows() and item == '/I'):
                swig_includes_extra += f' -I{compiler_extra_items[i+1]}'
                i += 1
            elif item.startswith('-I') or (windows() and item.startswith('/I')):
                swig_includes_extra += f' -I{compiler_extra_items[i][2:]}'
            i += 1
        swig_includes_extra = swig_includes_extra.strip()
    deps_path = f'{path_cpp}.d'
    prerequisites_swig2 = _get_prerequisites( deps_path)
    run_if(
            f'''
            {swig}
                -Wall
                {"-c++" if cpp else ""}
                -python
                -module {name}
                -outdir {outdir}
                -o {path_cpp}
                -MD -MF {deps_path}
                {includes_text}
                {swig_includes_extra}
                {path_i}
            '''
            ,
            path_cpp,
            path_i,
            prerequisites_swig,
            prerequisites_swig2,
            )

    so_suffix = _so_suffix(use_so_versioning = not py_limited_api)
    path_so_leaf = f'_{name}{so_suffix}'
    path_so = f'{outdir}/{path_so_leaf}'

    py_limited_api2 = current_py_limited_api() if py_limited_api else None

    if windows():
        path_obj = f'{path_so}.obj'

        permissive = '/permissive-'
        EHsc = '/EHsc'
        T = '/Tp' if cpp else '/Tc'
        optimise2 = '/DNDEBUG /O2' if optimise else '/D_DEBUG'
        debug2 = ''
        if debug:
            debug2 = '/Zi'  # Generate .pdb.
            # debug2 = '/Z7'    # Embed debug info in .obj files.
        
        py_limited_api3 = f'/DPy_LIMITED_API={py_limited_api2}' if py_limited_api2 else ''

        # As of 2023-08-23, it looks like VS tools create slightly
        # .dll's each time, even with identical inputs.
        #
        # Some info about this is at:
        # https://nikhilism.com/post/2020/windows-deterministic-builds/.
        # E.g. an undocumented linker flag `/Brepro`.
        #

        command, pythonflags = base_compiler(cpp=cpp)
        command = f'''
                {command}
                    # General:
                    /c                          # Compiles without linking.
                    {EHsc}                      # Enable "Standard C++ exception handling".

                    #/MD                         # Creates a multithreaded DLL using MSVCRT.lib.
                    {'/MDd' if debug else '/MD'}

                    # Input/output files:
                    {T}{path_cpp}               # /Tp specifies C++ source file.
                    /Fo{path_obj}               # Output file. codespell:ignore

                    # Include paths:
                    {includes_text}
                    {pythonflags.includes}      # Include path for Python headers.

                    # Code generation:
                    {optimise2}
                    {debug2}
                    {permissive}                # Set standard-conformance mode.

                    # Diagnostics:
                    #/FC                         # Display full path of source code files passed to cl.exe in diagnostic text.
                    /W3                         # Sets which warning level to output. /W3 is IDE default.
                    /diagnostics:caret          # Controls the format of diagnostic messages.
                    /nologo                     #

                    {defines_text}
                    {compiler_extra}

                    {py_limited_api3}
                '''
        run_if( command, path_obj, path_cpp, prerequisites_compile)

        command, pythonflags = base_linker(cpp=cpp)
        debug2 = '/DEBUG' if debug else ''
        base, _ = os.path.splitext(path_so_leaf)
        command = f'''
                {command}
                    /DLL                    # Builds a DLL.
                    /EXPORT:PyInit__{name}  # Exports a function.
                    /IMPLIB:{base}.lib      # Overrides the default import library name.
                    {libpaths_text}
                    {pythonflags.ldflags}
                    /OUT:{path_so}          # Specifies the output file name.
                    {debug2}
                    /nologo
                    {libs_text}
                    {path_obj}
                    {linker_extra}
                '''
        run_if( command, path_so, path_obj, prerequisites_link)

    else:

        # Not Windows.
        #
        command, pythonflags = base_compiler(cpp=cpp)

        # setuptools on Linux seems to use slightly different compile flags:
        #
        # -fwrapv -O3 -Wall -O2 -g0 -DPY_CALL_TRAMPOLINE
        #

        general_flags = ''
        if debug:
            general_flags += ' -g'
        if optimise:
            general_flags += ' -O2 -DNDEBUG'

        py_limited_api3 = f'-DPy_LIMITED_API={py_limited_api2}' if py_limited_api2 else ''

        if darwin():
            # MacOS's linker does not like `-z origin`.
            rpath_flag = "-Wl,-rpath,@loader_path/"

            # Avoid `Undefined symbols for ... "_PyArg_UnpackTuple" ...'.
            general_flags += ' -undefined dynamic_lookup'
        elif pyodide():
            # Setting `-Wl,-rpath,'$ORIGIN',-z,origin` gives:
            #   emcc: warning: ignoring unsupported linker flag: `-rpath` [-Wlinkflags]
            #   wasm-ld: error: unknown -z value: origin
            #
            log0(f'pyodide: PEP-3149 suffix untested, so omitting. {_so_suffix()=}.')
            path_so_leaf = f'_{name}.so'
            path_so = f'{outdir}/{path_so_leaf}'

            rpath_flag = ''
        else:
            rpath_flag = "-Wl,-rpath,'$ORIGIN',-z,origin"
        path_so = f'{outdir}/{path_so_leaf}'
        # Fun fact - on Linux, if the -L and -l options are before '{path_cpp}'
        # they seem to be ignored...
        #
        prerequisites = list()

        if pyodide():
            # Looks like pyodide's `cc` can't compile and link in one invocation.
            prerequisites_compile_path = f'{path_cpp}.o.d'
            prerequisites += _get_prerequisites( prerequisites_compile_path)
            command = f'''
                    {command}
                        -fPIC
                        {general_flags.strip()}
                        {pythonflags.includes}
                        {includes_text}
                        {defines_text}
                        -MD -MF {prerequisites_compile_path}
                        -c {path_cpp}
                        -o {path_cpp}.o
                        {compiler_extra}
                        {py_limited_api3}
                    '''
            prerequisites_link_path = f'{path_cpp}.o.d'
            prerequisites += _get_prerequisites( prerequisites_link_path)
            ld, _ = base_linker(cpp=cpp)
            command += f'''
                    && {ld}
                        {path_cpp}.o
                        -o {path_so}
                        -MD -MF {prerequisites_link_path}
                        {rpath_flag}
                        {libpaths_text}
                        {libs_text}
                        {linker_extra}
                        {pythonflags.ldflags}
                    '''
        else:
            # We use compiler to compile and link in one command.
            prerequisites_path = f'{path_so}.d'
            prerequisites = _get_prerequisites(prerequisites_path)

            command = f'''
                    {command}
                        -fPIC
                        -shared
                        {general_flags.strip()}
                        {pythonflags.includes}
                        {includes_text}
                        {defines_text}
                        {path_cpp}
                        -MD -MF {prerequisites_path}
                        -o {path_so}
                        {compiler_extra}
                        {libpaths_text}
                        {linker_extra}
                        {pythonflags.ldflags}
                        {libs_text}
                        {rpath_flag}
                        {py_limited_api3}
                    '''
        command_was_run = run_if(
                command,
                path_so,
                path_cpp,
                prerequisites_compile,
                prerequisites_link,
                prerequisites,
                )

        if command_was_run and darwin():
            # We need to patch up references to shared libraries in `libs`.
            sublibraries = list()
            for lib in () if libs is None else libs:
                for libpath in libpaths:
                    found = list()
                    for suffix in '.so', '.dylib':
                        path = f'{libpath}/lib{os.path.basename(lib)}{suffix}'
                        if os.path.exists( path):
                            found.append( path)
                    if found:
                        assert len(found) == 1, f'More than one file matches lib={lib!r}: {found}'
                        sublibraries.append( found[0])
                        break
                else:
                    log2(f'Warning: can not find path of lib={lib!r} in libpaths={libpaths}')
            macos_patch( path_so, *sublibraries)

        #run(f'ls -l {path_so}', check=0)
        #run(f'file {path_so}', check=0)

    return path_so_leaf


# Functions that might be useful.
#


def base_compiler(vs=None, pythonflags=None, cpp=False, use_env=True):
    '''
    Returns basic compiler command and PythonFlags.

    Args:
        vs:
            Windows only. A `wdev.WindowsVS` instance or None to use default
            `wdev.WindowsVS` instance.
        pythonflags:
            A `pipcl.PythonFlags` instance or None to use default
            `pipcl.PythonFlags` instance.
        cpp:
            If true we return C++ compiler command instead of C. On Windows
            this has no effect - we always return `cl.exe`.
        use_env:
            If true we return '$CC' or '$CXX' if the corresponding
            environmental variable is set (without evaluating with `getenv()`
            or `os.environ`).

    Returns `(cc, pythonflags)`:
        cc:
            C or C++ command. On Windows this is of the form
            `{vs.vcvars}&&{vs.cl}`; otherwise it is typically `cc` or `c++`.
        pythonflags:
            The `pythonflags` arg or a new `pipcl.PythonFlags` instance.
    '''
    if not pythonflags:
        pythonflags = PythonFlags()
    cc = None
    if use_env:
        if cpp:
            if os.environ.get( 'CXX'):
                cc = '$CXX'
        else:
            if os.environ.get( 'CC'):
                cc = '$CC'
    if cc:
        pass
    elif windows():
        if not vs:
            vs = wdev.WindowsVS()
        cc = f'"{vs.vcvars}"&&"{vs.cl}"'
    elif wasm():
        cc = 'em++' if cpp else 'emcc'
    else:
        cc = 'c++' if cpp else 'cc'
    cc = macos_add_cross_flags( cc)
    return cc, pythonflags


def base_linker(vs=None, pythonflags=None, cpp=False, use_env=True):
    '''
    Returns basic linker command.

    Args:
        vs:
            Windows only. A `wdev.WindowsVS` instance or None to use default
            `wdev.WindowsVS` instance.
        pythonflags:
            A `pipcl.PythonFlags` instance or None to use default
            `pipcl.PythonFlags` instance.
        cpp:
            If true we return C++ linker command instead of C. On Windows this
            has no effect - we always return `link.exe`.
        use_env:
            If true we use `os.environ['LD']` if set.

    Returns `(linker, pythonflags)`:
        linker:
            Linker command. On Windows this is of the form
            `{vs.vcvars}&&{vs.link}`; otherwise it is typically `cc` or `c++`.
        pythonflags:
            The `pythonflags` arg or a new `pipcl.PythonFlags` instance.
    '''
    if not pythonflags:
        pythonflags = PythonFlags()
    linker = None
    if use_env:
        if os.environ.get( 'LD'):
            linker = '$LD'
    if linker:
        pass
    elif windows():
        if not vs:
            vs = wdev.WindowsVS()
        linker = f'"{vs.vcvars}"&&"{vs.link}"'
    elif wasm():
        linker = 'em++' if cpp else 'emcc'
    else:
        linker = 'c++' if cpp else 'cc'
    linker = macos_add_cross_flags( linker)
    return linker, pythonflags


def git_items( directory, submodules=False):
    '''
    Returns list of paths for all files known to git within a `directory`.

    Args:
        directory:
            Must be somewhere within a git checkout.
        submodules:
            If true we also include git submodules.

    Returns:
        A list of paths for all files known to git within `directory`. Each
        path is relative to `directory`. `directory` must be somewhere within a
        git checkout.

    We run a `git ls-files` command internally.

    This function can be useful for the `fn_sdist()` callback.
    '''
    command = 'cd ' + directory + ' && git ls-files'
    if submodules:
        command += ' --recurse-submodules'
    log1(f'Running {command=}')
    text = subprocess.check_output( command, shell=True)
    ret = []
    for path in text.decode('utf8').strip().split( '\n'):
        path2 = os.path.join(directory, path)
        # Sometimes git ls-files seems to list empty/non-existent directories
        # within submodules.
        #
        if not os.path.exists(path2):
            log2(f'Ignoring git ls-files item that does not exist: {path2}')
        elif os.path.isdir(path2):
            log2(f'Ignoring git ls-files item that is actually a directory: {path2}')
        else:
            ret.append(path)
    return ret


def run(
        command,
        *,
        capture=False,
        check=1,
        verbose=1,
        env_extra=None,
        timeout=None,
        caller=1,
        ):
    '''
    Runs a command using `subprocess.run()`.

    Args:
        command:
            A string, the command to run.

            Multiple lines in `command` are treated as a single command.

            * If a line starts with `#` it is discarded.
            * If a line contains ` #`, the trailing text is discarded.

            When running the command on Windows, newlines are replaced by
            spaces; otherwise each line is terminated by a backslash character.
        capture:
            If true, we include the command's output in our return value.
        check:
            If true we raise an exception on error; otherwise we include the
            command's returncode in our return value.
        verbose:
            If true we show the command.
        env_extra:
            None or dict to add to environ.
        timeout:
            If not None, timeout in seconds; passed directly to
            subprocess.run(). Note that on MacOS subprocess.run() seems to
            leave processes running if timeout expires.
    Returns:
        check capture   Return
        --------------------------
          false false   returncode
          false  true   (returncode, output)
          true  false   None or raise exception
          true   true   output or raise exception
    '''
    env = None
    if env_extra:
        env = os.environ.copy()
        env.update(env_extra)
    lines = _command_lines( command)
    nl = '\n'
    if verbose:
        log1( f'Running: {nl.join(lines)}', caller=caller+1)
    sep = ' ' if windows() else ' \\\n'
    command2 = sep.join( lines)
    cp = subprocess.run(
            command2,
            shell=True,
            stdout=subprocess.PIPE if capture else None,
            stderr=subprocess.STDOUT if capture else None,
            check=check,
            encoding='utf8',
            env=env,
            timeout=timeout,
            )
    if check:
        return cp.stdout if capture else None
    else:
        return (cp.returncode, cp.stdout) if capture else cp.returncode


def darwin():
    return sys.platform.startswith( 'darwin')

def windows():
    return platform.system() == 'Windows'

def wasm():
    return os.environ.get( 'OS') in ('wasm', 'wasm-mt')

def pyodide():
    return os.environ.get( 'PYODIDE') == '1'

def linux():
    return platform.system() == 'Linux'

def openbsd():
    return platform.system() == 'OpenBSD'

class PythonFlags:
    '''
    Compile/link flags for the current python, for example the include path
    needed to get `Python.h`.

    The 'PIPCL_PYTHON_CONFIG' environment variable allows to override
    the location of the python-config executable.

    Members:
        .includes:
            String containing compiler flags for include paths.
        .ldflags:
            String containing linker flags for library paths.
    '''
    def __init__(self):

        if windows():
            wp = wdev.WindowsPython()
            self.includes = f'/I"{wp.include}"'
            self.ldflags = f'/LIBPATH:"{wp.libs}"'

        elif pyodide():
            _include_dir = os.environ[ 'PYO3_CROSS_INCLUDE_DIR']
            _lib_dir = os.environ[ 'PYO3_CROSS_LIB_DIR']
            self.includes = f'-I {_include_dir}'
            self.ldflags = f'-L {_lib_dir}'

        else:
            python_config = os.environ.get("PIPCL_PYTHON_CONFIG")
            if not python_config:
                # We use python-config which appears to work better than pkg-config
                # because it copes with multiple installed python's, e.g.
                # manylinux_2014's /opt/python/cp*-cp*/bin/python*.
                #
                # But... on non-macos it seems that we should not attempt to specify
                # libpython on the link command. The manylinux docker containers
                # don't actually contain libpython.so, and it seems that this
                # deliberate. And the link command runs ok.
                #
                python_exe = os.path.realpath( sys.executable)
                if darwin():
                    # Basic install of dev tools with `xcode-select --install` doesn't
                    # seem to provide a `python3-config` or similar, but there is a
                    # `python-config.py` accessible via sysconfig.
                    #
                    # We try different possibilities and use the last one that
                    # works.
                    #
                    python_config = None
                    for pc in (
                            f'python3-config',
                            f'{sys.executable} {sysconfig.get_config_var("srcdir")}/python-config.py',
                            f'{python_exe}-config',
                            ):
                        e = subprocess.run(
                                f'{pc} --includes',
                                shell=1,
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL,
                                check=0,
                                ).returncode
                        log2(f'{e=} from {pc!r}.')
                        if e == 0:
                            python_config = pc
                    assert python_config, f'Cannot find python-config'
                else:
                    python_config = f'{python_exe}-config'
            log2(f'Using {python_config=}.')
            try:
                self.includes = run( f'{python_config} --includes', capture=1, verbose=0).strip()
            except Exception as e:
                raise Exception('We require python development tools to be installed.') from e
            self.ldflags = run( f'{python_config} --ldflags', capture=1, verbose=0).strip()
            if linux():
                # It seems that with python-3.10 on Linux, we can get an
                # incorrect -lcrypt flag that on some systems (e.g. WSL)
                # causes:
                #
                #   ImportError: libcrypt.so.2: cannot open shared object file: No such file or directory
                #
                ldflags2 = self.ldflags.replace(' -lcrypt ', ' ')
                if ldflags2 != self.ldflags:
                    log2(f'### Have removed `-lcrypt` from ldflags: {self.ldflags!r} -> {ldflags2!r}')
                    self.ldflags = ldflags2

        log2(f'{self.includes=}')
        log2(f'{self.ldflags=}')


def macos_add_cross_flags(command):
    '''
    If running on MacOS and environment variables ARCHFLAGS is set
    (indicating we are cross-building, e.g. for arm64), returns
    `command` with extra flags appended. Otherwise returns unchanged
    `command`.
    '''
    if darwin():
        archflags = os.environ.get( 'ARCHFLAGS')
        if archflags:
            command = f'{command} {archflags}'
            log2(f'Appending ARCHFLAGS to command: {command}')
            return command
    return command


def macos_patch( library, *sublibraries):
    '''
    If running on MacOS, patches `library` so that all references to items in
    `sublibraries` are changed to `@rpath/{leafname}`. Does nothing on other
    platforms.

    library:
        Path of shared library.
    sublibraries:
        List of paths of shared libraries; these have typically been
        specified with `-l` when `library` was created.
    '''
    log2( f'macos_patch(): library={library}  sublibraries={sublibraries}')
    if not darwin():
        return
    if not sublibraries:
        return
    subprocess.run( f'otool -L {library}', shell=1, check=1)
    command = 'install_name_tool'
    names = []
    for sublibrary in sublibraries:
        name = subprocess.run(
                f'otool -D {sublibrary}',
                shell=1,
                check=1,
                capture_output=1,
                encoding='utf8',
                ).stdout.strip()
        name = name.split('\n')
        assert len(name) == 2 and name[0] == f'{sublibrary}:', f'{name=}'
        name = name[1]
        # strip trailing so_name.
        leaf = os.path.basename(name)
        m = re.match('^(.+[.]((so)|(dylib)))[0-9.]*$', leaf)
        assert m
        log2(f'Changing {leaf=} to {m.group(1)}')
        leaf = m.group(1)
        command += f' -change {name} @rpath/{leaf}'
    command += f' {library}'
    log2( f'Running: {command}')
    subprocess.run( command, shell=1, check=1)
    subprocess.run( f'otool -L {library}', shell=1, check=1)


# Internal helpers.
#

def _command_lines( command):
    '''
    Process multiline command by running through `textwrap.dedent()`, removes
    comments (lines starting with `#` or ` #` until end of line), removes
    entirely blank lines.

    Returns list of lines.
    '''
    command = textwrap.dedent( command)
    lines = []
    for line in command.split( '\n'):
        if line.startswith( '#'):
            h = 0
        else:
            h = line.find( ' #')
        if h >= 0:
            line = line[:h]
        if line.strip():
            lines.append(line.rstrip())
    return lines


def _cpu_name():
    '''
    Returns `x32` or `x64` depending on Python build.
    '''
    #log(f'sys.maxsize={hex(sys.maxsize)}')
    return f'x{32 if sys.maxsize == 2**31 - 1 else 64}'


def run_if( command, out, *prerequisites):
    '''
    Runs a command only if the output file is not up to date.

    Args:
        command:
            The command to run. We write this into a file <out>.cmd so that we
            know to run a command if the command itself has changed.
        out:
            Path of the output file.

        prerequisites:
            List of prerequisite paths or true/false/None items. If an item
            is None it is ignored, otherwise if an item is not a string we
            immediately return it cast to a bool.

    Returns:
        True if we ran the command, otherwise None.


    If the output file does not exist, the command is run:

        >>> verbose(1)
        1
        >>> log_line_numbers(0)
        >>> out = 'run_if_test_out'
        >>> if os.path.exists( out):
        ...     os.remove( out)
        >>> if os.path.exists( f'{out}.cmd'):
        ...     os.remove( f'{out}.cmd')
        >>> run_if( f'touch {out}', out)
        pipcl.py:run_if(): Running command because: File does not exist: 'run_if_test_out'
        pipcl.py:run_if(): Running: touch run_if_test_out
        True

    If we repeat, the output file will be up to date so the command is not run:

        >>> run_if( f'touch {out}', out)
        pipcl.py:run_if(): Not running command because up to date: 'run_if_test_out'

    If we change the command, the command is run:

        >>> run_if( f'touch  {out}', out)
        pipcl.py:run_if(): Running command because: Command has changed
        pipcl.py:run_if(): Running: touch  run_if_test_out
        True

    If we add a prerequisite that is newer than the output, the command is run:

        >>> time.sleep(1)
        >>> prerequisite = 'run_if_test_prerequisite'
        >>> run( f'touch {prerequisite}', caller=0)
        pipcl.py:run(): Running: touch run_if_test_prerequisite
        >>> run_if( f'touch  {out}', out, prerequisite)
        pipcl.py:run_if(): Running command because: Prerequisite is new: 'run_if_test_prerequisite'
        pipcl.py:run_if(): Running: touch  run_if_test_out
        True

    If we repeat, the output will be newer than the prerequisite, so the
    command is not run:

        >>> run_if( f'touch  {out}', out, prerequisite)
        pipcl.py:run_if(): Not running command because up to date: 'run_if_test_out'
    '''
    doit = False
    cmd_path = f'{out}.cmd'

    if not doit:
        out_mtime = _fs_mtime( out)
        if out_mtime == 0:
            doit = f'File does not exist: {out!r}'

    if not doit:
        if os.path.isfile( cmd_path):
            with open( cmd_path) as f:
                cmd = f.read()
        else:
            cmd = None
        if command != cmd:
            if cmd is None:
                doit = 'No previous command stored'
            else:
                doit = f'Command has changed'
                if 0:
                    doit += f': {cmd!r} => {command!r}'

    if not doit:
        # See whether any prerequisites are newer than target.
        def _make_prerequisites(p):
            if isinstance( p, (list, tuple)):
                return list(p)
            else:
                return [p]
        prerequisites_all = list()
        for p in prerequisites:
            prerequisites_all += _make_prerequisites( p)
        if 0:
            log2( 'prerequisites_all:')
            for i in  prerequisites_all:
                log2( f'    {i!r}')
        pre_mtime = 0
        pre_path = None
        for prerequisite in prerequisites_all:
            if isinstance( prerequisite, str):
                mtime = _fs_mtime_newest( prerequisite)
                if mtime >= pre_mtime:
                    pre_mtime = mtime
                    pre_path = prerequisite
            elif prerequisite is None:
                pass
            elif prerequisite:
                doit = str(prerequisite)
                break
        if not doit:
            if pre_mtime > out_mtime:
                doit = f'Prerequisite is new: {pre_path!r}'

    if doit:
        # Remove `cmd_path` before we run the command, so any failure
        # will force rerun next time.
        #
        try:
            os.remove( cmd_path)
        except Exception:
            pass
        log1( f'Running command because: {doit}')

        run( command)

        # Write the command we ran, into `cmd_path`.
        with open( cmd_path, 'w') as f:
            f.write( command)
        return True
    else:
        log1( f'Not running command because up to date: {out!r}')

    if 0:
        log2( f'out_mtime={time.ctime(out_mtime)} pre_mtime={time.ctime(pre_mtime)}.'
                f' pre_path={pre_path!r}: returning {ret!r}.'
                )


def _get_prerequisites(path):
    '''
    Returns list of prerequisites from Makefile-style dependency file, e.g.
    created by `cc -MD -MF <path>`.
    '''
    ret = list()
    if os.path.isfile(path):
        with open(path) as f:
            for line in f:
                for item in line.split():
                    if item.endswith( (':', '\\')):
                        continue
                    ret.append( item)
    return ret


def _fs_mtime_newest( path):
    '''
    path:
        If a file, returns mtime of the file. If a directory, returns mtime of
        newest file anywhere within directory tree. Otherwise returns 0.
    '''
    ret = 0
    if os.path.isdir( path):
        for dirpath, dirnames, filenames in os.walk( path):
            for filename in filenames:
                path = os.path.join( dirpath, filename)
                ret = max( ret, _fs_mtime( path))
    else:
        ret = _fs_mtime( path)
    return ret


def _flags( items, prefix='', quote=''):
    '''
    Turns sequence into string, prefixing/quoting each item.
    '''
    if not items:
        return ''
    if isinstance( items, str):
        items = items,
    ret = ''
    for item in items:
        if ret:
            ret += ' '
        ret += f'{prefix}{quote}{item}{quote}'
    return ret.strip()


def _fs_mtime( filename, default=0):
    '''
    Returns mtime of file, or `default` if error - e.g. doesn't exist.
    '''
    try:
        return os.path.getmtime( filename)
    except OSError:
        return default


def _assert_version_pep_440(version):
    assert re.match(
                r'^([1-9][0-9]*!)?(0|[1-9][0-9]*)(\.(0|[1-9][0-9]*))*((a|b|rc)(0|[1-9][0-9]*))?(\.post(0|[1-9][0-9]*))?(\.dev(0|[1-9][0-9]*))?$',
                version,
            ), \
            f'Bad version: {version!r}.'


g_verbose = int(os.environ.get('PIPCL_VERBOSE', '1'))

def verbose(level=None):
    '''
    Sets verbose level if `level` is not None.
    Returns verbose level.
    '''
    global g_verbose
    if level is not None:
        g_verbose = level
    return g_verbose

g_log_line_numbers = True

def log_line_numbers(yes):
    '''
    Sets whether to include line numbers; helps with doctest.
    '''
    global g_log_line_numbers
    g_log_line_numbers = bool(yes)

def log0(text='', caller=1):
    _log(text, 0, caller+1)

def log1(text='', caller=1):
    _log(text, 1, caller+1)

def log2(text='', caller=1):
    _log(text, 2, caller+1)

def _log(text, level, caller):
    '''
    Logs lines with prefix.
    '''
    if level <= g_verbose:
        fr = inspect.stack(context=0)[caller]
        filename = relpath(fr.filename)
        for line in text.split('\n'):
            if g_log_line_numbers:
                print(f'{filename}:{fr.lineno}:{fr.function}(): {line}', file=sys.stdout, flush=1)
            else:
                print(f'{filename}:{fr.function}(): {line}', file=sys.stdout, flush=1)


def relpath(path, start=None):
    '''
    A safe alternative to os.path.relpath(), avoiding an exception on Windows
    if the drive needs to change - in this case we use os.path.abspath().
    '''
    if windows():
        try:
            return os.path.relpath(path, start)
        except ValueError:
            # os.path.relpath() fails if trying to change drives.
            return os.path.abspath(path)
    else:
        return os.path.relpath(path, start)

def _so_suffix(use_so_versioning=True):
    '''
    Filename suffix for shared libraries is defined in pep-3149.  The
    pep claims to only address posix systems, but the recommended
    sysconfig.get_config_var('EXT_SUFFIX') also seems to give the
    right string on Windows.
    
    If use_so_versioning is false, we return only the last component of
    the suffix, which removes any version number, for example changing
    `.cp312-win_amd64.pyd` to `.pyd`.
    '''
    # Example values:
    #   linux:      .cpython-311-x86_64-linux-gnu.so
    #   macos:      .cpython-311-darwin.so
    #   openbsd:    .cpython-310.so
    #   windows     .cp311-win_amd64.pyd
    #
    # Only Linux and Windows seem to identify the cpu. For example shared
    # libraries in numpy-1.25.2-cp311-cp311-macosx_11_0_arm64.whl are called
    # things like `numpy/core/_simd.cpython-311-darwin.so`.
    #
    ret = sysconfig.get_config_var('EXT_SUFFIX')
    if not use_so_versioning:
        # Use last component only.
        ret = os.path.splitext(ret)[1]
    return ret


def get_soname(path):
    '''
    If we are on Linux and `path` is softlink and points to a shared library
    for which `objdump -p` contains 'SONAME', return the pointee. Otherwise
    return `path`. Useful if Linux shared libraries have been created with
    `-Wl,-soname,...`, where we need to embed the versioned library.
    '''
    if linux() and os.path.islink(path):
        path2 = os.path.realpath(path)
        if subprocess.run(f'objdump -p {path2}|grep SONAME', shell=1, check=0).returncode == 0:
            return path2
    elif openbsd():
        # Return newest .so with version suffix.
        sos = glob.glob(f'{path}.*')
        log1(f'{sos=}')
        sos2 = list()
        for so in sos:
            suffix = so[len(path):]
            if not suffix or re.match('^[.][0-9.]*[0-9]$', suffix):
                sos2.append(so)
        sos2.sort(key=lambda p: os.path.getmtime(p))
        log1(f'{sos2=}')
        return sos2[-1]
    return path


def current_py_limited_api():
    '''
    Returns value of PyLIMITED_API to build for current Python.
    '''
    a, b = map(int, platform.python_version().split('.')[:2])
    return f'0x{a:02x}{b:02x}0000'
    

def install_dir(root=None):
    '''
    Returns install directory used by `install()`.

    This will be `sysconfig.get_path('platlib')`, modified by `root` if not
    None.
    '''
    # todo: for pure-python we should use sysconfig.get_path('purelib') ?
    root2 = sysconfig.get_path('platlib')
    if root:
        if windows():
            # If we are in a venv, `sysconfig.get_path('platlib')`
            # can be absolute, e.g.
            # `C:\\...\\venv-pypackage-3.11.1-64\\Lib\\site-packages`, so it's
            # not clear how to append it to `root`. So we just use `root`.
            return root
        else:
            # E.g. if `root` is `install' and `sysconfig.get_path('platlib')`
            # is `/usr/local/lib/python3.9/site-packages`, we set `root2` to
            # `install/usr/local/lib/python3.9/site-packages`.
            #
            return os.path.join( root, root2.lstrip( os.sep))
    else:
        return root2


class _Record:
    '''
    Internal - builds up text suitable for writing to a RECORD item, e.g.
    within a wheel.
    '''
    def __init__(self):
        self.text = ''

    def add_content(self, content, to_, verbose=True):
        if isinstance(content, str):
            content = content.encode('utf8')

        # Specification for the line we write is supposed to be in
        # https://packaging.python.org/en/latest/specifications/binary-distribution-format
        # but it's not very clear.
        #
        h = hashlib.sha256(content)
        digest = h.digest()
        digest = base64.urlsafe_b64encode(digest)
        digest = digest.rstrip(b'=')
        digest = digest.decode('utf8')

        self.text += f'{to_},sha256={digest},{len(content)}\n'
        if verbose:
            log2(f'Adding {to_}')

    def add_file(self, from_, to_):
        log1(f'Adding file: {os.path.relpath(from_)} => {to_}')
        with open(from_, 'rb') as f:
            content = f.read()
        self.add_content(content, to_, verbose=False)

    def get(self, record_path=None):
        '''
        Returns contents of the RECORD file. If `record_path` is
        specified we append a final line `<record_path>,,`; this can be
        used to include the RECORD file itself in the contents, with
        empty hash and size fields.
        '''
        ret = self.text
        if record_path:
            ret += f'{record_path},,\n'
        return ret
