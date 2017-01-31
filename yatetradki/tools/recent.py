"""
This script displays cards there were answered "Hard" today.
To be used in conky as a reminder for hard words.
"""
import sys
import argparse

sys.path.insert(0, '/usr/share/anki')

from anki import Collection


COLLECTION = '/home/bz/Documents/Anki/bz/collection.anki2'
QUERIES_AND_FIELDS = [
    ('deck:english::englishclub-phrasal-verbs rated:2:1', 'Word'),
    ('deck:english::idiomconnection rated:2:1', 'Word'),
    ('deck:english::jinja rated:2:1', 'Word'),
    ('deck:english::lingvo-online rated:2:1', 'Word'),
    ('deck:english::toefl-vocabulary rated:2:1', 'Word'),
    ('deck:english::using-english rated:2:1', 'Word'),
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


def show_recent(col, query, field):
    ids = col.findCards(query)
    words = []
    for id in ids:
        card = col.getCard(id)
        note = col.getNote(card.nid)
        words.append(note[field])
    return '\n'.join(words)


def show_recent_from_collection():
    col = Collection(COLLECTION)
    for query, field in QUERIES_AND_FIELDS:
        output = show_recent(col, query, field)
        if output:
            print('>>> %s (%s):' % (query, field))
            print(output)
            print('')


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
