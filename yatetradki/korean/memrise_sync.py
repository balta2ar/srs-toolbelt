r"""
This script synchronises given Memrise course (--course-url) with the given
text file (--filename).

Input text file should have the following format:

    # Level name 1
    @ this line is a comment and is ignored

    some word; meaning

    # Level name 2
    another word;meaning

Make sure all your level names are distinct. Duplicate level names are not
supported.

Sample usage:

    $ python ./memrise_sync.py save --filename WonGwan22Words-current.txt \
        --course-url 'https://www.memrise.com/course/1793248/wongwan-2-2-high-priority-bz-words/edit/'

    $ python ./memrise_sync.py --driver phantomjs upload \
        --only-log-changes=True --pronunciation korean \
        --filename WonGwan\ 2-2\ words.txt \
        --course-url 'https://www.memrise.com/course/1793248/wongwan-2-2-high-priority-bz-words/edit/'


"""

import logging
from pprint import pformat
from collections import namedtuple


import fire
import urllib3

from yatetradki.korean.memrise.model import MemriseCourseSyncher
from yatetradki.korean.memrise.model import ReadonlyCourse
from yatetradki.korean.memrise.injector import UserScriptInjector
from yatetradki.korean.memrise.common import DEFAULT_DRIVER_NAME
from yatetradki.korean.memrise.common import DEFAULT_LOG_LEVEL
from yatetradki.korean.memrise.common import DEFAULT_LOGGER_NAME
from yatetradki.korean.memrise.io import read_credentials_from_netrc
from yatetradki.korean.memrise.io import read_course_collection
from yatetradki.korean.memrise.telegram import read_telegram_notification_settings
from yatetradki.korean.memrise.telegram import start_session
from yatetradki.korean.memrise.telegram import finish_session


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
logging.basicConfig(format=FORMAT, level=DEFAULT_LOG_LEVEL)
_logger = logging.getLogger(DEFAULT_LOGGER_NAME)


SILENT_LOG_LEVEL = logging.ERROR
CoursePair = namedtuple('CoursePair', 'filename course_url')


def interactive(filename=None):
    url = 'https://www.memrise.com/course/1776472/bz-testing-course/edit/'
    if filename is None:
        filename = './sample3.txt'
    syncher = MemriseCourseSyncher()
    syncher.sync(filename, url, pronunciation=MemriseCourseSyncher.PRONUNCIATION_KOREAN)
    return syncher


def test_pronunciation():
    injector = UserScriptInjector(None)
    injector.inject()


def backup():
    course_url = 'https://www.memrise.com/course/1776472/bz-testing-course'
    course = ReadonlyCourse(course_url)
    # print(pformat(course.word_pairs))
    return course


class Runner:
    def __init__(self, log=None, driver=DEFAULT_DRIVER_NAME):
        self.log = log
        self.driver = driver

    def _validate_input(self, course_collection_filename, filename, course_url):
        if filename and course_url:
            return [CoursePair(filename, course_url)]
        elif course_collection_filename:
            return [CoursePair(filename, course_url)
                    for filename, course_url in read_course_collection(
                        course_collection_filename)]
        else:
            _logger.info('Invalid parameters: either use --course-collection-filename '
                         'argument with a path to yaml file or use both '
                         '--filename and --course-url')
            return None

    def upload(self, course_collection_filename=None,
               filename=None, course_url=None,
               pronunciation=None,
               only_log_changes=False, no_delete=True,
               no_duplicate=True, dry_run=False):
        """
        Upload contents of the given filename into the given course. Basically
        it synchronizes from filename to course. Note that you have to have
        edit access to the course.
        """
        if only_log_changes:
            _logger.setLevel(SILENT_LOG_LEVEL)

        courses = self._validate_input(course_collection_filename, filename, course_url)
        if not courses:
            return

        start_session()
        _logger.info('%d courses to sync', len(courses))

        username, password = read_credentials_from_netrc()
        syncher = MemriseCourseSyncher(self.driver)
        _logger.info('Logging in')
        syncher.login(username, password)

        for course_pair in courses:
            syncher.sync(filename=course_pair.filename,
                         course_url=course_pair.course_url,
                         pronunciation=pronunciation,
                         only_log_changes=only_log_changes,
                         no_delete=no_delete,
                         no_duplicate=no_duplicate,
                         dry_run=dry_run)

        _logger.info('Finished syncing %d courses', len(courses))

        telegram_settings = read_telegram_notification_settings(course_collection_filename)
        if telegram_settings is not None:
            _logger.info('Trying to send a notification to telegram')
            # finish_session(telegram_settings)

    def save(self, filename, course_url):
        """
        Saves given course into a given filename. You don't need edit access
        to do this operation.
        """
        course = ReadonlyCourse(course_url)
        print(pformat(course.word_pairs))
        course.save_to_file(filename)


def main():
    # interactive()
    fire.Fire(Runner)

if __name__ == '__main__':
    main()
