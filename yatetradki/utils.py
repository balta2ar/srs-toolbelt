from os import popen
from json import loads as json_loads
from codecs import open as codecs_open


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
