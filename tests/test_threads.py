import os
import random
import queue
import threading

import pymupdf


def log(text):
    print(f'{__file__}:  {threading.get_native_id()=} {text}', flush=1)


def threadfn(queue_to_threads, queue_from_threads):
    def tlog(text):
        log(f'### threadfn(): {text}')
    try:
        documents = list()
        while 1:
            action = queue_to_threads.get()
            #tlog(f'{action=}')
            if action == 'quit':
                break
            elif isinstance(action, tuple) and len(action) == 2 and action[0] == 'open':
                path = action[1]
                #tlog(f'Opening {path=}.')
                document = pymupdf.open(path)
                #tlog(f'Have opened {path=}.')
                documents.append(document)
            elif action == 'gettext':
                if documents:
                    document_i = random.randrange(len(documents))
                    document = documents[document_i]
                    page = document[random.randrange(len(document))]
                    text = page.get_text()
            elif action == 'close':
                if len(documents) >= 2:
                    document_i = random.randrange(len(documents))
                    del documents[document_i]
            else:
                assert 0, f'Unrecognised {action=}.'

        #tlog(f'Sending to queue_from_threads: {threading.current_thread()=}.')
        queue_from_threads.put(threading.current_thread())
    except Exception as e:
        tlog(f'error: {e}')
        queue_from_threads.put(e)
            

def test_threads_stress():

    print()
    paths = [
            os.path.normpath(f'{__file__}/../../tests/resources/test_3594.pdf'),
            os.path.normpath(f'{__file__}/../../tests/resources/test_3789.pdf'),
            ]
    
    threads = list()
    
    queue_to_threads = queue.Queue()
    queue_from_threads = queue.Queue()
    
    def put(action):
        #log(f'test_threads_stress(): Sending {action=}.')
        queue_to_threads.put(action)
    
    class Stats:
        pass
    stats = Stats()
    stats.num_opens = 0
    stats.num_gettexts = 0
    stats.num_threads_max = 0
    
    def start_thread():
        thread = threading.Thread(target=threadfn, args=(queue_to_threads, queue_from_threads), daemon=1)
        threads.append(thread)
        thread.start()
        stats.num_threads_max = max(stats.num_threads_max, len(threads))
    
    def quit_thread():
        put('quit')
        stopped_thread = queue_from_threads.get()
        assert isinstance(stopped_thread, threading.Thread), f'A thread has failed: {stopped_thread}'
        #log(f'{stopped_thread=}')
        stopped_thread.join()
        if 0:
            log(f'threads ({len(threads)}):')
            for thread in threads:
                log(f'    {thread=}')
            log(f'{stopped_thread=}')
        threads.remove(stopped_thread)
    
    def open_document():
        path = paths[random.randrange(len(paths))]
        put(('open', path))
        stats.num_opens += 1
    
    for i in range(10):
        start_thread()
        open_document()
    
    numits = 1000
    for i in range(numits):
        op = random.randrange(100)
        if 0:
            log('')
            log(f'{i+1}/{numits}')
            log(f'{len(threads)=}.')
            log(f'{stats.num_opens=}.')
            log(f'{stats.num_gettexts=}.')
            log(f'{op=}.')
        if op < 10:
            # Create new thread.
            start_thread()
        elif op < 15:
            if len(threads) >= 2:
                quit_thread()
        elif op < 30:
            # Open document in a thread.
            open_document()
        elif op == 40:
            # Close document in a thread.
            if threads:
                put('close')
        elif op < 100:
            # get text.
            put('gettext')
            stats.num_gettexts +=1 
        else:
            assert 0, f'Unrecognised {op=}'
    
    log(f'End:')
    log(f'{len(threads)=} {stats.num_opens=} {stats.num_gettexts=} {stats.num_threads_max=}.')
    
    for _ in range(len(threads)):
        quit_thread()
    
    # Ignore any warnings, which can occur for some pages in the documents.
    wt = pymupdf.TOOLS.mupdf_warnings()
    
