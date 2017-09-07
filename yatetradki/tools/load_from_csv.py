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

COLLECTION = '/home/bz/Documents/Anki/bz/collection.anki2'


def get_pronunciation(text):
    import sip
    sip.setapi('QString', 2)
    sip.setapi('QVariant', 2)
    sip.setapi('QUrl', 2)

    from PyQt4.QtGui import QApplication
    from PyQt4.QtCore import QTimer
    sound_path = [None]
    app = QApplication([])

    def fake_awesometts():
        class FakeAddons(object):
            def GetAddons(self):
                return []
            GetAddons.__bases__ = [object]

        import aqt
        aqt.addons = FakeAddons()

        sys.path.insert(0, expanduser('~/Documents/Anki/addons'))
        import awesometts

        #text = 'furfurfur'
        # text = 'smear'
        group = {u'presets': [u'Howjsay (en)', u'Oxford Dictionary (en-US)', u'Collins (en)', u'Google Translate (en-US)', u'Baidu Translate (en)', u'ImTranslator (VW Paul)'], u'mode': u'ordered'}
        presets = {u'ImTranslator (VW Paul)': {u'voice': u'VW Paul', u'speed': 0, u'service': u'imtranslator'}, u'Linguatec (ko, Sora)': {u'voice': u'Sora', u'service': u'linguatec'}, u'Collins (en)': {u'voice': u'en', u'service': u'collins'}, u'NeoSpeech (ko, Jihun)': {u'voice': u'Jihun', u'service': u'neospeech'}, u'Baidu Translate (en)': {u'voice': u'en', u'service': u'baidu'}, u'Google Translate (en-US)': {u'voice': u'en-US', u'service': u'google'}, u'Acapela Group (ko, Minji)': {u'voice': u'Minji', u'service': u'acapela'}, u'ImTranslator (ko, VW Yumi)': {u'voice': u'VW Yumi', u'speed': 0, u'service': u'imtranslator'}, u'Howjsay (en)': {u'voice': u'en', u'service': u'howjsay'}, u'Oxford Dictionary (en-US)': {u'voice': u'en-US', u'service': u'oxford'}, u'NAVER Translate (ko)': {u'voice': u'ko', u'service': u'naver'}}
        def on_okay(path):
            sound_path[0] = path
            app.quit()
        def on_fail(path):
            app.quit()
        callbacks = {
            'okay': on_okay,
            'fail': on_fail,
        } #{'fail': <function fail at 0x7fe53b8aa668>, 'then': <function <lambda> at 0x7fe53b8aa758>, 'done': <function done at 0x7fe55084fed8>, 'okay': <function okay at 0x7fe550afa758>, 'miss': <function miss at 0x7fe53b8aa6e0>}
        want_human = False
        note = None # <anki.notes.Note object at 0x7fe550871990>

        awesometts.router._logger = _logger
        awesometts.router.group(text, group, presets, callbacks, want_human, note)

    # fake_awesometts()
    QTimer.singleShot(1, fake_awesometts)
    app.exec_()
    return sound_path[0]


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
        word, meaning = line.split('\t')
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
            'Description': meaning,
        }

        audio = get_pronunciation(word)
        if audio is not None:
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

