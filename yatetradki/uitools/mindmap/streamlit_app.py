from textwrap import dedent, indent
from enum import Enum

import streamlit as st

from digraph import PUML as PUML_DIGRAPH
from digraph import SVG as SVG_DIGRAPH
from digraph import PNG as PNG_DIGRAPH
from digraph import render as render_digraph
from digraph import slurp
from mindmap import PUML as PUML_MINDMAP
from mindmap import SVG as SVG_MINDMAP
from mindmap import PNG as PNG_MINDMAP
from mindmap import render as render_mindmap

# TODO: control edge.len
# TODO: open png & svg in a new tab

Type = Enum('Type', 'digraph mindmap')

state = st.session_state
if 'type' not in state:
    state.type = Type.digraph.value

def fmt(s): return indent(dedent(s), ' ' * 4)

def settings(preset_name):
    if preset_name == 'neato':
        return fmt(f'''\n\
            layout=neato;
            overlap={overlap};
        ''')
    elif preset_name == 'small':
        return fmt(f'''\n\
            layout=sfdp;
            repulsiveforce={repulsiveforce}; # sfdp
            overlap={overlap};
        ''')
    elif preset_name == 'medium':
        return fmt(f'''\n\
            layout=fdp;
            K={K}; # fdp, sfdp
            overlap={overlap};
        ''')
    elif preset_name == 'large':
        return fmt(f'''\n\
            layout=fdp;
            K=1.3; # fdp, sfdp
            overlap=vpsc;
        ''')

st.set_page_config(
    page_title="Generate Mindmap",
    initial_sidebar_state="expanded",
    page_icon="🗺️",
    layout="wide",
    menu_items={
        'Get Help': 'https://github.com/balta2ar/srs-toolbelt',
        'Report a bug': "https://github.com/balta2ar/srs-toolbelt/issues",
        'About': "### Mindmap GUI",
    },
)
st.header('Mindmap GUI')

left, right = st.columns(2)

with left:
    if 'input' not in state:
        state.input = slurp(None) # "1.html"
    if 'start' not in state:
        state.start = 1
    html_text_area = st.text_area(
        'Input your HTML from Google Docs:',
        value=state.input)
    button_paste, button_digraph, button_mindmap, _ = st.columns(4)
    with button_paste:
        if st.button('Paste'):
            state.input = slurp(None)

    left1, right1 = st.columns(2)

    with left1:
        preset = st.radio(
            'Which preset?',
            ('neato', 'small', 'medium', 'large'))
        start = st.slider('start', 1, 10, state.start)

    with right1:
        if preset == 'neato':
            overlap = st.radio('overlap', ('vpsc',), horizontal=True)
        elif preset == 'small':
            overlap = st.radio('overlap', ('prism',), horizontal=True)
            repulsiveforce = st.slider('repulsiveforce', 0.0, 30.0, 8.0, step=0.5)
        elif preset == 'medium':
            overlap = st.radio('overlap', ('vpsc',), horizontal=True)
            K = st.slider('K', 0.0, 3.0, 0.7, step=0.1)
        elif preset == 'large':
            overlap = st.radio('overlap', ('vpsc',), horizontal=True)
            K = st.slider('K', 0.0, 3.0, 1.3, step=0.1)

with button_digraph:
    if st.button('Digraph'):
        state.type = Type.digraph.value
        render_digraph(state.input, settings(preset), start)
with button_mindmap:
    if st.button('Mindmap'):
        state.type = Type.mindmap.value
        render_mindmap(state.input)

puml = ''
with right:
    png, svg = st.tabs(['PNG', 'SVG'])
    if state.type == Type.digraph.value:
        with png:
            st.image(PNG_DIGRAPH)
        with svg:
            st.image(SVG_DIGRAPH)
        puml = slurp(PUML_DIGRAPH)
    elif state.type == Type.mindmap.value:
        with png:
            st.image(PNG_MINDMAP)
        with svg:
            st.image(SVG_MINDMAP)
        puml = slurp(PUML_MINDMAP)

st.divider()
st.text(puml)

hide_streamlit_style = """                                                                                      
            <style>                                                                                             
            footer {visibility: hidden;}                                                                        
            </style>                                                                                            
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
