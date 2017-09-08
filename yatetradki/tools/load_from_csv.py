#!/usr/bin/env python2

# See
# https://www.juliensobczak.com/tell/2016/12/26/anki-scripting.html


import io
from os.path import join, expanduser, expandvars, basename
from os import getcwd
import sys
import argparse

import logging
logging.basicConfig(format='%(asctime)s %(levelname)s: (%(name)s) %(message)s',
                    level=logging.DEBUG)
_logger = logging.getLogger('load_from_csv')


sys.path.insert(0, '/usr/share/anki')

from anki import Collection
from yatetradki.tools.audio import get_pronunciation_call

COLLECTION = '/home/bz/Documents/Anki/bz/collection.anki2'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", help="File to import data from", required=True)
    parser.add_argument("--deck", help="Deck name to import to", required=True)
    parser.add_argument("--model", help="Model to use (card type)", required=True)
    parser.add_argument("--fields", help="List of fields of the model", required=True)
    parser.add_argument("--update", help="True if existing notes should be updated",
        default=False, action='store_true')
    args = parser.parse_args()
    args.fields = args.fields.split(',')
    _logger.info('Args: %s', args)

    cwd = getcwd()
    col = Collection(COLLECTION, log=True)

    # Set the model
    modelBasic = col.models.byName(args.model)
    deck = col.decks.byName(args.deck)
    col.decks.select(deck['id'])
    col.decks.current()['mid'] = modelBasic['id']

    query_template = 'deck:%s note:%s word:%s'

    for line in io.open(join(cwd, args.csv), encoding='utf8'):
        word, example, meaning = line.split('\t')
        query = query_template % (args.deck, args.model, word)
        found_notes = col.findNotes(query)
        # import ipdb; ipdb.set_trace()
        # deck:english::lingvo-online epiphany
        # continue

        if found_notes:
            _logger.info('Duplicate notes (%s) for word %s: %s',
                len(found_notes), word, found_notes)
            if not args.update:
                _logger.info('Skipping word %s', word)
                continue
            _logger.info('Updating note %s', found_notes[0])
            note = col.getNote(found_notes[0])
        else:
            note = col.newNote()
        note.model()['did'] = deck['id']

        fields = {
            'Word': word,
            'Example': example,
            'Description': meaning,
        }

        audio = get_pronunciation_call(word)
        if audio is None:
            _logger.warning('Could not add audio for word %s', word)
        else:
            _logger.info('Adding audio for word %s: %s', word, audio)
            col.media.addFile(audio)
            fields['Audio'] = '[sound:%s]' % basename(audio)

        for field, value in fields.items():
            note.fields[args.fields.index(field)] = value

        if found_notes:
            _logger.info('Updated: %s', word)
        else:
            col.addNote(note)
            _logger.info('Added: %s', word)

        note.flush()
        col.save()


if __name__ == '__main__':
    main()

