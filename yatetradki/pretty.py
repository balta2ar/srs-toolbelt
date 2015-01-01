from yatetradki.printer import Printer
from yatetradki.printer import ColoredPrinter
from yatetradki.layout import StraightLayout
from yatetradki.layout import ColumnLayout


# Tokens:
#
# langfrom
# langto
# wordfrom
# wordto
# synonyms (list of max of 3 items)
# antonyms (list of max of 3 items)
# arrow
# delimeter_first_line
# delimeter_next_line
#
# Thesaurus provides relevancy information along with synonyms/antonyms, e.g.:
# data-category: {"name": "relevant--3"}


# TODO: add all tokens
TOKEN_LANGFROM = 'langfrom'


class Prettifier(object):
    """Compose printer and layour producer to get something pretty!"""
    def __init__(self, colorscheme, width, height, delimiter):
        self._colorscheme = colorscheme
        self._width = width
        self._height = height
        self._delimiter = delimiter

    def _print(self, colorscheme, cached_word):
        colored_printer = ColoredPrinter if colorscheme else Printer
        colored_printer = colored_printer(self._colorscheme)
        raw_printer = Printer(None)

        colored_producer = StraightLayout(colored_printer, self._width)
        colored_word = colored_producer(cached_word.tetradki_word,
                                        cached_word.thesaurus_word,
                                        cached_word.freedict_word,
                                        cached_word.bnc_word)

        raw_producer = StraightLayout(raw_printer, self._width)
        raw_word = raw_producer(cached_word.tetradki_word,
                                cached_word.thesaurus_word,
                                cached_word.freedict_word,
                                cached_word.bnc_word)

        return colored_word, raw_word

    def __call__(self, cached_words):
        column = ColumnLayout(self._width, self._height, self._delimiter)
        [column(*self._print(self._colorscheme, cached_word))
         for cached_word in cached_words]
        return column.getvalue()
