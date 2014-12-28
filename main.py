# vim: set fileencoding=utf-8 :

from sys import exit
from argparse import ArgumentParser

from yatetradki.slovari import YandexSlovari
from yatetradki.thesaurus import Thesaurus
from yatetradki.pretty import FancyWordPrinter


COOKIE_JAR = 'cookiejar.dat'


def main():
    parser = ArgumentParser(
        description='Yandex.Slovari/Tetradki words extractor.')
    parser.add_argument('--login', type=str, default=None,
                        help='Login to Yandex')
    parser.add_argument('--password', type=str, default=None,
                        help='Password')
    parser.add_argument('--num-words', type=int, default=10,
                        help='Number of last words to print')
    parser.add_argument('--width', type=int, default=0,
                        help='Width of the output in characters')
    args = parser.parse_args()

    if None in (args.login, args.password):
        print('Please specify login and password')
        return 1

    slovari = YandexSlovari(args.login, args.password, COOKIE_JAR)
    words = slovari.get_words()[-args.num_words:]

    thesaurus = Thesaurus(COOKIE_JAR)
    printer = FancyWordPrinter(args.width)

    for word in words:
        thes_word = thesaurus.find(word.wordfrom)
        print(printer(word, thes_word).encode('utf-8'))


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

'''
