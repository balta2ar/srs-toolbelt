import logging
from itertools import zip_longest


DEFAULT_DRIVER_NAME = 'phantomjs'
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOGGER_NAME = 'memrise_sync'


def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)
