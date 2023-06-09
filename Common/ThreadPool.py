import sys
import traceback
from concurrent.futures import ThreadPoolExecutor

class ThreadPoolExecutorStackTraced(ThreadPoolExecutor):

    def submit(self, fn, *args, **kwargs):
        # Submits the wrapped function instead of `fn`
        return super(ThreadPoolExecutorStackTraced, self).submit(self._function_wrapper, fn, *args, **kwargs)

    def _function_wrapper(self, fn, *args, **kwargs):
        # Wraps `fn` in order to preserve the traceback of any kind of raised exception
        try:
            return fn(*args, **kwargs)
        except Exception:
            #print("ex")
            print(traceback.format_exc())
            raise sys.exc_info()[0](traceback.format_exc())  
            # Creates an exception of the same type with the traceback as message