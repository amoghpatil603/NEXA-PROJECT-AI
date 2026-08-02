"""Dummy psutil module for environment compatibility."""
class Process:
    def __init__(self, pid=None):
        pass
    def memory_info(self):
        class Mem:
            rss = 350 * 1024 * 1024
        return Mem()
