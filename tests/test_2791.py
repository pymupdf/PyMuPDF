import pymupdf

import gc
import os
import platform
import sys


def merge_pdf(content: bytes, coverpage: bytes):
   with pymupdf.Document(stream=coverpage, filetype='pdf') as coverpage_pdf:
        with pymupdf.Document(stream=content, filetype='pdf') as content_pdf:
            coverpage_pdf.insert_pdf(content_pdf)
            doc = coverpage_pdf.write()
            return doc

def test_2791():
    '''
    Check for memory leaks.
    '''
    if os.environ.get('PYMUPDF_RUNNING_ON_VALGRIND') == '1':
        print(f'test_2791(): not running because PYMUPDF_RUNNING_ON_VALGRIND=1.')
        return
    if platform.system().startswith('MSYS_NT-'):
        print(f'test_2791(): not running on msys2 - psutil not available.')
        return
    #stat_type = 'tracemalloc'
    stat_type = 'psutil'
    if stat_type == 'tracemalloc':
        import tracemalloc
        tracemalloc.start(10)
        def get_stat():
            current, peak = tracemalloc.get_traced_memory()
            return current
    elif stat_type == 'psutil':
        # We use RSS, as used by mprof.
        import psutil
        process = psutil.Process()
        def get_stat():
            return process.memory_info().rss
    else:
        def get_stat():
            return 0
    n = 1000
    stats = [1] * n
    for i in range(n):
        root = os.path.abspath(f'{__file__}/../../tests/resources')  
        with open(f'{root}/test_2791_content.pdf', 'rb') as content_pdf:
            with open(f'{root}/test_2791_coverpage.pdf', 'rb') as coverpage_pdf:
                content = content_pdf.read()
                coverpage = coverpage_pdf.read()
                merge_pdf(content, coverpage)
                sys.stdout.flush()
        
        gc.collect()
        stats[i] = get_stat()

    print(f'Memory usage {stat_type=}.')
    for i, stat in enumerate(stats):
        sys.stdout.write(f' {stat}')
        #print(f'    {i}: {stat}')
    sys.stdout.write('\n')
    first = stats[2]
    last = stats[-1]
    ratio = last / first
    print(f'{first=} {last=} {ratio=}')

    if platform.system() != 'Linux':
        # Values from psutil indicate larger memory leaks on non-Linux. Don't
        # yet know whether this is because rss is measured differently or a
        # genuine leak is being exposed.
        print(f'test_2791(): not asserting ratio because not running on Linux.')
    elif not hasattr(pymupdf, 'mupdf'):
        # Classic implementation has unfixed leaks.
        print(f'test_2791(): not asserting ratio because using classic implementation.')
    elif [int(x) for x in platform.python_version_tuple()[:2]] < [3, 11]:
        print(f'test_2791(): not asserting ratio because python version less than 3.11: {platform.python_version()=}.')
    elif stat_type == 'tracemalloc':
        # With tracemalloc Before fix to src/extra.i's calls to
        # PyObject_CallMethodObjArgs, ratio was 4.26; after it was 1.40.
        assert ratio > 1 and ratio < 1.6
    elif stat_type == 'psutil':
        # Prior to fix, ratio was 1.043. After the fix, improved to 1.005, but
        # varies and sometimes as high as 1.010.
        # 2024-06-03: have seen 0.99919 on musl linux, and sebras reports .025.
        assert ratio >= 0.990 and ratio < 1.027, f'{ratio=}'
    else:
        pass
