"""A lightweight black mirror backdrop with soft reflections and no lines."""
import base64
from pathlib import Path
import streamlit as st

@st.cache_data(show_spinner=False)
def background_data():
    asset=Path(__file__).resolve().parent/'assets/black-mirror-soft-v1.webp'
    return base64.b64encode(asset.read_bytes()).decode('ascii')

THEMES={"light":"簡約淺色","tactics":"戰術板草圖","mirror":"黑色鏡面"}

def theme_slug():
    return next((k for k,v in THEMES.items() if v==st.session_state.get('visual_theme')), 'light')

def clear_oauth_query():
    # Preserve presentation preferences while removing the authorization response.
    for key in ('code','state','error','error_description'):
        if key in st.query_params: del st.query_params[key]
    st.query_params['theme']=theme_slug()

def render_court_theme():
    if 'visual_theme' not in st.session_state:
        slug=st.query_params.get('theme','light')
        returned=str(st.query_params.get('state','')).split('.')
        if len(returned)==3 and '~' in returned[1]:
            slug=returned[1].split('~',1)[0]
        st.session_state.visual_theme=THEMES.get(slug,THEMES['light'])
    theme=st.sidebar.selectbox("視覺風格", ["簡約淺色", "戰術板草圖", "黑色鏡面"], key="visual_theme")
    st.query_params['theme']=theme_slug()
    image=background_data()
    st.markdown("""
<style>
.stApp {
  background-image: linear-gradient(180deg,rgba(4,4,5,.48) 0%,rgba(5,5,6,.35) 48%,rgba(5,5,6,.48) 100%),url("data:image/webp;base64,"""+image+"""") !important;
  background-size:cover !important;
  background-position:center center !important;
  background-repeat:no-repeat !important;
  background-attachment:fixed !important;
  color:#f1f5f9;
}
[data-testid="stHeader"] { background:linear-gradient(180deg,rgba(5,5,6,.92),rgba(5,5,6,0)) !important; }
[data-testid="stSidebar"] { background:rgba(5,5,7,.18) !important; border-right:1px solid rgba(180,180,185,.10); }
[data-testid="stSidebar"] [data-testid="stSidebarContent"] { background:transparent !important; }
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] { gap:7px; }
[data-testid="stSidebar"] [role="radiogroup"] > div { width:100%; }
[data-testid="stSidebar"] [data-testid="stRadioOption"] {
  display:flex !important; width:100% !important; min-height:49px; padding:12px 13px; margin:0;
  border:1px solid rgba(180,195,210,.16); border-radius:11px;
  background:rgba(15,19,25,.66); cursor:pointer;
  transition:background .15s ease,border-color .15s ease;
}
[data-testid="stSidebar"] [data-testid="stRadioOption"] p { font-size:15px !important; font-weight:550; line-height:1.4; color:#edf3fb !important; }
[data-testid="stSidebar"] [data-testid="stRadioOption"]:hover { background:rgba(42,53,65,.8); border-color:rgba(180,210,225,.4); }
[data-testid="stSidebar"] [data-testid="stRadioOption"]:has(input:checked) { background:rgba(28,87,78,.76); border-color:#69c9b5; }
[data-testid="stSidebar"] [data-testid="stRadioOption"]:focus-within { outline:2px solid #9edbd1; outline-offset:2px; }
@media(prefers-reduced-motion:reduce) { [data-testid="stSidebar"] [data-testid="stRadioOption"] { transition:none; } }
[data-testid="stSidebar"] > div { background:transparent; }
[data-testid="stMain"] h1,[data-testid="stMain"] h2,[data-testid="stMain"] h3 { color:#f4f6fa; text-shadow:0 2px 14px rgba(0,0,0,.7); }
[data-testid="stCaptionContainer"] { color:#c4cbd5; }
[data-testid="stExpander"] { background:rgba(13,13,17,.88); border-color:rgba(143,160,180,.24); }
[data-testid="stMetric"] { background:rgba(18,18,23,.94); border-color:rgba(160,180,195,.2); }
[data-testid="stAlert"] { backdrop-filter:blur(8px); }
@media(max-width:640px) {
  .stApp { background-position:58% center !important; background-attachment:scroll !important; }
  [data-testid="stSidebar"] { backdrop-filter:none; }
}
@media(prefers-reduced-motion:reduce) {
  .stApp { background-attachment:scroll !important; }
}
</style>
""",unsafe_allow_html=True)

    if theme == "戰術板草圖":
        from tactics_theme import APP_CSS
        st.markdown("<style>"+APP_CSS+"</style>",unsafe_allow_html=True)

    if theme == "簡約淺色":
        from light_theme import APP_CSS
        st.markdown("<style>"+APP_CSS+"</style>",unsafe_allow_html=True)
