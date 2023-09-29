#!/usr/bin/env python3

import os
from aiohttp import web
from typing import List, Optional
from pydantic import BaseModel
import mimetypes
import hashlib
from pathlib import Path
import milli
from os import makedirs

import logging
logging.basicConfig(level=logging.DEBUG)

def traverse(basedir):
    basedir = Path(basedir)
    for entry in basedir.iterdir():
        if entry.is_symlink():
            entry = Path(os.readlink(entry)).resolve()  # Follow the symlink if entry is a symlink
            
        if entry.is_dir():
            yield from traverse(entry)  # Recursively traverse directories
        elif entry.is_file():
            yield entry  # Yield file paths

def build_index():
    # Index all *.vtt files in media folder
    path = "./milli_index"
    logging.info(f"Building index at {path}")
    makedirs(path, exist_ok=True)
    index = milli.Index(path, 1024*1024*1024) # 1GiB
    media_dir = Path('./media')
    # for file in media_dir.rglob('*.vtt'):
    docs = []
    for file in traverse(media_dir):
        if file.suffix == '.vtt':
            with open(file, 'r') as f:
                logging.info(f"Indexing {file}")
                # docs = []
                for line_index, line in enumerate(f.readlines()):
                    line = line.strip()
                    if line:  # Skip empty lines
                        # logging.info(f"Indexing {file} line {line_index}")
                        document_id = hashlib.sha256(f"{file}{line_index}{line}".encode()).hexdigest()
                        docs.append({
                            "id": document_id,
                            "title": str(file.relative_to(media_dir)),
                            "content": line
                        })
    index.add_documents(docs)
    logging.info(f"Index built at {path}")
    return index

index = build_index()


# Models
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


# Handler to fetch media
async def fetch_media(request):
    file_name = request.match_info.get('file_name', '')
    file_path = os.path.join('media', file_name)
    
    logging.info(f"Fetching {file_path}")
    if not os.path.exists(file_path):
        return web.HTTPNotFound(text="File not found")
    
    content_type, _ = mimetypes.guess_type(file_name)
    if content_type is None:
        content_type = 'application/octet-stream'
        
    return web.FileResponse(path=file_path, headers={'Content-Type': content_type})



# Handler to list media
async def list_media(request):
    media_dir = Path('./media')
    media_files = []

    #for file in media_dir.rglob('*'):  # Recursively search for all files
    for file in traverse(media_dir):
        if file.is_file() and file.suffix in ['.mp3', '.mp4', '.mkv', '.avi', '.webm']:
            relative_path = file.relative_to(media_dir)  # Get the relative path to the media directory
            media_files.append(str(relative_path))  # Convert the Path object to a string
    
    # Sort media files by modification time, most recent first
    media_files.sort(key=lambda f: (media_dir / f).stat().st_mtime, reverse=True)
    
    return web.json_response({'media_files': media_files})



# Handler to serve the UI
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


# aiohttp App
app = web.Application()
app.router.add_get('/', serve_index)
app.router.add_get('/search_content', search_content)
app.router.add_get('/media/{file_name:.*}', fetch_media)
app.router.add_get('/media', list_media)
app.router.add_static('/assets/', 'assets')


# Run aiohttp from Python Code
if __name__ == "__main__":
    web.run_app(app, host="127.0.0.1", port=8000)
