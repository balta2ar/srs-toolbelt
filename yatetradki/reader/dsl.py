#import codecs
#import io
from os import makedirs
from os.path import exists, basename, dirname, join, expanduser, expandvars
import re
import logging
import pickle
import fileinput
from argparse import ArgumentParser
from multiprocessing import Pool

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


class DSLRawReader(object):
    def __init__(self, filename, encoding='utf-16',
                 article_header='<meta charset="utf-8">'):
        self._filename = filename
        self._article_header = [article_header]

        self._file = open(filename, 'r', encoding=encoding)
        self._file.seek(0)

    def __repr__(self):
        return '%s(%s)' % (self.__class__, self._filename)

    @property
    def filename(self):
        return self._filename

    def tell(self):
        return self._file.tell()

    def seek(self, offset, from_what=0):
        return self._file.seek(offset, from_what)

    def __len__(self):
        pos = self.tell()
        self.seek(0, 2)
        size = self.tell()
        self.seek(pos)
        return size

    def read_header(self):
        while True:
            pos = self._file.tell()
            line = self._file.readline()
            if line == '':
                # unexpected EOF
                break
            elif line.startswith('#'):
                continue # header
            elif len(line.strip()) == 0:
                continue # empty line delimiter
            else:
                self._file.seek(pos)
                break

    def _skip_until_article_or_eof(self):
        initial_pos = self._file.tell()
        while True:
            saved_pos = self._file.tell()
            line = self._file.readline()
            if line == '': # eof
                break
            if line[0] in ' \t': # article body
                self._file.seek(saved_pos)
                break
        return initial_pos != self._file.tell()

    def _read_article_lines(self, convert=True):
        lines = []
        while True:
            saved_pos = self._file.tell()
            line = self._file.readline()
            if line == '': # eof
                break
            elif line[0] in ' \t': # article body
                if convert:
                    line = _clean_tags(line.strip(), None)
                lines.append(line)
            else:
                # we've reached next word title, probably
                self._file.seek(saved_pos)
                break
        return lines

    def get_next_word(self, convert=True):
        word = self._file.readline()
        if word == '': # eof
            return None, None

        saved_pos = self._file.tell()
        skipped_anything = self._skip_until_article_or_eof()
        article = self._read_article_lines(convert)
        if skipped_anything:
            self._file.seek(saved_pos)

        # Be cautious that words may contain multiple titles, e.g.:
        # En-En_American_Heritage_Dictionary.dsl:
        # 'preeminence', 'preeminently'
        # 'predominately', 'predomination', 'predominator'
        # 'Eurocentrism', 'Eurocentrist'
        #

        article = '\n'.join(self._article_header + article)
        return word.strip(), article


class DSLIndexer(object):
    def __init__(self, filename, dsl_raw_reader):

        self._index = dict()

        if exists(filename):
            with open(filename, 'rb') as index_file:
                self._index = pickle.load(index_file)
            return

        size = len(dsl_raw_reader)
        logging.info('Indexing to file %s (dict size %s)', filename, size)
        base_filename = basename(filename)

        dsl_raw_reader.read_header()
        last_percent = 0
        while True:
            pos = dsl_raw_reader.tell()
            current_word, _article = dsl_raw_reader.get_next_word(convert=False)
            if current_word is None: # eof
                break
            self._index[current_word] = pos
            percent = float(pos) / size * 100.
            if percent - last_percent > 10:
                last_percent = percent
                logging.info('Indexing %s... %%%d', base_filename, percent)

        try:
            makedirs(dirname(filename))
        except OSError:
            pass

        with open(filename, 'wb') as index_file:
            pickle.dump(self._index, index_file)
        logging.info('Indexing done (%s entries, %s)',
                     len(self._index), filename)

    def __len__(self):
        return len(self._index)

    def get_pos(self, word):
        return self._index.get(word)


class DSLLookuper(object):
    def __init__(self, filename, dsl_raw_reader=None, dsl_indexer=None):
        self._filename = filename

        self._dsl_raw_reader = dsl_raw_reader
        if self._dsl_raw_reader is None:
            self._dsl_raw_reader = DSLRawReader(filename)

        self._dsl_indexer = dsl_indexer
        if self._dsl_indexer is None:
            index_path = expanduser(expandvars('~/.cache/dsl_index/'))
            index_path = join(index_path, basename(filename) + '.index')
            self._dsl_indexer = DSLIndexer(index_path, self._dsl_raw_reader)

        self._dsl_raw_reader.seek(0)

    def __repr__(self):
        return '%s(%s)' % (self.__class__, self._filename)

    def _find_word(self, word):
        while True:
            current_word, article = self._dsl_raw_reader.get_next_word()
            if word == current_word:
                return article
            elif current_word is None:
                logging.info('Could not find word "%s"', word)
                return None

    def lookup(self, word):
        self._dsl_raw_reader.seek(0, 0)
        self._dsl_raw_reader.read_header()
        pos = self._dsl_indexer.get_pos(word)
        if pos is None:
            return None

        self._dsl_raw_reader.seek(pos)
        result = self._find_word(word)
        return result


def check_reference(dsl_lookuper, word, article, depth):
    # Special case for articles in En-En-Longman_DOCE5.dsl
    text = BeautifulSoup(article, 'html.parser').text
    if text.startswith(STR_SEE_MAIN_ENTRY):
        referenced_word = text[len(STR_SEE_MAIN_ENTRY):].strip()
        logging.info('Detected reference from "%s" to "%s" (LongmanDOCE5)', word, referenced_word)
        return lookup_word(dsl_lookuper, referenced_word, depth)

    # Special case for CambridgeAdvancedLearners
    main_entry_start = article.find(STR_MAIN_ENTRY)
    if main_entry_start != -1:
        article_rest = article[main_entry_start + len(STR_MAIN_ENTRY):]
        match = RE_A_HREF.search(article_rest)
        if match:
            referenced_word = match.group(1)
            if referenced_word != word:
                logging.info('Detected reference from "%s" to "%s" (CambridgeAdvancedLearners)', word, referenced_word)
                more_article, more_examples = lookup_word(dsl_lookuper, referenced_word, depth)
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
                return lookup_word(dsl_lookuper, referenced_word, depth)

    # Special case for En-En_American_Heritage_Dictionary.dsl
    match = RE_SEE_OTHER.search(text)
    if match:
        referenced_word = match.group(1)
        if referenced_word != word:
            logging.info('Detected reference from "%s" to "%s" (AmericanHeritageDictionary)', word, referenced_word)
            return lookup_word(dsl_lookuper, referenced_word, depth)

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


def strip_dots(text):
    return text.strip('.')


def extract_examples(article):
    result = []
    soup = BeautifulSoup(article, 'html.parser')
    for tag in ('div', 'span'):
        for element in soup.findAll(tag, class_='sec ex'):
            text = strip_russian_translation(element.text.strip())
            text = strip_dots(text)
            if text:
                result.append(text)
    return result


def lookup_word(dsl_lookuper, word):
    article = dsl_lookuper.lookup(word)
    if article is None:
        return None, None

    # print(dsl_lookuper, file=stderr)
    # print(article, file=stderr)

    article = cleanup_article(article)
    article, _examples = check_reference(dsl_lookuper, word, article, depth-1)

    # print('----------------', file=stderr)
    examples = None
    if article is not None:
        examples = extract_examples(article)
    # print('EXAMPLES', examples, file=stderr)

    return article, examples


def _init_index(filename):
    """
    It does not work if this function is a closure. Keep it on
    the module level.
    """
    DSLLookuper(filename)


def _ensure_indexes_present(dsl_filenames):
    """
    This functions is only called for its side effects. It creates DSLLookupers
    for each DSL file in parallel processes to make user DSLIndexers are also
    created in parallel.
    """
    with Pool(processes=None) as pool:
        pool.map(_init_index, dsl_filenames)


def _uniq_at(current_chunk, all_words):
    uniq = set(current_chunk) - set(all_words)
    return [word for word in current_chunk if word in uniq]


def main():
    parser = ArgumentParser('Extract word articles from a DSL file')
    parser.add_argument('--dsl', dest='dsl', type=str, action='append',
                        help='path to a dsl dictionary file')
    args = parser.parse_args()

    #path = '/mnt/big_ntfs/distrib/lang/dictionaries/LDOCE5 for Lingvo/dsl/long-8.dsl'
    #path = '/mnt/big_ntfs/distrib/lang/dictionaries/LDOCE5 for Lingvo/dsl/En-En-Longman_DOCE5.dsl'
    _ensure_indexes_present(args.dsl)
    dsl_lookupers = [DSLLookuper(dsl) for dsl in args.dsl]
    # print(dsl_reader.lookup('abrade'))
    words_found = 0
    words_missing = 0

    for word in fileinput.input('-'):
        found = 0
        articles = []
        examples = []
        word = word.strip()
        for dsl_reader in dsl_lookupers:
            depth = 5
            article, current_examples = lookup_word(dsl_reader, word, depth)
            if article is not None:
                articles.append(article)
                uniq_examples = _uniq_at(current_examples, examples)
                examples.extend(uniq_examples[:EXAMPLES_PER_DICT])
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
