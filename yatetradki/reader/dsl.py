#import codecs
#import io
from os import makedirs
from os.path import exists, basename, dirname, join
import logging
import pickle
import fileinput
from argparse import ArgumentParser

from bs4 import BeautifulSoup

from yatetradki.reader.demangle_dsl import _clean_tags


FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.DEBUG)


class DSLIndex(object):
    def __init__(self, dsl_reader, filename):

        self._index = dict()

        if exists(filename):
            with open(filename, 'rb') as index_file:
                self._index = pickle.load(index_file)
            logging.info('Loaded %d entries from index file (%s)',
                         len(self._index), filename)
        else:
            logging.info('Indexing to file %s', filename)

            pos = dsl_reader._file.tell()
            dsl_reader._file.seek(0, 2)
            size = dsl_reader._file.tell()
            dsl_reader._file.seek(pos)
            logging.info('File size is %d', size)

            dsl_reader._read_header()
            last_percent = 0
            while True:
                pos = dsl_reader._file.tell()
                current_word, _article = dsl_reader._get_next_word(convert=False)
                if current_word is None: # eof
                    break
                self._index[current_word] = pos
                # if len(self._index) > 100:
                #     break
                percent = float(pos) / size * 100.
                # logging.info('word %s pos %s delta %s', current_word, pos, delta)
                if percent - last_percent > 5:
                    last_percent = percent
                    logging.info('Indexing... %%%d', percent)
            try:
                makedirs(dirname(filename))
            except OSError:
                pass

            with open(filename, 'wb') as index_file:
                pickle.dump(self._index, index_file)
            logging.info('Indexing done (%s)', filename)
        # from ipdb import set_trace; set_trace()

    def get_pos(self, word):
        return self._index.get(word)


class DSLReader(object):
    def __init__(self, filename):
        # self._file = io.TextIOWrapper(io.BufferedReader(io.open(
        #     filename, 'r', encoding='utf-16')))
        self._file = open(filename, 'r', encoding='utf-16')
        self._index = DSLIndex(self, join('index', basename(filename) + '.index'))
        self._file.seek(0)

    def _read_header(self):
        # logging.info('Reading header')
        while True:
            pos = self._file.tell()
            line = self._file.readline()
            if line.startswith('#'):
                continue # header
            elif len(line.strip()) == 0:
                continue # empty line delimiter
            else:
                #logging.error('Unexpected line: %s', line)
                self._file.seek(pos)
                break

    def _get_next_word(self, convert=True):
        # logging.info('Reading next word')
        word = self._file.readline()
        if len(word) == 0: # eof
            return None, None
        # logging.info('word %s', word.strip())

        article = ['<meta charset="utf-8">']
        while True:
            pos = self._file.tell()
            line = self._file.readline()
            # logging.info('line %s', line.strip())
            if len(line) == 0: # eof
                # logging.info('EOF')
                break
            elif line[0] in ' \t': # article line
                if convert:
                    line = _clean_tags(line.strip(), None)
                    article.append(line)
                # logging.info('Append')
            else: # start of the next article
                self._file.seek(pos)
                # logging.info('Rewind and break')
                break

        return word.strip(), '\n'.join(article)

    def _find_word(self, word):
        while True:
            current_word, article = self._get_next_word()
            # logging.info('Current word: %s', current_word)
            #if current_word.startswith(word):
            # if current_word.startswith(word):
            if word == current_word:
                return article
            elif current_word is None:
                logging.info('Could not find word "%s"', word)
                return None

    def lookup(self, word):
        self._file.seek(0, 0)
        self._read_header()
        # if self._index is not None:
        pos = self._index.get_pos(word)
        if pos is None:
            return None

        self._file.seek(pos)
        result = self._find_word(word)
        return result


def check_reference(dsl_reader, word, article):
    # Special case for articles in En-En-Longman_DOCE5.dsl
    reference_prefix = 'See main entry: ↑'

    text = BeautifulSoup(article, 'html.parser').text
    if text.startswith(reference_prefix):
        referenced_word = text[len(reference_prefix):].strip()
        logging.info('Detected reference from "%s" to "%s"', word, referenced_word)
        return lookup_word(dsl_reader, referenced_word)

    return article


def lookup_word(dsl_reader, word):
    article = dsl_reader.lookup(word)
    if article is None:
        return None

    article = article.replace('\t', ' ')
    article = article.replace('\n', '')

    return check_reference(dsl_reader, word, article)

def main():
    parser = ArgumentParser('Extract word articles from a DSL file')
    parser.add_argument('--dsl', dest='dsl', type=str, action='append',
                        help='path to a dsl dictionary file')
    args = parser.parse_args()

    #path = '/mnt/big_ntfs/distrib/lang/dictionaries/LDOCE5 for Lingvo/dsl/long-8.dsl'
    #path = '/mnt/big_ntfs/distrib/lang/dictionaries/LDOCE5 for Lingvo/dsl/En-En-Longman_DOCE5.dsl'
    dsl_readers = [DSLReader(dsl) for dsl in args.dsl]
    # print(dsl_reader.lookup('abrade'))
    words_found = 0
    words_missing = 0

    for word in fileinput.input('-'):
        found = 0
        articles = []
        word = word.strip()
        for dsl_reader in dsl_readers:
            article = lookup_word(dsl_reader, word)
            if article is not None:
                articles.append(article)
                found = 1
        if found:
            print('%s\t%s' % (word, '<br>'.join(articles)))
            words_found += 1
        else:
            words_missing += 1
            # logging.info('Missing word: %s', word)

    logging.info('Found %d words, %d missing words, %d total',
                 words_found, words_missing, words_found + words_missing)


if __name__ == '__main__':
    main()
