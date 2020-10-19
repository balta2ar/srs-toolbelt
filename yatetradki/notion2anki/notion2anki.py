"""
Module that implements a class that sends zip file from notion
to notion2anki server for conversion to apkg.
"""

import requests

from yatetradki.tools.io import Blob, requests_enable_debug
from yatetradki.tools.log import get_logger

_logger = get_logger('anki_convert_notion2anki')

"""
"deckName"

Content-Disposition: form-data; name="template"
specialstyle
Content-Disposition: form-data; name="tags"
on
Content-Disposition: form-data; name="basic"
on
Content-Disposition: form-data; name="cloze"
on
Content-Disposition: form-data; name="toggle-mode"
open_toggle
Content-Disposition: form-data; name="font-size"
20
"""


class Notion2Anki:
    # UPLOAD_URL = 'https://2anki.net/upload'
    ORIGIN_URL = 'https://dev.2anki.net'
    UPLOAD_URL = ORIGIN_URL + '/upload'

    def __init__(self):
        self._session = requests.Session()

    def upload(self, blob: Blob) -> Blob:
        # requests_enable_debug()
        # self._session.get(self.UPLOAD_URL)
        files = {'pakker': ('notion.zip', blob.data())}
        data = {
            "deckName": "",
            "template": "specialstyle",
            "tags": "on",
            "basic": "on",
            "cloze": "on",
            "toggle-mode": "open_toggle",
            "font-size": "20",
        }
        headers = {
            'Origin': self.ORIGIN_URL,
            'Referer': self.UPLOAD_URL,
        }
        response = self._session.post(self.UPLOAD_URL, files=files, data=data, headers=headers)
        response.raise_for_status()
        _logger.info("received reply from notion2anki: code %s, %d bytes",
                     response.status_code, len(response.content))
        return Blob(response.content)
