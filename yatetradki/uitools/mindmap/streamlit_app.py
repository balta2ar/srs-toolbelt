from textwrap import dedent, indent
import streamlit as st
from digraph import slurp, render, PUML

state = st.session_state

def fmt(s): return indent(dedent(s.strip()), '    ')

def settings(preset_name):
    if preset_name == 'neato':
        return fmt(f'''
            layout=neato;
            overlap={overlap};
        ''')
    elif preset_name == 'small':
        return fmt(f'''
            layout=sfdp;
            repulsiveforce={repulsiveforce}; # sfdp
            overlap={overlap};
        ''')
    elif preset_name == 'medium':
        return fmt(f'''
            layout=fdp;
            K={K}; # fdp, sfdp
            overlap={overlap};
        ''')
    elif preset_name == 'large':
        return fmt(f'''
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
        state.input = slurp('1.html')
    if 'start' not in state:
        state.start = 1
    html_text_area = st.text_area(
        'Input your HTML from Google Docs:',
        value=state.input)
    button_paste, button_generate, _ = st.columns(3)
    with button_paste:
        if st.button('Paste from clipboard'):
            state.input = slurp(None)

    left1, right1 = st.columns(2)

    with left1:
        preset = st.radio(
            'Which preset?',
            ('neato', 'small', 'medium', 'large'))
        start = st.slider('start', 1, 20, state.start)

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

with button_generate:
    if st.button('Generate'):
        render(state.input, settings(preset), start)

with right:
    png, svg = st.tabs(['PNG', 'SVG'])
    with png:
        st.image('/tmp/digraph.png')
    with svg:
        st.image('/tmp/digraph.svg')

st.divider()
st.text(slurp(PUML))

hide_streamlit_style = """                                                                                      
            <style>                                                                                             
            footer {visibility: hidden;}                                                                        
            </style>                                                                                            
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
