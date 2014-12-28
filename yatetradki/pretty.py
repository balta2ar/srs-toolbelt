from yatetradki.utils import get_terminal_width


DEFUALT_WIDTH = 100


class FancyWordPrinter(object):
    def __init__(self, width=0):
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
