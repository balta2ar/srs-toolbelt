from contextlib import contextmanager
import logging
from urllib.parse import quote
from datetime import datetime
from time import sleep
from os.path import expanduser, expandvars
from os.path import basename

import requests

from yatetradki.utils import must_env

from telegram.client import Telegram
from telegram.text import Text

logging.getLogger("requests").setLevel(logging.WARNING)


class TdlibClient:
    def __init__(self, db_path=None):
        db_path = db_path or expanduser(expandvars('~/.cache/tdlib/'))
        db_path = expanduser(expandvars(db_path))
        tg = Telegram(
            api_id=must_env('TELEGRAM_API_ID'),
            api_hash=must_env('TELEGRAM_API_HASH'),
            phone=must_env('TELEGRAM_PHONE'),
            database_encryption_key=must_env('TELEGRAM_DB_ENCRYPTION_KEY'),
            files_directory=db_path,
            tdlib_verbosity=0,
        )
        tg.login()
        # if this is the first run, library needs to preload all chats
        # otherwise the message will not be sent
        result = tg.get_chats()
        result.wait()
        self.tg = tg
    @staticmethod
    @contextmanager
    def make(db_path=None):
        client = TdlibClient(db_path=db_path)
        try:
            yield client
        finally:
            client.close()
    def close(self):
        self.tg.stop()
    def recent_filenames_audio(self, chat_id, limit=100):
        filenames = []
        from_message_id = 0
        while len(filenames) < limit:
            print(f'recent in {chat_id} from {from_message_id}')
            result = self.tg.get_chat_history(
                chat_id=chat_id, limit=100, from_message_id=from_message_id
            )
            result.wait()
            messages = result.update['messages']
            if not messages: break
            for m in messages:
                from_message_id = m['id']
                if m['content']['@type'] == 'messageAudio':
                    filenames.append(m['content']['audio']['file_name'])
        return filenames
    def send_audio(self, chat_id, filename):
        params = {
            'chat_id': chat_id,
            'input_message_content': {
                '@type': 'inputMessageAudio',
                'audio': {
                    '@type': 'inputFileLocal',
                    'path': filename,
                },
                'duration': 0,
                'title': basename(filename),
                # 'performer': '',
            },
        }
        result = self.tg.call_method('sendMessage', params, block=True)
        result.wait()
        print(result.update)
        print(result.error_info)
    def send_text(self, chat_id, text):
        params = {
            'chat_id': chat_id,
            'input_message_content': {
                '@type': 'inputMessageText',
                'text': {
                    '@type': 'formattedText',
                    'text': text,
                },
            },
        }
        result = self.tg.call_method('sendMessage', params, block=True)
        result.wait()
        print(result.update)
        print(result.error_info)
    def get_latest_message(self, chat_id):
        result = self.tg.get_chat_history(chat_id=chat_id, limit=1, from_message_id=0)
        result.wait()
        print(result.update)
        messages = result.update['messages']
        if not messages: return None
        return messages[0]
    def edit_message(self, chat_id, message_id, text):
        params = {
            'chat_id': chat_id,
            'message_id': message_id,
            'input_message_content': {
                '@type': 'inputMessageText',
                'text': {
                    '@type': 'formattedText',
                    'text': text,
                },
            },
        }
        result = self.tg.call_method('editMessageText', params, block=True)
        result.wait()
        print(result.update)
        print(result.error_info)
    def print_chats(self):
        offset_order = 2**63-1
        offset_chat_id = 0
        while True:
            result = self.tg.get_chats(offset_order=offset_order, offset_chat_id=offset_chat_id)
            result.wait()
            for chat_id in result.update['chat_ids']:
                chat = self.tg.get_chat(chat_id=chat_id)
                chat.wait()
                offset_order = int(chat.update['positions'][0]['order'])
                offset_chat_id = chat_id
                line = '{0} {1}'.format(chat_id, chat.update['title'])
                print(line)
            else:
                break

def test_tdlib():
    print('start')
    client = TdlibClient()
    chat_id = int(must_env('TELEGRAM_NYHETER_ID'))
    client.recent_filenames_audio(chat_id)
    #name = '/home/bz/dev/src/srs-toolbelt/yatetradki/uitools/nrkup/test.mp3'
    #client.send_audio(chat_id, name)
    #client.close()

def test_edit():
    chat_id = int(must_env('TELEGRAM_ORDBOK_ID'))
    # chat_id = int(must_env('TELEGRAM_NYHETER_ID'))
    print(chat_id)
    client = TdlibClient(db_path='~/.cache/tdlib/ordbok')
    # client.send_text(chat_id, 'testing')
    latest = client.get_latest_message(chat_id)
    text = latest['content']['text']['text']
    print(text)
    text = text + '\n' + 'testing1'
    client.edit_message(chat_id, latest['id'], text)
    client.close()

def test_chats():
    client = TdlibClient(db_path='~/.cache/tdlib/ordbok')
    client.print_chats()
    client.close()

def notify(message):
    ACCESS_TOKEN = must_env('TELEGRAM_ACCESS_TOKEN')
    CHAT_ID = must_env('TELEGRAM_CHAT_ID')

    message = quote(message)
    data = "chat_id={0}&text={1}".format(CHAT_ID, message)
    url = "https://api.telegram.org/bot{0}/sendMessage?{1}".format(ACCESS_TOKEN, data)
    response = requests.post(url, data)
    response.raise_for_status()

class aupto:
    def __init__(self, it, limit):
        self.it = it
        self.limit = limit
        self.i = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        self.i += 1
        if self.i > self.limit:
            raise StopAsyncIteration
        return self.i - 1, await self.it.__anext__() # python3.9 compatibility

def is_today(dt):
    #fmt = '%Y%m%d-%H%M'
    fmt = '%Y%m%d'
    today = datetime.utcnow()
    a = today.strftime(fmt)
    b = dt.strftime(fmt)
    #print(a, b)
    return a == b

def add_word(text, word):
    words = [x.strip().lower() for x in text.splitlines()]
    if word in words: return text, False
    return '\n'.join(words + [word]), True

class WordLogger:
    MAX_SIZE = 4096
    def __init__(self, tg, chat_id):
        self.tg = tg
        self.chat_id = chat_id
    def add(self, word):
        logging.info('Telegram: adding word: %s', word)
        word = word.strip().lower()
        latest = self.tg.get_latest_message(chat_id=self.chat_id)
        text = latest['content']['text']['text']
        when = datetime.fromtimestamp(latest['date'])
        if latest is None or not is_today(when):
            self.tg.send_text(self.chat_id, word)
        else:
            text, updated = add_word(text, word)
            if updated and len(text) < self.MAX_SIZE:
                self.tg.edit_message(self.chat_id, latest['id'], text)

def test_log(text):
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
    channel_id = int(must_env('TELEGRAM_ORDBOK_ID'))
    tg = TdlibClient(db_path='~/.cache/tdlib/ordbok')
    wl = WordLogger(tg, channel_id)
    wl.add(text)
