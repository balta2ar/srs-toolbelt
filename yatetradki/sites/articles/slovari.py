# vim: set fileencoding=utf-8 :
from bs4 import BeautifulSoup
from requests import get
#from urllib import quote_plus
from six.moves.urllib.parse import quote_plus
from jinja2 import Environment, FileSystemLoader
import logging

from yatetradki.types import SlovariWord
from yatetradki.types import SlovariPartOfSpeechGroup
from yatetradki.types import SlovariEntryGroup
from yatetradki.types import SlovariExample


_logger = logging.getLogger()


URL_SLOVARI = 'https://slovari.yandex.ru/{0}/en-ru/'


def as_dict(word):
    if isinstance(word, SlovariWord):
        return {
            'slovariword': {
                'wordfrom': word.wordfrom,
                'transcription': word.transcription,
                'groups': [as_dict(x) for x in word.groups]
            }
        }
    elif isinstance(word, SlovariPartOfSpeechGroup):
        return {
            'part_of_speech': word.part_of_speech,
            'entries': [as_dict(x) for x in word.entries]
        }
    elif isinstance(word, SlovariEntryGroup):
        return {
            'wordto': word.wordto,
            'examples': [as_dict(x) for x in word.examples]
        }
    elif isinstance(word, SlovariExample):
        return {
            'synomyms': word.synonyms,
            'examplefrom': word.examplefrom,
            'exampleto': word.exampleto
        }


def format_jinja2(word, straight_front, reversed_front, back):
    jinja_environment = Environment(loader=FileSystemLoader('templates'),
                                    trim_blocks=True)
    template_straight_front = jinja_environment.get_template(
        straight_front).render(slovariword=word)
    template_reversed_front = jinja_environment.get_template(
        reversed_front).render(slovariword=word)
    template_back = jinja_environment.get_template(
        back).render(slovariword=word)
    return template_straight_front, template_reversed_front, template_back


def save_json(basename, dict_data, data, filename):
    from json import dump
    from codecs import getwriter

    with open(filename + '.json', 'w') as file_object:
        wrapped = getwriter('utf-8')(file_object)
        dump(dict_data, wrapped, ensure_ascii=False, indent=4)

    template_front, template_back = format_jinja2(
        data, 'slovari/front.jinja2', 'slovari/back.jinja2')

    print(template_front)
    print('-' * 50)
    print(template_back)
    print('-' * 50)
    with open(filename + '.front.html', 'w') as file_object:
        wrapped = getwriter('utf-8')(file_object)
        wrapped.write(template_front)
    with open(filename + '.back.html', 'w') as file_object:
        wrapped = getwriter('utf-8')(file_object)
        wrapped.write(template_back)


# SlovariWord = namedtuple('SlovariWord', 'wordfrom transcription groups')
# SlovariPartOfSpeechGroup = namedtuple('SlovariPartOfSpeechGroup',
#                                       'part_of_speech entries')
# SlovariEntryGroup = namedtuple('SlovariEntryGroup', 'wordto examples')
# SlovariExample = namedtuple('SlovariExample',
#                             'synonyms examplefrom exampleto')


class YandexSlovari(object):
    """
    Extract article from YandexSlovari.
    """
    def _get_examples(self, entry):
        examples = entry.find_all('div', class_='b-translation__examples')
        for example in examples:
            synonym = example.find('span', class_='b-translation__synonym')
            if synonym:
                synonyms = example.text
                if synonyms.endswith('1'):
                    synonyms = synonyms[:-1]
                # print('SYNONYMS: %s' % synonyms)
                yield SlovariExample(synonyms, None, None)
            else:
                subexamples = example.find_all('div', class_='b-translation__example')
                for subexample in subexamples:
                    # left = example.find('span', 'b-translation__example-original').text
                    left = subexample.find('span', class_='b-translation__text')
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
        soup = BeautifulSoup(response.content, 'lxml')

        transcription = soup.find('span', class_='b-translation__tr')
        transcription = transcription.text if transcription else None
        # print('TRANSCRIPTION: %s' % transcription)

        # print('-----------------------------------------')
        # return SlovariWord(word, transcription, None)
        result = SlovariWord(word, transcription, list(self._get_groups(soup)))

        # save_json(word, as_dict(result), result, 'tetradki_dump/{0}'.format(word))

        return result

        # return response
