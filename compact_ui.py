"""Responsive density and auto-collapsing navigation shared by both entry URLs."""
import streamlit as st
import streamlit.components.v1 as components
CSS='''
.dashboard-big-score{padding:14px 10px;border:1px solid var(--fgm-feature-border,#46658d);border-radius:12px;text-align:center;background:var(--fgm-feature-bg,#1c2b44)}
.dashboard-score-numbers{display:flex;align-items:center;justify-content:center;gap:24px}
.dashboard-score-numbers strong{font-size:52px!important;font-weight:800;line-height:1;font-variant-numeric:tabular-nums}
.dashboard-score-numbers>span{font-size:22px;opacity:.6}
.dashboard-score-opponent{font-size:13px;line-height:1.4;margin-top:8px;overflow-wrap:anywhere}

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
.planner-card-overview{display:grid;grid-template-columns:minmax(180px,2.5fr) repeat(3,minmax(0,1fr));gap:8px;align-items:start;margin-bottom:8px}
.planner-card-overview.planner-card-mobile{grid-template-columns:repeat(3,minmax(0,1fr))}
.planner-card-mobile .planner-mobile-player{grid-column:1/-1}
.planner-card-overview .planner-mobile-player{margin:0;min-width:0;height:auto;align-items:flex-start}
.planner-card-overview .planner-mobile-player>div{flex:1;min-width:0}
.planner-card-overview .planner-mobile-player :is(b,span,small){display:block;height:auto!important;min-height:0;line-height:1.5!important;white-space:normal;overflow-wrap:anywhere;flex-shrink:0}
.planner-card-stat{display:flex;flex-direction:column;gap:4px;min-width:0;padding:7px 5px;border:1px solid var(--fgm-feature-border,#84939b55);border-radius:8px}
.planner-card-stat span{font-size:11px;line-height:1.4;white-space:normal}
.planner-card-stat b{font-size:22px;line-height:1.3;font-variant-numeric:tabular-nums;overflow-wrap:anywhere}
.planner-mobile-player{display:flex;align-items:center;gap:10px;margin-bottom:8px}
.planner-mobile-player img{width:60px!important;height:58px!important;max-height:58px!important;object-fit:contain;flex:0 0 60px}
.planner-mobile-player>div{min-width:0;display:flex;flex-direction:column;gap:5px;line-height:1.45}
.planner-mobile-player b{font-size:14px;overflow-wrap:anywhere}.planner-mobile-player span{font-size:12px}.planner-mobile-player small{font-size:11px}
.mobile-player-rows{width:100%;min-width:0}
.mobile-stat-player{padding:6px 0;border-bottom:1px solid #84939b55;min-width:0}
.mobile-stat-heading{display:flex;align-items:center;justify-content:space-between;gap:6px;font-size:12px;line-height:1.4}
.mobile-stat-heading b{flex:1;min-width:0;overflow-wrap:anywhere}.mobile-stat-heading span{white-space:nowrap;font-size:11px}
.mobile-stat-position{font-size:10px!important;font-weight:500;opacity:.8;margin-left:4px;white-space:nowrap}
.mobile-stat-values{display:grid;grid-template-columns:repeat(9,minmax(0,1fr));gap:2px;margin-top:3px}
.mobile-stat-values>span{display:flex;flex-direction:column;min-width:0;text-align:center}
.mobile-stat-values small{font-size:8px;opacity:.8}.mobile-stat-values b{font-size:clamp(8px,2.4vw,11px);font-variant-numeric:tabular-nums;overflow-wrap:anywhere}
.mobile-rank-list{max-height:576px;overflow-y:auto;width:100%}
.mobile-rank-list>div{height:36px;box-sizing:border-box;align-items:center;overflow:hidden}
.mobile-rank-list>div:first-child{position:sticky;top:0;background:var(--fgm-feature-bg,#f6f7f9);z-index:1}
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
.st-key-watch_grid [class*="st-key-watch_card_"] button{font-size:11px!important;padding:5px 8px!important;min-height:36px}
.st-key-watch_controls [data-baseweb="select"]>div{max-height:68px;overflow-y:auto}
.st-key-watch_grid [class*="st-key-watch_card_"] [data-testid="stVerticalBlock"]{gap:3px!important}
.st-key-watch_grid [class*="st-key-watch_card_"] p{font-size:11px!important;line-height:1.3!important;overflow-wrap:anywhere}
.st-key-watch_grid [class*="st-key-watch_detail_"],.st-key-watch_grid > [data-testid="stLayoutWrapper"]:has([class*="st-key-watch_detail_"]){grid-column:1/-1!important}
.st-key-watch_grid [class*="st-key-watch_detail_"] img{max-height:none}
.st-key-dashboard_controls [data-testid="stColumn"]{min-width:0!important;width:100%!important;max-width:100%!important;box-sizing:border-box!important}
.st-key-dashboard_controls [data-testid="stHorizontalBlock"]{display:grid!important;grid-template-columns:minmax(110px,.8fr) minmax(160px,1.6fr) minmax(170px,1.1fr) minmax(130px,1fr);gap:16px!important;align-items:start!important}
.st-key-dashboard_controls [data-testid="stElementContainer"]{min-width:0!important;max-width:100%!important}
.st-key-dashboard_controls [data-testid="stDateInput"] input{min-width:0!important;width:100%!important}
.st-key-dashboard_controls [data-testid="stDateInput"],.st-key-dashboard_controls [data-baseweb="input"]{min-width:0!important;max-width:100%!important;width:100%!important}
.st-key-dashboard_controls [role="radiogroup"]{flex-wrap:wrap!important}
@media(min-width:641px) and (max-width:1100px){.st-key-dashboard_controls [data-testid="stHorizontalBlock"]{display:grid!important;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px!important}.st-key-dashboard_controls [data-testid="stColumn"]{width:100%!important}}
@media(min-width:900px){.st-key-dashboard_controls [data-testid="stHorizontalBlock"],.st-key-watch_controls [data-testid="stHorizontalBlock"]{flex-wrap:nowrap!important;gap:12px!important}}
@media(max-width:640px){
 .sched-calendar{max-height:none!important;height:auto!important;overflow:visible!important}
 .mobile-rank-list{max-height:576px!important;overflow-y:auto!important}


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
 .st-key-watch_grid{grid-template-columns:repeat(4,minmax(0,1fr));gap:4px!important}
 .st-key-watch_grid > [data-testid="stLayoutWrapper"]:has(> [class*="st-key-watch_card_"]){height:170px!important;min-height:170px!important}
 .st-key-watch_grid [class*="st-key-watch_card_"]{height:170px!important;min-height:170px!important;flex:0 0 170px!important;box-sizing:border-box;overflow:hidden}
 .st-key-watch_grid [class*="st-key-watch_card_"] [data-testid="stMarkdownContainer"] p{height:34px!important;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
 .st-key-watch_grid [class*="st-key-watch_card_"] [data-testid="stCaptionContainer"]{height:24px!important;overflow:hidden}
 .st-key-watch_grid [class*="st-key-watch_card_"] p{font-size:9px!important;line-height:1.2!important;overflow-wrap:anywhere}
 .st-key-watch_grid [class*="st-key-watch_card_"] [data-testid="stCaptionContainer"] p{font-size:8px!important}
 .st-key-watch_grid [class*="st-key-watch_card_"]{padding:3px!important}
 .st-key-watch_grid img{max-height:40px;width:42px!important}
 .st-key-watch_grid [data-testid="stVerticalBlock"]{gap:.25rem!important}
 .st-key-watch_grid [class*="st-key-watch_card_"] button{font-size:12px!important;white-space:normal!important;width:100%;padding:2px!important}
 [class*="st-key-pie_row_"] [data-testid="stHorizontalBlock"]{flex-wrap:nowrap!important;gap:4px!important}
 [class*="st-key-pie_row_"] [data-testid="stColumn"]{min-width:0!important;width:calc(20% - 3px)!important;flex:1 1 0!important}
 [class*="st-key-pie_row_"] p{font-size:11px!important}

}
[data-testid="stElementContainer"]:has(> .stMarkdown > div > [data-testid="stMarkdownContainer"] > style:only-child){display:none!important}
[data-testid="stSidebar"] .st-key-main_navigation,[data-testid="stSidebar"] [data-testid="stRadio"]{width:100%!important;max-width:none!important}
[data-testid="stSidebar"][aria-expanded="true"]{width:225px!important;min-width:225px!important;max-width:225px!important;flex-basis:225px!important}
[data-testid="stSidebar"][aria-expanded="false"]{width:0!important;min-width:0!important;max-width:0!important;flex-basis:0!important;margin-left:0!important;margin-right:0!important;padding:0!important;border:0!important}
[data-testid="stAppViewContainer"]:has([data-testid="stSidebar"][aria-expanded="false"]) [data-testid="stMain"]{margin-left:0!important;width:100%!important;max-width:100%!important;flex:1 1 100%!important}
.st-key-current_feature p,.st-key-current_feature strong{font-size:28px!important;font-weight:800!important;line-height:1.2!important;letter-spacing:-.025em}
.st-key-current_feature{min-height:48px!important;padding:7px 8px!important}
/* Compact full-width sidebar, with its two actions above the brand. */
[data-testid="stSidebarUserContent"]{padding:8px 12px!important}
[data-testid="stSidebarHeader"]{display:none!important}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"]{gap:5px!important}
.st-key-sidebar_actions [data-testid="stHorizontalBlock"]{display:flex!important;flex-wrap:nowrap!important;gap:6px!important}
.st-key-sidebar_actions [data-testid="stColumn"]{min-width:0!important;flex:1 1 0!important}
.st-key-sidebar_actions button{width:100%!important;min-height:38px!important;padding:5px!important}
.st-key-sidebar_identity{height:auto!important;min-height:64px!important;flex-shrink:0!important}
.st-key-sidebar_identity [data-testid="stElementContainer"],.st-key-sidebar_identity [data-testid="stMarkdown"]{height:auto!important;flex-shrink:0!important}
.sidebar-identity{display:flex;flex-direction:column;gap:9px;padding:3px 0 5px}
.sidebar-account{font-size:12px;line-height:1.5;overflow-wrap:anywhere}
.st-key-sidebar_actions button p{font-size:11px!important;white-space:nowrap!important;line-height:1.3!important}
.st-key-mobile_sync_shortcut button p{color:#7200d2!important;font-size:24px!important;font-weight:900!important;font-family:system-ui,sans-serif!important}
.st-key-refresh_current_page button p{font-size:20px!important}
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

/* Equal action boxes and explicit sidebar direction. */
.st-key-sidebar_actions button{height:40px!important;min-height:40px!important;max-height:40px!important;box-sizing:border-box!important;display:flex!important;align-items:center!important;justify-content:center!important}
.st-key-sidebar_close button p{font-size:20px!important;font-weight:700!important}
[data-testid="stExpandSidebarButton"] svg,[data-testid="stSidebarCollapsedControl"] button svg,button[aria-label="Expand sidebar"] svg{display:block!important;width:24px!important;height:24px!important}
[data-testid="stExpandSidebarButton"]::after,[data-testid="stSidebarCollapsedControl"] button::after,button[aria-label="Expand sidebar"]::after{content:none!important;display:none!important}
.watch-card-content{display:grid;grid-template-rows:60px 34px 24px;gap:3px;text-align:center;min-width:0}
.watch-portrait{height:60px;display:flex;align-items:center;justify-content:center;overflow:hidden}
.st-key-watch_grid .watch-portrait img{width:100%!important;height:60px!important;max-height:60px!important;object-fit:contain}
.watch-name{font-size:11px;font-weight:700;line-height:17px;overflow:hidden;overflow-wrap:anywhere}
.watch-meta,.watch-availability{font-size:9px;line-height:12px;overflow:hidden;overflow-wrap:anywhere}
.st-key-watch_grid [class*="st-key-watch_card_"] button{display:flex!important;align-items:center!important;justify-content:center!important}
.st-key-watch_grid [class*="st-key-watch_card_"] button [data-testid="stMarkdownContainer"] p{height:auto!important;min-height:0!important;display:block!important;margin:0!important;line-height:20px!important;overflow:visible!important}

.st-key-watch_grid [class*="st-key-watch_detail_"]{height:auto!important;overflow:visible!important;position:relative}
.st-key-watch_grid [class*="st-key-watch_detail_"] button{min-height:40px!important;height:auto!important;pointer-events:auto!important;white-space:normal!important;font-size:14px!important;padding:6px 10px!important}
.st-key-watch_grid .watch-detail-portrait img{width:100%!important;max-width:260px!important;height:auto!important;max-height:190px!important;object-fit:contain}
.watch-detail-portrait{width:100%;text-align:center}
.watch-detail-stats{display:block;width:100%;white-space:nowrap;overflow-x:auto;font-size:11px;line-height:1.8;padding:6px 0;font-variant-numeric:tabular-nums}

/* Match the actual outer boxes, including theme borders and label wrappers. */
.stApp [data-testid="stSidebar"] .st-key-sidebar_actions [data-testid="stHorizontalBlock"]{display:grid!important;grid-template-columns:repeat(3,minmax(0,1fr))!important;gap:6px!important;align-items:start!important}
.stApp [data-testid="stSidebar"] .st-key-sidebar_actions [data-testid="stColumn"]{width:100%!important;min-width:0!important;max-width:none!important}
.stApp [data-testid="stSidebar"] .st-key-sidebar_actions button{width:100%!important;height:44px!important;min-height:44px!important;max-height:44px!important;margin:0!important;padding:0!important;border-width:1.5px!important;box-sizing:border-box!important;display:flex!important;align-items:center!important;justify-content:center!important}
.stApp [data-testid="stSidebar"] .st-key-sidebar_actions button [data-testid="stMarkdownContainer"]{display:flex!important;align-items:center!important;justify-content:center!important;height:24px!important;min-height:0!important;padding:0!important;margin:0!important}
.stApp [data-testid="stSidebar"] .st-key-sidebar_actions button p{height:24px!important;min-height:0!important;line-height:24px!important;margin:0!important;padding:0!important;font-size:22px!important;display:block!important}

button[data-testid="stExpandSidebarButton"],[data-testid="stExpandSidebarButton"] button,[data-testid="stSidebarCollapsedControl"] button,button[aria-label="Expand sidebar"]{width:44px!important;min-width:44px!important;max-width:44px!important;height:44px!important;min-height:44px!important;max-height:44px!important;padding:0!important;display:flex!important;align-items:center!important;justify-content:center!important;border-radius:10px!important;box-sizing:border-box!important}
.st-key-sidebar_close button [data-testid="stIconMaterial"]{font-size:24px!important;line-height:24px!important}

.stApp .st-key-sidebar_close button{gap:0!important}
.stApp .st-key-sidebar_close button [data-testid="stMarkdownContainer"]{display:flex!important;width:100%!important;align-items:center!important;justify-content:center!important}
.stApp .st-key-sidebar_close button [data-testid="stIconMaterial"]{display:flex!important;align-items:center!important;justify-content:center!important;margin:0!important;width:24px!important;height:24px!important;padding:0!important}
.stApp .st-key-app_status_bar [data-testid="stColumn"]{display:flex!important;align-items:center!important;justify-content:center!important;min-height:42px!important}
.stApp .st-key-app_status_bar [data-testid="stColumn"] > div{width:100%!important}
.stApp .st-key-app_status_bar :is(p,[data-testid="stCaptionContainer"]){margin:0!important;line-height:1.35!important}
.stApp .st-key-app_status_bar [data-testid="stMarkdown"]{display:flex!important;align-items:center!important;min-height:36px!important}
.stApp .mvp-body{align-items:stretch!important;min-height:170px}
.stApp .mvp-photo{position:relative!important;flex:0 0 35%!important;max-width:none!important;min-height:170px!important;align-self:stretch!important}
.stApp .mvp-photo img{position:static!important;width:100%!important;height:170px!important;max-height:170px!important;object-fit:contain!important;object-position:center bottom!important;border-radius:8px!important}

button:has(>[data-fgm-expand-emoji])>*:not([data-fgm-expand-emoji]){display:none!important}
button>[data-fgm-expand-emoji]{display:flex!important;align-items:center;justify-content:center;width:100%;font-size:22px;line-height:1;margin:0;padding:0}

.mobile-stat-player{display:grid;grid-template-columns:72px minmax(0,1fr);grid-template-rows:auto auto;column-gap:5px;row-gap:2px;padding:4px 0!important;align-items:center}
.mobile-stat-photo{grid-column:1;grid-row:1/3;align-self:stretch;display:flex;align-items:center;justify-content:center;min-height:64px;overflow:hidden}
.mobile-stat-photo img,.mobile-stat-photo .mobile-stat-avatar{width:72px!important;height:100%!important;min-height:64px;max-height:82px;object-fit:cover;object-position:center top}
.mobile-stat-player .mobile-stat-heading{grid-column:2;grid-row:1;gap:3px;font-size:11px}
.mobile-stat-player .mobile-stat-heading>span{font-size:9px}
.mobile-stat-player .mobile-stat-values{grid-column:2;grid-row:2;gap:0;margin-top:0}
.mobile-stat-player .mobile-stat-values small{font-size:7px;line-height:1.2}
.mobile-stat-player .mobile-stat-values b{font-size:clamp(7px,2vw,10px);line-height:1.25;letter-spacing:-.3px}

/* One continuous segmented switch; label wrappers must not stretch buttons. */
.stApp .st-key-app_status_bar [data-testid="stButtonGroup"]{display:flex!important;gap:0!important;padding:3px!important;border:1px solid var(--fgm-feature-border)!important;border-radius:11px!important;background:var(--fgm-feature-bg)!important;box-sizing:border-box!important;min-width:0!important}
.stApp .st-key-app_status_bar [data-testid="stButtonGroup"] button{flex:1 1 0!important;min-width:0!important;width:50%!important;height:32px!important;min-height:32px!important;max-height:32px!important;margin:0!important;padding:0 5px!important;border:0!important;border-radius:8px!important;box-shadow:none!important;display:flex!important;justify-content:center!important;align-items:center!important;white-space:nowrap!important}
.stApp .st-key-app_status_bar [data-testid="stButtonGroup"] button [data-testid="stMarkdownContainer"]{display:block!important;min-height:0!important;height:auto!important;margin:0!important;padding:0!important}
.stApp .st-key-app_status_bar [data-testid="stButtonGroup"] button p{font-size:12px!important;line-height:20px!important;white-space:nowrap!important;margin:0!important;padding:0!important}
.stApp .st-key-app_status_bar [data-testid="stButtonGroup"] button[aria-pressed="false"]{background:transparent!important}
.stApp .st-key-app_status_bar [data-testid="stButtonGroup"] button[aria-pressed="true"]{background:#2f8475!important;color:#fff!important}
.stApp .st-key-app_status_bar [data-testid="stButtonGroup"] button[aria-pressed="true"] :is(p,span){color:#fff!important;background:transparent!important}

/* Plan cards grow with content; native layout items cannot shrink over neighbours. */
.stApp [class*="st-key-planner_plan_"]{height:auto!important;min-height:0!important;overflow:visible!important}
.stApp [class*="st-key-planner_plan_"] [data-testid="stVerticalBlock"]{gap:10px!important;height:auto!important;min-height:0!important}
.stApp [class*="st-key-planner_plan_"] :is([data-testid="stElementContainer"],[data-testid="stLayoutWrapper"],[data-testid="stMarkdown"]){height:auto!important;min-height:0!important;flex-shrink:0!important;position:relative!important}
.planner-card-overview{width:100%;box-sizing:border-box;align-items:stretch!important;gap:10px!important;margin:0!important;min-width:0}
.planner-card-overview>*{box-sizing:border-box;min-width:0;max-width:100%}
.planner-card-stat{height:auto!important;min-height:68px;justify-content:center;overflow-wrap:anywhere}
.planner-card-stat :is(span,b){margin:0!important;white-space:normal!important;overflow-wrap:anywhere}
.planner-plan-insights{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;width:100%;box-sizing:border-box;padding:2px 0;clear:both}
.planner-plan-insights>div{display:flex;flex-direction:column;gap:4px;padding:8px;min-width:0;border:1px solid var(--fgm-feature-border);border-radius:8px;box-sizing:border-box}
.planner-plan-insights :is(span,b){display:block;position:static!important;margin:0!important;line-height:1.5!important;white-space:normal!important;overflow-wrap:anywhere;font-size:12px}
.planner-plan-insights span{font-size:11px;color:var(--fgm-muted)}
@media(max-width:760px){.planner-card-overview{grid-template-columns:repeat(3,minmax(0,1fr))!important}.planner-card-overview .planner-mobile-player{grid-column:1/-1}.planner-card-stat b{font-size:19px}}
@media(max-width:350px){.planner-plan-insights{grid-template-columns:minmax(0,1fr)}.planner-card-overview{gap:5px!important}.planner-card-stat{padding:6px 3px}.planner-card-stat span{font-size:10px}}

@media(max-width:600px){
.stApp .st-key-app_status_bar [data-testid="stHorizontalBlock"]{display:grid!important;grid-template-columns:minmax(0,1fr) minmax(110px,1.1fr) minmax(50px,.5fr)!important;gap:5px!important}
.stApp .st-key-app_status_bar [data-testid="stColumn"]{width:100%!important;max-width:100%!important;min-height:32px!important;box-sizing:border-box!important}
.stApp .st-key-app_status_bar [data-testid="stMarkdown"]{min-height:30px!important;overflow-wrap:anywhere}
}

html,body{max-width:100%;overflow-x:clip}
[data-testid="stAppViewContainer"],[data-testid="stMain"],[data-testid="stMainBlockContainer"]{min-width:0!important;max-width:100%!important;box-sizing:border-box!important}
[data-testid="stSidebar"] [data-testid="stRadioOption"]{transition:none!important;animation:none!important;white-space:normal}
@media(max-width:600px){
.stApp :is(input,textarea,select){font-size:16px!important}
[data-testid="stMainBlockContainer"]{padding-left:12px!important;padding-right:12px!important}
[data-testid="stDataFrame"],[data-testid="stTable"]{max-width:100%!important;min-width:0!important;overflow-x:auto}
}

/* Readable single-row player stats: percentages get extra width. */
.mobile-stat-player{grid-template-columns:64px minmax(0,1fr);column-gap:5px}
.mobile-stat-photo img,.mobile-stat-photo .mobile-stat-avatar{width:64px!important}
.mobile-stat-player .mobile-stat-values{grid-template-columns:1.35fr 1.35fr repeat(7,minmax(0,1fr));column-gap:3px;align-items:start}
.mobile-stat-player .mobile-stat-values small{font-size:9px!important;line-height:1.4!important;white-space:nowrap}
.mobile-stat-player .mobile-stat-values b{font-size:clamp(11px,2.9vw,13px)!important;line-height:1.5!important;letter-spacing:-.2px;white-space:nowrap;overflow-wrap:normal}
.mobile-stat-player .mobile-stat-heading{font-size:12px!important}

/* A single flow box owns the complete plan summary height. */
.plan-summary{display:flex;flex-direction:column;gap:12px;min-width:0;width:100%;height:auto;box-sizing:border-box;isolation:isolate}
.plan-summary *{box-sizing:border-box}
.plan-top{display:grid;grid-template-columns:minmax(180px,2fr) repeat(3,minmax(0,1fr));gap:8px;align-items:stretch}
.plan-person{display:flex;align-items:flex-start;gap:8px;min-width:0}
.plan-person img{width:60px;height:64px;object-fit:contain;flex:0 0 60px}
.plan-person>div{display:flex;flex-direction:column;gap:4px;min-width:0}
.plan-person :is(b,span,small){display:block;line-height:1.45;overflow-wrap:anywhere;white-space:normal;margin:0}
.plan-person b{font-size:14px}.plan-person span{font-size:12px}.plan-person small{font-size:11px}
.plan-number{display:flex;flex-direction:column;justify-content:center;gap:4px;min-width:0;padding:8px;border:1px solid var(--fgm-feature-border);border-radius:8px}
.plan-number span{font-size:11px;line-height:1.4;overflow-wrap:anywhere}.plan-number b{font-size:22px;line-height:1.3;overflow-wrap:anywhere;font-variant-numeric:tabular-nums}
.plan-insights{display:flex;flex-wrap:wrap;gap:8px;clear:both}
.plan-insights>div{flex:1 1 120px;min-width:0;padding:8px;border:1px solid var(--fgm-feature-border);border-radius:8px;display:flex;flex-direction:column;gap:4px}
.plan-insights span{font-size:11px;line-height:1.4;color:var(--fgm-muted)}.plan-insights b{font-size:12px;line-height:1.5;overflow-wrap:anywhere}
@media(max-width:760px){.plan-top{grid-template-columns:repeat(3,minmax(0,1fr))}.plan-person{grid-column:1/-1}}
/* Keep the feature title and expand control on the same horizontal bar. */
[data-testid="stSidebarCollapsedControl"],[data-testid="stExpandSidebarButton"]{position:fixed!important;top:calc(3rem + env(safe-area-inset-top,0px))!important;left:12px!important;z-index:100002!important}
[data-testid="stAppViewContainer"]:has([data-testid="stSidebar"][aria-expanded="false"]) .st-key-current_feature{padding-left:58px!important;display:flex!important;flex-direction:row!important;align-items:center!important;justify-content:flex-start!important;min-height:48px!important}
.st-key-current_feature p,.st-key-current_feature strong{white-space:nowrap!important;font-size:26px!important}
.stApp .st-key-app_status_bar [data-testid="stColumn"]{min-height:36px!important}
.stApp .st-key-app_status_bar [data-testid="stMarkdown"]{min-height:32px!important}

@media(max-width:600px){
[data-testid="stMainBlockContainer"]{padding-top:calc(3rem + env(safe-area-inset-top,0px))!important}
.st-key-current_feature{top:calc(2.875rem + env(safe-area-inset-top,0px))!important}
[data-testid="stSidebarUserContent"]{padding-top:calc(8px + env(safe-area-inset-top,0px))!important}
}

/* Minimal menu glyph; keep a full touch target without a decorative frame. */
.stApp [data-testid="stSidebar"] .st-key-sidebar_actions .st-key-sidebar_close button,.stApp button:has(>[data-fgm-expand-emoji]),button[aria-label="Expand sidebar"]:has(>[data-fgm-expand-emoji]){border:0!important;background:transparent!important;box-shadow:none!important;border-radius:8px!important;color:var(--fgm-feature-fg)!important}
.stApp .st-key-sidebar_close button p,button>[data-fgm-expand-emoji]{font-family:Arial,sans-serif!important;font-weight:400!important;font-size:26px!important;line-height:1!important}

'''
NAV='''<script>
try{
 const w=window.parent,d=w.document;
 const setViewport=doc=>{
  let meta=doc.querySelector('meta[name="viewport"]');
  if(!meta){meta=doc.createElement('meta');meta.name='viewport';doc.head.appendChild(meta);}
  const value='width=device-width, initial-scale=1, viewport-fit=cover';
  if(meta.content!==value)meta.content=value;
 };
 setViewport(d);try{setViewport(w.parent.document);}catch(e){}

 // Hide only explicit badge leaves. Never infer shell containers from text or position.
 try{
  const shell=w.parent.document;
  if(w.__fgmCloudAttribution){w.__fgmCloudAttribution.disconnect();delete w.__fgmCloudAttribution;}
  const hideAttribution=()=>{
   shell.querySelectorAll('[data-testid="app-viewer-badge"],[data-testid="stAppViewerBadge"],[class*="viewerBadge"],[class*="viewer-badge"]').forEach(el=>{
    if(el===shell.body||el===shell.documentElement||el.querySelector('iframe,main,[data-testid="stAppViewContainer"],[data-testid="stMain"]'))return;
    el.style.setProperty('display','none','important');
   });
  };
  hideAttribution();
  w.__fgmCloudAttribution=new w.MutationObserver(hideAttribution);
  w.__fgmCloudAttribution.observe(shell.body,{childList:true,subtree:true});
 }catch(e){}

 const install=()=>{
  d.querySelectorAll('button[data-testid="stExpandSidebarButton"],[data-testid="stExpandSidebarButton"] button,[data-testid="stSidebarCollapsedControl"] button,button[aria-label="Expand sidebar"]').forEach(button=>{
   let icon=button.querySelector('[data-fgm-expand-emoji]');
   if(!icon){icon=d.createElement('span');icon.dataset.fgmExpandEmoji='1';button.appendChild(icon);}
   if(icon.textContent!=='☰')icon.textContent='☰';
  });
  d.querySelectorAll('[data-baseweb="popover"],[data-testid="stSelectboxVirtualDropdown"],[data-testid="stMultiSelectDropdown"]').forEach(pop=>{
   if(!pop.querySelector('[role="listbox"]')||pop.querySelector('[data-fgm-done]'))return;
   const done=d.createElement('button');done.type='button';done.textContent='完成選擇 · 收起';done.dataset.fgmDone='1';
   done.style.cssText='position:sticky;bottom:0;width:100%;min-height:44px;border:1px solid #8c9aa8;border-radius:6px;background:var(--fgm-feature-bg,#f7f8fa);color:var(--fgm-feature-fg,#202936);font-size:14px;z-index:2;cursor:pointer';
   done.onclick=()=>{const dismiss=pop.querySelector('button[aria-label="Dismiss"]');if(dismiss){dismiss.click();return;}const active=d.activeElement;active?.dispatchEvent(new w.KeyboardEvent('keydown',{key:'Escape',code:'Escape',bubbles:true}));active?.blur();d.body.dispatchEvent(new w.MouseEvent('mousedown',{bubbles:true}));};
   pop.appendChild(done);
  });
 };
 if(!w.__fgmSelectDone){w.__fgmSelectDone=new w.MutationObserver(install);w.__fgmSelectDone.observe(d.body,{childList:true,subtree:true});}install();
 const closeSidebar=()=>{
  const sidebar=d.querySelector('[data-testid="stSidebar"]');
  if(!sidebar||sidebar.getAttribute('aria-expanded')==='false')return;
  const control=d.querySelector('[data-testid="stCollapseSidebarButton"]')||d.querySelector('[data-testid="stSidebarCollapseButton"]')||sidebar.querySelector('button[aria-label="Collapse sidebar"]');
  const button=control?.matches('button')?control:control?.querySelector('button');
  button?.click();
 };
 if(w.__fgmNavHandler){d.removeEventListener('click',w.__fgmNavHandler,true);w.removeEventListener('click',w.__fgmNavHandler,true);}
 w.__fgmNavHandler=e=>{
  const close=e.target.closest('.st-key-sidebar_close');
  if(close){e.preventDefault();e.stopImmediatePropagation();closeSidebar();return;}
  const nav=e.target.closest('[data-testid="stSidebar"] [data-testid="stRadioOption"]');
  if(!nav&&!e.target.closest('.st-key-mobile_sync_shortcut,.st-key-refresh_current_page'))return;
  if(!w.__fgmAutoNav)w.setTimeout(closeSidebar,180);
  if(nav)w.setTimeout(()=>{const main=d.querySelector('[data-testid="stMain"]');if(main)main.scrollTop=0;w.scrollTo(0,0);},200);
 };
 w.addEventListener('click',w.__fgmNavHandler,true);

}catch(e){}
</script>'''

def render_compact_styles():
    theme=st.session_state.get('visual_theme','黑色鏡面')
    bg,fg,border={'簡約淺色':('#f7f8fa','#202936','#d5dce5'),'戰術板草圖':('#142b29','#f0eee3','#54736a')}.get(theme,('#0b1020','#edf2f7','#384152'))
    variables=f'.stApp{{--fgm-feature-bg:{bg};--fgm-feature-fg:{fg};--fgm-feature-border:{border};--fgm-muted:{'#526174' if theme=='簡約淺色' else '#b8c7d2'};}}'
    responsive=CSS.replace('@media(max-width:640px)','@media(max-width:100000px)') if st.session_state.get('device_view')=='手機版' else CSS
    # Wide screens retain four controls even when mobile content is selected.
    responsive+='''@media(min-width:1101px){.stApp .st-key-dashboard_controls [data-testid="stHorizontalBlock"]{display:grid!important;grid-template-columns:minmax(110px,.8fr) minmax(180px,1.6fr) minmax(180px,1.1fr) minmax(140px,1fr)!important;gap:16px!important}.stApp .st-key-dashboard_controls [data-testid="stColumn"]{width:100%!important;min-width:0!important}}'''

    responsive+='''
/* Shared two-row app header: override earlier density rules explicitly. */
.stApp [data-testid="stMainBlockContainer"]{padding-top:0!important}
.stApp .st-key-current_feature [data-testid="stButton"] button{border:0!important;box-shadow:none!important;background:transparent!important}
.stApp .st-key-app_status_bar [data-baseweb="select"]{border:0!important;background:transparent!important}

.stApp .st-key-current_feature{padding:6px 8px 6px 58px!important;min-height:56px!important;display:block!important;border-radius:0!important;margin:0!important}
.stApp .st-key-current_feature [data-testid="stHorizontalBlock"]{display:grid!important;grid-template-columns:minmax(0,1fr) 44px 44px!important;gap:6px!important;align-items:center!important}
.stApp .st-key-current_feature [data-testid="stColumn"]{width:100%!important;min-width:0!important;max-width:100%!important;flex:none!important}
.stApp .st-key-current_feature button{width:44px!important;height:44px!important;min-height:44px!important;border:0!important;background:transparent!important;padding:0!important}
.stApp .st-key-current_feature p,.stApp .st-key-current_feature strong{font-size:24px!important;line-height:44px!important;margin:0!important}
.stApp .st-key-current_feature .st-key-mobile_sync_shortcut button p{color:#7200c8!important;font-size:28px!important;font-weight:800!important}
.stApp .st-key-current_feature .st-key-refresh_current_page button p{font-size:30px!important}
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > [data-testid="stLayoutWrapper"]:has(.st-key-current_feature){top:0!important}
[data-testid="stSidebarCollapsedControl"],[data-testid="stExpandSidebarButton"]{top:6px!important}
.stApp .st-key-app_status_bar [data-testid="stHorizontalBlock"]{display:grid!important;grid-template-columns:minmax(0,1fr) 110px 70px!important;gap:10px!important;align-items:center!important}
.stApp .st-key-app_status_bar [data-testid="stColumn"]{width:100%!important;min-width:0!important;max-width:100%!important}
.stApp .st-key-app_status_bar [data-testid="stWidgetLabel"]{display:none!important}
.stApp .st-key-app_status_bar [data-baseweb="select"]>div{border:0!important;background:transparent!important;min-height:40px!important}
.stApp .st-key-app_status_bar [data-testid="stCaptionContainer"]{text-align:right!important;white-space:nowrap!important}
.stApp .st-key-sidebar_actions [data-testid="stHorizontalBlock"]{grid-template-columns:44px!important}
'''
    responsive+='''
/* The platform header must not paint over the app's own toolbar. */
.stApp.stApp.stApp header[data-testid="stHeader"]{background:transparent!important;pointer-events:none!important;box-shadow:none!important}
.stApp [data-testid="stHeader"] button{pointer-events:auto!important}
.stApp .st-key-current_feature{opacity:1!important;visibility:visible!important}
.stApp .st-key-sidebar_close{position:fixed!important;left:12px!important;top:6px!important;width:44px!important;height:44px!important;z-index:100003!important;margin:0!important}
.stApp.stApp.stApp .st-key-sidebar_close button,.stApp.stApp.stApp button[data-testid="stExpandSidebarButton"],.stApp.stApp.stApp [data-testid="stExpandSidebarButton"] button,.stApp.stApp.stApp [data-testid="stSidebarCollapsedControl"] button,.stApp.stApp.stApp button[aria-label="Expand sidebar"]{border:0!important;outline:0!important;box-shadow:none!important;background:transparent!important;border-radius:0!important;padding:0!important;width:44px!important;height:44px!important;color:var(--fgm-feature-fg)!important}
.stApp .st-key-sidebar_identity{margin-top:50px!important}
.stApp .st-key-app_status_bar [data-testid="stSegmentedControl"]{margin:0!important;min-height:36px!important}
.stApp .st-key-app_status_bar button{min-height:34px!important;padding:4px 8px!important}
@media(max-width:380px){.stApp .st-key-app_status_bar [data-testid="stHorizontalBlock"]{grid-template-columns:minmax(0,1fr) 84px 58px!important;gap:4px!important}}
'''
    st.markdown('<style>'+variables+responsive+'</style>',unsafe_allow_html=True)

def render_compact_ui(apply_styles=True):
    if apply_styles:render_compact_styles()
    components.html(NAV,height=0)
