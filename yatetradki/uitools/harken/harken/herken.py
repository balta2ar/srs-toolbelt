#!/usr/bin/env python3

import argparse
from ast import Sub
import logging
import mimetypes
import os
import re
import time
from collections import Counter, defaultdict
from os import makedirs
from os.path import abspath, basename, dirname, exists, join, splitext
from pathlib import Path
from pprint import pprint
from typing import Iterable, List, Optional
from inspect import isgenerator
from collections import namedtuple

from aiohttp import web
# from py import log
from pydantic import BaseModel

from nicegui import ui, app
# from sympy import N


ASSETS = './assets'
logging.basicConfig(level=logging.DEBUG)
logging.info(f"Starting harken. ASSETS={ASSETS}")

MEDIA = set(['.mp3', '.mp4', '.mkv', '.avi', '.webm', '.opus', '.ogg'])
SUBS = set(['.vtt'])
# SUBS = ['.vtt', '.srt']
# MEDIA_DIR = './media'

NamedPair = namedtuple('NamedPair', ['sub', 'media'])

def slurp(path):
    logging.info(f"Slurping {path}")
    with open(path, 'rb') as f:
        return f.read()

def slurp_lines(path):
    with open(path, 'r') as f:
        return f.readlines()

def traverse(basedir):
    basedir = Path(basedir)
    for entry in basedir.iterdir():
        if entry.is_symlink():
            yield entry
        elif entry.is_dir():
            yield from traverse(entry)  # Recursively traverse directories
        elif entry.is_file():
            yield entry

# def build_index():
#     docs = read_corpus(find(MEDIA_DIR, SUBS))
#     return Search().index(docs)

def with_extension(path: str, ext: str) -> str:
    return splitext(path)[0] + ext

def search_index(index, q):
    results = index.search(q)
    out = []
    for doc in [index.get_document(result) for result in results]:
        sub = doc['filename']
        for ext in MEDIA:
            path = with_extension(sub, ext)
            if exists(sub) and exists(path):
                out.append(SearchResult(
                    content=doc['content'],
                    id=doc['id'],
                    title=with_extension(doc['filename'], ext),
                    offset=doc['offset'],
                    subtitle=doc['filename'],
                    media=with_extension(doc['filename'], ext)
                ).dict())
    return out

index = None

def parse_timestamp(s):
    """
    00:00:26,240
    00:00:09.320
    """
    h, m, s_ms = s.split(':')
    s, ms = s_ms.replace('.', ',').split(',')
    return int(h) * 3600000 + int(m) * 60000 + int(s) * 1000 + int(ms)

def parse_timestamp_seconds(s):
    return parse_timestamp(s) / 1000.0

class Subtitle(BaseModel):
    start_time: str
    start: float
    end_time: str
    end: float
    text: str
    offset: int
    @property
    def start(self) -> float: return parse_timestamp_seconds(self.start_time)
    @property
    def end(self) -> float: return parse_timestamp_seconds(self.end_time)

class MediaDetail(BaseModel):
    file_name: str
    file_path: str
    subtitles: List[Subtitle]

class MediaList(BaseModel):
    media_files: List[str]

class SearchResult(BaseModel):
    content: str
    id: int
    title: str
    offset: int
    subtitle: str
    media: str

def parse_vtt(file_path: str) -> List[Subtitle]:
    subtitles = []
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read().splitlines()
        idx = 1
        while idx < len(content) and content[idx].strip() == "":
            idx += 1

        while idx < len(content):
            if content[idx].strip() == "":
                idx += 1
                continue

            start, end = content[idx].strip().split(' --> ')
            idx += 1

            text_lines = []
            while idx < len(content) and content[idx].strip() != "":
                text_lines.append(content[idx].strip())
                idx += 1
            text = ' '.join(text_lines)

            subtitles.append(Subtitle(start_time=start, end_time=end, text=text))
    return subtitles


async def fetch_media(request):
    name = request.match_info.get('file_name', '')
    # path = join(MEDIA_DIR, name)
    path = name

    logging.info(f"Fetching {path}")
    if not exists(path):
        return web.HTTPNotFound(text="Requested file not found")

    content_type, _ = mimetypes.guess_type(path)
    if content_type is None:
        content_type = 'application/octet-stream'

    return web.FileResponse(path=path, headers={'Content-Type': content_type})

async def list_media(request):
    out = []
    for media_filename in find(MEDIA_DIR, MEDIA):
        media = join(MEDIA_DIR, media_filename)
        for ext in SUBS:
            path = with_extension(media, ext)
            if exists(media) and exists(path):
                out.append({
                    'media': media_filename,
                    'subtitle': with_extension(media_filename, ext),
                })
    key = lambda x: (splitext(x['media'])[1], x['media'])
    out = sorted(out, key=key)
    return web.json_response({'media_files': out})

async def serve_index(request):
    content = open(join(ASSETS, 'index.html'), 'r').read()
    return web.Response(text=content, content_type='text/html')

async def search_content(request):
    q = request.query.get('q', '')
    if not q: return web.json_response({'error': 'q parameter is required'}, status=400)

    documents = search_index(index, q)
    return web.json_response({'results': documents})


# def test_repo2():
    # pprint(find(MEDIA_DIR, MEDIA))

def test_index():
    # index = build_index()
    # results = index.search('bulke')
    # documents = [index.get_document(result) for result in results]
    # documents = search_index(build_index(), 'direkte')
    # documents = search_index(build_index(), 'peive')
    # pprint(documents)
    print(1)

def equals(a, b):
    assert a == b, f"{a} != {b}"

class Search:
    def trigrams(word): return [word[i:i+3] for i in range(len(word)-2)] or [word]
    def __init__(self):
        self.docs = {} # doc_id to doc mapping
        self.plist = defaultdict(set) # term to doc_id mapping
        self.trigram_index = defaultdict(set) # trigram to terms mapping
    # def media(self, needle) -> [str]:
        # return [doc['media'] for doc in self.docs.values() if needle in doc['media']]
    def content(self, documents):
        t0 = time.time()
        self.docs.update({doc['id']: doc for doc in documents})
        def tokenize(text): return re.findall(r'\b[a-zA-Z0-9åøæÅØÆ]+\b', text.lower())
        for document in documents:
            doc_id = document['id']
            # title = document['title']
            content = document['content']
            for term in tokenize(content):
                self.plist[term].add(doc_id)
        for term in self.plist:
            for trigram in Search.trigrams(term):
                self.trigram_index[trigram].add(term)
        logging.info(f"Index built in {time.time() - t0:.2f}s, {len(self.docs)} documents, {len(self.plist)} terms, {len(self.trigram_index)} trigrams")
        return self
    def search(self, query):
        t0 = time.time()
        query_words = query.lower().split()
        if not query_words: return []
        logging.info(f"Searching for '{query_words}'")
        sets_of_words = [list(self._trigram_words(w)) for w in query_words]
        if not sets_of_words: return []
        logging.info(f'Words mapped to trigrams: {sets_of_words}')

        # trigrams(word) map to many terms, so it's union between trigrams mapped to terms
        # but since the query itself assumes AND, we intersect between sets of terms
        result = self._search(sets_of_words[0], set.union)
        logging.info(f'Result after first word: {result}')
        for words in sets_of_words[1:]:
            result = result.intersection(self._search(words, set.union))

        logging.info(f"Search for '{query}' took {time.time() - t0:.2f}s, {len(result)} results")
        return sorted(list(result))
    def _trigram_words(self, query_word):
        result = set()
        for trigram in Search.trigrams(query_word):
            for word in self.trigram_index[trigram]:
                if query_word in word:
                    result.add(word)
        return result
    def _search(self, query_words, set_combine):
        if not query_words: return set()
        result = self.plist[query_words[0]]
        for word in query_words[1:]:
            if word in self.plist:
                result = set_combine(result, self.plist[word])
        return result
    def get_document(self, doc_id): return self.docs[doc_id]
    def get_documents(self, doc_ids): return [self.get_document(doc_id) for doc_id in doc_ids]

def consume(line, pattern, *parsers):
    matches = re.match(pattern, line)
    if not matches: raise ValueError(f"Pattern {pattern} did not match line {line}")
    return tuple(parser(group) for parser, group in zip(parsers, matches.groups()))

RX_TIMESTAMP = r'(\d{2}:\d{2}:\d{2}[,.]\d{3}) --> (\d{2}:\d{2}:\d{2}[,.]\d{3})'

def parse_subtitles(filename) -> Iterable[Subtitle]:
    suffix = splitext(filename)[1]
    match suffix:
        case '.srt': return parse_srt(open(filename))
        case '.vtt': return parse_vtt(open(filename))
        case _: raise ValueError(f"Unknown subtitle format {suffix}")

def parse_srt(lines) -> Iterable[Subtitle]:
    if not isgenerator(lines): lines = iter(lines)
    for line in lines:
        i = consume(line, r'(\d+)', int)
        start_str, end_str = consume(next(lines), RX_TIMESTAMP, str, str)
        text = consume(next(lines), r'(.*)', str)[0]
        _ = consume(next(lines), r'^$')
        yield Subtitle(start_time=start_str, end_time=end_str, text=text, offset=i[0])

def parse_vtt(lines) -> Iterable[Subtitle]:
    if not isgenerator(lines): lines = iter(lines)
    _ = consume(next(lines), r'^WEBVTT$')
    _ = consume(next(lines), r'^$')
    for i, line in enumerate(lines):
        start_str, end_str = consume(line, RX_TIMESTAMP, str, str)
        text = consume(next(lines), r'(.*)', str)[0]
        _ = consume(next(lines), r'^$')
        yield Subtitle(start_time=start_str, end_time=end_str, text=text, offset=i)

def find(where: str, subs: Iterable[str], medias: Iterable[str]) -> List[NamedPair]:
    result = []
    for root, dirs, files in os.walk(where, followlinks=True):
        for filename in files:
            media = join(root, filename)
            media_ext = Path(filename).suffix
            for sub_ext in subs:
                sub = with_extension(media, sub_ext)
                if media_ext in medias and exists(media) and exists(sub):
                    # relative_path = os.path.relpath(os.path.join(root, filename), where)
                    result.append(NamedPair(sub=sub, media=media))
    logging.info(f"Found {len(result)} pairs at {where}")
    return result

class Corpus:
    def __init__(self):
        self.doc_id = 0
    def read(self, filenames: List[NamedPair]):
        docs = []
        for file in filenames:
            start_doc_id = self.doc_id
            for line in parse_subtitles(file.sub):
                docs.append({
                    "id": self.doc_id,
                    "sub": f'{file.sub}',
                    "media": f'{file.media}',
                    "content": line.text,
                    "offset": self.doc_id - start_doc_id,
                })
                self.doc_id += 1
        logging.info(f"Read {len(docs)} documents from {len(filenames)} files")
        return docs

def test_parse():
    srt = 'w/byday/20230904/by10m/by10m_03.srt'
    lines = list(parse_subtitles(join(MEDIA_DIR, srt)))
    pprint(lines)
    vtt = 'w/byday/20230904/by10m/by10m_03.vtt'
    lines = list(parse_subtitles(join(MEDIA_DIR, vtt)))
    pprint(lines)

def test_vtt():
    vtt = 'h/ukesnytt/20240331/by10m/by10m_01.vtt'
    lines = list(parse_subtitles(vtt))
    pprint(lines)


def test_search():
    search = Search()

    # corpus = [
    #     {"id": 0, "title": "apple", "content": "Apples are normally found in the fruit section"},
    #     {"id": 1, "title": "banana", "content": "hånd bananas are Yellow"},
    #     {"id": 2, "title": "orange", "content": "oranges are not found From another planet"},
    #     {"id": 3, "title": "fourth", "content": "retired soldier returns"},
    # ]
    # search.fit(corpus)
    # equals([1], search.transform("hånd"))
    # equals([0], search.transform("apples"))
    # equals([0, 1, 2], search.transform("are"))
    # equals([2], search.transform("from"))
    # equals([0, 2], search.transform("are found"))
    # equals([3], search.transform("red"))
    # equals([3], search.transform("red ns"))

    corp = Corpus()
    corpus = corp.read(find(MEDIA_DIR, SUBS))
    search.content(corpus)
    # pprint(search.show(search.transform("smukke")))
    pprint(search.get_documents(search.search("porten")))
    # equals([1], search.transform("smukke"))


# def main():
#     global index
#     global MEDIA_DIR
#     parser = argparse.ArgumentParser()
#     parser.add_argument('media', nargs='+', help='Media directories', default=[MEDIA_DIR])
#     args = parser.parse_args()
#     logging.info(f"Args: {args}")

#     MEDIA_DIR = args.media
#     index = build_index()

#     app = web.Application()
#     app.router.add_get('/', serve_index)
#     app.router.add_get('/search_content', search_content)
#     app.router.add_get('/media/{file_name:.*}', fetch_media)
#     app.router.add_get('/media', list_media)
#     app.router.add_static('/assets/', path=ASSETS, name='assets')

#     web.run_app(app, host="127.0.0.1", port=4000)

ui.add_css('''
:root {
    --nicegui-default-padding: 1.0rem;
    --nicegui-default-gap: 0.1rem;
}
.active {
    font-weight: bold;
}
''')

def on_click():
    ui.notify('Button clicked!')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('dirs', nargs='+', help='Media directories, can be several')
    args = parser.parse_args()
    logging.info(f"Args: {args}")

    search = Search()
    corp = Corpus()
    files: List[NamedPair] = []
    for media_dir in args.dirs:
        logging.info(f"Indexing {media_dir}")
        batch = find(media_dir, SUBS, MEDIA)
        files.extend(batch)
        corpus = corp.read(batch)
        search.content(corpus)
        app.add_media_files(media_dir, Path(media_dir))

    files = sorted(list(set(files)), key=lambda x: x.media)
    media2sub = {m.media: m for m in files}
    current_file = files[0]
    subtitles: [Subtitle] = list(parse_subtitles(current_file.sub))
    player = None
    logging.info(f"Media files: {len(files)}")

    def load_media(file: str):
        subtitles.clear()
        subtitles.extend(list(parse_subtitles(media2sub[file.media].sub)))
        nonlocal current_file
        current_file = file
        draw.refresh()
        # player.play

    def play_line(sub: Subtitle):
        player.seek(sub.start)
        player.play()
        # player.currentTime = parse_timestamp(sub.start_time

    @ui.refreshable
    def draw():
        nonlocal player
        with ui.row().classes('w-full'):
            ui.input(label='Search by word', placeholder='Type something to search').classes('w-2/12')
            player = ui.audio(current_file.media).classes('w-9/12')
        with ui.row().classes('w-full'):
            with ui.column().classes('border w-5/12'):
                for f in files:
                    on_click = lambda f=f: load_media(f)
                    classes = 'pl-4 hover:underline cursor-pointer'
                    if f == current_file: ui.label(f.media).on('click', on_click).classes(classes + ' active')
                    else: ui.label(f.media).on('click', on_click).classes(classes)
            with ui.column().classes('border w-5/12'):
                for s in subtitles:
                    on_click = lambda s=s: play_line(s)
                    with ui.row().classes('pl-4 hover:ring-1'):
                        ui.label('>').on('click', on_click).classes('cursor-pointer')
                        ui.label(f'{s.text}')
    # ui.button('Click me', on_click=on_click)
    # draw(current_file.media, subtitles)
    draw()
    ui.run(title='herken', show=False)
    

if __name__ in {'__main__', '__mp_main__'}:
    main()