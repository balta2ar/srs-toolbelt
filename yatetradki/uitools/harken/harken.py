#!/usr/bin/env python3

import hashlib
import logging
import mimetypes
import re
import os
import time
from os import makedirs
from os.path import abspath, basename, dirname, exists, join, splitext
from pathlib import Path
from pprint import pprint
from typing import Iterable, List, Optional
from collections import defaultdict, Counter

from aiohttp import web
from pydantic import BaseModel

logging.basicConfig(level=logging.DEBUG)

MEDIA = ['.mp3', '.mp4', '.mkv', '.avi', '.webm', '.opus', '.ogg']
SUBS = ['.vtt', '.srt']
MEDIA_DIR = './media'

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

def build_index():
    docs = []
    for file in find(MEDIA_DIR, SUBS):
        logging.info(f"Indexing {file}")
        for i, line in enumerate(slurp_lines(join(MEDIA_DIR, file))):
            line = line.strip()
            if line:
                document_id = hashlib.sha256(f"{file}{i}{line}".encode()).hexdigest()
                docs.append({
                    "id": document_id,
                    "title": f'{file}',
                    "content": line
                })
    return Search().index(docs)

def with_extension(path: str, ext: str) -> str:
    return splitext(path)[0] + ext

def search_index(index, q):
    results = index.search(q)
    out = []
    for doc in [index.get_document(result) for result in results]:
        sub = join(MEDIA_DIR, doc['title'])
        for ext in MEDIA:
            path = with_extension(sub, ext)
            if exists(sub) and exists(path):
                out.append(SearchResult(
                    content=doc['content'],
                    id=doc['id'],
                    title=with_extension(doc['title'], ext)
                ).dict())
    return out

index = None

class Subtitle(BaseModel):
    start_time: str
    end_time: str
    text: str

class MediaDetail(BaseModel):
    file_name: str
    file_path: str
    subtitles: List[Subtitle]

class MediaList(BaseModel):
    media_files: List[str]

class SearchResult(BaseModel):
    content: str
    id: str
    title: str

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
    path = join(MEDIA_DIR, name)

    logging.info(f"Fetching {path}")
    if not exists(path):
        return web.HTTPNotFound(text="Requested file not found")

    content_type, _ = mimetypes.guess_type(path)
    if content_type is None:
        content_type = 'application/octet-stream'

    return web.FileResponse(path=path, headers={'Content-Type': content_type})

async def list_media(request):
    return web.json_response({'media_files': find(MEDIA_DIR, MEDIA)})

async def serve_index(request):
    content = open('assets/index.html', 'r').read()
    return web.Response(text=content, content_type='text/html')

async def search_content(request):
    q = request.query.get('q', '')
    if not q: return web.json_response({'error': 'q parameter is required'}, status=400)

    results = index.search(q)
    documents = [index.get_document(result) for result in results]

    return web.json_response({'results': documents})


def find(where: str, types: Iterable[str]) -> List[str]:
    file_list = []
    for root, dirs, files in os.walk(where, followlinks=True):
        for filename in files:
            if Path(filename).suffix in types:
                relative_path = os.path.relpath(os.path.join(root, filename), where)
                file_list.append(relative_path)
    return file_list

def test_repo2():
    pprint(find(MEDIA_DIR, MEDIA))

def test_index():
    # index = build_index()
    # results = index.search('bulke')
    # documents = [index.get_document(result) for result in results]
    documents = search_index(build_index(), 'direkte')
    pprint(documents)

def equals(a, b):
    assert a == b, f"{a} != {b}"

class Search:
    def trigrams(word): return [word[i:i+3] for i in range(len(word)-2)] or [word]
    def __init__(self):
        self.docs = {} # doc_id to doc mapping
        self.plist = defaultdict(set) # term to doc_id mapping
        self.trigram_index = defaultdict(set) # trigram to terms mapping
    def index(self, documents):
        t0 = time.time()
        self.docs = {doc['id']: doc for doc in documents}
        def tokenize(text): return re.findall(r'\b[a-zA-Z0-9åøæÅØÆ]+\b', text.lower())
        for document in documents:
            doc_id = document['id']
            title = document['title']
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
        sets_of_words = [list(self._trigram_words(w)) for w in query_words]
        if not sets_of_words: return []

        # trigrams(word) map to many terms, so it's union between trigrams mapped to terms
        # but since the query itself assumes AND, we intersect between sets of terms
        result = self._search(sets_of_words[0], set.union)
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

def read_corpus(filenames):
    docs = []
    doc_id = 0
    for file in filenames:
        for i, line in enumerate(slurp_lines(join(MEDIA_DIR, file))):
            line = line.strip()
            if line:
                # document_id = hashlib.sha256(f"{file}{i}{line}".encode()).hexdigest()
                docs.append({
                    "id": doc_id,
                    "title": f'{file}',
                    "content": line
                })
                doc_id += 1
    return docs

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

    corpus = read_corpus(find(MEDIA_DIR, SUBS))
    search.index(corpus)
    # pprint(search.show(search.transform("smukke")))
    pprint(search.get_documents(search.search("porten")))
    # equals([1], search.transform("smukke"))


def main():
    app = web.Application()
    app.router.add_get('/', serve_index)
    app.router.add_get('/search_content', search_content)
    app.router.add_get('/media/{file_name:.*}', fetch_media)
    app.router.add_get('/media', list_media)
    app.router.add_static('/assets/', 'assets')

    web.run_app(app, host="127.0.0.1", port=4000)

if __name__ == "__main__":
    index = build_index()
    main()
