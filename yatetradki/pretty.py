from yatetradki.printer import Printer
from yatetradki.printer import ColoredPrinter
from yatetradki.producer import Producer


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
    def __init__(self, colorscheme, width):
        self._colorscheme = colorscheme
        self._term_width = width

    def __call__(self, tetradki_word, thesaurus_word):
        printer = ColoredPrinter if self._colorscheme else Printer
        printer = printer(self._colorscheme)
        producer = Producer(printer, self._term_width)
        return producer(tetradki_word, thesaurus_word)
