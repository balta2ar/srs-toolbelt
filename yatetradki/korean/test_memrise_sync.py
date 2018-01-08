import pytest
from collections import OrderedDict

from yatetradki.korean.memrise_sync import get_course_difference
from yatetradki.korean.memrise_sync import load_string_with_words
from yatetradki.korean.memrise_sync import WordPair

from yatetradki.korean.memrise_sync import DiffActionDeleteLevel
from yatetradki.korean.memrise_sync import DiffActionCreateLevel
from yatetradki.korean.memrise_sync import DiffActionDeleteWord
from yatetradki.korean.memrise_sync import DiffActionCreateWord
from yatetradki.korean.memrise_sync import DiffActionChangeLevel
from yatetradki.korean.memrise_sync import DiffActionChangeWord

from yatetradki.korean.memrise_sync import cleanup
from yatetradki.korean.memrise_sync import pretty_print_actions


class TestCleanup:
    def test_cleanup(self):
        assert cleanup(' word up ') == 'word up'
        assert cleanup('   무료;   【無料】    бесплатный   ') == \
            '무료; 【無料】 бесплатный'

class TestPrettyPrintDiffActions:
    def test_pretty_print(self):
        actions = [
            DiffActionCreateLevel('l1'),
            DiffActionChangeLevel('l1', 'l2'),
            DiffActionDeleteLevel('l1'),
            DiffActionCreateWord('l1', WordPair('w1', 'm1')),
            DiffActionChangeWord('l1', WordPair('w1', 'm1'), WordPair('w2', 'm2')),
            DiffActionDeleteWord('l1', WordPair('w1', 'm1')),
        ]
        expected = '''+#l1
*#l1 ===> #l2
-#l1
+w1; m1
*w1; m1 ===> w2; m2
-w1; m1'''
        assert pretty_print_actions(actions) == expected


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
