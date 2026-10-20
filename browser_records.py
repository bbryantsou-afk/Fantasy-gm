"""Explicit browser-local recovery of non-credential user records."""
import copy,json
from pathlib import Path
from datetime import date
import streamlit as st
import streamlit.components.v1 as components
from app_storage import private_path
from profile_preferences import preference_key,validate_preferences,capture_preferences
ROOT=Path(__file__).parent
FILES={'league_rosters.json','league_results.json','player_watchlist.json','ninecat_state.json','trade_preferences.json','trade_feedback.json'}
bridge=components.declare_component('browser_records',path=str(ROOT/'browser_records'))

def validate_records(snapshot,entries):
    if not isinstance(snapshot,dict) or snapshot.get('schema')!=1 or len(json.dumps(snapshot))>4_000_000:raise ValueError('瀏覽器備份格式不符。')
    files=snapshot.get('files',{})
    if not isinstance(files,dict) or set(files)-FILES:raise ValueError('瀏覽器備份含未知檔案。')
    files=copy.deepcopy(files)
    teams=list(dict.fromkeys(e['fantasyTeam'] for e in entries))
    if 'league_rosters.json' in files:
        from league_settings import validate_backup
        files['league_rosters.json']=validate_backup(files['league_rosters.json'],teams)
    if 'league_results.json' in files:
        from data_center import checked_week,validate_totals
        results=files['league_results.json']
        if not isinstance(results,dict) or not isinstance(results.get('weeks'),dict) or not isinstance(results.get('days'),dict):raise ValueError('比賽備份格式不符。')
        for key,w in results['weeks'].items():
            date.fromisoformat(key)
            checked_week([{'team':t,'opponent':r['opponent'],**r['totals']} for t,r in w['teams'].items()],teams)
            if type(w.get('final')) is not bool:raise ValueError('結算狀態不符。')
        for day,d in results['days'].items():
            date.fromisoformat(day)
            if set(d['totals'])!=set(teams):raise ValueError('比賽隊伍不符。')
            for r in d['totals'].values():validate_totals(r)
    for name,value in files.items():
        if not isinstance(value,(dict,list)):raise ValueError('備份內容不符。')
    prefs=validate_preferences(snapshot.get('prefs',{}),teams)
    return files,prefs

def restore_browser_records():
    result=bridge(mode='read',namespace=st.session_state.get('_account_id','guest'),key='browser_records_reader',default=None)
    if st.session_state.get('_browser_records_ready') or not isinstance(result,dict):return
    if not result.get('ready'):
        st.warning('瀏覽器保存不可用，請使用一般模式並允許網站儲存，或下載備份。');return
    if st.session_state.get('_account_id'):
        guest=result.get('guestSnapshot')
        if guest:
            try:
                from ninecat_strategy import load_data
                _,entries=load_data();files,prefs=validate_records(guest,entries)
                st.session_state['_browser_guest_snapshot']={'schema':1,'files':files,'prefs':prefs}
            except (ValueError,KeyError,TypeError):pass
        st.session_state['_browser_records_ready']=True
        return
    snapshot=result.get('snapshot')
    if snapshot:
        try:
            from ninecat_strategy import load_data
            _,entries=load_data();files,prefs=validate_records(snapshot,entries)
            # Shared links always use the shared server copy; never overwrite it with an older browser copy.
            shared=bool(st.query_params.get('mobile') or st.session_state.get('_mobile_share_token'))
            for name,data in files.items():
                if shared and name in ('league_rosters.json','league_results.json'):continue
                path=private_path(ROOT/name)
                if path.exists():continue  # Keep records already saved in this live session.
                path.write_text(json.dumps(data,ensure_ascii=False))
                if name=='league_rosters.json':st.session_state['_league']=data
                if name=='league_results.json':st.session_state['_results']=data
            st.session_state['_portable_preferences']=copy.deepcopy(prefs)
            for key,value in prefs.items():
                if key=='visual_theme' and st.query_params.get('theme'):continue
                st.session_state[key]=value
        except (ValueError,KeyError,TypeError,OSError) as exc:
            st.warning('瀏覽器紀錄尚未還原：'+str(exc));return
    st.session_state['_browser_records_ready']=True

def save_browser_records():
    if not st.session_state.get('_browser_records_ready'):return
    files={}
    for name in FILES:
        try:files[name]=json.loads(private_path(ROOT/name).read_text())
        except (ValueError,OSError):pass
    if '_league' in st.session_state:files['league_rosters.json']=st.session_state['_league']
    if '_results' in st.session_state:files['league_results.json']=st.session_state['_results']
    prefs=capture_preferences(st.session_state)
    bridge(mode='write',namespace=st.session_state.get('_account_id','guest'),enabled=True,snapshot={'schema':1,'files':files,'prefs':prefs},key='browser_records_writer',default=None)
