#! /usr/bin/env python3

'''
Runs a command using different implementations of PyMuPDF:

1.  Run with rebased implementation of PyMuPDF.

2.  As 1 but also set PYMUPDF_USE_EXTRA=0 to disable use of C++ optimisations.

Example usage:

    ./PyMuPDF/tests/run_compound.py python -m pytest -s PyMuPDF

Use `-i <implementations>` to select which implementations to use. In
`<implementations>`, `r` means rebased, `R` means rebased without
optimisations.

For example use the rebased and unoptimised rebased implementations with:

    ./PyMuPDF/tests/run_compound.py python -m pytest -s PyMuPDF
'''

import shlex
import os
import platform
import subprocess
import sys
import textwrap
import time


def log(text):
    print(textwrap.indent(text, 'PyMuPDF:tests/run_compound.py: '))
    sys.stdout.flush()


def log_star(text):
    log('#' * 40)
    log(text)
    log('#' * 40)


def main():

    implementations = 'rR'
    timeout = None
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '-i':
            i += 1
            implementations = sys.argv[i]
        elif arg == '-t':
            i += 1
            timeout = float(sys.argv[i])
        elif arg.startswith('-'):
            raise Exception(f'Unrecognised {arg=}.')
        else:
            break
        i += 1
    args = sys.argv[i:]
    
    e_rebased = None
    e_rebased_unoptimised = None
    
    endtime = None
    if timeout:
        endtime = time.time() + timeout
    
    # Check `implementations`.
    implementations_seen = set()
    for i in implementations:
        assert i not in implementations_seen, f'Duplicate implementation {i!r} in {implementations!r}.'
        if i == 'r':
            name = 'rebased'
        elif i == 'R':
            name = 'rebased (unoptimised)'
        else:
            assert 0, f'Unrecognised implementation {i!r} in {implementations!r}.'
        log(f'    {i!r}: will run with PyMuPDF {name}.')
        implementations_seen.add(i)
    
    for i in implementations:
        log(f'run_compound.py: {i=}')
        timeout = None
        if endtime:
            timeout = max(0, endtime - time.time())
        if i == 'r':
    
            # Run with default `pymupdf` (rebased).
            #
            log_star( f'Running using pymupdf (rebased): {shlex.join(args)}')
            e_rebased = subprocess.run( args, shell=0, check=0, timeout=timeout).returncode
    
        elif i == 'R':
    
            # Run with `pymupdf` (rebased) again, this time with PYMUPDF_USE_EXTRA=0.
            #
            env = os.environ.copy()
            env[ 'PYMUPDF_USE_EXTRA'] = '0'
            log_star(f'Running using pymupdf (rebased) with PYMUPDF_USE_EXTRA=0: {shlex.join(args)}')
            e_rebased_unoptimised = subprocess.run( args, shell=0, check=0, env=env, timeout=timeout).returncode
        
        else:
            raise Exception(f'Unrecognised implementation {i!r}.')
    
    if e_rebased is not None:
        log(f'{e_rebased=}')
    if e_rebased_unoptimised is not None:
        log(f'{e_rebased_unoptimised=}')
    
    if e_rebased or e_rebased_unoptimised:
       log('Test(s) failed.')
       return 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        # Terminate relatively quietly, failed commands will usually have
        # generated diagnostics.
        log(str(e))
        sys.exit(1)
