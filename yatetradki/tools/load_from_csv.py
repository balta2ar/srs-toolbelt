#!/usr/bin/env python2

# See
# https://www.juliensobczak.com/tell/2016/12/26/anki-scripting.html


import io
from os.path import join
from os import getcwd
import sys
import argparse

sys.path.insert(0, '/usr/share/anki')

from anki import Collection

COLLECTION = '/home/bz/Documents/Anki/bz/collection.anki2'


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", help="File to import data from", required=True)
    parser.add_argument("--deck", help="Deck name to import to", required=True)
    parser.add_argument("--model", help="Model to use (card type)", required=True)
    parser.add_argument("--fields", help="List of fields of the model", required=True)
    parser.add_argument("--update", help="True if existing notes should be updated",
        default=False, action='store_true')
    args = parser.parse_args()
    args.fields = args.fields.split(',')
    print(args)

    cwd = getcwd()
    col = Collection(COLLECTION, log=True)

    # Set the model
    modelBasic = col.models.byName(args.model)
    deck = col.decks.byName(args.deck)
    col.decks.select(deck['id'])
    col.decks.current()['mid'] = modelBasic['id']

    query_template = 'deck:%s note:%s word:%s'

    for line in io.open(join(cwd, args.csv), encoding='utf8'):
        word, meaning = line.split('\t')
        query = query_template % (args.deck, args.model, word)
        found_notes = col.findNotes(query)
        # import ipdb; ipdb.set_trace()
        # deck:english::lingvo-online epiphany
        # continue

        if found_notes:
            print('Duplicate notes (%s) for word %s: %s' % (
                len(found_notes), word, found_notes))
            if not args.update:
                print('Skipping word %s' % word)
                continue
            print('Updating note %s' % found_notes[0])
            note = col.getNote(found_notes[0])
        else:
            note = col.newNote()
        note.model()['did'] = deck['id']

        fields = {
            'Word': word,
            'Description': meaning,
        }

        for field, value in fields.items():
            note.fields[args.fields.index(field)] = value

        if found_notes:
            print('Updated: %s' % word)
        else:
            col.addNote(note)
            print('Added: %s' % word)

        col.save()
