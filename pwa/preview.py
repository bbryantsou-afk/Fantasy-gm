"""Local comparison host for only the new component, without legacy page widgets."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import streamlit as st
st.set_page_config(page_title='Fantasy GM · App 預覽',layout='wide')
from account_store import init_account
init_account()
from pwa.streamlit_host import render
render()
