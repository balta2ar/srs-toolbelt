from bs4 import BeautifulSoup
from requests import get
# from urllib import quote_plus
from six.moves.urllib.parse import quote_plus
import re
import logging

from yatetradki.types import PriberamWord


_logger = logging.getLogger()


URL_WORD = 'http://priberam.pt/dlpo/{0}'
URL_SYNONIMS = 'http://www.priberam.pt/dlpo/async/Relacionadas.aspx?pal={0}&palID={1}'


class Priberam(object):
    """
    Extract article from priberam.pt.
    """
    def _get_synonyms(self, word, wordId):
        response = get(URL_SYNONIMS.format(word, wordId))
        soup = BeautifulSoup(response.content)
        return soup.text.split(', ')

    def find(self, word):
        response = get(URL_WORD.format(quote_plus(word)))
        soup = BeautifulSoup(response.content)

        resultados = soup.find('div', id='resultados')
        div = resultados.find().find_all('div')[5]

        varpts = div.find_all('span', class_='varpt')
        wordfrom = varpts[0].text
        part_of_speech = varpts[2].text
        defs = [p.text for p in div.find_all('p')]

        script = resultados.find('script').text
        wordId = re.search(r'verificaRelacionadasDef\((\d+)',
                           script).group(1)

        syns = self._get_synonyms(word, wordId)

        result = PriberamWord(wordfrom, part_of_speech, defs, syns)
        return result
