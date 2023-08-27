from contextlib import contextmanager
import logging
from urllib.parse import quote
from datetime import datetime
from time import sleep
from os.path import expanduser, expandvars
from os.path import basename

import requests

from yatetradki.utils import must_env

from telethon import TelegramClient
from telethon import utils

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
        )
        tg.login()
        # if this is the first run, library needs to preload all chats
        # otherwise the message will not be sent
        result = tg.get_chats()
        result.wait()
        self.tg = tg
    @staticmethod
    @contextmanager
    def make():
        client = TdlibClient()
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
    client = TdlibClient()
    #chat_id = int(must_env('TELEGRAM_NYHETER_ID'))
    # client.recent_filenames_audio(chat_id)
    name = '/home/bz/dev/src/srs-toolbelt/yatetradki/uitools/nrkup/test.mp3'
    client.send_audio(chat_id, name)
    client.close()    

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

async def get_latest(client, chat, limit=1):
    async for i, m in aupto(client.iter_messages(chat), limit):
        return m
    return None

async def init_client(phone, api_id, api_hash, channel_id):
    client = TelegramClient('srs-toolbelt', api_id, api_hash)
    real_id, peer_type = utils.resolve_id(channel_id)
    await client.start(phone=phone, code_callback=get_code)
    return client

def get_code():
    logging.info('Telegram: need code, put it into /tmp/code, waiting 30s')
    sleep(30.0)
    logging.info('Telegram: reading code from /tmp/code now')
    return open('/tmp/code').read().strip()

class WordLogger:
    MAX_SIZE = 4096
    def __init__(self, phone, api_id, api_hash, channel_id):
        self.phone = phone
        self.api_id = api_id
        self.api_hash = api_hash
        self.channel_id = channel_id
        self.client = TelegramClient('ordbok', api_id, api_hash)
        real_id, peer_type = utils.resolve_id(channel_id)
    async def start(self):
        await self.client.start(phone=self.phone, code_callback=get_code)
    async def add(self, word):
        word = word.strip().lower()
        chat = await self.client.get_entity(self.channel_id)
        latest = await get_latest(self.client, chat)
        if latest is None or not is_today(latest.date):
            await self.client.send_message(chat, word)
        else:
            text, updated = add_word(latest.text, word)
            if updated and len(text) < self.MAX_SIZE:
                await self.client.edit_message(latest, text)

async def log_word(text):
    api_id = must_env('TELEGRAM_API_ID')
    api_hash = must_env('TELEGRAM_API_HASH')
    channel_id = int(must_env('TELEGRAM_ORDBOK_ID'))
    phone = int(must_env('TELEGRAM_PHONE'))
    word_logger = WordLogger(phone, api_id, api_hash, channel_id)
    await word_logger.start()
    await word_logger.add(text)

from asyncio import new_event_loop, set_event_loop, gather, TimeoutError as AsyncioTimeoutError, run_coroutine_threadsafe
from threading import Thread

def test_log(text):
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
    api_id = must_env('TELEGRAM_API_ID')
    api_hash = must_env('TELEGRAM_API_HASH')
    channel_id = int(must_env('TELEGRAM_ORDBOK_ID'))
    phone = int(must_env('TELEGRAM_PHONE'))
    wl = WordLogger(phone, api_id, api_hash, channel_id)
    loop = new_event_loop()
    async def auth():
        logging.info('Telegram: checking is_user_authorized')
        logging.info('Telegram: is_user_authorized: %s', await wl.client.is_user_authorized())
        logging.info('Telegram: checking is_user_authorized done')
    #@pyqtSlot(str)
    def on_translate(word):
        logging.info('Telegram: add word to history: %s', word)
        run_coroutine_threadsafe(wl.add(word), loop)
    def start():
        print('Telegram: Starting thread')
        set_event_loop(loop)
        print('Telegram: loop set')
        run_coroutine_threadsafe(wl.start(), loop)
        run_coroutine_threadsafe(auth(), loop)
        run_coroutine_threadsafe(wl.add(text), loop)
        # try:
        #     loop.run_until_complete(wl.start())
        #     loop.run_until_complete(auth())
        #     loop.run_until_complete(wl.add(text))
        # except Exception as e:
        #     print('Telegram: exception: %s', e)
        #loop.run_until_complete(auth())
        print('Telegram: running forever')
        loop.run_forever()
    #set_event_loop(loop)
    #start()
    #source_signal.connect(on_translate)
    print('Telegram: creating thread')
    t = Thread(target=start, daemon=True)
    t.start()
    t.join()
