# vim: set fileencoding=utf-8 :

from sys import exit
from json import loads
from requests import Session
from requests.utils import dict_from_cookiejar
from requests.utils import cookiejar_from_dict
from bs4 import BeautifulSoup
from codecs import open as codecs_open
from pickle import load as pickle_load
from pickle import dump as pickle_dump
from argparse import ArgumentParser


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


URL_COPYBOOKS = 'https://slovari.yandex.ru/~%D1%82%D0%B5%D1%82%D1%80%D0%B0%D0%B4%D0%BA%D0%B8/0/'
URL_PART_PASSPORT = 'passport.yandex.ru/passport?mode=auth'
URL_PASSPORT = 'https://passport.yandex.ru/passport'
COOKIE_JAR = 'cookiejar.dat'


def get_urls_containing(content, substring):
    soup = BeautifulSoup(content)
    links = [link.get('href') for link in soup.find_all('a')]
    valid = filter(lambda x: substring in x, filter(None, links))
    return valid


def clear_words(words):
    return filter(lambda line: len(line[4]) < 200, words)


def print_words(words):
    for langfrom, langto, _, wordfrom, wordto, _ in words:
        print(u'{0} -> {1} | {2:30} {3}'
              .format(langfrom, langto, wordfrom, wordto))


def save(reply):
    with codecs_open('reply.html', encoding='utf-8', mode='w') as f:
        f.write(reply)


def main():
    #enable_debug()

    parser = ArgumentParser(description='Yandex.Slovari/Tetradki words extractor.')
    parser.add_argument('--login', type=str, default=None, help='Login to Yandex')
    parser.add_argument('--password', type=str, default=None, help='Password')
    args = parser.parse_args()

    if None in (args.login, args.password):
        print('Please specify login and password')
        return 1

    session = Session()
    try:
        with open(COOKIE_JAR) as f:
            session.cookies = cookiejar_from_dict(pickle_load(f))
    except IOError:
        print('Could not load cookies from {0}'.format(COOKIE_JAR))

    responce = session.get(URL_COPYBOOKS)
    # soup = BeautifulSoup(responce.content)

    passport_urls = get_urls_containing(responce.content, URL_PART_PASSPORT)
    if len(passport_urls) == 0:
        print('already authenticated')
    elif len(passport_urls) == 1:
        auth_url = passport_urls[0]
        print('needs authentication at: %s' % auth_url)
        # sleep(3.0)
        print('go')
        params = {'mode': 'auth',
                  'msg': 'slovari',
                  'retpath': URL_COPYBOOKS}
        data = {'login': args.login,
                'passwd': args.password,
                'retpath': URL_COPYBOOKS}
        responce = session.post(URL_PASSPORT,
                                params=params,
                                data=data,
                                allow_redirects=True)
        # from ipdb import set_trace; set_trace()
        print(responce.status_code, responce.history)
        save(responce.content.decode('utf8'))
    else:
        print('too many passport urls on the page, dont know what to do')

    with open(COOKIE_JAR, 'w') as f:
        pickle_dump(dict_from_cookiejar(session.cookies), f)

    soup = BeautifulSoup(responce.content)
    dirty_words = filter(None,
                         [x.get('data-words')
                          for x in soup.find_all('div')])[0]
    # save(dirty_words)
    words = clear_words(loads(dirty_words))[-10:]
    #print(words)
    #print(type(words))

    print_words(words)

    # from ipdb import set_trace; set_trace()


if __name__ == '__main__':
    exit(main())


'''
Things to implement

Usage:
    http://bnc.bl.uk/saraWeb.php?qy=gruesome

Thesaurus:
    http://www.thesaurus.com/browse/intact?s=ts

http://www.thefreedictionary.com/gruesome

No results from thesaurus: "no thesaurus results"

Sample output:

en -> ru | scrotum       мошонка       flawless perfect unblemished unbroken unharmed unhurt unscathed untouched
                                       broken damaged flawed harmed hurt imperfect injured

'''
