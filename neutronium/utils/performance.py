import time


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

    def reset(self, starting_level=0):
        for i in range(starting_level, self.num_levels):
            self.start_time_by_level[i] = time.time()
