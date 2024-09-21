from os.path import join, relpath, exists, splitext
from fastapi import FastAPI, HTTPException, Response, BackgroundTasks
from typing import List, Dict
import argparse, subprocess, webvtt, uvicorn, duckdb
from tqdm import tqdm
import polars as pl
import tempfile
import multiprocessing as mp
import threading
import time

app = FastAPI()
db = None

def parse_time(t):
    try:
        h, m, s = t.split(':')
        s, ms = s.split('.')
        return int(h)*3600 + int(m)*60 + float(s) + int(ms)/1000
    except Exception as e:
        raise ValueError(f"Invalid time format: {t}") from e

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

def reindex_worker(vtt_files, root, return_dict, idx, counter, lock):
    rows = []
    for vtt in vtt_files:
        captions = process_vtt(vtt, root)
        rows.extend(captions)
        with lock:
            counter.value += 1
    return_dict[idx] = rows

def update_progress(total, counter, lock, stop_event):
    with tqdm(total=total, desc="Reindexing VTT files") as pbar:
        while not stop_event.is_set():
            with lock:
                current = counter.value
            pbar.n = current
            pbar.refresh()
            if current >= total:
                break
            time.sleep(0.5)
        pbar.n = total
        pbar.refresh()

def reindex():
    global db
    db.execute("DROP TABLE IF EXISTS lines")
    db.execute("CREATE TABLE lines (filename VARCHAR, start VARCHAR, end_time VARCHAR, text VARCHAR)")
    
    # Find all .vtt files using fd
    try:
        fd = subprocess.run(
            ['fd', '--type', 'f', '--extension', 'vtt', '--base-directory', args.root],
            capture_output=True,
            text=True,
            check=True
        )
        vtt_files = fd.stdout.splitlines()
    except subprocess.CalledProcessError as e:
        print(f"Error running fd: {e}")
        vtt_files = []
    
    total_files = len(vtt_files)
    print(f"Found {total_files} VTT files.")
    
    if not vtt_files:
        print("No VTT files found. Reindexing skipped.")
        return
    
    manager = mp.Manager()
    return_dict = manager.dict()
    counter = manager.Value('i', 0)
    lock = manager.Lock()
    
    num_processes = min(mp.cpu_count(), 8)  # Limit to 8 processes to prevent overloading
    chunk_size = (total_files + num_processes - 1) // num_processes
    chunks = [vtt_files[i:i + chunk_size] for i in range(0, total_files, chunk_size)]
    
    jobs = []
    for idx, chunk in enumerate(chunks):
        p = mp.Process(target=reindex_worker, args=(chunk, args.root, return_dict, idx, counter, lock))
        jobs.append(p)
        p.start()
    
    # Start progress bar in a separate thread
    stop_event = threading.Event()
    progress_thread = threading.Thread(target=update_progress, args=(total_files, counter, lock, stop_event))
    progress_thread.start()
    
    for p in jobs:
        p.join()
    
    stop_event.set()
    progress_thread.join()
    
    # Collect all rows
    all_rows = []
    for idx in range(len(chunks)):
        all_rows.extend(return_dict.get(idx, []))
    
    print(f"Total captions collected: {len(all_rows)}")
    
    if all_rows:
        # Convert to Polars DataFrame for faster processing
        df = pl.DataFrame(all_rows, schema=["filename", "start", "end_time", "text"])
        # Insert into DuckDB using DuckDB's Polars integration
        db.register("df", df)
        db.execute("INSERT INTO lines SELECT filename, start, end_time, text FROM df")
        db.unregister("df")
    
    db.commit()
    print("Reindexing completed.")

@app.get("/uttale/Scopes")
def scopes(q: str = "") -> List[str]:
    try:
        r = subprocess.run(
            ['fd', '--type', 'd', '--max-depth', '2', '--base-directory', args.root],
            capture_output=True,
            text=True,
            check=True
        )
        dirs = sorted([relpath(d, args.root) for d in r.stdout.splitlines()])
        return [d for d in dirs if q in d]
    except subprocess.CalledProcessError as e:
        print(f"Error running fd for scopes: {e}")
        return []

@app.get("/uttale/Search")
def search(scope: str, q: str) -> List[Dict]:
    if not scope:
        raise HTTPException(status_code=400, detail="Scope parameter is required")
    
    # Ensure scope ends with a slash for accurate prefix matching
    scope_prefix = scope if scope.endswith('/') else scope + '/'
    
    try:
        cursor = db.execute("""
            SELECT filename, start, end_time, text 
            FROM lines 
            WHERE filename LIKE ? AND text LIKE ?
        """, (f"{scope_prefix}%", f"%{q}%",)).fetchall()
    except Exception as e:
        print(f"Error executing search query: {e}")
        raise HTTPException(status_code=500, detail="Search query failed")
    
    return [{"filename": row[0], "text": row[3], "start": row[1], "end": row[2]} for row in cursor]

def get_audio_segment(filename, start, end):
    o = splitext(join(args.root, filename))[0] + '.ogg'
    if not exists(o):
        raise HTTPException(status_code=404, detail="File not found")
    try:
        start_sec = parse_time(start)
        end_sec = parse_time(end)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    duration = end_sec - start_sec
    if duration <= 0:
        raise HTTPException(status_code=400, detail="End time must be greater than start time")
    
    try:
        proc = subprocess.run(
            ['ffmpeg', '-ss', str(start_sec), '-t', str(duration), '-i', o, '-f', 'ogg', 'pipe:1'],
            capture_output=True,
            check=True
        )
        return proc.stdout
    except subprocess.CalledProcessError as e:
        print(f"ffmpeg error: {e.stderr.decode().strip()}")
        raise HTTPException(status_code=500, detail="Audio processing failed")

@app.get("/uttale/Play")
def play(filename: str, start: str, end: str, background_tasks: BackgroundTasks):
    try:
        audio_data = get_audio_segment(filename, start, end)
    except HTTPException as e:
        raise e
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as tmp:
        tmp.write(audio_data)
        tmp_path = tmp.name
    
    try:
        subprocess.Popen(['play', tmp_path])
    except Exception as e:
        print(f"Error playing audio: {e}")
        raise HTTPException(status_code=500, detail="Audio playback failed")
    
    # Schedule deletion of the temporary file after a short delay to ensure playback starts
    background_tasks.add_task(lambda: (time.sleep(5), exists(tmp_path) and tempfile.os.remove(tmp_path)))
    
    return {"status": "playing"}

@app.get("/uttale/Audio")
def audio_endpoint(filename: str, start: str, end: str):
    try:
        audio_data = get_audio_segment(filename, start, end)
    except HTTPException as e:
        raise e
    headers = {"Cache-Control": "max-age=86400"}
    return Response(content=audio_data, media_type="application/octet-stream", headers=headers)

@app.post("/uttale/Reindex")
def trigger_reindex(background_tasks: BackgroundTasks):
    background_tasks.add_task(reindex)
    return {"status": "Reindexing started in background"}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Uttale Server")
    parser.add_argument('--root', default='.', help='Path to the root directory containing podcasts')
    parser.add_argument('--iface', default='0.0.0.0:7010', help='Interface and port to bind the server (e.g., 0.0.0.0:7010)')
    args = parser.parse_args()
    print(f"Arguments: root={args.root}, iface={args.iface}")
    
    db = duckdb.connect('lines.duckdb')
    reindex()
    
    try:
        iface, port = args.iface.split(':')
    except ValueError:
        print("Invalid iface format. Use <interface>:<port> (e.g., 0.0.0.0:7010)")
        exit(1)
    
    uvicorn.run(app, host=iface, port=int(port))
