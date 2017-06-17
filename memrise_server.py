"""
This is backend server for memrise_client.js.

Run this server before using memrise_client.js in a browser. The client
will call API to get audio for words and will upload them to memrise
servers.

This server is using fill_audio module that references local tables
with words/audios.

Run me like this (without any conda env):

PYTHONPATH=/usr/share/anki:. python2 memrise_server.py
"""
import logging
import re
try:
    from urllib.parse import unquote
except ImportError:
    from urllib import unquote
from base64 import b64encode

from flask import Flask, jsonify

from fill_audio import create_master_table, create_forced_alignment_table


FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.DEBUG)

app = Flask(__name__)
#MASTER_TABLE = create_forced_alignment_table()
MASTER_TABLE = create_master_table()
ESCAPE_RX = re.compile(r'[/]')


@app.route("/")
def root():
    logging.info('Root')
    return "Root"


def slurp(filename):
    with open(filename, 'rb') as file_:
        return file_.read()


def escape(text):
    return ESCAPE_RX.sub('_', text)


@app.route("/api/get_audio/<string:word>")
def get_audio(word):
    word = escape(unquote(word))
    logging.info('incoming word: %s', word)

    #return 'WORD: %s' % word
    results = MASTER_TABLE.lookup(word)
    if results:
        #data = slurp('sample.mp3')
        data = slurp(results[0].mp3from)
        base64 = b64encode(data).decode('utf-8')
        result = {
            'success': True,
            'word': word,
            'base64_data': base64,
        }
        #logging.info('word: %s', word)
        logging.info('word size (bytes): %s, %s', word, len(data))
        return jsonify(result)
    else:
        result = {
            'success': False,
            'word': word,
        }
        logging.info('word not found: %s', word)
        return jsonify(result)


if __name__ == '__main__':
    app.run()
