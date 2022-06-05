#!/usr/bin/env python3
import asyncio
import logging
from asyncio import create_subprocess_shell
from asyncio import new_event_loop
from asyncio import run_coroutine_threadsafe
from contextlib import asynccontextmanager
from datetime import datetime
from glob import glob
from hashlib import sha1
from os import makedirs
from os.path import isfile
from os.path import join
from shlex import quote
from urllib.request import urlopen

from aiohttp import web
from aiohttp_middlewares import cors_middleware
from bs4 import BeautifulSoup
from urllib3 import disable_warnings
from yatetradki.tools.telegram import aupto
from yatetradki.tools.telegram import init_client
from yatetradki.utils import must_env

FORMAT = '%(asctime)-15s %(levelname)s (%(name)s) %(message)s'
logging.basicConfig(format=FORMAT, level=logging.DEBUG)

HOST = 'localhost'
PORT = 7000


def disable_logging():
    disable_warnings()
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    logging.getLogger('telethon').setLevel(logging.CRITICAL)


def http_get(url):
    with urlopen(url) as r:
        return r.read()


async def async_run(args):
    cmd = ' '.join(quote(x) for x in args)
    logging.info('Running: %s', cmd)
    proc = await create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise Exception(stderr.decode())


async def ui_notify(title, message):
    await async_run(['notify-send', title, message])


def find_first(pattern):
    files = glob(pattern, recursive=True)
    return files[0] if len(files) > 0 else None


async def nrk_download(url, where) -> str:
    makedirs(where, exist_ok=True)
    logging.info('Downloading %s to %s', url, where)
    await async_run(['nrkdownload', '-d', where, url])
    return find_first(where + '/**/*.m4v')


async def ffmpeg_extract_audio(video, audio):
    logging.info('converting %s to %s', video, audio)
    await async_run(['ffmpeg', '-i', video, '-q:a', '0', '-map', 'a', audio])


class Episode:
    def __init__(self, title, url, date):
        self.title = title
        self.url = url
        self.date = date
        self.short = self.date.strftime('%Y%m%d-%H%M')

    async def get_mp3(self):
        if isfile(self.audio):
            return self.audio
        video = find_first(self.base + '/**/*.m4v')
        if not video:
            await ui_notify('NRKUP', 'Downloading video: ' + self.title)
            video = await nrk_download(self.url, self.base)
        await ui_notify('NRKUP', 'Extracting audio: ' + self.title)
        await ffmpeg_extract_audio(video, self.audio)
        return self.audio

    @property
    def base(self):
        hash = sha1(self.url.encode('utf8')).hexdigest()[:8]
        return f'/tmp/nrkup/{self.short}-{hash}'

    @property
    def audio(self):
        return join(self.base, self.name)

    @property
    def name(self):
        return f'nord-{self.short}.mp3'

    @staticmethod
    def make(url):
        soup = BeautifulSoup(http_get(url), 'html.parser')
        title = soup.find('title').text
        date = soup.find('meta', property='video:release_date').get('content')
        # 2022-06-01T22:55:00+02:00
        date = datetime.strptime(date, '%Y-%m-%dT%H:%M:%S%z')
        return Episode(title, url, date)


class TeleFile:
    def __init__(self):
        self.api_id = must_env('TELEGRAM_API_ID')
        self.api_hash = must_env('TELEGRAM_API_HASH')
        self.channel_id = int(must_env('TELEGRAM_NYHETER_ID'))
        self.phone = int(must_env('TELEGRAM_PHONE'))

    async def init(self):
        self.client = await init_client(self.phone, self.api_id, self.api_hash, self.channel_id)
        self.chat = await self.client.get_entity(self.channel_id)

    async def recent(self, limit=50):
        out = []
        async for i, m in aupto(self.client.iter_messages(self.chat), limit):
            try:
                out.append(m.file.name)
            except AttributeError:
                pass
        logging.info('Recent files: %s', out)
        return out

    async def send(self, filename):
        await self.client.send_file(self.chat, filename)

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


async def fetch(url):
    episode = Episode.make(url)
    async with TeleFile.open() as tele:
        if episode.name in await tele.recent():
            await ui_notify('NRKUP', 'Already available: ' + episode.name)
            return
        await tele.send(await episode.get_mp3())
        await ui_notify('NRKUP', 'Uploaded: ' + episode.name)


class HttpServer:
    def __init__(self, host, port, loop):
        self.host = host
        self.port = port
        self.loop = loop

    async def run(self):
        logging.info('Starting HTTP server on %s:%s', self.host, self.port)
        app = web.Application(middlewares=[cors_middleware(allow_all=True)])
        app.router.add_route('POST', '/download', self.download)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()

    async def download(self, request):
        try:
            url = (await request.json()).get('url')
            if not url: return web.Response(status=400, text='Missing url')
            await ui_notify('NRKUP', 'Fetching: ' + url)
            run_coroutine_threadsafe(fetch(url), self.loop)
            return web.Response(text='OK ' + url)
        except Exception as e:
            return web.Response(status=400, text=str(e))


def test(url=None):
    url = 'https://tv.nrk.no/serie/distriktsnyheter-nordland/202206/DKNO99060122'
    disable_logging()
    loop = new_event_loop()
    host, port = HOST, PORT
    # loop.run_until_complete(fetch(url))
    loop.run_until_complete(HttpServer(host, port, loop).run())
    loop.run_forever()


def main():
    disable_logging()
    loop = new_event_loop()
    host, port = HOST, PORT
    loop.run_until_complete(HttpServer(host, port, loop).run())
    loop.run_forever()


if __name__ == '__main__':
    main()
