#!/usr/bin/env python3

import os
from aiohttp import web
from typing import List, Optional
from pydantic import BaseModel
import mimetypes


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
    
    if not os.path.exists(file_path):
        return web.HTTPNotFound(text="File not found")
    
    content_type, _ = mimetypes.guess_type(file_name)
    if content_type is None:
        content_type = 'application/octet-stream'
        
    return web.FileResponse(path=file_path, headers={'Content-Type': content_type})



# Handler to list media
async def list_media(request):
    media_folder = 'media'
    media_files = [f for f in os.listdir(media_folder) if os.path.isfile(os.path.join(media_folder, f))]
    return web.json_response(MediaList(media_files=media_files).dict())


# Handler to serve the UI
async def serve_index(request):
    content = open('assets/index.html', 'r').read()
    return web.Response(text=content, content_type='text/html')


# aiohttp App
app = web.Application()
app.router.add_get('/', serve_index)
app.router.add_get('/media/{file_name}', fetch_media)
app.router.add_get('/media', list_media)
app.router.add_static('/assets/', 'assets')


# Run aiohttp from Python Code
if __name__ == "__main__":
    web.run_app(app, host="127.0.0.1", port=8000)
