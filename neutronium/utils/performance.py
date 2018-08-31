import time

from django.db import connections, reset_queries


class Performance:
    num_levels = 4

    def __init__(self):
        self.start_time_by_level = []
        for i in range(0, self.num_levels):
            self.start_time_by_level.append(time.time())

    def print_time_since(self, level=0, pre_print="", multiplier=1000):
        spaces = ""
        for i in range(0, 3 * level):
            spaces += " "
        time_diff = (time.time() - self.start_time_by_level[level]) * multiplier
        print(f"{spaces}{pre_print}: {time_diff}")

        # Reset time for all lower levels
        self.reset(starting_level=level)

    def get_time_since(self, level=0, multiplier=1000):
        time_diff = (time.time() - self.start_time_by_level[level]) * multiplier

        # Reset time for all lower levels
        self.reset(starting_level=level)

        return time_diff

    @staticmethod
    def clear_latest_queries():
        reset_queries()

    @staticmethod
    def print_latest_queries(num_queries=60, stop_program=False):
        for connection_id in ('default', 'replica1'):
            print(f"== CONNECTION: {connection_id}")
            [print(f"[{q['time']}s] {q['sql']}")
             for q in connections[connection_id].queries[-num_queries:]]
        if stop_program:
            raise ValueError("Stopping program in print_latest_queries as requested.")

    @staticmethod
    def do_latest_queries_contain_keywords(keywords, db='default'):
        for query in connections[db].queries[-60:]:
            for keyword in keywords:
                if keyword in query['sql']:
                    return True
        return False

    def reset(self, starting_level=0):
        for i in range(starting_level, self.num_levels):
            self.start_time_by_level[i] = time.time()
