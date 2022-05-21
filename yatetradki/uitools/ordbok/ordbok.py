#!/usr/bin/env python3

import sys
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer
from threading import Thread
from urllib.request import urlopen, Request

from aiohttp import web, ClientSession
from aiohttp_jinja2 import setup as aiohttp_jinja2_setup
from aiohttp_jinja2 import render_template as aiohttp_jinja2_render_template
from jinja2 import FileSystemLoader
from urllib3 import disable_warnings

USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'

def is_interactive():
    import __main__ as main
    return not hasattr(main, '__file__')

def http_post(url, data):
    with urlopen(url, data) as resp:
        return resp.read()

class WatchDog:
    class Server(HTTPServer):
        class RequestHandler(BaseHTTPRequestHandler):
            def __init__(self, request, client_address, server):
                BaseHTTPRequestHandler.__init__(self, request, client_address, server)
                self.server = server
            def do_POST(self):
                print('showing main window')
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'OK')
                self.server.on_show()
            def do_GET(self):
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'This is WatchDog endpoint. Use POST to show main window.\n')
        def __init__(self, host, port, on_show):
            HTTPServer.__init__(self, (host, port), WatchDog.Server.RequestHandler)
            self.host = host
            self.port = port
            self.on_show = on_show
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server = None
        self.thread = None
        self.on_show_callback = None
    def start(self):
        try:
            self.server = WatchDog.Server(self.host, self.port, self._call_on_show)
            self.thread = Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()
            return True
        except OSError:
            return False
    def show(self):
        print('Watchdog already running, showing previous instance')
        http_post(self.get_show_url(), b'')
    def get_show_url(self):
        return 'http://{0}:{1}/'.format(self.host, self.port)
    def _call_on_show(self):
        self.on_show_callback()
    def observe(self, on_show):
        self.on_show_callback = on_show


UI_HOST = 'localhost'
UI_PORT = 5660
WATCHDOG_HOST = 'localhost'
WATCHDOG_PORT = 5650
dog = WatchDog(WATCHDOG_HOST, WATCHDOG_PORT)
if (not is_interactive()) and (not dog.start()):
    dog.show()
    sys.exit()

import logging
import logging.handlers
import re
import bz2
from tempfile import gettempdir
from os import makedirs, environ
from os.path import dirname, exists, normpath, join, expanduser, expandvars
from urllib.parse import urlparse
from json import loads, dumps
from string import Template
from itertools import groupby
from pathlib import Path
from asyncio import new_event_loop, set_event_loop, gather, TimeoutError as AsyncioTimeoutError, run_coroutine_threadsafe
# # https://bugs.python.org/issue34679#msg347525
# policy = asyncio.get_event_loop_policy()
# policy._loop_factory = asyncio.SelectorEventLoop

import time
from functools import wraps
import socket

from requests import Session
from requests.exceptions import HTTPError, ReadTimeout, ConnectionError
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from pyppeteer import launch as launch_pyppeteer
from pyppeteer.errors import TimeoutError as PyppeteerTimeoutError
from playwright.sync_api import sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright
from playwright.async_api import TimeoutError as PlaywrightTimeoutErrorAsync

from PyQt5.QtWidgets import (QApplication, QComboBox, QVBoxLayout,
                             QWidget, QCompleter,
                             QSystemTrayIcon, QMenu, QAction)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from PyQt5.QtGui import QIcon, QFont, QClipboard
from PyQt5.QtCore import Qt, QTimer, QObject, QUrl
from PyQt5.QtCore import pyqtSignal, pyqtSlot

from yatetradki.reader.dsl import lookup as dsl_lookup
from yatetradki.uitools.index.search import search as index_search, INDEX_PATH
from yatetradki.tools.telegram import WordLogger

FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.DEBUG)


WINDOW_TITLE = 'Ordbok'
WINDOW_WIDTH = 1300
WINDOW_HEIGHT = 800
UPDATE_DELAY = 1000
ACTIVE_MODE_DELAY = 1000 # milliseconds
DIR = Path(dirname(__file__))
ICON_FILENAME = str(DIR / 'ordbok.png')
TEMPLATE_DIR = DIR / 'static' / 'html'
STATIC_DIR = DIR / 'static'
CACHE_DIR = Path(environ.get('CACHE_DIR', DIR / 'cache'))
CACHE_BY_METHOD = CACHE_DIR / 'by_method'
CACHE_BY_URL = CACHE_DIR / 'by_url'
ADD_TO_FONT_SIZE = 6
NETWORK_TIMEOUT = 5000 # milliseconds
NETWORK_RETRIES = 3
RECENT_GRAB_DELAY = (UPDATE_DELAY / 1000.0) + 0.1 # seconds
LOG_FILENAME = 'ordbok.log'

#POOL = ProcessPoolExecutor()

def force_ipv4():
    """
    https://ordbok.uib.no gets stuck when accessed by IPV6.
    Should be disbled when switched to https://ordbokene.no.
    """
    old_getaddrinfo = socket.getaddrinfo
    def new_getaddrinfo(*args, **kwargs):
        responses = old_getaddrinfo(*args, **kwargs)
        return [response
                for response in responses
                if response[0] == socket.AF_INET]
    socket.getaddrinfo = new_getaddrinfo

def disable_logging():
    disable_warnings()
    #print(logging.root.manager.loggerDict)
    blacklist = r'.*pyppeteer.*|.*urllib.*'
    for name in logging.root.manager.loggerDict:
        if re.match(blacklist, name) is not None:
            logger = logging.getLogger(name)
            logger.setLevel(logging.ERROR)
            logger.propagate = False
            #logging.info('Disabled logger "%s"', name)
    logging.getLogger('telethon').setLevel(logging.CRITICAL)


def in_temp_dir(filename) -> str:
    temp_dir = gettempdir()
    return join(temp_dir, filename)

def init_logger(filename: str):
    FORMAT = '%(asctime)-15s %(process)-5d %(levelname)-8s %(filename)s:%(lineno)d:%(funcName)s %(message)s'
    MAX_LOG_SIZE = 50 * 1024 * 1024
    LOG_BACKUP_COUNT = 1

    log = logging.getLogger()
    log.setLevel(logging.DEBUG)
    handler = logging.handlers.RotatingFileHandler(
        filename=filename,
        maxBytes=MAX_LOG_SIZE,
        backupCount=LOG_BACKUP_COUNT,
    )
    handler.setFormatter(logging.Formatter(FORMAT))
    log.addHandler(handler)
    log.info('Logger has been created')
    return log

async def http_get_async(url, timeout=None):
    USER_AGENT = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:100.0) Gecko/20100101 Firefox/100.0'
    headers = {'User-Agent': USER_AGENT}
    retries = NETWORK_RETRIES
    async with ClientSession() as session:
        for i in range(retries):
            try:
                async with session.get(url, timeout=timeout, headers=headers) as resp:
                    return await resp.text()
            except AsyncioTimeoutError as e:
                logging.warning('timeout (%s) getting "%s": "%s"', timeout, url, e)
                if i == retries-1:
                    raise

class StaticHttpClient:
    USER_AGENT = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:100.0) Gecko/20100101 Firefox/100.0'
    TIMEOUT = NETWORK_TIMEOUT/1000.0
    RETRIES = NETWORK_RETRIES
    def headers(self, origin=None):
        headers = {'User-Agent': self.USER_AGENT}
        if origin: headers['Origin'] = origin
        return headers
    async def get_async(self, url, origin=None):
        retries = self.RETRIES
        logging.info('http get async "%s"', url)
        async with ClientSession() as session:
            for i in range(retries):
                try:
                    async with session.get(url, timeout=self.TIMEOUT, headers=self.headers(origin), ssl=False, allow_redirects=True) as resp:
                        result = await resp.text()
                        logging.info('http get async done: "%s"', url)
                        return result
                except AsyncioTimeoutError as e:
                    logging.warning('async timeout (%s) getting "%s": "%s"', self.TIMEOUT, url, e)
                    if i == retries-1:
                        raise

class DynamicClient:
    TIMEOUT = NETWORK_TIMEOUT

class PlaywrightClientAsync(DynamicClient):
    async def get_async(self, url, selector=None, action=None):
        disable_logging()
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(url)
            if selector is not None:
                await page.wait_for_selector(selector, timeout=self.TIMEOUT)
            if action is not None:
                await page.evaluate(action)
            content = await page.evaluate('document.body.innerHTML')
            logging.info('async playwright "%d"', len(content))
            await browser.close()
            return content

class DynamicHttpClient:
    async def get_async(self, url, selector=None, action=None):
        return await PlaywrightClientAsync().get_async(url, selector, action)

def cache_get(basedir, keypath):
    path = join(basedir, *keypath)
    if not exists(path):
        logging.info('cache miss "%s"', keypath)
        return None
    logging.info('cache hit "%s"', keypath)
    return slurp(bz2.open, path)

def cache_set(basedir, keypath, value):
    path = join(basedir, *keypath)
    makedirs(dirname(path), exist_ok=True)
    spit(bz2.open, path, value)

def by_method_and_arg(f, *args, **kwargs):
    key = f.__name__.split('_')
    key.extend(args[1:])
    key.extend(kwargs.values())
    return key

def cached_async(f):
    @wraps(f)
    async def wrapper(*args, **kwargs):
        keypath = by_method_and_arg(f, *args, **kwargs)
        logging.info('async cache keypath "%s", args %s %s', keypath, args, kwargs)
        value = cache_get(CACHE_BY_METHOD, keypath)
        if value is None:
            value = await f(*args, **kwargs)
            cache_set(CACHE_BY_METHOD, keypath, value)
        return value
    return wrapper

class CachedHttpClient:
    def __init__(self, client, cachedir):
        self.client = client
        self.cachedir = cachedir
    async def get_async(self, url, **kwargs):
        path = self.get_path(self.get_key(url))
        content = slurp(bz2.open, path)
        if content is None:
            logging.info('cache miss: "%s"', url)
            content = await self.client.get_async(url, **kwargs)
            spit(bz2.open, path, content)
        return content
    def get_path(self, key):
        return join(self.cachedir, key)
    def get_key(self, url):
        J = lambda x: re.sub(r'\W+', '', x)
        S = lambda x: re.sub(r'^\w\s\d-', '/', x)
        p = urlparse(url)
        a = normpath('/'.join([J(p.hostname), J(p.path), J(p.query)]))
        b = normpath('/'.join([J(p.hostname), S(p.path)]))
        return a if p.query else b

class NoContent(Exception):
    pass

def slurp_lines(do_open, filename):
    result = slurp(do_open, filename)
    if result:
        return [x.strip() for x in result.splitlines()]

def slurp(do_open, filename):
    filename = expanduser(expandvars(filename))
    try:
        with do_open(filename, 'rb') as file_:
            return file_.read().decode()
    except:
        return None

def spit(do_open, filename, content):
    filename = expanduser(expandvars(filename))
    dir = dirname(filename)
    if not exists(dir):
        makedirs(dir)
    with do_open(filename, 'wb') as file_:
        file_.write(content.encode())

def to_text(html):
    return parse(html).text

def uniq(items, key):
    seen = set()
    return [x for x in items if not (key(x) in seen or seen.add(key(x)))]

def no_content():
    return '<body>No content</body>'

def extract(source, soup, *args):
    result = soup.find(*args)
    if result: return result.prettify()
    raise NoContent('{0}: {1}'.format(source, args))

def remove_one(soup, selector):
    target = soup.select_one(selector)
    if target: target.decompose()
    return soup

def remove_all(soup, selector):
    target = soup.select(selector)
    for tag in target:
        tag.decompose()
    return soup

def parse(body):
    t0 = time.time()
    result = BeautifulSoup(body, features='html.parser')
    #result = BeautifulSoup(body, features='lxml')
    t1 = time.time()
    logging.info('parse: %.2f (size=%d)', t1-t0, len(body))
    return result

def iframe_mix(word):
    t = Template(open(here_html('iframe-mix.html')).read())
    return t.substitute(word=word)

def iframe_nor(word):
    t = Template(open(here_html('iframe-nor.html')).read())
    return t.substitute(word=word)

def iframe_third(word):
    t = Template(open(here_html('iframe-third.html')).read())
    return t.substitute(word=word)

def iframe_fourth(word):
    t = Template(open(here_html('iframe-fourth.html')).read())
    return t.substitute(word=word)

def iframe_q(word):
    t = Template(open(here_html('iframe-q.html')).read())
    return t.substitute(word=word)

def iframe_w(word):
    t = Template(open(here_html('iframe-w.html')).read())
    return t.substitute(word=word)

def iframe_e(word):
    t = Template(open(here_html('iframe-e.html')).read())
    return t.substitute(word=word)

def iframe_r(word):
    t = Template(open(here_html('iframe-r.html')).read())
    return t.substitute(word=word)

def iframe_h(word):
    t = Template(open(here_html('iframe-h.html')).read())
    return t.substitute(word=word)

def ui_mix_url(word):
    return 'http://{0}:{1}/ui/mix/{2}'.format(UI_HOST, UI_PORT, word)

def ui_nor_url(word):
    return 'http://{0}:{1}/ui/nor/{2}'.format(UI_HOST, UI_PORT, word)

def ui_third_url(word):
    return 'http://{0}:{1}/ui/third/{2}'.format(UI_HOST, UI_PORT, word)

def ui_fourth_url(word):
    return 'http://{0}:{1}/ui/fourth/{2}'.format(UI_HOST, UI_PORT, word)

def ui_q_url(word):
    return 'http://{0}:{1}/ui/q/{2}'.format(UI_HOST, UI_PORT, word)

def ui_w_url(word):
    return 'http://{0}:{1}/ui/w/{2}'.format(UI_HOST, UI_PORT, word)

def ui_e_url(word):
    return 'http://{0}:{1}/ui/e/{2}'.format(UI_HOST, UI_PORT, word)

def ui_r_url(word):
    return 'http://{0}:{1}/ui/r/{2}'.format(UI_HOST, UI_PORT, word)

def ui_h_url(word):
    return 'http://{0}:{1}/ui/h/{2}'.format(UI_HOST, UI_PORT, word)

def ui_aulismedia_norsk(word):
    return 'http://{0}:{1}/aulismedia/norsk/{2}'.format(UI_HOST, UI_PORT, word)

def ui_aulismedia_search_norsk(word):
    return 'http://{0}:{1}/aulismedia/search_norsk/{2}'.format(UI_HOST, UI_PORT, word)

def css(filename):
    return '<style>{0}</style>'.format(slurp(open, here_css(filename)))

def here(name):
    return join(DIR, name)

def here_js(name):
    return join(DIR, 'static/js', name)

def here_css(name):
    return join(DIR, 'static/css', name)

def here_html(name):
    return join(DIR, 'static/html', name)

def pretty(html):
    return parse(html).prettify()

class WordGetter:
    def __init__(self, client, word):
        self.client = client
        self.word = word

class LexinOsloMetArticle(WordGetter):
    # curl -k
    # 'https://editorportal.oslomet.no/api/v1/findwords?searchWord=gift&lang=bokm%C3%A5l-russisk&page=1&selectLang=bokm%C3%A5l-russisk'
    # -H 'Origin: https://lexin.oslomet.no'
    # {
    #   "id": 1523,
    #   "sub_id": 2,
    #   "type": "E-lem",
    #   "text": "gift"
    # },
    # "resArray": {
    #      "0": {
    #          "id": 1168
    #      },
    ORIGIN = 'https://lexin.oslomet.no'
    async def get_async(self):
        soup = loads(await self.client.get_async(self.get_url(self.word), origin=self.ORIGIN))
        self.html = self.transform(soup)
        return self.styled()
    def order(self, soup):
        items = soup['resArray']
        if isinstance(items, dict):
            order1 = sorted(items.items(), key=lambda x: int(x[0]))
            order2 = [x[1]['id'] for x in order1]
            return order2
        elif isinstance(items, list):
            order1 = [x['id'] for x in items]
            return order1
        raise RuntimeError('unexpected type: %s' % items)
    def transform(self, soup):
        #items = [x['text'] for x in soup['result'][0]]
        order = self.order(soup)
        items = soup['result'][0]
        group_map = {k: list(g) for k, g in groupby(items, lambda x: x['id'])}
        groups = [group_map[b] for b in order if b in group_map]
        blocks = []
        for group in groups:
            blocks.append(self.paint(group))
        if not blocks:
            raise NoContent('LexinOsloMetArticle: "{0}"'.format(self.word))
        #return '<br>\n<br>\n'.join(blocks)
        return '<br>\n'.join(blocks)
    def paint(self, group):
        lems, group = pluck('.*-lem$', group)
        #lems = ', '.join(text(lems))
        kats, group = pluck('.*-kat$', group)
        defs, group = pluck('.*-def$', group)
        eks, group = pluck('.*-eks$', group)
        sms, group = pluck('.*-sms', group)
        idi, group = pluck('.*-idi', group)
        _, group = pluck('.*-div$', group) # something with bilde(127, ...)
        _, group = pluck('.*-kom$', group)
        mor, group = pluck('.*-mor$', group)
        _, group = pluck('.*-utt$', group)
        _, group = pluck('.*-alt', group)

        # N, E
        # B
        # Ru
        lines = []
        lines.append(span('lem', notilda(comma(text(lems)))) + ' ' + span('kat', notilda(comma(text(kats)))))
        lines.append(divs('def', combine(defs)))
        lines.append(divs('eks', combine(eks)))
        #lines.append(divs('sms', text(sms)))
        lines.append(divs('sms', combine(sms)))
        lines.append(divs('idi', combine(idi)))
        lines.append(divs('mor', combine(mor)))
        lines.append(''.join(unknown(x) for x in group))
        #lines.append('<br>'.join(unknown(x) for x in group))
        #lines.append(div('columns2', divs('sms', text(sms))))
        return ''.join(lines)
    def styled(self):
        return self.style() + self.html
    def get_url(self, word):
        return 'https://editorportal.oslomet.no/api/v1/findwords?searchWord={0}&lang=bokm%C3%A5l-russisk&page=1&selectLang=bokm%C3%A5l-russisk'.format(word)
    def style(self):
        return css('lexin-style.css')

# class Suggestions:
#     # https://ordbok.uib.no/perl/lage_ordliste_liten_nr2000.cgi?spr=bokmaal&query=gam
#     #
#     # {query:'gam',
#     # suggestions:["gaman","gamasje","gambe","gambier","gambisk","gambit","gamble","gambler","game","game","gamet","gametofytt","gamla","gamle-","gamleby","gamlefar","gamleheim","gamlehjem","gamlekjжreste","gamlemor","gamlen","gamlestev","gamletid","gamleеr","gamling","gamma","gammaglobulin","gammal","gammaldags","gammaldans","gammaldansk","gammaldansk","gammalengelsk","gammalgresk","gammalkjent","gammalkjжreste","gammalkommunist","gammalmannsaktig","gammalmodig","gammalnorsk","gammalnorsk","gammalost","gammalrosa","gammalstev","gammaltestamentlig","gammaltid","gammalvoren","gammastrеle","gammastrеling","gamme","gammel","gammel jomfru","gammel norsk mil","gammel som alle haugene","gammeldags","gammeldans","gammeldansk","gammeldansk","gammelengelsk","gammelgresk","gammelkjent","gammelkjжreste","gammelkommunist","gammelmannsaktig","gammelmodig","gammelnorsk","gammelnorsk","gammelost","gammelrosa","gammelstev","gammeltestamentlig","gammeltid","gammelvoren","gammen","gamp","gampe"],
#     # data:["gaman","gamasje","gambe","gambier","gambisk","gambit","gamble","gambler","game","game","gamet","gametofytt","gamla","gamle-","gamleby","gamlefar","gamleheim","gamlehjem","gamlekjжreste","gamlemor","gamlen","gamlestev","gamletid","gamleеr","gamling","gamma","gammaglobulin","gammal","gammaldags","gammaldans","gammaldansk","gammaldansk","gammalengelsk","gammalgresk","gammalkjent","gammalkjжreste","gammalkommunist","gammalmannsaktig","gammalmodig","gammalnorsk","gammalnorsk","gammalost","gammalrosa","gammalstev","gammaltestamentlig","gammaltid","gammalvoren","gammastrеle","gammastrеling","gamme","gammel","gammel jomfru","gammel norsk mil","gammel som alle haugene","gammeldags","gammeldans","gammeldansk","gammeldansk","gammelengelsk","gammelgresk","gammelkjent","gammelkjжreste","gammelkommunist","gammelmannsaktig","gammelmodig","gammelnorsk","gammelnorsk","gammelost","gammelrosa","gammelstev","gammeltestamentlig","gammeltid","gammelvoren","gammen","gamp","gampe"]
#     # }
#     TOP_COUNT = 5
#     def __init__(self, client, word):
#         self.word = word
#         items = loads(self.cleanup(client.get(self.get_url(word)))).get('suggestions', [])
#         self.items = uniq(items, lambda s: s.lower())
#         self.top = self.items[:Suggestions.TOP_COUNT]
#
#     def cleanup(self, text):
#         text = '{}'[:1] + '\n' + text[text.index('\n')+1:]
#         #a = text.replace("'", '"')
#         # :2 because of the syntax parser in neovim plugin, if I leave one
#         # bracket open, it will incorrectly detect indentation
#         a = text
#         #a = re.sub('^{}'[:2] + 'query', '{"query"}', a)
#         a = re.sub('^suggestions', '"suggestions"', a, flags=re.MULTILINE)
#         a = re.sub('^data', '"data"', a, flags=re.MULTILINE)
#         return a
#
#     def get_url(self, query):
#         return 'https://ordbok.uib.no/perl/lage_ordliste_liten_nr2000.cgi?spr=bokmaal&query={0}'.format(query)
#
#     def __repr__(self):
#         return f'Suggestions(word={self.word}, count={len(self.items)}, top={self.top})'

class NaobWord(WordGetter):
    async def get_async(self):
        soup = parse(await self.client.get_async(self.get_url(self.word), selector='main > div.container'))
        self.parse(soup)
        return self.styled()
    def parse(self, soup):
        article = soup.select_one('div.article')
        container = soup.select_one('main > div.container')
        main = container.parent
        main = remove_one(main, '.vipps-box')
        main = remove_one(main, '.prompt')
        if article:
            self.html = extract('NaobWord', main, 'div', {'class': 'article'})
        elif container.select_one('div.list-item'):
            self.html = extract('NoabWord', main, 'div', {'class': 'container'})
        else:
            raise NoContent('NaobWord: word="{0}"'.format(self.word))
    def styled(self):
        return self.style() + self.html
    def style(self):
        return css('naob-style.css')
    def get_url(self, word):
        return 'https://naob.no/ordbok/{0}'.format(word)

class OrdbokeneWord(WordGetter):
    # https://ordbokene.no/bm/search?q=mor&scope=ei
    async def get_async(self):
        action = "for (let x of document.querySelectorAll('button.show-inflection')) x.click()"
        selector = 'div.hits, div.no_results'
        soup = parse(await self.client.get_async(self.get_url(self.word), selector=selector, action=action))
        self.parse(soup)
        return self.styled()
    def parse(self, soup):
        no_results = soup.select_one('div.no_results')
        if no_results:
            raise NoContent('OrdbokeneWord: word="{0}"\n\n{1}'.format(self.word, no_results.prettify()))
        soup = remove_all(soup, 'div.dict-label-top')
        soup = remove_all(soup, 'div.article_footer')
        soup = remove_all(soup, 'span.inflection-wrapper')
        main = extract('OrdbokeneWord', soup, 'div', {'class': 'hits'})
        self.html = main
    def styled(self):
        return self.style() + self.html
    def style(self):
        return css('ordbokene-word.css')
    def get_url(self, word):
        return 'https://ordbokene.no/bm/search?q={0}&scope=ei'.format(word)

class OrdbokeneInflect(OrdbokeneWord):
    def parse(self, soup):
        no_results = soup.select_one('div.no_results')
        if no_results:
            raise NoContent('OrdbokeneWord: word="{0}"\n\n{1}'.format(self.word, no_results.prettify()))
        soup = remove_all(soup, 'button')
        parts = []
        for tag in soup.select('span.inflection-wrapper'):
            parts.append(tag.prettify())
        self.html = '\n'.join(parts)

class Inflection(WordGetter):
    # https://ordbok.uib.no/perl/bob_hente_paradigme.cgi?lid=41772
    #  <div id="41772"><table class="paradigmetabell" cellspacing="0" style="margin: 25px;"><tr><th class="nobgnola"><span class="grunnord">liv</span></th><th class="nola" colspan="2">Entall</th><th class="nola" colspan="2">Flertall</th></tr><tr><th class="nobg">&nbsp;&nbsp;</th><th>Ubestemt form</th><th>Bestemt form</th><th>Ubestemt form</th><th>Bestemt form</th></tr><tr id="41772_1"><td class="ledetekst">n1</td><td class="vanlig">et liv</td><td class="vanlig">livet</td><td class="vanlig">liv</td><td class="vanlig">liva</td></tr><tr id="41772_2"><td class="ledetekst">n1</td><td class="vanlig">et liv</td><td class="vanlig">livet</td><td class="vanlig">liv</td><td class="vanlig">livene</td></tr></table></div>
    async def get_async(self):
        self.html = self.cleanup(await self.client.get_async(self.get_url(self.word)))
    def cleanup(self, text):
        return re.sub(r'style="margin:[^"]*"', 'style="margin: 3px;"', text)
    def get_url(self, lid):
        return 'https://ordbok.uib.no/perl/bob_hente_paradigme.cgi?lid={0}'.format(lid)
    def __repr__(self):
        return f'Inflection(lid={self.word})'

class PartOfSpeech:
    # <span class="oppsgramordklasse" onclick="vise_fullformer(&quot;8225&quot;,'bob')">adj.</span>
    def __init__(self, client, soup):
        self.client = client
        self.soup = soup
    async def get_async(self):
        await self.parse_async(self.soup)
    def parse(self, soup):
        self.name = soup.text
        self.lid = None
        self.inflection = None
        m = re.search(r'\d+', soup['onclick'])
        if m:
            self.lid = m.group(0)
            self.inflection = Inflection(self.client, self.lid)
            self.inflection.get()
    async def parse_async(self, soup):
        self.name = soup.text
        self.lid = None
        self.inflection = None
        m = re.search(r'\d+', soup['onclick'])
        if m:
            self.lid = m.group(0)
            self.inflection = Inflection(self.client, self.lid)
            await self.inflection.get_async()
    def __repr__(self):
        return f'PartOfSpeech(name="{self.name}", lid={self.lid}, inflection={self.inflection})'

class OrdbokInflect(WordGetter):
    # https://ordbok.uib.no/perl/ordbok.cgi?OPP=bra&ant_bokmaal=5&ant_nynorsk=5&bokmaal=+&ordbok=bokmaal
    # <span class="oppslagsord b" id="22720">gi</span>
    # <span class="oppsgramordklasse" onclick="vise_fullformer(&quot;8225&quot;,'bob')">adj.</span>
    async def get_async(self):
        soup = parse(await self.client.get_async(self.get_url(self.word)))
        args = ('span', {"class": "oppsgramordklasse"})
        parts = soup.find_all(*args)
        if not parts:
            raise NoContent('OrdbokInflect: word="{0}", args={1}'.format(self.word, args))
        parts = [PartOfSpeech(self.client, p) for p in parts]
        [await p.get_async() for p in parts]
        self.parts = [p for p in parts if p.inflection]
        self.parse()
        return self.styled()
    def parse(self):
        self.html = ''.join(uniq([p.inflection.html for p in self.parts], to_text))
    def styled(self):
        return self.style() + self.html
    def style(self):
        return css('ordbok-inflect.css')
    def get_url(self, word: str) -> str:
        return 'https://ordbok.uib.no/perl/ordbok.cgi?OPP={0}&ant_bokmaal=5&ant_nynorsk=5&bokmaal=+&ordbok=bokmaal'.format(word)
    def __repr__(self):
        return f'OrdbokInflect(word={self.word}, parts={self.parts})'

class OrdbokWord(WordGetter):
    async def get_async(self):
        soup = parse(await self.client.get_async(self.get_url(self.word)))
        self.parse(soup)
        return self.styled()
    def parse(self, soup):
        self.html = extract('OrdbokWord', soup, 'table', {'id': 'byttutBM'})
    def styled(self):
        return self.style() + self.html
    def style(self):
        return css('ordbok-word.css')
    def get_url(self, word):
        return 'https://ordbok.uib.no/perl/ordbok.cgi?OPP={0}&ant_bokmaal=5&ant_nynorsk=5&bokmaal=+&ordbok=begge'.format(word)

class GlosbeWord(WordGetter):
    async def get_async(self):
        soup = parse(await self.client.get_async(self.get_url(self.word)))
        self.parse(soup)
        return self.styled()
    def parse(self, soup):
        self.html = extract('GlosbeWord', soup, 'div', {'id': 'dictionary-content'})
    def styled(self):
        return self.style() + self.html
    def get_url(self, word):
        pass
        #raise NotImplemented
    def style(self):
        return css('glosbe-style.css')

class GlosbeNoRuWord(GlosbeWord):
    def get_url(self, word):
        nbru = 'https://nb.glosbe.com/nb/ru/{0}'
        runb = 'https://nb.glosbe.com/ru/nb/{0}'
        url = runb if re.search(r'[\u0400-\u04FF]', word) is not None else nbru
        return url.format(word)

class GlosbeNoEnWord(GlosbeWord):
    def get_url(self, word):
        return 'https://nb.glosbe.com/nb/en/{0}'.format(word)

class GlosbeEnNoWord(GlosbeWord):
    def get_url(self, word):
        return 'https://nb.glosbe.com/en/nb/{0}'.format(word)

class WiktionaryNo(WordGetter):
    async def get_async(self):
        soup = parse(await self.client.get_async(self.get_url(self.word)))
        self.parse(soup)
        return self.styled()
    def parse(self, soup):
        self.html = extract('WiktionaryNo', soup, 'div', {'class': 'mw-parser-output'})
    def styled(self):
        return self.style() + self.html
    def style(self):
        return css('wiktionary-style.css')
    def get_url(self, word):
        return 'https://no.wiktionary.org/wiki/{0}'.format(word)

class CambridgeEnNo(WordGetter):
    async def get_async(self):
        soup = parse(await self.client.get_async(self.get_url(self.word)))
        self.parse(soup)
        return self.styled()
    def parse(self, soup):
        self.html = extract('CambridgeEnNo', soup, 'div', {'class': 'dictionary'})
    def styled(self):
        return self.style() + self.html
    def style(self):
        return css('cambridge-style.css')
    def get_url(self, word):
        return 'https://dictionary.cambridge.org/dictionary/english-norwegian/{0}'.format(word)

class DslWord(WordGetter):
    FILENAME = '~/.ordbok.dsl.txt'
    async def get_async(self):
        self.parse()
        return self.styled()
    def parse(self):
        # TODO: is file is empty or missing, show a hint on what to put there and where
        dsls = slurp_lines(open, self.FILENAME)
        self.word = self.word
        if not dsls:
            raise NoContent(self.no_dictionary())
        self.html = dsl_lookup(dsls, [self.word])
        if not self.html:
            raise NoContent('DslWord: "{0}"'.format(self.word))
    def no_dictionary(self):
        return 'DslWord: No dictionaries found. Put full filename paths to DSL ' \
            'dictionaries into {0}, one filename per line'.format(self.FILENAME)
    def styled(self):
        return self.style() + self.html
    def style(self):
        return '' # css('wiktionary-style.css')
    # def get_url(self, word):
    #     return 'https://no.wiktionary.org/wiki/{0}'.format(word)

class GoogleTranslate(WordGetter):
    FROM = 'NA'
    TO = 'NA'
    async def get_async(self):
        soup = parse(await self.client.get_async(self.get_url(self.word, self.FROM, self.TO)))
        self.parse(soup)
        return self.styled()
    def parse(self, soup):
        self.html = extract('GoogleTranslate', soup, 'div', {'class': 'result-container'})
    def styled(self):
        return self.style() + self.html
    def style(self):
        return '' #css('wiktionary-style.css')
    def get_url(self, word, src, dest):
        return 'https://translate.google.com/m?hl=en&sl={0}&tl={1}&prev=_m&q={2}'.format(src, dest, word)

class GoogleTranslateNoEn(GoogleTranslate):
    FROM = 'no'
    TO = 'en'

class GoogleTranslateEnNo(GoogleTranslate):
    FROM = 'en'
    TO = 'no'

class AulismediaWord(WordGetter):
    # {"lastpage": 1470,"firstpage": 1,"page": 14,"direction": "nor","term": "al"}
    async def get_async(self):
        soup = loads(await self.client.get_async(self.get_url(self.word)))
        self.parse(soup)
        return self.styled()
    def parse(self, soup):
        page = '{}{:04d}.jpg'.format(soup['direction'], soup['page'])
        self.html = Template(open(here_html('aulismedia-norsk.html')).read()).substitute(word=page)
    def styled(self):
        return self.style() + self.html
    def style(self):
        return '' # css('aulismedia-style.css')
    def get_url(self, word):
        return ui_aulismedia_search_norsk(word)
        # return 'http://norsk.dicts.aulismedia.com/processnorsk.php?search={0}'.format(word)
    @staticmethod
    def flip(word, increment):
        index = int(''.join(filter(lambda x: x.isdigit(), word))) + increment
        url = ui_aulismedia_norsk('{:04d}.jpg'.format(index))
        return url

def pluck(regexp, group):
    yes, no = [], []
    for x in group:
        if re.match(regexp, x['type']) is not None:
            yes.append(x)
        else:
            no.append(x)
    return yes, no

def text(group):
    return [x['text'] for x in group]

def comma(items):
    return sjoin(', ', items)

def equals(items):
    return sjoin(' = ', items)

def tabbed(items):
    return sjoin('\t', items)

def sjoin(separator, items):
    return separator.join(items)

def div(klass, line):
    return '<div class="{0}">{1}</div>'.format(klass, line)

def divs(klass, lines):
    return ''.join(div(klass, x) for x in lines)

def span(klass, line):
    return '<span class="{0}">{1}</span>'.format(klass, line)

def spans(klass, lines):
    return ''.join(span(klass, x) for x in lines)

def notilda(line):
    return line.replace('~', '')

def unknown(group_item):
    return '{0}={1}'.format(group_item['type'], group_item['text'])

def combine(group):
    def first(line):
        return line.startswith('N-') or line.startswith('E-')
    counter = [0]
    def key(group_item):
        if first(group_item['type']): counter[0] += 1
        return counter[0]
    lines = []
    for k, g in groupby(group, key=key):
        lines.append(notilda(equals(text(g))))
    return lines

class QComboBoxKey(QComboBox):
    def __init__(self, parent, on_key_press):
        super(QComboBoxKey, self).__init__(parent)
        self.on_key_press = on_key_press
    def keyPressEvent(self, e):
        if not self.on_key_press(e):
            super(QComboBoxKey, self).keyPressEvent(e)

class WebEnginePage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        logging.info("js console: %s %s %s %s", level, message, lineNumber, sourceID)

class Browsers:
    def __init__(self, parent, layout, num):
        self.browsers = [QWebEngineView(parent) for _ in range(num)]
        [b.setPage(WebEnginePage(b)) for b in self.browsers]
        self.current = 0
        self.layout = layout
    def load(self, urls):
        for url, browser in zip(urls, self.browsers):
            browser.load(QUrl(url))
    def show(self, index):
        for i, browser in enumerate(self.browsers):
            if i == index:
                self.layout.addWidget(browser)
                browser.show()
            else:
                self.layout.removeWidget(browser)
                browser.hide()
    def zoom(self, factor):
        for browser in self.browsers:
            browser.setZoomFactor(factor)
    def scan_shortcut(self, e):
        if (e.key() == Qt.Key_Exclam) and (e.modifiers() == Qt.AltModifier): # and (e.type == QEvent.KeyPress):
            return 0
        if (e.key() == Qt.Key_At) and (e.modifiers() == Qt.AltModifier): # and (e.type == QEvent.KeyPress):
            return 1
        if (e.key() == Qt.Key_NumberSign) and (e.modifiers() == Qt.AltModifier): # and (e.type == QEvent.KeyPress):
            return 2
        if (e.key() == Qt.Key_Dollar) and (e.modifiers() == Qt.AltModifier): # and (e.type == QEvent.KeyPress):
            return 3
        if (e.key() == Qt.Key_Q) and (e.modifiers() == Qt.AltModifier): # and (e.type == QEvent.KeyPress):
            return 4
        if (e.key() == Qt.Key_W) and (e.modifiers() == Qt.AltModifier): # and (e.type == QEvent.KeyPress):
            return 5
        if (e.key() == Qt.Key_F) and (e.modifiers() == Qt.AltModifier): # and (e.type == QEvent.KeyPress):
            return 6
        if (e.key() == Qt.Key_P) and (e.modifiers() == Qt.AltModifier): # and (e.type == QEvent.KeyPress):
            return 7
        if (e.key() == Qt.Key_H) and (e.modifiers() == Qt.AltModifier): # and (e.type == QEvent.KeyPress):
            return 8
        return None
    def on_key_press(self, e):
        index = self.scan_shortcut(e)
        if index is None:
            return False
        self.show(index)
        return True

class MainWindow(QWidget):
    ZOOM = 1.7
    MAX_WORDS_IN_CLIPBOARD = 5
    myActivate = pyqtSignal()
    myTranslate = pyqtSignal(str)
    def __init__(self, app):
        super().__init__()
        self.myActivate.connect(self.activate)
        self.app = app

        mainLayout = QVBoxLayout(self)
        mainLayout.setSpacing(0)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(mainLayout)
        self.main_layout = mainLayout

        self.browsers = Browsers(self, mainLayout, 9)
        self.browsers.zoom(self.ZOOM)

        self.comboBox = QComboBoxKey(self, self.browsers.on_key_press)
        self.comboBox.setEditable(True)
        self.comboBox.setCurrentText('')
        self.comboBox.setCompleter(None)
        self.comboBox.currentTextChanged.connect(self.on_text_changed)
        self.comboBox.installEventFilter(self)

        font = QFont()
        font.setPointSize(font.pointSize() + ADD_TO_FONT_SIZE)
        self.comboBox.setFont(font)

        self.set_text('hund')
        mainLayout.addWidget(self.comboBox)
        self.browsers.show(0)

        self.setWindowTitle(WINDOW_TITLE)
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setWindowIcon(QIcon(ICON_FILENAME))

        QTimer.singleShot(1, self.center)
        self.active_mode = False
        QTimer.singleShot(ACTIVE_MODE_DELAY, self.on_active_mode)
        self.last_manual_change = time.time()

        self.center()
        self.show()

    def show_browser(self, index):
        self.browser.show(index)

    def toggle_active_mode(self):
        self.active_mode = not self.active_mode
        if self.active_mode:
            self.setWindowTitle(WINDOW_TITLE + ' | A')
        else:
            self.setWindowTitle(WINDOW_TITLE)

    def focused(self):
        return QApplication.activeWindow() == self

    def on_active_mode(self):
        if self.active_mode and not self.focused():
            self.grab(QApplication.clipboard().text(QClipboard.Selection))
        QTimer.singleShot(ACTIVE_MODE_DELAY, self.on_active_mode)

    def short(self, content):
        return content and (len(content.split()) <= self.MAX_WORDS_IN_CLIPBOARD)

    def grab(self, content):
        self.last_manual_change = time.time()
        if self.short(content) and not self.same_text(content):
            self.set_text(content)
            return True
        return False

    def recent_manual_change(self):
        return (time.time() - self.last_manual_change) < RECENT_GRAB_DELAY

    def grab_clipboard(self):
        self.grab(QApplication.clipboard().text(QClipboard.Selection)) or \
            self.grab(QApplication.clipboard().text())

    def unminimize(self):
        if self.windowState() == Qt.WindowMinimized:
            self.setWindowState(Qt.WindowNoState)

    def activate(self):
        self.grab_clipboard()
        self.center()
        self.unminimize()
        self.raise_()
        self.show()
        self.activateWindow()
        self.comboBox.lineEdit().selectAll()
        self.comboBox.setFocus()

    def center(self):
        qr = self.frameGeometry()
        desktop = QApplication.desktop()
        screen = desktop.screenNumber(desktop.cursor().pos())
        cp = desktop.screenGeometry(screen).center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def suggest(self, words):
        completer = QCompleter(words, self)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.comboBox.setCompleter(completer)
        completer.complete()

    def set_text(self, text):
        logging.info('Setting text: %s', text)
        self.myTranslate.emit(text)
        self.comboBox.setCurrentText(text)
        urls = [ui_mix_url(text),
                ui_nor_url(text),
                ui_third_url(text),
                ui_fourth_url(text),
                ui_q_url(text),
                ui_w_url(text),
                ui_e_url(text),
                ui_r_url(text),
                ui_h_url(text),
               ]
        self.browsers.load(urls)

    def on_text_changed(self, text):
        if text == '':
            return
        QTimer.singleShot(UPDATE_DELAY, lambda: self.update(text))

    def update(self, old_text):
        if self.recent_manual_change():
            return
        if self.same_text(old_text):
            self.set_text(old_text)

    def onTrayActivated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.show()

    def same_text(self, word):
        return word == self.text()

    def text(self):
        return self.comboBox.currentText()

    # def eventFilter(self, obj, e):
    #     if isinstance(e, QKeyEvent):
    #         if e.key() == Qt.Key_Exclam and e.type == QEvent.KeyPress:
    #             return True
    #         elif e.key() == Qt.Key_At and e.type == QEvent.KeyPress:
    #             return True
    #     return super(MainWindow, self).eventFilter(obj, e)

    def keyPressEvent(self, e):
        if self.browsers.on_key_press(e):
            return
        if e.key() == Qt.Key_Escape:
            self.hide()
        elif (e.key() == Qt.Key_Q) and (e.modifiers() == Qt.ControlModifier):
            self.close()
        elif (e.key() == Qt.Key_L) and (e.modifiers() == Qt.ControlModifier):
            self.comboBox.lineEdit().selectAll()
            self.comboBox.setFocus()
        elif (e.key() == Qt.Key_W) and (e.modifiers() == Qt.ControlModifier):
            self.toggle_active_mode()
        elif e.key() == Qt.Key_Return:
            self.last_manual_change = time.time()
            self.set_text(self.text())
        else:
            logging.info('key event: %s, %s', e.key(), e.modifiers())

async def timed_http_get_async(url):
    logging.info('timed html: %s', url)
    t0 = time.time()
    await http_get_async(url)
    t1 = time.time()
    return t1 - t0

def text_html(text):
    return web.Response(text=text, content_type='text/html')

def text_css(text):
    return web.Response(text=text, content_type='text/css')

class AIOHTTPUIServer:
    def __init__(self, static_client, dynamic_client, host, port):
        self.static_client = static_client
        self.dynamic_client = dynamic_client
        self.host = host
        self.port = port
        self.app = web.Application(middlewares=[self.error_middleware, self.stats_middleware])
        aiohttp_jinja2_setup(self.app, loader=FileSystemLoader(TEMPLATE_DIR))
        self.setup_routes(self.app)
        # https://docs.aiohttp.org/en/stable/web_advanced.html#application-runners
        self.runner = web.AppRunner(self.app)
        self.stats = TimingStats()
    def url(self, path):
        return 'http://{}:{}{}'.format(self.host, self.port, path)
    def serve_background(self):
        Thread(target=self.serve, daemon=True).start()
    def serve(self):
        logging.info('Starting AIOHTTPUIServer on %s:%s', self.host, self.port)
        loop = new_event_loop()
        set_event_loop(loop)
        loop.run_until_complete(self.runner.setup())
        site = web.TCPSite(self.runner, self.host, self.port)
        loop.run_until_complete(site.start())
        loop.run_forever()
    @web.middleware
    async def stats_middleware(self, request, handler):
        t0 = time.time()
        response = await handler(request)
        total = time.time() - t0
        self.stats.set(request.rel_url.path, total)
        return response
    @web.middleware
    async def error_middleware(self, request, handler):
        try:
            response = await handler(request)
            return response
        except (
            HTTPError,
            ReadTimeout,
            ConnectionError,
            PyppeteerTimeoutError,
            PlaywrightTimeoutError,
            PlaywrightTimeoutErrorAsync,
            AsyncioTimeoutError,
            NoContent,
        ) as e:
            return text_html('{0}: {1}'.format(type(e).__name__, e))
    def setup_routes(self, app):
        def wrap(fn):
            async def handler(request):
                word = request.match_info.get('word')
                result = await fn(word)
                if isinstance(result, str):
                    return text_html(result)
                if isinstance(result, web.HTTPException):
                    return result
                return web.json_response(result)
            return handler
        router = app.router
        router.add_get('/static/css/iframe.css', self.route_iframe_css)
        router.add_get('/ui/mix/{word}', wrap(self.route_ui_mix))
        router.add_get('/ui/nor/{word}', wrap(self.route_ui_nor))
        router.add_get('/ui/third/{word}', wrap(self.route_ui_third))
        router.add_get('/ui/fourth/{word}', wrap(self.route_ui_fourth))
        router.add_get('/ui/q/{word}', wrap(self.route_ui_q))
        router.add_get('/ui/w/{word}', wrap(self.route_ui_w))
        router.add_get('/ui/e/{word}', wrap(self.route_ui_e))
        router.add_get('/ui/r/{word}', wrap(self.route_ui_r))
        router.add_get('/ui/h/{word}', wrap(self.route_ui_h))
        router.add_get('/lexin/word/{word}', wrap(self.route_lexin_word))
        router.add_get('/ordbok/inflect/{word}', wrap(self.route_ordbok_inflect))
        router.add_get('/ordbok/word/{word}', wrap(self.route_ordbok_word))
        router.add_get('/ordbokene/word/{word}', wrap(self.route_ordbokene_word))
        router.add_get('/ordbokene/inflect/{word}', wrap(self.route_ordbokene_inflect))
        router.add_get('/naob/word/{word}', wrap(self.route_naob_word))
        router.add_get('/glosbe/noru/{word}', wrap(self.route_glosbe_noru))
        router.add_get('/glosbe/noen/{word}', wrap(self.route_glosbe_noen))
        router.add_get('/glosbe/enno/{word}', wrap(self.route_glosbe_enno))
        router.add_get('/wiktionary/no/{word}', wrap(self.route_wiktionary_no))
        router.add_get('/cambridge/enno/{word}', wrap(self.route_cambridge_enno))
        router.add_get('/dsl/word/{word}', wrap(self.route_dsl_word))
        router.add_get('/gtrans/noen/{word}', wrap(self.route_gtrans_noen))
        router.add_get('/gtrans/enno/{word}', wrap(self.route_gtrans_enno))
        router.add_get('/aulismedia/norsk/{word}', wrap(self.route_aulismedia_norsk))
        router.add_get('/aulismedia/prev/{word}', wrap(self.route_aulismedia_prev))
        router.add_get('/aulismedia/next/{word}', wrap(self.route_aulismedia_next))
        router.add_get('/aulismedia/search_norsk/{word}', wrap(self.route_aulismedia_search_norsk))
        router.add_get('/all/word/{word}', self.route_all_word)
        router.add_get('/stats', self.route_stats)
        router.add_get('/', self.route_index)
        app.add_routes([web.static('/static', STATIC_DIR)])
    def route_iframe_css(self, _request):
        return text_css(open(here_css('iframe.css')).read())
    async def route_ui_mix(self, word):
        return iframe_mix(word)
    async def route_ui_nor(self, word):
        return iframe_nor(word)
    async def route_ui_third(self, word):
        return iframe_third(word)
    async def route_ui_fourth(self, word):
        return iframe_fourth(word)
    async def route_ui_q(self, word):
        return iframe_q(word)
    async def route_ui_w(self, word):
        return iframe_w(word)
    async def route_ui_e(self, word):
        return iframe_e(word)
    async def route_ui_r(self, word):
        return iframe_r(word)
    async def route_ui_h(self, word):
        return iframe_h(word)
    @cached_async
    async def route_lexin_word(self, word):
        return await LexinOsloMetArticle(self.static_client, word).get_async()
    @cached_async
    async def route_glosbe_noru(self, word):
        return await GlosbeNoRuWord(self.static_client, word).get_async()
    @cached_async
    async def route_glosbe_noen(self, word):
        return await GlosbeNoEnWord(self.static_client, word).get_async()
    @cached_async
    async def route_glosbe_enno(self, word):
        return await GlosbeEnNoWord(self.static_client, word).get_async()
    @cached_async
    async def route_ordbok_inflect(self, word):
        return await OrdbokInflect(self.static_client, word).get_async()
    @cached_async
    async def route_ordbok_word(self, word):
        return await OrdbokWord(self.static_client, word).get_async()
    @cached_async
    async def route_ordbokene_word(self, word):
        return await OrdbokeneWord(self.dynamic_client, word).get_async()
    @cached_async
    async def route_ordbokene_inflect(self, word):
        return await OrdbokeneInflect(self.dynamic_client, word).get_async()
    @cached_async
    async def route_naob_word(self, word):
        return await NaobWord(self.dynamic_client, word).get_async()
    @cached_async
    async def route_wiktionary_no(self, word):
        return await WiktionaryNo(self.static_client, word).get_async()
    @cached_async
    async def route_cambridge_enno(self, word):
        return await CambridgeEnNo(self.static_client, word).get_async()
    @cached_async
    async def route_dsl_word(self, word):
        return await DslWord(None, word).get_async()
    @cached_async
    async def route_gtrans_noen(self, word):
        return await GoogleTranslateNoEn(self.static_client, word).get_async()
    @cached_async
    async def route_gtrans_enno(self, word):
        return await GoogleTranslateEnNo(self.static_client, word).get_async()
    async def route_aulismedia_norsk(self, word):
        return await AulismediaWord(self.static_client, word).get_async()
    async def route_aulismedia_prev(self, word):
        return web.HTTPFound(AulismediaWord.flip(word, -1))
    async def route_aulismedia_next(self, word):
        return web.HTTPFound(AulismediaWord.flip(word, 1))
    async def route_aulismedia_search_norsk(self, word):
        return index_search(INDEX_PATH, word.lower())
    # def route_aulismedia_static(self, word):
    #     return AulismediaWord.static(word)
    async def route_all_word(self, request):
        word = request.match_info.get('word')
        parallel = request.rel_url.query.get('parallel', '')
        urls = [
            self.url('/lexin/word/{}'.format(word)),
            self.url('/ordbok/inflect/{}'.format(word)),
            self.url('/ordbok/word/{}'.format(word)),
            self.url('/naob/word/{}'.format(word)),
            self.url('/glosbe/noru/{}'.format(word)),
            self.url('/glosbe/noen/{}'.format(word)),
            self.url('/glosbe/enno/{}'.format(word)),
            self.url('/wiktionary/no/{}'.format(word)),
            self.url('/cambridge/enno/{}'.format(word)),
            self.url('/dsl/word/{}'.format(word)),
            self.url('/gtrans/noen/{}'.format(word)),
            self.url('/gtrans/enno/{}'.format(word)),
            self.url('/aulismedia/norsk/{}'.format(word)),
        ]
        logging.info('all: word=%s, parallel=%s, #urls=%d', word, parallel, len(urls))
        header = f'parallel={bool(parallel)}\n'
        if parallel:
            times = await gather(*[timed_http_get_async(url) for url in urls])
        else:
            times = [await timed_http_get_async(url) for url in urls]
        strs = ['{:.2f}'.format(x) for x in times]
        details = ''.join('{} {}\n'.format(t, u) for t, u in zip(strs, urls))
        result = header + details + ' '.join(strs) + '\n'
        return text_html(result)
    async def route_stats(self, _request):
        return web.json_response(self.stats.get_all(), dumps=lambda x: dumps(x, indent=2))
    async def route_index(self, request):
        links = []
        for r in self.app.router.resources():
            info = r.get_info()
            pattern = info.get('formatter', info.get('path', None))
            if pattern:
                links.append((pattern, pattern))
        context = {'links': links}
        return aiohttp_jinja2_render_template("index.html", request, context=context)

class TimingStats:
    MAX_ITEMS = 30
    def __init__(self):
        self.times = {}
    def set(self, path, value):
        self.times[path] = {'took': value, 'at': time.time()}
        self.times = self.trim(self.times)
    def trim(self, times):
        list = self.as_list(times)
        list.sort(key=lambda x: x['at'])
        list = list[-self.MAX_ITEMS:]
        return self.as_dict(list)
    def as_list(self, times):
        result = [{'path': path, 'took': value['took'], 'at': value['at']}
                  for path, value in times.items()]
        return result
    def as_dict(self, times_list):
        return {x['path']: {'took': x['took'], 'at': x['at']} for x in times_list}
    def get_all(self):
        result = self.as_list(self.times)
        result.sort(key=lambda x: x['took'])
        return result

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

def track_history(source_signal):
    load_env('~/.telegram')
    phone = environ.get('TELEGRAM_PHONE')
    api_id = environ.get('TELEGRAM_API_ID')
    api_hash = environ.get('TELEGRAM_API_HASH')
    channel_id = environ.get('TELEGRAM_ORDBOK_ID')
    if not api_id or not api_hash or not channel_id or not phone:
        logging.info('Missing Telegram env variables')
        return
    logging.info('Starting Telegram logger')
    channel_id = int(channel_id)
    wl = WordLogger(phone, api_id, api_hash, channel_id)
    loop = new_event_loop()
    async def auth():
        logging.info('Telegram: checking is_user_authorized')
        logging.info('Telegram: is_user_authorized: %s', await wl.client.is_user_authorized())
        logging.info('Telegram: checking is_user_authorized done')
    @pyqtSlot(str)
    def on_translate(word):
        logging.info('Telegram: add word to history: %s', word)
        run_coroutine_threadsafe(wl.add(word), loop)
    def start():
        set_event_loop(loop)
        loop.run_until_complete(wl.start())
        loop.run_until_complete(auth())
        #run_coroutine_threadsafe(wl.start(), loop)
        #run_coroutine_threadsafe(auth(), loop)
        loop.run_forever()
    #set_event_loop(loop)
    #start()
    source_signal.connect(on_translate)
    Thread(target=start, daemon=True).start()

def main():
    logging.info(CACHE_BY_URL)
    logging.info(CACHE_BY_METHOD)
    disable_logging()
    init_logger(in_temp_dir(LOG_FILENAME))
    force_ipv4()
    static_client = CachedHttpClient(StaticHttpClient(), CACHE_BY_URL)
    dynamic_client = CachedHttpClient(DynamicHttpClient(), CACHE_BY_URL)
    ui_server = AIOHTTPUIServer(static_client, dynamic_client, UI_HOST, UI_PORT)
    ui_server.serve_background()

    qtApp = QApplication(sys.argv)
    window = MainWindow(qtApp)

    tray = QSystemTrayIcon(QIcon(ICON_FILENAME), qtApp)
    menu = QMenu()
    show = QAction('Show')
    hide = QAction('Hide')
    quit = QAction('Quit')
    show.triggered.connect(window.show)
    hide.triggered.connect(window.hide)
    quit.triggered.connect(window.close)
    menu.addAction(show)
    menu.addAction(hide)
    menu.addAction(quit)
    tray.setContextMenu(menu)
    tray.activated.connect(window.onTrayActivated)
    tray.show()

    dog.observe(lambda: window.myActivate.emit())
    track_history(window.myTranslate)

    result = qtApp.exec()

def testnaob(word):
    client = CachedHttpClient(DynamicHttpClient(), 'cache')
    print(NaobWord(client, word).html)

if __name__ == '__main__':
    main()
