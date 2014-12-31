from textwrap import wrap


class LayoutProducer(object):
    """Knows the outline of the output, how to lay it out.
    Does not know about colors.
    """
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

    def __call__(self, tetradki_word, thesaurus_word, freedict_word, bnc_word):
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

        defs = [wrap(x, room) for x in freedict_word.definitions]
        defs = sum(defs, []) # flatten list: http://stackoverflow.com/a/952946/258421
        defs = [p.produce('definition', x) for x in defs]
        pads = ['     def : '] + ['           '] * len(defs)
        defs = u'\n'.join([u''.join([pad, defn])
                           for pad, defn in zip(pads, defs)])
        [p.swallow(x) for x in defs]
        p.spew('newline')

        usages = [wrap(x, room) for x in bnc_word.usages]
        usages = sum(usages, [])
        usages = [p.produce('usage', x) for x in usages]
        pads = ['   usage : '] + ['           '] * len(usages)
        usages = u'\n'.join([u''.join([pad, usage])
                             for pad, usage in zip(pads, usages)])
        [p.swallow(x) for x in usages]
        p.spew('newline')

        return self._printer.getvalue()
