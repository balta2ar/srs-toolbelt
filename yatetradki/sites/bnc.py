from re import sub
from bs4 import BeautifulSoup
from requests import Session

from yatetradki.utils import text_cleanup
from yatetradki.types import BncWord


URL_BNC = u'http://bnc.bl.uk/saraWeb.php?qy={0}'


class BncSimpleSearch(object):
    _DUMMY = []

    def __init__(self):
        self._session = Session()

    def _remove_first_two_words(self, text):
        return sub(r'^\W*\w+\W+\w+\W*', '', text)

    def find(self, word):
        import logging
        logging.basicConfig(level=logging.DEBUG)
        responce = self._session.get(URL_BNC.format(word))
        soup = BeautifulSoup(responce.content)
        start = soup.find('div', {'id': 'solutions'})
        usages = start.findAll('p')[1:]
        usages = [self._remove_first_two_words(text_cleanup(x.text))
                  for x in usages]
        usages = sorted(usages, key=len)
        usages = usages or self._DUMMY
        return BncWord(usages)
