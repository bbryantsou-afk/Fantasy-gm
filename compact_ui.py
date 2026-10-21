"""Responsive density and auto-collapsing navigation shared by both entry URLs."""
import streamlit as st
import streamlit.components.v1 as components
CSS='''
/* Stick the outer layout wrapper so its containing block spans the entire page. */
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > [data-testid="stLayoutWrapper"]:has(.st-key-current_feature){
 position:sticky!important;top:2.875rem;z-index:990;
}
.st-key-current_feature{
 background:var(--fgm-feature-bg,#0b1020)!important;color:var(--fgm-feature-fg,#edf2f7)!important;
 border-bottom:1px solid var(--fgm-feature-border,#384152);padding:8px 12px!important;
 border-radius:0 0 8px 8px;
}
.st-key-current_feature p,.st-key-current_feature strong{
 background:transparent!important;color:inherit!important;margin:0!important;font-size:15px!important;line-height:1.4!important;
}

.st-key-app_status_bar [data-testid="stVerticalBlock"]{gap:2px!important}
.st-key-app_status_bar [data-testid="stHorizontalBlock"]{align-items:center;flex-wrap:nowrap!important;gap:8px!important}
.st-key-app_status_bar [data-testid="stColumn"]{min-width:0!important;flex:1 1 0!important}
.st-key-app_status_bar p{margin:0!important;font-size:12px!important;line-height:1.3!important}
.st-key-app_status_bar [data-testid="stRadio"]{margin:0!important}
.st-key-app_status_bar [role="radiogroup"]{gap:10px!important;flex-wrap:nowrap!important}

.st-key-watch_grid{display:grid!important;grid-template-columns:repeat(10,minmax(0,1fr));gap:6px!important;align-items:start}
.st-key-watch_grid>[data-testid="stLayoutWrapper"]{min-width:0}
.st-key-watch_grid [data-testid="stVerticalBlockBorderWrapper"]{padding:6px!important}
.st-key-watch_grid img{max-height:55px;object-fit:contain}
.st-key-watch_grid button{font-size:11px!important;padding:5px 8px!important;min-height:36px}
.st-key-watch_controls [data-baseweb="select"]>div{max-height:68px;overflow-y:auto}
.st-key-watch_grid [class*="st-key-watch_card_"] [data-testid="stVerticalBlock"]{gap:3px!important}
.st-key-watch_grid [class*="st-key-watch_card_"] p{font-size:11px!important;line-height:1.3!important;overflow-wrap:anywhere}
.st-key-watch_grid [class*="st-key-watch_detail_"],.st-key-watch_grid > [data-testid="stLayoutWrapper"]:has([class*="st-key-watch_detail_"]){grid-column:1/-1!important}
.st-key-watch_grid [class*="st-key-watch_detail_"] img{max-height:none}
@media(min-width:900px){.st-key-dashboard_controls [data-testid="stHorizontalBlock"],.st-key-watch_controls [data-testid="stHorizontalBlock"]{flex-wrap:nowrap!important;gap:12px!important}}
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
    theme=st.session_state.get('visual_theme','黑色鏡面')
    bg,fg,border={'簡約淺色':('#f7f8fa','#202936','#d5dce5'),'戰術板草圖':('#142b29','#f0eee3','#54736a')}.get(theme,('#0b1020','#edf2f7','#384152'))
    variables=f'.stApp{{--fgm-feature-bg:{bg};--fgm-feature-fg:{fg};--fgm-feature-border:{border};}}'
    st.markdown('<style>'+variables+CSS+'</style>',unsafe_allow_html=True)
    components.html(NAV,height=0)
