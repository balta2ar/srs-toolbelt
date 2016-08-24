"""
This scripts updates my deck of korean words with audios grabbed from
koreanclass101.com/korean-dictionary. These pronunciations are far
better because they are recorded by humans. Field for which human pronunction
is missing are filled with TextToSpeech generated audio (use AwesomeTTS
Anki plugin to do that).
"""
from os.path import join, exists
from shutil import copy2
from operator import itemgetter
import codecs
import logging

from anki import Collection


FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.DEBUG)


MP3_DIR = '/mnt/video/rip/koreanclass101/dictionary-mp3'
MEDIA_DIR = '/home/bz/Documents/Anki/bz/collection.media'
COPIED_PREFIX = 'kc101_'
LOOKUP_TABLE_FILENAME = '/mnt/big_ext4/btsync/prg/koreanclass101-dictionary/sort-uniq-table.txt'
WORD_FIELD = 'Korean'
AUDIO_FIELD = 'Audio'


class WordTable(object):
    def __init__(self, filename):
        self._db = []
        for line in codecs.open(filename, 'r', encoding='utf-8').readlines():
            line = line.strip()
            try:
                korean, english, roman, mp3base, mp3url = line.split('\t')
                self._db.append({'korean': korean,
                                 'english': english,
                                 'roman': roman,
                                 'mp3base': mp3base,
                                 'mp3url': mp3url})
            except ValueError:
                logging.error('Skipping line: "%s"', line)
        logging.info('Loaded %d entries from table %s',
                     len(self._db), filename)

    def lookup(self, value):
        return sorted([entry for entry in self._db
                       if entry['korean'] == value],
                      key=itemgetter('mp3base'))


def main():
    logging.info('Starting')

    table = WordTable(LOOKUP_TABLE_FILENAME)

    colname = 'collection.anki2'
    modelname = 'CourseraKoreanBasic'
    deckname = 'korean::coursera-korean'

    col = Collection(colname)
    deckid = col.decks.id(deckname)
    col.decks.select(deckid)

    model = col.models.byName(modelname)
    deck = col.decks.get(deckid)
    deck['mid'] = model['id']
    col.decks.save(deck)

    cardids = col.findCards('deck:"%s"' % deckname)
    #noteids = col.findNotes('deck:"%s"' % deckname)
    logging.info('Found %d cards in "%s" deck', len(cardids), deckname)

    # from ipdb import set_trace; set_trace()
    # return

    updated_count = 0

    #for noteid in noteids:
    for cardid in cardids:
        card = col.getCard(cardid)
        note = card.note()
        #note = col.getNote(noteid)
        logging.info('"%s" "%s" "%s"', cardid, note[WORD_FIELD], note[AUDIO_FIELD])

        new_audio_field = ''
        entries = table.lookup(note[WORD_FIELD])[:2]
        for entry in entries:
            logging.info('Entry: "%s"', entry)
            mp3from = join(MP3_DIR, entry['mp3base'])
            mp3tobase = COPIED_PREFIX + entry['mp3base']
            mp3to = join(MEDIA_DIR, mp3tobase)

            if not exists(mp3to):
                logging.info('Copying "%s" to "%s"', mp3from, mp3to)
                copy2(mp3from, mp3to)

            new_audio_field += '[sound:%s]' % mp3tobase


        if entries:
            logging.info('New audio field: "%s"', new_audio_field)
            note[AUDIO_FIELD] = new_audio_field
            note.flush()
            updated_count += 1

        # from ipdb import set_trace; set_trace()
        # break

    logging.info('Closing DB')
    col.save()
    col.close()

    logging.info('Updated %d cards', updated_count)


if __name__ == '__main__':
    main()
