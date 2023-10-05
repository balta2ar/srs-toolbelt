#!/usr/bin/env python3

import hashlib
import logging
import mimetypes
import os
from os import makedirs
from os.path import abspath, basename, dirname, exists, join
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
    index.add_documents(docs)
    logging.info(f"Index built at {path}")
    return index

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
    sid: str
    pid: str
    title: str
    content: str

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
    if not q:
        return web.json_response({'error': 'q parameter is required'}, status=400)
    
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
    index = build_index()
    results = index.search('bulke')
    documents = [index.get_document(result) for result in results]
    pprint(documents)

def main():
    app = web.Application()
    app.router.add_get('/', serve_index)
    app.router.add_get('/search_content', search_content)
    app.router.add_get('/media/{file_name:.*}', fetch_media)
    app.router.add_get('/media', list_media)
    app.router.add_static('/assets/', 'assets')

    web.run_app(app, host="127.0.0.1", port=8000)

if __name__ == "__main__":
    index = build_index()
    main()
