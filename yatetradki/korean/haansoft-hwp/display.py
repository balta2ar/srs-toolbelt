import re
import sys
from struct import unpack

import fire


RX_NEWLINE = re.compile('\r\n')
RX_WORD_PLACEHOLDER = re.compile('∼')
COLLOCATION_MARKER = '♣'
EXAMPLE_MARKER = '┈┈•'


def read_pair(file_, offset, title_len, article_len):
    file_.seek(offset, 0)
    title = file_.read(title_len)
    article = file_.read(article_len)
    return title, article


def iter_words_utf8(data_filename, index_filename):
    with open(data_filename, 'rb') as data, open(index_filename, 'rb') as index:
        while index:
            block = index.read(3 * 4)
            if not block:
                break
            offset, title_len, article_len = unpack('<III', block)
            #msg = '%s %s %s' % (offset, title_len, article_len)
            # msg = '%s %s %s' % (offset, title_len, article_len)
            # sys.stdout.buffer.write(msg.encode('utf8'))
            # sys.stdout.buffer.write('\n'.encode('utf8'))
            # print(offset, title_len, article_len)
            title, article = read_pair(data, offset, title_len, article_len)
            yield title, article


def display(data_filename, index_filename, selected_words):
    for title_utf8, article_utf8 in iter_words_utf8(data_filename, index_filename):
        if selected_words:
            if title_utf8.decode('utf8') in selected_words:
                sys.stdout.buffer.write(title_utf8)
                sys.stdout.buffer.write('\n'.encode('utf8'))
                sys.stdout.buffer.write(article_utf8)
                sys.stdout.buffer.write('\n'.encode('utf8'))
        else:
            sys.stdout.buffer.write(title_utf8)
            sys.stdout.buffer.write('\n'.encode('utf8'))


def prettify(word, article):
    new_article = RX_NEWLINE.sub('\n', article)
    new_article = RX_WORD_PLACEHOLDER.sub('~', new_article)
    result = []

    prev_line = None
    for index, line in enumerate(new_article.split('\n')):
        clean_line = line.strip()

        if index == 0 or prev_line == '':
            # print(word, file=sys.stderr)
            fixed_line = '[m1][b]%s[/b][/m]' % clean_line
        elif clean_line.startswith(COLLOCATION_MARKER):
            fixed_line = '[m2][i]%s[/i][/m]' % clean_line[len(COLLOCATION_MARKER):]
        elif clean_line.startswith(EXAMPLE_MARKER):
            fixed_line = '[m2][ex]%s[/ex][/m]' % clean_line[len(EXAMPLE_MARKER):]
        else:
            fixed_line = clean_line
            if clean_line != '':
                fixed_line = '[m1]%s[/m]' % clean_line
        prev_line = clean_line

        result.append(fixed_line)

    return result
    # return '\n'.join(result)


def convert_to(data_filename, index_filename, output_file):
    seen_titles = set()
    count = 0
    for title_utf8, article_utf8 in iter_words_utf8(data_filename, index_filename):
        if title_utf8 in seen_titles:
            continue

        seen_titles.add(title_utf8)

        output_file.write(title_utf8.decode('utf8'))
        output_file.write('\n')

        title = title_utf8.decode('utf8')
        article = article_utf8.decode('utf8')
        # article = prettify(title, article)
        lines = prettify(title, article)

        for line in lines: # article.split('\n'):
            # line_utf8 = line.encode('utf8')
            # line = line.strip(' \t\n\r')
            output_file.write('\t')
            output_file.write(line)
            output_file.write('\n')
        output_file.write('\t\n')

        count += 1
        if count > 100:
            break


class Executor:
    def __init__(self, dict, index):
        self._dict = dict
        self._index = index

    def word(self, word, article=False):
        if article:
            # print(word)
            display(self._dict, self._index, [word])
        else:
            display(self._dict, self._index, None)

    def convert(self, output, name, lang_from, lang_to):
        with open(output, 'w') as file_:
            file_.write('#NAME\t"%s"\n' % name)
            file_.write('#INDEX_LANGUAGE\t"%s"\n' % lang_from)
            file_.write('#CONTENTS_LANGUAGE\t"%s"\n' % lang_to)
            convert_to(self._dict, self._index, file_)


if __name__ == '__main__':
    # data_filename, index_filename = sys.argv[1:3]
    # display(data_filename, index_filename)
    fire.Fire(Executor)
