from itertools import zip_longest
from typing import List

from yatetradki.korean.memrise.types import WordCollection
from yatetradki.korean.memrise.types import WordPair
from yatetradki.korean.memrise.types import DiffActionCreateLevel
from yatetradki.korean.memrise.types import DiffActionChangeLevel
from yatetradki.korean.memrise.types import DiffActionDeleteLevel
from yatetradki.korean.memrise.types import DiffActionCreateWord
# from yatetradki.korean.memrise.types import DiffActionChangeWord
from yatetradki.korean.memrise.types import DiffActionChangeWordAt
from yatetradki.korean.memrise.types import DiffActionDeleteWord


def get_words_difference(level_name: str,
                         course_level_words: List[WordPair],
                         file_level_words: List[WordPair]):
    actions = []
    index = 0
    for file_pair, course_pair \
            in zip_longest(file_level_words, course_level_words):

        # Present in file, missing in course
        if (file_pair is not None) and (course_pair is None):
            actions.append(DiffActionCreateWord(level_name, file_pair))

        # Missing in file, present in course
        elif (file_pair is None) and (course_pair is not None):
            actions.append(DiffActionDeleteWord(
                level_name, course_pair))

        # Equal?
        elif file_pair != course_pair:
            actions.append(DiffActionChangeWordAt(
                level_name, index, course_pair, file_pair))

        index += 1

    return actions


def get_course_difference(course_words: WordCollection, file_words: WordCollection):
    actions = []
    for file_level, course_level in zip_longest(file_words, course_words):

        # Present in file, missing in course
        if (file_level is not None) and (course_level is None):
            actions.append(DiffActionCreateLevel(file_level))
            actions.extend(get_words_difference(
                file_level,
                [],
                file_words[file_level]))
            continue

        # Missing in file, present in course
        elif (file_level is None) and (course_level is not None):
            actions.append(DiffActionDeleteLevel(course_level))
            continue

        # Present everywhere. Equal?
        elif file_level != course_level:
            actions.append(DiffActionChangeLevel(course_level, file_level))

        actions.extend(get_words_difference(
            file_level,
            course_words[course_level],
            file_words[file_level]))

    return actions
