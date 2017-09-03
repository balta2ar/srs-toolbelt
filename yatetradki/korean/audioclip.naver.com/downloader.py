import sys
import threading
import queue
import subprocess
import logging

_logger = logging.getLogger('downloader')


class ThreadedDownloader:
    def __init__(self, logger):
        self._download_thread = threading.Thread(target=self._download_routine)
        self._download_queue = queue.Queue()

        self._download_thread.start()

    def _download_routine(self):
        while True:
            try:
                item = self._download_queue.get()
                if item is None:
                    break
                filename, url = item
                _logger.info('Starting download: url "%s" into file "%s"', url, filename)
                subprocess.run(['aria2c', '--continue=true', '-o', filename, url], stdout=sys.stdout)
                _logger.info('Download finished: url "%s" into file "%s"', url, filename)
            except Exception:
                _logger.exception('Error in the downloader thread')

    def add(self, filename, url):
        self._download_queue.put((filename, url))

    def join(self):
        self._download_queue.put(None)
        self._download_thread.join()


def main():
    logging.basicConfig(format='%(asctime)s %(levelname)s: (%(name)s) %(message)s',
                        level=logging.INFO)
    _downloader = ThreadedDownloader(_logger)

    url = "https://ssl.phinf.net/audio/20161024_154/1477296007608SF5kK_JPEG/%B0%A3%B4%DC%C8%F7%BA%B8%B4%C2%C7%D1%B1%B9%C0%C7%C1%F6%B8%AE.jpeg"
    filename = "./test/1.jpg"
    _downloader.add(filename, url)
    _downloader.add("./test/2.jpg", url)
    _downloader.add("./test/3.jpg", url)
    _downloader.join()
    _logger.info('Leaving')


if __name__ == '__main__':
    main()
