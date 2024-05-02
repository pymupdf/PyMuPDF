import pymupdf

import os
import subprocess
import sys


def test_flake8():
    '''
    Check rebased Python code with flake8.
    '''
    if not hasattr(pymupdf, 'mupdf'):
        print(f'Not running flake8 with classic implementation.')
        return
    ignores = (
            'E123', # closing bracket does not match indentation of opening bracket's line
            'E124', # closing bracket does not match visual indentation
            'E126', # continuation line over-indented for hanging indent
            'E127', # continuation line over-indented for visual indent
            'E128', # continuation line under-indented for visual indent
            'E131', # continuation line unaligned for hanging indent
            'E201', # whitespace after '('
            'E203', # whitespace before ':'
            'E221', # E221 multiple spaces before operator
            'E225', # missing whitespace around operator
            'E226', # missing whitespace around arithmetic operator
            'E231', # missing whitespace after ','
            'E241', # multiple spaces after ':'
            'E251', # unexpected spaces around keyword / parameter equals
            'E252', # missing whitespace around parameter equals
            'E261', # at least two spaces before inline comment
            'E265', # block comment should start with '# '
            'E271', # multiple spaces after keyword
            'E272', # multiple spaces before keyword
            'E302', # expected 2 blank lines, found 1
            'E305', # expected 2 blank lines after class or function definition, found 1
            'E306', # expected 1 blank line before a nested definition, found 0
            'E402', # module level import not at top of file
            'E501', # line too long (80 > 79 characters)
            'E701', # multiple statements on one line (colon)
            'E741', # ambiguous variable name 'l'
            'F541', # f-string is missing placeholders
            'W293', # blank line contains whitespace
            'W503', # line break before binary operator
            'W504', # line break after binary operator
            'E731', # do not assign a lambda expression, use a def
            )
    ignores = ','.join(ignores)
    root = os.path.abspath(f'{__file__}/../..')
    def run(command):
        print(f'test_flake8(): Running: {command}')
        subprocess.run(command, shell=1, check=1)
    run(f'flake8 --ignore={ignores} --statistics {root}/src/__init__.py {root}/src/utils.py {root}/src/table.py')
    print(f'test_flake8(): flake8 succeeded.')
