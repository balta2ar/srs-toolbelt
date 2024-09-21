from os.path import join, relpath, exists, splitext
from fastapi import FastAPI, HTTPException, Response
from typing import List, Dict
import argparse, subprocess, webvtt, uvicorn
from io import BytesIO
import tempfile

app = FastAPI()

def parse_time(t):
    h, m, s = t.split(':')
    s, ms = s.split('.')
    return f"{h}:{m}:{s}.{ms}"

def get_audio_segment(filename, start, end):
    o = splitext(join(args.root, filename))[0] + '.ogg'
    if not exists(o):
        raise HTTPException(status_code=404, detail="File not found")
    start_ff, end_ff = parse_time(start), parse_time(end)
    proc = subprocess.run(['ffmpeg', '-ss', start_ff, '-to', end_ff, '-i', o, '-f', 'ogg', 'pipe:1'], capture_output=True)
    if proc.returncode != 0:
        raise HTTPException(status_code=500, detail="Audio processing failed")
    return proc.stdout

@app.get("/uttale/Scopes")
def scopes(q: str = "") -> List[str]:
    r = subprocess.run(['fd', '--type', 'd', '--max-depth', '2', '--base-directory', args.root], capture_output=True, text=True).stdout.splitlines()
    dirs = sorted([relpath(d, args.root) for d in r])
    return [d for d in dirs if q in d]

@app.get("/uttale/Search")
def search(scope: str, q: str) -> List[Dict]:
    s = join(args.root, scope)
    if not exists(s):
        raise HTTPException(status_code=404, detail="Scope not found")
    rg = subprocess.run(['rg', q, '-g', '*.txt', s], capture_output=True, text=True).stdout.splitlines()
    m = []
    for line in rg:
        f, _, _ = line.partition(':')
        v = splitext(f)[0] + '.vtt'
        if exists(v):
            for c in webvtt.read(v):
                if q.lower() in c.text.lower():
                    m.append({"filename": relpath(v, args.root), "text": c.text, "start": c.start, "end": c.end})
    return m

@app.get("/uttale/Play")
def play(filename: str, start: str, end: str):
    try:
        audio_data = get_audio_segment(filename, start, end)
    except HTTPException as e:
        raise e
    with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as tmp:
        tmp.write(audio_data)
        tmp_path = tmp.name
    subprocess.Popen(['play', tmp_path])
    return {"status": "playing"}

@app.get("/uttale/Audio")
def audio(filename: str, start: str, end: str):
    audio_data = get_audio_segment(filename, start, end)
    headers = {"Cache-Control": "max-age=86400"}
    return Response(content=audio_data, media_type="application/octet-stream", headers=headers)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', default='.')
    parser.add_argument('--iface', default='0.0.0.0:7010')
    args = parser.parse_args()
    print(f"Arguments: root={args.root}, iface={args.iface}")
    iface, port = args.iface.split(':')
    uvicorn.run(app, host=iface, port=int(port))
