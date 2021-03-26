import logging
from yatetradki.utils import must_env

import requests

logging.getLogger("requests").setLevel(logging.WARNING)


ACCESS_TOKEN = must_env('TELEGRAM_ACCESS_TOKEN')
CHAT_ID = must_env('TELEGRAM_CHAT_ID')


def notify(message):
    data = "chat_id={0}&text={1}".format(CHAT_ID, message)
    url = "https://api.telegram.org/bot{0}/sendMessage?{1}".format(ACCESS_TOKEN, data)
    response = requests.post(url, data)
    response.raise_for_status()
