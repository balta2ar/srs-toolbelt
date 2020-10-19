"""
This module contains helpers to control Anki (sync, import packages).
"""
import time
from contextlib import contextmanager
from multiprocessing import Process

import aqt

from yatetradki.tools.anki_connect import invoke
from yatetradki.tools.log import get_logger

_logger = get_logger('anki_control')


class ErrorAnkiAlreadyRunning(Exception):
    pass


class ErrorAnkiCannotStart(Exception):
    pass


@contextmanager
def new_anki_instance():
    if anki_is_running():
        _logger.info('Anki is already running (must have started manually), skipping sync to avoid conflicts')
        raise ErrorAnkiAlreadyRunning()

    anki = Process(target=aqt.run)
    anki.start()

    if not wait_for(anki_is_running):
        _logger.error('Timeout awaiting anki to start up')
        raise ErrorAnkiCannotStart()

    _logger.info('Anki is running, starting sync')
    try:
        yield
    finally:
        _logger.info('Sync is done, exiting')
        anki.terminate()
        anki.join()


def anki_is_not_running():
    """Anki is not running"""
    return not anki_is_running()


def anki_is_running():
    """Anki is running"""
    try:
        result = invoke('version')
        _logger.info('anki_is_running: version: %s', result)
    except Exception as e:
        _logger.info('Anki not available yet: %s', e)
        return False
    return True


def wait_for(predicate, retry_interval=1.0, max_timeout=10.0):
    deadline = time.time() + max_timeout
    while time.time() < deadline:
        remains = deadline - time.time()
        _logger.info('Waiting %0.1f for: %s (%0.1f remains)', retry_interval, predicate.__doc__, remains)
        time.sleep(retry_interval)
        if predicate():
            return True
    return False
