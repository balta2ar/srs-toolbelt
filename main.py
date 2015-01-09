# vim: set fileencoding=utf-8 :

from sys import exit
from argparse import ArgumentParser
from argparse import ArgumentDefaultsHelpFormatter

from yatetradki.command import fetch
from yatetradki.command import show
from yatetradki.command import words
from yatetradki.command import word


CACHE_FILE = 'cache.dat'
NUM_WORDS = 3


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
    parser_show.add_argument('--height', type=int, default=0,
                             help='Height of the output in characters')
    parser_show.add_argument('--numbers', default=False, action='store_true',
                             help='Show numbers on the left')
    parser_show.add_argument('--delim', type=str, default=' . ',
                             help='Columns delimiter')

    help = 'Show words in the cache'
    parser_words = subparsers.add_parser(
        'words', description=help, help=help,
        formatter_class=ArgumentDefaultsHelpFormatter)
    parser_words.add_argument('--cache', type=str, default=CACHE_FILE,
                              help='Path to cache file')

    help = 'Print only specified words'
    parser_word = subparsers.add_parser(
        'word', description=help, help=help,
        formatter_class=ArgumentDefaultsHelpFormatter)
    parser_word.add_argument('words', type=str, nargs='+',
                             help='List of words to print')
    parser_word.add_argument('--cache', type=str, default=CACHE_FILE,
                             help='Path to cache file')
    parser_word.add_argument('--colors', type=str, default=None,
                             help='Path to colorscheme json')
    parser_word.add_argument('--width', type=int, default=0,
                             help='Width of the output in characters')
    parser_word.add_argument('--height', type=int, default=0,
                             help='Height of the output in characters')
    parser_word.add_argument('--numbers', default=False, action='store_true',
                             help='Show numbers on the left')
    parser_word.add_argument('--delim', type=str, default=' . ',
                             help='Columns delimiter')

    return parser.parse_args()


def main():
    args = parse_args()
    dispatch = {
        'fetch': fetch,
        'show': show,
        'words': words,
        'word': word
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
    + caching
        + download new words to file
        + download new syn&ant, usages, explanations to file
    + colorization (color tables)
    + usage (sample sentences, http://bnc.bl.uk/saraWeb.php?qy=gruesome)
    + explanation in English (http://www.thefreedictionary.com/gruesome)
    - all syn&ant groups (http://www.thesaurus.com/browse/intact?s=ts)
    - network timeouts
    - columns
        + break long output into columns
        - limit number of columns (--num-columns, conflicts with --num-words)
        + break by words, not by lines
    + trim wordsto
    + draw N random definitions/usages, but save them all
    - smart merge order from slovari, do not replace current one

    - split into commands:
        + fetch (download from everywhere to local storage)
            - support word as arguments (what to do with order?)
        + show (pretty-print local storage)
            - support word as arguments (basically word command)
        - both: make them chainable, so that there could be third script
          that could easily execute them both. do I really need that?
        + words: print all words in the cache
        + word: print specified words
        - remove: remove word from order and cache
        - add: add word to order and cache
        - random: print N random words from cache

    - draw from different sources depending on the language of wordfrom
    - timeout per command
    - logging system, timestamps
    + shape up tokens:
        + def -> def (token)
        + usage -> usage (token)
        + usage-1 -> usage color
        + definition-1 -> definition color
        - delimeters (screw that, though)
    + do not print section if content is not available
        + syn, ant, def, usage
    - redesign layout generation system, current one is awful
'''
