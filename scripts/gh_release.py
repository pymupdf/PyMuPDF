#! /usr/bin/env python3

'''
Build+test script for PyMuPDF, mostly for use with github builds.

We run cibuild manually, in order to build and test the two wheel flavours that
make up PyMuPDF:

    PyMuPDFrb
        Not specific to particular versions of Python. Contains shared
        libraries for the MuPDF C and C++ bindings.
    PyMuPDFrp
        Specific to particular versions of Python. Contains the rest of
        the(classic and rebased) PyMuPDF implementation.

Args:
    build
        Build using cibuild.
    build-devel
        Build using cibuild with `--platform` set.
    windows_pip_install <prefix>
        Windows only: run `pip install <prefix>-*-<platform_tag>.whl`,
        where `platform_tag` will be 'win32' or 'win_amd64' depending on
        the python we are running on.
    venv
        Run remaining args inside venv.
    test
        Internal.

We look at these items in the environment, should be unset (treated as '0'),
'0' or '1'.

    inputs_flavours
        If '1' Build separate PyMuPDFrb and PyMuPDFrp wheels. Usually
        this should be set to '1'.
    inputs_skeleton
        Build minimal wheel; for testing only.
    inputs_sdist
    inputs_wheels
    inputs_wheels_linux_aarch64
    inputs_wheels_macos_arm64

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
        elif arg == 'windows_pip_install':
            assert platform.system() == 'Windows'
            prefix = next(args)
            pattern = f'{prefix}-*-{windows_platform_tag()}.whl'
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
    log(f'### sys.argv ({len(sys.argv)}):')
    for i, arg in enumerate(sys.argv):
        log(f'###     {i}: {arg!r}')
    log(f'### os.environ ({len(os.environ)}):')
    for k in sorted( os.environ.keys()):
        v = os.environ[ k]
        log( f'###     {k}: {v!r}')
    
    platform_arg = f' --platform {platform_}' if platform_ else ''
    
    # Parameters are in os.environ, as that seems to be the only way that
    # Github workflow .yml files can encode them.
    #
    def get_bool(name):
        v = os.environ.get(name)
        if v in ('1', 'true'):
            return 1
        elif v in ('0', 'false', None):
            return 0
        else:
            assert 0, f'Bad environ {name=} {v=}'
    inputs_flavours = get_bool('inputs_flavours')
    inputs_skeleton = get_bool('inputs_skeleton')
    inputs_sdist = get_bool('inputs_sdist')
    inputs_wheels = get_bool('inputs_wheels')
    inputs_wheels_linux_aarch64 = get_bool('inputs_wheels_linux_aarch64')
    inputs_wheels_macos_arm64 = get_bool('inputs_wheels_macos_arm64')
    
    log( f'{inputs_flavours=}')
    log( f'{inputs_skeleton=}')
    log( f'{inputs_sdist=}')
    log( f'{inputs_wheels=}')
    log( f'{inputs_wheels_linux_aarch64=}')
    log( f'{inputs_wheels_macos_arm64=}')

    run('pip install cibuildwheel')
    
    # Build 
    
    env_extra = dict()
    
    def set_if_unset(name, value):
        v = os.environ.get(name)
        if v is None:
            env_extra[ name] = value
        else:
            log( f'Not changing {name}={v!r} to {value!r}')
    set_if_unset( 'CIBW_BUILD_VERBOSITY', '3')
    set_if_unset( 'CIBW_SKIP', '"pp* *i686 *-musllinux_* cp36* cp37*"')
    set_if_unset( 'CIBW_ARCHS_LINUX', 'auto')
    
    # Don't build Windows x86, because MuPDF's workaround for win32 libclang
    # (where it runs `-b 0` in a separate venv with 64-bit Python) does not
    # work when run via cibuildwheel - in the 64-bit venv, clang module cannot
    # find libclang.
    #
    #set_if_unset( 'CIBW_ARCHS_WINDOWS', 'AMD64')
    
    # On Windows:
    #   cp310 gets dll load error at runtime.
    #   cp38 cp39 311 ok.
    #
    set_if_unset( 'CIBW_BUILD', 'cp38* cp39* cp310* cp311*')
    
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
    env_set('PYMUPDF_SETUP_SKELETON', str(inputs_skeleton), pass_=1)
    
    def set_cibuild_test():
        log( f'set_cibuild_test(): {inputs_skeleton=}')
        if inputs_skeleton:
            env_set('CIBW_TEST_COMMAND', 'python {project}/scripts/gh_release.py test {project} {package}')
        else:
            env_set('CIBW_TEST_REQUIRES', 'fontTools pytest')
            env_set('CIBW_TEST_COMMAND', 'python {project}/tests/run_compound.py pytest -s {project}/tests')
    
    pymupdf_dir = os.path.abspath( f'{__file__}/../..')
    if pymupdf_dir != os.path.abspath( os.getcwd()):
        log( f'Changing dir to {pymupdf_dir=}')
        os.chdir( pymupdf_dir)
    
    if inputs_flavours:
        # Build and test PyMuPDFrb and PyMuPDFrp wheels.
        #
        
        # First build PyMuPDFrb wheel. cibuildwheel will build a single wheel
        # here, which will work with any python version.
        #
        env_set( 'PYMUPDF_SETUP_FLAVOUR', 'rb', pass_=1)
        run( f'cibuildwheel{platform_arg}', env_extra)
        run( 'echo after flavour=rb')
        run( 'ls -l wheelhouse')

        # Now build PyMuPDFrp wheels. cibuildwheel will build one for each
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
        
        # We tell cibuildwheel to test these wheels, but also tell it to
        # install the PyMuPDFrb wheel first - otherwise installation of
        # PyMuPDFrp would fail because it lists the PyMuPDFrb wheel as a
        # prerequisite.
        #
        if platform.system() == 'Windows':
            # We need to make cibuild use our special
            # `windows_pip_install` arg, which selects an appropriate
            # platform tag so we cope with 32 and 64-bit wheels being
            # available.
            #
            env_set('CIBW_BEFORE_TEST', f'python scripts/gh_release.py windows_pip_install wheelhouse/PyMuPDFrb')
        else:
            env_set('CIBW_BEFORE_TEST', 'pip install wheelhouse/PyMuPDFrb-*.whl')
        set_cibuild_test()
        
        env_set( 'PYMUPDF_SETUP_FLAVOUR', 'rp', pass_=1)
        run( f'cibuildwheel{platform_arg}', env_extra)
        run( 'echo after flavour=rp')
        run( 'ls -l wheelhouse')

        wheel_b = glob.glob( 'wheelhouse/PyMuPDFrb-*.whl')
        assert len(wheel_b) == 1
        wheel_b = wheel_b[0]

        wheel_p = glob.glob( 'wheelhouse/PyMuPDFrp-*.whl')
    
    else:
        # Build and test wheels which contain everything.
        #
        set_cibuild_test()
        run( f'cibuildwheel{platform_arg}', env_extra)


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
    
    import bar
    log( f'{bar.bar(23)=}')
    return
    
    run('ls -l')
    run( f'ls -l {project}')
    run( f'ls -l {package}')
    run( f'ls -l {project}/wheelhouse', check=0)
    run( f'ls -l {package}/wheelhouse', check=0)
    
    platform_tag = ''
    if platform.system() == 'Windows':
        platform_tag = windows_platform_tag()
    wheel_b = glob.glob( f'{project}/wheelhouse/PyMuPDFrb-*{platform_tag}.whl')
    assert len(wheel_b) == 1, f'{wheel_b=}'
    wheel_b = wheel_b[0]

    py_version = platform.python_version_tuple()
    py_version = py_version[:2]
    py_version = ''.join( py_version)
    log( '### test(): {py_version=}')
    wheel_p = glob.glob( f'wheelhouse/PyMuPDFrp-*-cp{py_version}-*.whl')
    assert len(wheel_p) == 1, f'{wheel_p=}'
    
    run( f'pip install {wheel_b}')
    run( f'pip install {wheel_p}')
        
    


def log(text):
    print(f'{__file__}: {text}')
    sys.stdout.flush()


def run(command, env_extra=None, check=1):
    env = None
    if env_extra:
        env = os.environ.copy()
        env.update(env_extra)
        log(f'Adding environment:')
        for n, v in env_extra.items():
            log(f'    {n}: {v!r}')
    log(f'Running: {command}')
    sys.stdout.flush()
    subprocess.run(command, check=check, shell=1, env=env)


def windows_platform_tag():
    assert platform.system() == 'Windows'
    if sys.maxsize == 2**31 - 1:
        return 'win32'
    else:
        return 'win_amd64'


if __name__ == '__main__':
    main()
