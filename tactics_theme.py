"""Optional chalkboard styling shared by Streamlit and matchup components."""
FONT_CSS = "@import url('https://fonts.googleapis.com/css2?family=LXGW+WenKai+TC&family=Patrick+Hand&display=swap');"
FAMILY = '"Patrick Hand","LXGW WenKai TC","Kaiti TC",KaiTi,cursive'
APP_CSS = FONT_CSS + '''
.stApp {background-color:#142b29 !important;background-image:radial-gradient(ellipse at 25% 15%,#ffffff08,transparent 60%),repeating-linear-gradient(3deg,#ffffff02 0px,#ffffff02 1px,transparent 1px,transparent 7px) !important;color:#eeeede !important;}
.stApp [data-testid="stSidebar"] {background:#0d211e55 !important;border-right:2px dashed #bfcdb657;}
.stApp [data-testid="stHeader"] {background:linear-gradient(#142b29ee,#142b2900) !important;}
.stApp h1,.stApp h2,.stApp h3,.stApp p,.stApp label,.stApp button,.stApp input,.stApp textarea,.stApp select,.stApp table,.stApp [data-baseweb="select"],.stApp [data-testid="stCaptionContainer"],.stApp .nc-baseline-strip {font-family:HAND_FONT !important;letter-spacing:.25px;}
.stApp h1,.stApp h2,.stApp h3 {color:#f3eed5 !important;text-shadow:1px 1px #ffffff33 !important;}
.stApp [data-testid="stSidebar"] [data-testid="stRadioOption"],
.stApp button[kind],.stApp [data-testid="stDownloadButton"] button,
.stApp [data-baseweb="select"]>div,.stApp input,.stApp textarea,
.stApp [data-testid="stExpander"],.stApp [data-testid="stMetric"],
.stApp [data-testid="stAlert"],.stApp [data-testid="stDataFrame"],
.stApp [data-testid="stVegaLiteChart"],.stApp .nc-baseline-strip,
.stApp .sched-card,.stApp .sched-calendar,.stApp div:has(> .mvp-body) {
 background:#16322fee !important;color:#f4f0df !important;
 border:1.5px solid #cbd4bcaa !important;
 border-radius:7px 13px 5px 11px / 11px 5px 12px 6px !important;
 box-shadow:1px 2px 0 #d0dac544,-1px -1px 0 #d0dac522 !important;
}
.stApp [data-baseweb="select"] *, .stApp input,.stApp textarea {color:#f4f0df !important;}
.stApp [data-baseweb="select"] svg {fill:#eeeede !important;}
.stApp [data-testid="stSidebar"] [data-testid="stRadioOption"] p {font-family:HAND_FONT !important;font-size:16px !important;}
.stApp [data-testid="stSidebar"] [data-testid="stRadioOption"]:has(input:checked),.stApp button[kind="primary"] {background:#3b5041 !important;border-color:#ecd68e !important;color:#ffe7a0 !important;}
.stApp button[kind] *, .stApp [data-testid="stDownloadButton"] button * {color:#f4f0df !important;}
.stApp [data-testid="stMetricValue"],.stApp .nc-baseline-value {font-family:HAND_FONT !important;color:#ffe7a0 !important;}
.stApp .sched-calendar th,.stApp .sched-calendar td {background:#16322f !important;color:#eeeede;}
.stApp .sched-calendar td.sched-b2b {color:#b7e8bd;background:#285144 !important;}
.stApp .sched-more summary,.stApp .nc-baseline-label {color:#d4d6c0 !important;}
.stApp input::placeholder,.stApp textarea::placeholder {color:#bdc9b5 !important;}
.stApp [data-testid="stCaptionContainer"] {color:#ced4bd !important;}
'''.replace('HAND_FONT', FAMILY)

COMPONENT_CSS = FONT_CSS + '''
#lineup-app,#lineup-app *:not(img) {font-family:HAND_FONT !important;}
#lineup-app .roster,#lineup-app .middle,#lineup-app .summary,#lineup-app .sim-save,
#lineup-app .editor-panel,#lineup-app .player,#lineup-app .slot,#lineup-app .bench,
#lineup-app button,#lineup-app input,#lineup-app select,#lineup-app .stat,#lineup-app .trash {
 border:1.5px solid #cbd4bcaa !important;border-radius:5px 11px 4px 9px / 10px 4px 11px 5px !important;
 box-shadow:1px 1px 0 #d0dac533;background:#18352f !important;color:#f4f0df !important;
}
#lineup-app .slot,#lineup-app .bench {border-style:dashed !important;background:#102c25 !important;}
#lineup-app .player.game,#lineup-app .player.b2b {background:#315341 !important;}
#lineup-app .player.opp.game,#lineup-app .player.opp.b2b {background:#4b4930 !important;}
#lineup-app .day.active,#lineup-app .lite-tabs button.active {border-color:#ffe29b !important;background:#46543a !important;}
#lineup-app .player.off {background:#293b35 !important;}
#lineup-app .lite-tray {background:#122c25fa !important;border-top:2px dashed #d0dac5 !important;}
#lineup-app .lite-picked,#lineup-app .slot.over {outline:2px dashed #ffe29b !important;}
#lineup-app h3,#lineup-app .pos {color:#ffe29b !important;}
#lineup-app .table-wrap {border:1px dashed #cbd4bcaa;border-radius:9px;}
#lineup-app th,#lineup-app td {border-bottom:1px dashed #d0dac555 !important;}
'''.replace('HAND_FONT',FAMILY)

# Quiet playbook marks, drawn as vector paths so no large image is downloaded.
import base64
_SKETCH = '''<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="1000" viewBox="0 0 1400 1000"><g fill="none" stroke="#e2e5c7" stroke-width="2" opacity=".12" stroke-linecap="round" stroke-linejoin="round"><circle cx="1210" cy="140" r="30"/><circle cx="1207" cy="141" r="29"/><path d="M1160 155 Q1030 195 1080 290 L1062 272 M1080 290 L1090 265" stroke-dasharray="8 10"/><path d="M1280 300l28 28m-28 0l28-28M1240 450q100-20 70-100l-10 20m10-20l20 8M55 700l28 28m-28 0l28-28M115 810q80-90 160-40l-14-20m14 20l-25 2"/><circle cx="200" cy="900" r="26"/><path d="M980 850q130-95 290-15" stroke-dasharray="8 12"/></g></svg>'''
_sketch_url='data:image/svg+xml;base64,'+base64.b64encode(_SKETCH.encode()).decode()
APP_CSS += '''
.stApp {background-image:linear-gradient(135deg,#11262255,#24423922),url("SKETCH"),repeating-linear-gradient(3deg,#ffffff02 0px,#ffffff02 1px,transparent 1px,transparent 7px) !important;background-size:cover,cover,auto !important;}
.stApp [data-testid="stDateInputField"],.stApp [data-testid="stSelectbox"] [role="group"],
.stApp [data-testid="stMultiSelect"] [role="group"],.stApp [data-testid="stNumberInputContainer"] {
 background:#16322fee !important;color:#f4f0df !important;border:1.5px solid #cbd4bcaa !important;
 border-radius:7px 13px 5px 11px / 11px 5px 12px 6px !important;box-shadow:1px 2px 0 #d0dac544 !important;
}
.stApp [data-testid="stSelectbox"] input,.stApp [data-testid="stMultiSelect"] input,.stApp [data-testid="stNumberInputContainer"] input {border:0 !important;box-shadow:none !important;background:transparent !important;}
.stApp [data-testid="stSelectbox"] button,.stApp [data-testid="stMultiSelect"] button {background:transparent !important;color:#eeeede !important;}
.stApp [data-testid="stDateInputField"] *:not(svg),.stApp [data-testid="stSelectbox"] *:not(svg) {font-family:HAND_FONT !important;}
[role="listbox"],[role="option"] {background:#16322f !important;color:#f4f0df !important;font-family:HAND_FONT !important;}
'''.replace('SKETCH',_sketch_url).replace('HAND_FONT',FAMILY)
