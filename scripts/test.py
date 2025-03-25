#! /usr/bin/env python3

'''Developer build/test script for PyMuPDF.

Examples:

    ./PyMuPDF/scripts/test.py --mupdf mupdf buildtest
        Build and test with pre-existing local mupdf/ checkout.

    ./PyMuPDF/scripts/test.py buildtest
        Build and test with default internal download of mupdf.

    ./PyMuPDF/scripts/test.py --mupdf 'git:https://git.ghostscript.com/mupdf.git' buildtest
        Build and test with internal checkout of mupdf master.

    ./PyMuPDF/scripts/test.py --mupdf 'git:--branch 1.25.x https://github.com/ArtifexSoftware/mupdf.git' buildtest
        Build and test using internal checkout of mupdf 1.25.x branch from Github.

Usage:
    scripts/test.py <options> <command(s)>

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
        Equivalent to `-b debug`.
    -f 0|1
        If 1 we also test alias `fitz` as well as `pymupdf`. Default is '0'.
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
    -p <pytest-options>
        Set pytest options; default is ''.
    -P 0|1
        If 1, automatically install required packages such as Valgrind. Default
        is 0.
    -s 0 | 1
        If 1 (the default), build with Python Limited API/Stable ABI.
    -t <names>
        Pytest test names, comma-separated. Should be relative to PyMuPDF
        directory. For example:
            -t tests/test_general.py
            -t tests/test_general.py::test_subset_fonts
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
    --build-flavour <build_flavour>
        Combination of 'p', 'b', 'd'. See ../setup.py's description of
        PYMUPDF_SETUP_FLAVOUR. Default is 'pbd', i.e. self-contained PyMuPDF
        wheels including MuPDF build-time files.
    --build-mupdf 0|1
        Whether to rebuild mupdf when we build PyMuPDF. Default is 1.
    --gdb 0|1
        Run tests under gdb. Requires user interaction.
    --pytest-prefix <command>
        Use specified prefix when running pytest. E.g. `gdb --args`.
    --pybind 0|1
        Experimental, for investigating
        https://github.com/pymupdf/PyMuPDF/issues/3869. Runs run basic code
        inside C++ pybind. Requires `sudo apt install pybind11-dev` or similar.
    --pymupdf-pypi <name>
        Do not build PyMuPDF, instead install with `pip install <name>`. For
        example allows testing of a specific version with `--pymupdf-pypi
        pymupdf==x.y.z`.
    --system-site-packages 0|1
        If 1, use `--system-site-packages` when creating venv. Defaults is 0.
    --timeout <seconds>
        Sets timeout when running tests.
    --valgrind 0|1
        Use valgrind in `test` or `buildtest`.
        This will run `sudo apt update` and `sudo apt install valgrind`.
    --valgrind-args <valgrind_args>
        Extra args to valgrind.

Commands:
    build
        Builds and installs PyMuPDF into venv, using `pip install .../PyMuPDF`.
    buildtest
        Same as 'build test'.
    test
        Runs PyMuPDF's pytest tests in venv. Default is to test rebased and
        unoptimised rebased; use `-i` to change this.
    wheel
        Build wheel.
    pyodide_wheel
        Build Pyodide wheel. We clone `emsdk.git`, set it up, and run
        `pyodide build`. This runs our setup.py with CC etc set up
        to create Pyodide binaries in a wheel called, for example,
        `PyMuPDF-1.23.2-cp311-none-emscripten_3_1_32_wasm32.whl`.
        
        It seems that sys.version must match the Python version inside emsdk;
        as of 2025-02-14 this is 3.12. Otherwise we get build errors such as:
            [wasm-validator error in function 723] unexpected false: all used features should be allowed, on ...
            

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

sys.path.insert(0, pymupdf_dir)
import pipcl
del sys.path[0]

log = pipcl.log0
run = pipcl.run


def main(argv):

    if github_workflow_unimportant():
        return
    
    if len(argv) == 1:
        show_help()
        return
    
    log(f'{sys.executable=}')
    log(f'{sys.version=}')

    build_isolation = None
    valgrind = False
    valgrind_args = ''
    s = True
    build_do = 'i'
    build_type = None
    build_mupdf = True
    build_flavour = 'pbd'
    gdb = False
    test_fitz = False
    implementations = 'r'
    test_names = list()
    venv = 2
    pytest_prefix = None
    pybind = False
    pytest_options = None
    timeout = None
    pytest_k = None
    system_site_packages = False
    pyodide_build_version = None
    packages = False
    pymupdf_pypi = None
    
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
            if not mupdf.startswith('git:') and '://' not in mupdf and mupdf != '-':
                assert os.path.isdir(mupdf), f'Not a directory: {mupdf=}.'
                mupdf = os.path.abspath(mupdf)
            os.environ['PYMUPDF_SETUP_MUPDF_BUILD'] = mupdf
        elif arg == '-k':
            pytest_k = next(args)
        elif arg == '-p':
            pytest_options = next(args)
        elif arg == '-P':
            packages = int(next(args))
        elif arg == '-s':
            value = next(args)
            assert value in ('0', '1'), f'`-s` must be followed by `0` or `1`, not {value=}.'
            os.environ['PYMUPDF_SETUP_PY_LIMITED_API'] = value
        elif arg == '--pytest-prefix':
            pytest_prefix = next(args)
        elif arg == '--pybind':
            pybind = int(next(args))
        elif arg == '--system-site-packages':
            system_site_packages = int(next(args))
        elif arg == '-t':
            test_names += next(args).split(',')
        elif arg == '--timeout':
            timeout = float(next(args))
        elif arg == '-v':
            venv = int(next(args))
        elif arg == '--build-flavour':
            build_flavour = next(args)
        elif arg == '--build-mupdf':
            build_mupdf = int(next(args))
        elif arg == '--gdb':
            gdb = int(next(args))
        elif arg == '--valgrind':
            valgrind = int(next(args))
        elif arg == '--valgrind-args':
            valgrind_args = next(args)
        elif arg == '--pyodide-build-version':
            pyodide_build_version = next(args)
        elif arg == '--pymupdf-pypi':
            pymupdf_pypi = next(args)
        else:
            assert 0, f'Unrecognised option: {arg=}.'
    
    if arg is None:
        log(f'No command specified.')
        return
    
    commands = list()
    while 1:
        assert arg in ('build', 'buildtest', 'test', 'wheel', 'pyodide_wheel'), \
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

    def do_build(wheel=False):
        if pymupdf_pypi:
            run(f'pip install --force-reinstall {pymupdf_pypi}')
        else:
            build(
                    build_type=build_type,
                    build_isolation=build_isolation,
                    venv_quick=venv_quick,
                    build_mupdf=build_mupdf,
                    build_flavour=build_flavour,
                    wheel=wheel,
                    )
    def do_test():
        test(
                implementations=implementations,
                valgrind=valgrind,
                valgrind_args=valgrind_args,
                venv_quick=venv_quick,
                test_names=test_names,
                pytest_options=pytest_options,
                timeout=timeout,
                gdb=gdb,
                pytest_prefix=pytest_prefix,
                test_fitz=test_fitz,
                pytest_k=pytest_k,
                pybind=pybind,
                packages=packages,
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
        elif command == 'wheel':
            do_build(wheel=True)
        elif command == 'pyodide_wheel':
            build_pyodide_wheel(pyodide_build_version=pyodide_build_version)
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
        build_type=None,
        build_isolation=None,
        venv_quick=False,
        build_mupdf=True,
        build_flavour='pb',
        wheel=False,
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
        if names:
            names = ' '.join(names)
            if venv_quick:
                log(f'{venv_quick=}: Not installing packages with pip: {names}')
            else:
                run( f'python -m pip install --upgrade {names}')
        build_isolation_text = ' --no-build-isolation'
    
    env_extra = dict()
    if not build_mupdf:
        env_extra['PYMUPDF_SETUP_MUPDF_REBUILD'] = '0'
    if build_type:
        env_extra['PYMUPDF_SETUP_MUPDF_BUILD_TYPE'] = build_type
    if build_flavour:
        env_extra['PYMUPDF_SETUP_FLAVOUR'] = build_flavour
    if wheel:
        run(f'pip wheel{build_isolation_text} -v {pymupdf_dir}', env_extra=env_extra)
    else:
        run(f'pip install{build_isolation_text} -v {pymupdf_dir}', env_extra=env_extra)


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
        implementations,
        valgrind,
        valgrind_args,
        venv_quick=False,
        test_names=None,
        pytest_options=None,
        timeout=None,
        gdb=False,
        pytest_prefix=None,
        test_fitz=True,
        pytest_k=None,
        pybind=False,
        packages=False,
        ):
    '''
    Args:
        implementations:
            See top-level option `-i`.
        valgrind:
            See top-level option `--valgrind`.
        valgrind_args:
            See top-level option `--valgrind-args`.
        venv_quick:
            .
        test_names:
            See top-level option `-t`.
        pytest_options:
            See top-level option `-p`.
        gdb:
            See top-level option `--gdb`.
        pytest_prefix:
            See top-level option `--pytest-prefix`.
        test_fitz:
            See top-level option `-f`.
    '''
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
            run(f'pip install --upgrade {gh_release.test_packages}')
        run_compound_args = ''
        if implementations:
            run_compound_args += f' -i {implementations}'
        if timeout:
            run_compound_args += f' -t {timeout}'
        env_extra = None
        if valgrind:
            if packages:
                log('Installing valgrind.')
                run(f'sudo apt update')
                run(f'sudo apt install --upgrade valgrind')
            run(f'valgrind --version')
        
            log('Running PyMuPDF tests under valgrind.')
            command = (
                    f'{python} {pymupdf_dir_rel}/tests/run_compound.py{run_compound_args}'
                        f' valgrind --suppressions={pymupdf_dir_rel}/valgrind.supp --error-exitcode=100 --errors-for-leak-kinds=none --fullpath-after= {valgrind_args}'
                        f' {python} -m pytest {pytest_options}{pytest_arg}'
                        )
            env_extra=dict(
                    PYTHONMALLOC='malloc',
                    PYMUPDF_RUNNING_ON_VALGRIND='1',
                    )
        elif gdb:
            command = f'{python} {pymupdf_dir_rel}/tests/run_compound.py{run_compound_args} gdb --args {python} -m pytest {pytest_options} {pytest_arg}'
        elif pytest_prefix:
            command = f'{python} {pymupdf_dir_rel}/tests/run_compound.py{run_compound_args} {pytest_prefix} {python} -m pytest {pytest_options} {pytest_arg}'
        elif platform.system() == 'Windows':
            # `python -m pytest` doesn't seem to work.
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
        run(command, env_extra=env_extra, timeout=timeout)
            
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
