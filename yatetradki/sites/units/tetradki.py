from json import loads
from bs4 import BeautifulSoup

from requests import Session
from requests.utils import dict_from_cookiejar
from requests.utils import cookiejar_from_dict
import logging

from pickle import load as pickle_load
from pickle import dump as pickle_dump

from yatetradki.utils import save
from yatetradki.types import TetradkiWord


_logger = logging.getLogger()


URL_COPYBOOKS = 'https://slovari.yandex.ru/'\
                '~%D1%82%D0%B5%D1%82%D1%80%D0%B0%D0%B4%D0%BA%D0%B8/0/'
URL_PART_PASSPORT = 'passport.yandex.ru/passport?mode=auth'
URL_PASSPORT = 'https://passport.yandex.ru/passport'


class YandexTetradki(object):
    """
    Fetch units (words) from yandex.tetradki site.
    """

    def __init__(self, login, password, cookies=None):
        self._login = login
        self._password = password
        self._session = Session()
        self._cookies = cookies

        if cookies is not None:
            try:
                with open(cookies) as f:
                    self._session.cookies = cookiejar_from_dict(pickle_load(f))
            except IOError:
                _logger.error('Could not load cookies from {0}'.format(self._cookies))

    def newest(self, n):
        words = self._get_words()
        words = words[-n:] if n else words
        return words

    def _get_words_page(self):
        response = self._session.get(URL_COPYBOOKS)
        passport_urls = self._get_urls_containing(
            response.content, URL_PART_PASSPORT)
        if len(passport_urls) == 1:
            response = self._auth(passport_urls[0])
        elif len(passport_urls) > 1:
            raise Exception('too many passport urls on the page, '
                            'dont know what to do')
        save(response.content.decode('utf8'))
        with open(self._cookies, 'w') as f:
            pickle_dump(dict_from_cookiejar(self._session.cookies), f)
        return response

    def _auth(self, url):
        _logger.debug('Authorizing at: %s' % url)
        params = {'mode': 'auth',
                  'msg': 'slovari',
                  'retpath': URL_COPYBOOKS}
        data = {'login': self._login,
                'passwd': self._password,
                'retpath': URL_COPYBOOKS}
        response = self._session.post(URL_PASSPORT,
                                      params=params,
                                      data=data,
                                      allow_redirects=True)
        _logger.debug(response.status_code, response.history)
        return response

    def _get_urls_containing(self, content, substring):
        soup = BeautifulSoup(content)
        links = [link.get('href') for link in soup.find_all('a')]
        valid = filter(lambda x: substring in x, filter(None, links))
        return valid

    def _clear_words(self, words):
        # 4 is wordsto
        return filter(lambda line: len(line[4]) < 200, words)

    def _export(self, words):
        return [TetradkiWord(*parts) for parts in words]

    def _split(self, words):
        """Split wordsto string into a list of words"""
        def _translate(parts):
            # 4 is wordsto
            parts[4] = parts[4].split(', ')
            return parts
        return map(_translate, words)

    def _get_words(self):
        page = self._get_words_page()
        soup = BeautifulSoup(page.content)
        dirty_words = filter(None,
                             [x.get('data-words')
                              for x in soup.find_all('div')])[0]
        # in page words are ordered oldest to newest (--but we return newest
        # first--)
        result = self._export(self._split(
            self._clear_words(loads(dirty_words))))
        #result.reverse()
        return result
