#!/usr/bin/env python3
from __future__ import annotations
import asyncio
import json
import logging
import re
import shutil
from asyncio import TimeoutError as AsyncioTimeoutError
from asyncio import create_subprocess_shell
from asyncio import new_event_loop
from bisect import bisect_right
from contextlib import asynccontextmanager
from datetime import datetime
from glob import glob
from itertools import groupby
from os import environ
from os import makedirs
from os.path import dirname
from os.path import exists
from os.path import expanduser
from os.path import expandvars
from os.path import getsize
from os.path import isfile
from os.path import join
from shlex import quote
from tempfile import NamedTemporaryFile
from typing import List

import hachoir
import pysubs2
from aiohttp import ClientSession
from aiohttp import web
from aiohttp_middlewares import cors_middleware
from bs4 import BeautifulSoup
from diskcache import Cache
from urllib3 import disable_warnings
from yatetradki.tools.telega import TdlibClient
from yatetradki.utils import must_env

from episode import Episode, ui_notify, which

FORMAT = '%(asctime)-15s %(levelname)s (%(name)s) %(message)s'
logging.basicConfig(format=FORMAT, level=logging.DEBUG)

def expand(path):
    return expanduser(expandvars(path))

HOST = '127.0.0.1'
PORT = 7000
TDLIB = expand('~/.cache/tdlib/nrkup')


def disable_logging():
    disable_warnings()
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    logging.getLogger('telethon').setLevel(logging.CRITICAL)
    logging.getLogger('telegram').setLevel(logging.WARNING)


class TeleFile:
    def __init__(self):
        self.api_id = must_env('TELEGRAM_API_ID')
        self.api_hash = must_env('TELEGRAM_API_HASH')
        self.channel_id = int(must_env('TELEGRAM_NYHETER_ID'))
        self.phone = int(must_env('TELEGRAM_PHONE'))

    async def init(self):
        self.client = await init_client(self.phone, self.api_id, self.api_hash, self.channel_id)
        self.chat = await self.client.get_entity(self.channel_id)

    async def recent(self, limit=100):
        out = []
        async for _, m in aupto(self.client.iter_messages(self.chat), limit):
            try:
                out.append(m.file.name)
            except AttributeError:
                pass
        logging.info('Recent files: %s', out)
        return out

    async def send(self, filename):
        logging.info('Sending %s', filename)
        await ui_notify('NRKUP', 'Sending: ' + filename)
        await self.client.send_file(self.chat, filename, supports_streaming=True)

    async def close(self):
        await self.client.disconnect()

    @staticmethod
    async def make():
        tele_file = TeleFile()
        await tele_file.init()
        return tele_file

    @staticmethod
    @asynccontextmanager
    async def open():
        tele = await TeleFile.make()
        try:
            yield tele
        finally:
            await tele.close()


async def fetch(tg, url):
    chat_id = int(must_env('TELEGRAM_NYHETER_ID'))
    logging.info('chat_id = %d', chat_id)
    episode = await Episode.make(url)
    logging.info('Found episode: %s', episode)
    filename = await episode.mp3() # make sure file is present in fs
    if episode.name in tg.recent_filenames_audio(chat_id):
        await ui_notify('NRKUP', 'Already available: ' + episode.name)
        return
    logging.info('Sending %s', filename)
    await ui_notify('NRKUP', 'Sending: ' + filename)
    tg.send_audio(chat_id, filename)
    await ui_notify('NRKUP', 'Uploaded: ' + episode.name)


async def subtitles(url):
    episode = await Episode.make(url)
    logging.info('Found episode: %s', episode)
    return await episode.pretty_srt()


class HttpServer:
    def __init__(self, host, port, loop, tg):
        self.host = host
        self.port = port
        self.loop = loop
        self.tg = tg

    async def run(self):
        logging.info('Starting HTTP server on %s:%s', self.host, self.port)
        app = web.Application(middlewares=[cors_middleware(allow_all=True)])
        app.router.add_route('POST', '/download', self.download)
        app.router.add_route('GET', '/subtitles', self.subtitles)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()

    async def download(self, request):
        try:
            url = (await request.json()).get('url')
            if not url: return web.Response(status=400, text='Missing url')
            await ui_notify('NRKUP', 'Fetching: ' + url)
            await fetch(self.tg, url)
            return web.Response(text='OK ' + url)
        except Exception as e:
            logging.exception(e)
            return web.Response(status=400, text=str(e))

    async def subtitles(self, request):
        url = request.query.get('url')
        if not url: return web.Response(status=400, text='Missing url')
        try:
            return web.Response(text=await subtitles(url))
        except Exception as e:
            logging.exception(e)
            message = 'Cannot get subtitles for ' + url + ': ' + str(e)
            return web.Response(status=500, text=message)


def load_env(filename):
    filename = expanduser(expandvars(filename))
    if not exists(filename):
        logging.warning('Missing env file "%s"', filename)
        return
    with open(filename, 'r') as f:
        for line in [x.strip() for x in f.readlines()]:
            if line.startswith('#'): continue
            key, value = line.strip().split('=', 1)
            environ[key] = value


def test_init(url=None):
    #
    # return
    load_env('~/.telegram')
    url = 'https://tv.nrk.no/serie/distriktsnyheter-nordland/202308/DKNO98082423'
    with TdlibClient.make(TDLIB) as tg:
        logging.info('created client')
    return
    disable_logging()
    loop = new_event_loop()
    host, port = HOST, PORT
    loop.run_until_complete(fetch(tg, url))
    # loop.run_until_complete(HttpServer(host, port, loop).run())
    # loop.run_forever()


def testsub(url=None):
    # url = 'https://tv.nrk.no/serie/distriktsnyheter-nordland/202206/DKNO98061322/avspiller'
    url = 'https://tv.nrk.no/serie/distriktsnyheter-nordland/202207/DKNO98072622/avspiller'
    disable_logging()
    loop = new_event_loop()
    #loop.run_until_complete(subtitles(url))
    print(loop.run_until_complete(subtitles(url)))


def assert_bin(*names):
    for name in names:
        assert which(name), name

def main():
    assert_bin('notify-send', 'ffmpeg', 'nrkdownload', 'sox', 'detect-speakers')
    logging.info('hachoir version: %s', hachoir.__version__)
    load_env('~/.telegram')
    disable_logging()
    loop = new_event_loop()
    host, port = HOST, PORT
    with TdlibClient.make(TDLIB) as tg:
        loop.run_until_complete(HttpServer(host, port, loop, tg).run())
        loop.run_forever()


if __name__ == '__main__':
    main()
