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
        #syn = 'pb-relacionadas-words-list'
        return soup.text.split(', ')

    def find(self, word):
        response = get(URL_WORD.format(quote_plus(word)))
        soup = BeautifulSoup(response.content)

        # from ipdb import set_trace; set_trace()
        resultados = soup.find('div', id='resultados')

        #div = resultados.find().find_all('div')[5]
        #varpts = div.find_all('span', class_='varpt')
        #wordfrom = varpts[0].text
        #part_of_speech = varpts[2].text
        definitions = [p.text for p in resultados.find_all('p')]
        part_of_speech = u', '.join(
            [part.text
             for part in resultados.find_all('categoria_ext_aao')])
        #part_of_speech = u'{0}'.format(part_of_speech)

        script = resultados.find('script').text
        wordId = re.search(r'verificaRelacionadasDef\((\d+)',
                           script).group(1)

        synonims = self._get_synonyms(word, wordId)
        result = PriberamWord(word.decode('utf8'),
                              part_of_speech, definitions, synonims)
        return result
