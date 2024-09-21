from os.path import join, relpath, exists, splitext
from fastapi import FastAPI, HTTPException, Response, BackgroundTasks
from typing import List, Dict
import argparse, subprocess, webvtt, uvicorn, duckdb
from tqdm import tqdm
import polars as pl
import tempfile
import multiprocessing as mp

app = FastAPI()
db = None

def parse_time(t):
    h, m, s = t.split(':')
    s, ms = s.split('.')
    return int(h)*3600 + int(m)*60 + float(s) + int(ms)/1000

def process_vtt(vtt, root):
    abs_vtt = join(root, vtt)
    rel_vtt = relpath(abs_vtt, root)
    if not exists(abs_vtt):
        print(f"File does not exist: {abs_vtt}")
        return []
    try:
        captions = []
        for c in webvtt.read(abs_vtt):
            captions.append((rel_vtt, c.start, c.end, c.text))
        return captions
    except Exception as e:
        print(f"Error reading {abs_vtt}: {e}")
        return []

def reindex_worker(vtt_files, root, return_dict, idx):
    rows = []
    for vtt in vtt_files:
        captions = process_vtt(vtt, root)
        rows.extend(captions)
    return_dict[idx] = rows

def reindex():
    global db
    db.execute("DROP TABLE IF EXISTS lines")
    db.execute("CREATE TABLE lines (filename VARCHAR, start VARCHAR, end_time VARCHAR, text VARCHAR)")
    fd = subprocess.run(['fd', '--type', 'f', '--extension', 'vtt', '--base-directory', args.root], capture_output=True, text=True)
    vtt_files = fd.stdout.splitlines()
    print(f"Found {len(vtt_files)} VTT files.")
    
    if not vtt_files:
        print("No VTT files found. Reindexing skipped.")
        return
    
    # Determine number of processes
    num_processes = min(mp.cpu_count(), 8)  # Limit to 8 to prevent excessive usage
    chunk_size = (len(vtt_files) + num_processes - 1) // num_processes
    chunks = [vtt_files[i:i + chunk_size] for i in range(0, len(vtt_files), chunk_size)]
    
    manager = mp.Manager()
    return_dict = manager.dict()
    jobs = []
    
    for idx, chunk in enumerate(chunks):
        p = mp.Process(target=reindex_worker, args=(chunk, args.root, return_dict, idx))
        jobs.append(p)
        p.start()
    
    for p in jobs:
        p.join()
    
    # Collect all rows
    all_rows = []
    for idx in range(len(chunks)):
        all_rows.extend(return_dict[idx])
    
    print(f"Total captions collected: {len(all_rows)}")
    
    if all_rows:
        # Convert to Polars DataFrame
        df = pl.DataFrame(all_rows, schema=["filename", "start", "end_time", "text"])
        # Insert into DuckDB using DuckDB's Polars integration
        db.register("df", df)
        db.execute("INSERT INTO lines SELECT filename, start, end_time, text FROM df")
        db.unregister("df")
    
    db.commit()
    print("Reindexing completed.")

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
    cursor = db.execute("SELECT filename, start, end_time, text FROM lines WHERE text LIKE ?", (f"%{q}%",)).fetchall()
    return [{"filename": row[0], "text": row[3], "start": row[1], "end": row[2]} for row in cursor]

def get_audio_segment(filename, start, end):
    o = splitext(join(args.root, filename))[0] + '.ogg'
    if not exists(o):
        raise HTTPException(status_code=404, detail="File not found")
    start_sec = parse_time(start)
    end_sec = parse_time(end)
    duration = end_sec - start_sec
    proc = subprocess.run(['ffmpeg', '-ss', str(start_sec), '-t', str(duration), '-i', o, '-f', 'ogg', 'pipe:1'], capture_output=True)
    if proc.returncode != 0:
        raise HTTPException(status_code=500, detail="Audio processing failed")
    return proc.stdout

@app.get("/uttale/Play")
def play(filename: str, start: str, end: str, background_tasks: BackgroundTasks):
    try:
        audio_data = get_audio_segment(filename, start, end)
    except HTTPException as e:
        raise e
    with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as tmp:
        tmp.write(audio_data)
        tmp_path = tmp.name
    subprocess.Popen(['play', tmp_path])
    # Schedule deletion of the temporary file
    background_tasks.add_task(tempfile.os.remove, tmp_path)
    return {"status": "playing"}

@app.get("/uttale/Audio")
def audio(filename: str, start: str, end: str):
    audio_data = get_audio_segment(filename, start, end)
    headers = {"Cache-Control": "max-age=86400"}
    return Response(content=audio_data, media_type="application/octet-stream", headers=headers)

@app.post("/uttale/Reindex")
def trigger_reindex(background_tasks: BackgroundTasks):
    background_tasks.add_task(reindex)
    return {"status": "Reindexing started in background"}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', default='.')
    parser.add_argument('--iface', default='0.0.0.0:7010')
    args = parser.parse_args()
    print(f"Arguments: root={args.root}, iface={args.iface}")
    db = duckdb.connect('lines.duckdb')
    reindex()
    iface, port = args.iface.split(':')
    uvicorn.run(app, host=iface, port=int(port))
