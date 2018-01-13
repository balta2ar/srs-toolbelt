import logging

from contextlib import contextmanager
from pprint import pformat
from typing import Callable
from time import time, sleep
from functools import lru_cache
from urllib.parse import urlparse
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
# from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait as wait

from yatetradki.korean.memrise.types import WordCollection
from yatetradki.korean.memrise.types import WordPair
from yatetradki.korean.memrise.types import DiffActionCreateLevel
from yatetradki.korean.memrise.types import DiffActionChangeLevel
from yatetradki.korean.memrise.types import DiffActionDeleteLevel
from yatetradki.korean.memrise.types import DiffActionCreateWord
from yatetradki.korean.memrise.types import DiffActionChangeWord
from yatetradki.korean.memrise.types import DiffActionDeleteWord
from yatetradki.korean.memrise.injector import UserScriptInjector
from yatetradki.korean.memrise.io import read_credentials_from_netrc
from yatetradki.korean.memrise.io import get_page
from yatetradki.korean.memrise.words import load_file_with_words
from yatetradki.korean.memrise.words import DuplicateWords
from yatetradki.korean.memrise.diff import get_course_difference
from yatetradki.korean.memrise.action import contains_deletions
from yatetradki.korean.memrise.action import pretty_print_actions
from yatetradki.korean.memrise.text import cleanup
from yatetradki.korean.memrise.common import DEFAULT_LOG_LEVEL
from yatetradki.korean.memrise.common import DEFAULT_DRIVER_NAME
from yatetradki.korean.memrise.common import DEFAULT_LOGGER_NAME

UI_LARGE_DELAY = 3.0
UI_SMALL_DELAY = 1.0
UI_TINY_DELAY = 0.5
UI_MAX_IMPLICIT_TIMEOUT = 10.0
ADD_PRONUNCIATION_TIMEOUT = 10.0
BS_PARSER = 'html.parser'


_logger = logging.getLogger(DEFAULT_LOGGER_NAME)


def snooze(delay):
    _logger.info('Sleeping %s', delay)
    sleep(delay)


def _create_driver(driver_name):
    if driver_name == 'phantomjs':
        return webdriver.PhantomJS(
            service_args=['--ignore-ssl-errors=true'])
    elif driver_name == 'chrome':
        options = webdriver.ChromeOptions()
        options.add_argument('--ignore-certificate-errors')
        return webdriver.Chrome(chrome_options=options)
    else:
        raise ValueError('Unknown driver name "%s". Please only use '
                         '"phantomjs" or "chrome".' % driver_name)


@contextmanager
def without_implicit_wait(driver, old_delay):
    driver.implicitly_wait(0)
    try:
        yield
    finally:
        driver.implicitly_wait(old_delay)


class MemriseCourseSyncher:
    MEMRISE_LOGIN_PAGE = 'https://www.memrise.com/login/'
    PRONUNCIATION_KOREAN = 'korean'

    def __init__(self, filename, course_url, driver_name=DEFAULT_DRIVER_NAME):
        self._course_url = course_url
        self._filename = filename
        self._driver = _create_driver(driver_name)

        self._driver.implicitly_wait(UI_LARGE_DELAY)
        # self._driver.implicitly_wait(UI_TINY_DELAY)
        self._userscript_injector = UserScriptInjector(self._driver)

        self._course = EditableCourse(course_url, self._driver)

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

    @property
    def _file_word_pairs(self):
        return load_file_with_words(self._filename)

    def _apply_single_diff_action(self, action):
        _logger.info('Applying action: "%s"', action)

        if isinstance(action, DiffActionCreateLevel):
            self._course.create_level(action.level_name)

        elif isinstance(action, DiffActionChangeLevel):
            self._course.change_level(action.level_name, action.new_level_name)

        elif isinstance(action, DiffActionDeleteLevel):
            self._course.delete_level(action.level_name)

        elif isinstance(action, DiffActionCreateWord):
            self._course.create_word(action.level_name,
                                     action.pair.word,
                                     action.pair.meaning)

        elif isinstance(action, DiffActionChangeWord):
            self._course.change_word(action.level_name,
                                     action.old_pair.word,
                                     action.new_pair.word,
                                     action.new_pair.meaning)

        elif isinstance(action, DiffActionDeleteWord):
            self._course.delete_word(action.level_name,
                                     action.pair.word)

        else:
            _logger.error('Unknown action: %s', action)

    def _apply_diff_actions(self, diff_actions):
        for action in diff_actions:
            try:
                self._apply_single_diff_action(action)
            except AttributeError as e:
                _logger.exception('Diff action failed "%s": %s', action, e)

    def sync(self, pronunciation=None, only_log_changes=False,
             no_delete=False, no_duplicate=False, dry_run=False):
        if pronunciation not in (None, self.PRONUNCIATION_KOREAN):
            raise ValueError('Unsupported pronunciation: %s. Supported: %s' %
                             (pronunciation, self.PRONUNCIATION_KOREAN))

        _logger.info('Starting sync')

        username, password = read_credentials_from_netrc()
        _logger.info('Logging in')
        self._login(username, password)
        self._course.load()

        _logger.info('Calculating difference')
        diff_actions = get_course_difference(
            self._course.word_pairs,
            self._file_word_pairs)

        if diff_actions:
            # If we see changes and we would like to log them, make logging
            # level more verbose. We expect that if this option is set,
            # someone else had already set logging level to WARNING earlier.
            if only_log_changes:
                _logger.setLevel(DEFAULT_LOG_LEVEL)

                # Log current arguments because we couldn't have a chance before.
                _logger.info(
                    'Program arguments: driver="%s" '
                    'only_log_changes=%s pronunciation="%s" '
                    'filename="%s" course_url="%s"',
                    self._driver, only_log_changes, pronunciation,
                    self._filename, self._course_url)

            duplicates = DuplicateWords(self._file_word_pairs)
            if duplicates:
                _logger.warning('Found %s duplicates: %s',
                                len(duplicates), duplicates)
                if no_duplicate:
                    _logger.warning('Flag --no-duplicate is set and there are '
                                    'duplicates, thus terniating sync early...')
                    return

            _logger.info('%s actions to apply: %s',
                         len(diff_actions), pformat(diff_actions))
            _logger.info('Pretty printing actions: \n%s',
                         pretty_print_actions(diff_actions))
            if no_delete and contains_deletions(diff_actions):
                _logger.warning('Flag --no-delete is set and there are deletions '
                                'in the actions, thus teminating sync early...')
                return

            if dry_run:
                _logger.warning('Not applying actions because of --dry-run option')
            else:
                self._apply_diff_actions(diff_actions)

        if (pronunciation == self.PRONUNCIATION_KOREAN) and \
                self._userscript_injector.inject():
            # Wait a little before injected code adds buttons that should
            # be clicked.
            if dry_run:
                _logger.warning('Not adding pronunciation because of --dry-run option')
            else:
                snooze(UI_LARGE_DELAY)
                self._course.add_pronunciation()

        _logger.info('Sync has finished')


class ElementUnchangedWithin:
    def __init__(self, get_element, duration_ms):
        self._get_element = get_element
        self._duration_ms = duration_ms
        self._current_state = get_element()
        self._last_modified = time()

    def __call__(self):
        """
        :return: True if element has not been changed within the duration.
        :rtype: bool
        """
        new_state = self._get_element()
        now = time()
        if new_state != self._current_state:
            self._current_state = new_state
            self._last_modified = now
            return False

        diff = now - self._last_modified
        return diff > self._duration_ms


class WaitableWithDriver:
    """
    Adds several common helper methods that allow more convenient waiting on
    conditions.
    """
    def __init__(self):
        self._driver = None

    def _wait_condition(self, condition: Callable[[WebDriver], bool]):
        w = wait(self._driver, UI_MAX_IMPLICIT_TIMEOUT)
        return w.until(condition)

    def _element_missing(self, where, by):
        return not self._element_present(where, by)

    def _element_present(self, where, by):
        with without_implicit_wait(self._driver, UI_MAX_IMPLICIT_TIMEOUT):
            try:
                where.find_element(*by)
                return True
            except NoSuchElementException:
                return False

    def _element_changed(self,
                         old_element: WebElement,
                         get_new_element: Callable[[], WebElement]):
        return old_element != get_new_element()

    def _wait_element_present(self, where, by):
        self._wait_condition(
            lambda _driver: self._element_present(where, by))

    def _wait_element_missing(self, where, by):
        self._wait_condition(
            lambda _driver: self._element_missing(where, by))

    def _wait_element_unchanged_within(self, get_element, duration_ms):
        unchanged = ElementUnchangedWithin(get_element, duration_ms)
        self._wait_condition(lambda _driver: unchanged())

    def _wait_number_changed(self, initial_number, get_new_number):
        def _number_changed(_driver):
            return get_new_number() != initial_number

        w = wait(self._driver, UI_MAX_IMPLICIT_TIMEOUT)
        w.until(_number_changed)


class EditableCourse(WaitableWithDriver):
    TAG_A = 'a'
    SELECTOR_ADD_LEVEL_MENU = '.btn-group.pull-left'
    ID_HEADER = 'header'

    def __init__(self, course_url, driver):
        super().__init__()

        self.course_url = course_url

        self._driver = driver
        self._levels = None

    def add_pronunciation(self):
        for level in self._levels:
            level.add_pronunciation()

    def create_word(self, level_name, word, meaning):
        level = self.find_level(level_name)
        level.create_word(word, meaning)

    def change_word(self, level_name, old_word, new_word, new_meaning):
        level = self.find_level(level_name)
        level.change_word(old_word, new_word, new_meaning)

    def delete_word(self, level_name, word):
        level = self.find_level(level_name)
        level.delete_word(word)

    def _js_click(self, element):
        self._driver.execute_script('arguments[0].click();', element)

    @property
    def _last_level(self):
        return self._levels[-1]

    def _wait_level_count_changed(self, initial_level_count):
        self._wait_number_changed(initial_level_count, self._reload_levels)

    def _wait_level_created(self):
        # 1. Wait until new level appears.
        self._wait_level_count_changed(len(self._levels))

        # 2. Now wait until there is a tag with 'level-name' class.
        self._wait_condition(
            lambda _driver: self._last_level.level_name_present())

        # 3. Creating a new level actually reloads current page. But it's not
        # only that. Level header gets changed after a while after page reload.
        # Thus we need to wait until level header has NOT been been changed for
        # some period of time.
        self._wait_element_unchanged_within(
            self._last_level.header, UI_TINY_DELAY)

    def create_level(self, level_name):
        # We're using JavaScript-powered method to initiate click event
        # because a naive click() method will occasionally fail due to
        # site header covering "Add level" drop-down button. There is
        # _remove_header() helper, but even after calling it, the header
        # sometimes reappears so I've taught the script to add levels
        # independent of that annoying header.
        add_level_menu = self._driver.find_element_by_css_selector(
            self.SELECTOR_ADD_LEVEL_MENU)
        self._js_click(add_level_menu)

        li = add_level_menu.find_element_by_tag_name(self.TAG_A)
        self._js_click(li)

        # Wait a little before request reaches the server and UI updates.
        self._wait_level_created()

        # I noticed that after creating a level, header reappears (this is
        # because course page gets reloaded. So let's remove the header again.
        self._remove_header()

        self._reload_levels()
        self._levels[-1].name = level_name

    def change_level(self, old_level_name, new_level_name):
        self.find_level(old_level_name).name = new_level_name
        self._reload_levels()

    def delete_level(self, level_name):
        self.find_level(level_name).delete()
        self._reload_levels()

    def _expand_all_levels(self):
        for index, level in enumerate(self._levels):
            if level.collapsed:
                _logger.info('Expanding level %s. %s', index + 1, level.name)
                level.show_hide()

    @property
    def word_pairs(self):
        return WordCollection([(level.name, level.word_pairs)
                               for level in self._levels])

    def _remove_header(self):
        # This method is safe to call even if header is missing.
        self._driver.execute_script(
            'var header = document.getElementById(arguments[0]);'
            'if (header) header.parentNode.removeChild(header);',
            self.ID_HEADER)

    def load(self):
        self._driver.get(self.course_url)
        self._remove_header()

        self._reload_levels()
        self._expand_all_levels()
        _logger.info('Expanded all')

        self._reload_levels()

    def _reload_levels(self):
        self._levels = Level.load_all(self._driver)
        return len(self._levels)

    def find_level(self, name):
        for level in self._levels:
            if level.name == name:
                return level
        return None


class Level(WaitableWithDriver):
    CLASS_LEVEL = 'level'
    CLASS_LEVEL_NAME = 'level-name'
    CLASS_LEVEL_HEADER = 'level-header'
    CLASS_LEVEL_LOADING = 'level-loading'
    CLASS_COLLAPSED = 'collapsed'
    CLASS_ICO_PLUS = 'ico-plus'
    CLASS_ICO_CLOSE = 'ico-close'
    CLASS_ADDING = 'adding'
    CLASS_ADD_AUDIO = 'btn-bz-add-audio'
    # This class is used by a row of words
    CLASS_THING = 'thing'
    CLASS_TEXT = 'text'
    CLASS_LEVEL_ACTIONS = 'level-actions'
    CLASS_BTN = 'btn'
    SELECTOR_SHOW_HIDE = '.show-hide.btn.btn-small'
    SELECTOR_CELL = '.cell.text.column'
    SELECTOR_MODAL_YESNO = '#modal-yesno .btn-yes'
    TAG_INPUT = 'input'

    def __init__(self, driver, index):
        super().__init__()

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

    def header(self):
        return self._element().find_element_by_class_name(
            self.CLASS_LEVEL_HEADER)

    def level_name_present(self):
        by = (By.CLASS_NAME, self.CLASS_LEVEL_NAME)
        return self._element_present(self._element(), by)

    @property
    def _things(self):
        with without_implicit_wait(self._driver, UI_MAX_IMPLICIT_TIMEOUT):
            return self._element().find_elements_by_class_name(
                self.CLASS_THING)

    def _cells(self, thing):
        return thing.find_elements_by_css_selector(self.SELECTOR_CELL)

    def _find_thing(self, word):
        for thing in self._things:
            cells = self._cells(thing)
            if cells[0].text == word:
                return thing

        raise AttributeError('Cant find word "%s" in level "%s"' %
                             (word, self.name))

    def _find_add_audio_buttons(self):
        with without_implicit_wait(self._driver, UI_MAX_IMPLICIT_TIMEOUT):
            return self._element().find_elements_by_class_name(
                self.CLASS_ADD_AUDIO)

    def _wait_add_audio_button_count_changed(self, initial_count):
        try:
            self._wait_number_changed(
                initial_count,
                lambda: len(self._find_add_audio_buttons()))
            return True
        except TimeoutError:
            return False

    def add_pronunciation(self):
        _logger.info('Adding pronunciation to level %s', self.name)
        self.ensure_expanded()

        started = time()
        buttons = self._find_add_audio_buttons()
        while buttons:
            _logger.info('Clicking AddAudio button (%s more remains)',
                         len(buttons))
            first_button = buttons[0]
            first_button.click()

            if self._wait_add_audio_button_count_changed(len(buttons)):
                started = time()
            else:
                diff = time() - started
                if diff > ADD_PRONUNCIATION_TIMEOUT:
                    _logger.info('Timeout waiting for pronunciation at '
                                 'level %s', self.name)
                    break
            buttons = self._find_add_audio_buttons()

    def create_word(self, word, meaning):
        self.ensure_expanded()

        adding = self._element().find_element_by_class_name(self.CLASS_ADDING)
        input_fields = self._get_inputs(adding)
        self._set_input(input_fields[0], word, send_return=False)
        self._set_input(input_fields[1], meaning, send_return=False)
        adding.find_element_by_class_name(self.CLASS_ICO_PLUS).click()

        self._wait_word_present(word)

    def _text(self, element):
        return element.find_element_by_class_name(self.CLASS_TEXT)

    def _wait_word_present(self, word):
        self._wait_condition(lambda _driver: word in self.words_only)

    def change_word(self, old_word, new_word, new_meaning):
        self.ensure_expanded()

        thing = self._find_thing(old_word)
        cells = self._cells(thing)
        self._text(cells[0]).click()
        self._set_input(self._get_input(cells[0]), new_word)
        self._text(cells[1]).click()
        self._set_input(self._get_input(cells[1]), new_meaning)

        self._wait_word_present(new_word)

    def _wait_clickable(self, by):
        w = wait(self._driver, UI_MAX_IMPLICIT_TIMEOUT)
        return w.until(EC.element_to_be_clickable(by))

    def _wait_gone(self, by):
        w = wait(self._driver, UI_MAX_IMPLICIT_TIMEOUT)
        return w.until(lambda _driver: self._element_missing(self._driver, by))

    def delete_word(self, word):
        self.ensure_expanded()

        thing = self._find_thing(word)
        thing.find_element_by_class_name(self.CLASS_ICO_CLOSE).click()
        # Delay a little before the dialog pops up (animation).
        # Confirmation dialog shows up slowly, so we need large delay here.
        by = (By.CSS_SELECTOR, self.SELECTOR_MODAL_YESNO)
        self._wait_clickable(by).click()
        self._wait_gone(by)

    @property
    def words_only(self):
        return [pair.word for pair in self.word_pairs]

    @property
    def word_pairs(self):
        self.ensure_expanded()

        result = []
        for thing in self._things:
            cells = self._cells(thing)
            word = cleanup(cells[0].text)
            meaning = cleanup(cells[1].text)
            result.append(WordPair(word, meaning))
        return result

    def _get_inputs(self, element):
        return element.find_elements_by_tag_name(self.TAG_INPUT)

    def _get_input(self, element):
        return element.find_element_by_tag_name(self.TAG_INPUT)

    def _set_input(self, input_field, value, send_return=True):
        input_field.clear()
        input_field.send_keys(value)
        if send_return:
            # input_field.send_keys(Keys.RETURN)
            # Due to a bug, I send ENTER, not RETURN, see:
            # https://github.com/detro/ghostdriver/issues/249
            input_field.send_keys(Keys.ENTER)

    @property
    def id(self):
        return self._element().get_attribute('id')

    def _js_click(self, element):
        self._driver.execute_script('arguments[0].click();', element)

    @property
    def name(self):
        name = self._element().find_element_by_class_name(
            self.CLASS_LEVEL_NAME)
        return name.text

    @name.setter
    def name(self, value):
        name = self._element().find_element_by_class_name(
            self.CLASS_LEVEL_NAME)
        # name.click()
        self._js_click(name)

        by = (By.TAG_NAME, self.TAG_INPUT)
        self._wait_element_present(self.header(), by)
        self._set_input(self._get_input(self.header()), value)
        self._wait_element_missing(self.header(), by)

    @property
    def collapsed(self):
        """
        This method is not exact opposite of expanded because when we collapse
        level, <input> tag is not removed. Thus to consider the level to be
        collapsed, we only check the class.
        """
        class_ = self._element().get_attribute('class')
        return self.CLASS_COLLAPSED in class_

    @property
    def expanded(self):
        """
        Levels are lazy-loaded. Level becomes expanded when:
            1. "collapsed" class is gone
            2. AND <input> tag is added to the level.
        """
        by = (By.TAG_NAME, self.TAG_INPUT)
        input_present = self._element_present(self._element(), by)
        return (not self.collapsed) and input_present

    def _safe_expanded(self):
        """
        From my observations, Memrise after expanding a level reinserts
        the div that represents. Thus we should be ready to meet stale elements
        and retry in that case.
        """
        try:
            return self.expanded
        except StaleElementReferenceException:
            return False

    @property
    def _lazy_loaded(self) -> bool:
        """
        Levels are not fully loaded initially. Only the header is shown at
        first. When you click Show/Hide, level words are loaded.

        :return: True if the level has not been completely loaded yet.
        :rtype: bool
        """
        by = (By.CLASS_NAME, self.CLASS_LEVEL_LOADING)
        return self._element_present(self._element(), by)

    def show_hide(self):
        was_collapsed = self.collapsed
        lazy_loaded = self._lazy_loaded
        old_element = self._element()

        button = self._element().find_element_by_css_selector(
            self.SELECTOR_SHOW_HIDE)
        self._js_click(button)
        # button.click()

        if was_collapsed:
            self._wait_condition(lambda _driver: self._safe_expanded)

            if lazy_loaded:
                self._wait_condition(
                    lambda _driver: self._element_changed(
                        old_element,
                        self._element))

    def ensure_expanded(self):
        if self.collapsed:
            self.show_hide()

    def delete(self):
        level_id = self.id
        actions = self._element().find_element_by_class_name(
            self.CLASS_LEVEL_ACTIONS)
        buttons = actions.find_elements_by_class_name(self.CLASS_BTN)
        # Delete button is the last one in the row.
        delete_button = buttons[-1]
        # This first time we click the button, it turns red. You need to
        # click it two times to actually delete the course.
        # delete_button.click()
        # delete_button.click()
        self._js_click(delete_button)
        self._js_click(delete_button)
        # Wait for the animation to finish.
        by = (By.ID, level_id)
        self._wait_gone(by)


class ReadonlyCourse:
    def __init__(self, course_url):
        self._course_url = course_url
        self._body = get_page(course_url)

    def save_to_file(self, filename=None):
        if filename is None:
            filename = '%s.txt' % self.name
        _logger.info('Saving course %s to filename %s', self.name, filename)

        with open(filename, 'w') as file_:
            file_.write(str(self.word_pairs))

    def _make_level_url(self, short_level_url):
        parsed = urlparse(self._course_url)
        base = "%s://%s" % (parsed.scheme, parsed.netloc)
        return urljoin(base, short_level_url)

    @property
    @lru_cache()
    def name(self):
        soup = BeautifulSoup(self._body, BS_PARSER)
        return soup.select_one('h1.course-name').text.strip()

    @property
    @lru_cache()
    def word_pairs(self):
        _logger.info('Reading course %s (%s)', self.name, self._course_url)
        result = WordCollection()

        soup = BeautifulSoup(self._body, BS_PARSER)
        a_levels = soup.find_all('a', class_='level')
        for a_level in a_levels:
            href = self._make_level_url(a_level['href'])
            level = ReadonlyLevel(href)
            if not level.name in result:
                result[level.name] = []
            result[level.name].extend(level.word_pairs)

        return result


class ReadonlyLevel:
    def __init__(self, level_url):
        self._level_url = level_url
        self._body = get_page(level_url)

    @property
    @lru_cache()
    def name(self):
        soup = BeautifulSoup(self._body, BS_PARSER)
        infos = soup.find('div', class_='infos')
        return infos.find('h3', class_='progress-box-title').text.strip()

    @property
    @lru_cache()
    def word_pairs(self):
        _logger.info('Reading level %s (%s)', self.name, self._level_url)

        result = []

        soup = BeautifulSoup(self._body, BS_PARSER)
        things = soup.select('div.things div.thing')
        for thing in things:
            pair = WordPair(
                cleanup(thing.select_one('div.col_a.col.text').text),
                cleanup(thing.select_one('div.col_b.col.text').text))
            result.append(pair)

        return result
