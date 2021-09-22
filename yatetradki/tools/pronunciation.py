from os.path import basename

from yatetradki.korean.fill_audio import CustomServiceWithFunction
from yatetradki.korean.fill_audio import create_cached_table
from yatetradki.korean.fill_audio import create_aws_norwegian_table
from yatetradki.korean.fill_audio import create_azure_norwegian_table
from yatetradki.korean.fill_audio import create_azure_english_table
from yatetradki.tools.audio import get_pronunciation_call
from yatetradki.tools.log import get_logger


#NORWEGIAN_PRONUNCIATION_TABLE = create_aws_norwegian_table()
NORWEGIAN_PRONUNCIATION_TABLE = create_azure_norwegian_table()
ENGLISH_PRONUNCIATION_TABLE = create_azure_english_table()


_logger = get_logger('pronunciation')


class Pronunciation:
    def __init__(self, audio_type):
        self._audio_type = audio_type
    def fill(self, word, col, fields):
        return fill_pronunciation(self._audio_type, word, col, fields)


def get_norwegian_pronunciation(word):
    """Should return a filename (mp3) with the pronounced word. None if not found."""
    results = NORWEGIAN_PRONUNCIATION_TABLE.lookup(word)
    if not results:
        return None
    return results[0].mp3from


def get_english_azure_pronunciation(word):
    """Should return a filename (mp3) with the pronounced word. None if not found."""
    results = ENGLISH_PRONUNCIATION_TABLE.lookup(word)
    if not results:
        return None
    return results[0].mp3from


def get_english_pronunciation(word):
    """Should return a filename (mp3) with the pronounced word. None if not found."""
    cache_dir = 'cache_english_awesometts'
    prefix = 'cache_english_awesometts_'
    english_service = CustomServiceWithFunction(prefix, get_pronunciation_call)
    results = create_cached_table(cache_dir, prefix, english_service).lookup(word)
    if not results:
        return None
    return results[0].mp3from


def fill_pronunciation(audio_type, word, col, fields):
    TABLE = {
        'norwegian': get_norwegian_pronunciation,
        'english': get_english_pronunciation,
        'english-azure': get_english_azure_pronunciation,
        #'english': get_pronunciation_call,
    }
    get_pronunciation = TABLE.get(audio_type)
    if get_pronunciation is None:
        _logger.warning('Pronunciation "%s" is not supported', audio_type)
        return False

    audio = get_pronunciation(word)
    if audio is None:
        _logger.warning('Could not add audio for word %s', word)
    else:
        _logger.debug('Adding audio for word %s: %s', word, audio)
        col.media.addFile(audio)
        fields['Audio'] = '[sound:%s]' % basename(audio)
    return True

