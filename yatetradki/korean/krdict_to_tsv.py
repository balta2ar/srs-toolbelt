import re
import sys
import lzma
import logging
from os.path import isfile, expanduser, expandvars
from requests import get
from bs4 import BeautifulSoup


#CACHE_DIR = 'cache_krdict_html'
CACHE_DIR = '/mnt/data/prg/src/bz/python/yandex-slovari-tetradki/yatetradki/korean/cache_krdict_html'
KRDICT_URL = 'https://krdict.korean.go.kr/eng/dicSearch/search?nation=eng&nationCode=6&ParaWordNo=&mainSearchWord=%s'
SUBWORD_URL = 'https://krdict.korean.go.kr/eng/dicSearch/SearchView?wordMatchFlag=N&mainSearchWord=%s&currentPage=1&sort=W&searchType=W&proverbType=&exaType=&ParaWordNo=%s&nation=eng&nationCode=6&viewType=A&blockCount=10&viewTypes=on&myViewWord=73750&myViewWord=%s&myViewWord=30609&myViewWord=31788&myViewWord=15863'
#: Total number of examples in the preview section of a card.
TOTAL_MAX_EXAMPLES = 10
#: Maximum number of examples that are added to each translation.
SINGLE_WORD_ATTACHED_MAX_EXAMPLES = 5
#: Maximum number of examples that are added to the preview of the card.
#: This number is smaller so that preview is not too cluttered.
SINGLE_WORD_PREVIEW_MAX_EXAMPLES = 3


DEFAULT_LOG_LEVEL = 'INFO'
DEFAULT_LOGGER_NAME = 'krdict'
FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
logging.basicConfig(format=FORMAT, level=DEFAULT_LOG_LEVEL)
_logger = logging.getLogger(DEFAULT_LOGGER_NAME)


def spit(filename, data):
    compress = filename.endswith('.xz')
    fn_open = lzma.open if compress else open
    data = data.encode('utf8') if compress else data
    with fn_open(filename, 'w') as file_:
        file_.write(data)


def slurp(filename):
    compress = filename.endswith('.xz')
    fn_open = lzma.open if compress else open
    with fn_open(filename) as file_:
        data = file_.read()
        data = data.decode('utf8') if compress else data
        return data


def get_cached_word(word):
    filename = '%s/%s.html.xz' % (CACHE_DIR, word)
    if isfile(filename):
        return slurp(filename)

    url = KRDICT_URL % word
    _logger.info('getting word %s (%s)', word, url)
    request = get(url)
    spit(filename, request.text)
    return request.text


def get_cached_subword(word, subword):
    filename = '%s/%s-%s.html.xz' % (CACHE_DIR, word, subword)
    if isfile(filename):
        return slurp(filename)

    url = SUBWORD_URL % (word, subword, subword)
    _logger.info('getting subword %s %s (%s)', word, subword, url)
    request = get(url)
    spit(filename, request.text)
    return request.text


def clean(text):
    # return text.strip(': \n')
    # text = text.strip().replace('\n', '<br>').replace('\t', ' ')
    text = text.strip().replace('\t', ' ').replace('\n', '')
    # text = re.sub(r'<!--.*?-->', '', text)
    # text = re.sub(r'<script.*</script>', '', text)
    # text = re.sub(r'class="[^"]*"', '', text)
    # text = re.sub(r'href="[^"]*"', '', text)
    text = re.sub(r'href="[^"]*"', '', text)
    text = re.sub(r'style="[^"]*"', '', text)
    text = re.sub(r'title="[^"]*"', '', text)
    text = re.sub(r'\s+', ' ', text)
    text = text.replace(' ]', ']')
    # text = text.replace(' <b> ', ' <b>')
    # text = text.replace(' </b> ', '</b> ')
    return text


def clean_dots_from_tag(tag):
    text = str(tag) #tag.prettify()
    text = text.strip().replace('.', '').strip()
    return BeautifulSoup(text, 'html.parser')


def get_subword(tag):
    try:
        return int(re.search(r'.*\'(\d+)\'', tag.attrs['href']).group(1))
    except:
        return None


def fetch_subword_examples(word, tag):
    subword = get_subword(tag)
    if subword is None:
        return []

    soup = BeautifulSoup(get_cached_subword(word, subword), 'html.parser')
    examples = soup.select('div.word_explain_list ul li')
    examples = [clean_dots_from_tag(e) for e in examples]
    return examples


def add_examples(soup, where, examples):
    ul = soup.new_tag('ul')
    for example in examples:
        ul.append(example)

    div = soup.new_tag('div', **{'class': 'examples'})
    div.append(ul)
    where.append(div)


def fetch_word(word):
    soup = BeautifulSoup(get_cached_word(word), 'html.parser')
    article = soup.select_one('ul.search_list.printArea')
    if article is None:
        return None, None

    article0 = soup.select_one('ul.search_list.printArea > li#article0')
    if article0 is None:
        return None, None

    examples = []

    for tag_img in article.select('img'):
        tag_img.extract()
    for tag_a in article.select('a[href*="javascript"]'):
        strong = tag_a.find('strong')
        if strong is None:
            # First try to extract examples
            subword_examples = fetch_subword_examples(word, tag_a)
            add_examples(soup, tag_a.parent.parent,
                         subword_examples[:SINGLE_WORD_ATTACHED_MAX_EXAMPLES])
            if len(examples) < TOTAL_MAX_EXAMPLES:
                examples.extend(subword_examples[:SINGLE_WORD_PREVIEW_MAX_EXAMPLES])
                examples = examples[:TOTAL_MAX_EXAMPLES]
            # parent = tag_a.parent.parent
            # from ipdb import set_trace; set_trace()

            tag_a.extract()

    #examples = [clean(e.prettify()) for e in examples]
    examples = [clean(str(e)) for e in examples]
    examples = '<ul>' + ''.join(examples) + '</ul>'
    print(examples)

    # examples = soup.select('p[class="sub_p1"]')
    # examples = '<ul>' + ''.join(['<li>%s</li>' % e.text.strip() for e in examples]) + '</ul>'
    #article = clean(article.prettify())
    article = clean(str(article))
    # from ipdb import set_trace; set_trace()

    return examples, article


def word_to_entry(word):
    examples, article = fetch_word(word)
    examples = examples if examples is not None else ''
    if article is None:
        return None
    _logger.info('Adding %s', word)
    return '%s\t%s\t%s'% (word, examples, article)


def convert_file(input_filename, output_filename):
    words = [line.strip() for line in open(input_filename).readlines()]
    articles = list(filter(None, (word_to_entry(word) for word in words)))
    _logger.info('Added %s words', len(articles))
    spit(output_filename, '%s\n' % '\n'.join(articles))


if __name__ == '__main__':
    input_filename, output_filename = sys.argv[1:3]
    convert_file(input_filename, output_filename)

