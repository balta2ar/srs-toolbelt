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


HOST = 'localhost'
PORT = 5650
dog = WatchDog(HOST, PORT)
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

from requests import get
from bs4 import BeautifulSoup

from PyQt5.QtWidgets import (QApplication, QComboBox, QVBoxLayout,
                             QWidget, QDesktopWidget, QCompleter, QTextBrowser,
                             QSystemTrayIcon, QMenu, QAction)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt, QTimer, QObject
from PyQt5.QtCore import pyqtSignal, pyqtSlot

FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.DEBUG)


WINDOW_WIDTH = 1300
WINDOW_HEIGHT = 800
UPDATE_DELAY = 200
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
STYLE = '''
<style>
th {
    font-family: "Trebuchet MS", Verdana, Arial, Helvetica, sans-serif;
    font-weight: bold;
    color: #557FBD;
    border-right: 1px solid #557FBD;
    border-bottom: 1px solid #557FBD;
    border-top: 1px solid #557FBD;
    text-align: center;
    padding: 6px 6px 6px 12px;
}
td {
    font-family: "Trebuchet MS", Verdana, Arial, Helvetica, sans-serif;
    color: #557FBD;
    border-right: 1px solid #557FBD;
    border-bottom: 1px solid #557FBD;
    background: #fff;
    padding: 6px 6px 6px 12px;
    text-align: center;
}
</style>
'''
HTML = '''
<div id="41772"><table class="paradigmetabell" cellspacing="0" style="margin: 25px;"><tbody><tr><th class="nobgnola"><span class="grunnord">liv</span></th><th class="nola" colspan="2">Entall</th><th class="nola" colspan="2">Flertall</th></tr><tr><th class="nobg">&nbsp;&nbsp;</th><th>Ubestemt form</th><th>Bestemt form</th><th>Ubestemt form</th><th>Bestemt form</th></tr><tr id="41772_1"><td class="ledetekst">n1</td><td class="vanlig">et liv</td><td class="vanlig">livet</td><td class="vanlig">liv</td><td class="vanlig">liva</td></tr><tr id="41772_2"><td class="ledetekst">n1</td><td class="vanlig">et liv</td><td class="vanlig">livet</td><td class="vanlig">liv</td><td class="vanlig">livene</td></tr></tbody></table></div>
'''

class HttpClient:
    def get(self, url):
        logging.info('http get "%s"', url)
        headers = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:59.0) Gecko/20100101 Firefox/59.0'}
        result = get(url, headers=headers)
        result.raise_for_status()
        return result.text


class CachedHttpClient:
    def __init__(self, client, dirname):
        self.client = client
        self.dirname = dirname

    def get(self, url):
        path = self.get_path(self.get_key(url))
        content = slurp(bz2.open, path)
        if content is None:
            logging.info('cache miss: "%s"', url)
            content = self.client.get(url)
            spit(bz2.open, path, content)
        return content

    def get_path(self, key):
        return '{0}/{1}/{2}'.format(dirname(__file__), self.dirname, key)

    def get_key(self, url):
        J = lambda x: re.sub(r'\W+', '', x)
        S = lambda x: re.sub(r'\W+', '/', x)
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
    return BeautifulSoup(html, features='lxml').text


def uniq(items, key):
    seen = set()
    return [x for x in items if not (key(x) in seen or seen.add(key(x)))]


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
        soup = BeautifulSoup(client.get(self.get_url(word)), features='lxml')
        parts = soup.find_all('span', {"class": "oppsgramordklasse"})
        parts = [PartOfSpeech(client, x) for x in parts]
        self.parts = parts
        self.html = ''.join(uniq([x.inflection.html for x in self.parts], to_text))

    def get_url(self, word: str) -> str:
        return 'https://ordbok.uib.no/perl/ordbok.cgi?OPP={0}&ant_bokmaal=5&ant_nynorsk=5&bokmaal=+&ordbok=bokmaal'.format(word)

    def __repr__(self):
        return f'Article(word={self.word}, parts={self.parts})'


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
        self.browser.setHtml(STYLE + HTML) #setText(STYLE + HTML)
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

    def set_text(self, text):
        #self.browser.setText(STYLE + text)
        self.browser.setHtml(STYLE + text)

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
                self.set_text(result.html)
        elif isinstance(result, Suggestions):
            if self.same_text(result.word) and result.top:
                print(result)
                #self.suggest(result.top)
        else:
            logging.warn('unknown fetch result: %s', result)

    def fetch(self, word):
        self.async_fetch.add(lambda client: Article(client, word))
        self.async_fetch.add(lambda client: Suggestions(client, word))

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

def here(name):
    return join(dirname(__file__), name)

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
        self.app.route('/ordbok/inflect/<word>', methods=['GET'])(self.route_ordbok_inflect)
        self.app.route('/ordbok/word/<word>', methods=['GET'])(self.route_ordbok_word)
        self.app.route('/glosbe/noru/<word>', methods=['GET'])(self.route_glosbe_noru)
        self.app.route('/static/css/ord-concatenated.css', methods=['GET'])(self.route_css)
        self.app.run(host=self.host, port=self.port, debug=True, use_reloader=False)
    def route_glosbe_noru(self, word):
        url = 'https://nb.glosbe.com/nb/ru/{0}'.format(word)
        result = self.client.get(url)
        #https://nb.glosbe.com/nb/ru/gift
        return result
    def route_ordbok_inflect(self, word):
        body = Article(client, word).html
        return body
    def route_ordbok_word(self, word):
        logging.info('Inflect: %s', word)
        r = Response(open(here('barn.html')).read())
        r.headers['age'] = '0'
        r.headers['cache-control'] = 'public,must-revalidate,max-age=600,s-maxage=0'
        r.headers['content-type'] = 'text/html; charset=utf-8'
        r.headers['server'] = 'nginx'
        r.headers['via'] = '1.1 varnish-v4'
        r.headers['x-cache'] = 'MISS'
        r.headers['x-cache-hits'] = '0'
        r.headers['x-debug-max-age-sec'] = '43200'
        r.headers['x-debugdb'] = 'ok'
        r.headers['x-varnish'] = '28182065'
        #date: Sun, 03 Oct 2021 14:24:58 GMT
        #last-modified: Sun, 03 Oct 2021 14:24:58 GMT
        from datetime import datetime, timezone
        r.headers['last-modified'] = datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT') #r.headers['date']
        return r
        #return self.format(Article(self.client, word).html)
        #return 'word: {0}'.format(word)
    def format(self, html):
        return PRELUDE.format(html)
    def route_css(self):
        body = open(here('ord-concatenated.css')).read()
        return Response(body, mimetype='text/css')

        # result = '<html><head>{0}</head><body>{1}</body></html>'.format(PROXY_STYLE, html)
        # return pretty(result)

        #return '<html><head>{0}</head><body>{1}</body></html>'.format(STYLE, html)
        #return '{0}{1}'.format(STYLE, html)
        #return '{0}'.format(html)

        # x = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">'
        # x += '<html xmlns="http://www.w3.org/1999/xhtml">'
        # x += '<body>'
        # x += html
        # x += '</body>'
        # x += '</html>'
        # return x

def pretty(html):
    return BeautifulSoup(html, features='lxml').prettify()


if __name__ == '__main__':
    client = CachedHttpClient(HttpClient(), 'cache')
    golden_dict_proxy = GoldenDictProxy(client, 'localhost', 5660)
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

