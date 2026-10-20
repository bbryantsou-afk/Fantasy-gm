"""Verified Google identity + server-only persistent profile storage with revision checks."""
import copy,hashlib,json,re,tempfile,time
from pathlib import Path
import requests
import streamlit as st
from profile_preferences import preference_key,capture_preferences
from drive_profiles import CloudError,CloudConflict,CloudClient
from google_drive_auth import config,init_auth,render_login,render_logout,finish_auth

def signed_user():
    return st.session_state.get('_drive_user')

def owner_id(user):
    if not isinstance(user,dict) or user.get('iss') not in ['https://accounts.google.com','accounts.google.com'] or not isinstance(user.get('sub'),str) or not user['sub']:raise CloudError('Google 身分驗證資料不完整，未載入帳號資料。')
    return hashlib.sha256(('google:'+user['sub']).encode()).hexdigest()

def client():return CloudClient(config())

def account_path(filename):
    owner=st.session_state.get('_account_id')
    if not owner:return None
    from browser_records import FILES
    if filename not in FILES:return None
    path=Path(tempfile.gettempdir())/'fantasy-gm-accounts'/owner/st.session_state['_account_workspace']
    path.mkdir(parents=True,exist_ok=True)
    return path/filename

def digest(payload):return hashlib.sha256(json.dumps(payload,sort_keys=True,ensure_ascii=False).encode()).hexdigest()

def snapshot():
    from browser_records import FILES
    from app_storage import private_path
    root=Path(__file__).parent;files={}
    for name in FILES:
        path=private_path(root/name)
        try:files[name]=json.loads(path.read_text())
        except (ValueError,OSError):pass
    if '_league' in st.session_state:files['league_rosters.json']=copy.deepcopy(st.session_state['_league'])
    if '_results' in st.session_state:files['league_results.json']=copy.deepcopy(st.session_state['_results'])
    prefs=capture_preferences(st.session_state)
    return {'schema':1,'files':files,'prefs':prefs}

def clean(payload):
    from ninecat_strategy import load_data
    from browser_records import validate_records
    _,entries=load_data();files,prefs=validate_records(payload,entries,max_bytes=25_000_000)
    return {'schema':1,'files':files,'prefs':prefs}

def apply_profile(payload,revision):
    payload=clean(payload)
    from browser_records import FILES
    for name in FILES:
        path=account_path(name)
        if name in payload['files']:
            temp=path.with_suffix('.restore.tmp');temp.write_text(json.dumps(payload['files'][name],ensure_ascii=False));temp.replace(path)
        elif path.exists():path.unlink()
    for key in list(st.session_state):
        if preference_key(key) or key in ['_league','_results','nc_roster','nc_weeks','watch_open','watch_stars','nc_watch_stars'] or key.startswith('auto_protect_'):st.session_state.pop(key,None)
    if 'league_rosters.json' in payload['files']:st.session_state['_league']=payload['files']['league_rosters.json']
    if 'league_results.json' in payload['files']:st.session_state['_results']=payload['files']['league_results.json']
    st.session_state['_portable_preferences']=copy.deepcopy(payload['prefs'])
    for k,v in payload['prefs'].items():st.session_state[k]=v
    for key in ['_sim_restore','_sim_restore_name','sim_open_name']:
        st.session_state.pop(key,None)
    st.session_state['_sim_restore_nonce']=__import__('uuid').uuid4().hex
    st.session_state['_account_revision']=revision
    st.session_state['_account_base']=digest(payload)
    st.session_state['_account_loaded']=True
    st.session_state.pop('_account_conflict',None);st.session_state.pop('_account_save_error',None)
    if payload['prefs'].get('visual_theme'):
        from court_theme import theme_slug
        st.query_params['theme']=theme_slug()

def init_account():
    if not config():return
    init_auth()
    user=signed_user()
    if not user:return
    try:owner=owner_id(user)
    except CloudError as exc:st.error(str(exc));st.stop()
    import uuid
    previous=st.session_state.get('_account_id')
    if previous and previous!=owner:
        auth={k:v for k,v in st.session_state.items() if k.startswith('_drive_')}
        st.session_state.clear();st.session_state.update(auth)
    st.session_state['_account_id']=owner
    st.session_state.setdefault('_account_workspace',uuid.uuid4().hex)
    st.session_state['_account_user_name']=str(user.get('name') or 'Google 使用者')
    st.session_state.pop('_mobile_share_token',None)
    if st.session_state.pop('_account_reload',False):
        try:
            remote=client().load(owner)
            if remote:apply_profile(remote['payload'],remote['revision'])
        except (CloudError,ValueError,KeyError,TypeError) as exc:st.session_state['_account_save_error']=str(exc)
    if not st.session_state.get('_account_checked'):
        try:
            remote=client().load(owner)
            if remote:apply_profile(remote['payload'],remote['revision'])
            else:st.session_state['_account_new']=True
            st.session_state['_account_checked']=True
        except (CloudError,ValueError,KeyError,TypeError) as exc:
            st.error('無法載入帳號資料，暫停編輯以避免誤覆寫。'+str(exc))
            st.button('重試載入帳號',on_click=st.rerun);render_logout('drive_error_logout');finish_auth();st.stop()

@st.fragment(run_every='5s')
def poll_account():
    if not st.session_state.get('_account_loaded'):return
    force=st.button('重新檢查 Google Drive',key='account_check_now',help='重新讀取雲端版本，不會直接覆蓋此裝置未保存的修改。')
    st.caption('跨裝置同步 · 雲端版本 '+str(st.session_state.get('_account_revision','—')))
    if st.session_state.get('_account_conflict'):
        st.warning('跨裝置更新衝突，請到設定選擇保留版本。');return
    try:
        service=client()
        remote=(service.load if force else getattr(service,'load_if_changed',service.load))(st.session_state['_account_id'])
        st.session_state['_account_poll_at']=time.time()
        st.session_state.pop('_account_poll_error',None)
        if remote and remote['revision']!=st.session_state['_account_revision']:
            if digest(clean(snapshot()))!=st.session_state.get('_account_base'):
                st.session_state['_account_conflict']=remote['revision']
            else:st.session_state['_account_reload']=True
            st.rerun()
    except (CloudError,ValueError,KeyError,TypeError) as exc:
        st.session_state['_account_poll_error']=str(exc)
    if st.session_state.get('_account_poll_error'):
        st.warning('跨裝置更新暫停：'+st.session_state['_account_poll_error'])

def render_account():
    st.markdown('### Google 帳號與個人 Drive 保存')
    if not config():
        st.info('個人 Drive 保存尚未啟用；管理者需先完成 Google 登入與 Drive 設定。現有訪客功能仍可使用。')
        st.caption('管理者設定檔：account_setup/README.md；不需把帳密或金鑰貼到聊天中。')
        return
    if not st.session_state.get('_account_id'):
        st.caption('登入後，手機、電腦與不同瀏覽器可載入同一份私人名單、觀察名單及分析設定。Google 登入不等於 Yahoo 同步。')
        st.caption('資料保存在你的 Google Drive 隱藏 App 專用資料夾。App 伺服器仍會暫時處理資料；不使用集中式帳號資料庫。')
        render_login('drive_settings_login')
        return
    st.write('已登入：'+st.session_state['_account_user_name'])
    with st.expander('Google Drive 現在保存什麼？'):
        st.write('聯盟球隊與球員名單（含 IL、每日先發快照）、已同步的每週對手排程、已保存週比分與即時數據、星號觀察名單、9-Cat 母體與權重、交易偏好與評語，以及按「儲存模擬」保存的雙方七日排陣、每日數據套用、自訂預測與新增球員。')
        st.caption('保存於你自己的 Drive 隱藏 App 資料夾。Google／Yahoo 密鑰不放進紀錄；未按儲存的模擬編輯不會上傳。NBA 原始資料由網站提供，不會整份複製至個人 Drive。')
    render_logout()
    if st.session_state.get('_account_new'):
        st.info('帳號尚無資料。請選擇匯入本裝置既有紀錄，或建立新紀錄；未確認前不會自動上傳。')
        guest=st.session_state.get('_browser_guest_snapshot')
        if guest:
            files=guest.get('files',{});roster=files.get('league_rosters.json',{}).get('teams',{})
            st.caption(f"待匯入：{len(roster)} 隊、{sum(len(rs) for rs in roster.values())} 位球員；{len(files.get('league_results.json',{}).get('weeks',{}))} 週比賽紀錄。")
        if st.button('匯入此裝置既有紀錄',disabled=not bool(guest),key='account_import'):
            create_profile(guest)
        if st.button('建立新的帳號紀錄',key='account_new'):
            create_profile(snapshot())
    if st.session_state.get('_account_loaded'):
        st.caption('變更後自動保存至個人 Drive；其他裝置開著網站時每 5 秒檢查更新，無需配對連結或手動重新整理。手機在背景或鎖定時，更新可能暫停。')
    if st.session_state.get('_account_conflict'):
        st.warning('其他裝置已保存較新版本，目前不會覆寫。請先下載這台裝置的版本，再選擇保留哪一份。')
        st.download_button('下載此裝置待處理資料',json.dumps(snapshot(),ensure_ascii=False,indent=2),'account_unsaved.json','application/json')
        if st.button('載入雲端最新版本',key='account_load_remote'):
            st.session_state['_account_reload']=True;st.rerun()
        if st.button('以此裝置版本取代雲端',key='account_replace_remote'):
            persist_account(force_revision=st.session_state['_account_conflict']);st.rerun()
    if st.session_state.get('_account_save_error'):st.error(st.session_state['_account_save_error'])

def create_profile(payload):
    try:
        payload=clean(payload);revision=client().save(st.session_state['_account_id'],0,payload)
        st.session_state['_account_new']=False;apply_profile(payload,revision);st.rerun()
    except CloudConflict:
        st.session_state['_account_new']=False;st.session_state['_account_reload']=True;st.rerun()
    except (CloudError,ValueError,KeyError,TypeError) as exc:st.error('尚未建立帳號紀錄：'+str(exc))

def persist_account(force_revision=None):
    if not st.session_state.get('_account_loaded'):return
    if st.session_state.get('_account_conflict') and force_revision is None:return
    payload=clean(snapshot());hashed=digest(payload)
    if hashed==st.session_state.get('_account_base') and force_revision is None:return
    try:
        rev=force_revision if force_revision is not None else st.session_state['_account_revision']
        new=client().save(st.session_state['_account_id'],rev,payload)
        st.session_state['_account_revision']=new;st.session_state['_account_base']=hashed
        st.session_state.pop('_account_conflict',None);st.session_state.pop('_account_save_error',None)
    except CloudConflict:
        try:
            remote=client().load(st.session_state['_account_id'])
            st.session_state['_account_conflict']=remote['revision'] if remote else 0
        except CloudError:
            st.session_state['_account_conflict']=st.session_state['_account_revision']
            st.session_state['_account_save_error']='其他裝置已更新，暫時無法讀取新版本；本次修改尚未上傳。'
    except CloudError as exc:st.session_state['_account_save_error']=str(exc)

def finish_account():
    finish_auth()
    if not st.session_state.get('_account_id'):return
    try:persist_account()
    except (ValueError,KeyError,TypeError) as exc:st.session_state['_account_save_error']='資料未保存：'+str(exc)
    if st.session_state.get('_account_save_error'):st.error(st.session_state['_account_save_error'])
    elif st.session_state.get('_account_conflict'):st.warning('有跨裝置更新衝突，請到設定選擇保留版本。')
    elif st.session_state.get('_account_loaded'):
        st.caption('✓ Google Drive 已保存 · 版本 '+str(st.session_state.get('_account_revision','—'))+' · '+st.session_state.get('_account_user_name',''))
        if st.session_state.get('_account_poll_error'):st.warning('目前無法讀取其他裝置更新：'+st.session_state['_account_poll_error'])
