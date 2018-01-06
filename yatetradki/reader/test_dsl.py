from unittest import TestCase
from tempfile import NamedTemporaryFile

from yatetradki.reader.dsl import DSLRawReader, DSLIndexer, DSLLookuper


def spit(data, filename):
    with open(filename, 'w') as file_:
        file_.write(data)


def slurp(filename):
    with open(filename) as file_:
        return file_.read()


def read_dsl_contents(dsl_contents):
    pairs = []
    with NamedTemporaryFile() as dsl, NamedTemporaryFile() as index:
        dsl.write(dsl_contents)

        dsl_raw_reader = DSLRawReader(dsl.name, encoding='utf-8')
        dsl_indexer = DSLIndexer(index.name, dsl_raw_reader)
        _dsl_lookuper = DSLLookuper(dsl.name, dsl_raw_reader, dsl_indexer)

        dsl_raw_reader.read_header()
        word, article = dsl_raw_reader.get_next_word()
        while word is not None and article is not None:
            pairs.append((word, article))
            word, article = dsl_raw_reader.get_next_word()

    return pairs


class TestDslReader(TestCase):
    def test_header_only(self):
        contents = """#NAME   "Test"
#INDEX_LANGUAGE "English"
#CONTENTS_LANGUAGE      "Spanish"
"""
        actual = read_dsl_contents(contents)
        expected = [()]
        assert expected == actual
