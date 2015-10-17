# coding=utf8
"""
This module contains all word types in one place.
"""

from collections import namedtuple


ThesaurusWord = namedtuple('ThesaurusWord', 'synonyms antonyms')
RelevantWord = namedtuple('RelevantWord', 'word relevance')

BncWord = namedtuple('BncWord', 'usages')

FreeDictWord = namedtuple('FreeDictWord', 'definitions')

TetradkiWord = namedtuple('TetradkiWord',
                          'langfrom langto hash wordfrom wordsto dictionary')

CachedWord = namedtuple('CachedWord',
                        'tetradki_word thesaurus_word '
                        'freedict_word bnc_word')


# def namedtuple_str(obj):
#     encoded_fields = []
#     for field in obj._fields:
#         value = getattr(obj, field)
#         encoded_value = value
#         if isinstance(value, unicode):
#             encoded_value = "u'" + value.encode('utf8') + "'"
#         elif isinstance(value, basestring):
#             encoded_value = "'" + value + "'"
#         encoded_fields.append('%s=%s' % (field, encoded_value))
#
#     return '%s(%s)' % (obj.__class__.__name__, ', '.join(encoded_fields))


SlovariWord = namedtuple('SlovariWord', 'wordfrom transcription groups')

# SlovariWord.__str__ = namedtuple_str
# namedtuple.__str__ = namedtuple_str

SlovariPartOfSpeechGroup = namedtuple('PartOfSpeechGroup',
                                      'part_of_speech entries')
SlovariEntryGroup = namedtuple('EntryGroup', 'wordto examples')
SlovariExample = namedtuple('SlovariExample',
                            'synonyms examplefrom exampleto')


def eval_word(string):
    return eval(string)
