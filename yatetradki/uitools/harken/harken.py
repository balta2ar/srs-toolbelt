#!/usr/bin/env python3

import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
import uvicorn
from pydantic import BaseModel
import subprocess


# Models
class Subtitle(BaseModel):
    start_time: float
    end_time: float
    text: str


class MediaDetail(BaseModel):
    file_name: str
    file_path: str
    subtitles: List[Subtitle]


# FastAPI App
app = FastAPI()


# Helper Function to Parse SRT
def parse_srt(file_path: str) -> List[Subtitle]:
    subtitles = []
    with open(file_path, 'r', encoding='utf-8') as f:
        blocks = f.read().split('\n\n')
        for block in blocks:
            if block.strip() == '':
                continue
            lines = block.split('\n')
            if len(lines) < 3:
                continue  # Invalid block
            start_end, *text_lines = lines
            start, end = start_end.split(' --> ')
            subtitles.append(Subtitle(start_time=start, end_time=end, text=' '.join(text_lines)))
    return subtitles


# API Route to fetch media
@app.get("/media/{file_name}", response_model=MediaDetail)
def fetch_media(file_name: str) -> Optional[MediaDetail]:
    media_path = os.path.join('media', file_name)
    subtitle_path = os.path.join('subtitles', f"{os.path.splitext(file_name)[0]}.srt")
    
    if not os.path.exists(media_path) or not os.path.exists(subtitle_path):
        raise HTTPException(status_code=404, detail="Media or Subtitle not found")
    
    subtitles = parse_srt(subtitle_path)
    return MediaDetail(file_name=file_name, file_path=media_path, subtitles=subtitles)


# Run Uvicorn from Python Code
if __name__ == "__main__":
    # uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
    subprocess.run(["uvicorn", __file__.replace(".py", ":app"), "--reload", "--host", "127.0.0.1", "--port", "8000"])
