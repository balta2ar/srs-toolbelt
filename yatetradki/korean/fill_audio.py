# coding=utf-8
"""
This scripts updates my deck of korean words with audios grabbed from
koreanclass101.com/korean-dictionary. These pronunciations are far
better because they are recorded by humans. Field for which human pronunction
is missing are filled with TextToSpeech generated audio (use AwesomeTTS
Anki plugin to do that).
"""
from os.path import join, exists, getsize
from shutil import copy2
from operator import itemgetter
import codecs
import logging
import argparse
from collections import namedtuple
from pprint import pformat


FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.DEBUG)


KOREAN_CLASS_MP3_DIR = '/mnt/video/rip/koreanclass101/dictionary-mp3'
HOSGELDI_MP3_DIR = '/mnt/video/rip/hosgeldi.com/mp3s'
MEDIA_DIR = '/home/bz/Documents/Anki/bz/collection.media'
KOREAN_CLASS_COPIED_PREFIX = 'kc101_'
HOSGELDI_COPIED_PREFIX = 'hosgeldi_'
KOREAN_CLASS_LOOKUP_TABLE_FILENAME = '/mnt/big_ext4/btsync/prg/koreanclass101-dictionary/sort-uniq-table.txt'
HOSGELDI_LOOKUP_TABLE_FILENAME = '/mnt/video/rip/hosgeldi.com/uniq.txt'
WORD_FIELD = 'Korean'
ENGLISH_FIELD = 'English'
AUDIO_FIELD = 'Audio'
MAX_AUDIO_COUNT = 3


TableEntry = namedtuple('TableEntry', 'mp3from mp3to mp3tobase')


class WordTable(object):
    def _make_entry(self, entry_dict):
        mp3from = join(self._mp3dir, entry_dict['mp3base'])
        mp3tobase = self._copied_prefix + entry_dict['mp3base']
        mp3to = join(self._media_dir, mp3tobase)
        return TableEntry(mp3from, mp3to, mp3tobase)

    def lookup(self, value):
        raise NotImplementedError('NOT IMPLEMENTED')


class ComposedTable(WordTable):
    def __init__(self, tables):
        self._tables = tables

    def lookup(self, value):
        result = []
        for table in self._tables:
            result.extend(table.lookup(value))
        return result


class KoreanClass101WordTable(WordTable):
    def __init__(self, filename, mp3dir, media_dir, copied_prefix):
        super(KoreanClass101WordTable, self).__init__()

        self._mp3dir = mp3dir
        self._media_dir = media_dir
        self._copied_prefix = copied_prefix

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
        results = [entry for entry in self._db
                   if entry['korean'] == value
                   and '_' not in entry['mp3base']]

        uniq_sizes = {getsize(join(self._mp3dir, entry['mp3base'])): entry
                      for entry in results}

        uniq_results = list(uniq_sizes.values())

        return [self._make_entry(x)
                for x in sorted(uniq_results, key=itemgetter('mp3base'))]


class HosgeldiWordTable(WordTable):
    def __init__(self, filename, mp3dir, media_dir, copied_prefix):
        super(HosgeldiWordTable, self).__init__()

        self._mp3dir = mp3dir
        self._media_dir = media_dir
        self._copied_prefix = copied_prefix

        self._db = []
        for line in codecs.open(filename, 'r', encoding='utf-8').readlines():
            line = line.strip()
            try:
                korean, russian, id, mp3base, mp3url, image_base, image_url = line.split('\t')
                self._db.append({'korean': '%s' % korean,
                                 'russian': '%s' % russian,
                                 'id': id,
                                 'mp3base': mp3base,
                                 'mp3url': mp3url,
                                 'image_base': image_base,
                                 'image_url': image_url})
            except ValueError:
                logging.error('Skipping line: "%s"', line)
        logging.info('Loaded %d entries from table %s',
                     len(self._db), filename)

    def lookup(self, value):
        results = [entry for entry in self._db
                   if entry['korean'] == value]

        uniq_sizes = {getsize(join(self._mp3dir, entry['mp3base'])): entry
                      for entry in results}

        uniq_results = list(uniq_sizes.values())

        return [self._make_entry(x)
                for x in sorted(uniq_results, key=itemgetter('mp3base'))]


def create_master_table():
    korean_class_table = KoreanClass101WordTable(
        KOREAN_CLASS_LOOKUP_TABLE_FILENAME,
        KOREAN_CLASS_MP3_DIR,
        MEDIA_DIR,
        KOREAN_CLASS_COPIED_PREFIX
    )
    hosgeldi_table = HosgeldiWordTable(
        HOSGELDI_LOOKUP_TABLE_FILENAME,
        HOSGELDI_MP3_DIR,
        MEDIA_DIR,
        HOSGELDI_COPIED_PREFIX
    )
    return ComposedTable([korean_class_table, hosgeldi_table])


def test_table(value=None):
    print('Hello')
    if value is not None:
        table = create_master_table()
        result = table.lookup(value)
        print(result)
    print('Done')


def test_neospeech():
    word = '색인'
    import service
    logger = logging.getLogger()
    neospeech = service.neospeech.NeoSpeech(
        normalize=None,
        ecosystem=None,
        logger=logger,
        lame_flags=None,
        temp_dir='/tmp'
    )
    print(neospeech, type(neospeech))
    neospeech.run(word, {'voice': 'Jihun'}, '/tmp/neo.mp3')
    print(word)


def main():
    parser = argparse.ArgumentParser(description='Add audio pronunciation to korean words')
    parser.add_argument('--dry-run', action='store_true', default=False,
                        help='Do not modify anything')
    parser.add_argument('--num', type=int, default=None,
                        help='Number of items to update')
    parser.add_argument('--collection', type=str, required=True,
                        help='Filename of the collection to update (collection.anki2)')
    parser.add_argument('--model-name', type=str, required=True,
                        help='Model name to update (CourseraKoreanBasic)')
    parser.add_argument('--deck-name', type=str, required=True,
                        help='Deck name to update (korean::coursera-korean)')
    parser.add_argument('--korean-word-field', type=str, required=True,
                        help='Korean word field name')
    parser.add_argument('--translated-word-field', type=str, required=True,
                        help='Translated word field name')
    parser.add_argument('--korean-audio-field', type=str, required=True,
                        help='Korean audio field name')
    args = parser.parse_args()

    logging.info('Starting')
    logging.info(pformat(args.__dict__))
    if args.dry_run:
        logging.info('Dry run mode')

    korean_class_table = KoreanClass101WordTable(
        KOREAN_CLASS_LOOKUP_TABLE_FILENAME,
        KOREAN_CLASS_MP3_DIR,
        MEDIA_DIR,
        KOREAN_CLASS_COPIED_PREFIX
    )
    hosgeldi_table = HosgeldiWordTable(
        HOSGELDI_LOOKUP_TABLE_FILENAME,
        HOSGELDI_MP3_DIR,
        MEDIA_DIR,
        HOSGELDI_COPIED_PREFIX
    )

    from anki import Collection
    col = Collection(args.collection)
    deckid = col.decks.id(args.deck_name)
    col.decks.select(deckid)

    model = col.models.byName(args.model_name)
    deck = col.decks.get(deckid)
    deck['mid'] = model['id']
    col.decks.save(deck)

    cardids = col.findCards('deck:"%s"' % args.deck_name)
    #noteids = col.findNotes('deck:"%s"' % args.deck_name)
    logging.info('Found %d cards in "%s" deck', len(cardids), args.deck_name)

    # from ipdb import set_trace; set_trace()
    # return

    updated_count = 0

    #for noteid in noteids:
    for i, cardid in enumerate(cardids):
        card = col.getCard(cardid)
        note = card.note()
        #note = col.getNote(noteid)
        word = note[args.korean_word_field]
        # word = '의사'

        # en_word = note[ENGLISH_FIELD]
        # strip <div> tags
        # if en_word.startswith('<div>'):
        #     en_word = en_word[5:]
        # if en_word.endswith('</div>'):
        #     en_word = en_word[:en_word.rfind('</div>')]
        # note[ENGLISH_FIELD] = en_word
        # note.flush()

        logging.info('Another card: id:"%s" Korean:"%s" audio:"%s" Translated:"%s"',
                     cardid, word, note[args.korean_audio_field], note[args.translated_word_field])

        new_audio_field = ''
        entries = korean_class_table.lookup(word)[:MAX_AUDIO_COUNT]
        entries += hosgeldi_table.lookup(word)[:MAX_AUDIO_COUNT]
        for entry in entries:
            logging.info('Entry: "%s"', entry)

            if not args.dry_run and not exists(entry.mp3to):
                logging.info('Copying "%s" to "%s"', entry.mp3from, entry.mp3to)
                copy2(entry.mp3from, entry.mp3to)

            new_audio_field += '[sound:%s]' % entry.mp3tobase

        if entries:
            logging.info('New audio field: "%s"', new_audio_field)
            note[args.korean_audio_field] = new_audio_field
            if not args.dry_run:
                note.flush()
            updated_count += 1

        # from ipdb import set_trace; set_trace()
        # break
        if args.num is not None and i >= args.num:
            break

    logging.info('Closing DB')
    if not args.dry_run:
        col.save()
    col.close()

    logging.info('Would have updated %d cards' if args.dry_run else 'Updated %d cards',
                 updated_count)


if __name__ == '__main__':
    main()
