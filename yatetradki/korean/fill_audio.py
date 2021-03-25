# coding=utf-8
"""
This scripts updates my deck of korean words with audios grabbed from
koreanclass101.com/korean-dictionary. These pronunciations are far
better because they are recorded by humans. Field for which human pronunction
is missing are filled with TextToSpeech generated audio (use AwesomeTTS
Anki plugin to do that).
"""
import codecs
import random
import string
import logging
import argparse

from pprint import pformat
from shutil import copy2, move
from operator import itemgetter
from collections import namedtuple
from os import makedirs
from os.path import exists, getsize, join, expanduser, expandvars

from yatetradki.korean.aws_polly_synthesize_speech import norwegian_synthesize

FORMAT = '%(asctime)-15s %(levelname)s (%(name)s) %(message)s'
logging.basicConfig(format=FORMAT, level=logging.DEBUG)


KOREAN_CLASS_MP3_DIR = '/mnt/video/rip/koreanclass101/dictionary-mp3'
HOSGELDI_MP3_DIR = '/mnt/video/rip/hosgeldi.com/mp3s'
#MEDIA_DIR = '/home/bz/Documents/Anki/bz/collection.media'
MEDIA_DIR = expandvars(expanduser('$HOME/.local/share/Anki2/bz/collection.media'))
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
    """
    Common interface to lookup words from a table. A table is a file with
    the following columns:
    korean_word, russian_word, path_to_file, ...
    """

    def _make_random_filename(self, length=20):
        letters = string.ascii_lowercase
        return ''.join(random.choice(letters) for i in range(length))

    def _make_default_entry(self, from_name, to_name):
        mp3to = join(MEDIA_DIR, to_name)
        return TableEntry(from_name, mp3to, to_name)

    def _make_entry(self, entry_dict):
        mp3from = join(self._mp3dir, entry_dict['mp3base'])
        mp3tobase = self._copied_prefix + entry_dict['mp3base']
        mp3to = join(self._media_dir, mp3tobase)
        return TableEntry(mp3from, mp3to, mp3tobase)

    def lookup(self, value):
        raise NotImplementedError('NOT IMPLEMENTED')


class ComposedWordTable(WordTable):
    """
    This table can compose several child tables and query them one by one,
    returning result as soon as the first result is available.
    """

    def __init__(self, tables):
        self._tables = tables

    def lookup(self, value):
        results = []
        for table in self._tables:
            lookup_results = table.lookup(value)
            if lookup_results:
                results.extend(lookup_results)
                break
        return results


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
                      for entry in results if exists(join(self._mp3dir, entry['mp3base']))}

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
                korean, russian, id_, mp3base, mp3url, image_base, image_url = \
                    line.split('\t')
                self._db.append({'korean': '%s' % korean,
                                 'russian': '%s' % russian,
                                 'id': id_,
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
                      for entry in results if exists(join(self._mp3dir, entry['mp3base']))}

        uniq_results = list(uniq_sizes.values())

        return [self._make_entry(x)
                for x in sorted(uniq_results, key=itemgetter('mp3base'))]


class NorwegianOnWebWordTable(WordTable):
    def __init__(self, filename, mp3dir, media_dir, copied_prefix):
        super(NorwegianOnWebWordTable, self).__init__()

        self._mp3dir = mp3dir
        self._media_dir = media_dir
        self._copied_prefix = copied_prefix

        self._db = []
        for line in codecs.open(filename, 'r', encoding='utf-8').readlines():
            line = line.strip()
            try:
                norwegian,\
                english,\
                transcription,\
                inflection,\
                audio_id,\
                audio_base,\
                audio_src = line.split('\t')
                self._db.append({'norwegian': '%s' % norwegian,
                                 'english': '%s' % english,
                                 'transcription': transcription,
                                 'inflection': inflection,
                                 'audio_id': audio_id,
                                 'mp3base': audio_base,
                                 'audio_src': audio_src})
            except ValueError:
                logging.error('Skipping line: "%s"', line)
        logging.info('Loaded %d entries from table %s',
                     len(self._db), filename)

    def lookup(self, value):
        results = [entry for entry in self._db
                   if entry['norwegian'] == value]

        uniq_sizes = {getsize(join(self._mp3dir, entry['mp3base'])): entry
                      for entry in results if exists(join(self._mp3dir, entry['mp3base']))}

        uniq_results = list(uniq_sizes.values())

        return [self._make_entry(x)
                for x in sorted(uniq_results, key=itemgetter('mp3base'))]


def create_forced_alignment_table():
    """
    Forced alingnment table simply retrieves words from a directory. Filenames
    should be as follows:
    <korean_word>.mp3
    """
    cached_table = CachingWordTable('lesson11_parts', None)
    return ComposedWordTable([cached_table])


def create_cached_table(cache_dir, prefix, table):
    caching_table = CachingPrefixedWordTable(MEDIA_DIR, cache_dir, prefix, table)
    return ComposedWordTable([caching_table])

def create_norwegian_table():
    cache_dir = 'aws_polly_cache_norwegian'
    prefix = cache_dir + '_'
    aws_polly_norwegian_table = AwsPollyNorwegianService()
    aws_polly_norwegian_caching_table = CachingPrefixedWordTable(
        MEDIA_DIR, cache_dir, prefix, aws_polly_norwegian_table)
    return ComposedWordTable([aws_polly_norwegian_caching_table])

    # norwegianonweb_table = NorwegianOnWebWordTable(
    #     filename='/mnt/video/rip/ntnu.edu/vocabulary/all.tsv',
    #     mp3dir='/mnt/video/rip/ntnu.edu/audio/mp3',
    #     media_dir=MEDIA_DIR,
    #     copied_prefix='norwegianonweb_',
    # )
    # return ComposedWordTable([norwegianonweb_table])


def create_korean_table():
    """
    Master table chains 4 audio sources:
        - words from KoreanClass101 site
        - words from Hosgeldi site
        - words from Naver (pronounced by human, but serviced from Krdict)
        - NaverTTS
        - NeoSpeechTTS
    """
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

    krdict_table = KrdictService()
    krdict_caching_table = CachingWordTable('cache_krdict', krdict_table)

    naver_table = NaverService()
    naver_caching_table = CachingWordTable('tts_cache_naver', naver_table)

    neospeech_table = NeoSpeechService()
    neospeech_caching_table = CachingWordTable(
        'tts_cache_neospeech', neospeech_table)

    return ComposedWordTable([korean_class_table,
                              hosgeldi_table,
                              krdict_caching_table,
                              naver_caching_table,
                              neospeech_caching_table])


def test_table(value=None):
    print('Hello')
    if value is not None:
        table = create_korean_table()
        result = table.lookup(value)
        print(result)
    print('Done')


class CachingWordTable(WordTable):
    """
    This table cannot generate or provide audios for words, it only caches
    the result into cache_dir. However, if cache_dir contains audios for
    many words, it can easily become an audio source.
    """

    def __init__(self, cache_dir, table):
        super(CachingWordTable, self).__init__()

        self._cache_dir = cache_dir
        self._table = table
        self._logger = logging.getLogger(self.__class__.__name__)

    def _mkpath(self, path):
        if not exists(path):
            makedirs(path)

    def lookup(self, value):
        basename = value + '.mp3'
        filename = join(self._cache_dir, basename)

        if not exists(filename):
            self._logger.info('Cache miss: %s', value)
            self._mkpath(self._cache_dir)
            results = self._table.lookup(value)
            if results:
                result = results[0]
                move(result.mp3from, filename)
            else:
                self._logger.info('Child table returned None: %s', self._table)
                return None
        else:
            self._logger.info('Cache hit: %s', value)

        #return [TableEntry(filename, None, basename)]
        return [self._make_default_entry(filename, basename)]


class CachingPrefixedWordTable(WordTable):
    """
    Same as CachingWordTable, but copies cached files into media folder.
    The reasoning was that for years fords were unique in media folder, e.g.
    gift.mp3 is clearly an english word. When I started to learn (LOL)
    norwegian, that has changed, and gift in norwegian is not gift in english.
    Yeah, I know...
    """
    def __init__(self, media_dir, cache_dir, prefix, table):
        super(CachingPrefixedWordTable, self).__init__()

        self._media_dir = media_dir
        self._cache_dir = cache_dir
        self._prefix = prefix
        self._table = table
        self._logger = logging.getLogger(self.__class__.__name__)

    def _mkpath(self, path):
        if not exists(path):
            makedirs(path)

    def lookup(self, value):
        basename = value + '.mp3'
        filename = join(self._cache_dir, basename)
        prefixed = self._prefix + basename
        full_prefixed = join(self._media_dir, prefixed)

        if not exists(filename):
            self._logger.info('Cache miss: %s', value)
            self._mkpath(self._cache_dir)
            results = self._table.lookup(value)
            if results:
                result = results[0]
                move(result.mp3from, filename)
            else:
                self._logger.info('Child table returned None: %s', self._table)
                return None
        else:
            self._logger.info('Cache hit: %s', value)

        if not exists(full_prefixed):
            copy2(filename, full_prefixed)

        #return [TableEntry(filename, None, basename)]
        return [self._make_default_entry(full_prefixed, prefixed)]


class CustomServiceWithFunction(WordTable):
    def __init__(self, prefix, getter):
        self.prefix = prefix
        self.getter = getter
    def lookup(self, value):
        logger = logging.getLogger()
        filename = '%s%s.mp3' % (self.prefix, self._make_random_filename())
        result = self.getter(value)
        logger.info('word: %s, custom service result: %s', value, result)
        move(result, filename)
        return [self._make_default_entry(filename, filename)]


class AwsPollyNorwegianService(WordTable):
    def lookup(self, value):
        logger = logging.getLogger()
        filename = 'aws_polly_norwegian_%s.mp3' % self._make_random_filename()
        result = norwegian_synthesize(value, filename)
        logger.info('word: %s, AWS polly result: %s', value, result)
        #return [TableEntry('neo.mp3', None, 'neo.mp3')]
        return [self._make_default_entry(filename, filename)]


class NeoSpeechService(WordTable):
    def lookup(self, value):
        import service

        #word = '색인'
        logger = logging.getLogger()
        neospeech = service.neospeech.NeoSpeech(
            normalize=None,
            ecosystem=None,
            logger=logger,
            lame_flags=None,
            temp_dir='/tmp'
        )
        neospeech.net_reset()
        #value = value.decode('utf-8')
        result = neospeech.run(value, {'voice': 'Jihun'}, 'neo.mp3')
        #return [TableEntry('neo.mp3', None, 'neo.mp3')]
        return [self._make_default_entry('neo.mp3', 'neo.mp3')]


class NaverService(WordTable):
    def lookup(self, value):
        import service

        #word = '색인'
        logger = logging.getLogger()
        neospeech = service.naver.Naver(
            normalize=None,
            ecosystem=None,
            logger=logger,
            lame_flags=None,
            temp_dir='/tmp'
        )
        neospeech.net_reset()
        #value = value.decode('utf-8')
        result = neospeech.run(value, {'voice': 'ko'}, 'naver.mp3')
        #return [TableEntry('naver.mp3', None, 'naver.mp3')]
        return [self._make_default_entry('naver.mp3', 'naver.mp3')]


class KrdictService(WordTable):
    """
    Extractor of audio from https://krdict.korean.go.kr/eng/dicSearch/search?
    service.
    """
    def lookup(self, value):
        import service

        logger = logging.getLogger()
        krdict = service.krdictkoreangokr.Krdict(
            normalize=None,
            ecosystem=None,
            logger=logger,
            lame_flags=None,
            temp_dir='/tmp'
        )
        krdict.net_reset()
        #value = value.decode('utf-8')
        result = krdict.run(value, {'voice': 'ko'}, 'krdict.mp3')
        if result is not None:
            #return [TableEntry('krdict.mp3', None, 'krdict.mp3')]
            return [self._make_default_entry('krdict.mp3', 'krdict.mp3')]
        return None


def test_krdict():
    import sys

    print(sys.path)
    word = '줄이다' #'성공적' #'종일'

    import service

    logger = logging.getLogger()
    krdict = service.krdictkoreangokr.Krdict(
        normalize=None,
        ecosystem=None,
        logger=logger,
        lame_flags=None,
        temp_dir='/tmp')
    print(krdict, type(krdict))
    krdict.net_reset()

    result = krdict.run(word.decode('utf-8'),
                        {'voice': 'VW Yumi', 'speed': 0}, 'krdict.mp3')
    print(result)
    print(word)


def test_neospeech():
    #word = '색인'
    import sys

    print(sys.path)
    word = '성공적' #'종일'

    import service

    logger = logging.getLogger()
    krdict = service.krdictkoreangokr.Krdict(
        normalize=None,
        ecosystem=None,
        logger=logger,
        lame_flags=None,
        temp_dir='/tmp')
    # neospeech = service.imtranslator.ImTranslator(
    # neospeech = service.neospeech.NeoSpeech(
    # neospeech = service.naver.Naver(
    #     normalize=None,
    #     ecosystem=None,
    #     logger=logger,
    #     lame_flags=None,
    #     temp_dir='/tmp'
    # )
    print(krdict, type(krdict))
    krdict.net_reset()

    result = krdict.run(word.decode('utf-8'),
                        {'voice': 'VW Yumi', 'speed': 0}, 'krdict.mp3')
    #result = neospeech.run(word.decode('utf-8'), {'voice': 'Jihun'}, 'neo.mp3')
    #result = neospeech.run(word.decode('utf-8'), {'voice': 'ko'}, 'naver.mp3')
    print(result)
    print(word)


def main():
    parser = argparse.ArgumentParser(
        description='Add audio pronunciation to korean words')
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

    # korean_class_table = KoreanClass101WordTable(
    #     KOREAN_CLASS_LOOKUP_TABLE_FILENAME,
    #     KOREAN_CLASS_MP3_DIR,
    #     MEDIA_DIR,
    #     KOREAN_CLASS_COPIED_PREFIX
    # )
    # hosgeldi_table = HosgeldiWordTable(
    #     HOSGELDI_LOOKUP_TABLE_FILENAME,
    #     HOSGELDI_MP3_DIR,
    #     MEDIA_DIR,
    #     HOSGELDI_COPIED_PREFIX
    # )
    master_table = create_korean_table()

    from anki import Collection

    col = Collection(args.collection)
    deckid = col.decks.id(args.deck_name)
    col.decks.select(deckid)

    model = col.models.byName(args.model_name)
    deck = col.decks.get(deckid)
    deck['mid'] = model['id']
    col.decks.save(deck)

    cardids = col.findCards('deck:"%s" Audio:' % args.deck_name)
    #noteids = col.findNotes('deck:"%s"' % args.deck_name)
    logging.info('Found %d cards in "%s" deck', len(cardids), args.deck_name)

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
                     cardid, word, note[args.korean_audio_field], note[args.translated_word_field][:10])

        new_audio_field = ''
        # entries = korean_class_table.lookup(word)[:MAX_AUDIO_COUNT]
        # entries += hosgeldi_table.lookup(word)[:MAX_AUDIO_COUNT]
        entries = master_table.lookup(word)[:1]
        for entry in entries:
            logging.info('Entry: "%s"', entry)

            if not args.dry_run and not exists(entry.mp3to):
                logging.info('Copying "%s" to "%s"',
                             entry.mp3from, entry.mp3to)
                copy2(entry.mp3from, entry.mp3to)

            new_audio_field += '[sound:%s]' % entry.mp3tobase

        if entries:
            logging.info('New audio field: "%s"', new_audio_field)
            note[args.korean_audio_field] = new_audio_field
            if not args.dry_run:
                note.flush()
            updated_count += 1

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
