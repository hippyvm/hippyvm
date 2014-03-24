

class RegexpCache(object):
    # TODO: this should use an LRU cache, and be elidable for the JIT.
    def __init__(self, space):
        self._contents = {}

    def get(self, pattern):
        return self._contents.get(pattern, None)

    def set(self, pattern, compiled_regexp):
        self._contents[pattern] = compiled_regexp
