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
        remains = round(deadline - time.time(), 2)
        _logger.info('Waiting for: %s (%s remains)', predicate.__doc__, remains)
        if predicate():
            return True
        time.sleep(retry_interval)
    return False


def main():
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
