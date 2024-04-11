#!/usr/bin/env python3

# ideas
# - display part of speech, color code (especially adjectives and verbs)
# - copy audio to clipboard (extract with ffmpeg + pyperclip/xclip)

import argparse
import logging
import os
import re
import time
from bisect import bisect_left
from collections import defaultdict, namedtuple
from dataclasses import dataclass
from inspect import isgenerator
from os.path import exists, join, splitext
from pathlib import Path
from pprint import pprint
from typing import Callable, Iterable, List

from nicegui import app, ui
from nicegui.elements.audio import Audio
from nicegui.elements.button import Button
from nicegui.elements.input import Input
from nicegui.events import KeyEventArguments
from pydantic import BaseModel

ASSETS = './assets'
logging.basicConfig(level=logging.DEBUG)
logging.info(f"Starting harken. ASSETS={ASSETS}")

MEDIA = set(['.mp3', '.mp4', '.mkv', '.avi', '.webm', '.opus', '.ogg'])
SUBS = set(['.vtt'])

NamedPair = namedtuple('NamedPair', ['sub', 'media'])

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

def with_extension(path: str, ext: str) -> str:
    return splitext(path)[0] + ext

def search_index(index, q):
    results = index.search(q)
    out = []
    for doc in [index.get_document(result) for result in results]:
        sub = doc['filename']
        for ext in MEDIA:
            path = with_extension(sub, ext)
            if exists(sub) and exists(path):
                out.append(SearchResult(
                    content=doc['content'],
                    id=doc['id'],
                    title=with_extension(doc['filename'], ext),
                    offset=doc['offset'],
                    subtitle=doc['filename'],
                    media=with_extension(doc['filename'], ext)
                ).dict())
    return out

index = None

def parse_ts_int(s):
    """
    00:00:26,240
    00:00:09.320
    """
    h, m, s_ms = s.split(':')
    s, ms = s_ms.replace('.', ',').split(',')
    return int(h) * 3600000 + int(m) * 60000 + int(s) * 1000 + int(ms)

def parse_ts(s):
    return parse_ts_int(s) / 1000.0

class Subtitle(BaseModel):
    start_time: str
    start: float
    end_time: str
    end: float
    text: str
    offset: int

class SearchResult(BaseModel):
    content: str
    id: int
    title: str
    offset: int
    subtitle: str
    media: str

def equals(a, b): assert a == b, f"{a} != {b}"

class Search:
    def trigrams(word): return [word[i:i+3] for i in range(len(word)-2)] or [word]
    def __init__(self):
        self.docs = {} # doc_id to doc mapping
        self.plist = defaultdict(set) # term to doc_id mapping
        self.trigram_index = defaultdict(set) # trigram to terms mapping
    # def media(self, needle) -> [str]:
        # return [doc['media'] for doc in self.docs.values() if needle in doc['media']]
    def content(self, documents):
        t0 = time.time()
        self.docs.update({doc['id']: doc for doc in documents})
        def tokenize(text): return re.findall(r'\b[a-zA-Z0-9åøæÅØÆ]+\b', text.lower())
        for document in documents:
            doc_id = document['id']
            # title = document['title']
            content = document['content']
            for term in tokenize(content):
                self.plist[term].add(doc_id)
        for term in self.plist:
            for trigram in Search.trigrams(term):
                self.trigram_index[trigram].add(term)
        logging.info(f"Index built in {time.time() - t0:.2f}s, {len(self.docs)} documents, {len(self.plist)} terms, {len(self.trigram_index)} trigrams")
        return self
    def search(self, query):
        t0 = time.time()
        query_words = query.lower().split()
        if not query_words: return []
        logging.info(f"Searching for '{query_words}'")
        sets_of_words = [list(self._trigram_words(w)) for w in query_words]
        if not sets_of_words: return []
        logging.info(f'Words mapped to trigrams: {sets_of_words}')

        # trigrams(word) map to many terms, so it's union between trigrams mapped to terms
        # but since the query itself assumes AND, we intersect between sets of terms
        result = self._search(sets_of_words[0], set.union)
        logging.info(f'Result after first word: {result}')
        for words in sets_of_words[1:]:
            result = result.intersection(self._search(words, set.union))

        logging.info(f"Search for '{query}' took {time.time() - t0:.2f}s, {len(result)} results")
        return sorted(list(result))
    def _trigram_words(self, query_word):
        result = set()
        for trigram in Search.trigrams(query_word):
            for word in self.trigram_index[trigram]:
                if query_word in word:
                    result.add(word)
        return result
    def _search(self, query_words, set_combine):
        if not query_words: return set()
        result = self.plist[query_words[0]]
        for word in query_words[1:]:
            if word in self.plist:
                result = set_combine(result, self.plist[word])
        return result
    def get_document(self, doc_id): return self.docs[doc_id]
    def get_documents(self, doc_ids): return [self.get_document(doc_id) for doc_id in doc_ids]

def consume(line, pattern, *parsers):
    matches = re.match(pattern, line)
    if not matches: raise ValueError(f"Pattern {pattern} did not match line {line}")
    return tuple(parser(group) for parser, group in zip(parsers, matches.groups()))

RX_TIMESTAMP = r'(\d{2}:\d{2}:\d{2}[,.]\d{3}) --> (\d{2}:\d{2}:\d{2}[,.]\d{3})'

def parse_subtitles(filename) -> Iterable[Subtitle]:
    suffix = splitext(filename)[1]
    match suffix:
        case '.srt': return parse_srt(open(filename))
        case '.vtt': return parse_vtt(open(filename))
        case _: raise ValueError(f"Unknown subtitle format {suffix}")

def parse_srt(lines) -> Iterable[Subtitle]:
    if not isgenerator(lines): lines = iter(lines)
    for line in lines:
        i = consume(line, r'(\d+)', int)
        start_str, end_str = consume(next(lines), RX_TIMESTAMP, str, str)
        text = consume(next(lines), r'(.*)', str)[0]
        _ = consume(next(lines), r'^$')
        s = parse_ts(start_str)
        e = parse_ts(end_str)
        yield Subtitle(start_time=start_str, start=s, end_time=end_str, end=e, text=text, offset=i[0])

def parse_vtt(lines) -> Iterable[Subtitle]:
    if not isgenerator(lines): lines = iter(lines)
    _ = consume(next(lines), r'^WEBVTT$')
    _ = consume(next(lines), r'^$')
    for i, line in enumerate(lines):
        start_str, end_str = consume(line, RX_TIMESTAMP, str, str)
        text = consume(next(lines), r'(.*)', str)[0]
        _ = consume(next(lines), r'^$')
        s = parse_ts(start_str)
        e = parse_ts(end_str)
        yield Subtitle(start_time=start_str, start=s, end_time=end_str, end=e, text=text, offset=i)

def find(where: str, subs: Iterable[str], medias: Iterable[str]) -> List[NamedPair]:
    result = []
    for root, dirs, files in os.walk(where, followlinks=True):
        for filename in files:
            media = join(root, filename)
            media_ext = Path(filename).suffix
            for sub_ext in subs:
                sub = with_extension(media, sub_ext)
                if media_ext in medias and exists(media) and exists(sub):
                    # relative_path = os.path.relpath(os.path.join(root, filename), where)
                    result.append(NamedPair(sub=sub, media=media))
    logging.info(f"Found {len(result)} pairs at {where}")
    return result

class Corpus:
    def __init__(self):
        self.doc_id = 0
    def read(self, filenames: List[NamedPair]):
        docs = []
        for file in filenames:
            start_doc_id = self.doc_id
            for line in parse_subtitles(file.sub):
                docs.append({
                    "id": self.doc_id,
                    "sub": f'{file.sub}',
                    "media": f'{file.media}',
                    "content": line.text,
                    "offset": self.doc_id - start_doc_id,
                })
                self.doc_id += 1
        logging.info(f"Read {len(docs)} documents from {len(filenames)} files")
        return docs

def test_parse():
    srt = 'w/byday/20230904/by10m/by10m_03.srt'
    lines = list(parse_subtitles(join(MEDIA_DIR, srt)))
    pprint(lines)
    vtt = 'w/byday/20230904/by10m/by10m_03.vtt'
    lines = list(parse_subtitles(join(MEDIA_DIR, vtt)))
    pprint(lines)

def test_vtt():
    vtt = 'h/ukesnytt/20240331/by10m/by10m_01.vtt'
    lines = list(parse_subtitles(vtt))
    pprint(lines)

def test_search():
    search = Search()

    # corpus = [
    #     {"id": 0, "title": "apple", "content": "Apples are normally found in the fruit section"},
    #     {"id": 1, "title": "banana", "content": "hånd bananas are Yellow"},
    #     {"id": 2, "title": "orange", "content": "oranges are not found From another planet"},
    #     {"id": 3, "title": "fourth", "content": "retired soldier returns"},
    # ]
    # search.fit(corpus)
    # equals([1], search.transform("hånd"))
    # equals([0], search.transform("apples"))
    # equals([0, 1, 2], search.transform("are"))
    # equals([2], search.transform("from"))
    # equals([0, 2], search.transform("are found"))
    # equals([3], search.transform("red"))
    # equals([3], search.transform("red ns"))

    corp = Corpus()
    corpus = corp.read(find(MEDIA_DIR, SUBS))
    search.content(corpus)
    # pprint(search.show(search.transform("smukke")))
    pprint(search.get_documents(search.search("porten")))
    # equals([1], search.transform("smukke"))

ui.add_css('''
:root {
    --nicegui-default-padding: 1.0rem;
    --nicegui-default-gap: 0.1rem;
}
.active {
    font-weight: bold;
}
''')

class MyPlayer:
    def __init__(self, player: Audio):
        self.player: Audio = player
        self.playing = False
    def play(self):
        self.player.play()
        self.playing = True
    def toggle(self):
        if self.playing: self.player.pause()
        else: self.player.play()
        self.playing = not self.playing
    def seek_and_play(self, at):
        self.player.seek(at)
        self.play()

class SubtitleLines:
    def __init__(self):
        self.reset()
    def reset(self):
        self.lines = []
        self.starts = []
        self.current_line = 0
    def activate(self, at): # float (time in seconds) or int (index, # of the line)
        if isinstance(at, int): index = at
        elif isinstance(at, float): index = max(0, bisect_left(self.starts, at)-1)
        else: raise ValueError(f"Invalid type {type(at)}: {at}")
        self.lines[self.current_line].classes(remove='active')
        self.lines[index].classes(add='active')
        self.current_line = index
    def add(self, line, start):
        self.lines.append(line)
        self.starts.append(start)

@dataclass
class UiState:
    files: List[NamedPair]
    media2file: dict
    current_file: NamedPair
    subtitles: [Subtitle]
    sub_lines: SubtitleLines
    player: MyPlayer
    button_record: Button
    button_play: Button
    button_compress: Button
    search_field: Input
    search_query: str
    commands: [Callable]

def main(reload=False):
    parser = argparse.ArgumentParser()
    parser.add_argument('dirs', nargs='+', help='Media directories, can be several')
    args = parser.parse_args()
    logging.info(f"Args: {args}")

    search = Search()
    corp = Corpus()
    files: List[NamedPair] = []
    for media_dir in args.dirs:
        logging.info(f"Indexing {media_dir}")
        batch = find(media_dir, SUBS, MEDIA)
        files.extend(batch)
        corpus = corp.read(batch)
        search.content(corpus)
        app.add_media_files(media_dir, Path(media_dir))

    state = UiState(
        files=sorted(list(set(files)), key=lambda x: x.media),
        media2file={m.media: m for m in files},
        current_file=files[0],
        subtitles=list(parse_subtitles(files[0].sub)),
        sub_lines=SubtitleLines(),
        player=MyPlayer(None),
        button_record=None,
        button_play=None,
        button_compress=None,
        search_field=None,
        search_query='',
        commands=[]
    )
    logging.info(f"Media files: {len(files)}")

    def load_media(media: str, offset: int = -1):
        file = state.media2file[media]
        state.subtitles.clear()
        state.subtitles.extend(list(parse_subtitles(file.sub)))
        state.current_file = file
        state.commands.clear()
        at = 0.0 if offset < 0 else state.subtitles[offset].start
        state.commands.append(lambda: state.player.seek_and_play(at))
        draw.refresh()

    def play_line(sub: Subtitle): state.player.seek_and_play(sub.start)
    def play_line_by_index(index: int):
        index = max(0, min(index, len(state.subtitles)-1))
        state.sub_lines.activate(index)
        play_line(state.subtitles[index])
    def replay_current_line(): play_line_by_index(state.sub_lines.current_line)
    def play_previous_line(): play_line_by_index(state.sub_lines.current_line - 1)
    def play_next_line(): play_line_by_index(state.sub_lines.current_line + 1)
    async def player_position():
        return await ui.run_javascript("document.querySelector('audio').currentTime")
    async def player_update(ev):
        at = await player_position()
        state.sub_lines.activate(at)

    def on_key(ev: KeyEventArguments):
        if ev.key == 'v' and ev.action.keydown:
            state.player.toggle()
        elif ev.key == 'w' and ev.action.keydown:
            replay_current_line()
        elif ev.key == 'q' and ev.action.keydown:
            play_previous_line()
        elif ev.key == 'f' and ev.action.keydown:
            play_next_line()
        elif ev.key == 'r' and ev.action.keydown:
            state.button_record.run_method('click')
        elif ev.key == 'p' and ev.action.keydown:
            state.button_play.run_method('click')
        elif ev.key == 'c' and ev.action.keydown:
            state.button_compress.run_method('click')
        elif ev.key == 'k' and ev.action.keydown:
            state.search_field.run_method('focus')

    @ui.refreshable
    def redraw_search(query=None):
        if not query: return
        ids = search.search(query)[0:10]
        docs = search.get_documents(ids) # content, id, media, offset, sub
        # with ui.scroll_area().classes('border w-full h-80'):
        with ui.column().classes('border w-full'):
            for doc in docs:
                print('doc', doc)
                on_click = lambda doc=doc: load_media(doc['media'], doc['offset'])
                content = doc['content']
                content = re.sub(rf'({query})', r'<b>\1</b>', content, flags=re.IGNORECASE)
                ui.html(content).classes('pl-4 hover:outline-1 hover:outline-dashed').on('click', on_click)
    def on_search(e):
        nonlocal state
        state.search_query = e.value
        redraw_search.refresh(e.value)
    async def on_record_toggle(self):
        print(self)
        recording = await ui.run_javascript('''
if (window.recorder && window.recorder.state === 'recording') {
    window.recorder.stop()
    return false
} else {
    navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
        const context = new AudioContext()
        const source = context.createMediaStreamSource(stream)
        const compressor = context.createDynamicsCompressor()

        compressor.threshold.setValueAtTime(-50, context.currentTime) // dB
        compressor.knee.setValueAtTime(40, context.currentTime) // dB
        compressor.ratio.setValueAtTime(12, context.currentTime)
        compressor.attack.setValueAtTime(0, context.currentTime) // seconds
        compressor.release.setValueAtTime(0.25, context.currentTime) // seconds

        source.connect(compressor)
        //compressor.connect(context.destination)
        const destination = context.createMediaStreamDestination()
        compressor.connect(destination)

        window.chunks = []
        //window.recorder = new MediaRecorder(stream)
        window.recorder = new MediaRecorder(destination.stream)
        window.recorder.addEventListener('dataavailable', e => { window.chunks.push(e.data) })
        window.recorder.addEventListener('stop', e => {
            const blob = new Blob(window.chunks, { type: 'audio/ogg; codecs=opus' })
            const url = URL.createObjectURL(blob)
            window.audio = new Audio(url)  
        })
        window.recorder.start()
    })
    return true
}
''')
        self.sender.props(f'color={"red" if recording else "green"}')
    def on_record_play():
        ui.run_javascript('window.audio.play()')
    def on_add_dynamic_compression(self):
        ui.run_javascript('''
const context = new AudioContext()
const audioElement = document.querySelector('audio')
const source = context.createMediaElementSource(audioElement)
const compressor = context.createDynamicsCompressor()

compressor.threshold.setValueAtTime(-50, context.currentTime) // dB
compressor.knee.setValueAtTime(40, context.currentTime) // dB
compressor.ratio.setValueAtTime(12, context.currentTime)
compressor.attack.setValueAtTime(0, context.currentTime) // seconds
compressor.release.setValueAtTime(0.25, context.currentTime) // seconds

source.connect(compressor)
compressor.connect(context.destination)
console.log('Dynamic compression added')
''')
        self.sender.props(f'color={"green"}')
        self.sender.disable()

    @ui.refreshable
    def draw():
        keyboard = ui.keyboard(on_key=on_key)
        nonlocal state
        with ui.row().classes('w-full'):
            state.search_field = ui.input(label='Search by word',
                                          value=state.search_query,
                                          placeholder='Type something to search',
                                          on_change=on_search).classes('w-2/12 pl-1')
            state.button_record = ui.button('R').on('click', on_record_toggle).tooltip('Record audio')
            state.button_play = ui.button('P').on('click', on_record_play).tooltip('Play recorded audio')
            state.button_compress = ui.button('C').on('click', on_add_dynamic_compression).tooltip('Add dynamic compression')
            state.player.player = ui.audio(state.current_file.media).classes('w-8/12')
            state.player.player.on('timeupdate', player_update)
        with ui.row().classes('w-full'):
            with ui.column().classes('border w-4/12'):
                with ui.scroll_area().classes('border w-full h-80'):
                    for f in files:
                        on_click = lambda f=f: load_media(f.media)
                        classes = 'hover:underline cursor-pointer'
                        if f == state.current_file: ui.label(f.media).on('click', on_click).classes(classes + ' active')
                        else: ui.label(f.media).on('click', on_click).classes(classes)
                redraw_search(state.search_query)
            # with ui.column().classes('border w-5/12'):
            with ui.scroll_area().classes('border w-7/12 h-[90vh]'):
                with ui.row():
                    state.sub_lines.reset()
                    for s in state.subtitles:
                        on_click = lambda s=s: play_line(s)
                        with ui.row().classes('hover:ring-1'):
                            l = ui.label(f'{s.text}').on('dblclick', on_click)
                            state.sub_lines.add(l, s.start)
        for c in state.commands: c()
        state.commands.clear()
    draw()
    ui.run(title='herken', show=False, reload=reload)


if __name__ in {'__main__', '__mp_main__'}:
    main(reload=True)