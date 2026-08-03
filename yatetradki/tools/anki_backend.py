"""
Reusable helpers for talking to the Anki backend.

Anki's backend prints a noisy "blocked main thread for ...ms:" traceback
whenever a slow command runs on the main thread. Anything that talks to
AnkiWeb (login, sync) is always slow, so we run such work on a worker thread
to keep that warning quiet. See anki/_backend.py:_run_command.
"""

import os
import threading

from yatetradki.tools.log import get_logger

_logger = get_logger('anki_backend')


def run_off_main_thread(fn, *args, **kwargs):
    """Run fn(*args, **kwargs) on a worker thread and return its result.

    Exceptions raised inside fn are re-raised on the calling thread, so this is
    transparent to callers apart from silencing Anki's blocked-main-thread
    warning.
    """
    result = []
    error = []

    def _target():
        try:
            result.append(fn(*args, **kwargs))
        except BaseException as exc:  # noqa: BLE001 - re-raised on caller thread
            error.append(exc)

    worker = threading.Thread(target=_target)
    worker.start()
    worker.join()
    if error:
        raise error[0]
    return result[0]


def sync_open_collection(col, user=None, password=None):
    """Sync an already-open Collection with AnkiWeb on a worker thread.

    Credentials default to the ANKIWEB_USER / ANKIWEB_PASSWORD environment
    variables when not passed explicitly.
    """
    user = user or os.getenv('ANKIWEB_USER')
    password = password or os.getenv('ANKIWEB_PASSWORD')
    if not user or not password:
        raise SystemExit(
            'Missing AnkiWeb credentials. Set ANKIWEB_USER and '
            'ANKIWEB_PASSWORD in the environment.')

    def _sync():
        _logger.info('Logging in to AnkiWeb as %s', user)
        auth = col.sync_login(user, password, None)
        _logger.info('Syncing collection (with media)...')
        col.sync_collection(auth, sync_media=True)
        _logger.info('Sync finished.')

    run_off_main_thread(_sync)
