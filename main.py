# vim: set fileencoding=utf-8 :

from sys import exit
from argparse import ArgumentParser
from argparse import ArgumentDefaultsHelpFormatter
from collections import namedtuple

from yatetradki.sites.slovari import YandexSlovari
from yatetradki.sites.thesaurus import Thesaurus
from yatetradki.sites.freedict import TheFreeDictionary
from yatetradki.sites.bnc import BncSimpleSearch

from yatetradki.pretty import Prettifier
from yatetradki.cache import Cache
from yatetradki.utils import load_colorscheme
from yatetradki.utils import get_terminal_width_fallback
from yatetradki.utils import load_credentials_from_netrc


COOKIE_JAR = 'cookiejar.dat'
NETRC_HOST = 'YandexSlovari'
CACHE_FILE = 'cache.dat'
NUM_WORDS = 3


CachedWord = namedtuple('CachedWord',
                        'tetradki_word thesaurus_word '
                        'freedict_word bnc_word')


def parse_args():
    parser = ArgumentParser(
        description='Yandex.Slovari/Tetradki words extractor.')
    subparsers = parser.add_subparsers(dest='command')

    help = 'Fetch all words into cache'
    parser_fetch = subparsers.add_parser(
        'fetch', description=help, help=help,
        formatter_class=ArgumentDefaultsHelpFormatter)
    parser_fetch.add_argument('--cache', type=str, default=CACHE_FILE,
                              help='Path to cache file')
    parser_fetch.add_argument('--num-words', type=int, default=NUM_WORDS,
                              help='Number of last words to fetch')
    parser_fetch.add_argument('--login', type=str, default=None,
                              help='Login to Yandex')
    parser_fetch.add_argument('--password', type=str, default=None,
                              help='Password')

    help = 'Pretty print words in cache'
    parser_show = subparsers.add_parser(
        'show', description=help, help=help,
        formatter_class=ArgumentDefaultsHelpFormatter)
    parser_show.add_argument('--cache', type=str, default=CACHE_FILE,
                             help='Path to cache file')
    parser_show.add_argument('--num-words', type=int, default=NUM_WORDS,
                             help='Number of last words to print')
    parser_show.add_argument('--colors', type=str, default=None,
                             help='Path to colorscheme json')
    parser_show.add_argument('--width', type=int, default=0,
                             help='Width of the output in characters')

    return parser.parse_args()


def fetch(args):
    if None in (args.login, args.password):
        login, password = load_credentials_from_netrc(NETRC_HOST)
        if None in (login, password):
            print('Please specify login and password')
            return 1
        args.login, args.password = login, password

    cache = Cache(args.cache)

    slovari = YandexSlovari(args.login, args.password, COOKIE_JAR)
    words = slovari.get_words()
    words = words[-args.num_words:] if args.num_words else words

    thesaurus = Thesaurus()
    freedict = TheFreeDictionary()
    bnc = BncSimpleSearch()

    cache.order = [x.wordfrom for x in words]
    words_fetched = 0
    for i, word in enumerate(words):
        if not cache.contains(word.wordfrom):
            print('Fetching {0}/{1}: {2}'
                  .format(i + 1, len(words), word.wordfrom))
            thesaurus_word = thesaurus.find(word.wordfrom)
            freedict_word = freedict.find(word.wordfrom)
            bnc_word = bnc.find(word.wordfrom)
            cache.save(word.wordfrom, CachedWord(word,
                                                 thesaurus_word,
                                                 freedict_word,
                                                 bnc_word))
            words_fetched += 1

    cache.flush()
    if words_fetched:
        print('{0} new words fetched'.format(words_fetched))


def show(args):
    cache = Cache(args.cache)
    words = cache.order
    words = words[-args.num_words:] if args.num_words else words

    prettifier = Prettifier(load_colorscheme(args.colors),
                            get_terminal_width_fallback(args.width))

    for i, word in enumerate(words):
        cached_word = cache.load(word)
        print(prettifier(cached_word.tetradki_word,
                         cached_word.thesaurus_word,
                         cached_word.freedict_word,
                         cached_word.bnc_word).encode('utf-8'))


def main():
    args = parse_args()
    dispatch = {
        'fetch': fetch,
        'show': show
    }
    return dispatch[args.command](args)


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
    - break long output into columns
    - limit number of columns

    - split into two separate scripts:
        - fetch (download from everywhere to local storage)
        - print (pretty-print local storage into file)
        - make them chainable, so that there could be third script
          that could easily execute them both
'''
