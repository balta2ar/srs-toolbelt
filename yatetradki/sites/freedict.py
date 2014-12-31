from bs4 import BeautifulSoup
from requests import Session
from collections import namedtuple

from yatetradki.utils import text_cleanup


URL_FREEDICT = u'http://www.thefreedictionary.com/{0}'


FreeDictWord = namedtuple('FreeDictWord', 'definitions')


class TheFreeDictionary(object):
    _DUMMY = FreeDictWord(['<NA>'])

    def __init__(self):
        self._session = Session()

    def find(self, word):
        responce = self._session.get(URL_FREEDICT.format(word))
        soup = BeautifulSoup(responce.content)

        try:
            start = soup.find('div', {'id': 'Definition'})
            defs = start.section.findAll('div',
                                         {'class': ['ds-list', 'ds-single']})
            defs = [text_cleanup(x.text) for x in defs]
            return FreeDictWord(defs)
        except AttributeError:
            return self._DUMMY
