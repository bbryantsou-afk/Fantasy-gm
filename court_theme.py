"""A lightweight black mirror backdrop with soft reflections and no lines."""
import base64
from pathlib import Path
import streamlit as st

@st.cache_data(show_spinner=False)
def background_data():
    asset=Path(__file__).resolve().parent/'assets/black-mirror-soft-v1.webp'
    return base64.b64encode(asset.read_bytes()).decode('ascii')

def render_court_theme():
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
[data-testid="stSidebar"] { background:rgba(9,9,11,.94) !important; border-right:1px solid rgba(180,180,185,.12); backdrop-filter:blur(10px); }
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
