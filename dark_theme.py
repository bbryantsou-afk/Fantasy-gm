"""Paired dark surfaces and readable widget text, independent of host theme."""
APP_CSS = '''
.stApp{color-scheme:dark;--background-color:#101319;--secondary-background-color:#202630;--text-color:#edf2f7;--fgm-muted:#b5c1ce;--fgm-feature-bg:#161c24;--fgm-feature-border:#526071}
.stApp :is(button[kind],button[data-testid^="stBaseButton"],[data-testid="stDownloadButton"] button,[data-testid="stLinkButton"] a,a[kind]){background:#202630!important;color:#edf2f7!important;border-color:#657386!important;box-shadow:none!important}
.stApp :is(button[kind],button[data-testid^="stBaseButton"],[data-testid="stDownloadButton"] button,[data-testid="stLinkButton"] a,a[kind]) :is(div,p,span,strong,small){color:inherit!important;background:transparent!important;background-image:none!important}
.stApp :is(button[kind],button[data-testid^="stBaseButton"],[data-testid="stLinkButton"] a,a[kind]):hover{background:#303d4d!important;color:#fff!important;border-color:#a4bbd1!important}
.stApp :is(button[kind],button[data-testid^="stBaseButton"],a[kind]):focus-visible{outline:2px solid #8fc8ff!important;outline-offset:2px}
.stApp :is(button[kind="primary"],button[aria-pressed="true"]){background:#254f46!important;color:#f0fff9!important;border-color:#78cdb6!important}
.stApp button:disabled{background:#252a33!important;color:#aeb8c7!important;opacity:1!important;border-color:#505c6b!important}
.stApp button:disabled :is(div,p,span,strong){color:inherit!important;background:transparent!important}
.stApp :is(input,textarea,select,[data-baseweb="select"]>div,[data-testid="stDateInputField"],[data-testid="stNumberInputContainer"]){background:#161c24!important;color:#edf2f7!important;border-color:#657386!important}
.stApp [data-baseweb="select"] :is(span,input),.stApp [data-testid="stDateInputField"] input{color:#edf2f7!important;background:transparent!important}
.stApp :is(input,textarea)::placeholder{color:#aebdca!important}
.stApp :is([data-testid="stExpander"] summary,[data-testid="stFileUploaderDropzone"]){background:#161c24!important;color:#edf2f7!important}
.stApp [data-testid="stExpander"] summary :is(p,span){color:inherit!important;background:transparent!important}
.stApp [data-testid="stFileUploaderDropzone"] :is(p,small,span){color:#edf2f7!important;background:transparent!important}
[data-baseweb="popover"] :is([role="listbox"],[role="option"]),[role="listbox"],[role="option"],[data-testid="stPopoverBody"]{background:#202630!important;color:#edf2f7!important}
[role="option"] :is(div,span,p),[data-testid="stPopoverBody"] :is(p,label){color:#edf2f7!important;background:transparent!important}
[data-testid="stPopoverBody"] :is(button,a[kind]){background:#303d4d!important;color:#edf2f7!important;border-color:#657386!important}
[data-testid="stPopoverBody"] button :is(div,p,span){color:inherit!important;background:transparent!important}
.stApp .st-key-mobile_sync_shortcut button p{color:#d7b0ff!important}
'''
