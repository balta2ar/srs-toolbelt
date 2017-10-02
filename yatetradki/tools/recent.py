"""
This script displays cards there were answered "Hard" today.
To be used in conky as a reminder for hard words.
"""
import sys
import argparse

sys.path.insert(0, '/usr/share/anki')

from anki import Collection

MIN_COLUMN_WIDTH = 10
COLUMN_SEPARATOR = ' '


COLLECTION = '/home/bz/Documents/Anki/bz/collection.anki2'
QUERIES_AND_FIELDS = [
    # ('deck:english::english-for-students rated:7:2', 'Word'),
    ('deck:english::englishclub-phrasal-verbs rated:7:2', 'Word'),
    ('deck:english::idiomconnection rated:7:2', 'Word'),
    ('deck:english::jinja rated:7:2', 'Word'),
    ('deck:english::lingvo-online rated:7:2', 'Word'),
    ('deck:english::phrases-org-uk rated:7:2', 'Word'),
    ('deck:english::sat-words rated:7:2', 'Word'),
    ('deck:english::toefl-vocabulary rated:7:2', 'Word'),
    ('deck:english::using-english rated:7:2', 'Word'),
]

def get_collection():
    """Not used"""
    col = Collection(COLLECTION)
    ids = col.findCards(QUERY)
    print(ids)
    for id in ids:
        card = col.getCard(id)
        print(card)
        note = col.getNote(card.nid)
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
    ids = col.findCards(query)
    words = []
    for id in ids:
        card = col.getCard(id)
        note = col.getNote(card.nid)
        words.append(note[field])
    return sorted(set(words))
    #return '\n'.join(words)


def show_recent_from_collection():
    col = Collection(COLLECTION)
    padding = ' ' * 30
    for query, field in QUERIES_AND_FIELDS:
        header = '>>> %s (%s)%s' % (query, field, padding)
        words = show_recent(col, query, field)
        if words:
            maxlen = max(len(max(words, key=len)), MIN_COLUMN_WIDTH)
            fit = columns_fit(len(header), maxlen)
            body = format_n_columns(words, maxlen, fit)
            message = '%s\n%s\n' % (header, body)
            print(message.encode('utf8'))


def main():
    # parser = argparse.ArgumentParser(description='Extract recent cards from Anki collection')
    # parser.add_argument('--collection', type=str, required=True,
    #                     help='Filename of the collection to read (collection.anki2)')
    # parser.add_argument('--query', type=str, required=True,
    #                     help='Query that is used to filter cards')
    # parser.add_argument('--field', type=str, required=True,
    #                     help='Field name to print')
    # args = parser.parse_args()

    # col = Collection(args.collection)
    # deckid = col.decks.id(args.deck_name)
    # col.decks.select(deckid)
    # from ipdb import set_trace; set_trace()

    show_recent_from_collection()


if __name__ == '__main__':
    main()
