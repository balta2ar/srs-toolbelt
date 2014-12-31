# vim: set fileencoding=utf-8 :

from sys import exit
from argparse import ArgumentParser
from collections import namedtuple

from yatetradki.slovari import YandexSlovari
from yatetradki.thesaurus import Thesaurus
from yatetradki.freedict import TheFreeDictionary
from yatetradki.bnc import BncSimpleSearch
from yatetradki.pretty import Prettifier
from yatetradki.cache import Cache
from yatetradki.utils import load_colorscheme
from yatetradki.utils import get_terminal_width_fallback
from yatetradki.utils import load_credentials_from_netrc


COOKIE_JAR = 'cookiejar.dat'
NETRC_HOST = 'YandexSlovari'


CachedWord = namedtuple('CachedWord',
                        'tetradki_word thesaurus_word '
                        'freedict_word bnc_word')


def main():
    parser = ArgumentParser(
        description='Yandex.Slovari/Tetradki words extractor.')
    parser.add_argument('--login', type=str, default=None,
                        help='Login to Yandex')
    parser.add_argument('--password', type=str, default=None,
                        help='Password')
    parser.add_argument('--colors', type=str, default=None,
                        help='Path to colorscheme json')
    parser.add_argument('--cache', type=str, default=None,
                        help='Path to cache file (reduce network requests)')
    parser.add_argument('--num-words', type=int, default=10,
                        help='Number of last words to print')
    parser.add_argument('--width', type=int, default=0,
                        help='Width of the output in characters')
    args = parser.parse_args()

    if None in (args.login, args.password):
        login, password = load_credentials_from_netrc(NETRC_HOST)
        if None in (login, password):
            print('Please specify login and password')
            return 1
        args.login, args.password = login, password

    slovari = YandexSlovari(args.login, args.password, COOKIE_JAR)
    words = slovari.get_words()

    thesaurus = Thesaurus()
    freedict = TheFreeDictionary()
    bnc = BncSimpleSearch()
    prettifier = Prettifier(load_colorscheme(args.colors),
                            get_terminal_width_fallback(args.width))

    cache = Cache(args.cache)
    actual_words = words[-args.num_words:]

    for word in actual_words:
        if not cache.contains(word.wordfrom):
            thesaurus_word = thesaurus.find(word.wordfrom)
            freedict_word = freedict.find(word.wordfrom)
            bnc_word = bnc.find(word.wordfrom)
            cache.save(word.wordfrom, CachedWord(word,
                                                 thesaurus_word,
                                                 freedict_word,
                                                 bnc_word))

        cached_word = cache.load(word.wordfrom)
        print(prettifier(cached_word.tetradki_word,
                         cached_word.thesaurus_word,
                         cached_word.freedict_word,
                         cached_word.bnc_word).encode('utf-8'))

    cache.flush()


if __name__ == '__main__':
    exit(main())


'''
Things to implement

Usage:
    http://bnc.bl.uk/saraWeb.php?qy=gruesome

Thesaurus (synonims, antonims):
    http://www.thesaurus.com/browse/intact?s=ts

Many useful stuff:
    http://www.thefreedictionary.com/gruesome

No results from thesaurus: "no thesaurus results"

Sample output:

en -> ru | scrotum       мошонка       flawless perfect unblemished unbroken unharmed unhurt unscathed untouched
                                       broken damaged flawed harmed hurt imperfect injured

TODO:
    + read credentials from netrc
    - caching
        - download new words to file
        + download new syn&ant, usages, explanations to file
    + colorization (color tables)
    + usage (sample sentences, http://bnc.bl.uk/saraWeb.php?qy=gruesome)
    + explanation in English (http://www.thefreedictionary.com/gruesome)
    - all syn&ant groups (http://www.thesaurus.com/browse/intact?s=ts)
    - network timeouts
'''
