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
import os

FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.DEBUG)

if os.environ.get('TOR') == '1':
    logging.info('Using TOR')
    # pip2 install --user PySocks
    import socks
    import socket
    socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, "127.0.0.1", 9050)
    socket.socket = socks.socksocket

    import urllib2
    # print(urllib2.urlopen("http://www.ifconfig.me/ip").read())
    IP_CHECKER = "http://icanhazip.com"
    # IP_CHECKER = "http://httpbin.org/ip"
    logging.info('Current IP: %s', urllib2.urlopen(IP_CHECKER).read().strip())

try:
    from urllib.parse import unquote
except ImportError:
    from urllib import unquote
from base64 import b64encode

from flask import Flask, jsonify, send_from_directory

from fill_audio import create_master_table, create_forced_alignment_table


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


# NOTE: it turned out that I don't need this method because I inject
# JS in memrise_sync manually. Still, I left this method for possible
# convenience.
@app.route("/api/get_file/<path:filename>")
def get_file(filename):
    filename = escape(unquote(filename))
    logging.info('requested filename: %s', filename)
    return send_from_directory('.', filename)


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
        result = jsonify(result)
    else:
        result = {
            'success': False,
            'word': word,
        }
        logging.info('word not found: %s', word)
        result = jsonify(result)

    result.headers['Access-Control-Allow-Origin'] = '*'
    return result


if __name__ == '__main__':
    app.run(debug=False, ssl_context='adhoc')
    # app.run(debug=True, ssl_context='adhoc')
    # app.run(debug=True)
