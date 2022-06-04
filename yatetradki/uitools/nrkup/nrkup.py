#!/usr/bin/env python3

from asyncio import new_event_loop
from datetime import datetime
from urllib.request import urlopen

from bs4 import BeautifulSoup
from yatetradki.tools.telegram import aupto
from yatetradki.tools.telegram import init_client
from yatetradki.utils import must_env


def http_get(url):
    with urlopen(url) as r:
        return r.read()


class Episode:
    def __init__(self, title, url, date):
        self.title = title
        self.url = url
        self.date = date

    @property
    def name(self):
        when = self.date.strftime('%Y%m%d')
        return f'nord-{when}.mp3'

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
                print(m.file.name)
            except AttributeError:
                pass
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


async def run(url):
    tele = await TeleFile.make()
    episode = Episode.make(url)
    if episode.name not in await tele.recent():
        # TODO: download, convert to mp3, move here, send, delete, notify
        # await tele.send(episode.name)
        await tele.send('test.mp3')
    # episode = Episode.make(url)
    # print(episode.name)
    await tele.close()
    print('done')


def test(url=None):
    url = 'https://tv.nrk.no/serie/distriktsnyheter-nordland/202206/DKNO99060122'
    loop = new_event_loop()
    loop.run_until_complete(run(url))


def main():
    url = 'https://tv.nrk.no/serie/distriktsnyheter-nordland/202206/DKNO99060122'
    loop = new_event_loop()
    loop.run_until_complete(run(url))


if __name__ == '__main__':
    main()
