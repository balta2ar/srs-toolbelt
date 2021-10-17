#!/usr/bin/env python3

import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.request import urlopen
from threading import Thread
from queue import Queue


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
        with urlopen(self.get_show_url(), b'') as r:
            r.read()
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
if not dog.start():
    dog.show()
    sys.exit()

import logging
import re
import bz2
from os import makedirs
from os.path import dirname, exists, normpath, join
from urllib.parse import urlparse
from json import loads
from string import Template
from itertools import groupby
import asyncio

from requests import Session
from requests.exceptions import HTTPError, ReadTimeout
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from pyppeteer import launch
from pyppeteer.errors import TimeoutError

from PyQt5.QtWidgets import (QApplication, QComboBox, QVBoxLayout,
                             QWidget, QCompleter,
                             QSystemTrayIcon, QMenu, QAction)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtGui import QIcon, QFont, QKeyEvent
from PyQt5.QtCore import Qt, QTimer, QObject, QUrl, QEvent
from PyQt5.QtCore import pyqtSignal, pyqtSlot

FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.DEBUG)


WINDOW_WIDTH = 1300
WINDOW_HEIGHT = 800
UPDATE_DELAY = 500
ICON_FILENAME = dirname(__file__) + '/ordbok_uib_no.png'
ADD_TO_FONT_SIZE = 6
NETWORK_TIMEOUT = 5000


def disable_logging():
    #print(logging.root.manager.loggerDict)
    blacklist = r'.*pyppeteer.*|.*urllib.*'
    for name in logging.root.manager.loggerDict:
        if re.match(blacklist, name) is not None:
            logger = logging.getLogger(name)
            logger.setLevel(logging.ERROR)
            logger.propagate = False
            #logging.info('Disabled logger "%s"', name)

class StaticHttpClient:
    def get(self, url, origin=None):
        logging.info('http get "%s"', url)
        headers = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:59.0) Gecko/20100101 Firefox/59.0'}
        if origin:
            headers['Origin'] = origin
        session = Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[])
        session.mount('http://', HTTPAdapter(max_retries=retries))
        session.mount('https://', HTTPAdapter(max_retries=retries))
        result = session.get(url, verify=False, headers=headers, allow_redirects=True, timeout=NETWORK_TIMEOUT/1000.0)
        result.raise_for_status()
        return result.text



class DynamicHttpClient:
    TIMEOUT = NETWORK_TIMEOUT
    def __init__(self, timeout=None):
        self.timeout = timeout or self.TIMEOUT
    def get(self, url, selector=None):
        disable_logging()
        result = [no_content()]
        async def fetch():
            browser = await launch(handleSIGINT=False, handleSIGTERM=False, handleSIGHUP=False)
            page = await browser.newPage()
            await page.goto(url)
            if selector is not None:
                await page.waitForSelector(selector, timeout=self.timeout)
                # try:
                #     await page.waitForSelector(selector, timeout=self.timeout)
                # except TimeoutError as e:
                #     logging.info('url timeout (timeout=%s, url=%s): %s', self.timeout, url, e)
                #     return
            #div = await page.querySelector(selector)
            #content = await page.evaluate('(el) => el.innerHTML', div)
            content = await page.evaluate('document.body.innerHTML', force_expr=True)
            result[0] = content
            await browser.close()

        asyncio.new_event_loop().run_until_complete(fetch())
        return result[0]


class CachedHttpClient:
    def __init__(self, client, dirname):
        self.client = client
        self.dirname = dirname

    def get(self, url, **kwargs):
        path = self.get_path(self.get_key(url))
        content = slurp(bz2.open, path)
        if content is None:
            logging.info('cache miss: "%s"', url)
            content = self.client.get(url, **kwargs)
            spit(bz2.open, path, content)
        return content

    def get_path(self, key):
        return '{0}/{1}/{2}'.format(dirname(__file__), self.dirname, key)

    def get_key(self, url):
        J = lambda x: re.sub(r'\W+', '', x)
        S = lambda x: re.sub(r'^\w\s\d-', '/', x)
        p = urlparse(url)
        a = normpath('/'.join([J(p.hostname), J(p.path), J(p.query)]))
        b = normpath('/'.join([J(p.hostname), S(p.path)]))
        return a if p.query else b

class NoContent(Exception):
    pass

def slurp(do_open, filename):
    try:
        with do_open(filename, 'rb') as file_:
            return file_.read().decode()
    except:
        return None

def spit(do_open, filename, content):
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

def extract(soup, *args):
    result = soup.find(*args)
    if result: return result.prettify()
    raise NoContent('NoContent: {0}'.format(args))
    #return result.prettify() if result else no_content()

def parse(body):
    return BeautifulSoup(body, features='lxml')

def iframe_mix(word):
    t = Template(open(here('iframe-mix.html')).read())
    return t.substitute(word=word)

def iframe_nor(word):
    t = Template(open(here('iframe-nor.html')).read())
    return t.substitute(word=word)

def iframe_third(word):
    t = Template(open(here('iframe-third.html')).read())
    return t.substitute(word=word)

def ui_mix_url(word):
    return 'http://{0}:{1}/ui/mix/{2}'.format(UI_HOST, UI_PORT, word)

def ui_nor_url(word):
    return 'http://{0}:{1}/ui/nor/{2}'.format(UI_HOST, UI_PORT, word)

def ui_third_url(word):
    return 'http://{0}:{1}/ui/third/{2}'.format(UI_HOST, UI_PORT, word)

def css(filename):
    return '<style>{0}</style>'.format(slurp(open, here(filename)))

def here(name):
    return join(dirname(__file__), name)

def pretty(html):
    return parse(html).prettify()


class Suggestions:
    # https://ordbok.uib.no/perl/lage_ordliste_liten_nr2000.cgi?spr=bokmaal&query=gam
    #
    # {query:'gam',
    # suggestions:["gaman","gamasje","gambe","gambier","gambisk","gambit","gamble","gambler","game","game","gamet","gametofytt","gamla","gamle-","gamleby","gamlefar","gamleheim","gamlehjem","gamlekjжreste","gamlemor","gamlen","gamlestev","gamletid","gamleеr","gamling","gamma","gammaglobulin","gammal","gammaldags","gammaldans","gammaldansk","gammaldansk","gammalengelsk","gammalgresk","gammalkjent","gammalkjжreste","gammalkommunist","gammalmannsaktig","gammalmodig","gammalnorsk","gammalnorsk","gammalost","gammalrosa","gammalstev","gammaltestamentlig","gammaltid","gammalvoren","gammastrеle","gammastrеling","gamme","gammel","gammel jomfru","gammel norsk mil","gammel som alle haugene","gammeldags","gammeldans","gammeldansk","gammeldansk","gammelengelsk","gammelgresk","gammelkjent","gammelkjжreste","gammelkommunist","gammelmannsaktig","gammelmodig","gammelnorsk","gammelnorsk","gammelost","gammelrosa","gammelstev","gammeltestamentlig","gammeltid","gammelvoren","gammen","gamp","gampe"],
    # data:["gaman","gamasje","gambe","gambier","gambisk","gambit","gamble","gambler","game","game","gamet","gametofytt","gamla","gamle-","gamleby","gamlefar","gamleheim","gamlehjem","gamlekjжreste","gamlemor","gamlen","gamlestev","gamletid","gamleеr","gamling","gamma","gammaglobulin","gammal","gammaldags","gammaldans","gammaldansk","gammaldansk","gammalengelsk","gammalgresk","gammalkjent","gammalkjжreste","gammalkommunist","gammalmannsaktig","gammalmodig","gammalnorsk","gammalnorsk","gammalost","gammalrosa","gammalstev","gammaltestamentlig","gammaltid","gammalvoren","gammastrеle","gammastrеling","gamme","gammel","gammel jomfru","gammel norsk mil","gammel som alle haugene","gammeldags","gammeldans","gammeldansk","gammeldansk","gammelengelsk","gammelgresk","gammelkjent","gammelkjжreste","gammelkommunist","gammelmannsaktig","gammelmodig","gammelnorsk","gammelnorsk","gammelost","gammelrosa","gammelstev","gammeltestamentlig","gammeltid","gammelvoren","gammen","gamp","gampe"]
    # }
    TOP_COUNT = 5
    def __init__(self, client, word):
        self.word = word
        items = loads(self.cleanup(client.get(self.get_url(word)))).get('suggestions', [])
        self.items = uniq(items, lambda s: s.lower())
        self.top = self.items[:Suggestions.TOP_COUNT]

    def cleanup(self, text):
        text = '{}'[:1] + '\n' + text[text.index('\n')+1:]
        #a = text.replace("'", '"')
        # :2 because of the syntax parser in neovim plugin, if I leave one
        # bracket open, it will incorrectly detect indentation
        a = text
        #a = re.sub('^{}'[:2] + 'query', '{"query"}', a)
        a = re.sub('^suggestions', '"suggestions"', a, flags=re.MULTILINE)
        a = re.sub('^data', '"data"', a, flags=re.MULTILINE)
        return a

    def get_url(self, query):
        return 'https://ordbok.uib.no/perl/lage_ordliste_liten_nr2000.cgi?spr=bokmaal&query={0}'.format(query)

    def __repr__(self):
        return f'Suggestions(word={self.word}, count={len(self.items)}, top={self.top})'

class Inflection:
    # https://ordbok.uib.no/perl/bob_hente_paradigme.cgi?lid=41772
    #  <div id="41772"><table class="paradigmetabell" cellspacing="0" style="margin: 25px;"><tr><th class="nobgnola"><span class="grunnord">liv</span></th><th class="nola" colspan="2">Entall</th><th class="nola" colspan="2">Flertall</th></tr><tr><th class="nobg">&nbsp;&nbsp;</th><th>Ubestemt form</th><th>Bestemt form</th><th>Ubestemt form</th><th>Bestemt form</th></tr><tr id="41772_1"><td class="ledetekst">n1</td><td class="vanlig">et liv</td><td class="vanlig">livet</td><td class="vanlig">liv</td><td class="vanlig">liva</td></tr><tr id="41772_2"><td class="ledetekst">n1</td><td class="vanlig">et liv</td><td class="vanlig">livet</td><td class="vanlig">liv</td><td class="vanlig">livene</td></tr></table></div>
    def __init__(self, client, lid):
        self.lid = lid
        self.html = self.cleanup(client.get(self.get_url(lid)))

    def cleanup(self, text):
        return re.sub(r'style="margin:[^"]*"', 'style="margin: 3px;"', text)

    def get_url(self, lid):
        return 'https://ordbok.uib.no/perl/bob_hente_paradigme.cgi?lid={0}'.format(lid)

    def __repr__(self):
        return f'Inflection(lid={self.lid})'

class PartOfSpeech:
    # <span class="oppsgramordklasse" onclick="vise_fullformer(&quot;8225&quot;,'bob')">adj.</span>
    def __init__(self, client, soup):
        self.name = soup.text
        self.lid = None
        self.inflection = None
        m = re.search(r'\d+', soup['onclick'])
        if m:
            self.lid = m.group(0)
            self.inflection = Inflection(client, self.lid)

    def __repr__(self):
        return f'PartOfSpeech(name="{self.name}", lid={self.lid}, inflection={self.inflection})'

class Article:
    # https://ordbok.uib.no/perl/ordbok.cgi?OPP=bra&ant_bokmaal=5&ant_nynorsk=5&bokmaal=+&ordbok=bokmaal
    # <span class="oppslagsord b" id="22720">gi</span>
    # <span class="oppsgramordklasse" onclick="vise_fullformer(&quot;8225&quot;,'bob')">adj.</span>
    def __init__(self, client, word):
        self.word = word
        soup = parse(client.get(self.get_url(word)))
        args = ('span', {"class": "oppsgramordklasse"})
        parts = soup.find_all(*args)
        parts = [PartOfSpeech(client, x) for x in parts]
        if not parts:
            raise NoContent('Ordbok: word={0}, args={1}'.format(word, args))
        self.parts = parts
        self.html = ''.join(uniq([x.inflection.html for x in self.parts], to_text))
    def styled(self):
        return self.style() + self.html
    def style(self):
        return css('ordbok-inflect.css')
    def get_url(self, word: str) -> str:
        return 'https://ordbok.uib.no/perl/ordbok.cgi?OPP={0}&ant_bokmaal=5&ant_nynorsk=5&bokmaal=+&ordbok=bokmaal'.format(word)
    def __repr__(self):
        return f'Article(word={self.word}, parts={self.parts})'


class NaobWord:
    def __init__(self, client, word):
        self.word = word
        soup = parse(client.get(self.get_url(word), selector='div.article'))
        self.html = extract(soup, 'div', {'class': 'article'})
    def styled(self):
        return self.style() + self.html
    def style(self):
        return css('naob-style.css')
    def get_url(self, word):
        return 'https://naob.no/ordbok/{0}'.format(word)


class OrdbokWord:
    def __init__(self, client, word):
        self.word = word
        soup = parse(client.get(self.get_url(word)))
        self.html = extract(soup, 'table', {'id': 'byttutBM'})
    def styled(self):
        return self.style() + self.html
    def style(self):
        return css('ord-concatenated.css')
    def get_url(self, word):
        return 'https://ordbok.uib.no/perl/ordbok.cgi?OPP={0}&ant_bokmaal=5&ant_nynorsk=5&bokmaal=+&ordbok=begge'.format(word)

class GlosbeWord:
    def __init__(self, client, word):
        self.word = word
        soup = parse(client.get(self.get_url(word)))
        self.html = extract(soup, 'div', {'id': 'dictionary-content'})
    def styled(self):
        return self.style() + self.html
    def get_url(self, word):
        pass
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

class WiktionaryNo:
    def __init__(self, client, word):
        self.word = word
        soup = parse(client.get(self.get_url(word)))
        self.html = extract(soup, 'div', {'class': 'mw-parser-output'})
    def styled(self):
        return self.style() + self.html
    def style(self):
        return css('wiktionary-style.css')
    def get_url(self, word):
        return 'https://no.wiktionary.org/wiki/{0}'.format(word)

class CambridgeEnNo:
    def __init__(self, client, word):
        self.word = word
        soup = parse(client.get(self.get_url(word)))
        self.html = extract(soup, 'div', {'class': 'dictionary'})
    def styled(self):
        return self.style() + self.html
    def style(self):
        return css('cambridge-style.css')
    def get_url(self, word):
        return 'https://dictionary.cambridge.org/dictionary/english-norwegian/{0}'.format(word)

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


class LexinOsloMetArticle:
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
    def __init__(self, client, word):
        self.word = word
        origin = 'https://lexin.oslomet.no'
        soup = loads(client.get(self.get_url(word), origin=origin))
        self.html = self.transform(soup)
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


class AsyncFetch(QObject):
    ready = pyqtSignal(object)
    def __init__(self, client):
        super(AsyncFetch, self).__init__()
        self.client = client
        self.queue = Queue()
        for _ in range(10):
            Thread(target=self._serve, daemon=True).start()
    def add(self, task):
        self.queue.put(task)
    def _serve(self):
        while True:
            task = self.queue.get()
            result = task(self.client)
            self.ready.emit(result)


class QComboBoxKey(QComboBox):
    def __init__(self, parent, on_key_press):
        super(QComboBoxKey, self).__init__(parent)
        self.on_key_press = on_key_press
    def keyPressEvent(self, e):
        if not self.on_key_press(e):
            super(QComboBoxKey, self).keyPressEvent(e)


class Browsers:
    def __init__(self, parent, layout, num):
        self.browsers = [QWebEngineView(parent) for _ in range(num)]
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
        return None
    def on_key_press(self, e):
        index = self.scan_shortcut(e)
        if index is None:
            return False
        self.show(index)
        return True


class MainWindow(QWidget):
    ZOOM = 1.7
    myActivate = pyqtSignal()
    def __init__(self, app):
        super().__init__()
        self.myActivate.connect(self.activate)

        self.app = app
        self.async_fetch = AsyncFetch(CachedHttpClient(StaticHttpClient(), 'cache'))
        self.async_fetch.ready.connect(self.on_fetch_ready)

        mainLayout = QVBoxLayout(self)
        mainLayout.setSpacing(0)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(mainLayout)
        self.main_layout = mainLayout

        self.browsers = Browsers(self, mainLayout, 3)
        self.browsers.zoom(self.ZOOM)

        self.comboxBox = QComboBoxKey(self, self.browsers.on_key_press)
        self.comboxBox.setEditable(True)
        self.comboxBox.setCurrentText('')
        self.comboxBox.currentTextChanged.connect(self.on_text_changed)
        self.comboxBox.installEventFilter(self)

        font = QFont()
        font.setPointSize(font.pointSize() + ADD_TO_FONT_SIZE)
        self.comboxBox.setFont(font)

        self.set_text('hund')
        mainLayout.addWidget(self.comboxBox)
        self.browsers.show(0)

        self.setWindowTitle('OrdbokUibNo')
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setWindowIcon(QIcon(ICON_FILENAME))

        QTimer.singleShot(1, self.center)

        self.center()
        self.show()

    def show_browser(self, index):
        self.browser.show(index)

    def grab_clipboard(self):
        content = QApplication.clipboard().text()
        if content and len(content.split()) <= 5:
            self.set_text(content)

    def activate(self):
        self.grab_clipboard()
        self.center()
        self.show()
        self.raise_()
        self.activateWindow()
        self.comboxBox.lineEdit().selectAll()
        self.comboxBox.setFocus()

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
        self.comboxBox.setCompleter(completer)
        completer.complete()

    def set_text(self, text):
        logging.info('Setting text: %s', text)
        self.comboxBox.setCurrentText(text)
        urls = [ui_mix_url(text), ui_nor_url(text), ui_third_url(text)]
        self.browsers.load(urls)

    def on_text_changed(self, text):
        if text == '':
            return
        QTimer.singleShot(UPDATE_DELAY, lambda: self.update(text))

    def update(self, old_text):
        if self.same_text(old_text):
            self.set_text(old_text)

    @pyqtSlot(object)
    def on_fetch_ready(self, result: object):
        if isinstance(result, Article):
            if self.same_text(result.word) and result.parts:
                pass
                #self.set_text(result.html)
                #self.set_text(iframe(result.word))
        elif isinstance(result, Suggestions):
            if self.same_text(result.word) and result.top:
                print(result)
                #self.suggest(result.top)
        else:
            logging.warn('unknown fetch result: %s', result)

    # def fetch(self, word):
    #     self.set_url(ui_mix_url(word))
        #self.async_fetch.add(lambda client: Article(client, word))
        #self.set_text(iframe(word))
        #self.async_fetch.add(lambda client: Suggestions(client, word))

    def onTrayActivated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.show()

    def same_text(self, word):
        return word == self.text()

    def text(self):
        return self.comboxBox.currentText()

    def eventFilter(self, obj, e):
        if isinstance(e, QKeyEvent):
            if e.key() == Qt.Key_Exclam and e.type == QEvent.KeyPress:
                return True
            elif e.key() == Qt.Key_At and e.type == QEvent.KeyPress:
                return True
        return super(MainWindow, self).eventFilter(obj, e)

    def keyPressEvent(self, e):
        if self.browsers.on_key_press(e):
            return
        if e.key() == Qt.Key_Escape:
            self.hide()
        elif (e.key() == Qt.Key_Q) and (e.modifiers() == Qt.ControlModifier):
            self.close()
        elif (e.key() == Qt.Key_L) and (e.modifiers() == Qt.ControlModifier):
            self.comboxBox.lineEdit().selectAll()
            self.comboxBox.setFocus()
        elif e.key() == Qt.Key_Return:
            self.set_text(self.text())
        else:
            print('>>>EVENT', e.key(), e.modifiers())


from flask import Flask, Response, render_template, url_for
class GoldenDictProxy:
    def __init__(self, static_client, dynamic_client, host, port):
        self.static_client = static_client
        self.dynamic_client = dynamic_client
        self.host = host
        self.port = port
        self.app = Flask(__name__, template_folder=dirname(__file__))
    def serve_background(self):
        Thread(target=self.serve, daemon=True).start()
    def serve(self):
        logging.info('Starting GoldenDictProxy on %s:%s', self.host, self.port)
        self.app.register_error_handler(HTTPError, self.error_handler)
        self.app.register_error_handler(ReadTimeout, self.error_handler)
        self.app.register_error_handler(TimeoutError, self.error_handler)
        self.app.register_error_handler(NoContent, self.error_handler)
        self.app.route('/ui/mix/<word>', methods=['GET'])(self.route_ui_mix)
        self.app.route('/ui/nor/<word>', methods=['GET'])(self.route_ui_nor)
        self.app.route('/ui/third/<word>', methods=['GET'])(self.route_ui_third)
        self.app.route('/lexin/word/<word>', methods=['GET'])(self.route_lexin_word)
        self.app.route('/ordbok/inflect/<word>', methods=['GET'])(self.route_ordbok_inflect)
        self.app.route('/ordbok/word/<word>', methods=['GET'])(self.route_ordbok_word)
        self.app.route('/naob/word/<word>', methods=['GET'])(self.route_naob_word)
        self.app.route('/glosbe/noru/<word>', methods=['GET'])(self.route_glosbe_noru)
        self.app.route('/glosbe/noen/<word>', methods=['GET'])(self.route_glosbe_noen)
        self.app.route('/wiktionary/no/<word>', methods=['GET'])(self.route_wiktionary_no)
        self.app.route('/cambridge/enno/<word>', methods=['GET'])(self.route_cambridge_enno)
        self.app.route('/static/css/iframe.css', methods=['GET'])(self.route_iframe_css)
        self.app.route('/', methods=['GET'])(self.route_index)
        self.app.run(host=self.host, port=self.port, debug=True, use_reloader=False, threaded=True)
    def error_handler(self, e):
        return '{0}: {1}'.format(type(e).__name__, e)
    def route_ui_mix(self, word):
        return iframe_mix(word)
    def route_ui_nor(self, word):
        return iframe_nor(word)
    def route_ui_third(self, word):
        return iframe_third(word)
    def route_lexin_word(self, word):
        return LexinOsloMetArticle(self.static_client, word).styled()
    def route_glosbe_noru(self, word):
        return GlosbeNoRuWord(self.static_client, word).styled()
    def route_glosbe_noen(self, word):
        return GlosbeNoEnWord(self.static_client, word).styled()
    def route_ordbok_inflect(self, word):
        return Article(self.static_client, word).styled()
    def route_ordbok_word(self, word):
        return OrdbokWord(self.static_client, word).styled()
    def route_naob_word(self, word):
        return NaobWord(self.dynamic_client, word).styled()
    def route_iframe_css(self):
        return Response(open(here('iframe.css')).read(), mimetype='text/css')
    def route_wiktionary_no(self, word):
        return WiktionaryNo(self.static_client, word).styled()
    def route_cambridge_enno(self, word):
        return CambridgeEnNo(self.static_client, word).styled()
    def route_index(self):
        links = []
        for rule in self.app.url_map.iter_rules():
            args = {v: v for v in rule.arguments or {}}
            url = url_for(rule.endpoint, **args)
            links.append((url, rule.endpoint))
        return render_template("index.html", links=links)


if __name__ == '__main__':
    disable_logging()
    static_client = CachedHttpClient(StaticHttpClient(), 'cache')
    dynamic_client = CachedHttpClient(DynamicHttpClient(), 'cache')
    golden_dict_proxy = GoldenDictProxy(static_client, dynamic_client, UI_HOST, UI_PORT)
    golden_dict_proxy.serve_background()

    qtApp = QApplication(sys.argv)
    window = MainWindow(qtApp)

    tray = QSystemTrayIcon(QIcon(dirname(__file__)+'/ordbok_uib_no.png'), qtApp)
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

    result = qtApp.exec()

def testnaob(word):
    client = CachedHttpClient(DynamicHttpClient(), 'cache')
    print(NaobWord(client, word).html)

