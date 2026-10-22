"""Collect optional mobile guidance at the end of the active page."""
import streamlit as st

def caption(body, **kwargs):
    if st.session_state.get('device_view') == '手機版':
        notes=st.session_state.setdefault('_page_guidance',[])
        if body not in notes:notes.append(body)
    else:st.caption(body, **kwargs)

def note(body):
    notes=st.session_state.setdefault('_page_guidance',[])
    if body not in notes:notes.append(body)

def table(title,rows):
    st.session_state.setdefault('_page_guidance_tables',{})[title]=rows

def render():
    notes=st.session_state.pop('_page_guidance',[])
    tables=st.session_state.pop('_page_guidance_tables',{})
    if notes or tables:
        with st.expander('本頁說明',expanded=False):
            for item in notes:st.caption(item)
            for title,rows in tables.items():
                st.markdown('**'+title+'**')
                st.dataframe(rows,hide_index=True,width='stretch')
