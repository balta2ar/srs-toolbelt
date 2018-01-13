import logging

from requests import get
from requests.exceptions import RequestException

from yatetradki.korean.memrise.common import DEFAULT_LOGGER_NAME


_logger = logging.getLogger(DEFAULT_LOGGER_NAME)


class UserScriptInjector:
    SERVER_STATUS_URL = 'https://localhost:5000/api/get_audio/집'
    # SERVER_FILE_TEMPLATE = 'https://localhost:5000/api/get_file/%s'
    FILES_TO_INJECT = [
        'jquery.min.js',
        'userscript_stubs.js',  # Provides a replacement for GM_xmlhttpRequest
        'memrise_client.js'
    ]
    SCRIPT_TEMPLATE = '''
var s = window.document.createElement('script');
s.src = '%s';
window.document.head.appendChild(s);
'''

    def __init__(self, driver):
        self._driver = driver

    def _server_available(self):
        try:
            response = get(self.SERVER_STATUS_URL, verify=False)
            return response.status_code == 200 \
                and response.json()['success'] is True
        except RequestException as e:
            _logger.info('Pronunciation server is not available: %s', e)
        return False

    def _inject_js_file(self, filename):
        # url = self.SERVER_FILE_TEMPLATE % filename
        # script = self.SCRIPT_TEMPLATE % url
        with open(filename) as file_:
            script = file_.read()
        self._driver.execute_script(script)

    def inject(self):
        if not self._server_available():
            return False

        _logger.info('Pronunciation server is available, proceeding')
        for filename in self.FILES_TO_INJECT:
            _logger.info('Injecting file %s', filename)
            self._inject_js_file(filename)

        _logger.info('UserScript JS files have been injected')
        return True
