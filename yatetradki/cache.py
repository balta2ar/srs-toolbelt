from pickle import dump as pickle_dump
from pickle import load as pickle_load


class Cache(object):
    def __init__(self, cache_filename):
        self._cache_filename = cache_filename
        self._cache = self._load()

    def _load(self):
        if not self._cache_filename:
            return {}
        try:
            with open(self._cache_filename) as f:
                return pickle_load(f)
        except IOError:
            #print('Cannot load cache from file {0}'
            #      .format(self._cache_filename))
            return {}

    def flush(self):
        if not self._cache_filename:
            return
        with open(self._cache_filename, 'w') as f:
            pickle_dump(self._cache, f)

    def save(self, key, value):
        self._cache[key] = value

    def load(self, key):
        return self._cache.get(key)

    def contains(self, key):
        return key in self._cache
