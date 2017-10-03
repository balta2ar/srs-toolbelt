"""
This script converts sample Korean-Russian sentences from format A to format B.

In Format A the korean part is the line that contains at least one Hangul
character. Russian parts do not contain Hangul.

Format A:

사업가. 치약.
Предприниматель. Зубная паста.

Format B (tsv):

korean\trussian

After conversion:

Front: 사업가. 치약.
Back: Предприниматель. Зубная паста.

"""

import sys
import re


RE_HANGUL = re.compile('.*[ㄱ-힣].*')


def is_hangul(text):
    return RE_HANGUL.match(text) is not None


def convert_file(filename):
    pairs = []
    with open(filename) as file_:
        left, right = '', ''
        for line in file_:
            line = line.strip()
            if not line:
                if left or right:
                    pairs.append('%s\t%s' % (left, right))
                    left, right = '', ''
                continue

            if is_hangul(line):
                left += '<p>' + line + '</p>'
            else:
                right += '<p>' + line + '</p>'
            # print('HANGUL', line, is_hangul(line))
        if left or right:
            pairs.append('%s\t%s' % (left, right))
    return '\n'.join(pairs)


def main(args):
    for filename in args:
        print(convert_file(filename))


if __name__ == '__main__':
    main(sys.argv[1:])
