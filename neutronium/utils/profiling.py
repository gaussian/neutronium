
import time
import cProfile
from contextlib import contextmanager

cprofiler = None


def start_cprofile():
    global cprofiler
    cprofiler = cProfile.Profile()
    print("cProfile is ready to profile...")
    cprofiler.disable()


def end_cprofile(filename="cprofile"):
    global cprofiler
    if cprofiler and cprofiler.getstats():
        filename = f"{filename}-{int(time.time())}.pstat"
        print(f"Dumping profile to {filename}")
        cprofiler.dump_stats(filename)


def start_cprofile_segment():
    global cprofiler
    if cprofiler:
        cprofiler.enable()


def end_cprofile_segment():
    global cprofiler
    if cprofiler:
        cprofiler.disable()


def with_cprofile_segment(func):
    def profiled_func(*args, **kwargs):
        start_cprofile_segment()
        result = func(*args, **kwargs)
        end_cprofile_segment()
        return result
    return profiled_func


@contextmanager
def cprofile_segment(enable=True):
    if enable:
        start_cprofile_segment()
    yield
    if enable:
        end_cprofile_segment()


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
