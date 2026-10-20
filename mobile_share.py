"""Revocable, bearer-link sharing of roster/results only; never credentials."""
import hashlib,json,re,secrets,tempfile
from pathlib import Path
import streamlit as st

FILES={'league_rosters.json','league_results.json'}
BASE='https://fantasy-gm-bgjfjwjnxx8mbxjvajm2nk.streamlit.app/'

def share_root(token):
    if not isinstance(token,str) or not re.fullmatch(r'[a-f0-9]{64}',token):return None
    root=Path(tempfile.gettempdir())/'fantasy-gm-mobile'/hashlib.sha256(token.encode()).hexdigest()
    try:
        meta=json.loads((root/'access.json').read_text())
        # Older links used a positive expiry; keep them valid after removing expiry.
        if meta.get('revoked') is True or meta.get('expires')==0:return None
        if 'expires' not in meta and meta.get('revoked') is not False:return None
    except (OSError,ValueError,KeyError,TypeError):return None
    return root

def shared_path(filename):
    token=st.session_state.get('_mobile_share_token')
    root=share_root(token)
    return root/filename if root and filename in FILES else None

def write_json(path,data):
    temp=path.with_name(path.name+'.'+secrets.token_hex(8)+'.tmp')
    temp.write_text(json.dumps(data,ensure_ascii=False));temp.replace(path)

def create_share(roster,results):
    token=secrets.token_hex(32)
    root=Path(tempfile.gettempdir())/'fantasy-gm-mobile'/hashlib.sha256(token.encode()).hexdigest()
    root.mkdir(parents=True,exist_ok=False,mode=0o700)
    write_json(root/'league_rosters.json',roster);write_json(root/'league_results.json',results)
    write_json(root/'access.json',{'revoked':False})
    return token

def init_share():
    if st.session_state.get("_account_id"):return
    token=st.query_params.get('mobile') or st.session_state.get('_mobile_share_token')
    if not token:return
    root=share_root(token)
    if not root:
        st.error('舊共用連結已停用或資料已清除。請離開此連結，回一般入口登入 Google 使用個人 Drive 紀錄。')
        if st.button('離開此共用連結'):
            st.query_params.pop('mobile',None);st.session_state.pop('_mobile_share_token',None);st.rerun()
        st.stop()
    st.session_state['_mobile_share_token']=token
    for filename,key in [('league_rosters.json','_league'),('league_results.json','_results')]:
        try:st.session_state[key]=json.loads((root/filename).read_text())
        except (ValueError,OSError):pass
    st.session_state['_mobile_seen']=tuple((root/f).stat().st_mtime_ns for f in sorted(FILES))

@st.fragment(run_every='30s')
def watch_share():
    root=share_root(st.session_state.get('_mobile_share_token'))
    if not root:return
    version=tuple((root/f).stat().st_mtime_ns for f in sorted(FILES))
    if version!=st.session_state.get('_mobile_seen'):st.rerun()

def render_mobile_settings():
    st.markdown('### 電腦／手機入口')
    st.link_button('開啟 Fantasy GM',BASE+'?theme=light')
    st.caption('電腦、手機使用同一網站，在頁面頂端切換顯示版本。模擬對局：電腦版為完整介面，手機版為 Lite。相同 Google 帳號共用保存資料；顯示版本各裝置獨立。')
    if st.session_state.get('_account_id'):
        st.info('已連接個人 Drive。任何一端保存星號、權重或名單後，其他開啟的裝置每 5 秒檢查更新。')
        return
    st.info('請在上方登入 Google，啟用個人 Drive 跨裝置保存。訪客紀錄僅保存在這個瀏覽器。')
