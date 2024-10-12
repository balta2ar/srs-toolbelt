import sys, os, tempfile, threading
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PySide6 import QtGui
from PySide6.QtGui import QIcon, QPixmap, QAction, QPainter, QColor, QBrush, QActionGroup
from os.path import join, dirname, expanduser, expandvars
import signal
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

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

def state(): return slurp_lines("state")[0]
def models(): return slurp_lines("models")
def model_current(): return slurp_lines("model")[0] or models()[0]
def model_save(model): spit("model", model)
def langs(): return slurp_lines("langs")
def lang_current(): return slurp_lines("lang")[0] or langs()[0]
def lang_save(lang): spit("lang", lang)

class OneFile(FileSystemEventHandler):
    def __init__(self, target, update_callback):
        super().__init__()
        self.target = target
        self.update_callback = update_callback

    def on_modified(self, event):
        if event.src_path == self.target:
            self.update_callback()

class App:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.tray = QSystemTrayIcon()
        self.idle_icon = QIcon("idle.png")
        self.recording_icon = QIcon("record.png")
        self.transcribe_icon = QIcon("transcribe.png")
        self.tray.setIcon(self.idle_icon)
        self.tray.setToolTip("dictate (using groq + whisper)")

        menu = QMenu()
        self.model = model_current()
        print(f"Current model: {self.model}")
        model_group = QActionGroup(menu)
        for m in models():
            act = model_group.addAction(m)
            act.setCheckable(True)
            act.setChecked(m == self.model)
            act.triggered.connect(lambda checked, m=m: self.set_model(m))
            menu.addAction(act)

        menu.addSeparator()

        self.language = lang_current()
        print(f"Current language: {self.language}")
        lang_group = QActionGroup(menu)
        for l in langs():
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

        self.observer = Observer()
        event_handler = OneFile(join(BASE, "state"), self.update_icon)
        self.observer.schedule(event_handler, path=BASE, recursive=False)
        self.observer.start()

    def update_icon(self):
        s = state()
        match s:
            case "I": self.tray.setIcon(self.idle_icon)
            case "R": self.tray.setIcon(self.recording_icon)
            case "T": self.tray.setIcon(self.transcribe_icon)
            case _: print(f"Unknown state: {state()}")
        print(f"Updated icon to {s}")

    def set_model(self, model):
        model_save(model)
        self.model = model

    def set_language(self, lang):
        lang_save(lang)
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
