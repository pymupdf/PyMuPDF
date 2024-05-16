import pymupdf
import os
import re
import subprocess
import sys
import textwrap

def test_pylint():
    
    if not hasattr(pymupdf, 'mupdf'):
        print(f'test_pylint(): Not running with classic implementation.')
        return
    
    ignores = ''
    
    ignores += textwrap.dedent(
            '''
            C0103: Constant name "g_exceptions_verbose" doesn't conform to UPPER_CASE naming style (invalid-name)
            C0115: Missing class docstring (missing-class-docstring)
            C0116: Missing function or method docstring (missing-function-docstring)
            C0301: Line too long (142/100) (line-too-long)
            C0302: Too many lines in module (23586/1000) (too-many-lines)
            C0303: Trailing whitespace (trailing-whitespace)
            C0325: Unnecessary parens after 'not' keyword (superfluous-parens)
            C0415: Import outside toplevel (traceback) (import-outside-toplevel)
            R0902: Too many instance attributes (9/7) (too-many-instance-attributes)
            R0903: Too few public methods (1/2) (too-few-public-methods)
            R0911: Too many return statements (9/6) (too-many-return-statements)
            R0913: Too many arguments (6/5) (too-many-arguments)
            R1705: Unnecessary "elif" after "return", remove the leading "el" from "elif" (no-else-return)
            R1720: Unnecessary "elif" after "raise", remove the leading "el" from "elif" (no-else-raise)
            R1724: Unnecessary "elif" after "continue", remove the leading "el" from "elif" (no-else-continue)
            R1735: Consider using '{}' instead of a call to 'dict'. (use-dict-literal)
            W0511: Fixme: we don't support JM_MEMORY=1. (fixme)
            W0622: Redefining built-in 'FileNotFoundError' (redefined-builtin)
            W0622: Redefining built-in 'open' (redefined-builtin)
            W1309: Using an f-string that does not have any interpolated variables (f-string-without-interpolation)
            R1734: Consider using [] instead of list() (use-list-literal)
            '''
            )
    
    # Items that we might want to fix.
    ignores += textwrap.dedent(
            '''
            C0114: Missing module docstring (missing-module-docstring)
            C0117: Consider changing "not rotate % 90 == 0" to "rotate % 90 != 0" (unnecessary-negation)
            C0123: Use isinstance() rather than type() for a typecheck. (unidiomatic-typecheck)
            C0200: Consider using enumerate instead of iterating with range and len (consider-using-enumerate)
            C0201: Consider iterating the dictionary directly instead of calling .keys() (consider-iterating-dictionary)
            C0209: Formatting a regular string which could be an f-string (consider-using-f-string)
            C0305: Trailing newlines (trailing-newlines)
            C0321: More than one statement on a single line (multiple-statements)
            C1802: Do not use `len(SEQUENCE)` without comparison to determine if a sequence is empty (use-implicit-booleaness-not-len)
            C1803: "select == []" can be simplified to "not select", if it is strictly a sequence, as an empty list is falsey (use-implicit-booleaness-not-comparison)
            R0912: Too many branches (18/12) (too-many-branches)
            R0914: Too many local variables (20/15) (too-many-locals)
            R0915: Too many statements (58/50) (too-many-statements)
            R1702: Too many nested blocks (7/5) (too-many-nested-blocks)
            R1703: The if statement can be replaced with 'var = bool(test)' (simplifiable-if-statement)
            R1710: Either all return statements in a function should return an expression, or none of them should. (inconsistent-return-statements)
            R1714: Consider merging these comparisons with 'in' by using 'width not in (1, 0)'. Use a set instead if elements are hashable. (consider-using-in)
            R1716: Simplify chained comparison between the operands (chained-comparison)
            R1717: Consider using a dictionary comprehension (consider-using-dict-comprehension)
            R1718: Consider using a set comprehension (consider-using-set-comprehension)
            R1719: The if expression can be replaced with 'bool(test)' (simplifiable-if-expression)
            R1721: Unnecessary use of a comprehension, use list(roman_num(num)) instead. (unnecessary-comprehension)
            R1728: Consider using a generator instead 'max(len(k) for k in item.keys())' (consider-using-generator)
            R1728: Consider using a generator instead 'max(len(r.cells) for r in self.rows)' (consider-using-generator)
            R1730: Consider using 'rowheight = min(rowheight, height)' instead of unnecessary if block (consider-using-min-builtin)
            R1731: Consider using 'right = max(right, x1)' instead of unnecessary if block (consider-using-max-builtin)
            W0105: String statement has no effect (pointless-string-statement)
            W0107: Unnecessary pass statement (unnecessary-pass)
            W0212: Access to a protected member _graft_id of a client class (protected-access)
            W0602: Using global for 'CHARS' but no assignment is done (global-variable-not-assigned)
            W0602: Using global for 'EDGES' but no assignment is done (global-variable-not-assigned)
            W0603: Using the global statement (global-statement)
            W0612: Unused variable 'keyvals' (unused-variable)
            W0613: Unused argument 'kwargs' (unused-argument)
            W0621: Redefining name 'show' from outer scope (line 159) (redefined-outer-name)
            W0640: Cell variable o defined in loop (cell-var-from-loop)
            W0718: Catching too general exception Exception (broad-exception-caught)
            W0719: Raising too general exception: Exception (broad-exception-raised)
            C3001: Lambda expression assigned to a variable. Define a function using the "def" keyword instead. (unnecessary-lambda-assignment)
            R0801: Similar lines in 2 files
            '''
            )
    ignores_list = list()
    for line in ignores.split('\n'):
        if not line or line.startswith('#'):
            continue
        m = re.match('^(.....): ', line)
        assert m, f'Failed to parse {line=}'
        ignores_list.append(m.group(1))
    ignores = ','.join(ignores_list)
    
    root = os.path.abspath(f'{__file__}/../..')
    
    sys.path.insert(0, root)
    import pipcl
    del sys.path[0]
    
    # We want to run pylist on all of our src/*.py files so we find them with
    # `pipcl.git_items()`. However this seems to fail on github windows with
    # `fatal: not a git repository (or any of the parent directories): .git` so
    # we also hard-code the list and verify it matches `git ls-files` on other
    # platforms. This ensures that we will always pick up new .py files in the
    # future.
    #
    command = f'pylint -d {ignores}'
    directory = f'{root}/src'
    directory = directory.replace('/', os.sep)
    leafs = [
            '__init__.py',
            '__main__.py',
            '_apply_pages.py',
            'fitz___init__.py',
            'fitz_table.py',
            'fitz_utils.py',
            'pymupdf.py',
            'table.py',
            'utils.py',
            ]
    leafs.sort()
    try:
        leafs_git = pipcl.git_items(directory)
    except Exception as e:
        import platform
        assert platform.system() == 'Windows'
    else:
        leafs_git = [i for i in leafs_git if i.endswith('.py')]
        leafs_git.sort()
        assert  leafs_git == leafs, f'leafs:\n    {leafs!r}\nleafs_git:\n    {leafs_git!r}'
    for leaf in leafs:
        command += f' {directory}/{leaf}'
    print(f'Running: {command}')
    subprocess.run(command, shell=1, check=1)
    
