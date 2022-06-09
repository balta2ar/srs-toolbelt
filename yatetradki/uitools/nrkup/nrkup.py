#!/usr/bin/env python3
import asyncio
from asyncio import TimeoutError as AsyncioTimeoutError
from asyncio import create_subprocess_shell
from asyncio import new_event_loop
from asyncio import run_coroutine_threadsafe
from contextlib import asynccontextmanager
from datetime import datetime
from glob import glob
from hashlib import sha1
import logging
from os import environ
from os import makedirs
from os.path import exists
from os.path import expanduser
from os.path import expandvars
from os.path import join
from re import search
from shlex import quote
import shutil

from aiohttp import ClientSession
from aiohttp import web
from aiohttp_middlewares import cors_middleware
from bs4 import BeautifulSoup
import hachoir
from urllib3 import disable_warnings

from yatetradki.tools.telegram import aupto
from yatetradki.tools.telegram import init_client
from yatetradki.utils import must_env

FORMAT = '%(asctime)-15s %(levelname)s (%(name)s) %(message)s'
logging.basicConfig(format=FORMAT, level=logging.DEBUG)

HOST = 'localhost'
PORT = 7000


def expand(path):
    return expanduser(expandvars(path))


def which(program):
    paths = [None, '/usr/local/bin', '/usr/bin', '/bin', '~/bin', '~/.local/bin']
    for path in paths:
        path = expanduser(expandvars(path)) if path else None
        path = shutil.which(program, path=path)
        if path:
            return path


def disable_logging():
    disable_warnings()
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    logging.getLogger('telethon').setLevel(logging.CRITICAL)


async def async_http_get(url, timeout=10.0):
    logging.info('GET %s', url)
    USER_AGENT = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:100.0) Gecko/20100101 Firefox/100.0'
    headers = {'User-Agent': USER_AGENT}
    retries = 3
    async with ClientSession() as session:
        for i in range(retries):
            try:
                async with session.get(url, timeout=timeout, headers=headers) as resp:
                    return await resp.text()
            except AsyncioTimeoutError as e:
                logging.warning('timeout (%s) getting "%s": "%s"', timeout, url, e)
                if i == retries - 1:
                    raise


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
    await async_run([which('notify-send'), title, message])


def find_first(pattern):
    files = glob(pattern, recursive=True)
    return files[0] if len(files) > 0 else None


async def nrk_download(url, where) -> str:
    makedirs(where, exist_ok=True)
    logging.info('Downloading %s to %s', url, where)
    await async_run([expand(which('nrkdownload')), '-d', where, url])
    return find_first(where + '/**/*.m4v')


async def ffmpeg_extract_audio(video, audio):
    logging.info('converting %s to %s', video, audio)
    await async_run([which('ffmpeg'), '-i', video, '-q:a', '0', '-map', 'a', audio])


async def sox_compress_dynamic_range(input, output):
    logging.info('compressing dynamic range %s, %s', input, output)
    await async_run([which('sox'), input, output, 'compand', '0.3,1', '6:-70,-60,-20', '-5', '-90', '0.2'])
    #await async_run(['sox', input, output, 'compand', '0.02,0.20', '5:-60,-40,-10', '-5', '-90', '0.1'])


def cleanup(text):
    lines = [x.strip() for x in text.splitlines()]
    lines = [x for x in lines if '-->' not in x]
    lines = [x for x in lines if search(r'^\d+$', x) is None]
    lines = [x for x in lines if search(r'^$', x) is None]
    return '\n'.join(lines)


class Episode:
    def __init__(self, title, url, date):
        self.title = title
        self.url = url
        self.date = date
        self.short = self.date.strftime('%Y%m%d-%H%M')

    def srt(self):
        with open(find_first(self.base + '/**/*.srt')) as f:
            return f.read()

    async def mp3(self):
        if exists(self.audio):
            return self.audio
        video = find_first(self.base + '/**/*.m4v')
        if not video:
            await ui_notify('NRKUP', 'nwkdownload: Downloading video: ' + self.title)
            video = await nrk_download(self.url, self.base)
        orig_audio = join(self.base, 'orig-' + self.name)
        if not exists(orig_audio):
            await ui_notify('NRKUP', 'ffmpeg: Extracting audio: ' + self.title)
            await ffmpeg_extract_audio(video, orig_audio)
        if not exists(self.audio):
            await ui_notify('NRKUP', 'sox: compressing dynamic range: ' + self.title)
            await sox_compress_dynamic_range(orig_audio, self.audio)

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
    async def make(url):
        soup = BeautifulSoup(await async_http_get(url), 'html.parser')
        title = soup.find('title').text
        date = soup.find('meta', property='video:release_date').get('content')
        # 2022-06-01T22:55:00+02:00
        date = datetime.strptime(date, '%Y-%m-%dT%H:%M:%S%z')
        return Episode(title, url, date)

    def __repr__(self):
        return f'<Episode title="{self.title}" url="{self.url}" date="{self.date}">'


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
        async for i, m in aupto(self.client.iter_messages(self.chat), limit):
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


async def fetch(url):
    episode = await Episode.make(url)
    logging.info('Found episode: %s', episode)
    async with TeleFile.open() as tele:
        if episode.name in await tele.recent():
            await ui_notify('NRKUP', 'Already available: ' + episode.name)
            return
        await tele.send(await episode.mp3())
        await ui_notify('NRKUP', 'Uploaded: ' + episode.name)


async def subtitles(url):
    episode = await Episode.make(url)
    logging.info('Found episode: %s', episode)
    return cleanup(episode.name + '\n' + episode.srt())


class HttpServer:
    def __init__(self, host, port, loop):
        self.host = host
        self.port = port
        self.loop = loop

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
            run_coroutine_threadsafe(fetch(url), self.loop)
            return web.Response(text='OK ' + url)
        except Exception as e:
            return web.Response(status=400, text=str(e))

    async def subtitles(self, request):
        url = request.query.get('url')
        if not url: return web.Response(status=400, text='Missing url')
        try:
            return web.Response(text=await subtitles(url))
        except Exception as e:
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


def test(url=None):
    url = 'https://tv.nrk.no/serie/distriktsnyheter-nordland/202206/DKNO99060122'
    disable_logging()
    loop = new_event_loop()
    host, port = HOST, PORT
    # loop.run_until_complete(fetch(url))
    loop.run_until_complete(HttpServer(host, port, loop).run())
    loop.run_forever()


def main():
    assert which('notify-send')
    assert which('ffmpeg')
    assert which('nrkdownload')
    assert which('sox')
    logging.info('hachoir version: %s', hachoir.__version__)
    load_env('~/.telegram')
    disable_logging()
    loop = new_event_loop()
    host, port = HOST, PORT
    loop.run_until_complete(HttpServer(host, port, loop).run())
    loop.run_forever()


if __name__ == '__main__':
    main()
