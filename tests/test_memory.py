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
    if os.environ.get('PYODIDE_ROOT'):
        print('test_2791(): not running on Pyodide - No module named \'psutil\'.')
        return
        
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
    verbose = False
    if platform.python_implementation() == 'GraalVM':
        n = 10
        verbose = True
    stats = [1] * n
    for i in range(n):
        if verbose:
            print(f'{i+1}/{n}.', flush=1)
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


def test_4090():
    if os.environ.get('PYODIDE_ROOT'):
        print('test_4090(): not running on Pyodide - No module named \'psutil\'.')
        return
        
    print(f'test_4090(): {os.environ.get("PYTHONMALLOC")=}.')
    import psutil
    process = psutil.Process()
    rsss = list()
    def rss():
        ret = process.memory_info().rss
        rsss.append(ret)
        return ret
        
    path = os.path.normpath(f'{__file__}/../../tests/resources/test_4090.pdf')
    for i in range(100):
        d = dict()
        d[i] = dict()
        with pymupdf.open(path) as document:
            for j, page in enumerate(document):
                d[i][j] = page.get_text('rawdict')
        print(f'test_4090(): {i}: {rss()=}')
    print(f'test_4090(): {rss()=}')
    gc.collect()
    print(f'test_4090(): {rss()=}')
    r1 = rsss[2]
    r2 = rsss[-1]
    r = r2 / r1
    if platform.system() == 'Windows':
        assert 0.93 <= r < 1.05, f'{r1=} {r2=} {r=}.'
    else:
        assert 0.95 <= r < 1.05, f'{r1=} {r2=} {r=}.'


def show_tracemalloc_diff(snapshot1, snapshot2):
    top_stats = snapshot2.compare_to(snapshot1, 'lineno')
    n = 0
    mem = 0
    for i in top_stats:
        n += i.count
        mem += i.size
    print(f'{n=}')
    print(f'{mem=}')
    print("Top 10:")
    for stat in top_stats[:10]:
        print(f'    {stat}')
    snapshot_diff = snapshot2.compare_to(snapshot1, key_type='lineno')
    print(f'snapshot_diff:')
    count_diff = 0
    size_diff = 0
    for i, s in enumerate(snapshot_diff):
        print(f'    {i}: {s.count=} {s.count_diff=} {s.size=} {s.size_diff=} {s.traceback=}')
        count_diff += s.count_diff
        size_diff += s.size_diff
    print(f'{count_diff=} {size_diff=}')
    


def test_4125():
    if os.environ.get('PYODIDE_ROOT'):
        print('test_4125(): not running on Pyodide - No module named \'psutil\'.')
        return
        
    if os.environ.get('PYMUPDF_RUNNING_ON_VALGRIND') == '1':
        print(f'test_4125(): not running because PYMUPDF_RUNNING_ON_VALGRIND=1.')
        return
    if platform.system().startswith('MSYS_NT-'):
        print(f'test_4125(): not running on msys2 - psutil not available.')
        return
    
    print('')
    print(f'test_4125(): {platform.python_version()=}.')
    
    path = os.path.normpath(f'{__file__}/../../tests/resources/test_4125.pdf')
    import gc
    import psutil
    
    root = os.path.normpath(f'{__file__}/../..')
    sys.path.insert(0, root)
    try:
        import pipcl
    finally:
        del sys.path[0]
    
    process = psutil.Process()
    
    class State: pass
    state = State()
    state.rsss = list()
    state.prev = None
    
    def get_stat():
        rss = process.memory_info().rss
        if not state.rsss:
            state.prev = rss
        state.rsss.append(rss)
        drss = rss - state.prev
        state.prev = rss
        print(f'test_4125():'
                f' {rss=:,}'
                f' rss-rss0={rss-state.rsss[0]:,}'
                f' drss={drss:,}'
                f'.'
                )
    
    for i in range(10):
        with pymupdf.open(path) as document:
            for page in document:
                for image_info in page.get_images(full=True):
                    xref, smask, width, height, bpc, colorspace, alt_colorspace, name, filter_, referencer = image_info
                    pixmap = pymupdf.Pixmap(document, xref)
                    if pixmap.colorspace != pymupdf.csRGB:
                        pixmap2 = pymupdf.Pixmap(pymupdf.csRGB, pixmap)
                        del pixmap2
                    del pixmap
        pymupdf.TOOLS.store_shrink(100)
        pymupdf.TOOLS.glyph_cache_empty()
        gc.collect()
        get_stat()
    
    if platform.system() == 'Linux':
        rss_delta = state.rsss[-1] - state.rsss[3]
        print(f'{rss_delta=}')
        pv = platform.python_version_tuple()
        pv = (int(pv[0]), int(pv[1]))
        if pv < (3, 11):
            # Python < 3.11 has less reliable memory usage so we exclude.
            print(f'test_4125(): Not checking on {platform.python_version()=} because < 3.11.')
        else:
            # Before the fix, each iteration would leak 4.9MB.
            rss_delta_max = 100*1000 * (len(state.rsss) - 3)
            assert rss_delta < rss_delta_max
    else:
        # Unfortunately on non-Linux Github test machines the RSS values seem
        # to vary a lot, which causes spurious test failures. So for at least
        # we don't actually check.
        #
        print(f'Not checking results because non-Linux behaviour is too variable.')


def _test_4751():
    import gc
    import tracemalloc
    
    def analysis(stream_data, do_iter=True):
        pdf_info = pymupdf.Document(stream=stream_data, filetype='pdf')
        tmp_list = range(len(pdf_info))
        for page_num in tmp_list:
            page = pdf_info[page_num]
            raw_info = page.get_text('rawdict')['blocks']
            page_widgets_list = page.widgets() 
            if do_iter:
                for widget_info in page_widgets_list:
                    print(widget_info)
            del page_widgets_list
        pdf_info.close()
        pdf_info = None
        pymupdf.TOOLS.store_shrink(100)

    file_path = os.path.normpath(f'{__file__}/../../tests/resources/test_4751.pdf')
    
    def log(text):
        print(text, flush=1)

    # We filter out all allocations where leaf-most frame is in tracemalloc
    # itself, or in test_memory.py itself, because these are not relevant
    # to finding leaks in pymupdf.
    #
    tm_filters = [
            tracemalloc.Filter(inclusive=False, filename_pattern=tracemalloc.__file__, all_frames=True),
            tracemalloc.Filter(inclusive=False, filename_pattern=__file__),
            ]

    def get_snapshot():
        '''
        Wrapper for tracemalloc.take_snapshot() that filters out blocks with
        backtraces that we are not interested in.
        '''
        ret = tracemalloc.take_snapshot()
        ret2 = ret.filter_traces(tm_filters)
        #log(f'    {len(ret.traces)=} => {len(ret2.traces)=}')
        return ret2

    # Check that `analysis()` does not leak.
    #
    num_leaks = 0
    with open(file_path,'rb') as f:
        bytes_data = f.read()
    
    tracemalloc.start(30)
    snapshot_prev = get_snapshot()
    
    for it in range(2):
        log('')
        log(f'{it=}')
        
        current, peak = tracemalloc.get_traced_memory()
        log(f'    {current=} {peak=}')
        
        analysis(bytes_data)
        gc.collect()
        snapshot = get_snapshot()
        
        top_stats = snapshot.compare_to(snapshot_prev, 'traceback')
        snapshot_prev = snapshot
        
        top_stats = sorted(top_stats, key=lambda x: -x.size_diff)
        for block_num, stat in enumerate(top_stats[0:10]):
            if stat.size_diff > 0:
                log(f'    Leak detected')
                log(f'    {block_num=} {stat.size_diff=}: {stat}')
                bt = ''
                for frame in stat.traceback:
                    bt += f'        {frame.filename}:{frame.lineno}\n'
                log(bt)
                # We ignore extra allocations in the first iteration.
                if it != 0:
                    num_leaks += 1
    
    assert not num_leaks, f'{num_leaks=}'


def test_4751():
    # We run the actual test in a child process, because otherwise previous
    # tests seem to effect the leak detection causing false positives. It's
    # possible that these could be real leaks, but they are not the ones
    # we are testing for here.
    #
    if os.path.basename(__file__).startswith(f'test_fitz_'):
        # Don't test the `fitz` alias, because we assume our leafname.
        print(f'test_4751(): Not testing with fitz alias.')
        return
    
    if os.environ.get('PYODIDE_ROOT'):
        print('test_4751(): not running on Pyodide - cannot run child processes.')
        return
    
    GITHUB_ACTIONS = os.environ.get('GITHUB_ACTIONS')
    if GITHUB_ACTIONS == 'true':
        # We see additional leaks on Github, don't know why.
        print(f'test_4751(): {GITHUB_ACTIONS=}; not running on Github because known to fail.')
        return
    
    python_version = [int(i) for i in platform.python_version_tuple()[:2]]
    python_version_tuple = tuple(python_version)
    if python_version_tuple < (3, 13):
        # We see additional leaks with python-3.12.
        print(f'test_4751(): not running because known to fail on python < 3.13: {platform.python_version_tuple()=}')
        return
    
    import subprocess
    env_extra = dict(PYTHONPATH = os.path.abspath(f'{__file__}/..'))
    command = f'{sys.executable} -c "import test_memory; test_memory._test_4751()"'
    print('', flush=1)
    print(f'test_4751(): Running: {command!r}', flush=1)
    print(f'test_4751(): With: {env_extra=}', flush=1)
    subprocess.run(command, shell=1, check=1, env=os.environ | env_extra)
