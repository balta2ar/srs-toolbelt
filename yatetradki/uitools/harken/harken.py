#!/usr/bin/env python3

import os
from aiohttp import web
from typing import List, Optional
from pydantic import BaseModel


# Models
class Subtitle(BaseModel):
    start_time: float
    end_time: float
    text: str


class MediaDetail(BaseModel):
    file_name: str
    file_path: str
    subtitles: List[Subtitle]


# Helper Function to Parse VTT
def parse_vtt(file_path: str) -> List[Subtitle]:
    subtitles = []
    with open(file_path, 'r', encoding='utf-8') as f:
        blocks = f.read().split('\n\n')
        for block in blocks:
            if block.strip() == '':
                continue
            lines = block.split('\n')
            if len(lines) < 2:
                continue  # Invalid block
            start_end, *text_lines = lines[1:]
            start, end = start_end.split(' --> ')
            subtitles.append(Subtitle(start_time=start, end_time=end, text=' '.join(text_lines)))
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


# aiohttp App
app = web.Application()
app.router.add_get('/media/{file_name}', fetch_media)

# Run aiohttp from Python Code
if __name__ == "__main__":
    web.run_app(app, host="127.0.0.1", port=8000)
