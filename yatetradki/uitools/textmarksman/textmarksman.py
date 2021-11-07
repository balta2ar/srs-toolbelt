#!/usr/bin/env python3

import re
import sys
import subprocess
from typing import Optional
import tesserocr
import pyperclip

EXIT_OK = 0
EXIT_CANCEL = 1
UPPER = "".join([chr(i) for i in range(sys.maxunicode) if chr(i).isupper()])

def capture() -> Optional[str]:
    filename = '/tmp/textmarksman.png'
    p = subprocess.run(['maim', '-s', '-o', filename])
    if p.returncode == 0:
        return filename
    return None

def ocr(filename: str, lang: str) -> str:
    with tesserocr.PyTessBaseAPI(lang=lang) as api:
        api.SetImageFile(filename)
        return api.GetUTF8Text()

def unwrap(text: str) -> str:
    # remove trailing whitespace
    text = re.sub(r'\s+$', '', text)
    text = re.sub(r' +\n', '\n', text)
    text = re.sub(r'\n +', '\n', text)
    # join hyphen
    text = re.sub(r'[-\u2014]\s*\u2029\s*', '', text)
    pre, suc = '', ''
    # keep paragraphs
    pre += r'\u2029'
    # keep endmark
    pre += r'\.\?!'
    # keep quote
    # pre += r"'\"\u00BB\u00AB"
    # suc += r"'\"\u00AB\u00BB"
    # keep paragraphs
    suc += r'\u2029'
    if pre:
        pre = '([^' + pre + '])'
    if suc:
        suc = '(?![' + suc + '])'
    #expr = pre + '\u2029' + suc
    expr = pre + ' ' + suc
    #expr = r'([^\u2029\.\?!]) (?![\u2029])'
    expr = r'([^\.\n])\n(?![\n' + UPPER + '])'
    #print(expr)
    text = re.sub(expr, r'\1 ' if pre else ' ', text)
    # collapse spaces
    text = re.sub(r'[ \t]+', ' ', text)
    return text

def copy(text: str) -> str:
    pyperclip.copy(text)
    return text

def notify(title, message):
    subprocess.run(['notify-send', title, message], check=True)

def main():
    print(tesserocr.tesseract_version())
    print(tesserocr.get_languages())
    filename = capture()
    #filename = '/tmp/textmarksman.png'
    if filename:
        text = ocr(filename, 'nor')
        text = unwrap(text)
        copy(text)
        notify('OCR', text)
        print(text)
        return EXIT_OK
    return EXIT_CANCEL


if __name__ == '__main__':
    sys.exit(main())
