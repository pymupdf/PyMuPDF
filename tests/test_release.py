import pymupdf

import os
import re
import sys


g_root_abs = os.path.normpath(f'{__file__}/../../')

sys.path.insert(0, g_root_abs)
try:
    import pipcl
    import setup
finally:
    del sys.path[0]

g_root = pipcl.relpath(g_root_abs)


def _file_line(path, text, re_match, offset=+2):
    '''
    Returns <file>:<line> for location of regex match.
    
    path:
        filename.
    text:
        Contents of <filename>.
    re_match:
        A re.Match.
    offset:
        Added to line number of start of <re_match>. Default offset=2 is
        because callers usually grep for leading newline, and line numbers are
        generally 1-based.
    '''
    text_before = text[:re_match.start()]
    line = text_before.count('\n') + offset
    return f'{path}:{line}'


def test_release_versions():
    '''
    PyMuPDF and default MuPDF must have same major.minor version.
    '''
    version_p_tuple = [int(i) for i in setup.version_p.split('.')]
    version_mupdf_tuple = [int(i) for i in setup.version_mupdf.split('.')]
    assert version_p_tuple[:2] == version_mupdf_tuple[:2], \
            f'PyMuPDF and MuPDF major.minor versions do not match. {setup.version_p=} {setup.version_mupdf=}.'


def test_release_bug_template():
    '''
    Bug report template must list current PyMuPDF version.
    '''
    p = f'{g_root}/.github/ISSUE_TEMPLATE/bug_report.yml'
    expected = f'\n        - {setup.version_p}\n'
    with open(p) as f:
        text = f.read()
    assert expected in text, f'{p}:1: Failed to find line for {setup.version_p=}, {expected!r}.'


def test_release_changelog_version():
    '''
    In changes.txt, first item must match setup.version_p.
    '''
    p = f'{g_root}/changes.txt'
    with open(p) as f:
        text = f.read()
    m = re.search(f'\n[*][*]Changes in version ([0-9.]+)[*][*]\n', text)
    assert m, f'Cannot parse {p}.'
    assert m[1] == setup.version_p, \
            f'{_file_line(p, text, m)}: Cannot find {setup.version_p=} in first changelog item: {m[0].strip()!r}.'
    

def test_release_changelog_mupdf_version():
    '''
    In changes.txt, first mentioned of MuPDF must match setup.version_mupdf.
    '''
    p = f'{g_root}/changes.txt'
    with open(p) as f:
        text = f.read()
    m = re.search(f'\n[*] Use MuPDF-([0-9.]+)[.]\n', text)
    assert m, f'Cannot parse {p}.'
    assert m[1] == setup.version_mupdf, \
            f'{_file_line(p, text, m)}: First mentioned MuPDF version does not match {setup.version_mupdf=}: {m[0].strip()!r}.'
