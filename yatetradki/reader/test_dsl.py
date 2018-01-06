from unittest import TestCase
from os.path import join
from tempfile import TemporaryDirectory

from yatetradki.reader.dsl import DSLRawReader, DSLIndexer, DSLLookuper


HEADER = '''#NAME   "Test"
#INDEX_LANGUAGE "English"
#CONTENTS_LANGUAGE      "Spanish"
'''


def spit(data, filename, encoding=None):
    with open(filename, 'w', encoding=encoding) as file_:
        file_.write(data)


def slurp(filename, encoding=None):
    with open(filename, encoding=encoding) as file_:
        return file_.read()


class ContentReader:
    def __init__(self):
        self.dsl_raw_reader = None
        self.dsl_indexer = None
        self.dsl_lookuper = None

    def __call__(self, dsl_contents):
        pairs = []
        encoding = 'utf-8'
        with TemporaryDirectory() as dir_:
            dsl_name = join(dir_, 'testdict.dsl')
            index_name = join(dir_, 'testdict.dsl.index')
            spit(dsl_contents, dsl_name, encoding=encoding)

            dsl_raw_reader = DSLRawReader(dsl_name, encoding=encoding,
                                          article_header='')
            dsl_indexer = DSLIndexer(index_name, dsl_raw_reader)
            dsl_lookuper = DSLLookuper(dsl_name, dsl_raw_reader, dsl_indexer)

            self.dsl_raw_reader = dsl_raw_reader
            self.dsl_indexer = dsl_indexer
            self.dsl_lookuper = dsl_lookuper

            dsl_raw_reader.read_header()
            word, article = dsl_raw_reader.get_next_word()
            while word is not None and article is not None:
                pairs.append((word, article))
                word, article = dsl_raw_reader.get_next_word()

        return pairs


def decorate(pairs):
    """
    dsl_demangle.py adds some HTML decoratins to the output DSL contents. Let's
    add them here for testing purposes as well.
    """
    new_pairs = []
    for word, article in pairs:
        new_word = word
        lines = article.split('\n')
        lines = ['\n<div style="margin-left:1em">%s</div>' % article
                 for article in lines]
        new_article = ''.join(lines)
        new_pairs.append((new_word, new_article))
    return new_pairs


def assert_contents(contents, expected):
    decorated = decorate(expected)
    reader = ContentReader()
    assert decorated == reader(contents)
    assert len(expected) == len(reader.dsl_indexer)
    for word, article in decorated:
        assert article == reader.dsl_lookuper.lookup(word)


class TestDslReader:
    def test_multi_title_words(self):
        contents = HEADER + '''
word1
word11
	article1
word2
word21
word22
	article2
'''
        expected = [
            ('word1', 'article1'),
            ('word11', 'article1'),
            ('word2', 'article2'),
            ('word21', 'article2'),
            ('word22', 'article2'),
        ]
        decorated = decorate(expected)
        reader = ContentReader()
        _result = reader(contents)

        reader.dsl_raw_reader.seek(0)
        reader.dsl_raw_reader.read_header()
        for word, article in decorated:
            next_pair = reader.dsl_raw_reader.get_next_word(convert=True)
            print('expected %s, actual %s' % ((word, article), next_pair))
            assert (word, article) == next_pair
        # assert decorated == reader(contents)
        assert len(expected) == len(reader.dsl_indexer)


class TestDslIndexer:
    def test_multi_title_words(self):
        contents = HEADER + '''
word1
word11
	article1
word2
word21
word22
	article2
'''
        expected = [
            ('word1', 'article1'),
            ('word11', 'article1'),
            ('word2', 'article2'),
            ('word21', 'article2'),
            ('word22', 'article2'),
        ]
        decorated = decorate(expected)
        reader = ContentReader()
        _result = reader(contents)

        for word, _article in decorated:
            print('checking word %s' % word)
            assert reader.dsl_indexer.get_pos(word) >= len(HEADER)


class TestIntegration(TestCase):
    def test_header_only(self):
        contents = '''#NAME   "Test"
#INDEX_LANGUAGE "English"
#CONTENTS_LANGUAGE      "Spanish"'''
        assert [] == ContentReader()(contents)

        contents = '''#NAME   "Test"
#INDEX_LANGUAGE "English"
#CONTENTS_LANGUAGE      "Spanish"
'''
        assert [] == ContentReader()(contents)

        contents = '''#NAME   "Test"
#INDEX_LANGUAGE "English"
#CONTENTS_LANGUAGE      "Spanish"


'''
        assert [] == ContentReader()(contents)

    def test_one_word(self):
        contents = HEADER + '''word
	article
'''
        assert_contents(contents, [('word', 'article')])

        contents = HEADER + '''
word
	article
'''
        assert_contents(contents, [('word', 'article')])

    def test_many_words(self):
        contents = HEADER + '''
word1
	article1
word2
	article2
'''
        assert_contents(
            contents,
            [('word1', 'article1'),
             ('word2', 'article2')])

        # Do not strip the tab
        contents = HEADER + '''
word1
	article1
	
word2
	article2
'''
        assert_contents(
            contents,
            [('word1', 'article1\n'),
             ('word2', 'article2')])

        # Do not strip white space after the tab
        contents = HEADER + '''
word1
	article1
	 
word2
	article2
'''
        assert_contents(
            contents,
            [('word1', 'article1\n'),
             ('word2', 'article2')])

        contents = HEADER + '''
word1
	article1
    article1_part2
word2
	article2
'''
        assert_contents(
            contents,
            [('word1', 'article1\narticle1_part2'),
             ('word2', 'article2')])

        contents = HEADER + '''
word1
	article1
    article1_part2
	
word2
	article2
    article2_part2
'''
        assert_contents(
            contents,
            [('word1', 'article1\narticle1_part2\n'),
             ('word2', 'article2\narticle2_part2')])

    def test_multi_title_words(self):
        contents = HEADER + '''
word1
word11
	article1
word2
word21
word22
	article2
'''
        assert_contents(
            contents,
            [('word1', 'article1'),
             ('word11', 'article1'),
             ('word2', 'article2'),
             ('word21', 'article2'),
             ('word22', 'article2'),
            ]
        )
