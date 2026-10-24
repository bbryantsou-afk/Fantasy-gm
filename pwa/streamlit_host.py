"""Optional beta front-end hosted by the existing Streamlit deployment.

Only this component renders in ?app=1. Calculations/auth stay server-side;
client navigation and editing stay inside the persistent front-end.
"""
import json,re,secrets
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import streamlit as st
import streamlit.components.v1 as components
from pwa.server import validate_profile,normalize_snapshot,normalize_results,simulator_status
ROOT=Path(__file__).resolve().parents[1]
frame=components.declare_component('fantasy_pwa',path=str(Path(__file__).parent/'web'))

@st.cache_data(show_spinner=False)
def public_model():
    from dashboard_model import regular_schedule
    data=json.loads((ROOT/'ninecat_assets/data.json').read_text())
    schedule,_=regular_schedule(json.loads((ROOT/'nba_schedule_2026_27.json').read_text()))
    return {'season':data['season'],'players':data['players'],'schedule':{t:sorted(map(str,days)) for t,days in schedule.items()}}

def dispatch(request):
    from google_drive_auth import config,make_flow
    from account_store import client,owner_id,signed_user
    from drive_profiles import CloudError,CloudConflict
    path=request.get('path','');method=request.get('method','GET');body=request.get('body')
    if method not in ('GET','POST') or not isinstance(path,str) or len(path)>1000:raise ValueError('操作格式不符')
    from urllib.parse import urlsplit,parse_qs,quote
    url=urlsplit(path);query=parse_qs(url.query);path=url.path
    if path=='/api/session' and method=='GET':
        c=config();return {'csrf':st.session_state.setdefault('_pwa_csrf',secrets.token_urlsafe(32)),'user':signed_user(),'googleConfigured':bool(c),'embedded':True,'league':st.session_state.get('_account_scope') if str(st.session_state.get('_account_scope','')).isdigit() else st.session_state.get('_league',{}).get('sync_league','')}
    if path=='/api/sim-status' and method=='GET':return simulator_status()
    if path=='/api/model' and method=='GET':return public_model()
    if path=='/api/login' and method=='POST':
        c=config()
        if not c:raise ValueError('目前網站尚未設定 Google 登入')
        lid=str((body or {}).get('league',''))
        if re.fullmatch(r'\d{1,10}',lid):st.query_params['league']=lid
        return {'flow':make_flow(c)}
    if path=='/api/logout':
        for key in list(st.session_state):
            if key.startswith(('_drive_','_account_')) or key in ('_league','_results'):st.session_state.pop(key,None)
        st.session_state['_drive_logged_out']=True
        return {'logout':True}
    if path=='/api/validate' and method=='POST':return {'payload':validate_profile(body)}
    if path=='/api/normalize-results' and method=='POST':return {'league':normalize_results(body['results'],body['current'])}
    if path=='/api/normalize' and method=='POST':return {'league':normalize_snapshot(body['snapshot'],body.get('current'))}
    if path=='/api/bookmark':
        c=config();base=c['redirect_uri'].rstrip('/') if c else 'http://localhost:'+str(st.get_option('server.port'))
        script=(ROOT/'mobile_roster_sync.js').read_text().replace('__PARSER__',(ROOT/'browser_sync_extension/parser.js').read_text()).replace('__APP_URL__',json.dumps(base+'/?app=1&phone_sync=1'))
        return {'bookmark':'javascript:'+quote('\n'.join(x for x in script.splitlines() if not x.strip().startswith('//')),safe="()!*'~-._")}
    if path=='/api/news':
        pid=query.get('player',[''])[0]
        p=next((p for p in public_model()['players'] if str(p['PLAYER_ID'])==pid),None)
        if not p:raise ValueError('找不到球員')
        from player_hub import player_news,translated_news,news_time
        return {'items':[dict(n,time=news_time(n['published'])) for n in translated_news(player_news(p['PLAYER_NAME']))]}
    if path=='/api/cloud':
        user=signed_user()
        if not user:raise PermissionError('請先登入 Google')
        lid=query.get('league',[''])[0] if method=='GET' else str(body.get('league',''))
        if not re.fullmatch(r'\d{1,10}',lid):raise ValueError('聯盟 ID 不符')
        service=client();service.NAME='fantasy-gm-league-'+lid+'-v1.json';owner=owner_id(user)
        if method=='GET':return {'profile':service.load(owner)}
        payload=validate_profile(body['payload']);recorded=payload['files'].get('league_rosters.json',{}).get('sync_league')
        if recorded and recorded!=lid:raise ValueError('聯盟不符，未保存')
        revision=body.get('revision')
        if type(revision) is not int or revision<0:raise ValueError('版本不符')
        return {'revision':service.save(owner,revision,payload)}
    raise ValueError('找不到此操作')

def render():
    st.markdown('''<style>
    [data-testid="stHeader"],[data-testid="stToolbarActions"],footer{display:none!important}
    [data-testid="stMainBlockContainer"]{padding:0!important;max-width:100%!important}
    iframe[title*="fantasy_pwa"]{position:fixed!important;inset:0!important;width:100vw!important;height:100dvh!important;border:0!important;z-index:1000!important;background:#f6f7f9}
    [data-stale="true"]{opacity:1!important}
    </style>''',unsafe_allow_html=True)
    response=st.session_state.get('_pwa_response')
    result=frame(response=response,key='independent_pwa_frontend',default=None)
    if isinstance(result,dict) and isinstance(result.get('id'),str) and result['id']!=st.session_state.get('_pwa_request_id'):
        st.session_state['_pwa_request_id']=result['id']
        try:
            if len(json.dumps(result))>4_100_000:raise ValueError('資料過大')
            value=dispatch(result);answer={'id':result['id'],'ok':True,'value':value}
        except PermissionError as exc:answer={'id':result['id'],'ok':False,'status':401,'error':str(exc)}
        except Exception as exc:
            from drive_profiles import CloudConflict,CloudError
            if isinstance(exc,CloudConflict):status=409;message='雲端已更新，請先讀取最新版本'
            elif isinstance(exc,CloudError):status=502;message='Drive 連線未完成，請稍後重試'
            elif isinstance(exc,(ValueError,KeyError,TypeError)):status=400;message='資料或操作格式不符，原紀錄保留'
            else:status=500;message='操作未完成，原紀錄保留'
            answer={'id':result['id'],'ok':False,'status':status,'error':message}
        st.session_state['_pwa_response']=answer;st.rerun()
    from google_drive_auth import finish_auth
    finish_auth()
