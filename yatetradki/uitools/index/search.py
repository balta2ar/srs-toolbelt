import re
import csv
from bisect import bisect_left
from json import loads
from os.path import dirname
from os.path import join
from urllib.request import urlopen

import icu

NOR_INDEX_PATH = join(dirname(__file__), 'index-nor.csv')
RUS_INDEX_PATH = join(dirname(__file__), 'index-rus.csv')

def http_get(url):
    with urlopen(url) as r:
        return r.read()

def reference(word):
    url = 'http://norsk.dicts.aulismedia.com/processnorsk.php?search={}'.format(word)
    return loads(http_get(url).decode('utf-8'))

def less_equal(a, b):
    collator = icu.Collator.createInstance(icu.Locale('nb_NO.UTF-8'))

    def key(x):
        return collator.getSortKey(x)

    s = sorted([a, b], key=key)
    return s[0] == a

SETTINGS = {
    'nor': {
        'lastpage': 1470,
        'firstpage': 1,
    },
    'rus': {
        'lastpage': 1121,
        'firstpage': 1,
    }
}

def has_cyrillic(text):
    return bool(re.search('[\u0400-\u04FF]', text))

def search(query):
    path = RUS_INDEX_PATH if has_cyrillic(query) else NOR_INDEX_PATH
    lang = 'rus' if has_cyrillic(query) else 'nor'
    index = read_index(path)
    pages = sorted(index.items())
    values = [x[1][1] for x in pages]
    index = bisect_left(values, query, lo=0, hi=len(values))
    my = pages[index]  # e.g.: ('nor1396.jpg', ['vaker', 'vakthavende'])
    page = int(''.join([c for c in my[0] if c.isdigit()]))
    return {
        'lastpage': SETTINGS[lang]['lastpage'],
        'firstpage': SETTINGS[lang]['firstpage'],
        'page': page,
        'direction': lang,
        'term': query,
    }

def test_search(query):
    print(query)
    my = search(query)
    ref = reference(query)
    print('my = ', my)
    print('ref = ', ref)

def verify(path):
    index = read_index(path)
    print(len(index))
    pages = sorted(index.items())
    for i, (key, (left, right)) in enumerate(pages):
        left, right = left.lower(), right.lower()
        assert less_equal(left, right), '{}: left <= right: {} <= {}'.format(key, left, right)
        if i > 0:
            pleft, pright = pages[i - 1][1]
            assert less_equal(pleft, left), '{}: pleft <= left: {} <= {}'.format(key, pleft, left)
            assert less_equal(pright, left), '{}: pright <= left: {} <= {}'.format(key, pright, left)
            assert less_equal(pleft, right), '{}: pleft <= right: {} <= {}'.format(key, pleft, right)
            assert less_equal(pright, right), '{}: pright <= right: {} <= {}'.format(key, pright, right)
    print('OK')

def read_index(path):
    index = {}
    with open(path, 'r') as f:
        reader = csv.reader(f, delimiter=',')
        for i, row in enumerate(reader):
            index[row[0]] = [r.lower() for r in row[1:]]
            assert len(row) == 3, 'Invalid row #{}: {}'.format(i, row)
    return index

def save_index(path, index):
    with open(path, 'w') as f:
        writer = csv.writer(f, delimiter=',')
        for key, value in sorted(index.items()):
            writer.writerow([key] + value)
