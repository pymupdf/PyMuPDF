#! /usr/bin/env python3

'''Developer build/test script for PyMuPDF.

Examples:

    ./PyMuPDF/scripts/test.py --mupdf mupdf buildtest
        Build and test with pre-existing local mupdf/ checkout.

    ./PyMuPDF/scripts/test.py buildtest
        Build and test with default internal download of mupdf.

    ./PyMuPDF/scripts/test.py --mupdf 'git:https://git.ghostscript.com/mupdf.git' buildtest
        Build and test with internal checkout of mupdf master.

    ./PyMuPDF/scripts/test.py --mupdf 'git:--branch 1.24.x https://github.com/ArtifexSoftware/mupdf.git' buildtest
        Build and test using internal checkout of mupdf 1.24.x branch from Github.

Usage:
    scripts/test.py <options> <commands>

* Commands are handled in order, so for example `build` should usually be
  before `test`.

* If we are not already running inside a Python venv, we automatically create a
  venv and re-run ourselves inside it.

* We build directly with pip (unlike gh_release.py, which builds with
  cibuildwheel).

* We run tests with pytest.

* One can generate call traces by setting environment variables in debug
  builds. For details see:
  https://mupdf.readthedocs.io/en/latest/language-bindings.html#environmental-variables

Options:
    --help
    -h
        Show help.
    -b <build>
        Set build type for `build` or `buildtest` commands. `<build>` should
        be one of 'release', 'debug', 'memento'. [This makes `build` set
        environment variable `PYMUPDF_SETUP_MUPDF_BUILD_TYPE`, which is used by
        PyMuPDF's `setup.py`.]
    -d
        Equivalent to `--build-type debug`.
    -f 0|1
        If 1 (the default) we also test alias `fitz` as well as `pymupdf`.
    -i <implementations>
        Set PyMuPDF implementations to test.
        <implementations> must contain only these individual characters:
             'c' - classic.
             'r' - rebased.
             'R' - rebased without optimisations.
            Default is 'rR'. Also see `PyMuPDF:tests/run_compound.py`.
    -k <expression>
        Passed straight through to pytest's `-k`.
    -m <location> | --mupdf <location>
        Location of local mupdf/ directory or 'git:...' to be used
        when building PyMuPDF. [This sets environment variable
        PYMUPDF_SETUP_MUPDF_BUILD, which is used by PyMuPDF/setup.py. If not
        specifed PyMuPDF will download its default mupdf .tgz.]
    -p <pytest-options>
        Set pytest options; default is ''.
    -t <names>
        Pytest test names, comma-separated. Should be relative to PyMuPDF
        directory. For example:
            -t tests/test_general.py
            -t tests/test_general.py::test_subset_fonts.
        To specify multiple tests, use comma-separated list and/or multiple `-t
        <names>` args.
    -v 0|1|2
        0 - do not use a venv.
        1 - Use venv. If it already exists, we assume the existing directory
            was created by us earlier and is a valid venv containing all
            necessary packages; this saves a little time.
        2 - use venv.
        The default is 2.
    --build-isolation 0|1
        If true (the default on non-OpenBSD systems), we let pip create and use
        its own new venv to build PyMuPDF. Otherwise we force pip to use the
        current venv.
    --build-mupdf 0|1
        Whether to rebuild mupdf when we build PyMuPDF. Default is 1.
    --gdb 0|1
        Run tests under gdb.
    --system-site-packages 0|1
        If 1, use `--system-site-packages` when creating venv.
    --timeout <seconds>
        Sets timeout when running tests.
    --valgrind 0|1
        Use valgrind in `test` or `buildtest`.
        This will run `sudo apt update` and `sudo apt install valgrind`.

Commands:
    build
        Builds and installs PyMuPDF into venv, using `pip install .../PyMuPDF`.
    buildtest
        Same as 'build test'.
    test
        Runs PyMuPDF's pytest tests in venv. Default is to test rebased and
        unoptimised rebased; use `-i` to change this.

Environment:
    PYMUDF_SCRIPTS_TEST_options
        Is prepended to command line args.
'''

import gh_release

import glob
import os
import platform
import re
import shlex
import subprocess
import sys
import textwrap


pymupdf_dir = os.path.abspath( f'{__file__}/../..')


def main(argv):

    if len(argv) == 1:
        show_help()
        return

    build_isolation = None
    valgrind = False
    s = True
    build_type = None
    build_mupdf = True
    gdb = False
    test_fitz = True
    implementations = None
    test_names = list()
    venv = 2
    pytest_options = None
    timeout = None
    pytest_k = None
    system_site_packages = False
    
    options = os.environ.get('PYMUDF_SCRIPTS_TEST_options', '')
    options = shlex.split(options)
    
    args = iter(options + argv[1:])
    i = 0
    while 1:
        try:
            arg = next(args)
        except StopIteration:
            arg = None
            break
        if not arg.startswith('-'):
            break
        elif arg == '-b':
            build_type = next(args)
        elif arg == '--build-isolation':
            build_isolation = int(next(args))
        elif arg == '-d':
            build_type = 'debug'
        elif arg == '-f':
            test_fitz = int(next(args))
        elif arg in ('-h', '--help'):
            show_help()
            return
        elif arg == '-i':
            implementations = next(args)
        elif arg in ('--mupdf', '-m'):
            mupdf = next(args)
            if not mupdf.startswith('git:'):
                assert os.path.isdir(mupdf), f'Not a directory: {mupdf=}.'
                mupdf = os.path.abspath(mupdf)
            os.environ['PYMUPDF_SETUP_MUPDF_BUILD'] = mupdf
        elif arg == '-k':
            pytest_k = next(args)
        elif arg == '-p':
            pytest_options  = next(args)
        elif arg == '--system-site-packages':
            system_site_packages = int(next(args))
        elif arg == '-t':
            test_names += next(args).split(',')
        elif arg == '--timeout':
            timeout = float(next(args))
        elif arg == '-v':
            venv = int(next(args))
        elif arg == '--build-mupdf':
            build_mupdf = int(next(args))
        elif arg == '--gdb':
            gdb = int(next(args))
        elif arg == '--valgrind':
            valgrind = int(next(args))
        else:
            assert 0, f'Unrecognised option: {arg=}.'
    
    if arg is None:
        log(f'No command specified.')
        return
    
    commands = list()
    while 1:
        assert arg in ('build', 'buildtest', 'test'), \
                f'Unrecognised command: {arg=}.'
        commands.append(arg)
        try:
            arg = next(args)
        except StopIteration:
            break
    
    venv_quick = (venv==1)
    
    # Run inside a venv.
    if venv and sys.prefix == sys.base_prefix:
        # We are not running in a venv.
        log(f'Re-running in venv {gh_release.venv_name!r}.')
        gh_release.venv(
                ['python'] + argv,
                quick=venv_quick,
                system_site_packages=system_site_packages,
                )
        return

    def do_build():
        build(
                implementations=implementations,
                build_type=build_type,
                build_isolation=build_isolation,
                venv_quick=venv_quick,
                build_mupdf=build_mupdf,
                )
    def do_test():
        test(
                implementations=implementations,
                valgrind=valgrind,
                venv_quick=venv_quick,
                test_names=test_names,
                pytest_options=pytest_options,
                timeout=timeout,
                gdb=gdb,
                test_fitz=test_fitz,
                pytest_k=pytest_k,
                )
    
    for command in commands:
        if 0:
            pass
        elif command == 'build':
            do_build()
        elif command == 'test':
            do_test()
        elif command == 'buildtest':
            do_build()
            do_test()
        else:
            assert 0


def get_env_bool(name, default=0):
    v = os.environ.get(name)
    if v in ('1', 'true'):
        return 1
    elif v in ('0', 'false'):
        return 0
    elif v is None:
        return default
    else:
        assert 0, f'Bad environ {name=} {v=}'

def show_help():
    print(__doc__)
    print(venv_info())


def venv_info(pytest_args=None):
    '''
    Returns string containing information about the venv we use and how to
    run tests manually. If specified, `pytest_args` contains the pytest args,
    otherwise we use an example.
    '''
    pymupdf_dir_rel = gh_release.relpath(pymupdf_dir)
    ret = f'Name of venv: {gh_release.venv_name}\n'
    if pytest_args is None:
        pytest_args = f'{pymupdf_dir_rel}/tests/test_general.py::test_subset_fonts'
    if platform.system() == 'Windows':
        ret += textwrap.dedent(f'''
                Rerun tests manually with rebased implementation:
                    Enter venv:
                        {gh_release.venv_name}\\Scripts\\activate
                    Run specific test in venv:
                        {gh_release.venv_name}\\Scripts\\python -m pytest {pytest_args}
                ''')
    else:
        ret += textwrap.dedent(f'''
                Rerun tests manually with rebased implementation:
                    Enter venv and run specific test, also under gdb:
                        . {gh_release.venv_name}/bin/activate
                        python -m pytest {pytest_args}
                        gdb --args python -m pytest {pytest_args}
                    Run without explicitly entering venv, also under gdb:
                        ./{gh_release.venv_name}/bin/python -m pytest {pytest_args}
                        gdb --args ./{gh_release.venv_name}/bin/python -m pytest {pytest_args}
                ''')
    return ret


def build(
        implementations=None,
        build_type=None,
        build_isolation=None,
        venv_quick=False,
        build_mupdf=True,
        ):
    '''
    Args:
        build_type:
            See top-level option `-b`.
        build_isolation:
            See top-level option `--build-isolation`.
        venv_quick:
            See top-level option `-v`.
        build_mupdf:
            See top-level option `build-mupdf`
    '''
    print(f'{build_type=}')
    print(f'{build_isolation=}')
    
    if build_isolation is None:
        # On OpenBSD libclang is not available on pypi.org, so we need to force
        # use of system package py3-llvm with --no-build-isolation, manually
        # installing other required packages.
        build_isolation = False if platform.system() == 'OpenBSD' else True
    
    if build_isolation:
        # This is the default on non-OpenBSD.
        build_isolation_text = ''
    else:
        # Not using build isolation - i.e. pip will not be using its own clean
        # venv, so we need to explicitly install required packages.  Manually
        # install required packages from pyproject.toml.
        sys.path.insert(0, os.path.abspath(f'{__file__}/../..'))
        import setup
        names = setup.get_requires_for_build_wheel()
        del sys.path[0]
        names = ' '.join(names)
        if venv_quick:
            log(f'{venv_quick=}: Not installing packages with pip: {names}')
        else:
            gh_release.run( f'python -m pip install --upgrade {names}')
        build_isolation_text = ' --no-build-isolation'
    
    env_extra = dict()
    if implementations:
        v = ''
        if 'c' in implementations:
            v += 'a'
        if 'r' in implementations or 'R' in implementations:
            v += 'b'
        env_extra['PYMUPDF_SETUP_IMPLEMENTATIONS'] = v
    if not build_mupdf:
        env_extra['PYMUPDF_SETUP_MUPDF_REBUILD'] = '0'
    if build_type:
        env_extra['PYMUPDF_SETUP_MUPDF_BUILD_TYPE'] = build_type
    gh_release.run(f'pip install{build_isolation_text} -vv {pymupdf_dir}', env_extra=env_extra)


def test(
        implementations,
        valgrind,
        venv_quick=False,
        test_names=None,
        pytest_options=None,
        timeout=None,
        gdb=False,
        test_fitz=True,
        pytest_k=None
        ):
    '''
    Args:
        implementations:
            See top-level option `-i`.
        valgrind:
            See top-level option `--valgrind`.
        venv_quick:
            .
        test_names:
            See top-level option `-t`.
        pytest_options:
            See top-level option `-p`.
        gdb:
            See top-level option `--gdb`.
        test_fitz:
            See top-level option `-f`.
    '''
    pymupdf_dir_rel = gh_release.relpath(pymupdf_dir)
    if pytest_options is None:
        if valgrind:
            pytest_options = '-s -vv'
        else:
            pytest_options = ''
    if pytest_k:
        pytest_options += f' -k {shlex.quote(pytest_k)}'
    pytest_arg = ''
    if test_names:
        for test_name in test_names:
            pytest_arg += f' {pymupdf_dir_rel}/{test_name}'
    else:
        pytest_arg += f' {pymupdf_dir_rel}'
    python = gh_release.relpath(sys.executable)
    log('Running tests with tests/run_compound.py and pytest.')
    try:
        if venv_quick:
            log(f'{venv_quick=}: Not installing test packages: {gh_release.test_packages}')
        else:
            gh_release.run(f'pip install {gh_release.test_packages}')
        run_compound_args = ''
        if implementations:
            run_compound_args += f' -i {implementations}'
        if timeout:
            run_compound_args += f' -t {timeout}'
        env_extra = None
        if valgrind:
            log('Installing valgrind.')
            gh_release.run(f'sudo apt update')
            gh_release.run(f'sudo apt install valgrind')
            gh_release.run(f'valgrind --version')
        
            log('Running PyMuPDF tests under valgrind.')
            command = (
                    f'{python} {pymupdf_dir_rel}/tests/run_compound.py{run_compound_args}'
                        f' valgrind --suppressions={pymupdf_dir_rel}/valgrind.supp --error-exitcode=100 --errors-for-leak-kinds=none --fullpath-after='
                        f' {python} -m pytest {pytest_options}{pytest_arg}'
                        )
            env_extra=dict(
                    PYTHONMALLOC='malloc',
                    PYMUPDF_RUNNING_ON_VALGRIND='1',
                    )
        elif gdb:
            command = f'{python} {pymupdf_dir_rel}/tests/run_compound.py{run_compound_args} gdb --args {python} -m pytest {pytest_options} {pytest_arg}'
        elif platform.system() == 'Windows':
            # `python -m pytest` doesn' seem to work.
           command = f'{python} {pymupdf_dir_rel}/tests/run_compound.py{run_compound_args} pytest {pytest_options} {pytest_arg}'
        else:
            # On OpenBSD `pip install pytest` doesn't seem to install the pytest
            # command, so we use `python -m pytest ...`.
            command = f'{python} {pymupdf_dir_rel}/tests/run_compound.py{run_compound_args} {python} -m pytest {pytest_options} {pytest_arg}'
        
        # Always start by removing any test_*_fitz.py files.
        for p in glob.glob(f'{pymupdf_dir_rel}/tests/test_*_fitz.py'):
            print(f'Removing {p=}')
            os.remove(p)
        if test_fitz:
            # Create copies of each test file, modified to use `pymupdf`
            # instead of `fitz`.
            for p in glob.glob(f'{pymupdf_dir_rel}/tests/test_*.py'):
                if os.path.basename(p).startswith('test_fitz_'):
                    # Don't recursively generate test_fitz_fitz_foo.py,
                    # test_fitz_fitz_fitz_foo.py, ... etc.
                    continue
                branch, leaf = os.path.split(p)
                p2 = f'{branch}/{leaf[:5]}fitz_{leaf[5:]}'
                print(f'Converting {p=} to {p2=}.')
                with open(p, encoding='utf8') as f:
                    text = f.read()
                text2 = re.sub("([^\'])\\bpymupdf\\b", '\\1fitz', text)
                if p.replace(os.sep, '/') == f'{pymupdf_dir_rel}/tests/test_docs_samples.py'.replace(os.sep, '/'):
                    assert text2 == text
                else:
                    assert text2 != text, f'Unexpectedly unchanged when creating {p!r} => {p2!r}'
                with open(p2, 'w', encoding='utf8') as f:
                    f.write(text2)
        
        log(f'Running tests with tests/run_compound.py and pytest.')
        gh_release.run(command, env_extra=env_extra, timeout=timeout)
            
    except subprocess.TimeoutExpired as e:
         log(f'Timeout when running tests.')
         raise
    finally:
        log('\n' + venv_info(pytest_args=f'{pytest_options} {pytest_arg}'))


def get_pyproject_required(ppt=None):
    '''
    Returns space-separated names of required packages in pyproject.toml.  We
    do not do a proper parse and rely on the packages being in a single line.
    '''
    if ppt is None:
        ppt = os.path.abspath(f'{__file__}/../../pyproject.toml')
    with open(ppt) as f:
        for line in f:
            m = re.match('^requires = \\[(.*)\\]$', line)
            if m:
                names = m.group(1).replace(',', ' ').replace('"', '')
                return names
        else:
            assert 0, f'Failed to find "requires" line in {ppt}'

def wrap_get_requires_for_build_wheel(dir_):
    '''
    Returns space-separated list of required
    packages. Looks at `dir_`/pyproject.toml and calls
    `dir_`/setup.py:get_requires_for_build_wheel().
    '''
    dir_abs = os.path.abspath(dir_)
    ret = list()
    ppt = os.path.join(dir_abs, 'pyproject.toml')
    if os.path.exists(ppt):
        ret += get_pyproject_required(ppt)
    if os.path.exists(os.path.join(dir_abs, 'setup.py')):
        sys.path.insert(0, dir_abs)
        try:
            from setup import get_requires_for_build_wheel as foo
            for i in foo():
                ret.append(i)
        finally:
            del sys.path[0]
    return ' '.join(ret)


def log(text):
    gh_release.log(text, caller=1)


if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv))
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        # Terminate relatively quietly, failed commands will usually have
        # generated diagnostics.
        log(f'{e}')
        sys.exit(1)
    # Other exceptions should not happen, and will generate a full Python
    # backtrace etc here.
