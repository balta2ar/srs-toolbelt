# -*- coding: utf-8 -*-


"""
Extracts audio from https://krdict.korean.go.kr/eng/dicSearch/ service.
Note that audio is provided by Naver, but this service is used because
it returns results faster.
"""

from .base import Service
from .common import Trait

import re
from bs4 import BeautifulSoup
import logging
from urllib2 import HTTPError

_logger = logging.getLogger(__name__)
RX_MP3_URL = re.compile(r'http.*mp3')
# Sample request URL:
# https://krdict.korean.go.kr/eng/dicSearch/search?nation=eng&nationCode=6&ParaWordNo=&mainSearchWord=%EC%84%B1%EA%B3%B5%EC%A0%81
KRDIR_URL = 'https://krdict.korean.go.kr/eng/dicSearch/search'

__all__ = ['Krdict']


CNDIC_ENDPOINT = 'http://tts.cndic.naver.com/tts/mp3ttsV1.cgi'
CNDIC_CONFIG = [
    ('enc', 0),
    ('pitch', 100),
    ('speed', 80),
    ('text_fmt', 0),
    ('volume', 100),
    ('wrapper', 0),
]

TRANSLATE_INIT = 'http://translate.naver.com/getVcode.dic'
TRANSLATE_ENDPOINT = 'http://translate.naver.com/tts'
TRANSLATE_CONFIG = [
    ('from', 'translate'),
    ('service', 'translate'),
    ('speech_fmt', 'mp3'),
]

VOICE_CODES = [
    ('ko', (
        "Korean",
        False,
        [
            ('speaker', 'mijin'),
        ],
    )),

    ('en', (
        "English",
        False,
        [
            ('speaker', 'clara'),
        ],
    )),

    ('ja', (
        "Japanese",
        False,
        [
            ('speaker', 'yuri'),
            ('speed', 2),
        ],
    )),

    ('zh', (
        "Chinese",
        True,
        [
            ('spk_id', 250),
        ],
    )),
]

VOICE_LOOKUP = dict(VOICE_CODES)


def _quote_all(input_string,
               *args, **kwargs):  # pylint:disable=unused-argument
    """NAVER Translate needs every character quoted."""
    return ''.join('%%%x' % ord(char) for char in input_string)


class Krdict(Service):
    """
    Provides a Service implementation for Krdict Translate
    (audio is still powered by Naver though).
    """

    __slots__ = []

    NAME = "NAVER Translate"

    TRAITS = [Trait.INTERNET]

    def desc(self):
        """Returns a static description."""

        return "NAVER Translate (%d voices)" % len(VOICE_CODES)

    def options(self):
        """Returns an option to select the voice."""

        return [
            dict(
                key='voice',
                label="Voice",
                values=[(key, description)
                        for key, (description, _, _) in VOICE_CODES],
                transform=lambda str: self.normalize(str)[0:2],
                default='ko',
            ),
        ]

    def extract_audio_url_from_html_response(self, word, html):
        """
        Extract audio url from HTML response of Krdict service.

        @param html: HTML text to search for audio in.
        @type html: str

        @return: URL is found, None otherwise.
        @rtype: str | None
        """
        soup = BeautifulSoup(html, 'html.parser', from_encoding="utf-8")
        # There should be at least one result, and we're interested in the
        # first result
        article0 = soup.find('li', {'id': 'article0'})
        if article0 is None:
            _logger.error('Krdict: Could not find article0')
            return None

        # Find 'a' tag to make sure it's exactly our word
        tag_a = article0.find('a')
        if tag_a is None:
            _logger.error('Krdict: Could not find tag a')
            return None

        # Check if this is exactly our word
        if tag_a.text != word:
            _logger.error('Krdict: Tag a does not contain the word')
            return None

        # 'img' tag should contain the URL to mp3
        tag_img = article0.find('img')
        if tag_img is None:
            _logger.error('Krdict: Could not find tag img')
            return None

        onclick_attr = tag_img['onclick']
        _logger.error('onclick_attr %s', onclick_attr)
        match = RX_MP3_URL.search(onclick_attr)
        if match is None:
            _logger.error('Krdict: Could not find mp3 url in img onclick text')
            return
        return match.group(0)

    def run(self, text, options, path):
        """Downloads from Internet directly to an MP3."""

        vcode = self.net_stream(
            (KRDIR_URL, dict(nation='eng',
                             nationCode=6,
                             ParaWordNo='',
                             mainSearchWord=text)),
            method='GET',)
        url = self.extract_audio_url_from_html_response(text, vcode)

        if url is not None:
            try:
                self.net_download(
                    path, (url, dict(),),
                    require=dict(mime='audio/mpeg', size=256),
                    custom_quoter=dict(text=_quote_all),)
                return True
            except HTTPError as e:
                _logger.error('Could not fetch url %s: %s', url, e)
        return None
