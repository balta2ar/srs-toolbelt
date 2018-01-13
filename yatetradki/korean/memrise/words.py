from yatetradki.korean.memrise.types import WordCollection
from yatetradki.korean.memrise.types import WordPair
from yatetradki.korean.memrise.text import cleanup


MARK_COMMENT = '@'
MARK_LEVEL_NAME = '#'


def load_string_with_words(words_string):
    # key: level name
    # value: [(word, meaning)]
    words = WordCollection()
    current_level = None
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