#!/usr/bin/env python
"""
Generate a PlantUML digraph from a clipboard.

This script is used to quickly generate an SVG from a nested list, for example:
tannlege
    grunnen til besøk
        tannverk
            hele tiden
            kommer og går

Without arguments, the script grabs the clipboard contents as HTML, generates PlantUML
file, and opens the SVG in Chrome.

TODO: ui for quick editing and parameter tweaking
TODO: distance based on # of children / total # of descendants
TODO: support bold, underline, strikethrough, italics
TODO: add cli arguments to the script
TODO: options to generate svg & open browser, or png and copy to clipboard
TODO: custom markers for colors, e.g. !=red, @=blue, #=green, $=purple, %=teal
DONE: print error when there are duplicate lines
DONE: distance based on closeness to a leaf
DONE: find out best settings for compact small graphs
DONE: argument for presets: small, large, etc
"""
import re
import sys
from shutil import which
from plumbum import BG
from plumbum.cmd import bash, xclip, plantuml
from argparse import ArgumentParser
from html2text import HTML2Text
import webbrowser
from textwrap import wrap
from bs4 import BeautifulSoup

PUML = '/tmp/digraph.puml'
SVG = '/tmp/digraph.svg'
PNG = '/tmp/digraph.png'

def chrome_binary():
    candidates = [
        '/usr/sbin/google-chrome-stable',
        '/usr/sbin/google-chrome',
    ]
    for candidate in candidates:
        if which(candidate) is not None:
            return candidate
    raise RuntimeError("Cannot find Chrome binary")

def open_in_browser(filename):
    path = chrome_binary()
    webbrowser.register('chrome', None, webbrowser.BackgroundBrowser(path))
    webbrowser.get(using='chrome').open_new_tab(filename)

def must_bin(name, comment=""):
    where = which(name)
    if where is None:
        print("ERROR: {} is not installed. {}".format(name, comment))
        exit(1)
    return where

def spit(filename, data):
    with open(filename, 'w') as f:
        f.write(data)

def slurp(filename):
    if filename is None:
        return xclip['-selection', 'clipboard', '-o', '-t', 'text/html']().strip()
    else:
        with open(filename) as f:
            return f.read().strip()

def emphasis(html):
    soup = BeautifulSoup(html, 'html.parser')
    attrs = {'style': lambda s: 'text-decoration:underline' in s}
    def underline(old):
        tag = soup.new_tag('u')
        tag.string = old.text
        old.replace_with(tag)
        return tag
    [underline(p) for p in soup.find_all('span', attrs)]
    return soup.prettify()

def clean(text):
    output = []
    for l in text.splitlines():
        line = l.strip()
        if line:
            if line != '**':
                output.append(l)
    return '\n'.join(output)

def as_text(html):
    html = emphasis(html)
    h = HTML2Text()
    h.ignore_links = True
    h.ignore_images = True
    h.ignore_emphasis = False
    h.ignore_tables = True
    out = h.handle(html)
    out = clean(out)
    return out

def dense(text):
    lines = []
    for line in text.splitlines():
        if line.strip():
            lines.append(line)
    return "\n".join(lines)

def as_label(text):
    text = re.sub(r'_(.+?)_', '<u>\\1</u>', text)
    text = text.replace('\\n', '<br/>')
    return '<' + text + '>'

class Line:
    K = 2  # number of spaces per level

    def __init__(self, text):
        self.original = text
        self.text = re.sub(r' +', ' ', text.strip('\t *'))
        self.prefix = re.search(r'[\t *]*', text).group(0)  #text[:len(text) - len(self.text)]

        self.label = as_label(self.text)
        self.level = (len(text) - len(text.lstrip())) // self.K # distance from root
        self.to_leaf = None # distance to leaf
        self.color = '#000000'

    def __repr__(self):
        return "Line({} '{}')".format(self.level, self.text)

    @staticmethod
    def validate(lines):
        seen = set()
        for i, line in enumerate(lines):
            if line.text in seen:
                raise RuntimeError("Duplicate line {}: {}".format(i, line.text))
            seen.add(line.text)
        return lines

    @staticmethod
    def from_text(text):
        lines = []
        for line in text.splitlines():
            lines.append(Line(line))
        return Line.validate(lines)

class Node:
    def __init__(self, line):
        self.line = line
        self.children = []
    def add_child(self, child): self.children.append(child)
    @staticmethod
    def from_lines(lines):
        root = Node(lines[0])
        stack = [root]
        for line in lines[1:]:
            while stack[-1].line.level >= line.level:
                stack.pop()
            node = Node(line)
            stack[-1].add_child(node)
            stack.append(node)
        return root
    def measure(self):
        if not self.children:
            self.line.to_leaf = 0
        else:
            for child in self.children:
                child.measure()
            self.line.to_leaf = max([child.line.to_leaf for child in self.children]) + 1

HEADER = """
@startuml
digraph G {
"""
FOOTER = """
}
@enduml
"""

def base():
    return '''
    #start=10;

    node[style=rounded];
    node[fontsize=20];
    #node[fontname="DejaVu Sans"]; # thick but puts some letter together
    #node[fontname="Calibri"]; # thinner, okaish
    #node[fontname="Droid Sans"];
    #node[fontname="Droid Serif"]; # thinner, okayish
    #node[fontname="Roboto"];
    #node[fontname="Roboto Serif"];
    #node[fontname="Ubuntu"];
    node [shape=box, style="rounded,filled", fillcolor="#00000000", penwidth=0];
    #node [shape=plain];
    #node [shape=plaintext];
    #node [shape=underline];

    #edge [arrowhead="vee", arrowsize=0.5, color="#00000055"];
    #edge [arrowhead="vee", arrowsize=0.5, style="tapered"];
    edge [arrowhead="none", style="tapered"];

    #concentrate=true;
    splines=true;

    #layout=neato;
    #overlap=vpsc;
    #damping=0.99;
    #defaultdist=1.0; # if pack=false
    #pack=false;
    #epsilon=0.0001;
    #mode="major";
    #mode="KK";
    #mode="sgd";
    #mode="hier";
    #mode="ipsep"; # sep="+10"
    #mode="maxent"; # uses len=1.0 on edges
    #model="shortpath";
    #model="circuit";
    #model="subset";
    #model="mds"; # uses len=1.0 on edges
    #voro_margin=0.05;

    #overlap_scaling=-100;
    #overlap=vpsc;
    #overlap=prism;
    #overlap=orthoxy;
    #overlap=compact;
    #overlap=false;
    #overlap=true;
    #overlap=scale;
    #overlap=scalexy;
'''

def large():
    # large: fdp, K=1.3, overlap=vpsc
    return '''
    layout=fdp;
    K=1.3; # fdp, sfdp
    overlap=vpsc;
    #dim=10;
    #maxiter=10000;
    #sep="+10";
'''

def medium():
    # large: fdp, K=1.3, overlap=vpsc
    return '''
    layout=fdp;
    K=0.7; # fdp, sfdp
    overlap=vpsc;
    #dim=10;
    #maxiter=10000;
    #sep="+10";
'''

def small():
    # small: sfdp, repulsiveforce=10.0, overlap=prism
    return '''
    layout=sfdp;
    repulsiveforce=8.0; # sfdp
    overlap=prism;

    #layout=neato;
    #K=1.3; # fdp, sfdp
    #repulsiveforce=8.0; # sfdp
    #overlap=scale;

    # normalize=60;
    # smoothing=rng;
'''

def neato():
    # neato: overlap=vpsc
    return '''
    layout=neato;
    overlap=vpsc;
    #damping=0.99;
    #defaultdist=1.0; # if pack=false
    #pack=false;
    #epsilon=0.0001;
    #mode="major";
    #mode="KK";
    #mode="sgd";
    #mode="hier";
    #mode="ipsep"; # sep="+10"
    #mode="maxent"; # uses len=1.0 on edges
    #model="shortpath";
    #model="circuit";
    #model="subset"; # make nice clusters, but too far apart
    #model="mds"; # uses len=1.0 on edges
    #voro_margin=0.05;
    #levelsgap=0.0; # when mode="ipsep" or "hier"
    #len=1.0; # set dynamically
    #sep="+5"; # default +4
    #esep="+3"; # default +3, should be strictly less than sep

    #overlap_scaling=-100;
    #overlap=vpsc;
    #overlap=prism;
    #overlap=orthoxy;
    #overlap=compact;
    #overlap=false;
    #overlap=true;
    #overlap=scale;
    #overlap=scalexy;
'''

def footer(preset_name):
    if preset_name == "large": return large()
    elif preset_name == "medium": return medium()
    elif preset_name == "small": return small()
    elif preset_name == "neato": return neato()
    else:
        raise ValueError("Unknown preset name: {}".format(preset_name))

def colors(lines):
    levels = { 0: "brown", 1: "green", 2: "blue", 3: "teal", 4: "purple", }
    output = []
    for line in lines:
        if line.level in levels:
            color = levels[line.level]
            output.append('    "{}" [fontcolor="{}"];'.format(line.text, color))
    return "\n".join(output) + "\n"

def clip(x): return max(0.0, min(1.0, x))

def lighter(old, factor):
    color = tuple(int(old[i:i+2], 16) for i in (1, 3, 5))
    # factor = percent / 100.0
    # Adjust the color's lightness
    new = tuple(round(c + (255 - c) * factor) for c in color)
    new_color_code = '#' + ''.join(f'{c:02X}' for c in new)
    return new_color_code

def lightness(lines):
    base = [
        '#000080', # Navy Blue
        '#228B22', # Forest Green
        '#DC143C', # Crimson Red
        '#6B3FA0', # Royal Purple
        '#008080', # Teal Green
        '#FF4500', # Burnt Orange
        '#b88400', # Goldenrod Yellow
        '#4a525a', # Dark Slate Gray
        '#00a4da', # Deep Sky Blue
        '#8B008B', # Dark Magenta
        '#627a00', # Olive Green
    ]
    # base = [
    #     '#2ECC71',
    #     '#3498DB',
    #     '#9B59B6',
    #     '#F1C40F',
    #     '#E67E22',
    #     '#E74C3C',
    #     '#1ABC9C',
    #     '#34495E',
    #     '#8E44AD',
    #     '#D35400',
    # ]
    num_levels = max(line.level for line in lines)
    output = []
    current = -1
    space_scale = 2.0
    for line in lines:
        if line.level == 0: pass
        elif line.level == 1:
            current = (current + 1) % len(base)
            color = base[current]
            line.color = color
        else:
            depth = line.level - 1
            factor = clip(depth / (num_levels*space_scale))
            color = lighter(base[current], factor)
            line.color = color
        output.append(line)
    return output

def colorize(lines):
    output = []
    scale = 2 # 3
    base = 22 # 20
    transparent = "09"
    num_levels = max(line.level for line in lines)
    for line in lines:
        size = base + (num_levels - line.level) * scale
        #size = size if line.level > 0 else base
        fill = line.color + transparent
        output.append('    "{}" [label={}, fontcolor="{}", fontsize={}, fillcolor="{}"];'.format(
            line.text, line.label, line.color, size, fill,
        ))
        # output.append('    "{}" [fontcolor="{}", fillcolor="{}"];'.format(
        #     line.text, line.color, fill,
        # ))
        # output.append('    "{}";'.format(
        #     line.text,
        # ))
    return "\n".join(output) + "\n"

def lerp(a, b, t): return (1-t)*a + t*b
def invlerp(a, b, v): return (v-a) / (b-a)
def remap(a1, a2, b1, b2, v): return lerp(b1, b2, invlerp(a1, a2, v))

def connections(lines):
    text_to_line = { line.text: line for line in lines }
    num_levels = max(line.level for line in lines)+1
    print('num_levels', num_levels, file=sys.stderr)
    last = {}
    output = []
    for line in lines:
        last[line.level] = line
        if line.level > 0:
            width = num_levels - line.level
            target = text_to_line[line.text]
            parent = last[line.level-1]
            inv_level = num_levels-1 - parent.level
            src = parent.text
            dst = line.text
            # output.append('    "{}" -> "{}"[];'.format(
            #     src, dst, width,
            # ))
            # k = 1.3
            # output.append('    "{}" -> "{}"[penwidth={}, color="{}"];'.format(
            #     src, dst, width, target.color
            # ))
            #k = round(remap(1, num_levels-1, 0.1, 3.0, inv_level), 2)
            # k = round(remap(0, num_levels-2, 0.1, 3.0, line.to_leaf), 2)
            k = round(remap(0, num_levels-2, 1.0, 1.0, line.to_leaf), 2) # default for neato preset
            #k = round(remap(0, num_levels-2, 0.1, 0.2, line.to_leaf), 2)
            print('inv_level', inv_level, 'k', k, 'to_leaf', line.to_leaf, src, dst, file=sys.stderr)
            output.append('    "{}" -> "{}"[penwidth={}, color="{}", len={}];'.format(
                src, dst, width, target.color, k,
            ))
    return "\n".join(output) + "\n"

def rewrap(lines, width):
    output = []
    for line in lines:
        text = '\\n'.join(wrap(line.text, width=width))
        text = line.prefix + text
        output.append(Line(text))
    return output

def extra(start):
    return """
    start={};
""".format(start)

def render(text, preset, start):
    max_width = 18
    text = dense(as_text(text))
    lines = Line.from_text(text)
    lines = rewrap(lines, width=max_width)
    lines = lightness(lines)
    Node.from_lines(lines).measure()

    head = HEADER + base() + preset + extra(start)
    output = head + colorize(lines) + "\n" + connections(lines) + FOOTER
    print(output)

    spit(PUML, output)
    a = bash[must_bin('plantuml'), PUML, '-tsvg', '-o', '/tmp'] & BG
    b = bash[must_bin('plantuml'), PUML, '-tpng', '-o', '/tmp'] & BG
    a.wait()
    b.wait()

def main():
    must_bin("xclip", "Install xclip to use this script.")
    must_bin("plantuml", "Install plantuml to use this script.")
    must_bin("html2text", "Install html2text to use this script.")

    parser = ArgumentParser()
    parser.add_argument("-i", "--input", default=None, help="Input file")
    parser.add_argument("-p", "--preset", default='neato', choices=['small', 'large', 'medium', 'neato'], help="Preset file")
    parser.add_argument("-s", "--start", default=1, type=int, help="Start value (seed)")
    args = parser.parse_args()

    text = slurp(args.input)
    # text = dense(as_text(text))
    # lines = Line.from_text(text)
    # lines = rewrap(lines, width=max_width)
    # lines = lightness(lines)
    # Node.from_lines(lines).measure()

    # head = footer(args.preset) + extra(args)
    # output = head + colorize(lines) + "\n" + connections(lines) + FOOTER
    # print(output)

    # if args.input is None:
    #     spit(PUML, output)
    #     bash[must_bin('plantuml'), PUML, '-tsvg', '-o', '/tmp']()
    #     bash[must_bin('plantuml'), PUML, '-tpng', '-o', '/tmp']()
    render(text, footer(args.preset), args.start)
    print("Mindmap saved to {}".format(SVG), file=sys.stderr)
    open_in_browser(SVG)

if __name__ == "__main__":
    main()