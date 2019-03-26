
import os

import cProfile


# From https://zapier.com/engineering/profiling-python-boss/
def with_cprofile(func):
    def profiled_func(*args, **kwargs):
        profile = cProfile.Profile()
        try:
            profile.enable()
            result = func(*args, **kwargs)
            profile.disable()
            return result
        finally:
            filename = os.path.expanduser(
                os.path.join('~', func.__name__ + '.pstat')
            )
            profile.dump_stats(filename)
    return profiled_func


# From https://zapier.com/engineering/profiling-python-boss/
try:
    from line_profiler import LineProfiler

    def do_profile(follow=[]):
        def inner(func):
            def profiled_func(*args, **kwargs):
                try:
                    profiler = LineProfiler()
                    profiler.add_function(func)
                    for f in follow:
                        profiler.add_function(f)
                    profiler.enable_by_count()
                    return func(*args, **kwargs)
                finally:
                    profiler.print_stats()
            return profiled_func
        return inner

except ImportError:
    def do_profile(follow=[]):
        """Helpful if you accidentally leave in production!"""
        def inner(func):
            def nothing(*args, **kwargs):
                return func(*args, **kwargs)
            return nothing
        return inner
