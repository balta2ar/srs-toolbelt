import sys, os, tempfile, threading
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PySide6 import QtGui
from PySide6.QtGui import QIcon, QPixmap, QAction, QPainter, QColor, QBrush, QActionGroup
from os.path import join, dirname, expanduser, expandvars
import signal

BASE = expanduser(expandvars("$HOME/.config/dictate"))

def slurp_lines(filename):
    full = join(BASE, filename)
    if not os.path.exists(full): return []
    with open(full) as f:
        return [line.strip() for line in f.readlines() if line.strip()]

def spit(filename, data):
    print(f"Saving to {filename} with {data}")
    with open(join(BASE, filename), "w") as f:
        f.write(data)

class Models:
    @staticmethod
    def all(): return slurp_lines("models")
    @staticmethod
    def current(): return slurp_lines("model")[0] or Models.all()[0]
    @staticmethod
    def save(model): spit("model", model)

class Langs:
    @staticmethod
    def all(): return slurp_lines("langs")
    @staticmethod
    def current(): return slurp_lines("lang")[0] or Langs.all()[0]
    @staticmethod
    def save(lang): spit("lang", lang)

class App:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.tray = QSystemTrayIcon()
        self.blue_icon = QIcon("letter-d.png")
        self.red_icon = QIcon("letter-r.png")
        self.tray.setIcon(self.blue_icon)
        self.tray.setToolTip("dictate")

        menu = QMenu()
        self.model = Models.current()
        print(f"Current model: {self.model}")
        model_group = QActionGroup(menu)
        for m in Models.all():
            act = model_group.addAction(m)
            act.setCheckable(True)
            act.setChecked(m == self.model)
            act.triggered.connect(lambda checked, m=m: self.set_model(m))
            menu.addAction(act)

        menu.addSeparator()

        self.language = Langs.current()
        print(f"Current language: {self.language}")
        lang_group = QActionGroup(menu)
        for l in Langs.all():
            act = lang_group.addAction(l)
            act.setCheckable(True)
            act.setChecked(l == self.language)
            act.triggered.connect(lambda checked, l=l: self.set_language(l))
            menu.addAction(act)
        menu.addSeparator()
        exit = menu.addAction("Exit")
        exit.triggered.connect(self.exit)
        self.tray.setContextMenu(menu)
        self.tray.show()

    def set_model(self, model):
        Models.save(model)
        self.model = model

    def set_language(self, lang):
        Langs.save(lang)
        self.language = lang

    def exit(self):
        self.tray.hide()
        self.app.quit()

    def run(self):
        sys.exit(self.app.exec())

def handler_sigterm(signum, frame):
    app.exit()

if __name__ == "__main__":
    # signal.signal(signal.SIGTERM, handler_sigterm)
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = App()
    app.run()
