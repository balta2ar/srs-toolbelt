"""
This module contains functionality related to telegram notifications.
"""
import logging
from pathlib import Path
from collections import namedtuple
import yaml
from requests import post
from os.path import isfile
from shutil import move
from os import remove

from yatetradki.korean.memrise.common import DEFAULT_LOGGER_NAME


BASE_DIR = Path('/mnt/data/prg/src/bz/python/yandex-slovari-tetradki/telegrambot')
CURRENT_STATE_FILENAME = BASE_DIR / 'current_state.txt'
LAST_STATE_FILENAME = BASE_DIR / 'last_state.txt'

_logger = logging.getLogger(DEFAULT_LOGGER_NAME)


TelegramNotificationSettings = namedtuple(
    'TelegramNotificationSettings',
    'token chat_id')


def read_telegram_notification_settings(filename):
    with open(filename) as file_:
        settings = yaml.load(file_)['notification']['telegram']
        return TelegramNotificationSettings(settings['token'], settings['chat_id'])


def _notify_in_chat(token, chat_id, message):
    url = 'https://api.telegram.org/bot%s/sendMessage' % token
    response = post(url=url, data={'chat_id': chat_id, 'text': message})
    return response.status_code, response.text


def _append_to_file(filename, data, end='\n'):
    with open(filename, 'a') as file_:
        return file_.write('%s%s' % (data, end))


def slurp(filename):
    with open(filename) as file_:
        return file_.read()


def _touch(filename):
    if not isfile(filename):
        _append_to_file(filename, '', end='')


def _reset(filename):
    if isfile(filename):
        remove(filename)
    _append_to_file(filename, '', end='')


def start_session():
    """
    Initialize state files (current and last).
    """
    _reset(CURRENT_STATE_FILENAME)
    _touch(LAST_STATE_FILENAME)


def append_telegram_message(message):
    """
    Append another message to the current state.
    """
    _append_to_file(CURRENT_STATE_FILENAME, message)


def finish_session(telegram_settings):
    """
    Send accumulated state as a notification and move current state to last.
    """
    current_state = slurp(CURRENT_STATE_FILENAME)
    last_state = slurp(LAST_STATE_FILENAME)

    if current_state != last_state:
        # settings = _read_telegram_notification_settings()
        message = current_state
        # if not message:
            # message = 'No new messages during the last sync. Sync is back to normal.'
        if message:
            _logger.info('Finishing telegram session, sending this to the chat: %s', message)
            _status_code, _response = _notify_in_chat(
                telegram_settings.token, telegram_settings.chat_id, message)
        move(CURRENT_STATE_FILENAME, LAST_STATE_FILENAME)
