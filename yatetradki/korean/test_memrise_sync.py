import pytest
from collections import OrderedDict

from memrise_sync import get_course_difference
from memrise_sync import load_string_with_words
from memrise_sync import WordPair

from memrise_sync import DiffActionDeleteLevel
from memrise_sync import DiffActionCreateLevel
from memrise_sync import DiffActionDeleteWord
from memrise_sync import DiffActionCreateWord
from memrise_sync import DiffActionChangeLevel
from memrise_sync import DiffActionChangeWord


class TestCourseDifference:
    def test_diff(self):
        course = load_string_with_words(
            '# Chapter 1\n'
            'word1;meaning1\n'
            '# Chapter 2\n'
            'word1;meaning1\n'
            'word2;meaning2\n'
            '# Chapter 3\n'
            'word1;\n')

        file_ = load_string_with_words(
            '# Chapter 1\n'
            'word1;meaning1\n'
            '# Chapter 2\n'
            'word1;meaning1\n'
            'word2;meaning2\n'
            '# Chapter 3\n'
            'word1;\n')
        assert get_course_difference(course, file_) == []

        file_ = load_string_with_words(
            '# Chapter 1\n'
            'word1;meaning1\n')
        assert get_course_difference(course, file_) == [
            DiffActionDeleteLevel('Chapter 2'),
            DiffActionDeleteLevel('Chapter 3')
        ]

        file_ = load_string_with_words(
            '# Chapter 1\n'
            'word1;meaning1\n')
        assert get_course_difference(course, file_) == [
            DiffActionDeleteLevel('Chapter 2'),
            DiffActionDeleteLevel('Chapter 3')
        ]

        file_ = load_string_with_words(
            '# Chapter 1.5\n'
            'word1.5;meaning1\n'
            'word2;meaning2\n'
            '# Chapter 2\n'
            'word1;meaning1\n'
            'word2;meaning2\n'
            '# Chapter 3\n'
            'word1;\n')
        assert get_course_difference(course, file_) == [
            DiffActionChangeLevel('Chapter 1', 'Chapter 1.5'),
            DiffActionChangeWord(
                'Chapter 1.5',
                WordPair('word1', 'meaning1'),
                WordPair('word1.5', 'meaning1')),
            DiffActionCreateWord('Chapter 1.5', WordPair('word2', 'meaning2'))
        ]

        # file_ = load_string_with_words(
        #     '# Chapter 1\n'
        #     'word1;meaning1\n'
        #     '# Chapter 2\n'
        #     'word1;meaning1\n'
        #     'word2;meaning2\n'
        #     '# Chapter 3\n'
        #     'word1;\n'
        #     '# Chapter 3\n'
        # )
        # print(get_course_difference(course, file_))
        # assert get_course_difference(course, file_) == [
        #     DiffActionCreateLevel('Chapter 3')
        # ]

        file_ = load_string_with_words(
            '# Chapter 1\n'
            'word1;meaning1\n'
            '# Chapter 2\n'
            'word1;meaning1\n'
            'word2;meaning2\n'
            '# Chapter 3\n'
            'word1;\n'
            '# Chapter 3\n'
            'word2;\n'
        )
        print(get_course_difference(course, file_))
        assert get_course_difference(course, file_) == [
            DiffActionCreateWord('Chapter 3', WordPair('word2', '')),
        ]
