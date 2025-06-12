#! /usr/bin/env python3

'''Developer build/test script for PyMuPDF.

Examples:

    ./PyMuPDF/scripts/test.py --m mupdf build test
        Build and test with pre-existing local mupdf/ checkout.

    ./PyMuPDF/scripts/test.py build test
        Build and test with default internal download of mupdf.

    ./PyMuPDF/scripts/test.py -m 'git:https://git.ghostscript.com/mupdf.git' build test
        Build and test with internal checkout of MuPDF master.

    ./PyMuPDF/scripts/test.py -m 'git:--branch 1.26.x https://github.com/ArtifexSoftware/mupdf.git' build test
        Build and test using internal checkout of mupdf 1.26.x branch from
        Github.

Usage:

* Command line arguments are called parameters if they start with `-`,
  otherwise they are called commands.
* Parameters are evaluated first in the order that they were specified.
* Then commands are run in the order in which they were specified.
* Usually command `test` would be specified after a `build`, `install` or
  `wheel` command.
* Parameters and commands can be interleaved but it may be clearer to separate
  them on the command line.

Other:

* If we are not already running inside a Python venv, we automatically create a
  venv and re-run ourselves inside it.
* Build/wheel/install commands always install into the venv.
* Tests use whatever PyMuPDF/MuPDF is currently installed in the venv.
* We run tests with pytest.

* One can generate call traces by setting environment variables in debug
  builds. For details see:
  https://mupdf.readthedocs.io/en/latest/language-bindings.html#environmental-variables

Command line args:

    -a <env_name>
        Read next space-separated argument(s) from environmental variable
        <env_name>.
        * Does nothing if <env_name> is unset.
        * Useful when running via Github action.
    
    -b <build>
        Set build type for `build` commands. `<build>` should be one of
        'release', 'debug', 'memento'. [This makes `build` set environment
        variable `PYMUPDF_SETUP_MUPDF_BUILD_TYPE`, which is used by PyMuPDF's
        `setup.py`.]
    
    --build-flavour <build_flavour>
        Combination of 'p', 'b', 'd'. See ../setup.py's description of
        PYMUPDF_SETUP_FLAVOUR. Default is 'pbd', i.e. self-contained PyMuPDF
        wheels including MuPDF build-time files.
    
    --build-isolation 0|1
        If true (the default on non-OpenBSD systems), we let pip create and use
        its own new venv to build PyMuPDF. Otherwise we force pip to use the
        current venv.
    
    --cibw-archs-linux <archs>
        Set CIBW_ARCHS_LINUX, e.g. to `auto64 aarch64`. Default is `auto64` so
        this allows control over whether to build linux-aarch64 wheels.
    
    --cibw-name <cibw_name>
        Name to use when installing cibuildwheel, e.g.:
            --cibw-name cibuildwheel==3.0.0b1
        Default is `cibuildwheel`, i.e. the current release.
    
    --cibw-pyodide 0|1
         Experimental, make `cibuild` command build a pyodide wheel.
         2025-05-27: this fails when building mupdf C API - `ld -r -b binary
         ...` fails with:
            emcc: error: binary: No such file or directory ("binary" was expected to be an input file, based on the commandline arguments provided)
    
    --cibw-release-1
        Set up so that `cibw` builds all wheels except linux-aarch64, and sdist
        if on Linux.
    
    --cibw-release-2
        Set up so that `cibw` builds only linux-aarch64 wheel.
    
    -d
        Equivalent to `-b debug`.
    
    --dummy
        Sets PYMUPDF_SETUP_DUMMY=1 which makes setup.py build a dummy wheel
        with no content. For internal testing only.
    
    -e <name>=<value>
        Add to environment used in build and test commands. Can be specified
        multiple times.
    
    -f 0|1
        If 1 we also test alias `fitz` as well as `pymupdf`. Default is '0'.
    
    --gdb 0|1
        Run tests under gdb. Requires user interaction.
    
    --help
    -h
        Show help.
    
    -i <implementations>
        Set PyMuPDF implementations to test.
        <implementations> must contain only these individual characters:
             'r' - rebased.
             'R' - rebased without optimisations.
            Default is 'r'. Also see `PyMuPDF:tests/run_compound.py`.
    
    -k <expression>
        Specify which test(s) to run; passed straight through to pytest's `-k`.
        For example `-k test_3354`.
    
    -m <location> | --mupdf <location>
        Location of local mupdf/ directory or 'git:...' to be used
        when building PyMuPDF. [This sets environment variable
        PYMUPDF_SETUP_MUPDF_BUILD, which is used by PyMuPDF/setup.py. If not
        specified PyMuPDF will download its default mupdf .tgz.]
    
    -M 0|1
    --build-mupdf 0|1
        Whether to rebuild mupdf when we build PyMuPDF. Default is 1.
    
    -o <os_names>
        Control whether we do nothing on the current platform.
        * <os_names> is a comma-separated list of names.
        * If <os_names> is empty (the default), we always run normally.
        * Otherwise we only run if an item in <os_names> matches (case
          insensitive) platform.system().
        * For example `-o linux,darwin` will do nothing unless on Linux or
          MacOS.
    
    -p <pytest-options>
        Set pytest options; default is ''.
    
    -P 0|1
        If 1, automatically install required system packages such as
        Valgrind. Default is 0.
    
    --pybind 0|1
        Experimental, for investigating
        https://github.com/pymupdf/PyMuPDF/issues/3869. Runs run basic code
        inside C++ pybind. Requires `sudo apt install pybind11-dev` or similar.
    
    --pyodide-build-version <version>
        Version of Python package pyodide-build; if None (the default) we use
        latest available version.
        2025-02-13: pyodide_build_version='0.29.3' works.
    
    -s 0 | 1
        If 1 (the default), build with Python Limited API/Stable ABI.
        [This simply sSets $PYMUPDF_SETUP_PY_LIMITED_API, which is used by
        PyMuPDF/setup.py.]
    
    --show-args:
        Show sys.argv and exit. For debugging.
    
    --sync-paths
        Do not run anything, instead write required files/directories/checkouts
        to stdout, one per line. This is to help with automated running on
        remote machines.
    
    --system-site-packages 0|1
        If 1, use `--system-site-packages` when creating venv. Defaults is 0.
    
    -t <names>
        Pytest test names, comma-separated. Should be relative to PyMuPDF
        directory. For example:
            -t tests/test_general.py
            -t tests/test_general.py::test_subset_fonts
        To specify multiple tests, use comma-separated list and/or multiple `-t
        <names>` args.
    
    --timeout <seconds>
        Sets timeout when running tests.
    
    -T <command> | --pytest-prefix <command>
        Use specified prefix when running pytest. E.g. `gdb --args`.
    
    -v 0|1|2
        0 - do not use a venv.
        1 - Use venv. If it already exists, we assume the existing directory
            was created by us earlier and is a valid venv containing all
            necessary packages; this saves a little time.
        2 - Use venv
        The default is 2.
    
    --valgrind 0|1
        Use valgrind in `test` or `buildtest`.
        This will run `sudo apt update` and `sudo apt install valgrind`.

Commands:
    
    build
        Builds and installs PyMuPDF into venv, using `pip install .../PyMuPDF`.
    
    buildtest
        Same as 'build test'.
    
    cibw
        Build and test PyMuPDF wheel(s) using cibuildwheel. Wheels are placed
        in directory `wheelhouse`.
        * We do not attempt to install wheels.
        * So it is generally not useful to do `cibw test`.
        
        If CIBW_BUILD is unset, we set it as follows:
        * On Github we build and test all supported Python versions.
        * Otherwise we build and test the current Python version only.
        
        If CIBW_ARCHS is unset we set $CIBW_ARCHS_WINDOWS, $CIBW_ARCHS_MACOS
        and $CIBW_ARCHS_LINUX to auto64 if they are unset.
    
    install <pymupdf>
        Install with `pip install --force-reinstall <pymupdf>`.
    
    pyodide
        Build Pyodide wheel. We clone `emsdk.git`, set it up, and run
        `pyodide build`. This runs our setup.py with CC etc set up
        to create Pyodide binaries in a wheel called, for example,
        `PyMuPDF-1.23.2-cp311-none-emscripten_3_1_32_wasm32.whl`.
        
        It seems that sys.version must match the Python version inside emsdk;
        as of 2025-02-14 this is 3.12. Otherwise we get build errors such as:
            [wasm-validator error in function 723] unexpected false: all used features should be allowed, on ...
    
    test
        Runs PyMuPDF's pytest tests. Default is to test rebased and unoptimised
        rebased; use `-i` to change this.
    
    wheel
        Build and install wheel.
            

Environment:
    PYMUDF_SCRIPTS_TEST_options
        Is prepended to command line args.
'''

import glob
import os
import platform
import re
import shlex
import subprocess
import sys
import textwrap


pymupdf_dir_abs = os.path.abspath( f'{__file__}/../..')

try:
    sys.path.insert(0, pymupdf_dir_abs)
    import pipcl
finally:
    del sys.path[0]

try:
    sys.path.insert(0, f'{pymupdf_dir_abs}/scripts')
    import gh_release
finally:
    del sys.path[0]


pymupdf_dir = pipcl.relpath(pymupdf_dir_abs)

log = pipcl.log0
run = pipcl.run


def main(argv):

    if github_workflow_unimportant():
        return
    
    build_isolation = None
    cibw_name = 'cibuildwheel'
    cibw_pyodide = None
    commands = list()
    env_extra = dict()
    implementations = 'r'
    mupdf_sync = None
    os_names = list()
    system_packages = False
    pybind = False
    pyodide_build_version = None
    pytest_options = ''
    pytest_prefix = None
    cibw_sdist = None
    show_args = False
    show_help = False
    sync_paths = False
    system_site_packages = False
    test_fitz = False
    test_names = list()
    test_timeout = None
    valgrind = False
    warnings = list()
    venv = 2
    
    options = os.environ.get('PYMUDF_SCRIPTS_TEST_options', '')
    options = shlex.split(options)
    
    # Parse args and update the above state. We do this before moving into a
    # venv, partly so we can return errors immediately.
    #
    args = iter(options + argv[1:])
    i = 0
    while 1:
        try:
            arg = next(args)
        except StopIteration:
            arg = None
            break
        
        if 0:
            pass
        
        elif arg == '-a':
            _name = next(args)
            _value = os.environ.get(_name, '')
            _args = shlex.split(_value) + list(args)
            args = iter(_args)
        
        elif arg == '-b':
            env_extra['PYMUPDF_SETUP_MUPDF_BUILD_TYPE'] = next(args)
        
        elif arg == '--build-flavour':
            env_extra['PYMUPDF_SETUP_FLAVOUR'] = next(args)
        
        elif arg == '--build-isolation':
            build_isolation = int(next(args))
        
        elif arg == '--cibw-release-1':
            cibw_sdist = True
            env_extra['CIBW_ARCHS_LINUX'] = 'auto64'
            env_extra['CIBW_ARCHS_MACOS'] = 'auto64'
            env_extra['CIBW_ARCHS_WINDOWS'] = 'auto'    # win32 and win64.
            env_extra['CIBW_SKIP'] = 'pp* *i686 cp36* cp37* *musllinux*aarch64*'
        
        elif arg == '--cibw-release-2':
            env_extra['CIBW_ARCHS_LINUX'] = 'aarch64'
            os_names = ['linux']
        
        elif arg == '--cibw-archs-linux':
            env_extra['CIBW_ARCHS_LINUX'] = next(args)
            
        elif arg == '--cibw-name':
            cibw_name = next(args)
        
        elif arg == '--cibw-pyodide':
            cibw_pyodide = next(args)
        
        elif arg == '-d':
            env_extra['PYMUPDF_SETUP_MUPDF_BUILD_TYPE'] = 'debug'
        
        elif arg == '--dummy':
            env_extra['PYMUPDF_SETUP_DUMMY'] = '1'
            env_extra['CIBW_TEST_COMMAND'] = ''
        
        elif arg == '-e':
            _nv = next(args)
            assert '=' in _nv, f'-e <name>=<value> does not contain "=": {_nv!r}'
            _name, _value = _nv.split('=', 1)
            env_extra[_name] = _value
        
        elif arg == '-f':
            test_fitz = int(next(args))
        
        elif arg == '--gdb':
            _gdb = int(next(args))
            if _gdb == 1:
                pytest_prefix = 'gdb'
            warnings += f'{arg=} is deprecated, use `-T gdb`.'
        
        elif arg in ('-h', '--help'):
            show_help = True
        
        elif arg == '-i':
            implementations = next(args)
        
        elif arg == '-k':
            pytest_options += f' -k {shlex.quote(next(args))}'
        
        elif arg in ('-m', '--mupdf'):
            _mupdf = next(args)
            if _mupdf == '-':
                _mupdf = None
            elif _mupdf.startswith('git:') or '://' in _mupdf:
                os.environ['PYMUPDF_SETUP_MUPDF_BUILD'] = _mupdf
            else:
                assert os.path.isdir(_mupdf), f'Not a directory: {_mupdf=}'
                os.environ['PYMUPDF_SETUP_MUPDF_BUILD'] = os.path.abspath(_mupdf)
                mupdf_sync = _mupdf
        
        elif arg in ('-M', '--build-mupdf'):
            env_extra['PYMUPDF_SETUP_MUPDF_REBUILD'] = next(args)
        
        elif arg == '-o':
            os_names += next(args).split(',')
        
        elif arg == '-p':
            pytest_options += f' {next(args)}'
        
        elif arg == '-P':
            system_packages = int(next(args))
        
        elif arg == '--pybind':
            pybind = int(next(args))
        
        elif arg == '--pyodide-build-version':
            pyodide_build_version = next(args)
        
        elif arg == '-s':
            _value = next(args)
            assert _value in ('0', '1'), f'`-s` must be followed by `0` or `1`, not {_value=}.'
            env_extra['PYMUPDF_SETUP_PY_LIMITED_API'] = _value
        
        elif arg == '--show-args':
            show_args = 1
        elif arg == '--sync-paths':
            sync_paths = True
        
        elif arg == '--system-site-packages':
            system_site_packages = int(next(args))
        
        elif arg == '-t':
            test_names += next(args).split(',')
        
        elif arg == '--timeout':
            test_timeout = float(next(args))
        
        elif arg in ('-T', '--pytest-prefix'):
            pytest_prefix = next(args)
        
        elif arg == '-v':
            venv = int(next(args))
            assert venv in (0, 1, 2), f'Invalid {venv=} should be 0, 1 or 2.'
        
        elif arg == '--valgrind':
            _valgrind = int(next(args))
            if _valgrind == 1:
                pytest_prefix = 'valgrind'
            warnings += f'{arg=} is deprecated, use `-T _valgrind`.'
        
        elif arg in ('build', 'cibw', 'pyodide', 'test', 'wheel'):
            commands.append(arg)
        
        elif arg == 'buildtest':
            commands += ['build', 'test']
        
        elif arg == 'install':
            _pymupdf = next(args)
            commands.append(f'{arg}.{_pymupdf}')
        
        else:
            assert 0, f'Unrecognised option/command: {arg=}.'
    
    # Handle special args --sync-paths, -h, -v, -o first.
    #
    if sync_paths:
        # Just print required files, directories and checkouts.
        print(pymupdf_dir)
        if mupdf_sync:
            print(mupdf_sync)
        return

    if show_help:
        print(__doc__)
        return
    
    if show_args:
        print(f'sys.argv ({len(sys.argv)}):')
        for arg in sys.argv:
            print(f'    {arg!r}')
        return
    
    if os_names:
        if platform.system().lower() not in os_names:
            log(f'Not running because {platform.system().lower()=} not in {os_names=}')
            return
    
    if commands:
        if venv:
            # Rerun ourselves inside a venv if not already in a venv.
            if not venv_in():
                e = venv_run(
                        sys.argv,
                        f'venv-pymupdf-{platform.python_version()}-{int.bit_length(sys.maxsize+1)}',
                        recreate=(venv==2),
                        )
                sys.exit(e)
    else:
        log(f'Warning, no commands specified so nothing to do.')
    
    # Handle commands.
    #
    have_installed = False
    for command in commands:
        
        if 0:
            pass
        
        elif command in ('build', 'wheel'):
            build(
                    env_extra,
                    build_isolation=build_isolation,
                    venv=venv,
                    wheel=(command=='wheel'),
                    )
            have_installed = True
        
        elif command == 'cibw':
            # Build wheel(s) with cibuildwheel.
            cibuildwheel(env_extra, cibw_name, cibw_pyodide, cibw_sdist)
        
        elif command.startswith('install.'):
            name = command[len('install.'):]
            run(f'pip install --force-reinstall {name}')
            have_installed = True
        
        elif command == 'test':
            if not have_installed:
                log(f'## Warning: have not built/installed PyMuPDF; testing whatever is already installed.')
            test(
                    env_extra=env_extra,
                    implementations=implementations,
                    test_names=test_names,
                    pytest_options=pytest_options,
                    test_timeout=test_timeout,
                    pytest_prefix=pytest_prefix,
                    test_fitz=test_fitz,
                    pybind=pybind,
                    system_packages=system_packages,
                    venv=venv,
                    )
        
        elif command == 'pyodide':
            build_pyodide_wheel(pyodide_build_version=pyodide_build_version)
        
        else:
            assert 0, f'{command=}'


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


def github_workflow_unimportant():
    '''
    Returns true if we are running a Github scheduled workflow but in a
    repository not called 'PyMuPDF'. This can be used to avoid consuming
    unnecessary Github minutes running workflows on non-main repositories such
    as ArtifexSoftware/PyMuPDF-julian.
    '''
    GITHUB_EVENT_NAME = os.environ.get('GITHUB_EVENT_NAME')
    GITHUB_REPOSITORY = os.environ.get('GITHUB_REPOSITORY')
    if GITHUB_EVENT_NAME == 'schedule' and GITHUB_REPOSITORY != 'pymupdf/PyMuPDF':
            log(f'## This is an unimportant Github workflow: a scheduled event, not in the main repository `pymupdf/PyMuPDF`.')
            log(f'## {GITHUB_EVENT_NAME=}.')
            log(f'## {GITHUB_REPOSITORY=}.')
            return True

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
        env_extra,
        *,
        build_isolation,
        venv,
        wheel,
        ):
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
        if names:
            names = ' '.join(names)
            if venv == 2:
                run( f'python -m pip install --upgrade {names}')
            else:
                log(f'{venv=}: Not installing packages with pip: {names}')
        build_isolation_text = ' --no-build-isolation'
    
    if wheel:
        new_files = pipcl.NewFiles(f'wheelhouse/*.whl')
        run(f'pip wheel{build_isolation_text} -w wheelhouse -v {pymupdf_dir_abs}', env_extra=env_extra)
        wheel = new_files.get_one()
        run(f'pip install --force-reinstall {wheel}')
    else:
        run(f'pip install{build_isolation_text} -v --force-reinstall {pymupdf_dir_abs}', env_extra=env_extra)


def cibuildwheel(env_extra, cibw_name, cibw_pyodide, cibw_sdist):
    
    if cibw_sdist and platform.system() == 'Linux':
        log(f'Building sdist.')
        run(f'cd {pymupdf_dir_abs} && {sys.executable} setup.py -d wheelhouse sdist', env_extra=env_extra)
        sdists = glob.glob(f'{pymupdf_dir_abs}/wheelhouse/pymupdf-*.tar.gz')
        log(f'{sdists=}')
        assert sdists
    
    run(f'pip install --upgrade {cibw_name}')

    # Some general flags.
    if 'CIBW_BUILD_VERBOSITY' not in env_extra:
        env_extra['CIBW_BUILD_VERBOSITY'] = '1'
    if 'CIBW_SKIP' not in env_extra:
        env_extra['CIBW_SKIP'] = 'pp* *i686 cp36* cp37* *musllinux* *-win32 *-aarch64'

    # Set what wheels to build, if not already specified.
    if 'CIBW_ARCHS' not in env_extra:
        if 'CIBW_ARCHS_WINDOWS' not in env_extra:
            env_extra['CIBW_ARCHS_WINDOWS'] = 'auto64'

        if 'CIBW_ARCHS_MACOS' not in env_extra:
            env_extra['CIBW_ARCHS_MACOS'] = 'auto64'

        if 'CIBW_ARCHS_LINUX' not in env_extra:
            env_extra['CIBW_ARCHS_LINUX'] = 'auto64'

    # Tell cibuildwheel not to use `auditwheel` on Linux and MacOS,
    # because it cannot cope with us deliberately having required
    # libraries in different wheel - specifically in the PyMuPDF wheel.
    #
    # We cannot use a subset of auditwheel's functionality
    # with `auditwheel addtag` because it says `No tags
    # to be added` and terminates with non-zero. See:
    # https://github.com/pypa/auditwheel/issues/439.
    #
    env_extra['CIBW_REPAIR_WHEEL_COMMAND_LINUX'] = ''
    env_extra['CIBW_REPAIR_WHEEL_COMMAND_MACOS'] = ''

    # Tell cibuildwheel how to test PyMuPDF.
    if 'CIBW_TEST_COMMAND' not in env_extra:
        env_extra['CIBW_TEST_COMMAND'] = f'python {{project}}/scripts/test.py test'

    # Specify python versions.
    CIBW_BUILD = env_extra.get('CIBW_BUILD')
    log(f'{CIBW_BUILD=}')
    if CIBW_BUILD is None:
        if os.environ.get('GITHUB_ACTIONS') == 'true':
            # Build/test all supported Python versions.
            CIBW_BUILD = 'cp39* cp310* cp311* cp312* cp313*'
        else:
            # Build/test current Python only.
            v = platform.python_version_tuple()[:2]
            log(f'{v=}')
            CIBW_BUILD = f'cp{"".join(v)}*'

    # Pass all the environment variables we have set, to Linux
    # docker. Note that this will miss any settings in the original
    # environment.
    env_extra['CIBW_ENVIRONMENT_PASS_LINUX'] = ' '.join(sorted(env_extra.keys()))

    # Build for lowest (assumed first) Python version.
    #
    cibw_pyodide_arg = ' --platform pyodide' if cibw_pyodide else ''
    CIBW_BUILD_0 = CIBW_BUILD.split()[0]
    log(f'Building for first Python version {CIBW_BUILD_0}.')
    env_extra['CIBW_BUILD'] = CIBW_BUILD_0
    run(f'cd {pymupdf_dir} && cibuildwheel{cibw_pyodide_arg}', env_extra=env_extra)

    # Tell cibuildwheel to build and test all specified Python versions; it
    # will notice that the wheel we built above supports all versions of
    # Python, so will not actually do any builds here.
    #
    env_extra['CIBW_BUILD'] = CIBW_BUILD
    run(f'cd {pymupdf_dir} && cibuildwheel{cibw_pyodide_arg}', env_extra=env_extra)
    run(f'ls -ld {pymupdf_dir}/wheelhouse/*')
        

def build_pyodide_wheel(pyodide_build_version=None):
    '''
    Build Pyodide wheel.

    This runs `pyodide build` inside the PyMuPDF directory, which in turn runs
    setup.py in a Pyodide build environment.
    '''
    log(f'## Building Pyodide wheel.')

    # Our setup.py does not know anything about Pyodide; we set a few
    # required environmental variables here.
    #
    env_extra = dict()

    # Disable libcrypto because not available in Pyodide.
    env_extra['HAVE_LIBCRYPTO'] = 'no'

    # Tell MuPDF to build for Pyodide.
    env_extra['OS'] = 'pyodide'

    # Build a single wheel without a separate PyMuPDFb wheel.
    env_extra['PYMUPDF_SETUP_FLAVOUR'] = 'pb'
    
    # 2023-08-30: We set PYMUPDF_SETUP_MUPDF_BUILD_TESSERACT=0 because
    # otherwise mupdf thirdparty/tesseract/src/ccstruct/dppoint.cpp fails to
    # build because `#include "errcode.h"` finds a header inside emsdk. This is
    # pyodide bug https://github.com/pyodide/pyodide/issues/3839. It's fixed in
    # https://github.com/pyodide/pyodide/pull/3866 but the fix has not reached
    # pypi.org's pyodide-build package. E.g. currently in tag 0.23.4, but
    # current devuan pyodide-build is pyodide_build-0.23.4.
    #
    env_extra['PYMUPDF_SETUP_MUPDF_TESSERACT'] = '0'
    setup = pyodide_setup(pymupdf_dir, pyodide_build_version=pyodide_build_version)
    command = f'{setup} && echo "### Running pyodide build" && pyodide build --exports whole_archive'
    
    command = command.replace(' && ', '\n && ')
    
    run(command, env_extra=env_extra)
    
    # Copy wheel into `wheelhouse/` so it is picked up as a workflow
    # artifact.
    #
    run(f'ls -l {pymupdf_dir}/dist/')
    run(f'mkdir -p {pymupdf_dir}/wheelhouse && cp -p {pymupdf_dir}/dist/* {pymupdf_dir}/wheelhouse/')
    run(f'ls -l {pymupdf_dir}/wheelhouse/')    


def pyodide_setup(
        directory,
        clean=False,
        pyodide_build_version=None,
        ):
    '''
    Returns a command that will set things up for a pyodide build.
    
    Args:
        directory:
            Our command cd's into this directory.
        clean:
            If true we create an entirely new environment. Otherwise
            we reuse any existing emsdk repository and venv.
        pyodide_build_version:
            Version of Python package pyodide-build; if None we use latest
            available version.
            2025-02-13: pyodide_build_version='0.29.3' works.
    
    The returned command does the following:
    
    * Checkout latest emsdk from https://github.com/emscripten-core/emsdk.git:
      * Clone emsdk repository to `emsdk` if not already present.
      * Run `git pull -r` inside emsdk checkout.
    * Create venv `venv_pyodide_<python_version>` if not already present.
    * Activate venv `venv_pyodide_<python_version>`.
    * Install/upgrade package `pyodide-build`.
    * Run emsdk install scripts and enter emsdk environment.
    
    Example usage in a build function:
    
        command = pyodide_setup()
        command += ' && pyodide build --exports pyinit'
        subprocess.run(command, shell=1, check=1)
    '''
    
    pv = platform.python_version_tuple()[:2]
    assert pv == ('3', '12'), f'Pyodide builds need to be run with Python-3.12 but current Python is {platform.python_version()}.'
    command = f'cd {directory}'
    
    # Clone/update emsdk. We always use the latest emsdk with `git pull`.
    #
    # 2025-02-13: this works: 2514ec738de72cebbba7f4fdba0cf2fabcb779a5
    #
    dir_emsdk = 'emsdk'
    if clean:
        shutil.rmtree(dir_emsdk, ignore_errors=1)
        # 2024-06-25: old `.pyodide-xbuildenv` directory was breaking build, so
        # important to remove it here.
        shutil.rmtree('.pyodide-xbuildenv', ignore_errors=1)
    if not os.path.exists(f'{directory}/{dir_emsdk}'):
        command += f' && echo "### Cloning emsdk.git"'
        command += f' && git clone https://github.com/emscripten-core/emsdk.git {dir_emsdk}'
    command += f' && echo "### Updating checkout {dir_emsdk}"'
    command += f' && (cd {dir_emsdk} && git pull -r)'
    command += f' && echo "### Checkout {dir_emsdk} is:"'
    command += f' && (cd {dir_emsdk} && git show -s --oneline)'
    
    # Create and enter Python venv.
    #
    python = sys.executable
    venv_pyodide = f'venv_pyodide_{sys.version_info[0]}.{sys.version_info[1]}'
    
    if not os.path.exists( f'{directory}/{venv_pyodide}'):
        command += f' && echo "### Creating venv {venv_pyodide}"'
        command += f' && {python} -m venv {venv_pyodide}'
    command += f' && . {venv_pyodide}/bin/activate'
    command += f' && echo "### Installing Python packages."'
    command += f' && python -m pip install --upgrade pip wheel pyodide-build'
    if pyodide_build_version:
        command += f'=={pyodide_build_version}'
    
    # Run emsdk install scripts and enter emsdk environment.
    #
    command += f' && cd {dir_emsdk}'
    command += ' && PYODIDE_EMSCRIPTEN_VERSION=$(pyodide config get emscripten_version)'
    command += ' && echo "### PYODIDE_EMSCRIPTEN_VERSION is: $PYODIDE_EMSCRIPTEN_VERSION"'
    command += ' && echo "### Running ./emsdk install"'
    command += ' && ./emsdk install ${PYODIDE_EMSCRIPTEN_VERSION}'
    command += ' && echo "### Running ./emsdk activate"'
    command += ' && ./emsdk activate ${PYODIDE_EMSCRIPTEN_VERSION}'
    command += ' && echo "### Running ./emsdk_env.sh"'
    command += ' && . ./emsdk_env.sh'   # Need leading `./` otherwise weird 'Not found' error.
    
    command += ' && cd ..'
    return command


def test(
        *,
        env_extra,
        implementations,
        venv=False,
        test_names=None,
        pytest_options=None,
        test_timeout=None,
        pytest_prefix=None,
        test_fitz=True,
        pytest_k=None,
        pybind=False,
        system_packages=False,
        ):
    if pybind:
        cpp_path = 'pymupdf_test_pybind.cpp'
        cpp_exe = 'pymupdf_test_pybind.exe'
        cpp = textwrap.dedent('''
                #include <pybind11/embed.h>
                
                int main()
                {
                    pybind11::scoped_interpreter guard{};
                    pybind11::exec(R"(
                            print('Hello world', flush=1)
                            import pymupdf
                            pymupdf.JM_mupdf_show_warnings = 1
                            print(f'{pymupdf.version=}', flush=1)
                            doc = pymupdf.Document()
                            pymupdf.mupdf.fz_warn('Dummy warning.')
                            pymupdf.mupdf.fz_warn('Dummy warning.')
                            pymupdf.mupdf.fz_warn('Dummy warning.')
                            print(f'{doc=}', flush=1)
                            )");
                }
                ''')
        def fs_read(path):
            try:
                with open(path) as f:
                    return f.read()
            except Exception:
                return
        def fs_remove(path):
            try:
                os.remove(path)
            except Exception:
                pass
        cpp_existing = fs_read(cpp_path)
        if cpp == cpp_existing:
            log(f'Not creating {cpp_exe} because unchanged: {cpp_path}')
        else:
            with open(cpp_path, 'w') as f:
                f.write(cpp)
        def getmtime(path):
            try:
                return os.path.getmtime(path)
            except Exception:
                return 0
        python_config = f'{os.path.realpath(sys.executable)}-config'
        # `--embed` adds `-lpython3.11` to the link command, which appears to
        # be necessary when building an executable.
        flags = run(f'{python_config} --cflags --ldflags --embed', capture=1)
        build_command = f'c++ {cpp_path} -o {cpp_exe} -g -W -Wall {flags}'
        build_path = f'{cpp_exe}.cmd'
        build_command_prev = fs_read(build_path)
        if build_command != build_command_prev or getmtime(cpp_path) >= getmtime(cpp_exe):
            fs_remove(build_path)
            run(build_command)
            with open(build_path, 'w') as f:
                f.write(build_command)
        run(f'./{cpp_exe}')
        return
    
    pymupdf_dir_rel = gh_release.relpath(pymupdf_dir)
    if not pytest_options and pytest_prefix == 'valgrind':
        pytest_options = '-sv'
    if pytest_k:
        pytest_options += f' -k {shlex.quote(pytest_k)}'
    pytest_arg = ''
    if test_names:
        for test_name in test_names:
            pytest_arg += f' {pymupdf_dir_rel}/{test_name}'
    else:
        pytest_arg += f' {pymupdf_dir_rel}/tests'
    python = gh_release.relpath(sys.executable)
    log('Running tests with tests/run_compound.py and pytest.')
    
    if venv == 2:
        run(f'pip install --upgrade {gh_release.test_packages}')
    else:
        log(f'{venv=}: Not installing test packages: {gh_release.test_packages}')
    run_compound_args = ''
    
    if implementations:
        run_compound_args += f' -i {implementations}'
    
    if test_timeout:
        run_compound_args += f' -t {test_timeout}'

    if pytest_prefix in ('valgrind', 'helgrind'):
        if system_packages:
            log('Installing valgrind.')
            run(f'sudo apt update')
            run(f'sudo apt install --upgrade valgrind')
        run(f'valgrind --version')

    command = f'{python} {pymupdf_dir_rel}/tests/run_compound.py{run_compound_args}'
    
    if pytest_prefix is None:
        pass
    elif pytest_prefix == 'gdb':
        command += ' gdb --args'
    elif pytest_prefix == 'valgrind':
        env_extra['PYMUPDF_RUNNING_ON_VALGRIND'] = '1'
        env_extra['PYTHONMALLOC'] = 'malloc'
        command += (
                    f' valgrind'
                    f' --suppressions={pymupdf_dir_abs}/valgrind.supp'
                    f' --trace-children=no'
                    f' --num-callers=20'
                    f' --error-exitcode=100'
                    f' --errors-for-leak-kinds=none'
                    f' --fullpath-after='
                    )
    elif pytest_prefix == 'helgrind':
        env_extra['PYMUPDF_RUNNING_ON_VALGRIND'] = '1'
        env_extra['PYTHONMALLOC'] = 'malloc'
        command = (
                f' valgrind'
                f' --tool=helgrind'
                f' --trace-children=no'
                f' --num-callers=20'
                f' --error-exitcode=100'
                f' --fullpath-after='
                )
    else:
        assert 0, f'Unrecognised {pytest_prefix=}'

    if platform.system() == 'Windows':
        # `python -m pytest` doesn't seem to work.
        command += ' pytest'
    else:
        # On OpenBSD `pip install pytest` doesn't seem to install the pytest
        # command, so we use `python -m pytest ...`.
        command += f' {python} -m pytest'

    command += f' {pytest_options} {pytest_arg}'

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
    try:
        log(f'Running tests with tests/run_compound.py and pytest.')
        run(command, env_extra=env_extra, timeout=test_timeout)
            
    except subprocess.TimeoutExpired as e:
         log(f'Timeout when running tests.')
         raise
    finally:
        log(f'\n'
                f'[As of 2024-10-10 we get warnings from pytest/Python such as:\n'
                f'    DeprecationWarning: builtin type SwigPyPacked has no __module__ attribute\n'
                f'This seems to be due to Swig\'s handling of Py_LIMITED_API.\n'
                f'For details see https://github.com/swig/swig/issues/2881.\n'
                f']'
                )
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


def venv_in(path=None):
    '''
    If path is None, returns true if we are in a venv. Otherwise returns true
    only if we are in venv <path>.
    '''
    if path:
        return os.path.abspath(sys.prefix) == os.path.abspath(path)
    else:
        return sys.prefix != sys.base_prefix


def venv_run(args, path, recreate=True):
    '''
    Runs command inside venv and returns termination code.
    
    Args:
        args:
            List of args.
        path:
            Name of venv.
        recreate:
            If false we do not run `<sys.executable> -m venv <path>` if <path>
            already exists. This avoids a delay in the common case where <path>
            is already set up, but fails if <path> exists but does not contain
            a valid venv.
    '''
    if recreate or not os.path.isdir(path):
        run(f'{sys.executable} -m venv {path}')
    if platform.system() == 'Windows':
        command = f'{path}\\Scripts\\activate'
    else:
        command = f'. {path}/bin/activate'
    command += f' && python {shlex.join(args)}'
    e = run(command, check=0)
    return e


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
