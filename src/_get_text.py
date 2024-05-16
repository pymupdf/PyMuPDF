import multiprocessing
import os

import pymupdf


# Support for `method='multiprocessing'`.
#
# By default each `multiprocessing` worker process would create a `Document`
# each time it was asked to process a page. We avoid this by using a global
# `Document` instance. Haven't found a more elegant way - putting state
# into a class on the server before creating workers doesn't work because
# multiprocessing appears to always send the server's state in each iteration.
#
# It's not too bad because this global state is only ever used by workers, so
# doesn't actually limit things in general.
#
_mp_worker_path = None
_mp_worker_document = None
_mp_worker_args_dict = None

def _mp_worker_init(path, args_dict):
    global _mp_worker_path
    global _mp_worker_args_dict
    assert _mp_worker_path is None
    assert _mp_worker_args_dict is None
    _mp_worker_path = path
    _mp_worker_args_dict = args_dict

def _mp_worker(page_number):
    global _mp_worker_document
    if not _mp_worker_document:
        _mp_worker_document = pymupdf.Document(_mp_worker_path)
    page = _mp_worker_document[page_number]
    ret = page.get_text(**_mp_worker_args_dict)
    return ret


def _get_text_mp(
        path,
        pages,
        concurrency,
        args_dict,
        ):
    with multiprocessing.Pool(
            concurrency,
            _mp_worker_init,
            (path, args_dict),
            ) as pool:
        result = pool.map_async(_mp_worker, pages)
        return result.get()


def _get_text_fork(
        path,
        pages,
        concurrency,
        args_dict,
        ):
    '''
    Implementation for `method='fork'`.
    '''
    verbose = 0
    if concurrency is None:
        concurrency = multiprocessing.cpu_count()
    # We send page numbers to queue_pc and collect (page_num, text) from
    # queue_cp. Workers each repeatedly take the next available page number
    # from queue_pc, extract the text and put it onto queue_cp.
    #
    # This is better than pre-allocating a subset of pages to each worker
    # because it ensures there will never be idle workers until we are near
    # the end with fewer pages left than workers.
    #
    queue_pc = multiprocessing.Queue()
    queue_cp = multiprocessing.Queue()
    
    def childfn():
        document = None
        while 1:
            if verbose: pymupdf.log(f'{os.getpid()=}: calling get().')
            page_num = queue_pc.get()
            if verbose: pymupdf.log(f'{os.getpid()=}: {page_num=}.')
            if page_num is None:
                break
            try:
                if document is None:
                    document = pymupdf.Document(path)
                page = document[page_num]
                ret = page.get_text(**args_dict)
            except Exception as e:
                ret = e
            queue_cp.put( (page_num, ret) )

    error = None

    # Start child processes.
    pids = list()
    try:
        for i in range(concurrency):
            p = os.fork()   # pylint: disable=no-member
            if p == 0:
                # Child process.
                try:
                    childfn()
                finally:
                    if verbose: pymupdf.log(f'{os.getpid()=}: calling os._exit(0)')
                    os._exit(0)
            pids.append(p)

        # Send page numbers.
        for page_num in range(len(pages)):
            queue_pc.put(page_num)

        # Collect results.
        ret = [None] * len(pages)
        for i in range(len(pages)):
            page_num, text = queue_cp.get()
            if verbose: pymupdf.log(f'{page_num=} {len(text)=}')
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
            queue_pc.put(None)
        if verbose: pymupdf.log(f'Closing queues.')
        queue_pc.close()

        if error:
            raise error
        if verbose: pymupdf.log(f'After concurrent, returning {len(ret)=}')
        return ret
        
    finally:
        # Join all child proceses.
        for pid in pids:
            if verbose: pymupdf.log(f'waiting for {pid=}.')
            e = os.waitpid(pid, 0)
            if verbose: pymupdf.log(f'{pid=} => {e=}')
