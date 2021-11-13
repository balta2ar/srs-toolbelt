#!/bin/env python3

from subprocess import run
import re
import sys

def slurp():
    return run('xsel', shell=True, capture_output=True).stdout.decode('utf-8')

def spit(text):
    run(['xsel', '-bi'], input=text.encode('utf8'), check=True)

def notify(title, message):
    run(['notify-send', title, message], check=True)

def unwrap(text: str) -> str:
    upper = "".join([chr(i) for i in range(sys.maxunicode) if chr(i).isupper()])
    # remove trailing whitespace
    text = re.sub(r'\s+$', '', text)
    text = re.sub(r' +\n', '\n', text)
    text = re.sub(r'\n +', '\n', text)
    # join hyphen
    text = re.sub(r'[-\u2014]\s*\u2029\s*', '', text)
    expr = r'([^\.\n])\n(?![\n' + upper + '])'
    text = re.sub(expr, r'\1 ', text)
    # collapse spaces
    text = re.sub(r'[ \t]+', ' ', text)
    return text

def main():
    text = slurp()
    text = unwrap(text)
    text = text.strip()
    print(text)
    spit(text)
    notify('dehyphen', text)


if __name__ == '__main__':
    main()
