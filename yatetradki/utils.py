from codecs import open as codecs_open
from json import loads as json_loads
from netrc import netrc
from os import dup, fdopen, popen, environ
from os.path import expanduser, expandvars
from re import sub
from bs4 import BeautifulSoup

from pydub import AudioSegment


DEFUALT_WIDTH = 100


def enable_debug():
    import logging

    # These two lines enable debugging at httplib level (requests->urllib3->http.client)
    # You will see the REQUEST, including HEADERS and DATA, and RESPONSE with HEADERS but without DATA.
    # The only thing missing will be the response.body which is not logged.
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


def mute_networking_logging():
    import logging
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)


def save(reply, filename='reply.html'):
    with codecs_open(filename, encoding='utf-8', mode='w') as f:
        f.write(reply)


def get_terminal_width():
    try:
        rows, columns = popen('stty size', 'r').read().split()
        return int(rows), int(columns)
    except ValueError:
        return 0, 0


def get_terminal_width_fallback(width):
    term_width = width
    if not width:
        _, width = get_terminal_width()
        term_width = width
        if not width:
            #print('Could not determine terminal size, using default {0}'
            #      .format(DEFUALT_WIDTH))
            term_width = DEFUALT_WIDTH
    return term_width


def load_colorscheme(path):
    if not path:
        return None
    with open(path) as f:
        return json_loads(f.read())


def load_credentials_from_netrc(host):
    try:
        rc = netrc()
    except IOError:
        # could not open ~/.netrc
        return None, None
    auth = rc.authenticators(host)
    if not auth:
        return None, None
    login, account, password = auth
    return login, password


def text_cleanup(text):
    return sub('\s{2,}', ' ', text.strip())


def cleanup_query(query: str) -> str:
    return query.replace('"', '')


def cleanup_filename(name: str) -> str:
    name = name.lower().replace(' ', '_')
    def valid(x):
        return x.isalnum() or x in '_'
    name = ''.join([x for x in name if valid(x)])
    return name


def html_to_text(data: str) -> str:
    soup = BeautifulSoup(data, features="lxml")
    return soup.get_text()


def open_output(filename, mode):
    if filename is None or filename == '-':
        return fdopen(dup(2), mode)
    else:
        return open(filename, mode)


def convert_wav_to_mp3(filename_wav, filename_mp3):
    sound = AudioSegment.from_wav(filename_wav)
    sound.export(filename_mp3, format='mp3')


def must_env(name):
    value = expandvars(expanduser(environ.get(name, '')))
    if not value:
        raise RuntimeError('env var "{0}" must be set'.format(name))
    return value
