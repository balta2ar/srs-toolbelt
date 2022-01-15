"""
This is a small script that runs Anki, waits for it to sync the db,
and closes. No error checking. This is used to sync db from cron.

Run as follows:

    PYTHONPATH=/usr/share/anki xvfb-run python2 anki_sync_anki_connect.py

"""
import sys
import time
import argparse
from multiprocessing import Process
from os.path import expanduser, expandvars
from os import getenv
from typing import Optional


#sys.path.insert(0, '/usr/share/anki')
#sys.path.insert(0, '/home/ybochkarev/miniconda3/envs/ankienv39/lib/python3.9/site-packages')
#sys.path.insert(0, '/home/ybochkarev/miniconda3/envs/ankienv39/lib/python3.9/PyQt5')
#print(sys.path)
#sys.path.insert(0, '/usr/share/local/anki')
#sys.path.insert(0, '/home/ybochkarev/bin/anki/anki-2.1.49/qt')
#sys.path.insert(0, '/home/ybochkarev/bin/anki/anki-2.1.49/pylib')
import aqt
try:
    from anki.collection import Collection
except ImportError:
    from anki import Collection

from yatetradki.tools.anki_connect import invoke
from yatetradki.tools.anki_control import anki_is_running, wait_for
from yatetradki.tools.log import get_logger

_logger = get_logger('anki_sync_anki_connect')
MEDIA_SYNC_SLEEP = 60.0
SYNC_SHUTDOWN_SLEEP = 10.0
ERROR_OK_FOUND_CHANGES = 0
ERROR_OK_NO_CHANGES = 1
ERROR_CANNOT_START_ANKI = 2
ERROR_ANKI_ALREADY_RUNNING = 3

COLLECTION = expandvars(expanduser(getenv('SRS_ANKI_COLLECTION', '$HOME/.local/share/Anki2/bz/collection.anki2')))

def get_latest_mod(deck_name: str, model_name: str) -> Optional[int]:
    col = Collection(COLLECTION, log=True)
    modelBasic = col.models.by_name(model_name)
    deck = col.decks.by_name(deck_name)
    col.decks.select(deck['id'])
    col.decks.current()['mid'] = modelBasic['id']

    query_template = 'deck:"%s" note:"%s"'
    query = query_template % (deck_name, model_name)
    found_notes = col.find_notes(query)
    if (not found_notes):
        col.close()
        return ERROR_OK_NO_CHANGES

    latest = None
    for fnote in found_notes:
        note = col.getNote(fnote)
        note.note_type()['did'] = deck['id']
        if latest is None or note.mod > latest:
            latest = note.mod
    col.close()
    return latest


def web_sync(deck: str, model: str) -> int:
    if anki_is_running():
        _logger.info('Anki is already running (must have started manually), skipping sync to avoid conflicts')
        return ERROR_ANKI_ALREADY_RUNNING

    detect_changes = (deck is not None) and (model is not None)
    if detect_changes:
        old_modified = get_latest_mod(deck, model)

    anki = Process(target=aqt.run)
    anki.start()

    if not wait_for(anki_is_running):
        _logger.error('Timeout awaiting anki to start up')
        return ERROR_CANNOT_START_ANKI

    _logger.info('Anki is running, starting sync')
    invoke('sync')
    # I have no idea why, but for some reason media files are synced in
    # background and AnkiConnect.sync terminates earlier that the actual sync.
    # So let's sleep a minute.
    time.sleep(MEDIA_SYNC_SLEEP)
    _logger.info('Sync is done, exiting')
    anki.terminate()
    anki.join()
    time.sleep(SYNC_SHUTDOWN_SLEEP)

    if detect_changes:
        new_modified = get_latest_mod(deck, model)
        if None not in (old_modified, new_modified) and new_modified > old_modified:
            return ERROR_OK_FOUND_CHANGES

    return ERROR_OK_NO_CHANGES


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--deck", help="Deck name to search changes in", required=False)
    parser.add_argument("--model", help="Model to use (card type)", required=False)
    args = parser.parse_args()
    code = web_sync(args.deck, args.model)
    sys.exit(code)

if __name__ == '__main__':
    main()
