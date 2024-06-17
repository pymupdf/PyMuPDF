#! /usr/bin/env python3

'''
Build+test script for PyMuPDF using cibuildwheel. Mostly for use with github
builds but can also be used to build Pyodide wheels.

We run cibuild manually, in order to build and test the two wheel
flavours that make up PyMuPDF:

    PyMuPDFb
        Not specific to particular versions of Python. Contains shared
        libraries for the MuPDF C and C++ bindings.
    PyMuPDF
        Specific to particular versions of Python. Contains the rest of
        the PyMuPDF implementation.

Args:
    build
        Build using cibuild.
    build-devel
        Build using cibuild with `--platform` set.
    pip_install <prefix>
        For internal use. Runs `pip install <prefix>-*<platform_tag>.whl`,
        where `platform_tag` will be things like 'win32', 'win_amd64',
        'x86_64`, depending on the python we are running on.
    venv
        Run with remaining args inside a venv.
    test
        Internal.

We also look at specific items in the environment, should be unset (treated as
'0'), '0' or '1'. We use environment variables here to allow use with Github
action inputs, which can't be easily translated into command-line arguments.

    inputs_flavours
        If unset or '1', build separate PyMuPDF and PyMuPDFb wheels.
        If '0', build complete PyMuPDF wheels.
    inputs_sdist
    inputs_skeleton
        Build minimal wheel; for testing only.
    inputs_wheels_cps:
        Python versions to build for. E.g. 'cp38* cp312*'.
    inputs_wheels_default
        Default value for other inputs_wheels_*.
    inputs_wheels_linux_aarch64
    inputs_wheels_linux_auto
    inputs_wheels_linux_pyodide
    inputs_wheels_macos_arm64
    inputs_wheels_macos_auto
    inputs_wheels_windows_auto
    inputs_PYMUPDF_SETUP_MUPDF_BUILD
        Used to directly set PYMUPDF_SETUP_MUPDF_BUILD.
        E.g. 'git:--recursive --depth 1 --shallow-submodules --branch master https://github.com/ArtifexSoftware/mupdf.git'
    inputs_PYMUPDF_SETUP_MUPDF_BUILD_TYPE
        Used to directly set PYMUPDF_SETUP_MUPDF_BUILD_TYPE.
    inputs_wheels_implementations
        Used to directly set PYMUPDF_SETUP_IMPLEMENTATIONS.
        'a', 'b', 'ab'.

Building for Pyodide

    If `inputs_wheels_linux_pyodide` is true and we are on Linux, we clone
    `emsdk.git`, set it up, and run `pyodide build`. This runs our setup.py
    with CC etc set up to create Pyodide binaries in a wheel called, for
    example, `PyMuPDF-1.23.2-cp311-none-emscripten_3_1_32_wasm32.whl`.

Example usage:

     PYMUPDF_SETUP_MUPDF_BUILD=../mupdf py -3.9-32 PyMuPDF/scripts/gh_release.py venv build-devel
'''

import glob
import inspect
import os
import platform
import shlex
import subprocess
import sys
import textwrap


pymupdf_dir = os.path.abspath( f'{__file__}/../..')

def main():

    log( '### main():')
    log(f'{platform.platform()=}')
    log(f'{platform.python_version()=}')
    log(f'{platform.architecture()=}')
    log(f'{platform.machine()=}')
    log(f'{platform.processor()=}')
    log(f'{platform.release()=}')
    log(f'{platform.system()=}')
    log(f'{platform.version()=}')
    log(f'{platform.uname()=}')
    log(f'{sys.executable=}')
    log(f'{sys.maxsize=}')
    log(f'sys.argv ({len(sys.argv)}):')
    for i, arg in enumerate(sys.argv):
        log(f'    {i}: {arg!r}')
    log(f'os.environ ({len(os.environ)}):')
    for k in sorted( os.environ.keys()):
        v = os.environ[ k]
        log( f'    {k}: {v!r}')
    
    valgrind = False
    if len( sys.argv) == 1:
        args = iter( ['build'])
    else:
        args = iter( sys.argv[1:])
    while 1:
        try:
            arg = next(args)
        except StopIteration:
            break
        if arg == 'build':
            build(valgrind=valgrind)
        elif arg == 'build-devel':
            if platform.system() == 'Linux':
                p = 'linux'
            elif platform.system() == 'Windows':
                p = 'windows'
            elif platform.system() == 'Darwin':
                p = 'macos'
            else:
                assert 0, f'Unrecognised {platform.system()=}'
            build(platform_=p)
        elif arg == 'pip_install':
            prefix = next(args)
            d = os.path.dirname(prefix)
            log( f'{prefix=}')
            log( f'{d=}')
            for leaf in os.listdir(d):
                log( f'    {d}/{leaf}')
            pattern = f'{prefix}-*{platform_tag()}.whl'
            paths = glob.glob( pattern)
            log( f'{pattern=} {paths=}')
            # Follow pipcl.py and look at AUDITWHEEL_PLAT. This allows us to
            # cope if building for both musl and normal linux.
            awp = os.environ.get('AUDITWHEEL_PLAT')
            if awp:
                paths = [i for i in paths if awp in i]
                log(f'After selecting AUDITWHEEL_PLAT={awp!r}, {paths=}.')
            paths = ' '.join( paths)
            run( f'pip install {paths}')
        elif arg == 'venv':
            command = ['python', sys.argv[0]]
            for arg in args:
                command.append( arg)
            venv( command, packages = 'cibuildwheel')
        elif arg == 'test':
            project = next(args)
            package = next(args)
            test( project, package, valgrind=valgrind)
        elif arg == '--valgrind':
            valgrind = int(next(args))
        else:
            assert 0, f'Unrecognised {arg=}'


def build( platform_=None, valgrind=False): 
    log( '### build():')   
    
    platform_arg = f' --platform {platform_}' if platform_ else ''
    
    # Parameters are in os.environ, as that seems to be the only way that
    # Github workflow .yml files can encode them.
    #
    def get_bool(name, default=0):
        v = os.environ.get(name)
        if v in ('1', 'true'):
            return 1
        elif v in ('0', 'false'):
            return 0
        elif v is None:
            return default
        else:
            assert 0, f'Bad environ {name=} {v=}'
    inputs_flavours = get_bool('inputs_flavours', 1)
    inputs_sdist = get_bool('inputs_sdist')
    inputs_skeleton = os.environ.get('inputs_skeleton')
    inputs_wheels_default = get_bool('inputs_wheels_default', 1)
    inputs_wheels_linux_aarch64 = get_bool('inputs_wheels_linux_aarch64', inputs_wheels_default)
    inputs_wheels_linux_auto = get_bool('inputs_wheels_linux_auto', inputs_wheels_default)
    inputs_wheels_linux_pyodide = get_bool('inputs_wheels_linux_pyodide', 0)
    inputs_wheels_macos_arm64 = get_bool('inputs_wheels_macos_arm64', 0)
    inputs_wheels_macos_auto = get_bool('inputs_wheels_macos_auto', inputs_wheels_default)
    inputs_wheels_windows_auto = get_bool('inputs_wheels_windows_auto', inputs_wheels_default)
    inputs_wheels_cps = os.environ.get('inputs_wheels_cps')
    inputs_PYMUPDF_SETUP_MUPDF_BUILD = os.environ.get('inputs_PYMUPDF_SETUP_MUPDF_BUILD')
    inputs_PYMUPDF_SETUP_MUPDF_BUILD_TYPE = os.environ.get('inputs_PYMUPDF_SETUP_MUPDF_BUILD_TYPE')
    inputs_wheels_implementations = os.environ.get('inputs_wheels_implementations', 'b')
    
    log( f'{inputs_flavours=}')
    log( f'{inputs_sdist=}')
    log( f'{inputs_skeleton=}')
    log( f'{inputs_wheels_default=}')
    log( f'{inputs_wheels_linux_aarch64=}')
    log( f'{inputs_wheels_linux_auto=}')
    log( f'{inputs_wheels_linux_pyodide=}')
    log( f'{inputs_wheels_macos_arm64=}')
    log( f'{inputs_wheels_macos_auto=}')
    log( f'{inputs_wheels_windows_auto=}')
    log( f'{inputs_wheels_cps=}')
    log( f'{inputs_PYMUPDF_SETUP_MUPDF_BUILD=}')
    log( f'{inputs_PYMUPDF_SETUP_MUPDF_BUILD_TYPE=}')
    
    # Build Pyodide wheel if specified.
    #
    if platform.system() == 'Linux' and inputs_wheels_linux_pyodide:
        build_pyodide_wheel(inputs_wheels_implementations, inputs_PYMUPDF_SETUP_MUPDF_BUILD)
    
    # Build sdist(s).
    #
    if inputs_sdist:
        if pymupdf_dir != os.path.abspath( os.getcwd()):
            log( f'Changing dir to {pymupdf_dir=}')
            os.chdir( pymupdf_dir)
        # Create PyMuPDF sdist.
        run(f'{sys.executable} setup.py sdist')
        assert glob.glob('dist/PyMuPDF-*.tar.gz')
        if inputs_flavours:
            # Create PyMuPDFb sdist.
            run(
                    f'{sys.executable} setup.py sdist',
                    env_extra=dict(PYMUPDF_SETUP_FLAVOUR='b'),
                    )
            assert glob.glob('dist/PyMuPDFb-*.tar.gz')
    
    # Build wheels.
    #
    if (0
            or inputs_wheels_linux_aarch64
            or inputs_wheels_linux_auto
            or inputs_wheels_macos_arm64
            or inputs_wheels_macos_auto
            or inputs_wheels_windows_auto
            ):
        env_extra = dict()
    
        def set_if_unset(name, value):
            v = os.environ.get(name)
            if v is None:
                log( f'Setting environment {name=} to {value=}')
                env_extra[ name] = value
            else:
                log( f'Not changing {name}={v!r} to {value!r}')
        set_if_unset( 'CIBW_BUILD_VERBOSITY', '3')
        # We exclude pp* because of `fitz_wrap.obj : error LNK2001: unresolved
        # external symbol PyUnicode_DecodeRawUnicodeEscape`.
        # 2024-06-05: musllinux on aarch64 fails because libclang cannot find
        # libclang.so.
        set_if_unset( 'CIBW_SKIP', '"pp* *i686 cp36* cp37* *musllinux*aarch64*"')
    
        def make_string(*items):
            ret = list()
            for item in items:
                if item:
                    ret.append(item)
            return ' '.join(ret)
    
        cps = inputs_wheels_cps if inputs_wheels_cps else 'cp38* cp39* cp310* cp311* cp312*'
        set_if_unset( 'CIBW_BUILD', cps)
    
        if platform.system() == 'Linux':
            set_if_unset(
                    'CIBW_ARCHS_LINUX',
                    make_string(
                        'auto64' * inputs_wheels_linux_auto,
                        'aarch64' * inputs_wheels_linux_aarch64,
                        ),
                    )
            if env_extra.get('CIBW_ARCHS_LINUX') == '':
                log(f'Not running cibuildwheel because CIBW_ARCHS_LINUX is empty string.')
                return
    
        if platform.system() == 'Windows':
            set_if_unset(
                    'CIBW_ARCHS_WINDOWS',
                    make_string(
                        'auto' * inputs_wheels_windows_auto,
                        ),
                    )
            if env_extra.get('CIBW_ARCHS_WINDOWS') == '':
                log(f'Not running cibuildwheel because CIBW_ARCHS_WINDOWS is empty string.')
                return
    
        if platform.system() == 'Darwin':
            set_if_unset(
                    'CIBW_ARCHS_MACOS',
                    make_string(
                        'auto' * inputs_wheels_macos_auto,
                        'arm64' * inputs_wheels_macos_arm64,
                        ),
                    )
            if env_extra.get('CIBW_ARCHS_MACOS') == '':
                log(f'Not running cibuildwheel because CIBW_ARCHS_MACOS is empty string.')
                return
    
        def env_pass(name):
            '''
            Adds `name` to CIBW_ENVIRONMENT_PASS_LINUX if required to be available
            when building wheel with cibuildwheel.
            '''
            if platform.system() == 'Linux':
                v = env_extra.get('CIBW_ENVIRONMENT_PASS_LINUX', '')
                if v:
                    v += ' '
                v += name
                env_extra['CIBW_ENVIRONMENT_PASS_LINUX'] = v
    
        def env_set(name, value, pass_=False):
            assert isinstance( value, str)
            if not name.startswith('CIBW'):
                assert pass_, f'{name=} {value=}'
            env_extra[ name] = value
            if pass_:
                env_pass(name)

        if os.environ.get('PYMUPDF_SETUP_LIBCLANG'):
            env_pass('PYMUPDF_SETUP_LIBCLANG')
    
        env_set('PYMUPDF_SETUP_IMPLEMENTATIONS', inputs_wheels_implementations, pass_=1)
        if inputs_skeleton:
            env_set('PYMUPDF_SETUP_SKELETON', inputs_skeleton, pass_=1)
    
        if inputs_PYMUPDF_SETUP_MUPDF_BUILD not in ('-', None):
            log(f'Setting PYMUPDF_SETUP_MUPDF_BUILD to {inputs_PYMUPDF_SETUP_MUPDF_BUILD!r}.')
            env_set('PYMUPDF_SETUP_MUPDF_BUILD', inputs_PYMUPDF_SETUP_MUPDF_BUILD, pass_=True)
            env_set('PYMUPDF_SETUP_MUPDF_TGZ', '', pass_=True)   # Don't put mupdf in sdist.
    
        if inputs_PYMUPDF_SETUP_MUPDF_BUILD_TYPE not in ('-', None):
            log(f'Setting PYMUPDF_SETUP_MUPDF_BUILD_TYPE to {inputs_PYMUPDF_SETUP_MUPDF_BUILD_TYPE!r}.')
            env_set('PYMUPDF_SETUP_MUPDF_BUILD_TYPE', inputs_PYMUPDF_SETUP_MUPDF_BUILD_TYPE, pass_=True)
    
        def set_cibuild_test():
            log( f'set_cibuild_test(): {inputs_skeleton=}')
            valgrind_text = ''
            if valgrind:
                valgrind_text = ' --valgrind 1'
            env_set('CIBW_TEST_COMMAND', f'python {{project}}/scripts/gh_release.py{valgrind_text} test {{project}} {{package}}')
    
        if pymupdf_dir != os.path.abspath( os.getcwd()):
            log( f'Changing dir to {pymupdf_dir=}')
            os.chdir( pymupdf_dir)
    
        run('pip install cibuildwheel')
    
        if inputs_flavours:
            # Build and test PyMuPDF and PyMuPDFb wheels.
            #
        
            # First build PyMuPDFb wheel. cibuildwheel will build a single wheel
            # here, which will work with any python version on current OS.
            #
            env_set( 'PYMUPDF_SETUP_FLAVOUR', 'b', pass_=1)
            run( f'cibuildwheel{platform_arg}', env_extra)
            run( 'echo after flavour=b')
            run( 'ls -l wheelhouse')

            # Now set environment to build PyMuPDF wheels. cibuildwheel will build
            # one for each Python version.
            #
        
            # Tell cibuildwheel not to use `auditwheel`, because it cannot cope
            # with us deliberately putting required libraries into a different
            # wheel.
            #
            # Also, `auditwheel addtag` says `No tags to be added` and terminates
            # with non-zero. See: https://github.com/pypa/auditwheel/issues/439.
            #
            env_set('CIBW_REPAIR_WHEEL_COMMAND_LINUX', '')
            env_set('CIBW_REPAIR_WHEEL_COMMAND_MACOS', '')
        
            # We tell cibuildwheel to test these wheels, but also set
            # CIBW_BEFORE_TEST to make it first run ourselves with the
            # `pip_install` arg to install the PyMuPDFb wheel. Otherwise
            # installation of PyMuPDF would fail because it lists the
            # PyMuPDFb wheel as a prerequisite. We need to use `pip_install`
            # because wildcards do not work on Windows, and we want to be
            # careful to avoid incompatible wheels, e.g. 32 vs 64-bit wheels
            # coexist during Windows builds.
            #
            env_set('CIBW_BEFORE_TEST', f'python scripts/gh_release.py pip_install wheelhouse/PyMuPDFb')
        
            set_cibuild_test()
        
            env_set( 'PYMUPDF_SETUP_FLAVOUR', 'p', pass_=1)
        
        else:
            # Build and test wheels which contain everything.
            #
            set_cibuild_test()
            env_set( 'PYMUPDF_SETUP_FLAVOUR', 'pb', pass_=1)
    
        run( f'cibuildwheel{platform_arg}', env_extra=env_extra)
    
        run( 'ls -lt wheelhouse')


def build_pyodide_wheel( implementations, inputs_PYMUPDF_SETUP_MUPDF_BUILD):
    '''
    Build Pyodide wheel.

    This does not use cibuildwheel but instead runs `pyodide build` inside
    the PyMuPDF directory, which in turn runs setup.py in a Pyodide build
    environment.
    '''
    log(f'## Building Pyodide wheel.')

    # Our setup.py does not know anything about Pyodide; we set a few
    # required environmental variables here.
    #
    env_extra = dict()

    # Disable libcrypto because not available in Pyodide.
    env_extra['HAVE_LIBCRYPTO'] = 'no'

    # Set PYMUPDF_SETUP_MUPDF_BUILD.
    if inputs_PYMUPDF_SETUP_MUPDF_BUILD:
        env_extra['PYMUPDF_SETUP_MUPDF_BUILD'] = inputs_PYMUPDF_SETUP_MUPDF_BUILD

    # Tell MuPDF to build for Pyodide.
    env_extra['OS'] = 'pyodide'

    env_extra['PYMUPDF_SETUP_IMPLEMENTATIONS'] = implementations
    
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
    
    command = pyodide_setup()
    command += ' && pyodide build --exports pyinit'
    run(command, env_extra=env_extra)
    
    # Copy wheel into `wheelhouse/` so it is picked up as a workflow
    # artifact.
    #
    run('ls -l dist/')
    run('mkdir -p wheelhouse && cp -p dist/* wheelhouse/')
    run('ls -l wheelhouse/')


def cpu_bits():
    return 32 if sys.maxsize == 2**31 - 1 else 64


# Name of venv used by `venv()`.
#
venv_name = f'venv-pymupdf-{platform.python_version()}-{cpu_bits()}'

def venv( command=None, packages=None, quick=False, system_site_packages=False):
    '''
    Runs remaining args, or the specified command if present, in a venv.
    
    command:
        Command as string or list of args. Should usually start with 'python'
        to run the venv's python.
    packages:
        List of packages (or comma-separated string) to install.
    quick:
        If true and venv directory already exists, we don't recreate venv or
        install Python packages in it.
    '''
    command2 = ''
    if platform.system() == 'OpenBSD':
        # libclang not available from pypi.org, but system py3-llvm package
        # works. `pip install` should be run with --no-build-isolation and
        # explicit `pip install swig setuptools psutil`.
        system_site_packages = True
        #ssp = ' --system-site-packages'
        log(f'OpenBSD: libclang not available from pypi.org.')
        log(f'OpenBSD: system package `py3-llvm` must be installed.')
        log(f'OpenBSD: creating venv with --system-site-packages.')
        log(f'OpenBSD: `pip install .../PyMuPDF` must be preceded by install of swig etc.')
    ssp = ' --system-site-packages' if system_site_packages else ''
    if quick and os.path.isdir(venv_name):
        log(f'{quick=}: Not creating venv because directory already exists: {venv_name}')
        command2 += 'true'
    else:
        quick = False
        command2 += f'{sys.executable} -m venv{ssp} {venv_name}'
    if platform.system() == 'Windows':
        command2 += f' && {venv_name}\\Scripts\\activate'
    else:
        command2 += f' && . {venv_name}/bin/activate'
    if quick:
        log(f'{quick=}: Not upgrading pip or installing packages.')
    else:
        command2 += ' && python -m pip install --upgrade pip'
        if packages:
            if isinstance(packages, str):
                packages = packages.split(',')
            command2 += ' && pip install ' + ' '.join(packages)
    command2 += ' &&'
    if isinstance( command, str):
        command2 += ' ' + command
    else:
        for arg in command:
            command2 += ' ' + shlex.quote(arg)
    
    run( command2)


def test( project, package, valgrind):
    
    run(f'pip install {test_packages}')
    if valgrind:
        log('Installing valgrind.')
        run(f'sudo apt update')
        run(f'sudo apt install valgrind')
        run(f'valgrind --version')
        
        log('Running PyMuPDF tests under valgrind.')
        # We ignore memory leaks.
        run(
                f'{sys.executable} {project}/tests/run_compound.py'
                    f' valgrind --suppressions={project}/valgrind.supp --error-exitcode=100 --errors-for-leak-kinds=none --fullpath-after='
                    f' pytest {project}/tests'
                    ,
                env_extra=dict(
                    PYTHONMALLOC='malloc',
                    PYMUPDF_RUNNING_ON_VALGRIND='1',
                    ),
                )
    else:
        run(f'{sys.executable} {project}/tests/run_compound.py pytest {project}/tests')
    

def pyodide_setup(clean=False):
    '''
    Returns a command that will set things up for a pyodide build.
    
    Args:
        clean:
            If true we create an entirely new environment. Otherwise
            we reuse any existing emsdk repository and venv.
    
    * Clone emsdk repository to `pipcl_emsdk` if not already present.
    * Create and activate a venv `pipcl_venv_pyodide` if not already present.
    * Install/upgrade package `pyodide-build`.
    * Run emsdk install scripts and enter emsdk environment.
    * Replace emsdk/upstream/bin/wasm-opt
      (https://github.com/pyodide/pyodide/issues/4048).
    
    Example usage in a build function:
    
        command = pipcl_wasm.pyodide_setup()
        command += ' && pyodide build --exports pyinit'
        subprocess.run(command, shell=1, check=1)
    '''
    command = 'true'
    
    # Clone emsdk.
    #
    dir_emsdk = 'emsdk'
    if clean and os.path.exists(dir_emsdk):
        shutil.rmtree( dir_emsdk, ignore_errors=1)
    if not os.path.exists(dir_emsdk):
        command += f' && echo "### cloning emsdk.git"'
        command += f' && git clone https://github.com/emscripten-core/emsdk.git {dir_emsdk}'
    
    # Create and enter Python venv.
    #
    venv_pyodide = 'venv_pyodide'
    if not os.path.exists( venv_pyodide):
        command += f' && echo "### creating venv {venv_pyodide}"'
        command += f' && {sys.executable} -m venv {venv_pyodide}'
    command += f' && . {venv_pyodide}/bin/activate'
    command += f' && echo "### running pip install ..."'
    command += f' && python -m pip install --upgrade pip wheel pyodide-build==0.23.4'
    
    # Run emsdk install scripts and enter emsdk environment.
    #
    command += f' && cd {dir_emsdk}'
    command += ' && PYODIDE_EMSCRIPTEN_VERSION=$(pyodide config get emscripten_version)'
    command += ' && echo "### running ./emsdk install"'
    command += ' && ./emsdk install ${PYODIDE_EMSCRIPTEN_VERSION}'
    command += ' && echo "### running ./emsdk activate"'
    command += ' && ./emsdk activate ${PYODIDE_EMSCRIPTEN_VERSION}'
    command += ' && echo "### running ./emsdk_env.sh"'
    command += ' && . ./emsdk_env.sh'   # Need leading `./` otherwise weird 'Not found' error.
    
    if 1:
        # Make our returned command replace emsdk/upstream/bin/wasm-opt
        # with a script that does nothing, otherwise the linker
        # command fails after it has created the output file. See:
        # https://github.com/pyodide/pyodide/issues/4048
        #
        
        def write( text, path):
            with open( path, 'w') as f:
                f.write( text)
            os.chmod( path, 0o755)
        
        # Create a script that our command runs, that overwrites
        # `emsdk/upstream/bin/wasm-opt`, hopefully in a way that is
        # idempotent.
        #
        # The script moves the original wasm-opt to wasm-opt-0.
        #
        write(
                textwrap.dedent('''
                    #! /usr/bin/env python3
                    import os
                    p = 'upstream/bin/wasm-opt'
                    p0 = 'upstream/bin/wasm-opt-0'
                    p1 = '../wasm-opt-1'
                    if os.path.exists( p0):
                        print(f'### {__file__}: {p0!r} already exists so not overwriting from {p!r}.')
                    else:
                        s = os.stat( p)
                        assert s.st_size > 15000000, f'File smaller ({s.st_size}) than expected: {p!r}'
                        print(f'### {__file__}: Moving {p!r} -> {p0!r}.')
                        os.rename( p, p0)
                    print(f'### {__file__}: Moving {p1!r} -> {p!r}.')
                    os.rename( p1, p)
                    '''
                    ).strip(),
                'wasm-opt-replace.py',
                )
        
        # Create a wasm-opt script that basically does nothing, except
        # defers to the original script when run with `--version`.
        #
        write(
                textwrap.dedent('''
                    #!/usr/bin/env python3
                    import os
                    import sys
                    import subprocess
                    if sys.argv[1:] == ['--version']:
                        root = os.path.dirname(__file__)
                        subprocess.run(f'{root}/wasm-opt-0 --version', shell=1, check=1)
                    else:
                        print(f'{__file__}: Doing nothing. {sys.argv=}')
                    '''
                    ).strip(),
                'wasm-opt-1',
                )
        command += ' && ../wasm-opt-replace.py'
    
    command += ' && cd ..'
    
    return command


if platform.system() == 'Windows':
    def relpath(path, start=None):
        try:
            return os.path.relpath(path, start)
        except ValueError:
            # os.path.relpath() fails if trying to change drives.
            return os.path.abspath(path)
else:
    def relpath(path, start=None):
        return os.path.relpath(path, start)


def log(text, caller=0):
    '''
    Writes `text` to stdout with prefix showing caller path relative to
    pymupdf_dir and fn name.
    '''
    frame_record = inspect.stack( context=0)[ caller+1]
    filename    = frame_record.filename
    line        = frame_record.lineno
    function    = frame_record.function
    prefix = f'{relpath(filename, pymupdf_dir)}:{function}(): '
    print(textwrap.indent(text, prefix))
    sys.stdout.flush()


def run(command, env_extra=None, check=1, timeout=None):
    '''
    Runs a command using subprocess.run().
    Args:
        command:
            The command to run.
        env_extra:
            None or dict containing extra environment variable settings to add
            to os.environ.
        check:
            Whether to raise exception if command fails.
        timeout:
            If not None, timeout in seconds; passed directory to
            subprocess.run(). Note that on MacOS subprocess.run() seems to
            leave processes running if timeout expires.
    '''
    env = None
    if env_extra:
        env = os.environ.copy()
        env.update(env_extra)
    log(f'Running: {command}')
    return subprocess.run(command, check=check, shell=1, env=env, timeout=timeout)


def platform_tag():
    bits = cpu_bits()
    if platform.system() == 'Windows':
        return 'win32' if bits==32 else 'win_amd64'
    elif platform.system() in ('Linux', 'Darwin'):
        assert bits == 64
        return platform.machine()
        #return 'x86_64'
    else:
        assert 0, f'Unrecognised: {platform.system()=}'


test_packages = 'pytest fontTools pymupdf-fonts flake8 pylint'
if platform.system() == 'Windows' and cpu_bits() == 32:
    # No pillow wheel available, and doesn't build easily.
    pass
else:
    test_packages += ' pillow'
if platform.system().startswith('MSYS_NT-'):
    # psutil not available on msys2.
    pass
else:
    test_packages += ' psutil'


if __name__ == '__main__':
    main()
