from json import loads
from bs4 import BeautifulSoup
from requests import Session
from operator import itemgetter

from yatetradki.types import ThesaurusWord
from yatetradki.types import RelevantWord


URL_THESAURUS = u'http://www.thesaurus.com/browse/{0}'


class Thesaurus(object):
    """
    Extract article from thesaurus.com.
    """
    _DUMMY = []

    def __init__(self):
        self._session = Session()

    def _parse_block(self, block):
        if not block:
            return self._DUMMY

        def _relevance(item):
            result = int(''.join(
                x for x in loads(item['data-category'])['name']
                if x.isdigit()))
            return result

        items = [x for x in block.find_all('a') if x.has_attr('data-length')]
        items = [(item.span.text, _relevance(item)) for item in items]
        items = map(lambda args: RelevantWord(*args),
                    sorted(items, key=itemgetter(1), reverse=True))
        return items if items else self._DUMMY

    def find(self, word):
        responce = self._session.get(URL_THESAURUS.format(word))
        soup = BeautifulSoup(responce.content)

        try:
            block = (soup.find('div', {'id': 'synonyms-0', 'class': 'synonyms'})
                     .find('div', {'class': 'relevancy-list'}))
            syn = self._parse_block(block)
        except AttributeError:
            syn = self._DUMMY

        try:
            block = (soup.find('div', {'id': 'synonyms-0', 'class': 'synonyms'})
                     .find('section', {'class': 'antonyms'}))
            ant = self._parse_block(block)
        except AttributeError:
            ant = self._DUMMY

        return ThesaurusWord(syn, ant)
