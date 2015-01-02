from bs4 import BeautifulSoup
from requests import Session
from collections import namedtuple

from yatetradki.utils import text_cleanup


URL_BNC = u'http://bnc.bl.uk/saraWeb.php?qy={0}'


BncWord = namedtuple('BncWord', 'usages')


class BncSimpleSearch(object):
    _DUMMY = BncWord(['<NA>'])

    def __init__(self):
        self._session = Session()

    def find(self, word):
        responce = self._session.get(URL_BNC.format(word))
        soup = BeautifulSoup(responce.content)
        start = soup.find('div', {'id': 'solutions'})
        usages = start.findAll('p')[1:]
        usages = [text_cleanup(x.text) for x in usages]
        usages = sorted(usages, key=len)
        usages = usages or self._DUMMY
        return BncWord(usages)