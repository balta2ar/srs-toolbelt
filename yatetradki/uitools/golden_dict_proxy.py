#!/usr/bin/env python3

import logging
from threading import Thread

from ordbok_uib_no import CachedHttpClient, HttpClient

from uvicorn import run as uvicorn_run
from fastapi import FastAPI
proxy_app = FastAPI()

FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.DEBUG)

class GoldenDictProxy:
    def __init__(self, client, host, port):
        self.client = client
        self.host = host
        self.port = port
    def serve(self):
        logging.info('Starting GoldenDictProxy on %s:%s', self.host, self.port)
        uvicorn_run('golden_dict_proxy:proxy_app', host=self.host, port=self.port, log_level='info')
    @proxy_app.get('/ordbok/inflect/{word}')
    def ordbok_inflect(self, word):
        logging.info('Inflect: %s', word)


if __name__ == '__main__':
    client = CachedHttpClient(HttpClient(), 'cache')
    golden_dict_proxy = GoldenDictProxy(client, 'localhost', 5660)
    golden_dict_proxy.serve()
    #Thread(target=golden_dict_proxy.serve, daemon=True).start()
