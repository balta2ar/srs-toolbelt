# vim: set fileencoding=utf-8 :

from sys import exit
from argparse import ArgumentParser

# from yatetradki.utils import enable_debug
from yatetradki.slovari import YandexSlovari


COOKIE_JAR = 'cookiejar.dat'


def print_words(words):
    for word in words:
        print(u'{0} -> {1} | {2:20} {3}'
              .format(word.langfrom, word.langto, word.wordfrom, word.wordto))


def main():
    parser = ArgumentParser(description='Yandex.Slovari/Tetradki words extractor.')
    parser.add_argument('--login', type=str, default=None, help='Login to Yandex')
    parser.add_argument('--password', type=str, default=None, help='Password')
    args = parser.parse_args()

    if None in (args.login, args.password):
        print('Please specify login and password')
        return 1

    slovari = YandexSlovari(args.login, args.password, COOKIE_JAR)
    print_words(slovari.get_words()[-10:])


if __name__ == '__main__':
    exit(main())


'''
Things to implement

Usage:
    http://bnc.bl.uk/saraWeb.php?qy=gruesome

Thesaurus:
    http://www.thesaurus.com/browse/intact?s=ts

http://www.thefreedictionary.com/gruesome

No results from thesaurus: "no thesaurus results"

Sample output:

en -> ru | scrotum       мошонка       flawless perfect unblemished unbroken unharmed unhurt unscathed untouched
                                       broken damaged flawed harmed hurt imperfect injured

'''
