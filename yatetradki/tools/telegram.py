import logging
from urllib.parse import quote
from datetime import datetime
from time import sleep

import requests

from yatetradki.utils import must_env

logging.getLogger("requests").setLevel(logging.WARNING)


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
    words = [x.strip() for x in text.splitlines()]
    if word in words: return text, False
    return '\n'.join(words + [word]), True

async def get_latest(client, chat):
    limit = 1
    async for i, m in aupto(client.iter_messages(chat), limit):
        return m
    return None

class WordLogger:
    MAX_SIZE = 4096
    def __init__(self, phone, api_id, api_hash, channel_id):
        from telethon import TelegramClient
        from telethon import utils
        self.phone = phone
        self.api_id = api_id
        self.api_hash = api_hash
        self.channel_id = channel_id
        self.client = TelegramClient('ordbok', api_id, api_hash)
        real_id, peer_type = utils.resolve_id(channel_id)
    def get_code(self):
        logging.info('Telegram: need code, put it into /tmp/code, waiting 30s')
        sleep(30.0)
        logging.info('Telegram: reading code from /tmp/code now')
        return open('/tmp/code').read().strip()
    async def start(self):
        await self.client.start(phone=self.phone, code_callback=self.get_code)
    async def add(self, word):
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
        #loop.run_until_complete(wl.start())
        print('Telegram: running forever')
        loop.run_forever()
    #set_event_loop(loop)
    #start()
    #source_signal.connect(on_translate)
    print('Telegram: creating thread')
    t = Thread(target=start, daemon=True)
    t.start()
    t.join()
