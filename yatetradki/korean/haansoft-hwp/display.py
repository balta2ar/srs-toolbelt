import sys
from struct import unpack

import fire


def read_pair(file_, offset, title_len, article_len):
    file_.seek(offset, 0)
    title = file_.read(title_len)
    article = file_.read(article_len)
    return title, article


def display(data_filename, index_filename, selected_words):
    with open(data_filename, 'rb') as data, open(index_filename, 'rb') as index:
        while index:
            block = index.read(3 * 4)
            if not block:
                break
            offset, title_len, article_len = unpack('<III', block)
            #msg = '%s %s %s' % (offset, title_len, article_len)
            msg = '%s %s %s' % (offset, title_len, article_len)
            # sys.stdout.buffer.write(msg.encode('utf8'))
            # sys.stdout.buffer.write('\n'.encode('utf8'))
            # print(offset, title_len, article_len)
            title, article = read_pair(data, offset, title_len, article_len)

            if selected_words:
                if title.decode('utf8') in selected_words:
                    sys.stdout.buffer.write(title)
                    sys.stdout.buffer.write('\n'.encode('utf8'))
                    sys.stdout.buffer.write(article)
                    sys.stdout.buffer.write('\n'.encode('utf8'))
            else:
                sys.stdout.buffer.write(title)
                sys.stdout.buffer.write('\n'.encode('utf8'))

            # print('')
            #sys.stdout.buffer.write(article)
            #print('')
            # print(article)
            # print(article.decode('utf8'))
            #msg = ('%s: %s' % (title, article.decode('utf8'))).encode('utf8')
            #print(msg)


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


if __name__ == '__main__':
    # data_filename, index_filename = sys.argv[1:3]
    # display(data_filename, index_filename)
    fire.Fire(Executor)
