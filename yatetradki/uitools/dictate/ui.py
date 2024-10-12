import sys, os, tempfile, threading
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PySide6 import QtGui
from PySide6.QtGui import QIcon, QPixmap, QAction, QPainter, QColor, QBrush, QActionGroup


class App:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.tray = QSystemTrayIcon()
        self.blue_icon = QIcon("letter-d.png")
        self.red_icon = QIcon("letter-r.png")
        self.tray.setIcon(self.blue_icon)
        self.tray.setToolTip("dictate")

        menu = QMenu()
        self.model = "whisper-large-v3-turbo"
        models = ["whisper-large-v3-turbo", "whisper-large-v3"]
        model_group = QActionGroup(menu)
        for m in models:
            act = model_group.addAction(m)
            act.setCheckable(True)
            act.setChecked(m == self.model)
            act.triggered.connect(lambda checked, m=m: self.set_model(m))
            menu.addAction(act)
        menu.addSeparator()
        self.language = "en"
        languages = ["en", "no", "nn", "ru"]
        lang_group = QActionGroup(menu)
        lang_group.setExclusive(True)
        for l in languages:
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
        self.model = model
        for act in self.tray.contextMenu().findChild(QMenu, "Model").actions():
            act.setChecked(act.text() == model)

    def set_language(self, lang):
        self.language = lang
        for act in self.tray.contextMenu().findChild(QMenu, "Language").actions():
            act.setChecked(act.text() == lang)

    def exit(self):
        self.tray.hide()
        self.app.quit()

    def run(self):
        sys.exit(self.app.exec())

if __name__ == "__main__":
    App().run()
