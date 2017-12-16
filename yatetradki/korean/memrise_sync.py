"""
This script synchronises given Memrise course (--course-url) with the given
text file (--filename).
"""

import logging
import netrc
from time import sleep
from collections import OrderedDict, namedtuple
from functools import partial
from itertools import zip_longest
from typing import Tuple, List
# from enum import Enum, auto
from pprint import pformat

from selenium import webdriver
from selenium.webdriver.common.keys import Keys


FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)
_logger = logging.getLogger(__name__)


COMMENT = '@'
UI_LARGE_DELAY = 3.0
UI_SMALL_DELAY = 1.0


class WordCollection(OrderedDict):
    pass


WordPair = namedtuple('WordPair', 'word meaning')
DiffActionCreateLevel = namedtuple('DiffActionCreateLevel', 'level_name')
DiffActionDeleteLevel = namedtuple('DiffActionDeleteLevel', 'level_name')
DiffActionChangeLevel = namedtuple('DiffActionChangeLevel',
                                   'level_name new_level_name')
DiffActionCreateWord = namedtuple('DiffActionCreateWord', 'level_name pair')
DiffActionDeleteWord = namedtuple('DiffActionDeleteWord', 'level_name pair')
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
            actions.append(DiffActionDeleteWord(
                level_name, course_pair))

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


def get_modal_dialog_yes(driver):
    dialog = driver.find_element_by_class_name('modal-dialog')
    return dialog.find_element_by_class_name('btn-yes')


# TODO: extract EditableCourse class from Syncer
# TODO: add ReadonlyCourse class
class MemriseCourseSyncer:
    MEMRISE_LOGIN_PAGE = 'https://www.memrise.com/login/'
    SELECTOR_ADD_LEVEL_MENU = '.btn-group.pull-left'
    CLASS_LI = 'li'

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

    def _create_level(self, level_name):
        add_level_menu = self._driver.find_element_by_css_selector(
            self.SELECTOR_ADD_LEVEL_MENU)
        add_level_menu.click()
        li = add_level_menu.find_element_by_tag_name(self.CLASS_LI)
        li.click()

        # Wait a little before request reaches the server and UI updates.
        sleep(UI_LARGE_DELAY)
        self._reload_levels()
        self._levels[-1].name = level_name

    def _change_level(self, old_level_name, new_level_name):
        self._find_level(old_level_name).name = new_level_name
        self._reload_levels()

    def _delete_level(self, level_name):
        self._find_level(level_name).delete()
        self._reload_levels()

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
        self._reload_levels()
        self._expand_all_levels()
        sleep(2.0)

        self._reload_levels()
        # for i, level in enumerate(self._levels):
        #     _logger.info('Level %s name "%s"', level.name, i)
        #     level.name = 'level_%s' % i
        #     _logger.info('Level %s name %s', level.name, i)

        # Expand non-exanded levels
        # Find current level names
        # For each level find all words

    def _reload_levels(self):
        self._levels = Level.load_all(self._driver)

    def _find_level(self, name):
        for level in self._levels:
            if level.name == name:
                return level
        return None

    def _apply_single_diff_action(self, action):
        level = self._find_level(action.level_name)
        _logger.info('Applying action: "%s"', action)

        if isinstance(action, DiffActionCreateLevel):
            self._create_level(action.level_name)

        elif isinstance(action, DiffActionChangeLevel):
            self._change_level(action.level_name, action.new_level_name)

        elif isinstance(action, DiffActionDeleteLevel):
            self._delete_level(action.level_name)

        elif isinstance(action, DiffActionCreateWord):
            level.create_word(action.pair.word, action.pair.meaning)

        elif isinstance(action, DiffActionChangeWord):
            level.change_word(action.old_pair.word,
                              action.new_pair.word,
                              action.new_pair.meaning)

        elif isinstance(action, DiffActionDeleteWord):
            level.delete_word(action.pair.word,
                              partial(get_modal_dialog_yes, self._driver))

        else:
            _logger.error('Unknown action: %s', action)

    def _apply_diff_actions(self, diff_actions):
        for action in diff_actions:
            try:
                self._apply_single_diff_action(action)
            except AttributeError as e:
                _logger.exception('Diff action failed "%s": %s', action, e)

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

        # self._apply_diff_actions(diff_actions)
        # return self._driver
        # input('wait')

class Level:
    CLASS_LEVEL = 'level'
    CLASS_LEVEL_NAME = 'level-name'
    CLASS_COLLAPSED = 'collapsed'
    CLASS_ICO_PLUS = 'ico-plus'
    CLASS_ICO_CLOSE = 'ico-close'
    CLASS_ADDING = 'adding'
    # This class is used by a row of words
    CLASS_THING = 'thing'
    CLASS_LEVEL_ACTIONS = 'level-actions'
    CLASS_BTN = 'btn'
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

    def _element(self):
        elements = self._driver.find_elements_by_class_name(self.CLASS_LEVEL)
        return elements[self._index]

    @property
    def _things(self):
        return self._element().find_elements_by_class_name(self.CLASS_THING)

    def _cells(self, thing):
        return thing.find_elements_by_css_selector(self.SELECTOR_CELL)

    def _find_thing(self, word):
        for thing in self._things:
            cells = self._cells(thing)
            if cells[0].text == word:
                return thing

        raise AttributeError('Cant find word "%s" in level "%s"' %
                             (word, self.name))

    def create_word(self, word, meaning):
        adding = self._element().find_element_by_class_name(self.CLASS_ADDING)
        input_fields = self._get_inputs(adding)
        self._set_input(input_fields[0], word, send_return=False)
        self._set_input(input_fields[1], meaning, send_return=False)
        adding.find_element_by_class_name(self.CLASS_ICO_PLUS).click()

    def delete_word(self, word, yes_button_finder):
        thing = self._find_thing(word)
        thing.find_element_by_class_name(self.CLASS_ICO_CLOSE).click()
        # Delay a little before the dialog pops up (animation)
        sleep(UI_LARGE_DELAY)
        yes_button_finder().click()

    def change_word(self, old_word, new_word, new_meaning):
        thing = self._find_thing(old_word)
        cells = self._cells(thing)
        cells[0].click()
        self._set_input(self._get_input(cells[0]), new_word)
        cells[1].click()
        self._set_input(self._get_input(cells[1]), new_meaning)

    def show_hide(self):
        button = self._element().find_element_by_css_selector(
            self.SELECTOR_SHOW_HIDE)
        button.click()
        sleep(UI_SMALL_DELAY)

    @property
    def words(self):
        result = []
        for thing in self._things:
            cells = self._cells(thing)
            word = cells[0].text
            meaning = cells[1].text
            result.append(WordPair(word, meaning))
        return result

    def _get_inputs(self, element):
        return element.find_elements_by_tag_name(self.TAG_INPUT)

    def _get_input(self, element):
        return element.find_element_by_tag_name(self.TAG_INPUT)

    def _set_input(self, input_field, value, send_return=True):
        # input_field = self._get_input(element)
        input_field.clear()
        input_field.send_keys(value)
        if send_return:
            input_field.send_keys(Keys.RETURN)

    @property
    def name(self):
        name = self._element().find_element_by_class_name(
            self.CLASS_LEVEL_NAME).text
        return name.text

    @name.setter
    def name(self, value):
        name = self._element().find_element_by_class_name(
            self.CLASS_LEVEL_NAME)
        name.click()

        name = self._element().find_element_by_class_name(
            self.CLASS_LEVEL_NAME)
        self._set_input(self._get_input(name), value)

    @property
    def collapsed(self):
        class_ = self._element().get_attribute('class')
        return self.CLASS_COLLAPSED in class_

    def delete(self):
        actions = self._element().find_element_by_class_name(
            self.CLASS_LEVEL_ACTIONS)
        buttons = actions.find_elements_by_class_name(self.CLASS_BTN)
        # Delete button is the last one in the row.
        delete_button = buttons[-1]
        # This first time we click the button, it turns red. You need to
        # click it two times to actually delete the course.
        delete_button.click()
        delete_button.click()
        # Wait for the animation to finish.
        sleep(UI_LARGE_DELAY)


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
