"""Responsive density and auto-collapsing navigation shared by both entry URLs."""
import streamlit as st
import streamlit.components.v1 as components
CSS='''
.st-key-watch_grid{display:grid!important;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px!important;align-items:start}
.st-key-watch_grid>[data-testid="stLayoutWrapper"]{min-width:0}
.st-key-watch_grid [data-testid="stVerticalBlockBorderWrapper"]{padding:10px!important}
.st-key-watch_grid img{max-height:76px;object-fit:contain}
.st-key-watch_grid button{font-size:13px!important;padding:5px 8px!important;min-height:36px}
@media(max-width:640px){
 [data-testid="stMainBlockContainer"]{padding:1rem .65rem 3rem!important}
 [data-testid="stVerticalBlock"]{gap:.55rem}
 [data-testid="stElementContainer"]{margin-bottom:0!important}
 [data-testid="stMain"] h1{font-size:1.65rem!important;margin-bottom:.35rem!important}
 [data-testid="stMain"] h2{font-size:1.35rem!important}
 [data-testid="stMain"] h3{font-size:1.1rem!important}
 [data-testid="stMain"] p,[data-testid="stMain"] label{font-size:13px!important;line-height:1.45!important}
 [data-testid="stMetric"]{padding:8px!important;min-height:0!important}
 [data-testid="stMetricValue"]{font-size:1.3rem!important}
 [data-testid="stExpander"] summary{padding:7px 9px!important}
 [data-testid="stVerticalBlockBorderWrapper"]{padding:8px!important}
 .st-key-watch_grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:7px!important}
 .st-key-watch_grid img{max-height:60px;width:75px!important}
 .st-key-watch_grid [data-testid="stVerticalBlock"]{gap:.25rem!important}
 .st-key-watch_grid button{font-size:12px!important;white-space:normal!important;width:100%;padding:4px!important}
 [class*="st-key-pie_row_"] [data-testid="stHorizontalBlock"]{flex-wrap:nowrap!important;gap:4px!important}
 [class*="st-key-pie_row_"] [data-testid="stColumn"]{min-width:0!important;width:calc(33.33% - 3px)!important;flex:1 1 0!important}
 [class*="st-key-pie_row_"] p{font-size:11px!important}
 .mvp-photo img{height:85px!important}
}
'''
NAV='''<script>
try{
 const w=window.parent,d=w.document;
 if(!w.__fgmAutoNav){
  w.__fgmAutoNav=true;
  d.addEventListener('click',e=>{
   if(!e.target.closest('[data-testid="stSidebar"] [data-testid="stRadioOption"]'))return;
   w.setTimeout(()=>{
    const close=d.querySelector('[data-testid="stSidebarCollapseButton"] button')||d.querySelector('[data-testid="stSidebar"] button[aria-label="Collapse sidebar"]');
    if(close)close.click();
   },180);
  },true);
 }
}catch(e){}
</script>'''

def render_compact_ui():
    st.markdown('<style>'+CSS+'</style>',unsafe_allow_html=True)
    components.html(NAV,height=0)
