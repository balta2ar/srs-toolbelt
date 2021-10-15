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
from urllib.parse import urlparse, quote
from json import loads
from string import Template
from itertools import groupby

from requests import get
from requests.exceptions import HTTPError
from bs4 import BeautifulSoup

from PyQt5.QtWidgets import (QApplication, QComboBox, QVBoxLayout,
                             QWidget, QDesktopWidget, QCompleter, QTextBrowser,
                             QSystemTrayIcon, QMenu, QAction)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt, QTimer, QObject, QUrl
from PyQt5.QtCore import pyqtSignal, pyqtSlot

FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.DEBUG)


WINDOW_WIDTH = 1300
WINDOW_HEIGHT = 800
UPDATE_DELAY = 500
ICON_FILENAME = dirname(__file__) + '/ordbok_uib_no.png'
ADD_TO_FONT_SIZE = 6

PROXY_STYLE = '''
<style>
* {
margin: 0;
padding: 0;
font-size: 100%;
}
body {
background-color: white;
color: black;
font-family: sans-serif;
}
</style>
'''
HTML = '''
<div id="41772"><table class="paradigmetabell" cellspacing="0" style="margin: 25px;"><tbody><tr><th class="nobgnola"><span class="grunnord">liv</span></th><th class="nola" colspan="2">Entall</th><th class="nola" colspan="2">Flertall</th></tr><tr><th class="nobg">&nbsp;&nbsp;</th><th>Ubestemt form</th><th>Bestemt form</th><th>Ubestemt form</th><th>Bestemt form</th></tr><tr id="41772_1"><td class="ledetekst">n1</td><td class="vanlig">et liv</td><td class="vanlig">livet</td><td class="vanlig">liv</td><td class="vanlig">liva</td></tr><tr id="41772_2"><td class="ledetekst">n1</td><td class="vanlig">et liv</td><td class="vanlig">livet</td><td class="vanlig">liv</td><td class="vanlig">livene</td></tr></tbody></table></div>
'''

class HttpClient:
    def get(self, url, origin=None):
        logging.info('http get "%s"', url)
        headers = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:59.0) Gecko/20100101 Firefox/59.0'}
        if origin:
            headers['Origin'] = origin
        result = get(url, verify=False, headers=headers)
        result.raise_for_status()
        return result.text


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

def extract(soup, *args):
    result = soup.find(*args)
    return result.prettify() if result else '<body>No content</body>'

def parse(body):
    return BeautifulSoup(body, features='lxml')

def iframe(word):
    t = Template(open(here('iframe.html')).read())
    return t.substitute(word=word)

def ui_url(word):
    return 'http://{0}:{1}/ui/{2}'.format(UI_HOST, UI_PORT, word)

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
        parts = soup.find_all('span', {"class": "oppsgramordklasse"})
        parts = [PartOfSpeech(client, x) for x in parts]
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
    URL: str
    def __init__(self, client, word):
        self.word = word
        soup = parse(client.get(self.get_url(word)))
        self.html = extract(soup, 'div', {'id': 'dictionary-content'})
    def styled(self):
        return self.style() + self.html
    def get_url(self, word):
        return self.URL.format(word)
    def style(self):
        return css('glosbe-style.css')

class GlosbeNoRuWord(GlosbeWord):
    URL = 'https://nb.glosbe.com/nb/ru/{0}'

class GlosbeNoEnWord(GlosbeWord):
    URL = 'https://nb.glosbe.com/nb/en/{0}'


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


class MainWindow(QWidget):
    myActivate = pyqtSignal()
    def __init__(self, app):
        super().__init__()
        self.myActivate.connect(self.activate)

        self.app = app
        self.async_fetch = AsyncFetch(CachedHttpClient(HttpClient(), 'cache'))
        self.async_fetch.ready.connect(self.on_fetch_ready)

        self.comboxBox = QComboBox(self)
        self.comboxBox.setEditable(True)
        self.comboxBox.setCurrentText('')
        self.comboxBox.currentTextChanged.connect(self.on_text_changed)

        font = QFont()
        font.setPointSize(font.pointSize() + ADD_TO_FONT_SIZE)
        self.comboxBox.setFont(font)

        self.browser = QWebEngineView(self) #QTextBrowser(self)
        self.browser.setZoomFactor(1.5)
        #self.browser.setHtml(iframe('hund')) #setHtml(STYLE + HTML) #setText(STYLE + HTML)
        #self.browser.setUrl(QUrl(ui_url('hund'))) #setHtml(STYLE + HTML) #setText(STYLE + HTML)
        self.set_url(ui_url('hund'))
        self.browser.show()

        mainLayout = QVBoxLayout(self)
        mainLayout.setSpacing(0)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.addWidget(self.comboxBox)
        mainLayout.addWidget(self.browser)
        self.setLayout(mainLayout)

        self.setWindowTitle('OrdbokUibNo')
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setWindowIcon(QIcon(ICON_FILENAME))

        QTimer.singleShot(1, self.center)

        self.center()
        self.show()

    def activate(self):
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

    def set_url(self, url):
        #self.browser.setUrl(QUrl(url))
        print('setting', url)
        self.browser.load(QUrl(url))

    def set_text(self, text):
        raise RuntimeError("should not be used")
        #self.browser.setText(STYLE + text)
        #self.browser.setHtml(STYLE + text)
        #self.browser.setHtml(text)
        #self.browser.setHtml(text)

    def on_text_changed(self, text):
        if text == '':
            return

        QTimer.singleShot(UPDATE_DELAY, lambda: self.update(text))

    def update(self, old_text):
        if self.same_text(old_text):
            self.fetch(old_text)

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

    def fetch(self, word):
        self.set_url(ui_url(word))
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

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.hide()
        elif (e.key() == Qt.Key_Q) and (e.modifiers() == Qt.ControlModifier):
            self.close()
        elif (e.key() == Qt.Key_L) and (e.modifiers() == Qt.ControlModifier):
            self.comboxBox.lineEdit().selectAll()
            self.comboxBox.setFocus()
        elif e.key() == Qt.Key_Return:
            self.fetch(self.text())


PRELUDE = '''
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<title>Bokmålsordboka | Nynorskordboka</title>
<meta name="description" content="" />
<meta name="keywords" content="" />

<meta name="robots" content="index,follow" />
<meta name="revisit-after" content="14 days" />
<link rel="shortcut icon" href="/apple-touch-icon.png" />
<link rel="apple-touch-icon" href="/apple-touch-icon.png" />

<script type="text/javascript" src="/js/jquery-1.7.2.min.js"></script>
<script type="text/javascript" src="/js/jquery-ui-1.8.22.custom.min.js"></script>
<script type="text/javascript" src="/js/jquery.autocomplete-1.1.3/jquery.autocomplete.js"></script>
<meta http-equiv="X-UA-Compatible" content="IE=edge">
<meta name="viewport" content="width=device-width, target-densityDpi=160dpi, initial-scale=1">
<meta name="MobileOptimized" content="width">
<meta name="HandheldFriendly" content="true">
<link href="/static/css/ord-concatenated.css" rel="stylesheet" type="text/css">
</head>
<body>
{0}
</body>
</html>
'''


from flask import Flask, Response
class GoldenDictProxy:
    def __init__(self, client, host, port):
        self.client = client
        self.host = host
        self.port = port
        self.app = Flask(__name__)
    def serve_background(self):
        Thread(target=self.serve, daemon=True).start()
    def serve(self):
        logging.info('Starting GoldenDictProxy on %s:%s', self.host, self.port)
        self.app.register_error_handler(HTTPError, self.http_error)
        self.app.route('/ui/<word>', methods=['GET'])(self.route_ui)
        self.app.route('/lexin/word/<word>', methods=['GET'])(self.route_lexin_word)
        self.app.route('/ordbok/inflect/<word>', methods=['GET'])(self.route_ordbok_inflect)
        self.app.route('/ordbok/word/<word>', methods=['GET'])(self.route_ordbok_word)
        self.app.route('/glosbe/noru/<word>', methods=['GET'])(self.route_glosbe_noru)
        self.app.route('/glosbe/noen/<word>', methods=['GET'])(self.route_glosbe_noen)
        self.app.route('/static/css/ord-concatenated.css', methods=['GET'])(self.route_css)
        self.app.run(host=self.host, port=self.port, debug=True, use_reloader=False, threaded=True)
    def http_error(self, e):
        return 'HTTPError: {0}'.format(e)
    def route_ui(self, word):
        return iframe(word)
    def route_lexin_word(self, word):
        return LexinOsloMetArticle(self.client, word).styled()
    def route_glosbe_noru(self, word):
        return GlosbeNoRuWord(self.client, word).styled()
    def route_glosbe_noen(self, word):
        return GlosbeNoEnWord(self.client, word).styled()
    def route_ordbok_inflect(self, word):
        return Article(client, word).styled()
    def route_ordbok_word(self, word):
        return OrdbokWord(client, word).styled()
    def format(self, html):
        return PRELUDE.format(html)
    def route_css(self):
        body = open(here('ord-concatenated.css')).read()
        return Response(body, mimetype='text/css')


if __name__ == '__main__':
    client = CachedHttpClient(HttpClient(), 'cache')
    golden_dict_proxy = GoldenDictProxy(client, UI_HOST, UI_PORT)
    golden_dict_proxy.serve_background()

    app = QApplication(sys.argv)
    window = MainWindow(app)

    tray = QSystemTrayIcon(QIcon(dirname(__file__)+'/ordbok_uib_no.png'), app)
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

    result = app.exec()

