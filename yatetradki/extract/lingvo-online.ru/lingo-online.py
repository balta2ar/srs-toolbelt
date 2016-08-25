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


def main():
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

    print('Logging in', file=stderr)
    result = session.get('https://www.lingvo-online.ru/ru/Account/DoLogin', params=params)
    if result.status_code != 200:
        print('Could not login', file=stderr)
        exit(1)

    print('Getting first page of history', file=stderr)
    result = session.get('http://www.lingvo-online.ru/ru/Search/History')
    if result.status_code != 200:
        print('Could not get the first page', file=stderr)
        exit(2)

    collected_words = []

    soup = BeautifulSoup(result.content, 'lxml')
    history_data = soup.find('div', class_='js-history-data')
    words = history_data.find_all('a', class_='l-searchHistory__historyLink')
    collected_words.extend([word.text for word in words])

    # Limit number of requested pages
    for i in range(1, 51):
        print('Getting page #%s of history' % i, file=stderr)
        result = session.get('http://www.lingvo-online.ru/ru/Search/History',
                             params={'pageNumber': str(i)})
        if result.status_code != 200:
            print('Could not get the page #%s' % i, file=stderr)
            exit(3)

        # Empty page
        if len(result.content) < 10:
            print('Page #%s is empty, terminating' % i, file=stderr)
            break

        soup = BeautifulSoup(result.content, 'lxml')
        words = soup.find_all('a', class_='l-searchHistory__historyLink')
        collected_words.extend([word.text for word in words])
    else:
        print('Reached maximum number of pages: #%s' % i, file=stderr)

    print('\n'.join(set(collected_words)))


if __name__ == '__main__':
    main()
