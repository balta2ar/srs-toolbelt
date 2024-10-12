import sys, os, tempfile, threading
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PySide6 import QtGui
from PySide6.QtGui import QIcon, QPixmap, QAction, QPainter, QColor, QBrush


class App:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.tray = QSystemTrayIcon()
        self.blue_icon = QIcon("letter-d.png")
        self.red_icon = QIcon("letter-r.png")
        self.tray.setIcon(self.blue_icon)
        menu = QMenu()
        self.model = "whisper-large-v3-turbo"
        models = ["whisper-large-v3-turbo", "whisper-large-v3"]
        model_menu = menu.addMenu("Model")
        for m in models:
            act = QAction(m, checkable=True)
            act.setChecked(m == self.model)
            act.triggered.connect(lambda checked, m=m: self.set_model(m))
            model_menu.addAction(act)
        menu.addSeparator()
        self.language = "en"
        languages = ["en", "no", "nn", "ru"]
        lang_menu = menu.addMenu("Language")
        for l in languages:
            act = QAction(l, checkable=True)
            act.setChecked(l == self.language)
            act.triggered.connect(lambda checked, l=l: self.set_language(l))
            lang_menu.addAction(act)
        menu.addAction("Exit", self.exit)
        self.tray.setContextMenu(menu)
        self.tray.show()

    def set_model(self, model):
        self.model = model
        for act in self.tray.contextMenu().findChild(QMenu, "Model").actions():
            act.setChecked(act.text() == model)

    def set_language(self, lang):
        self.language = lang
        for act in self.tray.contextMenu().findChild(QMenu, "Language").actions():
            act.setChecked(act.text() == lang)

    def exit(self):
        self.tray.hide()
        sys.exit()


    def run(self):
        sys.exit(self.app.exec())

if __name__ == "__main__":
    App().run()
