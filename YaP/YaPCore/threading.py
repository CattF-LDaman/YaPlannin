import functools
import threading

def threaded_nondaemon(func):
    @functools.wraps(func)
    def wr(*args, **kwargs):

        t = threading.Thread(target=func,args=args,kwargs=kwargs,name=str(func)+str((args,kwargs)),daemon=False)
        t.start()

    return wr

def threaded_daemon(func):
    @functools.wraps(func)
    def wr(*args, **kwargs):

        t = threading.Thread(target=func,args=args,kwargs=kwargs,name=str(func)+str((args,kwargs)),daemon=True)
        t.start()

    return wr

def run_multiple(func, worker_args: list):

    threads = []
    for args in worker_args:
        thread = threading.Thread(target=func, args=args, name="mult_"+str(func)+str((args)))
        thread.start()
        threads.append(thread)
    
    for thread in threads:
        thread.join()