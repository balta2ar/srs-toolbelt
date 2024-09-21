import argparse, subprocess, webvtt, uvicorn, duckdb, multiprocessing as mp, threading, time, os, tempfile
from fastapi import FastAPI, HTTPException, Response, BackgroundTasks
from typing import List, Dict
from os.path import join, relpath, exists, splitext
from tqdm import tqdm
import polars as pl

app = FastAPI()
db_duckdb = None

def parse_time(t: str) -> float:
    h, m, s = t.split(':')
    s, ms = s.split('.')
    return int(h)*3600 + int(m)*60 + float(s) + int(ms)/1000

def process_vtt(vtt: str, root: str) -> List[tuple]:
    abs_vtt = join(root, vtt)
    rel_vtt = relpath(abs_vtt, root)
    if not exists(abs_vtt):
        return []
    try:
        captions = []
        for c in webvtt.read(abs_vtt):
            captions.append((rel_vtt, c.start, c.end, c.text))
        return captions
    except:
        return []

def reindex_worker_duckdb(vtt_files: List[str], root: str, return_dict, idx: int, counter, lock: mp.Lock):
    rows = []
    for vtt in vtt_files:
        captions = process_vtt(vtt, root)
        rows.extend(captions)
        with lock:
            counter.value +=1
    return_dict[idx] = rows

def update_progress(total: int, counter, lock: mp.Lock, stop_event: threading.Event, description: str):
    with tqdm(total=total, desc=description) as pbar:
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

def reindex(root: str):
    global db_duckdb
    db_duckdb.execute("DROP TABLE IF EXISTS lines")
    db_duckdb.execute("CREATE TABLE lines (filename VARCHAR, start VARCHAR, end_time VARCHAR, text VARCHAR)")
    try:
        fd = subprocess.run(['fd', '--type', 'f', '--extension', 'vtt', '--base-directory', root], capture_output=True, text=True, check=True)
        vtt_files = fd.stdout.splitlines()
    except:
        vtt_files = []
    total_files = len(vtt_files)
    if not vtt_files:
        return
    manager = mp.Manager()
    return_dict = manager.dict()
    counter = manager.Value('i',0)
    lock = manager.Lock()
    num_processes = min(mp.cpu_count(),8)
    chunk_size = (total_files + num_processes -1)//num_processes
    chunks = [vtt_files[i:i+chunk_size] for i in range(0, total_files, chunk_size)]
    jobs = []
    for idx, chunk in enumerate(chunks):
        p = mp.Process(target=reindex_worker_duckdb, args=(chunk, root, return_dict, idx, counter, lock))
        jobs.append(p)
        p.start()
    stop_event = threading.Event()
    progress_thread = threading.Thread(target=update_progress, args=(total_files, counter, lock, stop_event, "Reindexing DuckDB"))
    progress_thread.start()
    for p in jobs:
        p.join()
    stop_event.set()
    progress_thread.join()
    all_rows = []
    for idx in range(len(chunks)):
        all_rows.extend(return_dict.get(idx, []))
    if all_rows:
        df = pl.DataFrame(all_rows, schema=["filename", "start", "end_time", "text"])
        db_duckdb.register("df", df)
        db_duckdb.execute("INSERT INTO lines SELECT filename, start, end_time, text FROM df")
        db_duckdb.unregister("df")
    db_duckdb.commit()

@app.get("/uttale/Scopes")
def scopes(q: str = "") -> List[str]:
    try:
        r = subprocess.run(['fd', '--type', 'd', '--max-depth', '2', '--base-directory', args.root], capture_output=True, text=True, check=True)
        dirs = sorted([relpath(d, args.root) for d in r.stdout.splitlines()])
        return [d for d in dirs if q.lower() in d.lower()]
    except:
        return []

@app.get("/uttale/Search")
def search(q: str, scope: str = "") -> List[Dict]:
    scope_prefix = scope #if scope.endswith('/') else scope + '/'
    try:
        cursor = db_duckdb.execute("SELECT filename, start, end_time, text FROM lines WHERE filename LIKE ? AND text LIKE ?", (f"{scope_prefix}%", f"%{q}%",)).fetchall()
    except:
        raise HTTPException(status_code=500, detail="DuckDB search query failed")
    return [{"filename": row[0], "text": row[3], "start": row[1], "end": row[2]} for row in cursor]

def get_audio_segment(filename: str, start: str, end: str) -> bytes:
    o = splitext(join(args.root, filename))[0] + '.ogg'
    if not exists(o):
        raise HTTPException(status_code=404, detail="File not found")
    try:
        start_sec = parse_time(start)
        end_sec = parse_time(end)
    except:
        raise HTTPException(status_code=400, detail="Invalid time format")
    duration = end_sec - start_sec
    if duration <=0:
        raise HTTPException(status_code=400, detail="End time must be greater than start time")
    try:
        proc = subprocess.run(['ffmpeg', '-ss', str(start_sec), '-t', str(duration), '-i', o, '-f', 'ogg', 'pipe:1'], capture_output=True, check=True)
        return proc.stdout
    except:
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
    except:
        raise HTTPException(status_code=500, detail="Audio playback failed")
    def cleanup(tmp_file):
        try:
            time.sleep(5)
            if exists(tmp_file):
                os.remove(tmp_file)
        except:
            pass
    background_tasks.add_task(cleanup, tmp_path)
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
    background_tasks.add_task(reindex, args.root)
    return {"status": "Reindexing started in background"}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', default='.')
    parser.add_argument('--iface', default='0.0.0.0:7010')
    args = parser.parse_args()
    db_duckdb = duckdb.connect('lines_duckdb.db')
    # reindex(args.root)
    try:
        iface, port = args.iface.split(':')
    except:
        exit(1)
    uvicorn.run(app, host=iface, port=int(port))
