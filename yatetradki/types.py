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
                        'tetradki_word slovari_word '
                        'thesaurus_word freedict_word bnc_word')

SlovariWord = namedtuple('SlovariWord', 'wordfrom transcription groups')
SlovariPartOfSpeechGroup = namedtuple('SlovariPartOfSpeechGroup',
                                      'part_of_speech entries')
SlovariEntryGroup = namedtuple('SlovariEntryGroup', 'wordto examples')
SlovariExample = namedtuple('SlovariExample',
                            'synonyms examplefrom exampleto')

PriberamWord = namedtuple('PriberamWord',
                          'wordfrom part_of_speech definitions synonims')

IdiomsTheFreeDictionaryWord = \
    namedtuple('IdiomsTheFreeDictionaryWord', 'wordfrom entries')
IdiomsTheFreeDictionaryEntry = \
    namedtuple('IdiomsTheFreeDictionaryEntry', 'phrase definitions')
IdiomsTheFreeDictionaryDefinition = \
    namedtuple('IdiomsTheFreeDictionaryDefinition', 'definition example')


def eval_word(string):
    return eval(string)
