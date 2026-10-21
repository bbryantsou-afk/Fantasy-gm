"""Clean white theme, with no handwriting or decorative background."""
APP_CSS = '''
.stApp {background:#f7f8fa !important;background-image:none !important;color:#202a36 !important;color-scheme:light;--background-color:#ffffff;--secondary-background-color:#f1f4f7;--text-color:#202a36;}
.stApp [data-testid="stHeader"] {background:#f7f8faf2 !important;}
.stApp [data-testid="stSidebar"] {background:#fff !important;border-right:1px solid #dfe4e9;}
.stApp h1,.stApp h2,.stApp h3,.stApp p,.stApp label,.stApp button,.stApp input,.stApp textarea,.stApp select,.stApp table,.stApp [data-testid="stMetricValue"],.stApp [data-testid="stCaptionContainer"] {font-family:system-ui,-apple-system,"Noto Sans TC",sans-serif !important;letter-spacing:normal !important;text-shadow:none !important;}
.stApp h1,.stApp h2,.stApp h3,.stApp p,.stApp label {color:#202a36 !important;}
.stApp [data-testid="stCaptionContainer"],.stApp [data-testid="stCaptionContainer"] p {color:#5f6c7b !important;}
.stApp [data-testid="stVerticalBlockBorderWrapper"],.stApp [data-testid="stExpander"],.stApp [data-testid="stMetric"],.stApp [data-testid="stAlert"],.stApp .nc-baseline-strip,.stApp .sched-card,.stApp .sched-calendar,.stApp div:has(> .mvp-body) {background:#fff !important;border:1px solid #dce2e8 !important;border-radius:10px !important;box-shadow:none !important;color:#202a36 !important;}
.stApp div:has(> .mvp-body) *:not(img),.stApp .nc-baseline-value,.stApp [data-testid="stMetricValue"],.stApp [data-testid="stMetricLabel"] {color:#203f46 !important;}
.stApp .nc-baseline-label,.stApp .nc-baseline-stat {color:#5f6c7b !important;border-color:#e2e7ec !important;}
.stApp [data-testid="stSidebar"] [data-testid="stRadioOption"] {background:#fff !important;border:1px solid #dce2e8 !important;border-radius:9px !important;box-shadow:none !important;}
.stApp [data-testid="stSidebar"] [data-testid="stRadioOption"] p {color:#263444 !important;font-family:system-ui,sans-serif !important;}
.stApp [data-testid="stSidebar"] [data-testid="stRadioOption"]:has(input:checked) {background:#e8f4f0 !important;border-color:#58a38e !important;}
.stApp [data-testid="stSidebar"] [data-testid="stRadioOption"]:hover {background:#f0f4f7 !important;}
.stApp button[kind],.stApp [data-testid="stDownloadButton"] button {background:#fff !important;border:1px solid #b8c5d1 !important;color:#263444 !important;border-radius:8px !important;box-shadow:none !important;}
.stApp button[kind] *,.stApp [data-testid="stDownloadButton"] button * {color:#263444 !important;}
.stApp button[kind="primary"] {background:#e0f1eb !important;border-color:#4a9c83 !important;}
.stApp input,.stApp textarea,.stApp [data-baseweb="select"]>div,.stApp [data-testid="stDateInputField"],.stApp [data-testid="stSelectbox"] [role="group"],.stApp [data-testid="stMultiSelect"] [role="group"],.stApp [data-testid="stNumberInputContainer"] {background:#fff !important;border:1px solid #bcc8d3 !important;color:#202a36 !important;border-radius:8px !important;box-shadow:none !important;}
.stApp [data-testid="stSelectbox"] input,.stApp [data-testid="stMultiSelect"] input,.stApp [data-testid="stNumberInputContainer"] input {border:0 !important;background:transparent !important;}
.stApp [data-testid="stSelectbox"] button,.stApp [data-testid="stMultiSelect"] button {background:transparent !important;color:#263444 !important;}
.stApp [data-baseweb="select"] *,.stApp [data-testid="stDateInputField"] *:not(svg),.stApp [data-testid="stSelectbox"] input {color:#202a36 !important;}
.stApp input::placeholder,.stApp textarea::placeholder {color:#748190 !important;}
.stApp a {color:#176b87;}
.stApp .sched-calendar th,.stApp .sched-calendar td {background:#fff !important;color:#506172;border-color:#e2e7ed !important;}
.stApp .sched-calendar td.sched-b2b {background:#e4f3eb !important;color:#176347 !important;}
.stApp .sched-game-count,.stApp .sched-game-count strong,.stApp .sched-more summary,.stApp .sched-card strong {color:#334d56 !important;}
[role="listbox"],[role="option"] {background:#fff !important;color:#202a36 !important;font-family:system-ui,sans-serif !important;}
'''
COMPONENT_CSS = '''
#lineup-app {color:#263444 !important;}
#lineup-app,#lineup-app *:not(img) {font-family:system-ui,-apple-system,sans-serif !important;text-shadow:none !important;}
#lineup-app .roster,#lineup-app .middle,#lineup-app .summary,#lineup-app .sim-save,#lineup-app .editor-panel {background:#fff !important;border:1px solid #cdd7e1 !important;color:#263444 !important;border-radius:10px !important;box-shadow:none !important;}
#lineup-app .slot,#lineup-app .bench {background:#f4f7fa !important;border-color:#aebdcb !important;}
#lineup-app .player,#lineup-app .player.game {background:#dceee7 !important;color:#163e32 !important;}
#lineup-app .player.opp,#lineup-app .player.opp.game {background:#eee5f6 !important;color:#483358 !important;}
#lineup-app .player.off {background:#e7ebf0 !important;color:#5a6876 !important;}
#lineup-app .player.b2b,#lineup-app .player.opp.b2b {background:#f6ead0 !important;color:#684c19 !important;}
#lineup-app button,#lineup-app input,#lineup-app select {background:#fff !important;color:#263444 !important;border:1px solid #b0bfce !important;border-radius:7px !important;}
#lineup-app .day.active,#lineup-app .lite-tabs button.active {background:#dceee7 !important;border-color:#49957e !important;}
#lineup-app h3,#lineup-app .pos,#lineup-app .player-name,#lineup-app .stat b {color:#253c50 !important;}
#lineup-app .note,#lineup-app .guide,#lineup-app .actions,#lineup-app .analysis-note,#lineup-app small,#lineup-app .head,#lineup-app .editor-label {color:#526779 !important;}
#lineup-app .stat {background:#f1f5f8 !important;}
#lineup-app .lite-tray {background:#fffffff7 !important;border-top:1px solid #bdcbd7 !important;box-shadow:0 -3px 15px #17334a12;}
#lineup-app .lite-ghost {background:#24584a !important;color:#fff !important;}
#lineup-app .score-blue {color:#236a9a !important;}#lineup-app .score-purple {color:#79509a !important;}
#lineup-app .win {color:#17764e !important;}
#lineup-app th,#lineup-app td {color:#263444 !important;border-color:#dce3e9 !important;}
#lineup-app .editor-fields label {color:#364f63 !important;}
'''
APP_CSS += '''
.stApp [data-heading-text],.stApp [data-testid="stHeadingWithActionElements"] span {color:#202a36 !important;}
.stApp [data-testid="stRadioOption"]:not(:has(input:checked)) > div > div {background:#fff !important;border-color:#94a6b7 !important;}
'''
COMPONENT_CSS += '''
#lineup-app {color-scheme:light;}
#lineup-app select option,#lineup-app select {color:#263444 !important;background:#fff !important;}
'''
APP_CSS += '''
.stApp [data-testid="stLinkButton"] a,.stApp a[data-testid^="stBaseLinkButton"],.stApp a[kind] {background:#fff !important;color:#245366 !important;border:1px solid #b8c8d3 !important;border-radius:8px !important;box-shadow:none !important;}
.stApp [data-testid="stLinkButton"] a *,.stApp a[data-testid^="stBaseLinkButton"] *,.stApp a[kind] * {color:#245366 !important;}
.stApp [data-testid="stLinkButton"] a:hover {background:#edf5f7 !important;border-color:#639cae !important;}
.stApp [data-testid="stTable"],.stApp [data-testid="stTable"] th,.stApp [data-testid="stTable"] td,.stApp [data-testid="stJson"],.stApp pre {background:#fff !important;color:#263444 !important;border-color:#dce3e9 !important;}
.stApp [data-testid="stJson"] span,.stApp pre code {color:#263444 !important;}
'''

APP_CSS += '''
.stApp [data-testid="stMarkdownContainer"],.stApp [data-testid="stText"],.stApp [data-testid="stWidgetLabel"] p,.stApp [data-testid="stMetricValue"],.stApp [data-testid="stMetricLabel"] p,.stApp [data-testid="stExpander"] summary,.stApp [role="tab"],.stApp [role="tab"] p {color:#202a36 !important;}
.stApp [data-testid="stCaptionContainer"] p,.stApp small {color:#526171 !important;}
.stApp [data-baseweb="tag"],.stApp [data-baseweb="tag"] * {background:#e7f1ed !important;color:#214e43 !important;fill:#214e43 !important;}
.stApp button:disabled,.stApp button:disabled * {color:#647181 !important;background:#edf0f4 !important;opacity:1 !important;}
.stApp [data-testid="stCode"],.stApp [data-testid="stCode"] *, .stApp [data-testid="stTextInput"] input {color:#202a36 !important;}
@media(max-width:640px){.stApp [data-testid="stMainBlockContainer"]{padding-left:1rem;padding-right:1rem}.stApp [data-testid="stMetricValue"]{font-size:1.5rem}.stApp [role="tab"]{min-height:44px}}
'''

APP_CSS += '''
.stApp [data-testid="stCaptionContainer"],.stApp [data-testid="stCaptionContainer"] * {color:#455466 !important;opacity:1 !important;}
.stApp [data-testid="stMarkdownContainer"] small,.stApp [data-testid="stSidebar"] small {color:#455466 !important;opacity:1 !important;}
'''

# Keep controls and chart surfaces on the same neutral background as the page.
APP_CSS += """
.stApp{--background-color:#f7f8fa;--secondary-background-color:#f7f8fa;}
.stApp button[kind],.stApp [data-testid="stDownloadButton"] button,.stApp [data-testid="stLinkButton"] a,.stApp a[kind],.stApp input,.stApp textarea,.stApp [data-baseweb="select"]>div,.stApp [data-testid="stDateInputField"],.stApp [data-testid="stNumberInputContainer"],.stApp [data-testid="stExpander"],.stApp [data-testid="stVerticalBlockBorderWrapper"]{background:#f7f8fa!important;}
.stApp [data-testid="stVegaLiteChart"]{background:transparent!important;}
"""

APP_CSS += """
.stApp [data-testid="stSelectbox"] [role="group"],.stApp [data-testid="stMultiSelect"] [role="group"]{background:#f7f8fa!important;}
"""
