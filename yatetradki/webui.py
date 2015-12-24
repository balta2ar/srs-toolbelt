from os import remove
from os.path import exists
from os.path import basename
from os.path import dirname
from bottle import route
from bottle import run
from bottle import request
from bottle import static_file

from yatetradki.arguments import parse_args
from yatetradki.command import fetch
from yatetradki.command import export


INDEX_HTML = """
<html>
<body>
<form action="/upload" method="post" enctype="multipart/form-data">
  <input type="file" name="upload" />
  <input type="submit" value="Convert to anki" />
</form>
</body>
</html>
"""

FILENAME_WORDS = '/tmp/words.txt'
FILENAME_CACHE = '/tmp/cache.dat'
FILENAME_ANKI = '/tmp/anki.txt'
NUM_WORDS ='9999'


@route('/')
def index():
    return INDEX_HTML


def test():
    args = ['fetch',
            '--cache', FILENAME_CACHE,
            '--fetcher', 'Priberam',
            '--words-filename', FILENAME_WORDS,
            '--num-words', NUM_WORDS,
            '--jobs', '1']

    fetch(parse_args(args))

    args = ['export',
            '--cache', FILENAME_CACHE,
            '--num-words', NUM_WORDS,
            '--formatter', 'AnkiPriberam',
            '--output', FILENAME_ANKI]

    export(parse_args(args))


@route('/upload', method='POST')
def upload():
    upload = request.files.get('upload')

    if exists(FILENAME_WORDS):
        remove(FILENAME_WORDS)
    upload.save(FILENAME_WORDS)

    # Fetch
    args = ['fetch',
            '--cache', FILENAME_CACHE,
            '--fetcher', 'Priberam',
            '--words-filename', FILENAME_WORDS,
            '--num-words', '9999',
            '--jobs', '1']
    fetch(parse_args(args))

    # Export
    args = ['export',
            '--cache', FILENAME_CACHE,
            '--num-words', NUM_WORDS,
            '--formatter', 'AnkiPriberam',
            '--output', FILENAME_ANKI]
    export(parse_args(args))

    base, dir = basename(FILENAME_ANKI), dirname(FILENAME_ANKI)
    return static_file(base, root=dir, download=base)


run(host='0.0.0.0', port=8020, debug=True)
