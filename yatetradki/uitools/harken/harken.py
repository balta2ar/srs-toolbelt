#!/usr/bin/env python3

import os
from aiohttp import web
from typing import List, Optional
from pydantic import BaseModel


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
        # Skip the "WEBVTT" line and any blank lines that follow it
        idx = 1
        while idx < len(content) and content[idx].strip() == "":
            idx += 1

        # Process the subtitle blocks
        while idx < len(content):
            # Skip blank lines between blocks
            if content[idx].strip() == "":
                idx += 1
                continue

            # Parse the timestamp line
            start, end = content[idx].strip().split(' --> ')
            idx += 1
            
            # Process the text lines
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
    media_path = os.path.join('media', file_name)
    subtitle_path = os.path.join('media', f"{os.path.splitext(file_name)[0]}.vtt")
    
    if not os.path.exists(media_path) or not os.path.exists(subtitle_path):
        return web.HTTPNotFound(text="Media or Subtitle not found")
    
    subtitles = parse_vtt(subtitle_path)
    media_detail = MediaDetail(file_name=file_name, file_path=media_path, subtitles=subtitles)
    return web.json_response(media_detail.dict())


# Handler to list media
async def list_media(request):
    media_folder = 'media'
    media_files = [f for f in os.listdir(media_folder) if os.path.isfile(os.path.join(media_folder, f))]
    return web.json_response(MediaList(media_files=media_files).dict())


# aiohttp App
app = web.Application()
app.router.add_get('/media/{file_name}', fetch_media)
app.router.add_get('/media', list_media)

# Run aiohttp from Python Code
if __name__ == "__main__":
    web.run_app(app, host="127.0.0.1", port=8000)
