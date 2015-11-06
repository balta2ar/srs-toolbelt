from bs4 import BeautifulSoup
from requests import get
from urllib import quote_plus
import logging

from yatetradki.types import SlovariWord
from yatetradki.types import SlovariPartOfSpeechGroup
from yatetradki.types import SlovariEntryGroup
from yatetradki.types import SlovariExample


_logger = logging.getLogger()


URL_SLOVARI = 'https://slovari.yandex.ru/{0}/en-ru/'


class YandexSlovari(object):
    """
    Extract article from YandexSlovari.
    """
    def _get_examples(self, entry):
        examples = entry.find_all('div', class_='b-translation__example')
        for example in examples:
            synomym = example.find('span', class_='b-translation__synonym')
            if synomym:
                synomyms = example.text
                # print('SYNONYMS: %s' % synomyms)
                yield SlovariExample(synomyms, None, None)
            else:
                # left = example.find('span', 'b-translation__example-original').text
                left = example.find('span', class_='b-translation__text')
                left_text = left.text
                right_text = left.find_next('span', class_='b-translation__text').text
                # print('EXAMPLES: %s -> %s' % (left_text, right_text))
                yield SlovariExample(None, left_text, right_text)

    def _get_entries(self, group):
        entries = group.find_all('li', class_='b-translation__entry')
        for entry in entries:
            words_to = entry.find(
                'span', class_='b-translation__translation-words').text
            # print('TRANSLATION: %s' % words_to)
            yield SlovariEntryGroup(words_to, list(self._get_examples(entry)))

    def _get_groups(self, soup):
        groups = soup.find_all('div', class_='b-translation__group')
        for group in groups:
            part_of_speech = group.find('h2')
            if not part_of_speech:
                continue

            part_of_speech = part_of_speech['id']
            # print('PART OF SPEECH: %s' % part_of_speech)
            yield SlovariPartOfSpeechGroup(
                part_of_speech, list(self._get_entries(group)))

    def find(self, word):
        response = get(URL_SLOVARI.format(quote_plus(word)))
        soup = BeautifulSoup(response.content)

        transcription = soup.find('span', class_='b-translation__tr')
        transcription = transcription.text if transcription else None
        # print('TRANSCRIPTION: %s' % transcription)

        # print('-----------------------------------------')
        # return SlovariWord(word, transcription, None)
        return SlovariWord(word, transcription, list(self._get_groups(soup)))

        # return response
