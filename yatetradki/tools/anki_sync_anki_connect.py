"""
This is a small script that runs Anki, waits for it to sync the db,
and closes. No error checking. This is used to sync db from cron.

Run as follows:

    PYTHONPATH=/usr/share/anki xvfb-run python2 anki_sync_anki_connect.py

"""
import time
import sys
import aqt
import requests
from multiprocessing import Process

from yatetradki.tools.log import get_logger
from yatetradki.tools.anki_connect import invoke

_logger = get_logger('anki_sync_anki_connect')
ERROR_CANNOT_START_ANKI = 1
ERROR_ANKI_ALREADY_RUNNING = 2


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


def main():
    if anki_is_running():
        _logger.info('Anki is already running (must have started manually), skipping sync to avoid conflicts')
        sys.exit(ERROR_ANKI_ALREADY_RUNNING)

    anki = Process(target=aqt.run)
    anki.start()

    if not wait_for(anki_is_running):
        _logger.error('Timeout awaiting anki to start up')
        sys.exit(ERROR_CANNOT_START_ANKI)

    _logger.info('Anki is running, starting sync')
    invoke('sync')
    _logger.info('Sync is done, exiting')
    anki.terminate()
    anki.join()


if __name__ == '__main__':
    main()
