# import abc
from pickle import dump as pickle_dump
from pickle import load as pickle_load
from threading import Lock
from collections import OrderedDict

from yatetradki.types import eval_word


class Cache(object):
    pass
    # __meta__ = abc.ABCMeta

    # @abc.abstractmethod
    # @property
    # def order(self):
    #     """"""

    # @abc.abstractmethod
    # @order.setter
    # def order(self, value):
    #     """"""

    # @abc.abstractmethod
    # def flush(self):
    #     """"""

    # @abc.abstractmethod
    # def put(self, key, value):
    #     """"""

    # @abc.abstractmethod
    # def get(self, key):
    #     """"""

    # @abc.abstractmethod
    # def contains(self, key):
    #     """"""


class PickleCache(Cache):
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

    def put(self, key, value):
        with self._lock:
            self._cache[key] = value

    def get(self, key):
        with self._lock:
            return self._cache.get(key)

    def contains(self, key):
        with self._lock:
            return key in self._cache


class EvalReprTsvCache(Cache):
    _ORDER = '__order__'

    def __init__(self, cache_filename):
        self._cache_filename = cache_filename
        self._cache = self._load()
        self._lock = Lock()
        self._flushed_keys = set(self._cache.keys())

    def _construct_pair(self, line):
        word, string = line.split('\t')
        return word, eval_word(string)

    def _load(self):
        if not self._cache_filename:
            return OrderedDict()
        try:
            with open(self._cache_filename) as f:
                return OrderedDict([self._construct_pair(line)
                                    for line in f if line.strip()])
        except IOError:
            #print('Cannot load cache from file {0}'
            #      .format(self._cache_filename))
            return OrderedDict()

    @property
    def order(self):
        return list(self._cache.keys())
        # return self._cache[self._ORDER]

    @order.setter
    def order(self, value):
        # self._cache[self._ORDER] = value
        # TODO: IMPLEMENT ME
        pass

    def flush(self):
        with self._lock:
            if not self._cache_filename:
                return
            with open(self._cache_filename, 'a') as f:
                f.writelines([u'{0}\t{1}\n'.format(key, repr(value))
                                           .encode('utf-8')
                              for key, value in self._cache.items()
                              if key not in self._flushed_keys])
                self._flushed_keys = set(self._cache.keys())

    def put(self, key, value):
        with self._lock:
            self._cache[key] = value

    def get(self, key):
        with self._lock:
            return self._cache.get(key)

    def contains(self, key):
        with self._lock:
            return key in self._cache
