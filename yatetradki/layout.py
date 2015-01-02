from io import StringIO
from textwrap import wrap
from itertools import izip
from itertools import izip_longest


NUM_DEFINITIONS = 3
NUM_USAGES = 3


class StraightLayout(object):
    """
    Knows the outline of the output, how to lay it out.
    Does not know about colors. Can generate layout for a single word.
    """
    def __init__(self, printer, width=0):
        self._printer = printer
        self._term_width = width

    def _build_token_table(self, tetradki_word, thesaurus_word):
        return {
            'langfrom': tetradki_word.langfrom,
            'langto': tetradki_word.langto,
            'wordfrom': tetradki_word.wordfrom,
            #'wordsto': u' | '.join(tetradki_word.wordsto),
            'synonym': 'syn',
            'antonym': 'ant',
            'space': ' ',
            'arrow': '->',
            'delimeter_first_line': '|',
            'delimeter_next_line': ':',
            'newline': '\n'
        }

    def _clip(self, relevant_words, max_length, convert=None):
        """
        Keep joining words until they exceed max_length. Return the numbers
        of words that when joind is smaller than max_length.
        """
        def _words(words):
            return [x.word for x in words]

        if convert is None:
            convert = _words

        words = convert(relevant_words)
        xs = filter(lambda (n, word): n < max_length,
                    [(len(u', '.join(words[:i + 1])), i + 1)
                     for i in range(len(relevant_words))])
        return relevant_words[:xs[-1][1]] if xs else [relevant_words[0]]

    def __call__(self, tetradki_word, thesaurus_word, freedict_word, bnc_word):
        # TODO: separate this into another class, leave helpers in base class
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
        p.spew('wordfrom', fmt=u'{0:15}')
        room = self._term_width - len('en -> ru | {0:15}'
                                      .format(tetradki_word.wordfrom))
        wordsto = self._clip(tetradki_word.wordsto, room, convert=lambda x: x)
        p.swallow(u', '.join([p.produce('wordsto', word) for word in wordsto]))
        p.spew('newline')

        spacing = '     '
        room = self._term_width - len(spacing) - len('syn : ')
        syns = self._clip(thesaurus_word.synonyms, room)
        ants = self._clip(thesaurus_word.antonyms, room)

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

        pads = ['     def : ', '           ']
        defs = self._wrap(freedict_word.definitions[:NUM_DEFINITIONS], room)
        self._produce_join_swallow('definition', pads, defs)
        p.spew('newline')

        pads = ['   usage : ', '           ']
        usages = self._wrap(bnc_word.usages[:NUM_USAGES], room)
        self._produce_join_swallow('usage', pads, usages)

        # we don't have information whether this word is the last,
        # so we don't know whether we sould print newline or not.
        # show command is suppose to know that info.
        # p.spew('newline')

        return p.getvalue()

    def _wrap(self, lines, limit):
        lines = [wrap(x, limit) for x in lines]
        # flatten list: http://stackoverflow.com/a/952946/258421
        return sum(lines, [])

    def _join_two_columns(self, left_rows, right_rows):
        # duplicate last item in left rows N times (N = len(right_rows)
        left_rows = left_rows + [left_rows[-1]] * len(right_rows)
        joined = u'\n'.join([u''.join([left, right])
                             for left, right in zip(left_rows, right_rows)])
        return joined

    def _produce_join_swallow(self, token, pads, items):
        p = self._printer
        items = [p.produce(token, x) for x in items]
        items = self._join_two_columns(pads, items)
        p.swallow(items)


class ColumnLayout(object):
    """
    Can layout generated words into columns. ATM requires both colored
    and raw version of words. Very inefficient.
    """
    def __init__(self, width, height, delimiter):
        self._width = width
        self._height = height
        self._delimeter = delimiter

        self._colored_columns = [StringIO()]
        self._raw_columns = [StringIO()]

    def _get_height(self, word):
        return len(word.splitlines())

    def __call__(self, colored_word, raw_word):
        # this method is called to add another word to column layout
        raw_column = self._raw_columns[-1]
        colored_column = self._colored_columns[-1]

        word_height = self._get_height(raw_word)
        current_height = self._get_height(raw_column.getvalue())
        if (self._height > 0) and (word_height + current_height + 1 > self._height):
            # start new column
            self._raw_columns.append(StringIO())
            self._colored_columns.append(StringIO())
            raw_column = self._raw_columns[-1]
            colored_column = self._colored_columns[-1]
            current_height = 0

        # put word into current column
        if current_height > 0:
            raw_column.write(u'\n\n')
            colored_column.write(u'\n\n')
        raw_column.write(raw_word)
        colored_column.write(colored_word)

    def getvalue(self):
        # generate a list of list of lines from all columns
        raw_lines = [x.getvalue().splitlines() for x in self._raw_columns]
        colored_lines = [x.getvalue().splitlines() for x in self._colored_columns]

        # same list of lists, but this time short columns are extended
        # with empty lines to match the long ones
        raw_lines = izip_longest(*raw_lines, fillvalue='')
        colored_lines = izip_longest(*colored_lines, fillvalue='')

        lines = []
        for raw, colored in izip(raw_lines, colored_lines):
            # determine how many spaces each line is missing
            spaces = [' ' * (self._width - len(x)) for x in raw]
            # fill colored line with remaning spaces
            filled_colored = [c + s for c, s in izip(colored, spaces)]
            # join short lines with delimeter get to full, wide line
            line = self._delimeter.join(filled_colored)
            lines.append(line)

        return u'\n'.join(lines)
