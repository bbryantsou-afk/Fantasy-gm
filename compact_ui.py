"""Responsive density and auto-collapsing navigation shared by both entry URLs."""
import streamlit as st
import streamlit.components.v1 as components
CSS='''

.mobile-player-rows{width:100%;min-width:0}
.mobile-stat-player{padding:6px 0;border-bottom:1px solid #84939b55;min-width:0}
.mobile-stat-heading{display:flex;justify-content:space-between;gap:6px;font-size:12px;line-height:1.4}
.mobile-stat-heading b{min-width:0;overflow-wrap:anywhere}.mobile-stat-heading span{white-space:nowrap;font-size:11px}
.mobile-stat-values{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:3px;margin-top:4px}
.mobile-stat-values>span{display:flex;flex-direction:column;min-width:0;text-align:center}
.mobile-stat-values small{font-size:9px;opacity:.8}.mobile-stat-values b{font-size:11px;font-variant-numeric:tabular-nums;overflow-wrap:anywhere}
.mobile-rank-list{max-height:340px;overflow-y:auto;width:100%}
.mobile-rank-list>div{display:grid;grid-template-columns:30px minmax(0,1fr) 65px;gap:5px;padding:5px 0;border-bottom:1px solid #84939b44;font-size:12px}
.mobile-rank-list>div>span{overflow-wrap:anywhere}

.st-key-background_sync{display:none!important}
[data-testid="stLayoutWrapper"]:has(> .st-key-background_sync){display:none!important}

/* Stick the outer layout wrapper so its containing block spans the entire page. */
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > [data-testid="stLayoutWrapper"]:has(.st-key-current_feature){
 position:sticky!important;top:2.875rem;z-index:990;
}
.st-key-current_feature{
 background:var(--fgm-feature-bg,#0b1020)!important;color:var(--fgm-feature-fg,#edf2f7)!important;
 border-bottom:1px solid var(--fgm-feature-border,#384152);padding:8px 12px!important;
 border-radius:0 0 8px 8px;min-height:38px!important;height:auto!important;box-sizing:border-box;flex-shrink:0!important;
}
.st-key-current_feature [data-testid="stElementContainer"],
.st-key-current_feature [data-testid="stMarkdown"],
.st-key-current_feature [data-testid="stMarkdown"] > div,
.st-key-current_feature [data-testid="stMarkdownContainer"]{
 height:auto!important;min-height:21px!important;flex-shrink:0!important;overflow:visible!important;
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

[class*="st-key-planner_plan_"]{padding:10px!important}
[class*="st-key-planner_plan_"] [data-testid="stVerticalBlock"]{gap:5px!important}
[class*="st-key-planner_plan_"] [data-testid="stMetric"]{padding:8px!important;min-height:85px!important;height:85px!important;box-sizing:border-box}
[class*="st-key-planner_plan_"] [data-testid="stMetricValue"]{font-size:24px!important}
[class*="st-key-planner_plan_"] [data-testid="stMetricLabel"] p{font-size:12px!important}
[class*="st-key-planner_plan_"] p{margin-bottom:0!important}
@media(min-width:900px){
 .st-key-planner_teams [data-testid="stHorizontalBlock"],.st-key-planner_period [data-testid="stHorizontalBlock"],.st-key-planner_candidates [data-testid="stHorizontalBlock"],
 [class*="st-key-planner_plan_"] > [data-testid="stHorizontalBlock"]{flex-wrap:nowrap!important;gap:10px!important}
}
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

 /* Keep related controls together instead of Streamlit's one-column stacking. */
 [data-testid="stMain"] [data-testid="stHorizontalBlock"]{flex-wrap:nowrap!important;gap:6px!important}
 [data-testid="stMain"] [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]{min-width:0!important;flex:1 1 0!important;width:auto!important}
 .st-key-dashboard_controls [data-testid="stHorizontalBlock"]{display:grid!important;grid-template-columns:repeat(2,minmax(0,1fr))}
 .st-key-watch_controls [data-testid="stHorizontalBlock"]{display:grid!important;grid-template-columns:repeat(2,minmax(0,1fr))}
 .st-key-watch_controls [data-testid="stColumn"]:last-child{grid-column:1/-1}
 [data-testid="stMain"] [data-baseweb="select"]{min-width:0!important;font-size:12px!important}
 [data-testid="stMain"] input{min-width:0!important;font-size:16px!important;padding:6px!important}
 [data-testid="stMain"] button{min-height:36px;padding:5px 8px!important}
 [data-testid="stMain"] [role="radiogroup"]{gap:5px!important;flex-wrap:wrap!important}
 [class*="st-key-planner_plan_"] > [data-testid="stHorizontalBlock"]{display:grid!important;grid-template-columns:repeat(6,minmax(0,1fr));align-items:center}
 [class*="st-key-planner_plan_"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]{grid-column:span 2}
 [class*="st-key-planner_plan_"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child{grid-column:span 1}
 [class*="st-key-planner_plan_"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(2){grid-column:span 5}
 [class*="st-key-planner_plan_"] img{max-height:52px!important;width:52px!important;object-fit:contain}
 [class*="st-key-planner_plan_"] [data-testid="stMetric"]{min-height:60px!important;height:60px!important;padding:5px!important}
 [class*="st-key-planner_plan_"] [data-testid="stMetricValue"]{font-size:20px!important}
 [data-testid="stMain"] [data-testid="stColumn"] [data-testid="stWidgetLabel"] p{font-size:12px!important}

 [data-testid="stMainBlockContainer"]{padding:3.3rem .65rem 2rem!important}
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
 .st-key-watch_grid{grid-template-columns:repeat(5,minmax(0,1fr));gap:4px!important}
 .st-key-watch_grid [class*="st-key-watch_card_"] p{font-size:9px!important;line-height:1.2!important;overflow-wrap:anywhere}
 .st-key-watch_grid [class*="st-key-watch_card_"] [data-testid="stCaptionContainer"] p{font-size:8px!important}
 .st-key-watch_grid [class*="st-key-watch_card_"]{padding:3px!important}
 .st-key-watch_grid img{max-height:40px;width:42px!important}
 .st-key-watch_grid [data-testid="stVerticalBlock"]{gap:.25rem!important}
 .st-key-watch_grid button{font-size:12px!important;white-space:normal!important;width:100%;padding:2px!important}
 [class*="st-key-pie_row_"] [data-testid="stHorizontalBlock"]{flex-wrap:nowrap!important;gap:4px!important}
 [class*="st-key-pie_row_"] [data-testid="stColumn"]{min-width:0!important;width:calc(20% - 3px)!important;flex:1 1 0!important}
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
    responsive=CSS.replace('@media(max-width:640px)','@media(max-width:100000px)') if st.session_state.get('device_view')=='手機版' else CSS
    st.markdown('<style>'+variables+responsive+'</style>',unsafe_allow_html=True)
    components.html(NAV,height=0)
