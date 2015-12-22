# vim: set fileencoding=utf-8 :
from bs4 import BeautifulSoup
from requests import get
#from urllib import quote_plus
from six.moves.urllib.parse import quote_plus
# from jinja2 import Environment, FileSystemLoader
from os.path import exists
import logging
from collections import defaultdict

from yatetradki.types import IdiomsTheFreeDictionaryWord
from yatetradki.types import IdiomsTheFreeDictionaryEntry
from yatetradki.types import IdiomsTheFreeDictionaryDefinition


_logger = logging.getLogger()


URL_IDIOMS = 'http://idioms.thefreedictionary.com/{0}'

SOURCES = [
    'MGH_Idi',
    'IdiI',
    'FarlexIdi',
    'MGH_Slang',
    'HM_Idi',
    'IdiA',
    'hm',
    'HM_PhrVerb',
    'SH_EndPhr'
]


class IdiomsTheFreeDictionary(object):
    def __init__(self):
        pass

    def _idia_non_illustrations(self, soup):
        results = []
        for item in soup.children:
            if not hasattr(item, 'attrs'):
                results.append(item.strip())
        return ' '.join(results).strip()

    def _expand_pseg(self, soup):
        children = list(soup.children)
        pseg = soup.find('div', class_='pseg')
        if pseg is not None:
            children.extend(list(pseg.children))
        return children

    def _get_data_src(self, data_src, soup):
        data = soup.find('section', attrs={'data-src': data_src})
        if data is None:
            return None
        phrases = defaultdict(list)
        phrase = None

        children = self._expand_pseg(data)
        for child in children:
            if child.name == 'h2':
                phrase = child.text.strip()
                continue
            elif hasattr(child, 'attrs'):
                if child.attrs.get('class', [None])[0] not in ('ds-single',
                                                               'ds-list'):
                    continue
            else:
                continue

            definition = self._idia_non_illustrations(child)
            example = ' '.join(
                [sentence.text.strip()
                 for sentence in child.find_all('span', class_='illustration')])
            phrases[phrase].append(
                IdiomsTheFreeDictionaryDefinition(definition, example))

        result = [IdiomsTheFreeDictionaryEntry(phrase_, definitions)
                  for phrase_, definitions in phrases.iteritems()]
        return result

    def find(self, word):
        filename = 'idioms_dump/{0}'.format(word)
        if not exists(filename):
            import time
            time.sleep(1.0)

            response = get(URL_IDIOMS.format(quote_plus(word)), timeout=5.0)
            with open(filename, 'w') as file_object:
                file_object.write(response.content)

        # This is just to download all idioms pages first
        # return None

        with open(filename) as file_object:
            content = file_object.read()

        entries = []
        soup = BeautifulSoup(content, 'lxml')

        num_added = 0
        for source in SOURCES:
            data_src = self._get_data_src(source, soup)
            if data_src is not None:
                entries.extend(data_src)
                num_added += 1
                # Only one description is enough
                if num_added >= 1:
                    break

        if not entries:
            print('Could not find anything in "{0}"'.format(word))
            return None

        return IdiomsTheFreeDictionaryWord(word.decode('utf8'), entries)
        #
        # transcription = soup.find('span', class_='b-translation__tr')
