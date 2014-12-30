# vim: set fileencoding=utf-8 :

from sys import exit
from argparse import ArgumentParser

from yatetradki.slovari import YandexSlovari
from yatetradki.thesaurus import Thesaurus
from yatetradki.pretty import Prettifier
from yatetradki.utils import load_colorscheme
from yatetradki.utils import get_terminal_width_fallback
from yatetradki.utils import load_credentials_from_netrc


COOKIE_JAR = 'cookiejar.dat'
NETRC_HOST = 'YandexSlovari'


def main():
    parser = ArgumentParser(
        description='Yandex.Slovari/Tetradki words extractor.')
    parser.add_argument('--login', type=str, default=None,
                        help='Login to Yandex')
    parser.add_argument('--password', type=str, default=None,
                        help='Password')
    parser.add_argument('--colors', type=str, default=None,
                        help='Path to colorscheme json')
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
    words = slovari.get_words()[-args.num_words:]

    thesaurus = Thesaurus(COOKIE_JAR)
    prettifier = Prettifier(load_colorscheme(args.colors),
                            get_terminal_width_fallback(args.width))

    for word in words:
        thes_word = thesaurus.find(word.wordfrom)
        print(prettifier(word, thes_word).encode('utf-8'))


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
    - read credentials from netrc
    - caching
        - download new words to file
        - download new syn&ant, usages, explanations to file
    - colorization (color tables)
    - usage (sample sentences, http://bnc.bl.uk/saraWeb.php?qy=gruesome)
    - explanation in English (http://www.thefreedictionary.com/gruesome)
    - all syn&ant groups (http://www.thesaurus.com/browse/intact?s=ts)
'''
