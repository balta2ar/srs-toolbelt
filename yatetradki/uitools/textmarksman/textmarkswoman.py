#!/usr/bin/env python3

import signal
import sys
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer
from os.path import dirname
from pathlib import Path
from threading import Thread
from urllib.request import urlopen


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


DIR = Path(dirname(__file__))
ICON_FILENAME = str(DIR / 'ocr.png')
WATCHDOG_HOST = 'localhost'
WATCHDOG_PORT = 5650
dog = WatchDog(WATCHDOG_HOST, WATCHDOG_PORT)
if (not is_interactive()) and (not dog.start()):
    dog.show()
    sys.exit()

from PyQt6 import QtGui
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QActionGroup
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtWidgets import QMenu
from PyQt6.QtWidgets import QSystemTrayIcon
from PyQt6.QtWidgets import QWidget

from yatetradki.uitools.textmarksman.textmarksman import do_easyocr
from yatetradki.uitools.textmarksman.textmarksman import do_tesseract


def remap(src, mapping) -> [str]:
    return [mapping[x] for x in src]

class SystemTrayIcon(QSystemTrayIcon):
    myCapture = pyqtSignal()

    def __init__(self, app, widget, window, icon, parent=None):
        QSystemTrayIcon.__init__(self, icon, parent)
        self.myCapture.connect(self.on_capture)

        menu = QMenu(parent)

        exit = menu.addAction("Exit")
        exit.triggered.connect(app.quit)

        menu.addSeparator()

        capture = menu.addAction("Capture")
        capture.triggered.connect(self.on_capture)

        menu.addSeparator()

        self.unproject = menu.addAction("Unproject")
        self.unproject.setCheckable(True)
        self.pronounce = menu.addAction("Pronounce")
        self.pronounce.setCheckable(True)

        menu.addSeparator()

        self.en = menu.addAction("en")
        self.en.setCheckable(True)
        self.en.setChecked(True)
        self.no = menu.addAction("no")
        self.no.setCheckable(True)
        self.ru = menu.addAction("ru")
        self.ru.setCheckable(True)

        menu.addSeparator()

        self.eng_tesseract = menu.addAction("tesseract")
        self.eng_tesseract.setCheckable(True)
        self.eng_tesseract.setChecked(True)
        self.eng_easyocr = menu.addAction("easyocr")
        self.eng_easyocr.setCheckable(True)
        self.eng_paddleocr = menu.addAction("paddleocr")
        self.eng_paddleocr.setCheckable(True)
        engine_group = QActionGroup(menu)
        engine_group.addAction(self.eng_tesseract)
        engine_group.addAction(self.eng_easyocr)
        engine_group.addAction(self.eng_paddleocr)

        self.setContextMenu(menu)

    def langs(self):
        langs = []
        if self.en.isChecked():
            langs.append('en')
        if self.no.isChecked():
            langs.append('no')
        if self.ru.isChecked():
            langs.append('ru')
        return langs

    def on_capture(self):
        print("Greet")
        unproject = self.unproject.isChecked()
        pronounce = self.pronounce.isChecked()
        filename = None
        if self.eng_tesseract.isChecked():
            mapping = {'en': 'eng', 'no': 'nor', 'ru': 'rus'}
            print(self.langs())
            langs = '+'.join(remap(self.langs(), mapping))
            print(langs)
            do_tesseract(filename, langs, unproject, pronounce)
        if self.eng_easyocr.isChecked():
            langs = ','.join(self.langs())
            do_easyocr(filename, langs, unproject, pronounce)

def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QApplication(sys.argv)
    window = QMainWindow()

    widget = QWidget()
    trayIcon = SystemTrayIcon(app, widget, window, QIcon(ICON_FILENAME), widget)

    dog.observe(lambda: trayIcon.myCapture.emit())

    trayIcon.show()
    return app.exec()

if __name__ == '__main__':
    sys.exit(main())
