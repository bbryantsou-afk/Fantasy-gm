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
    token=st.query_params.get('mobile') or st.session_state.get('_mobile_share_token')
    if not token:return
    root=share_root(token)
    if not root:
        st.error('手機共用連結已停用，或雲端重部署後資料已清除。請在電腦建立新連結。')
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
    from ninecat_strategy import load_data
    from roster_store import state
    from data_center import store
    st.markdown('### 電腦／手機入口')
    st.link_button('電腦版入口',BASE+'?theme=light')
    st.link_button('手機版入口',BASE+'?theme=light&phone_sync=1')
    st.caption('兩個入口使用同一套網站程式，功能與版面同步發布。不同瀏覽器的私人名單不會自動互通；需開啟下方同一個共用連結，才能共用資料。')
    st.markdown('### 📱 手機共用連結')
    st.caption('先在電腦同步名單，再建立連結並用手機開啟。兩端共用名單與比賽紀錄，手機每 30 秒檢查更新，不需 Chrome 擴充功能。')
    st.info('持有連結的人可以查看與修改這份共用資料，請只傳給自己的裝置。沒有到期限制，可隨時手動停用；雲端重部署仍可能清除暫存資料。Yahoo 帳密與 API 金鑰不會分享。')
    token=st.session_state.get('_mobile_share_token')
    if not token and st.button('建立手機共用連結',key='create_mobile_share'):
        _,entries=load_data();token=create_share(state(entries),store())
        st.session_state['_mobile_share_token']=token;st.query_params['mobile']=token;st.rerun()
    if token and share_root(token):
        link=BASE+'?theme='+st.query_params.get('theme','light')+'&mobile='+token
        st.text_input('複製連結到手機（請勿公開）',value=link,key='mobile_share_url_'+token)
        st.caption('手機開啟後即可操作各功能；Yahoo 名單異動仍由電腦同步，手機會讀取更新。重要資料仍請定期備份。')
        if st.button('停用此共用連結',key='revoke_mobile_share'):
            root=share_root(token);write_json(root/'access.json',{'revoked':True})
            st.query_params.pop('mobile',None);st.session_state.pop('_mobile_share_token',None);st.rerun()
