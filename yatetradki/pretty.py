#from StringIO import StringIO
from io import StringIO

from yatetradki.utils import get_terminal_width


DEFUALT_WIDTH = 100


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


class Printer(object):
    """
    Has ref to:
        - token table
        - colorscheme table

    Know how to:
        - mix colors with content
    """
    def __init__(self, colorscheme=None):
        self._buffer = StringIO()
        self._colorscheme = colorscheme

    def setup(self, token_table):
        self._token_table = token_table

    def reset(self):
        self._buffer.close()
        self._buffer = StringIO()

    def produce(self, token, value=None, fmt=u'{0}', num=1):
        if value is None:
            value = self._token_table.get(token)
        if value is None:
            raise ValueError('Token {0} is missing from token table'
                             .format(token))
        return fmt.format(value) * num

    def swallow(self, text):
        self._buffer.write(text)

    def spew(self, token, value=None, fmt=u'{0}', num=1):
        self.swallow(self.produce(token, value, fmt, num))

    def getvalue(self):
        return self._buffer.getvalue()

    def _get_position(self):
        """TEMPORARILY NOT USED"""
        lines = self.getvalue().splitlines()
        if not len(lines):
            return 0, 0
        return len(lines), len(lines[-1])

    def get_column(self):
        """TEMPORARILY NOT USED"""
        _, col = self._get_position()
        return col

    def get_row(self):
        """TEMPORARILY NOT USED"""
        # TODO: this gets broken when colored printer is on
        row, _ = self._get_position()
        return row


class ColoredPrinter(Printer):
    def produce(self, token, value=None, fmt=u'{0}', num=1):
        result = super(ColoredPrinter, self).produce(
            token, value, fmt, num)
        color = self._colorscheme.get(token)
        if color is None:
            return result
        # On how to process escape sequences in strings, see:
        # http://stackoverflow.com/a/4020824/258421
        return unicode(color.decode('string_escape')).format(result)


class Producer(object):
    def __init__(self, printer, width=0):
        self._printer = printer
        self._term_width = width

    def _build_token_table(self, tetradki_word, thesaurus_word):
        return {
            'langfrom': tetradki_word.langfrom,
            'langto': tetradki_word.langto,
            'wordfrom': tetradki_word.wordfrom,
            'wordto': tetradki_word.wordto,
            'synonym': 'syn',
            'antonym': 'ant',
            'space': ' ',
            'arrow': '->',
            'delimeter_first_line': '|',
            'delimeter_next_line': ':',
            'newline': '\n'
        }

    def _clip(self, relevant_words, max_length):
        # yeah, well... this method is a little bit complicated
        def _words():
            return [x.word for x in relevant_words]

        xs = filter(lambda (n, word): n < max_length,
                    [(len(u', '.join(_words()[:i + 1])), i + 1)
                     for i in range(len(relevant_words))])
        return relevant_words[:xs[-1][1]] if xs else [relevant_words[0]]

    def __call__(self, tetradki_word, thesaurus_word):
        token_table = self._build_token_table(tetradki_word, thesaurus_word)

        self._printer.reset()
        self._printer.setup(token_table)
        p = self._printer

        p.spew('langfrom')
        p.spew('space')
        p.spew('arrow')
        p.spew('space')
        p.spew('langto')
        p.spew('space')
        p.spew('delimeter_first_line')
        p.spew('space')
        p.spew('wordfrom', fmt=u'{0:20}')
        p.spew('wordto')
        p.spew('newline')

        spacing = '     '
        syn_ant_width = self._term_width - len(spacing) - len('syn : ')
        syns = self._clip(thesaurus_word.synonyms, syn_ant_width)
        ants = self._clip(thesaurus_word.antonyms, syn_ant_width)

        p.spew('text', spacing)
        p.spew('synonym')
        p.spew('space')
        p.spew('delimeter_next_line')
        p.spew('space')
        p.swallow(u', '.join([p.produce('synonym-{0}'.format(relevance), word)
                              for word, relevance in syns]))
        p.spew('newline')

        p.spew('text', spacing)
        p.spew('antonym')
        p.spew('space')
        p.spew('delimeter_next_line')
        p.spew('space')
        p.swallow(u', '.join([p.produce('antonym-{0}'.format(relevance), word)
                              for word, relevance in ants]))
        p.spew('newline')

        return self._printer.getvalue()


class FancyWordPrinter(object):
    def __init__(self, colorscheme, width=0):
        self._colorscheme = colorscheme
        self._term_width = width
        if not width:
            _, width = get_terminal_width()
            self._term_width = width
            if not width:
                #print('Could not determine terminal size, using default {0}'
                #      .format(DEFUALT_WIDTH))
                self._term_width = DEFUALT_WIDTH

    def _clip(self, words, max_length):
        xs = filter(lambda x: len(x) < max_length,
                    [u', '.join(words[:i + 1])
                     for i in range(len(words))])
        return xs[-1] if xs else words[0]

    def __call__(self, tetradki_word, thesaurus_word):
        #printer = Printer(COLORSCHEME)

        #printer = ColoredPrinter(COLORSCHEME)
        printer = ColoredPrinter if self._colorscheme else Printer
        printer = printer(self._colorscheme)
        producer = Producer(printer, self._term_width)
        r = producer(tetradki_word, thesaurus_word)
        return r

        s = (u'{0} -> {1} | '
             .format(tetradki_word.langfrom, tetradki_word.langto))
        spacing = '     '
        syn_ant_width = self._term_width - len(spacing) - len('syn : ')
        s += u'{0:20} {1}\n'.format(tetradki_word.wordfrom,
                                    tetradki_word.wordto)
        syns = self._clip(thesaurus_word.synonyms, syn_ant_width)
        ants = self._clip(thesaurus_word.antonyms, syn_ant_width)
        s += (u'{spacing}syn : {0}\n{spacing}ant : {1}\n'
              .format(syns, ants, spacing=spacing))
        return s
