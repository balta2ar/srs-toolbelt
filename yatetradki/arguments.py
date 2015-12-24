from argparse import ArgumentParser
from argparse import ArgumentDefaultsHelpFormatter


CACHE_FILE = 'cache.dat'
NUM_WORDS = 3


def parse_args(args=None):
    parser = ArgumentParser(
        description='Yandex.Slovari/Tetradki words extractor.')
    subparsers = parser.add_subparsers(dest='command')

    help = 'Fetch only specified words'
    parser_fetch_word = subparsers.add_parser(
        'fetch_word', description=help, help=help,
        formatter_class=ArgumentDefaultsHelpFormatter)
    parser_fetch_word.add_argument('words', type=str, nargs='+',
                                   help='List of words to fetch')

    help = 'Fetch all words into cache'
    parser_fetch = subparsers.add_parser(
        'fetch', description=help, help=help,
        formatter_class=ArgumentDefaultsHelpFormatter)
    parser_fetch.add_argument('--cache', type=str, default=CACHE_FILE,
                              help='Path to cache file')
    parser_fetch.add_argument('--fetcher', type=str, default=None,
                              help='Name of the fetcher')
    parser_fetch.add_argument('--words-filename', type=str, default=None,
                              help='Grab list of units (words) from file')
    parser_fetch.add_argument('--num-words', type=int, default=NUM_WORDS,
                              help='Number of last words to fetch')
    parser_fetch.add_argument('--login', type=str, default=None,
                              help='Login to Yandex')
    parser_fetch.add_argument('--password', type=str, default=None,
                              help='Password')
    parser_fetch.add_argument('--jobs', type=int, default=5,
                              help='Number of parallel jobs')
    parser_fetch.add_argument('--timeout', type=float, default=30.0,
                              help='Timeout in seconds for word retrieve operation')

    help = 'Export words into another format'
    parser_export = subparsers.add_parser(
        'export', description=help, help=help,
        formatter_class=ArgumentDefaultsHelpFormatter)
    parser_export.add_argument('--cache', type=str, default=CACHE_FILE,
                               help='Path to cache file')
    parser_export.add_argument('--num-words', type=int, default=NUM_WORDS,
                               help='Number of last words to export')
    parser_export.add_argument('--formatter', type=str, default='Conky',
                               help='Class name of the formatter (see formatters directory)')
    parser_export.add_argument('--output', type=str, default=None,
                               help='Path to the output filename')

    help = 'Pretty print words in cache'
    parser_show = subparsers.add_parser(
        'show', description=help, help=help,
        formatter_class=ArgumentDefaultsHelpFormatter)
    parser_show.add_argument('--cache', type=str, default=CACHE_FILE,
                             help='Path to cache file')
    parser_show.add_argument('--num-words', type=int, default=NUM_WORDS,
                             help='Number of last words to print')
    parser_show.add_argument('--num-columns', type=int, default=0,
                             help='Number of columns (automatic fill)')
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

    return parser.parse_args(args)


