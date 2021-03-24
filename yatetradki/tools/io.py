import hashlib
import logging
from os.path import exists, getsize

from yatetradki.tools.log import get_logger

_logger = get_logger('anki_tools_io')


def requests_enable_debug():
    try:
        import http.client as http_client
    except ImportError:
        # Python 2
        import httplib as http_client
    http_client.HTTPConnection.debuglevel = 1

    # You must initialize logging, otherwise you'll not see debug output.
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True


def get_file_hash(filename: str) -> str:
    return Blob.read(filename).checksum()


def spit(filename: str, data: bytes) -> None:
    with open(filename, 'wb') as f:
        f.write(data)


def slurp(filename: str) -> bytes:
    with open(filename, 'rb') as f:
        return f.read()


class Blob:
    def __init__(self, data: bytes):
        self._data: bytes = data

    @staticmethod
    def read(filename: str):
        return Blob(slurp(filename))

    def data(self) -> bytes:
        return self._data

    def __len__(self) -> int:
        return len(self._data)

    def checksum(self) -> str:
        crc = hashlib.sha512()
        crc.update(self._data)
        return crc.hexdigest()

    def same_as(self, filename: str) -> bool:
        return exists(filename) and (getsize(filename) == len(self))

    def save_if_different(self, filename: str) -> None:
        if self.same_as(filename):
            _logger.info('checksum of %s is the same', filename)
            return

        self.save(filename)

    def save(self, filename: str) -> None:
        spit(filename, self._data)
        _logger.info('saved %d bytes into %s', len(self._data), filename)
