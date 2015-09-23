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
