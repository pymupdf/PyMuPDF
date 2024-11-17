import multiprocessing
import os
import time

import pymupdf


# Support for concurrent processing of document pages.
#

class _worker_State:
    pass
_worker_state = _worker_State()


def _worker_init(
        path,
        initfn,
        initfn_args,
        initfn_kwargs,
        pagefn,
        pagefn_args,
        pagefn_kwargs,
        stats,
        ):
    # pylint: disable=attribute-defined-outside-init
    _worker_state.path = path
    _worker_state.pagefn = pagefn
    _worker_state.pagefn_args = pagefn_args
    _worker_state.pagefn_kwargs = pagefn_kwargs
    _worker_state.stats = stats
    _worker_state.document = None
    if initfn:
        initfn(*initfn_args, **initfn_kwargs)


def _stats_write(t, label):
    t = time.time() - t
    if t >= 0.1:
        pymupdf.log(f'{os.getpid()=}: {t:2f}s: {label}.')


def _worker_fn(page_number):
    # Create Document from filename if we haven't already done so.
    if not _worker_state.document:
        if _worker_state.stats:
            t = time.time()
        _worker_state.document = pymupdf.Document(_worker_state.path)   # pylint: disable=attribute-defined-outside-init
        if _worker_state.stats:
            _stats_write(t, 'pymupdf.Document()')
    
    if _worker_state.stats:
        t = time.time()
    page = _worker_state.document[page_number]
    if _worker_state.stats:
        _stats_write(t, '_worker_state.document[page_number]')
    
    if _worker_state.stats:
        t = time.time()
    ret = _worker_state.pagefn(
            page,
            *_worker_state.pagefn_args,
            **_worker_state.pagefn_kwargs,
            )
    if _worker_state.stats:
        _stats_write(t, '_worker_state.pagefn()')
    
    return ret
    

def _multiprocessing(
        path,
        pages,
        pagefn,
        pagefn_args,
        pagefn_kwargs,
        initfn,
        initfn_args,
        initfn_kwargs,
        concurrency,
        stats,
        ):
    #print(f'_worker_mp(): {concurrency=}', flush=1)
    with multiprocessing.Pool(
            concurrency,
            _worker_init,
            (
                path,
                initfn, initfn_args, initfn_kwargs,
                pagefn, pagefn_args, pagefn_kwargs,
                stats,
            ),
            ) as pool:
        result = pool.map_async(_worker_fn, pages)
        return result.get()
    

def _fork(
        path,
        pages,
        pagefn,
        pagefn_args,
        pagefn_kwargs,
        initfn,
        initfn_args,
        initfn_kwargs,
        concurrency,
        stats,
        ):
    verbose = 0
    if concurrency is None:
        concurrency = multiprocessing.cpu_count()
    # We write page numbers to `queue_down` and read `(page_num, text)` from
    # `queue_up`. Workers each repeatedly read the next available page number
    # from `queue_down`, extract the text and write it onto `queue_up`.
    #
    # This is better than pre-allocating a subset of pages to each worker
    # because it ensures there will never be idle workers until we are near the
    # end with fewer pages left than workers.
    #
    queue_down = multiprocessing.Queue()
    queue_up = multiprocessing.Queue()
    def childfn():
        document = None
        if verbose:
            pymupdf.log(f'{os.getpid()=}: {initfn=} {initfn_args=}')
        _worker_init(
                path,
                initfn,
                initfn_args,
                initfn_kwargs,
                pagefn,
                pagefn_args,
                pagefn_kwargs,
                stats,
                )
        while 1:
            if verbose:
                pymupdf.log(f'{os.getpid()=}: calling get().')
            page_num = queue_down.get()
            if verbose:
                pymupdf.log(f'{os.getpid()=}: {page_num=}.')
            if page_num is None:
                break
            try:
                if not document:
                    if stats:
                        t = time.time()
                    document = pymupdf.Document(path)
                    if stats:
                        _stats_write(t, 'pymupdf.Document(path)')
                
                if stats:
                    t = time.time()
                page = document[page_num]
                if stats:
                    _stats_write(t, 'document[page_num]')
                
                if verbose:
                    pymupdf.log(f'{os.getpid()=}: {_worker_state=}')
                
                if stats:
                    t = time.time()
                ret = pagefn(
                        page,
                        *_worker_state.pagefn_args,
                        **_worker_state.pagefn_kwargs,
                        )
                if stats:
                    _stats_write(t, f'{page_num=} pagefn()')
            except Exception as e:
                if verbose: pymupdf.log(f'{os.getpid()=}: exception {e=}')
                ret = e
            if verbose:
                pymupdf.log(f'{os.getpid()=}: sending {page_num=} {ret=}')
                
            queue_up.put( (page_num, ret) )

    error = None

    pids = list()
    try:
        # Start child processes.
        if stats:
            t = time.time()
        for i in range(concurrency):
            p = os.fork()   # pylint: disable=no-member
            if p == 0:
                # Child process.
                try:
                    try:
                        childfn()
                    except Exception as e:
                        pymupdf.log(f'{os.getpid()=}: childfn() => {e=}')
                        raise
                finally:
                    if verbose:
                        pymupdf.log(f'{os.getpid()=}: calling os._exit(0)')
                    os._exit(0)
            pids.append(p)
        if stats:
            _stats_write(t, 'create child processes')

        # Send page numbers.
        if stats:
            t = time.time()
        if verbose:
            pymupdf.log(f'Sending page numbers.')
        for page_num in range(len(pages)):
            queue_down.put(page_num)
        if stats:
            _stats_write(t, 'Send page numbers')

        # Collect results. We give up if any worker sends an exception instead
        # of text, but this hasn't been tested.
        ret = [None] * len(pages)
        for i in range(len(pages)):
            page_num, text = queue_up.get()
            if verbose:
                pymupdf.log(f'{page_num=} {len(text)=}')
            assert ret[page_num] is None
            if isinstance(text, Exception):
                if not error:
                    error = text
                break
            ret[page_num] = text

        # Close queue. This should cause exception in workers and terminate
        # them, but on macos-arm64 this does not seem to happen, so we also
        # send None, which makes workers terminate.
        for i in range(concurrency):
            queue_down.put(None)
        if verbose: pymupdf.log(f'Closing queues.')
        queue_down.close()

        if error:
            raise error
        if verbose:
            pymupdf.log(f'After concurrent, returning {len(ret)=}')
        return ret
        
    finally:
        # Join all child processes.
        if stats:
            t = time.time()
        for pid in pids:
            if verbose:
                pymupdf.log(f'waiting for {pid=}.')
            e = os.waitpid(pid, 0)
            if verbose:
                pymupdf.log(f'{pid=} => {e=}')
        if stats:
            _stats_write(t, 'Join all child proceses')
