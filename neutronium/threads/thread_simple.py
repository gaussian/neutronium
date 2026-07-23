import threading


class SimpleThread(threading.Thread):
    result = None

    def __init__(self, func, run_sync=False, *args, **kwargs):
        super().__init__()
        self.kwargs = kwargs
        # for kwarg in kwargs.items():
        #     setattr(self, kwarg[0], kwarg[1])
        self.func = func
        self.run_sync = run_sync
        self.exception = None

    def start(self):
        # Allow for override to run synchronously...
        if self.run_sync:
            self.run()
        else:
            super().start()

    def run(self):
        try:
            self.result = self.func(**self.kwargs)
        except Exception as e:
            self.exception = e

    def get_result(self):
        if not self.run_sync:
            self.join()
        return self.result


class SimpleThreadManager:
    def __init__(self, pass_through_exceptions=False):
        self.threads = []
        self.results_list = []
        self.results_total = 0
        self.pass_through_exceptions = pass_through_exceptions

    def start_thread(self, simple_thread):
        """
        Add thread to the threads list and start it running.
        :param simple_thread:
        :type: SimpleThread
        :return:
        """
        simple_thread.start()
        self.threads.append(simple_thread)

    def wait_return_results_as_list(self):
        for thread in self.threads:
            result = thread.get_result()
            if thread.exception and self.pass_through_exceptions:
                raise thread.exception
            if result is not None:
                if isinstance(result, (list, set)):
                    self.results_list += result
                else:
                    self.results_list.append(result)
        self.threads = []
        return self.results_list

    def wait_return_results_as_total(self):
        for thread in self.threads:
            result = thread.get_result()
            if result:
                self.results_total += result
        self.threads = []
        return self.results_total
