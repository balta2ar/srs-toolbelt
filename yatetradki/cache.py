from pickle import dump as pickle_dump
from pickle import load as pickle_load
from threading import Lock


class Cache(object):
    _ORDER = '__order__'

    def __init__(self, cache_filename):
        self._cache_filename = cache_filename
        self._cache = self._load()
        self._lock = Lock()

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

    @property
    def order(self):
        return self._cache[self._ORDER]

    @order.setter
    def order(self, value):
        self._cache[self._ORDER] = value

    def flush(self):
        with self._lock:
            if not self._cache_filename:
                return
            with open(self._cache_filename, 'w') as f:
                pickle_dump(self._cache, f)

    def save(self, key, value):
        with self._lock:
            self._cache[key] = value

    def load(self, key):
        with self._lock:
            return self._cache.get(key)

    def contains(self, key):
        with self._lock:
            return key in self._cache
