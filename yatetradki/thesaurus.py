from json import loads
from bs4 import BeautifulSoup
from requests import Session
from collections import namedtuple
from operator import itemgetter


URL_THESAURUS = 'http://www.thesaurus.com/browse/{0}'


ThesaurusWord = namedtuple('ThesaurusWord', 'synonyms antonyms')
RelevantWord = namedtuple('RelevantWord', 'word relevance')


class Thesaurus(object):
    def __init__(self, cookies=None):
        self.__cookies = cookies
        self._session = Session()

    def _parse_block(self, block):
        if not block:
            return [RelevantWord('<NA>', 0)]

        def _relevance(item):
            result = int(''.join(
                x for x in loads(item['data-category'])['name']
                if x.isdigit()))
            # print(item, result)
            return result

        items = [x for x in block.find_all('a') if x.has_attr('data-length')]
        items = [(item.span.text, _relevance(item)) for item in items]
        items = map(lambda args: RelevantWord(*args),
                    sorted(items, key=itemgetter(1), reverse=True))
        return items if items else [RelevantWord('<NA>', 0)]

    def find(self, word):
        responce = self._session.get(URL_THESAURUS.format(word))
        soup = BeautifulSoup(responce.content)
        block = (soup.find('div', {'id': 'synonyms-0', 'class': 'synonyms'})
                     .find('div', {'class': 'relevancy-list'}))
        syn = self._parse_block(block)
        block = (soup.find('div', {'id': 'synonyms-0', 'class': 'synonyms'})
                     .find('section', {'class': 'antonyms'}))
        ant = self._parse_block(block)
        return ThesaurusWord(syn, ant)
