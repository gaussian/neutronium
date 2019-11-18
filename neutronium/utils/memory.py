import psutil
import os


def print_memory_usage(label=None):
    """
    Prints current memory usage stats.
    See: https://stackoverflow.com/a/15495136

    :return: None
    """

    MEGA = 10 ** 6

    svm = psutil.virtual_memory()
    total, available, percent, used, free = svm.total / MEGA, svm.available / MEGA, svm.percent, svm.used / MEGA, svm.free / MEGA
    proc = psutil.Process(os.getpid()).memory_info().rss / MEGA
    message = f"process = {proc} total = {total} available = {available} used = {used} free = {free} " \
              f"percent = {percent}"
    if label:
        message = f"{label} {message}"
    print(message)


def print_memory_growth(label=None):
    import objgraph

    if label:
        print(label)

    objgraph.show_growth()


def print_ref_graph(obj):
    import objgraph
    objgraph.show_refs([obj], filename='sample-graph.png')
