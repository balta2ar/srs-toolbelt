
LIMIT = 2
BR = u'<br>'
BR_EXAMPLES = u' :: '


def _limit(list_):
    return list_[:LIMIT]


class Anki(object):
    """
    Export SlovariWord into anki format. Supports both directions: en->ru,
    ru->en. Add part of speech, transcription, translation and usage examples.

    TODO: rewrite in a more clear, obvious way (front/back separation).
    """
    def __init__(self, word):
        self._word = word

    def _examples(self, examples, front):
        return [u'syn: {0}'.format(example.synonyms)
                if example.synonyms
                else u'{0}'.format(example.examplefrom if front
                                   else example.exampleto)
                for example in examples]

    def _entries(self, entries, front):
        back_newline = '' if front else BR
        return [u'{0}{1}{2}'.format(
            '' if front else '= ' + entry.wordto,
            back_newline + BR_EXAMPLES.join(self._examples(_limit(entry.examples), front)),
            BR)
            for entry in entries]

    def _groups(self, groups, front):
        return [u'({0}){1}{2}'.format(
            group.part_of_speech,
            BR,
            BR.join(self._entries(_limit(group.entries), front)))
            for group in groups]

    def __call__(self):
        groups = _limit(self._word.groups)
        transcription = self._word.transcription
        front = u'{0}{1}{2}{3}'.format(
            self._word.wordfrom.decode('utf8'),
            ' ' + transcription if transcription else '',
            BR,
            BR.join(self._groups(groups, front=True)))
        back = BR.join(self._groups(groups, front=False))
        return u'{0}\t{1}'.format(front, back)
