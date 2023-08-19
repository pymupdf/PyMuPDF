#! /usr/bin/env python3

'''
Build+test script for PyMuPDF, mostly for use with github builds.

We run cibuild manually, in order to build and test the two wheel
flavours that make up PyMuPDF:

    PyMuPDFb
        Not specific to particular versions of Python. Contains shared
        libraries for the MuPDF C and C++ bindings.
    PyMuPDF
        Specific to particular versions of Python. Contains the rest of
        the(classic and rebased) PyMuPDF implementation.

Args:
    build
        Build using cibuild.
    build-devel
        Build using cibuild with `--platform` set.
    pip_install <prefix>
        Run `pip install <prefix>-*<platform_tag>.whl`,
        where `platform_tag` will be things like 'win32', 'win_amd64',
        'x86_64`, depending on the python we are running on.
    venv
        Run remaining args inside venv.
    test
        Internal.

We look at these items in the environment, should be unset (treated as '0'),
'0' or '1'.

    inputs_flavours
        If unset or '1', build separate PyMuPDF and PyMuPDFb wheels.
        If '0', build complete PyMuPDF wheels.
    inputs_skeleton
        Build minimal wheel; for testing only.
    inputs_sdist
    inputs_wheels
    inputs_wheels_linux_aarch64
    inputs_wheels_linux_auto
    inputs_wheels_macos_arm64
    inputs_wheels_macos_auto
    inputs_wheels_windows_auto

Example usage:

     PYMUPDF_SETUP_MUPDF_BUILD=../mupdf-master py -3.9-32 PyMuPDF/scripts/gh_release.py venv build-devel
   
'''


import glob
import os
import platform
import shlex
import sys
import subprocess


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
            build()
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
            test( project, package)
        else:
            assert 0, f'Unrecognised {arg=}'


def build( platform_=None): 
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
    inputs_wheels = get_bool('inputs_wheels')
    inputs_wheels_linux_aarch64 = get_bool('inputs_wheels_linux_aarch64')
    inputs_wheels_linux_auto = get_bool('inputs_wheels_linux_auto', 1)
    inputs_wheels_macos_arm64 = get_bool('inputs_wheels_macos_arm64')
    inputs_wheels_macos_auto = get_bool('inputs_wheels_macos_auto', 1)
    inputs_wheels_windows_auto = get_bool('inputs_wheels_windows_auto', 1)
    inputs_wheels_cps = os.environ.get('inputs_wheels_cps')
    
    #inputs_wheels_cp38 = get_bool('inputs_wheels_cp38', 1)
    #inputs_wheels_cp39 = get_bool('inputs_wheels_cp39', 1)
    #inputs_wheels_cp310 = get_bool('inputs_wheels_cp310', 1)
    #inputs_wheels_cp311 = get_bool('inputs_wheels_cp311', 1)
    
    log( f'{inputs_flavours=}')
    log( f'{inputs_sdist=}')
    log( f'{inputs_skeleton=}')
    log( f'{inputs_wheels=}')
    log( f'{inputs_wheels_linux_aarch64=}')
    log( f'{inputs_wheels_linux_auto=}')
    log( f'{inputs_wheels_macos_arm64=}')
    log( f'{inputs_wheels_macos_auto=}')
    log( f'{inputs_wheels_windows_auto=}')
    log( f'{inputs_wheels_cps=}')
    
    #log( f'{inputs_wheels_cp38=}')
    #log( f'{inputs_wheels_cp39=}')
    #log( f'{inputs_wheels_cp310=}')
    #log( f'{inputs_wheels_cp311=}')

    # Build 
    
    env_extra = dict()
    
    def set_if_unset(name, value):
        v = os.environ.get(name)
        if v is None:
            log( f'Setting environment {name=} to {value=}')
            env_extra[ name] = value
        else:
            log( f'Not changing {name}={v!r} to {value!r}')
    set_if_unset( 'CIBW_BUILD_VERBOSITY', '3')
    set_if_unset( 'CIBW_SKIP', '"pp* *i686 *-musllinux_* cp36* cp37*"')
    
    def make_string(*items):
        ret = list()
        for item in items:
            if item:
                ret.append(item)
        return ' '.join(ret)
    
    cps = inputs_wheels_cps if inputs_wheels_cps else 'cp38* cp39* cp310* cp311*'
    set_if_unset( 'CIBW_BUILD', cps)
    
    if 0:
        cps = ([]
                + inputs_wheels_cp38 * ['cp38*']
                + inputs_wheels_cp39 * ['cp39*']
                + inputs_wheels_cp310 * ['cp310*']
                + inputs_wheels_cp311 * ['cp311*']
                )
        cps = ' '.join(cps)
        log(f'{cps=}')
        set_if_unset( 'CIBW_BUILD', cps)
    
    if platform.system() == 'Linux':
        set_if_unset(
                'CIBW_ARCHS_LINUX',
                make_string(
                    'auto' * inputs_wheels_linux_auto,
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
    
    def env_set(name, value, pass_=False):
        assert isinstance( value, str)
        if not name.startswith('CIBW'):
            assert pass_, f'{name=} {value=}'
        env_extra[ name] = value
        if pass_ and platform.system() == 'Linux':
            v = env_extra.get('CIBW_ENVIRONMENT_PASS_LINUX', '')
            if v:
                v += ' '
            v += name
            env_extra['CIBW_ENVIRONMENT_PASS_LINUX'] = v

    env_set('PYMUPDF_SETUP_IMPLEMENTATIONS', 'ab', pass_=1)
    if inputs_skeleton:
        env_set('PYMUPDF_SETUP_SKELETON', inputs_skeleton, pass_=1)
    
    def set_cibuild_test():
        log( f'set_cibuild_test(): {inputs_skeleton=}')
        if inputs_skeleton:
            env_set('CIBW_TEST_COMMAND', 'python {project}/scripts/gh_release.py test {project} {package}')
        else:
            env_set('CIBW_TEST_REQUIRES', 'fontTools pytest')
            env_set('CIBW_TEST_COMMAND', 'python {project}/tests/run_compound.py pytest -s {project}/tests')
        
        # Don't attempt to run tests on cross-built ARM wheels.
        #
        # https://cibuildwheel.readthedocs.io/en/stable/options/#test-skip
        #
        #env_set('CIBW_TEST_SKIP', 'manylinux*_aarch64 macos*_arm64')
    
    pymupdf_dir = os.path.abspath( f'{__file__}/../..')
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

        # Now build PyMuPDF wheels. cibuildwheel will build one for each
        # Python version.
        #
        
        # Tell cibuildwheel not to use `auditwheel`, because it cannot cope
        # with us deliberately putting required libraries into a different
        # wheel.
        #
        # Also, `auditwheel addtag` says `No tags to be added` and terminates
        # with non-zero.
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


def venv( command=None, packages=None):
    '''
    Runs remaining args, or the specified command if present, in a venv.
    
    command:
        Command as string or list of args. Should usually start with 'python'
        to run the venv's python.
    packages:
        List of packages (or comma-separated string) to install.
    '''
    venv_name = f'venv-pymupdf-{platform.python_version()}'
    command2 = ''
    command2 += f'{sys.executable} -m venv {venv_name}'
    if platform.system() == 'Windows':
        command2 += f' && {venv_name}\\Scripts\\activate'
    else:
        command2 += f' && . {venv_name}/bin/activate'
    if packages:
        command2 += ' && python -m pip install --upgrade pip'
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


def test( project, package):

    
    log('### test():')
    log(f'### test(): {sys.executable=}')
    log(f'### test(): {project=}')
    log(f'### test(): {package=}')
    
    import fitz
    import fitz_new
    print(f'{fitz.bar(3)=}')
    print(f'{fitz_new.bar(3)=}')
    
    return
    
    run('ls -l')
    run( f'ls -l {project}')
    run( f'ls -l {package}')
    run( f'ls -l {project}/wheelhouse', check=0)
    run( f'ls -l {package}/wheelhouse', check=0)
    
    wheel_b = glob.glob( f'{project}/wheelhouse/PyMuPDFb-*{platform_tag()}.whl')
    assert len(wheel_b) == 1, f'{wheel_b=}'
    wheel_b = wheel_b[0]

    py_version = platform.python_version_tuple()
    py_version = py_version[:2]
    py_version = ''.join( py_version)
    log( '### test(): {py_version=}')
    wheel_p = glob.glob( f'wheelhouse/PyMuPDF-*-cp{py_version}-*.whl')
    print(f'{wheel_p=}')
    #assert len(wheel_p) == 1, f'{wheel_p=}'
    
    #run( f'pip install {wheel_b}')
    #run( f'pip install {wheel_p}')
    


def log(text):
    print(f'{__file__}: {text}')
    sys.stdout.flush()


def run(command, env_extra=None, env=None, check=1):
    if env is None:
        env = add_env(env_extra)
    else:
        assert env_extra is None
    log(f'Running: {command}')
    sys.stdout.flush()
    subprocess.run(command, check=check, shell=1, env=env)


def add_env(env_extra):
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
        log(f'Adding environment:')
        for n, v in env_extra.items():
            log(f'    {n}: {v!r}')
    return env


def platform_tag():
    bits = 32 if sys.maxsize == 2**31 - 1 else 64
    if platform.system() == 'Windows':
        return 'win32' if bits==32 else 'win_amd64'
    elif platform.system() in ('Linux', 'Darwin'):
        assert bits == 64
        return platform.machine()
        #return 'x86_64'
    else:
        assert 0, f'Unrecognised: {platform.system()=}'


if __name__ == '__main__':
    main()
