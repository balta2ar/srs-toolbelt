import sys
from os.path import basename
from bs4 import BeautifulSoup


def clean_idiom(filename):
    with open(filename) as file_object:
        soup = BeautifulSoup(file_object.read(), 'lxml')

    main_txt = soup.find('div', {'id': 'MainTxt'})
    if main_txt is None:
        print('Could not find MainTxt')
        return

    [x.extract() for x in main_txt.findAll('div', class_='SeeAlso')]

    output_filename = 'idioms_dump_clean/{0}'.format(basename(filename))
    with open(output_filename, 'w') as file_object:
        file_object.write(main_txt.prettify('utf-8'))


def main(argv):
    for filename in argv:
        clean_idiom(filename)


if __name__ == '__main__':
    main(sys.argv[1:])
