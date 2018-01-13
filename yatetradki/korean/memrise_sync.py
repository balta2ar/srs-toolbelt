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


import fire
import urllib3

from yatetradki.korean.memrise.model import MemriseCourseSyncher
from yatetradki.korean.memrise.model import ReadonlyCourse
from yatetradki.korean.memrise.injector import UserScriptInjector
from yatetradki.korean.memrise.common import DEFAULT_DRIVER_NAME
from yatetradki.korean.memrise.common import DEFAULT_LOG_LEVEL


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
logging.basicConfig(format=FORMAT, level=DEFAULT_LOG_LEVEL)
_logger = logging.getLogger(__name__)


SILENT_LOG_LEVEL = logging.ERROR


def interactive(filename=None):
    url = 'https://www.memrise.com/course/1776472/bz-testing-course/edit/'
    if filename is None:
        filename = './sample3.txt'
    syncher = MemriseCourseSyncher(filename, url)
    syncher.sync(pronunciation=MemriseCourseSyncher.PRONUNCIATION_KOREAN)
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

    def upload(self, filename, course_url, pronunciation=None,
               only_log_changes=False, no_delete=False,
               dry_run=False):
        """
        Upload contents of the given filename into the given course. Basically
        it synchronizes from filename to course. Note that you have to have
        edit access to the course.
        """
        if only_log_changes:
            _logger.setLevel(SILENT_LOG_LEVEL)

        syncher = MemriseCourseSyncher(filename, course_url, self.driver)
        syncher.sync(pronunciation=pronunciation,
                     only_log_changes=only_log_changes,
                     no_delete=no_delete,
                     dry_run=dry_run)

    def save(self, filename, course_url):
        """
        Saves given course into a given filename. You don't need edit access
        to do this operation.
        """
        course = ReadonlyCourse(course_url)
        print(pformat(course.word_pairs))
        course.save_to_file(filename)


# TODO: add checker for duplicates (levels, words, meanings)
def main():
    # interactive()
    fire.Fire(Runner)

if __name__ == '__main__':
    main()
