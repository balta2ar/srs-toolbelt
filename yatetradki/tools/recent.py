"""
This script displays cards there were answered "Hard" today.
To be used in conky as a reminder for hard words.
"""
import sys
import argparse

sys.path.insert(0, '/usr/share/anki')

from anki import Collection

MIN_COLUMN_WIDTH = 15
COLUMN_SEPARATOR = ' '


COLLECTION = '/home/bz/Documents/Anki/bz/collection.anki2'
QUERIES_AND_FIELDS = [
    ('deck:english::englishclub-phrasal-verbs rated:7:2', 'Word'),
    ('deck:english::idiomconnection rated:7:2', 'Word'),
    ('deck:english::jinja rated:7:2', 'Word'),
    ('deck:english::lingvo-online rated:7:2', 'Word'),
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


def format_1_columns(lines, maxlen):
    return '\n'.join(lines)


def format_2_columns(lines, maxlen):
    result = []
    for a, b in zip(lines[::2], lines[1::2]):
        result.append('%s %s' % (a.ljust(maxlen, COLUMN_SEPARATOR), b))
    return '\n'.join(result)


def format_3_columns(lines, maxlen):
    result = []
    for a, b, c in zip(lines[::3], lines[1::3], lines[2::3]):
        result.append('%s %s %s' % (a.ljust(maxlen, COLUMN_SEPARATOR),
                                    b.ljust(maxlen, COLUMN_SEPARATOR),
                                    c))
    return '\n'.join(result)


def format_4_columns(lines, maxlen):
    result = []
    for a, b, c, d in zip(lines[::4], lines[1::4], lines[2::4], lines[3::4]):
        result.append('%s %s %s %s' % (a.ljust(maxlen, COLUMN_SEPARATOR),
                                       b.ljust(maxlen, COLUMN_SEPARATOR),
                                       c.ljust(maxlen, COLUMN_SEPARATOR),
                                       d))
    return '\n'.join(result)


def show_recent(col, query, field):
    ids = col.findCards(query)
    words = []
    for id in ids:
        card = col.getCard(id)
        note = col.getNote(card.nid)
        words.append(note[field])
    return words
    #return '\n'.join(words)


def show_recent_from_collection():
    col = Collection(COLLECTION)
    for query, field in QUERIES_AND_FIELDS:
        header = '>>> %s (%s)' % (query, field)
        words = sorted(show_recent(col, query, field))
        if words:
            maxlen = max(len(max(words, key=len)), MIN_COLUMN_WIDTH)
            fit = columns_fit(len(header), maxlen)
            # print(len(header), maxlen, fit)

            if fit >= 4:
                body = format_4_columns(words, maxlen)
            elif fit >= 3:
                body = format_3_columns(words, maxlen)
            elif fit >= 2:
                body = format_2_columns(words, maxlen)
            else:
                body = format_1_columns(words, maxlen)
            message = '%s\n%s\n\n' % (header, body)
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
