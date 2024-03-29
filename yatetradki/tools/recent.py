"""
This script displays cards there were answered "Hard" today.
To be used in conky as a reminder for hard words.
"""
import re
import os
import sys
import argparse

from rich.console import Console
from rich.table import Table
from rich.style import Style
#sys.path.insert(0, '/usr/share/anki')

import anki
try:
    from anki import Collection
except ImportError:
    from anki.collection import Collection

MIN_COLUMN_WIDTH = 10
MIN_HEADER_WIDTH = 80
DENSIFY_PADDING = 5
COLUMN_SEPARATOR = ' '

# rated:n:m
# n -- number of days back (up to 30)
# m - one of:
#   1 - Again
#   2 - Hard
#   3 - Normal
#   4 - Easy

#COLLECTION = '/home/bz/Documents/Anki/bz/collection.anki2'
COLLECTION = '/home/bz/.local/share/Anki2/bz/collection.anki2'
QUERIES_AND_FIELDS = [
    #('deck:english::english-for-students rated:7:2', 'Word'),
    ('deck:english::englishclub-phrasal-verbs rated:7:2', 'Word'),
    #('deck:english::jinja rated:7:2', 'Word'),
    ('deck:english::lingvo-online rated:7:2', 'Word'),
    ('deck:english::sat-words rated:7:2', 'Word'),
    ('deck:english::toefl-vocabulary rated:7:2', 'Word'),
    ('deck:english::idiomconnection rated:7:2', 'Word'),

    ('deck:english::using-english rated:7:2', 'Word'),
    ('deck:english::the-idioms rated:7:2', 'Word'),
    ('deck:english::outcomes-vocabulary rated:7:2', 'Word'),
    ('deck:english::phrases-org-uk rated:7:2', 'Word'),
]


def get_collection():
    """Not used"""
    col = Collection(COLLECTION)
    ids = col.findCards(QUERY)
    print(ids)
    for id in ids:
        card = col.get_card(id)
        print(card)
        note = col.get_note(card.nid)
        print(note['Word'])
    return col


def columns_fit(total_width, column_width):
    return int(total_width / column_width)


# Left for reference
# def format_6_columns(lines, maxlen):
#     result = []
#     for a, b, c, d, e, f in zip(lines[::5], lines[1::6], lines[2::6], lines[3::6], lines[4::6], lines[5::6]):
#         result.append('%s %s %s %s %s %s' % (a.ljust(maxlen, COLUMN_SEPARATOR),
#                                              b.ljust(maxlen, COLUMN_SEPARATOR),
#                                              c.ljust(maxlen, COLUMN_SEPARATOR),
#                                              d.ljust(maxlen, COLUMN_SEPARATOR),
#                                              e.ljust(maxlen, COLUMN_SEPARATOR),
#                                              f))
#     return '\n'.join(result)


def test():
    lines = ['a', 'b', 'c']
    print(format_n_columns(lines, 10, 3))


def format_n_columns(lines, maxlen, n):
    result = []

    missing_count = 0
    if (len(lines) % n) > 0:
        missing_count = n - (len(lines) % n)
    lines = lines + [''] * missing_count

    zip_parts = []
    for i in range(n):
        zip_parts.append(lines[i::n])

    for parts in zip(*zip_parts):
        strings = ('%s ' * n).strip()
        ljusted = [part.ljust(maxlen, COLUMN_SEPARATOR) if i+1 != len(parts) else part
                   for i, part in enumerate(parts)]
        result.append(strings % tuple(ljusted))

    return '\n'.join(result)


def show_recent(col, query, field):
    placeholders = re.findall(r"{(\w+)}", field)
    try:
        order = {x.key: x for x in col.all_browser_columns()}
        order = order['noteCrt'] # noteMod
        ids = col.find_cards(query, order=order)
    except Exception as e:
        print('Search error: %s (col=%s, query=%s, field=%s)', e, col, query, field)
        return []
    words = []
    #sorted(ids, key=lambda x: col.get_card(x).mod)
    special = ('n', 't')
    for id in ids:
        card = col.get_card(id)
        note = col.get_note(card.nid)
        values = {p:note[p] for p in placeholders if p not in special}
        values['n'] = '\n'
        values['t'] = '\t'
        words.append(field.format(**values))
    return words
    #return set(words)
    #return sorted(set(words))
    # return '\n'.join(words)


def densify(words, maxlen):
    if words is None:
        words = [line.strip() for line in open('long-list.txt')]
    if maxlen is None:
        maxlen = max(len(max(words, key=len)), MIN_COLUMN_WIDTH)

    free_words = set(words)
    used_words = set()
    new_words = []
    for _index, word in enumerate(words):
        if word in used_words:
            continue

        toplen = maxlen - DENSIFY_PADDING - len(word)
        candidates = sorted([free for free in free_words
                             if len(free) <= toplen and free != word])
        if candidates:
            first = candidates[0]
            used_words.add(first)
            free_words.remove(first)
            if word in free_words:
                free_words.remove(word)
            padding = ' ' * (maxlen - len(word) - len(first))
            word = '%s%s%s' % (word, padding, first)
        new_words.append(word)

    # print('\n'.join(new_words))
    return new_words

def odd(x):
    return x % 2 == 1

def grey(x):
    return '[on grey30]{}[/]'.format(x)

def show_recent_from_collection(queries, header_width):
    col = Collection(COLLECTION)
    #padding = ' ' * 10
    #from rich import print as pprint
    console = Console()
    bg = Style(bgcolor="rgb(70,70,70)")
    for query, field in queries:  # QUERIES_AND_FIELDS:
        #header = '>>> %s (%s)%s' % (query, field, padding)
        #header = '>>> %s (%s)' % (query, field)
        #header = header.ljust(header_width, COLUMN_SEPARATOR)
        words = show_recent(col, query, field)
        words = [w.replace('<b>', '[bold green]').replace('</b>', '[/bold green]') for w in words]
        words = [w.replace('<strong>', '[bold green]').replace('</strong>', '[/bold green]') for w in words]
        table = Table(box=None, padding=(0,), row_styles=['none', bg])
        table.add_column('')
        [table.add_row(w) for w in words]
        console.print(table)
        #words = [grey(w) if odd(i) else w for i, w in enumerate(words)]
        #line = '\n'.join(words)
        #pprint(line)

        #print_formatted_text(HTML('\n'.join(words)))
        # if words:
        #     maxlen = max(len(max(words, key=len)), MIN_COLUMN_WIDTH)
        #     fit = columns_fit(len(header), maxlen)
        #     words = densify(words, maxlen)
        #     print(fit, len(header), maxlen)
        #     body = format_n_columns(words, maxlen, fit)
        #     message = '%s\n%s\n' % (header, body)
        #     print(message)
            #print(message.encode('utf8'))


def read_queries(filename):
    with open(filename) as file_:
        for line in file_:
            parts = line.strip().split('\t', maxsplit=1)
            yield parts


def get_terminal_width():
    rows, columns = os.popen('stty size', 'r').read().split()
    return int(columns) - 10


def main():
    parser = argparse.ArgumentParser(
        description='Show recently studied anki cards')
    parser.add_argument('--queries', type=str, required=False, default=None,
                        help='Filename with queries of format: query<tab>field')
    parser.add_argument('--width', type=int, required=False, default=None,
                        help='Minimal header width (words are formatted into columns '
                        'to fill this width)')
    # parser.add_argument('--field', type=str, required=True,
    #                     help='Field name to print')
    args = parser.parse_args()

    # col = Collection(args.collection)
    # deckid = col.decks.id(args.deck_name)
    # col.decks.select(deckid)
    # from ipdb import set_trace; set_trace()

    queries = QUERIES_AND_FIELDS
    if args.queries:
        queries = list(read_queries(args.queries))

    width = MIN_HEADER_WIDTH
    if args.width is not None:
        if args.width > 0:
            width = args.width
        else:
            width = get_terminal_width()
    show_recent_from_collection(queries, width)


if __name__ == '__main__':
    main()
