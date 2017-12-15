"""
This script synchronises given Memrise course (--course-url) with the given
text file (--filename).
"""

import logging
import netrc
from time import sleep
from collections import OrderedDict, namedtuple
from itertools import zip_longest
from typing import Tuple, List
# from enum import Enum, auto
from pprint import pformat

from selenium import webdriver
from selenium.webdriver.common.keys import Keys


FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.DEBUG)
_logger = logging.getLogger(__name__)


COMMENT = '@'


class WordCollection(OrderedDict):
    pass


WordPair = namedtuple('WordPair', 'word meaning')
DiffActionDeleteLevel = namedtuple('DiffActionDeleteLevel', 'level_name')
DiffActionCreateLevel = namedtuple('DiffActionCreateLevel', 'level_name')
DiffActionDeleteWord = namedtuple('DiffActionDeleteWord', 'level_name pair')
DiffActionCreateWord = namedtuple('DiffActionCreateWord', 'level_name pair')
DiffActionChangeLevel = namedtuple('DiffActionChangeLevel',
                                   'level_name new_level_name')
DiffActionChangeWord = namedtuple('DiffActionChangeWord',
                                  'level_name old_pair new_pair')


def get_words_difference(level_name: str,
                         course_level_words: List[WordPair],
                         file_level_words: List[WordPair]):
    actions = []
    for file_pair, course_pair \
            in zip_longest(file_level_words, course_level_words):

        # Present in file, missing in course
        if (file_pair is not None) and (course_pair is None):
            actions.append(DiffActionCreateWord(level_name, file_pair))

        # Missing in file, present in course
        elif (file_pair is None) and (course_pair is not None):
            course_word, _course_meaning = course_pair
            actions.append(DiffActionDeleteWord(
                level_name, course_word))

        # Equal?
        elif file_pair != course_pair:
            actions.append(DiffActionChangeWord(
                level_name, course_pair, file_pair))

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


def load_string_with_words(words_string):
    # key: level name
    # value: [(word, meaning)]
    words = WordCollection()
    current_level = None
    lines = words_string.split('\n')
    for line in (l.strip() for l in lines if l.strip()):
        if line.startswith(COMMENT):
            continue

        if line.startswith('#'):
            line = line[1:].strip()
            current_level = line
            words[current_level] = []
            continue

        if current_level is None:
            raise ValueError('Please specify level name before any words')

        try:
            word, meaning = line.split(';', maxsplit=1)
        except ValueError as e:
            raise ValueError('Invalid line format, <word>;<meaning> '
                             'expected, got %s: %s' % (line, e))

        word = word.strip()
        meaning = meaning.strip()
        words[current_level].append(WordPair(word, meaning))

    return words


def load_file_with_words(filename):
    with open(filename) as file_:
        return load_string_with_words(file_.read())


def read_credentials_from_netrc():
    rc = netrc.netrc()
    username, _account, password = rc.hosts['memrise']
    return username, password


class MemriseCourseSyncer:
    MEMRISE_LOGIN_PAGE = 'https://www.memrise.com/login/'

    def __init__(self, course_url, filename):
        self._course_url = course_url
        self._filename = filename
        self._driver = webdriver.Chrome()
        self._driver.implicitly_wait(10)

        self._levels = None

    def _login(self, username, password):
        self._driver.get(self.MEMRISE_LOGIN_PAGE)

        login_field = self._driver.find_element_by_xpath(
            '//*[@id="login"]/div[4]/input')
        login_field.send_keys(username)

        password_field = self._driver.find_element_by_xpath(
            '//*[@id="login"]/div[5]/input')
        password_field.send_keys(password)

        login_button = self._driver.find_element_by_xpath(
            '//*[@id="login"]/input[3]')
        login_button.click()

    def _add_new_level(self):
        pass

    def _rename_level(self):
        pass

    def _add_word(self, word, meaning):
        pass

    def _expand_all_levels(self):
        for level in self._levels:
            if level.collapsed:
                level.show_hide()

    @property
    def _file_words(self):
        return load_file_with_words(self._filename)

    @property
    def _course_words(self):
        return WordCollection([(level.name, level.words)
                              for level in self._levels])

    def _load_course(self):
        self._driver.get(self._course_url)

        # input('expand now')
        self._levels = Level.load_all(self._driver)
        self._expand_all_levels()
        sleep(2.0)

        self._levels = Level.load_all(self._driver)
        # for i, level in enumerate(self._levels):
        #     _logger.info('Level %s name "%s"', level.name, i)
        #     level.name = 'level_%s' % i
        #     _logger.info('Level %s name %s', level.name, i)

        # Expand non-exanded levels
        # Find current level names
        # For each level find all words

    def _apply_diff_actions(self, diff_actions):
        pass

    def sync(self):
        words = self._file_words
        _logger.info(pformat(words))

        username, password = read_credentials_from_netrc()
        self._login(username, password)

        self._load_course()
        diff_actions = get_course_difference(
            self._course_words,
            self._file_words)
        _logger.info('Applying difference: %s', diff_actions)

        self._apply_diff_actions(diff_actions)

        # return self._driver

        # input('wait')

class Level:
    CLASS_LEVEL = 'level'
    CLASS_LEVEL_NAME = 'level-name'
    CLASS_COLLAPSED = 'collapsed'
    # This class is used by a row of words
    CLASS_THING = 'thing'
    SELECTOR_SHOW_HIDE = '.show-hide.btn.btn-small'
    SELECTOR_CELL = '.cell.text.column'
    TAG_INPUT = 'input'

    def __init__(self, driver, index):
        self._driver = driver
        self._index = index

    @classmethod
    def load_all(cls, driver):
        elements = driver.find_elements_by_class_name(cls.CLASS_LEVEL)
        return [Level(driver, i)
                for i, element in enumerate(elements)]

    def element(self):
        elements = self._driver.find_elements_by_class_name(self.CLASS_LEVEL)
        return elements[self._index]

    def show_hide(self):
        button = self.element().find_element_by_css_selector(
            self.SELECTOR_SHOW_HIDE)
        button.click()

    @property
    def words(self):
        result = []
        things = self.element().find_elements_by_class_name(self.CLASS_THING)
        for thing in things:
            cells = thing.find_elements_by_css_selector(self.SELECTOR_CELL)
            word = cells[0].text
            meaning = cells[1].text
            result.append((word, meaning))
        return result

    @property
    def name(self):
        name = self.element().find_element_by_class_name(self.CLASS_LEVEL_NAME)
        return name.text

    @name.setter
    def name(self, value):
        name = self.element().find_element_by_class_name(self.CLASS_LEVEL_NAME)
        name.click()

        name = self.element().find_element_by_class_name(self.CLASS_LEVEL_NAME)
        input_field = name.find_element_by_tag_name(self.TAG_INPUT)
        input_field.clear()
        input_field.send_keys(value)
        input_field.send_keys(Keys.RETURN)

    @property
    def collapsed(self):
        class_ = self.element().get_attribute('class')
        return self.CLASS_COLLAPSED in class_


def interactive():
    url = 'https://www.memrise.com/course/1776472/bz-testing-course/edit/'
    filename = './sample.txt'
    syncer = MemriseCourseSyncer(url, filename)
    _logger.info('Starting sync...')
    syncer.sync()
    _logger.info('Sync has finished')
    return syncer


def main():
    interactive()


if __name__ == '__main__':
    main()
