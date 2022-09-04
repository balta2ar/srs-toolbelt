import re
import sys
import argparse
from os import getenv
from os.path import expanduser, expandvars

#sys.path.insert(0, '/usr/share/anki')
try:
    from anki.collection import Collection
except ImportError:
    from anki import Collection

from yatetradki.tools.log import get_logger
from yatetradki.tools.anki_control import anki_is_running
from yatetradki.tools.pronunciation import Pronunciation
from yatetradki.tools.anki_sync_anki_connect import web_sync
from yatetradki.tools.telegram import notify
from yatetradki.utils import cleanup_query
from yatetradki.utils import mute_networking_logging
from yatetradki.utils import must_env
from yatetradki.utils import html_to_text

ERROR_OK_FOUND_CHANGES = 0
ERROR_OK_NO_CHANGES = 1
ERROR_ANKI_ALREADY_RUNNING = 2

COLLECTION = expandvars(expanduser(getenv('SRS_ANKI_COLLECTION', '$HOME/.local/share/Anki2/bz/collection.anki2')))
_logger = get_logger('add_audio')

def cleanup_html(text):
    def nowhite(text):
        text = re.sub(r' +', ' ', text)
        text = re.sub(r'^ +', '', text)
        text = re.sub(r' +$', '', text)
        return text
    def noemptydiv(text): return re.sub(r'<div></div>', '', text)
    def twobr(text): return re.sub(r'<br><br><br>', '<br><br>', text)
    def divs(text): return re.sub(r'<div>', '', text)
    def dive(text): return re.sub(r'</div>', '<br>', text)
    def full(text):
        text = nowhite(text)
        text = re.sub(r'</?\b(?!(?:br|b|strong)\b)[^>]+>', ' ', text)
        #text = re.sub(r' *(</?br>) *', r'\1', text)
        text = re.sub(r'</?br>$', r'', text)
        text = re.sub(r'&nbsp;', ' ', text)
        text = re.sub(r'  ', ' ', text)
        text = re.sub(r' ([.,!?])', r'\1', text)
        text = nowhite(text)
        return text
    def keep(text, fns):
        old = text
        i, limit = 0, 20
        while i < limit:
            i += 1
            for fn in fns:
                text = fn(text)
            if text == old:
                return text
            old = text
    text = keep(text, [noemptydiv, twobr, divs, dive])
    text = full(text)
    text = full(text)
    text = full(text)
    return text

def cleanup_fields(deck, deck_name, model_name, field_names, col, allowed):
    query_template = 'deck:"%s" note:"%s"'
    query = cleanup_query(query_template % (deck_name, model_name))
    found_notes = col.find_notes(query)
    if (not found_notes):
        return

    added = []
    for fnote in found_notes:
        note = col.get_note(fnote)
        note.note_type()['did'] = deck['id']
        fields = {field: note.fields[field_names.index(field)]
                  for field in field_names}
        for field_name in allowed:
            field_value = fields[field_name]
            new_value = cleanup_html(field_value)
            if new_value != field_value:
                _logger.info('Fixed field "%s"', field_name)
                _logger.info('old="%s"', field_value)
                _logger.info('new="%s"', new_value)
                note.fields[field_names.index(field_name)] = new_value
                added.append(new_value)
                note.flush()
                col.save()
    #sys.exit(1)
    if added:
        mute_networking_logging()
        notify('Fixed html in {0} fields'.format(len(added)))

def add_audio(args):
    if anki_is_running():
        _logger.info('Anki is already running (must have started manually), skipping sync to avoid conflicts')
        return ERROR_ANKI_ALREADY_RUNNING

    must_env('TELEGRAM_ACCESS_TOKEN')
    must_env('TELEGRAM_CHAT_ID')
    must_env('AZURE_KEY')
    must_env('AZURE_REGION')

    col = Collection(COLLECTION, log=True)
    pronunciation = Pronunciation(args.audio)

    modelBasic = col.models.by_name(args.model)
    deck = col.decks.by_name(args.deck)
    col.decks.select(deck['id'])
    col.decks.current()['mid'] = modelBasic['id']

    allowed = [x for x in args.cleanup.split(',') if x]
    if allowed:
        cleanup_fields(deck, args.deck, args.model, args.fields, col, allowed)

    query_template = 'audio: deck:"%s" note:"%s"'
    query = cleanup_query(query_template % (args.deck, args.model))
    found_notes = col.find_notes(query)
    #if (not found_notes) or (not args.update):
    if (not found_notes):
        print('No notes found, adding new notes')
        return ERROR_OK_NO_CHANGES

    added = []
    for fnote in found_notes:
        note = col.get_note(fnote)
        note.note_type()['did'] = deck['id']
        fields = {field: note.fields[args.fields.index(field)]
                  for field in args.fields}
        word = fields[args.word_field]
        audio = fields[args.audio_field]
        if pronunciation.fill(html_to_text(word), col, fields):
            new_audio = fields[args.audio_field]
            if audio != new_audio: # audio field value has changed
                added.append(word)
                _logger.info('Added audio for word "%s", new value="%s"', word, new_audio)
                for field, value in fields.items():
                    note.fields[args.fields.index(field)] = value
                note.flush()
                col.save()
    if added:
        mute_networking_logging()
        body = '\n'.join(added)
        if len(body) > 400:
            body = body[:400] + '...'
        notify('Language: {0}\nAdded audio for ({1}):\n{2}'.format(
            args.audio, len(added), body))
        # if args.update:
        #     web_sync()
        return ERROR_OK_FOUND_CHANGES
    return ERROR_OK_NO_CHANGES


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--deck", help="Deck name to import to", required=True)
    parser.add_argument("--model", help="Model to use (card type)", required=True)
    parser.add_argument("--fields", help="List of fields of the model", required=True)
    parser.add_argument("--word-field", help="Word field name to generate audio for", required=True)
    parser.add_argument("--audio-field", help="Audio field name to save audio in", required=True)
    # parser.add_argument("--update", help="True if existing notes should be updated",
    #     default=False, action='store_true')
    parser.add_argument("--sync", help="Run web sync after adding audio in case there were changes",
        default=False, action='store_true')
    parser.add_argument("--audio", choices=['none', 'norwegian', 'korean', 'english', 'english-azure'],
        help="If set, add audio generated by TTS depending on the choice",
        default='none')
    parser.add_argument("--cleanup", help="Cleanup html from fields",
        default='')
    args = parser.parse_args()
    args.fields = args.fields.split(',')

    sys.exit(add_audio(args))


def test_cleanup():
    def same(actual, expected):
        assert actual == expected, 'actual "{}" != expected "{}"'.format(actual, expected)
    same(cleanup_html('   so</br>me<div><div><div></div><div>text<br></div>more</br></div></br>'), 'so</br>me text<br>more')


if __name__ == '__main__':
    main()
