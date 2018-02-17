from collections import defaultdict

from yatetradki.korean.memrise.types import WordCollection
from yatetradki.korean.memrise.types import WordPair
from yatetradki.korean.memrise.text import cleanup


MARK_COMMENT = '@'
MARK_LEVEL_NAME = '#'
# Google Docs inserts such marks
# BYTE_ORDER_MARK = '\xef\xbb\xbf'
BYTE_ORDER_MARK = '\ufeff'


def load_string_with_words(words_string):
    # key: level name
    # value: [(word, meaning)]
    words = WordCollection()
    current_level = None
    if words_string.startswith(BYTE_ORDER_MARK):
        words_string = words_string[len(BYTE_ORDER_MARK):]
    lines = words_string.split('\n')
    for line in (l.strip() for l in lines if l.strip()):
        if line.startswith(MARK_COMMENT):
            continue

        if line.startswith(MARK_LEVEL_NAME):
            line = line[1:].strip()
            current_level = line
            if current_level not in words:
                words[current_level] = []
            continue

        if current_level is None:
            raise ValueError('Please specify level name before any words')

        try:
            word, meaning = line.split(';', maxsplit=1)
        except ValueError as e:
            raise ValueError('Invalid line format, <word>;<meaning> '
                             'expected, got %s: %s' % (line, e))

        word = cleanup(word)
        meaning = cleanup(meaning)
        words[current_level].append(WordPair(word, meaning))

    return words


def load_file_with_words(filename):
    with open(filename) as file_:
        return load_string_with_words(file_.read())


class DuplicateWords:
    def __init__(self, words: WordCollection):
        pair = self._find_duplicates(words)
        self._duplicate_keys, self._duplicate_values = pair

    def _find_duplicates(self, words: WordCollection):
        keys = defaultdict(list)
        values = defaultdict(list)

        for _level_name, word_pairs in words.items():
            for pair in word_pairs:
                both = '%s; %s' % (pair.word, pair.meaning)
                keys[pair.word].append(both)
                values[pair.meaning].append(both)

        keys = {k: v for k, v in keys.items() if len(v) > 1}
        values = {k: v for k, v in values.items() if len(v) > 1}

        return keys, values

    def __len__(self):
        return len(self._duplicate_keys) + len(self._duplicate_values)

    def __str__(self):
        message = ''
        if self._duplicate_keys:
            message += '*** Duplicate keys found:\n'
            message += '\n'.join(sum(self._duplicate_keys.values(), []))
            message += '\n'

        if self._duplicate_values:
            message += '*** Duplicate values found:\n'
            message += '\n'.join(sum(self._duplicate_values.values(), []))
            message += '\n'

        return message
