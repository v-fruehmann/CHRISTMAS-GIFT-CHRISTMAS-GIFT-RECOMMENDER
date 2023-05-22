import streamlit as st
import random


@st.cache(allow_output_mutation=True)
def user_input():
    return {}


def page_config():
    st.set_page_config(
        page_title="Toys Recommender",
        layout="centered",
    )

def background(url):
    '''This function sets a gif in the background.
    '''
    st.markdown(
        f'''
    <style>
    .main {{
        background-image: url({url});
        background-size: cover;
        background-position-x: center;
        opacity: 80%;
    }}
    </style>
    ''',  
    unsafe_allow_html=True,
    )


