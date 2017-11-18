#import codecs
#import io
from os import makedirs
from os.path import exists, basename, dirname, join
import re
from sys import stderr
import logging
import pickle
import fileinput
from argparse import ArgumentParser

from bs4 import BeautifulSoup

from yatetradki.reader.demangle_dsl import _clean_tags


FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.DEBUG)

SHORT_ARTICLE_LENGTH = 60
RE_SHORT_REFERENCE = re.compile(r'= (\w+)')
RE_REF_DICT = re.compile(r'\[ref dict="[^"]*"\]')
RE_A_HREF = re.compile(r'<a href="(\w+)">')
RE_SEE_OTHER = re.compile(r'^See (\w+).?$')
RUSSIAN_TRANSLATION = re.compile(u" — [\u0400-\u0500]+")
STR_MAIN_ENTRY = 'Main entry:'
STR_SEE_MAIN_ENTRY = 'See main entry: ↑'
EXAMPLES_PER_DICT = 3
MAX_ARTICLE_LEN = 100000


class DSLIndex(object):
    def __init__(self, dsl_reader, filename):

        self._index = dict()

        if exists(filename):
            with open(filename, 'rb') as index_file:
                self._index = pickle.load(index_file)
            # logging.info('Loaded %d entries from index file (%s)',
            #              len(self._index), filename)
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
        self._filename = filename
        self._file = open(filename, 'r', encoding='utf-16')
        self._index = DSLIndex(self, join('index', basename(filename) + '.index'))
        self._file.seek(0)

    def __repr__(self):
        return '%s(%s)' % (self.__class__, self._filename)

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

        header = ['<meta charset="utf-8">']
        article = []
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
                if article:
                    self._file.seek(pos)
                    # logging.info('Rewind and break')
                    break
                # we've just skipped a line and didn't accumulate arcticle
                # this means we've men an empty word, e.g. 'preeminence'
                # in En-En_American_Heritage_Dictionary.dsl

        return word.strip(), '\n'.join(header + article)

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
    text = BeautifulSoup(article, 'html.parser').text
    if text.startswith(STR_SEE_MAIN_ENTRY):
        referenced_word = text[len(STR_SEE_MAIN_ENTRY):].strip()
        logging.info('Detected reference from "%s" to "%s" (LongmanDOCE5)', word, referenced_word)
        return lookup_word(dsl_reader, referenced_word)

    # Special case for CambridgeAdvancedLearners
    main_entry_start = article.find(STR_MAIN_ENTRY)
    if main_entry_start != -1:
        article_rest = article[main_entry_start + len(STR_MAIN_ENTRY):]
        match = RE_A_HREF.search(article_rest)
        if match:
            referenced_word = match.group(1)
            if referenced_word != word:
                logging.info('Detected reference from "%s" to "%s" (CambridgeAdvancedLearners)', word, referenced_word)
                more_article, more_examples = lookup_word(dsl_reader, referenced_word)
                return article + more_article, more_examples

    # Special case for LingvoUniversal
    if len(text) < SHORT_ARTICLE_LENGTH:
        match = RE_SHORT_REFERENCE.search(text)
        if match:
            referenced_word = match.group(1)
            if word == referenced_word:
                logging.warning('Self reference from "%s" to "%s", skipping (LingvoUniversal)', word, referenced_word)
            else:
                logging.info('Detected reference from "%s" to "%s" (LingvoUniversal)', word, referenced_word)
                return lookup_word(dsl_reader, referenced_word)

    # Special case for En-En_American_Heritage_Dictionary.dsl
    match = RE_SEE_OTHER.search(text)
    if match:
        referenced_word = match.group(1)
        if referenced_word != word:
            logging.info('Detected reference from "%s" to "%s" (AmericanHeritageDictionary)', word, referenced_word)
            return lookup_word(dsl_reader, referenced_word)

    return article, None


def cleanup_article(article):
    article = article.replace('\t', ' ')
    article = article.replace('\n', '')
    article = RE_REF_DICT.sub('', article)
    return article


def strip_russian_translation(text):
    match = re.search(RUSSIAN_TRANSLATION, text)
    if match is not None:
        text = text[:match.start(0)]
    return text


def extract_examples(article):
    result = []
    soup = BeautifulSoup(article, 'html.parser')
    for tag in ('div', 'span'):
        for element in soup.findAll(tag, class_='sec ex'):
            text = strip_russian_translation(element.text.strip())
            if text:
                result.append(text)
    return result


def lookup_word(dsl_reader, word):
    article = dsl_reader.lookup(word)
    if article is None:
        return None, None

    # print(dsl_reader, file=stderr)
    # print(article, file=stderr)

    article = cleanup_article(article)
    article, _examples = check_reference(dsl_reader, word, article)

    # print('----------------', file=stderr)
    examples = None
    if article is not None:
        examples = extract_examples(article)
    # print('EXAMPLES', examples, file=stderr)

    return article, examples

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
        examples = []
        word = word.strip()
        for dsl_reader in dsl_readers:
            article, current_examples = lookup_word(dsl_reader, word)
            if article is not None:
                articles.append(article)
                examples.extend(current_examples[:EXAMPLES_PER_DICT])
                found = 1
        if found:
            articles = '<br>'.join(articles)
            articles = articles[:MAX_ARTICLE_LEN]
            examples = ''.join(['<li>%s</li>' % ex for ex in examples])
            if examples:
                examples = '<ul>%s</ul>' % examples
            print('%s\t%s\t%s' % (word, examples, articles))
            #print(examples, file=stderr)
            words_found += 1
        else:
            words_missing += 1
            # logging.info('Missing word: %s', word)

    logging.info('Found %d words, %d missing words, %d total',
                 words_found, words_missing, words_found + words_missing)


if __name__ == '__main__':
    main()
