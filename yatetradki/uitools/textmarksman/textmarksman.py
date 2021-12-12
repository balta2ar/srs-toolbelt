#!/usr/bin/env python3

import re
import sys
import argparse
import subprocess
from typing import Optional
import tesserocr
from tesserocr import PSM, OEM
import pyperclip

from yatetradki.uitools.sayit.sayit import sayit

EXIT_OK = 0
EXIT_CANCEL = 1

def capture() -> Optional[str]:
    filename = '/tmp/textmarksman.png'
    p = subprocess.run(['maim', '-s', '-o', filename])
    if p.returncode == 0:
        return filename
    return None

def ocr(filename: str, lang: str) -> str:
    # https://github.com/sirfz/tesserocr/blob/master/tesseract.pxd#L293
    # OSD_ONLY,                # Orientation and script detection only.
    # AUTO_OSD,                # Automatic page segmentation with orientation and
    #                          # script detection. (OSD)
    # AUTO_ONLY,               # Automatic page segmentation, but no OSD, or OCR.
    # AUTO,                    # Fully automatic page segmentation, but no OSD.
    # SINGLE_COLUMN,           # Assume a single column of text of variable sizes.
    # SINGLE_BLOCK_VERT_TEXT,  # Assume a single uniform block of vertically
    #                          # aligned text.
    # SINGLE_BLOCK,            # Assume a single uniform block of text. (Default.)
    # SINGLE_LINE,             # Treat the image as a single text line.
    # SINGLE_WORD,             # Treat the image as a single word.
    # CIRCLE_WORD,             # Treat the image as a single word in a circle.
    # SINGLE_CHAR,             # Treat the image as a single character.
    # SPARSE_TEXT,             # Find as much text as possible in no particular order.
    # SPARSE_TEXT_OSD,         # Sparse text with orientation and script det.
    # RAW_LINE,                # Treat the image as a single text line, bypassing
    #                          # hacks that are Tesseract-specific.
    # COUNT                    # Number of enum entries.
    with tesserocr.PyTessBaseAPI(lang=lang, psm=PSM.SINGLE_COLUMN) as api:
        api.SetImageFile(filename)
        return api.GetUTF8Text()

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
    #text = re.sub(r'[\n]+', '\n', text)
    # remove 2 consecutive newlines
    text = re.sub(r'\n\n', '\n', text)
    return text

def copy(text: str) -> str:
    pyperclip.copy(text)
    return text

def notify(title, message):
    subprocess.run(['notify-send', title, message], check=True)

def parse_args():
    parser = argparse.ArgumentParser(description='OCR text from screen')
    parser.add_argument('--sayit', default=False, action='store_true', help='Pronounce text after OCR')
    return parser.parse_args()

def main():
    args = parse_args()
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
        if args.sayit:
            sayit(text)
        return EXIT_OK
    return EXIT_CANCEL


if __name__ == '__main__':
    sys.exit(main())
