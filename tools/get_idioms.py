import sys
from bs4 import BeautifulSoup


def get_idioms(filename):
    with open(filename) as file_object:
        soup = BeautifulSoup(file_object.read(), 'lxml')
        suggestions = soup.find_all('ul', class_='suggestions')
        result = []
        for suggestion in suggestions:
            for idiom in suggestion.find_all('li'):
                result.append(idiom.text)
        return result


def main(argv):
    for filename in argv:
        print('\n'.join(get_idioms(filename)))


if __name__ == '__main__':
    main(sys.argv[1:])
