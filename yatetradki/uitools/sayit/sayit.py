#!/usr/bin/env python3

from zlib import crc32
from os import makedirs
from os.path import dirname, exists, join
import subprocess
import sys

from PyQt5.QtGui import QClipboard
from PyQt5.QtWidgets import QApplication
from gtts import gTTS

CACHE_DIR = join(dirname(__file__), 'cache')

def ensure_path(filename):
    d = dirname(filename)
    if not exists(d):
        makedirs(d)

def limit(text, max_characters=50):
    checksum = hex(crc32(text.encode()))[2:]
    return text[:max_characters] + '_' + checksum

def play(filename):
    subprocess.run(['play', '-t', 'mp3', filename])

def pronounce(text) -> str:
    filename = join(CACHE_DIR, limit(text) + '.mp3')
    ensure_path(filename)
    if not exists(filename):
        tts = gTTS(text=text, lang='no')
        tts.save(filename)
    return filename

def selection() -> str:
    return QApplication.clipboard().text(QClipboard.Selection)

def main():
    _ = QApplication(sys.argv)
    text = selection()
    mp3 = pronounce(text)
    play(mp3)

if __name__ == '__main__':
    main()
