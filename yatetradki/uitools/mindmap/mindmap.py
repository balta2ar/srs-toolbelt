#!/usr/bin/env python
"""
Generate a PlantUML mindmap from a clipboard.

This script is used to quickly generate an SVG from a nested list, for example:
tannlege
    grunnen til besøk
        tannverk
            hele tiden
            kommer og går

Without arguments, the script grabs the clipboard contents as HTML, generates PlantUML
file, and opens the SVG in Chrome.
"""
import sys
from shutil import which
from plumbum import BG
from plumbum.cmd import xclip, plantuml
from argparse import ArgumentParser
from html2text import HTML2Text
import webbrowser

PUML = '/tmp/mindmap.puml'
PNG = '/tmp/mindmap.png'
SVG = '/tmp/mindmap.svg'

def chrome_binary():
    canditates = [
        '/usr/sbin/google-chrome-stable',
        '/usr/sbin/google-chrome',
    ]
    for candidate in canditates:
        if which(candidate) is not None:
            return candidate
    raise RuntimeError("Cannot find Chrome binary")

def open_in_browser(filename):
    path = chrome_binary()
    webbrowser.register('chrome', None, webbrowser.BackgroundBrowser(path))
    webbrowser.get(using='chrome').open_new_tab(filename)

def must_bin(name, comment):
    if which(name) is None:
        raise RuntimeError("{} is not installed. {}".format(name, comment))

def spit(filename, data):
    with open(filename, 'w') as f:
        f.write(data)

def slurp(filename):
    if filename is None:
        return xclip['-selection', 'clipboard', '-o', '-t', 'text/html']().strip()
    else:
        with open(filename) as f:
            return f.read().strip()

def as_text(text):
    h = HTML2Text()
    h.ignore_links = True
    h.ignore_images = True
    h.ignore_emphasis = True
    h.ignore_tables = True
    return h.handle(text)

def dense(text):
    lines = []
    for line in text.splitlines():
        if line.strip():
            lines.append(line)
    return "\n".join(lines)

class Line:
    K = 2  # number of spaces per level

    def __init__(self, text):
        self.original = text
        self.text = text.strip('\t *')
        self.level = (len(text) - len(text.lstrip())) // self.K
        self.divider = text == 'left side'

    def __repr__(self):
        return "Line({} '{}')".format(self.level, self.text)

    @staticmethod
    def from_text(text):
        lines = []
        for line in text.splitlines():
            lines.append(Line(line))
        return lines

HEADER = """
@startmindmap
<style>
mindmapDiagram {
    .green * { FontColor green }
    .darkgreen * { FontColor darkgreen }
    .blue * { FontColor blue }
    .brown * { FontColor brown }
    .sienna * { FontColor sienna }
    .darkorange * { FontColor darkorange }
    .red * { FontColor red }
    .maroon * { FontColor maroon }
    .purple * { FontColor purple }
    .teal * { FontColor teal }
    .deepskyblue * { FontColor deepskyblue }
    .peru * { FontColor peru }
    boxless {
        FontColor black
        FontSize 20
    }
    arrow {
        LineStyle 1
        LineColor grey
        LineThickness 1.0
    }
}
</style>
"""
FOOTER = """
@endmindmap
"""

def colors(lines):
    available = [
        'darkgreen',
        'blue',
        'brown',
        'darkorange',
        'red',
        'sienna',
        'maroon',
        'green',
        'purple',
        'teal',
        'deepskyblue',
        'peru',
    ]
    output = []
    current = 0
    for line in lines:
        if line.level == 1:
            text = line.original + " <<" + available[current] + ">>"
            line = Line(text)
            current = (current + 1) % len(available)
        output.append(line)
    return output

def divide(lines):
    if len(lines) < 3: return lines
    mid = len(lines) // 2
    separator = Line('left side')
    def split(at):
        lines.insert(at, separator)
        return lines
    def dist(pos): return abs(pos - mid)
    def next(at, direction, level):
        while at >= 0 and at < len(lines):
            if lines[at].level == level: return at
            at += direction
        return None
    divisible_level = 1
    left = next(mid, -1, divisible_level)
    right = next(mid, 1, divisible_level)
    if left is None and right is None: return lines
    if left is not None and right is not None:
        return split(left) if dist(left) < dist(right) else split(right)
    if left is not None: return split(left)
    if right is not None: return split(right)
    return lines

def markdown(lines):
    output = []
    for (i, line) in enumerate(lines):
        text = line.original
        if not line.divider:
            text = '* ' + line.original if i == 0 else line.original
            text = text.replace('*', '*_', 1)
        output.append(text)
    return '\n'.join(output)

def render(text):
    text = dense(as_text(text))
    lines = Line.from_text(text)
    lines = colors(lines)
    lines = divide(lines)

    output = HEADER + markdown(lines) + FOOTER
    print(output)

    spit(PUML, output)
    a = plantuml[PUML, '-tsvg', '-o', '/tmp'] & BG
    b = plantuml[PUML, '-tpng', '-o', '/tmp'] & BG
    a.wait()
    b.wait()

def main():    
    must_bin("xclip", "Install xclip to use this script.")
    must_bin("plantuml", "Install plantuml to use this script.")
    must_bin("html2text", "Install html2text to use this script.")

    parser = ArgumentParser()
    parser.add_argument("-i", "--input", default=None, help="Input file")
    args = parser.parse_args()

    text = slurp(args.input)
    # text = dense(as_text(text))
    # lines = Line.from_text(text)
    # lines = colors(lines)
    # lines = divide(lines)

    # output = HEADER + markdown(lines) + FOOTER
    # print(output)

    # if args.input is None:
    #     spit(PUML, output)
    #     plantuml[PUML, '-tsvg', '-o', '/tmp']()
    render(args.input)
    print("Mindmap saved to {}".format(SVG), file=sys.stderr)
    open_in_browser(SVG)

if __name__ == "__main__":
    main()