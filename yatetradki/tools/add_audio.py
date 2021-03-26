import sys
import argparse
from os import getenv
from os.path import expanduser, expandvars

sys.path.insert(0, '/usr/share/anki')
from anki import Collection

from yatetradki.tools.log import get_logger
from yatetradki.tools.pronunciation import Pronunciation
from yatetradki.tools.telegram import notify
from yatetradki.utils import cleanup_query
from yatetradki.utils import mute_networking_logging
from yatetradki.utils import must_env


COLLECTION = expandvars(expanduser(getenv('SRS_ANKI_COLLECTION', '$HOME/.local/share/Anki2/bz/collection.anki2')))
_logger = get_logger('add_audio')


def add_audio(args):
    must_env('TELEGRAM_ACCESS_TOKEN')
    must_env('TELEGRAM_CHAT_ID')
    must_env('AZURE_KEY')
    must_env('AZURE_REGION')

    col = Collection(COLLECTION, log=True)
    pronunciation = Pronunciation(args.audio)

    modelBasic = col.models.byName(args.model)
    deck = col.decks.byName(args.deck)
    col.decks.select(deck['id'])
    col.decks.current()['mid'] = modelBasic['id']

    query_template = 'deck:"%s" note:"%s"'
    query = cleanup_query(query_template % (args.deck, args.model))
    found_notes = col.findNotes(query)
    if (not found_notes) or (not args.update):
        return

    added = []
    for fnote in found_notes:
        note = col.getNote(fnote)
        note.model()['did'] = deck['id']
        fields = {field: note.fields[args.fields.index(field)]
                  for field in args.fields}
        word = fields[args.word_field]
        audio = fields[args.audio_field]
        if pronunciation.fill(word, col, fields):
            if audio != fields[args.audio_field]: # audio field value has changed
                added.append(word)
                _logger.info('Added audio for word "{0}"'.format(word))
        for field, value in fields.items():
            note.fields[args.fields.index(field)] = value
        note.flush()
        col.save()
    if added:
        mute_networking_logging()
        notify('Language: {0}\nAdded audio for ({1}):\n{2}'.format(
            args.audio, len(added), '\n'.join(added)))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--deck", help="Deck name to import to", required=True)
    parser.add_argument("--model", help="Model to use (card type)", required=True)
    parser.add_argument("--fields", help="List of fields of the model", required=True)
    parser.add_argument("--word-field", help="Word field name to generate audio for", required=True)
    parser.add_argument("--audio-field", help="Audio field name to save audio in", required=True)
    parser.add_argument("--update", help="True if existing notes should be updated",
        default=False, action='store_true')
    parser.add_argument("--audio", choices=['none', 'norwegian', 'korean', 'english'],
        help="If set, add audio generated by TTS depending on the choice",
        default='none')
    args = parser.parse_args()
    args.fields = args.fields.split(',')

    add_audio(args)


if __name__ == '__main__':
    main()
