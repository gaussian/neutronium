def print_top_heap_memory_objects(n=20):
    """
    The code iterates through sys.modules, which contains modules that have been imported. Many of these
    modules only represent a small "handle" to the code/data they manage. The heavy lifting might be done
    elsewhere (e.g., in large data structures created after module import, or in objects the modules create
    later) and thus not be reflected in the module object's size.

    The pympler.asizeof function calculates the size of Python objects from the Python heap. However, many
    modules (especially those with C extensions) allocate memory outside the Python-managed memory (e.g.,
    in C libraries). Such allocations aren't captured by asizeof.asizeof().
    """
    import sys
    from pympler import asizeof

    modules_memory = {}
    for name, module in list(sys.modules.items()):
        if not module:
            continue
        try:
            size = asizeof.asizeof(module)
        except Exception as e:
            # Log or print the error if you wish:
            print(f"Skipping module {name} due to error: {e}")
            continue
        modules_memory[name] = size

    # Print the top n memory-consuming modules:
    for name, size in sorted(
        modules_memory.items(), key=lambda item: item[1], reverse=True
    )[:n]:
        print(f"{name}: {size / 1024:.2f} KB")


def print_memory_usage(label=None):
    """
    Prints current memory usage stats.
    See: https://stackoverflow.com/a/15495136

    :return: None
    """
    import os
    import psutil

    MEGA = 10**6

    svm = psutil.virtual_memory()
    total, available, percent, used, free = (
        svm.total / MEGA,
        svm.available / MEGA,
        svm.percent,
        svm.used / MEGA,
        svm.free / MEGA,
    )
    proc = psutil.Process(os.getpid()).memory_info().rss / MEGA
    data_points = [
        f"process = {proc}",
        f"total = {total}",
        f"available = {available}",
        f"used = {used}",
        f"free = {free}",
        f"percent = {percent}",
    ]
    message = " // ".join(data_points)
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

    objgraph.show_refs([obj], filename="sample-graph.png")
