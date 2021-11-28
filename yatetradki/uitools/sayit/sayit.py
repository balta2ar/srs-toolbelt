#!/usr/bin/env python3

from typing import Optional
from zlib import crc32
from os import makedirs
from os.path import dirname, exists, join
import subprocess
import sys
import psutil

from PyQt5.QtGui import QClipboard
from PyQt5.QtWidgets import QApplication
from gtts import gTTS

CACHE_DIR = join(dirname(__file__), 'cache')
RUNTIME_PID_FILE = '/tmp/sayit.pid'

def ensure_path(filename):
    d = dirname(filename)
    if not exists(d):
        makedirs(d)

def limit(text, max_characters=50):
    checksum = hex(crc32(text.encode()))[2:]
    return text[:max_characters] + '_' + checksum

def already_running() -> Optional[int]:
    try:
        with open(RUNTIME_PID_FILE) as f:
            pid = int(f.readline().strip())
            file_cmdline = f.readline().strip()
            running_cmdline = ' '.join(psutil.Process(pid).cmdline()).strip()
            print('cmd line: "%s" vs "%s"', file_cmdline, running_cmdline)
            return pid if file_cmdline == running_cmdline else None
    except Exception as e:
        print('Exception: %s' % str(e))
        return None

def save_running(pid):
    with open(RUNTIME_PID_FILE, 'w') as f:
        f.write(str(pid) + '\n')
        f.write(' '.join(psutil.Process(pid).cmdline()).strip())

def play(filename):
    pid = already_running()
    if pid:
        print('killing running sound: %d' % pid)
        psutil.Process(pid).kill()
    #p = subprocess.Popen(['play', '-t', 'mp3', filename])
    p = subprocess.Popen(['mplayer', filename])
    print(p.pid)
    print(psutil.Process(p.pid).cmdline())
    save_running(p.pid)

def pronounce(text) -> str:
    filename = join(CACHE_DIR, limit(text) + '.mp3')
    ensure_path(filename)
    if not exists(filename):
        tts = gTTS(text=text, lang='no')
        tts.save(filename)
    return filename

def sayit(text: str) -> None:
    mp3 = pronounce(text)
    play(mp3)

def selection() -> str:
    return QApplication.clipboard().text(QClipboard.Selection)

def main():
    _ = QApplication(sys.argv)
    text = selection()
    sayit(text)

if __name__ == '__main__':
    main()
