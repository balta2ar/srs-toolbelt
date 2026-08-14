# -*- coding: utf-8 -*-
"""
LingoLive (https://lingvolive.ru) online translation.

A lightweight client for the LingoLive translate API
(https://lingvolive.ru/translate/en-ru), handy for grabbing quick
translations before offline dictionaries are in place.
"""

import requests


class LingoLive(object):
    API_URL = 'https://api.lingvolive.ru/translate/v2/translate'

    def __init__(self, from_lang='en', to_lang='ru'):
        self.from_lang = from_lang
        self.to_lang = to_lang

    def translate(self, text):
        params = {
            'from': self.from_lang,
            'to': self.to_lang,
            'query': text,
        }
        response = requests.get(self.API_URL, params=params)
        response.raise_for_status()
        return response.json()['text']
