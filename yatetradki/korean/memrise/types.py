from collections import OrderedDict, namedtuple


# TODO: REPLACE OrderedDict WITH SOMETHING ELSE!
# problematic case: multiple levels with the same name
class WordCollection(OrderedDict):
    def __str__(self):
        lines = []

        for level_name, word_pairs in self.items():
            lines.append('\n# %s\n' % level_name)
            for pair in word_pairs:
                lines.append('%s; %s' % (pair.word, pair.meaning))
        return '\n'.join(lines)


WordPair = namedtuple('WordPair', 'word meaning')
DiffActionCreateLevel = namedtuple('DiffActionCreateLevel', 'level_name')
DiffActionDeleteLevel = namedtuple('DiffActionDeleteLevel', 'level_name')
DiffActionChangeLevel = namedtuple('DiffActionChangeLevel',
                                   'level_name new_level_name')
DiffActionCreateWord = namedtuple('DiffActionCreateWord', 'level_name pair')
DiffActionDeleteWord = namedtuple('DiffActionDeleteWord', 'level_name pair')
DiffActionChangeWord = namedtuple('DiffActionChangeWord',
                                  'level_name old_pair new_pair')
