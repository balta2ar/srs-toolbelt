"""
This is a small script that runs Anki, waits for it to sync the db,
and closes. No error checking. This is used to sync db from cron.

Run as follows:

    PYTHONPATH=/usr/share/anki xvfb-run python2 anki_sync_anki_connect.py

"""
import sys
import time
from multiprocessing import Process

sys.path.insert(0, '/usr/share/anki')
import aqt

from yatetradki.tools.anki_connect import invoke
from yatetradki.tools.anki_control import anki_is_running, wait_for
from yatetradki.tools.log import get_logger

_logger = get_logger('anki_sync_anki_connect')
MEDIA_SYNC_SLEEP = 60.0
ERROR_CANNOT_START_ANKI = 1
ERROR_ANKI_ALREADY_RUNNING = 2


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
    # I have no idea why, but for some reason media files are synced in
    # background and AnkiConnect.sync terminates earlier that the actual sync.
    # So let's sleep a minute.
    time.sleep(MEDIA_SYNC_SLEEP)
    _logger.info('Sync is done, exiting')
    anki.terminate()
    anki.join()


if __name__ == '__main__':
    main()
