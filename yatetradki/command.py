# encoding=utf8
import logging
from multiprocessing.dummy import Pool as ThreadPool
from threading import Lock

from yatetradki.sites.units.tetradki import YandexTetradki
from yatetradki.sites.articles.slovari import YandexSlovari, format_jinja2
from yatetradki.sites.articles.thesaurus import Thesaurus
from yatetradki.sites.articles.freedict import TheFreeDictionary
from yatetradki.sites.articles.bnc import BncSimpleSearch
from yatetradki.sites.articles.priberam import Priberam
from yatetradki.sites.articles.idioms import IdiomsTheFreeDictionary

from yatetradki.formatters.anki import Anki

from yatetradki.pretty import Prettifier
# from yatetradki.cache import PickleCache
from yatetradki.cache import EvalReprTsvCache
from yatetradki.utils import open_output
from yatetradki.utils import load_colorscheme
from yatetradki.utils import get_terminal_width_fallback
from yatetradki.utils import load_credentials_from_netrc
from yatetradki.types import CachedWord


_logger = logging.getLogger()


COOKIE_JAR = 'cookiejar.dat'
NETRC_HOST = 'YandexTetradki'


def fetch_word(args):
    # cmd = Commander(args)
    for word in args.words:
        # print(word)
        slovari = YandexSlovari()
        data = slovari.find(word)
        anki = Anki(data)
        print(anki().encode('utf8'))


#
# # XXX: rename me later
# class Commander(object):
#     def __init__(self, args):
#         self._args = args
#
#         self._thesaurus = Thesaurus()
#         self._freedict = TheFreeDictionary()
#         self._bnc = BncSimpleSearch()
#
#     def fetch_words(self, words):
#         thesaurus_word = thesaurus.find(word.wordfrom)
#         freedict_word = freedict.find(word.wordfrom)
#         bnc_word = bnc.find(word.wordfrom)
#

class WordFetcherer(object):
    def __init__(self, cache):
        self._cache = cache

    def __call__(self, words, num_jobs):
        self._words = words
        self._words_fetched = [0]
        self._cache_lock = Lock()

        if num_jobs > 1:
            pool = ThreadPool(num_jobs)
            pool.map(self._process_word, enumerate(words))
            pool.close()
            pool.join()
        else:
            map(self._process_word, enumerate(words))

        if self._words_fetched[0]:
            _logger.info('{0} new words fetched'
                         .format(self._words_fetched[0]))

    def _process_word(self, pair):
        i, word = pair
        word_value = self._word_value(word)
        # TODO: deal with this ugly locks
        with self._cache_lock:
            if self._cache.contains(word_value):
                return

        _logger.info(u'Fetching {0}/{1}: {2}'
                     .format(i + 1, len(self._words), word_value))
        try:
            fetch_result = self._fetch(word)
            if fetch_result is None:
                return
        except Exception as e:
            _logger.exception(u'Could not fetch word {0} ({1})'
                              .format(word_value, str(e)))
        else:
            with self._cache_lock:
                key, value = self._save(word, fetch_result)
                self._cache.put(key, value)
                # self._cache.put(word_value,
                #           CachedWord(word, slovari_word, thesaurus_word,
                #                      freedict_word, bnc_word))
                self._words_fetched[0] += 1
                self._cache.flush() # save early
            _logger.info(u'Fetched {0}'.format(word_value))

    def _fetch(self, word):
        raise NotImplementedError

    def _save(self, fetch_result):
        raise NotImplementedError

    def _word_value(self, word):
        raise NotImplementedError


class SlovariWordFetcherer(WordFetcherer):
    def __init__(self, cache):
        super(SlovariWordFetcherer, self).__init__(cache)
        self._thesaurus = Thesaurus()
        self._freedict = TheFreeDictionary()
        self._bnc = BncSimpleSearch()
        self._slovari = YandexSlovari()

    def _fetch(self, word):
        slovari_word = self._slovari.find(word.wordfrom)
        thesaurus_word = self._thesaurus.find(word.wordfrom)
        freedict_word = self._freedict.find(word.wordfrom)
        bnc_word = self._bnc.find(word.wordfrom)
        return slovari_word, thesaurus_word, freedict_word, bnc_word

    def _save(self, word, fetch_result):
        slovari_word, thesaurus_word, freedict_word, bnc_word = fetch_result
        return self._word_value(word), CachedWord(
            word, slovari_word, thesaurus_word, freedict_word, bnc_word)

    def _word_value(self, word):
        return word.wordfrom


class IdiomsTheFreeDictionaryWordFetcherer(WordFetcherer):
    def __init__(self, cache):
        super(IdiomsTheFreeDictionaryWordFetcherer, self).__init__(cache)
        self._idioms = IdiomsTheFreeDictionary()

    def _fetch(self, word):
        idiom = self._idioms.find(word)
        return idiom

    def _save(self, word, fetch_result):
        idiom = fetch_result
        return self._word_value(word), idiom

    def _word_value(self, word):
        return word.decode('utf8')


class PriberamWordFetcherer(WordFetcherer):
    def __init__(self, cache):
        super(PriberamWordFetcherer, self).__init__(cache)
        self._priberam = Priberam()

    def _fetch(self, word):
        return self._priberam.find(word)

    def _save(self, word, fetch_result):
        return self._word_value(word), fetch_result

    def _word_value(self, word):
        return word.decode('utf8')


def fetch(args):
    if args.fetcher is None:
        _logger.error('Please specify fetcher name (--fetcher <name>)')

    elif args.fetcher == 'YandexTetradki':
        if None in (args.login, args.password):
            login, password = load_credentials_from_netrc(NETRC_HOST)
            if None in (login, password):
                _logger.error('Please specify login and password')
                return 1
            args.login, args.password = login, password

        # yandex.slovari/tetradki
        cache = EvalReprTsvCache(args.cache)
        slovari = YandexTetradki(args.login, args.password, COOKIE_JAR)
        words = slovari.newest(args.num_words)
        fetcherer = SlovariWordFetcherer(cache)
        fetcherer(words, args.jobs)

    elif args.fetcher == 'Idioms':
        # idioms.thefreedictionary.com
        words = [line.strip() for line in open(args.words_filename).readlines()]
        words = words[:args.num_words]
        cache = EvalReprTsvCache(args.cache)
        fetcherer = IdiomsTheFreeDictionaryWordFetcherer(cache)
        fetcherer(words, args.jobs)

    elif args.fetcher == 'Priberam':
        # Priberam
        words = [line.strip() for line in open(args.words_filename).readlines()]
        words = words[:args.num_words]
        cache = EvalReprTsvCache(args.cache)
        fetcherer = PriberamWordFetcherer(cache)
        fetcherer(words, args.jobs)


def export(args):
    cache = EvalReprTsvCache(args.cache)
    words = cache.newest(args.num_words)
    _export_words(args, cache, words)


def _anki(word):
    string = Anki(word.slovari_word)()
    return u'\n{0}'.format(string).encode('utf8')


def _anki_jinja2(word):
    front, back = format_jinja2(word, 'slovari/front.jinja2', 'slovari/back.jinja2')
    front = front.replace('\n', '')
    back = back.replace('\n', '')
    # We put three fields separated with tabs:
    # Front
    # Back
    # Word -- this one will be used by AwesomeTTS to find sound for the word
    return u'\n{0}\t{1}\t{2}'.format(front, back, word.wordfrom).encode('utf8')
    #return u'\n{0}\t{1}'.format(front, back).encode('utf8')


def _anki_idioms(word):
    front, back = format_jinja2(word, 'idioms/front.jinja2', 'idioms/back.jinja2')
    front = front.replace('\n', '')
    back = back.replace('\n', '')
    return u'\n{0}\t{1}'.format(front, back).encode('utf8')


def _anki_priberam(word):
    front, back = format_jinja2(word, 'priberam/front.jinja2', 'priberam/back.jinja2')
    front = front.replace('\n', '')
    back = back.replace('\n', '')
    return u'\n{0}\t{1}'.format(front, back).encode('utf8')


def _export_words(args, cache, words):
    cached_words = filter(None, map(cache.get, words))
    if args.formatter == 'Anki':
        with open_output(args.output, 'w') as output:
            output.writelines(_anki(word) for word in cached_words)
    elif args.formatter == 'AnkiJinja2':
        with open_output(args.output, 'w') as output:
            output.writelines(_anki_jinja2(word.slovari_word)
                              for word in cached_words)
    elif args.formatter == 'AnkiIdioms':
        with open_output(args.output, 'w') as output:
            output.writelines(_anki_idioms(word)
                              for word in cached_words)
    elif args.formatter == 'AnkiPriberam':
        with open_output(args.output, 'w') as output:
            output.writelines(_anki_priberam(word)
                              for word in cached_words)


def _add_numbers(text):
    lines = text.splitlines()
    lines = [u'{0:03} {1}'.format(i + 1, line) for i, line in enumerate(lines)]
    return u'\n'.join(lines)


def _show_words(args, cache, words):
    prettifier = Prettifier(load_colorscheme(args.colors),
                            get_terminal_width_fallback(args.width),
                            args.height, args.num_columns, args.delim)

    cached_words = filter(None, map(cache.get, words))
    result = prettifier(cached_words)
    if args.numbers:
        result = _add_numbers(result)
    print(result.encode('utf-8'))

    words_missing = len(words) - len(cached_words)
    if words_missing:
        _logger.error('Could not load {0} words from cache'.format(words_missing))


def show(args):
    if args.num_columns:
        args.num_words = 0

    # cache = PickleCache(args.cache)
    cache = EvalReprTsvCache(args.cache)
    words = cache.newest(args.num_words)
    # words = cache.order
    # words = words[:args.num_words] if args.num_words else words
    _show_words(args, cache, words)


def list_words(args):
    # cache = PickleCache(args.cache)
    cache = EvalReprTsvCache(args.cache)
    words = cache.order
    cached_words = filter(None, map(cache.get, words))
    result = u'\n'.join([x.tetradki_word.wordfrom for x in cached_words])
    print(result.encode('utf-8'))


def word(args):
    # cache = PickleCache(args.cache)
    cache = EvalReprTsvCache(args.cache)
    _show_words(args, cache, args.words)
