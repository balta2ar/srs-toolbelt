#!/usr/bin/env python3

import hashlib
import logging
import mimetypes
import os
from os import makedirs
from os.path import abspath, basename, dirname, join
from pathlib import Path
from pprint import pprint
from typing import Iterable, List, Optional

import milli
from aiohttp import web
from pydantic import BaseModel

logging.basicConfig(level=logging.DEBUG)

MEDIA = ['.mp3', '.mp4', '.mkv', '.avi', '.webm']
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
    path = "./milli_index"
    logging.info(f"Building index at {path}")
    makedirs(path, exist_ok=True)
    index = milli.Index(path, 1024*1024*1024) # 1GiB
    docs = []
    for entry in Repo(MEDIA_DIR).find(SUBS):
        file = entry.path()
        logging.info(f"Indexing {file}")
        for i, line in enumerate(slurp_lines(file)):
            line = line.strip()
            if line:
                document_id = hashlib.sha256(f"{file}{i}{line}".encode()).hexdigest()
                docs.append({
                    "id": document_id,
                    "title": f'{entry.pid}/{entry.rel}',
                    "content": line
                })
    index.add_documents(docs)
    logging.info(f"Index built at {path}")
    return index

index = None
repo = None

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

class Entry(BaseModel):
    rel: str
    parent: str
    base: str
    pid: str
    def path(self) -> Path: return Path(os.path.join(self.base, self.rel))

class EntryList(BaseModel):
    entries: List[Entry]

class SearchResult(BaseModel):
    sid: str
    pid: str
    title: str
    content: str

# Helper Function to Parse VTT
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
    id = request.match_info.get('id', '')
    file_name = request.match_info.get('file_name', '')
    file_path = file_name #os.path.join('media', file_name)

    logging.info(f"Fetching {id}/{file_path}")
    path = repo.serve(id, file_path)
    if not path:
        return web.HTTPNotFound(text="Requested file not found")

    content_type, _ = mimetypes.guess_type(file_name)
    if content_type is None:
        content_type = 'application/octet-stream'
        
    return web.FileResponse(path=path, headers={'Content-Type': content_type})

async def list_media(request):    
    entries = Repo(MEDIA_DIR).find(MEDIA)
    return web.json_response({'media_files': EntryList(entries=entries).dict()['entries']})

async def serve_index(request):
    content = open('assets/index.html', 'r').read()
    return web.Response(text=content, content_type='text/html')

async def search_content(request):
    q = request.query.get('q', '')
    if not q:
        return web.json_response({'error': 'q parameter is required'}, status=400)
    
    results = index.search(q)
    documents = [index.get_document(result) for result in results]
    
    return web.json_response({'results': documents})


class ManyRepo:
    def __init__(self, children: List['Repo']):
        self.children = children
    def find(self, types: Iterable[str]) -> [Entry]:
        out = []
        for child in self.children: out.extend(child.find(types))
        return out
    def serve(self, id: str, rel: str) -> Optional[str]:
        logging.info(f"Searching {id} in {self.children}")
        for child in self.children:
            out = child.serve(id, rel)
            if out: return out

class Repo:
    def __init__(self, base: str):
        self.base = abspath(base)
        self.last_parent = dirname(base)
        self.children = self.scan(base)
        self.id = hashlib.md5(self.base.encode()).hexdigest()[:8]
    def __repr__(self):
        return f"Repo({self.id}:{self.base})"
    def scan(self, base) -> ManyRepo:
        out = []
        for entry in traverse(base):
            if entry.is_symlink():
                entry = Path(os.readlink(entry)).resolve()
                if entry.is_dir():
                    out.append(Repo(entry))
        return ManyRepo(out)
    def find(self, types: Iterable[str]) -> [Entry]:
        media_dir = Path(self.base)
        out = []
        for entry in traverse(media_dir):
            if entry.is_symlink(): continue
            if entry.is_file() and entry.suffix in types:
                rel = str(entry.relative_to(media_dir))
                base = str(media_dir.absolute())
                parent = basename(base)
                out.append(Entry(rel=rel, parent=parent, base=base, pid=self.id))
        out.extend(self.children.find(types))
        out.sort(key=lambda f: f.path().stat().st_mtime, reverse=True)
        return out
    def serve(self, id: str, rel: str) -> Optional[str]:
        if id == self.id: return join(self.base, rel)
        return self.children.serve(id, rel)

def test_repo():
    repo = Repo(MEDIA_DIR)
    pprint(EntryList(entries=repo.find(MEDIA)).dict())
    # pprint(repo.find(SUBS))

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
    index = build_index()
    results = index.search('bulke')
    documents = [index.get_document(result) for result in results]
    pprint(documents)

def test_serve():
    repo = Repo(MEDIA_DIR)
    out = repo.serve('882400b9', 'by10m/by10m_04.vtt')
    print(out)

def main():
    app = web.Application()
    app.router.add_get('/', serve_index)
    app.router.add_get('/search_content', search_content)
    app.router.add_get('/media/{id}/{file_name:.*}', fetch_media)
    app.router.add_get('/media', list_media)
    app.router.add_static('/assets/', 'assets')

    web.run_app(app, host="127.0.0.1", port=8000)

if __name__ == "__main__":
    index = build_index()
    repo = Repo(MEDIA_DIR)
    main()
