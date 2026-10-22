"""Responsive density and auto-collapsing navigation shared by both entry URLs."""
import streamlit as st
import streamlit.components.v1 as components
CSS='''
/* Keep the sidebar toggle, remove platform promotion and overflow actions. */
[data-testid="stToolbarActions"],[data-testid="stMainMenu"],[data-testid="stAppDeployButton"],[class*="viewerBadge"],[class*="viewer-badge"],[data-testid="stAppViewerBadge"],footer{display:none!important}

/* Large, visible navigation targets; preserve native widget behaviour. */
[data-testid="stExpandSidebarButton"],[data-testid="stCollapseSidebarButton"],[data-testid="stSidebarCollapseButton"] button,[data-testid="stSidebarCollapsedControl"] button,button[aria-label="Expand sidebar"],button[aria-label="Collapse sidebar"]{min-width:44px!important;min-height:44px!important;padding:8px!important}
[data-testid="stSelectbox"] button[aria-haspopup],[data-testid="stMultiSelect"] button[aria-haspopup]{min-width:40px!important;min-height:40px!important}
[data-baseweb="select"] svg{min-width:22px;min-height:22px}
[data-baseweb="select"] [role="button"]{min-width:32px;min-height:32px}
[data-testid="stExpander"] summary{min-height:44px!important;cursor:pointer}
[data-testid="stMain"] h1{font-weight:750!important;letter-spacing:-.02em}
[data-testid="stMain"] h2,[data-testid="stMain"] h3{font-weight:700!important}
[data-testid="stCaptionContainer"]{color:var(--fgm-muted)!important}
[data-testid="stCaptionContainer"] p{font-size:12px!important;line-height:1.5!important;color:inherit!important}
[data-testid="stMetricValue"]{font-weight:700!important;font-variant-numeric:tabular-nums}


.mobile-stat-heading img,.mobile-stat-avatar{width:32px;height:28px;object-fit:contain;flex:0 0 32px}
.planner-mobile-player{display:flex;align-items:center;gap:10px;margin-bottom:8px}
.planner-mobile-player img{width:60px!important;height:58px!important;max-height:58px!important;object-fit:contain;flex:0 0 60px}
.planner-mobile-player>div{min-width:0;display:flex;flex-direction:column;gap:5px;line-height:1.45}
.planner-mobile-player b{font-size:14px;overflow-wrap:anywhere}.planner-mobile-player span{font-size:12px}.planner-mobile-player small{font-size:11px}
.mobile-player-rows{width:100%;min-width:0}
.mobile-stat-player{padding:6px 0;border-bottom:1px solid #84939b55;min-width:0}
.mobile-stat-heading{display:flex;align-items:center;justify-content:space-between;gap:6px;font-size:12px;line-height:1.4}
.mobile-stat-heading b{flex:1;min-width:0;overflow-wrap:anywhere}.mobile-stat-heading span{white-space:nowrap;font-size:11px}
.mobile-stat-values{display:grid;grid-template-columns:repeat(9,minmax(0,1fr));gap:2px;margin-top:3px}
.mobile-stat-values>span{display:flex;flex-direction:column;min-width:0;text-align:center}
.mobile-stat-values small{font-size:8px;opacity:.8}.mobile-stat-values b{font-size:clamp(8px,2.4vw,11px);font-variant-numeric:tabular-nums;overflow-wrap:anywhere}
.mobile-rank-list{max-height:340px;overflow-y:auto;width:100%}
.mobile-rank-list>div{display:grid;grid-template-columns:30px minmax(0,1fr) 65px;gap:5px;padding:5px 0;border-bottom:1px solid #84939b44;font-size:12px}
.mobile-rank-list>div>span{overflow-wrap:anywhere}

.st-key-background_sync{display:none!important}
[data-testid="stLayoutWrapper"]:has(> .st-key-background_sync){display:none!important}

/* Stick the outer layout wrapper so its containing block spans the entire page. */
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > [data-testid="stLayoutWrapper"]:has(.st-key-current_feature){
 position:sticky!important;top:2.875rem;z-index:990;
}
.st-key-current_feature [data-testid="stHorizontalBlock"]{flex-wrap:nowrap!important;align-items:center;gap:6px!important}
.st-key-current_feature [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child{flex:1 1 0!important;min-width:0!important}
.st-key-current_feature [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child{flex:0 0 38px!important;min-width:38px!important;width:38px!important}
.st-key-current_feature button{min-height:32px!important;height:32px!important;width:36px!important;padding:0!important}
.st-key-current_feature{
 background:var(--fgm-feature-bg,#0b1020)!important;color:var(--fgm-feature-fg,#edf2f7)!important;
 border-bottom:1px solid var(--fgm-feature-border,#384152);padding:4px 8px!important;
 border-radius:0 0 8px 8px;min-height:42px!important;height:auto!important;box-sizing:border-box;flex-shrink:0!important;
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
.st-key-watch_grid > [data-testid="stLayoutWrapper"]:has(> [class*="st-key-watch_card_"]){height:190px!important;min-height:190px!important}
.st-key-watch_grid [class*="st-key-watch_card_"]{height:190px!important;min-height:190px!important;flex:0 0 190px!important;box-sizing:border-box;overflow:hidden}
.st-key-watch_grid [class*="st-key-watch_card_"] [data-testid="stMarkdownContainer"] p{height:34px;overflow:hidden}
.st-key-watch_grid [class*="st-key-watch_card_"] [data-testid="stCaptionContainer"]{height:20px;overflow:hidden}
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
 .st-key-watch_grid > [data-testid="stLayoutWrapper"]:has(> [class*="st-key-watch_card_"]){height:150px!important;min-height:150px!important}
 .st-key-watch_grid [class*="st-key-watch_card_"]{height:150px!important;min-height:150px!important;flex:0 0 150px!important;box-sizing:border-box;overflow:hidden}
 .st-key-watch_grid [class*="st-key-watch_card_"] [data-testid="stMarkdownContainer"] p{height:34px!important;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
 .st-key-watch_grid [class*="st-key-watch_card_"] [data-testid="stCaptionContainer"]{height:24px!important;overflow:hidden}
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
[data-testid="stElementContainer"]:has(> .stMarkdown > div > [data-testid="stMarkdownContainer"] > style:only-child){display:none!important}
/* Compact full-width sidebar, with its two actions above the brand. */
[data-testid="stSidebarUserContent"]{padding:8px 12px!important}
[data-testid="stSidebarHeader"]{display:none!important}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"]{gap:5px!important}
.st-key-sidebar_actions [data-testid="stHorizontalBlock"]{display:flex!important;flex-wrap:nowrap!important;gap:6px!important}
.st-key-sidebar_actions [data-testid="stColumn"]{min-width:0!important;flex:1 1 0!important}
.st-key-sidebar_actions button{width:100%!important;min-height:38px!important;padding:5px!important}
.sidebar-brand{font-size:clamp(28px,9vw,40px);font-weight:800;line-height:1.2;letter-spacing:-.04em;white-space:nowrap;width:100%}
[data-testid="stSidebar"] [role="radiogroup"]{gap:4px!important;width:100%!important}
[data-testid="stSidebar"] [role="radiogroup"]>div{width:100%!important}
[data-testid="stSidebar"] label[data-testid="stRadioOption"]{box-sizing:border-box!important;min-height:36px!important;padding:6px 9px!important;width:100%!important}
[data-testid="stSidebar"] label[data-testid="stRadioOption"] p{font-size:14px!important;line-height:1.3!important}
[data-testid="stMainBlockContainer"]{padding-top:3rem!important}
[data-testid="stElementContainer"]:has(iframe[title^="google_drive_auth."]),[data-testid="stElementContainer"]:has(iframe[title^="browser_records."]){display:none!important}
.st-key-current_feature{margin-top:0!important}
.st-key-app_status_bar [data-testid="stButtonGroup"]{width:100%}
.st-key-app_status_bar [data-testid="stButtonGroup"] button{padding:4px 6px!important;min-height:32px!important;font-size:12px!important;transition:background .18s ease}
.st-key-watch_grid [class*="st-key-watch_card_"] [data-testid="stImage"],.st-key-watch_grid [class*="st-key-watch_card_"] [data-testid="stImage"] img{width:100%!important;max-width:100%!important;height:auto!important;max-height:68px!important;object-fit:contain!important}
.st-key-watch_grid [class*="st-key-watch_card_"] button{width:100%!important;min-height:26px!important;height:26px!important;padding:0 4px!important}

'''
NAV='''<script>
try{
 const w=window.parent,d=w.document;
 // Community Cloud renders its visitor attribution outside the app iframe.
 try{
  const shell=w.parent.document;
  const hideAttribution=()=>{
   // Cloud's mobile badge is icon-only until tapped, so text matching misses it.
   shell.querySelectorAll('[class*="viewerBadge"],[class*="viewer-badge"],[data-testid="app-viewer-badge"]').forEach(el=>el.style.setProperty('display','none','important'));
   shell.querySelectorAll('div,aside,a,button').forEach(el=>{
    const style=shell.defaultView.getComputedStyle(el),rect=el.getBoundingClientRect();
    if(style.position==='fixed'&&rect.width>0&&rect.width<=420&&rect.height>0&&rect.height<=180&&rect.bottom>=shell.defaultView.innerHeight-100&&rect.right>=shell.defaultView.innerWidth-120&&el.querySelector('svg,img')&&!el.querySelector('iframe')){
     el.style.setProperty('display','none','important');
    }
   });
   shell.querySelectorAll('a,span,p,footer').forEach(el=>{
    const label=(el.textContent||'').trim();
    if(label.length>160||!(/^(Created by|Hosted with Streamlit)/i.test(label)))return;
    const group=el.closest('footer')||el.parentElement;
    if(group&&(group.textContent||'').length<400)group.style.setProperty('display','none','important');
   });
  };
  hideAttribution();
  if(!w.__fgmCloudAttribution){w.__fgmCloudAttribution=new w.MutationObserver(hideAttribution);w.__fgmCloudAttribution.observe(shell.body,{childList:true,subtree:true});}
 }catch(e){}

 const install=()=>{
  d.querySelectorAll('[data-baseweb="popover"],[data-testid="stSelectboxVirtualDropdown"],[data-testid="stMultiSelectDropdown"]').forEach(pop=>{
   if(!pop.querySelector('[role="listbox"]')||pop.querySelector('[data-fgm-done]'))return;
   const done=d.createElement('button');done.type='button';done.textContent='完成選擇 · 收起';done.dataset.fgmDone='1';
   done.style.cssText='position:sticky;bottom:0;width:100%;min-height:44px;border:1px solid #8c9aa8;border-radius:6px;background:var(--fgm-feature-bg,#f7f8fa);color:var(--fgm-feature-fg,#202936);font-size:14px;z-index:2;cursor:pointer';
   done.onclick=()=>{const dismiss=pop.querySelector('button[aria-label="Dismiss"]');if(dismiss){dismiss.click();return;}const active=d.activeElement;active?.dispatchEvent(new w.KeyboardEvent('keydown',{key:'Escape',code:'Escape',bubbles:true}));active?.blur();d.body.dispatchEvent(new w.MouseEvent('mousedown',{bubbles:true}));};
   pop.appendChild(done);
  });
 };
 if(!w.__fgmSelectDone){w.__fgmSelectDone=new w.MutationObserver(install);w.__fgmSelectDone.observe(d.body,{childList:true,subtree:true});}install();
 if(!w.__fgmAutoNav){
  w.__fgmAutoNav=true;
  d.addEventListener('click',e=>{
   if(!e.target.closest('[data-testid="stSidebar"] [data-testid="stRadioOption"],.st-key-sidebar_close'))return;
   w.setTimeout(()=>{
    const close=d.querySelector('[data-testid="stCollapseSidebarButton"]')||d.querySelector('[data-testid="stSidebarCollapseButton"] button')||d.querySelector('[data-testid="stSidebar"] button[aria-label="Collapse sidebar"]');
    if(close)close.click();
   },180);
  },true);
 }
}catch(e){}
</script>'''

def render_compact_ui():
    theme=st.session_state.get('visual_theme','黑色鏡面')
    bg,fg,border={'簡約淺色':('#f7f8fa','#202936','#d5dce5'),'戰術板草圖':('#142b29','#f0eee3','#54736a')}.get(theme,('#0b1020','#edf2f7','#384152'))
    variables=f'.stApp{{--fgm-feature-bg:{bg};--fgm-feature-fg:{fg};--fgm-feature-border:{border};--fgm-muted:{'#526174' if theme=='簡約淺色' else '#b8c7d2'};}}'
    responsive=CSS.replace('@media(max-width:640px)','@media(max-width:100000px)') if st.session_state.get('device_view')=='手機版' else CSS
    st.markdown('<style>'+variables+responsive+'</style>',unsafe_allow_html=True)
    components.html(NAV,height=0)
