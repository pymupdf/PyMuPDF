import glob
import os
import sys
import tempfile
import textwrap

import pipcl

import util

import pymupdf


def test_upgrade():
    print()
    if not util._use_layout():
        print('test_upgrade(): doing nothing because pymupdf-lite.')
        return
    print(f'{pymupdf.pymupdf_version=}')
    APTEST_WHEELHOUSE = os.environ.get('APTEST_WHEELHOUSE')
    print(f'test_upgrade(): {APTEST_WHEELHOUSE=}')
    if not APTEST_WHEELHOUSE:
        print(f'test_upgrade(): doing nothing because APTEST_WHEELHOUSE unset.')
        return
    for dirpath, dirnames, filenames in os.walk(APTEST_WHEELHOUSE):
        for filename in filenames:
            print(f'    {os.path.join(dirpath, filename)}')
    PIP_EXTRA_INDEX_URL = f'file://{os.path.abspath(APTEST_WHEELHOUSE)}/simple'
    PIP_EXTRA_INDEX_URL = PIP_EXTRA_INDEX_URL.replace(os.sep, '/')
    print(f'test_upgrade(): {PIP_EXTRA_INDEX_URL=}')
    
    if pipcl.windows() and os.environ.get('GITHUB_ACTIONS') == 'true':
        # With tempfile.TemporaryDirectory, we get problems on Github windows:
        #
        #   test_upgrade(): Running: C:\Users\runneradmin\AppData\Local\Temp\cibw-run-miuhhhuw\cp311-win_amd64\venv-test\Scripts\python.exe -m venv C:\Users\RUNNER~1\AppData\Local\Temp\pymupdf-test-venvhxp3ac5q
        #   test_upgrade(): Actual environment location may have moved due to redirects, links or junctions.
        #   test_upgrade():   Requested location: "C:\Users\RUNNER~1\AppData\Local\Temp\pymupdf-test-venvhxp3ac5q\Scripts\python.exe"
        #   test_upgrade():   Actual location:    "C:\Users\runneradmin\AppData\Local\Temp\pymupdf-test-venvhxp3ac5q\Scripts\python.exe"
        #   test_upgrade(): 
        #   do(): Running: C:\Users\RUNNER~1\AppData\Local\Temp\pymupdf-test-venvhxp3ac5q/Scripts/activate && pip install pymupdf==1.28.2 pymupdf-layout==1.28.2 pymupdf4llm==1.28.2
        #   do(): Looking in indexes: https://pypi.org/simple, file://D:/a/aptest/aptest/aptest-wheelhouse/simple
        #   do(): ERROR: Could not install packages due to an OSError: [Errno 13] Permission denied: 'D:\\a\\aptest\\aptest\\aptest-wheelhouse\\simple\\pymupdf'
        #   do(): Check the permissions.
        #
        # Using a fixed local directory instead of tempfile.TemporaryDirectory() still fails:
        #
        #   test_upgrade(): Running: C:\Users\runneradmin\AppData\Local\Temp\cibw-run-mhqx6qsw\cp311-win_amd64\venv-test\Scripts\python.exe -m venv pymupdf_test_upgrade_venv
        #   do(): Running: pymupdf_test_upgrade_venv\Scripts\activate && pip install pymupdf==1.28.2 pymupdf-layout==1.28.2 pymupdf4llm==1.28.2
        #   do(): Looking in indexes: https://pypi.org/simple, file://D:/a/aptest/aptest/aptest-wheelhouse/simple
        #   do(): ERROR: Could not install packages due to an OSError: [Errno 13] Permission denied: 'D:\\a\\aptest\\aptest\\aptest-wheelhouse\\simple\\pymupdf'
        #   do(): Check the permissions.
        #
        # So we give up here.
        print(f'Not running on Github windows because of permissions problems.')
        return

    venv_dir = 'pymupdf_test_upgrade_venv'
    pipcl.fs_remove(venv_dir)

    pipcl.run(f'{sys.executable} -m venv {venv_dir}')
    if pipcl.windows():
        venv_enter = f'{venv_dir}\\Scripts\\activate'
    else:
        venv_enter = f'. {venv_dir}/bin/activate'

    def get_module_tree(module):
        '''
        Returns dict mapping file path to file size within venv module
        directory.
        '''
        if pipcl.windows():
            sp = f'{venv_dir}/Lib/site-packages/'
        else:
            sp = glob.glob(f'{venv_dir}/lib/python*/site-packages/')
            assert len(sp) == 1
            sp = sp[0]
        ret = dict()
        for dirpath, dirnames, filenames in os.walk(f'{sp}/{module}'):
            for filename in filenames:
                path = f'{dirpath}/{filename}'
                st = os.stat(path)
                ret[path] = st.st_size
        return ret

    def do(command, use_wheelhouse):
        '''
        Runs command in venv and returns pymupdf.pymupdf_version.
        '''
        env_extra = dict(PIP_EXTRA_INDEX_URL=PIP_EXTRA_INDEX_URL) if use_wheelhouse else None
        pipcl.run(f'{venv_enter} && {command}', env_extra=env_extra)
        out = pipcl.run(
                f'{venv_enter} && python -c "import pymupdf; print(pymupdf.pymupdf_version); document=pymupdf.open()"',
                out='log',
                capture=1,
                )
        # Ignore output lines that contain onnxruntime diagnostics.
        lines = list()
        for line in out.split('\n'):
            if 'onnxruntime' not in line:
                lines.append(line)
        out2 = '\n'.join(lines)
        return out2.strip(), get_module_tree('pymupdf')

    def uninstall_all():
        pipcl.run(f'{venv_enter} && pip uninstall -y pymupdf pymupdf-layout pymupdf4llm')

    # Get tree from fresh installation.
    out, tree0 = do('pip install pymupdf', True)
    assert out == pymupdf.pymupdf_version

    errors = []
    def check_tree(tree, description, *, expect_error=False):
        '''
        Check <tree> is identical to <tree0>. We use util.diff_dicts() to show
        clear info about any differences.
        '''
        text = util.diff_dicts(tree0, tree)
        l = len(text.split('\n')) if text else 0
        print(f'{description} ({l}):')
        if text:
            print(textwrap.indent(text, '    '))
        if expect_error:
            if not text:
                errors.append(f'Did not get expected error for {description=}.')
        else:
            if text:
                errors.append(description)

    print('### Test upgrade of pymupdf')
    uninstall_all()
    out1, _ = do('pip install pymupdf==1.28.2 pymupdf-layout==1.28.2 pymupdf4llm==1.28.2', False)
    out2, tree = do('pip install --upgrade pymupdf', True)
    assert out1 == '1.28.2'
    assert out2 == pymupdf.pymupdf_version
    check_tree(tree, 'upgrade of pymupdf')

    print('### Test upgrade of pymupdf4llm')
    uninstall_all()
    out1, _ = do('pip install pymupdf==1.28.2 pymupdf-layout==1.28.2 pymupdf4llm==1.28.2', False)
    out2, tree = do('pip install --upgrade pymupdf4llm', True)
    assert out1 == '1.28.2'
    assert out2 == pymupdf.pymupdf_version
    check_tree(tree, 'upgrade of pymupdf4llm')

    print('### Test upgrade of pymupdf-layout')
    uninstall_all()
    out1, _ = do('pip install pymupdf==1.28.2 pymupdf-layout==1.28.2 pymupdf4llm==1.28.2', False)
    out2, tree = do('pip install --upgrade pymupdf-layout', True)
    assert out1 == '1.28.2'
    assert out2 == pymupdf.pymupdf_version
    check_tree(tree, 'upgrade of pymupdf-layout', expect_error=1)

    print(f'{errors=}')
    assert not errors
