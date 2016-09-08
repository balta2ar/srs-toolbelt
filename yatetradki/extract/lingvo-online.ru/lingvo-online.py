#
# This script extracts your word history from linvgo-online.ru
# Make sure to add your credentials to ~/.netrc as follows:
#
# machine lingvo-online login your@email password yourpassword
#
# Run as follows:
# python lingvo-online.py > words-lingvo-online.txt
#
# Messages are printed to stderr, words are printed to stdout one per line.
#
from sys import stderr
from bs4 import BeautifulSoup
from requests import Session
from netrc import netrc
from collections import OrderedDict
import argparse
import logging


FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)


def main():
    parser = argparse.ArgumentParser(description='Grab word history from lingvo-online.ru')
    parser.add_argument('--num-pages', type=int, default=50,
                        help='Max numbers of history pages to scan')
    args = parser.parse_args()

    username, _, password = netrc().hosts['lingvo-online']

    session = Session()
    params = {
        'random_inhe4l63': '1',
        'callback': 'jQuery17203234328622929752_1461672587220',
        'back': '/ru/Search/History',
        'email': username,
        'password': password,
        'captchaText': '',
        'rememberMe': 'true',
        '_': '1461672601133'}

    logging.info('Logging in')
    result = session.get('https://www.lingvo-online.ru/ru/Account/DoLogin', params=params)
    if result.status_code != 200:
        logging.info('Could not login')
        exit(1)

    logging.info('Getting first page of history')
    result = session.get('http://www.lingvo-online.ru/ru/Search/History')
    if result.status_code != 200:
        logging.info('Could not get the first page')
        exit(2)

    collected_words = []

    soup = BeautifulSoup(result.content, 'lxml')
    history_data = soup.find('div', class_='js-history-data')
    words = history_data.find_all('a', class_='l-searchHistory__historyLink')
    collected_words.extend([word.text.lower() for word in words])

    # Limit number of requested pages
    logging.info('Scanning no more than %d pages', args.num_pages)
    for i in range(1, args.num_pages + 1):
        logging.info('Getting page #%s of history', i)
        result = session.get('http://www.lingvo-online.ru/ru/Search/History',
                             params={'pageNumber': str(i)})
        if result.status_code != 200:
            logging.info('Could not get the page #%s', i)
            exit(3)

        # Empty page
        if len(result.content) < 10:
            logging.info('Page #%s is empty, terminating', i)
            break

        soup = BeautifulSoup(result.content, 'lxml')
        words = soup.find_all('a', class_='l-searchHistory__historyLink')
        collected_words.extend([word.text.lower() for word in words])
    else:
        logging.info('Reached maximum number of pages: #%s', i)

    # remove duplicate words but keep the order
    collected_words = list(OrderedDict.fromkeys(collected_words))
    print('\n'.join(collected_words))


if __name__ == '__main__':
    main()
