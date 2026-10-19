"""Local league preferences and portable private backups."""
import json,copy
import streamlit as st
from ninecat_strategy import load_data
from roster_store import state,persist,identity

def validate_backup(data,teams,allow_history=True):
    if not isinstance(data,dict) or set(data.get('teams',{}))!=set(teams):raise ValueError('備份的聯盟球隊不符。')
    cap=data.get('capacity',14)
    if type(cap) is not int or not 10<=cap<=25:raise ValueError('名單席次必須介於10至25。')
    seen=set()
    for rows in data['teams'].values():
        if not isinstance(rows,list) or len(rows)>cap+3:raise ValueError('名單大小不符。')
        if any(not isinstance(r,dict) for r in rows):raise ValueError('球員資料不完整。')
        if sum(r.get('status')=='IL' for r in rows)>3:raise ValueError('IL 超過3席。')
        if sum(r.get('status')!='IL' for r in rows)>cap:raise ValueError('一般席次超額。')
        for r in rows:
            if not isinstance(r,dict) or not isinstance(r.get('name'),str) or not r['name'].strip():raise ValueError('球員資料不完整。')
            if r.get('status','active') not in ('active','IL','bench'):raise ValueError('球員狀態不符。')
            if r.get('eligible') and (not isinstance(r['eligible'],list) or any(p not in ['PG','SG','SF','PF','C'] for p in r['eligible'])):raise ValueError('位置資格不符。')
            k=identity(r)
            if k in seen:raise ValueError('同一球員出現在兩份名單。')
            seen.add(k)
    free=data.get('free',[])
    if not isinstance(free,list) or any(not isinstance(k,str) or k in seen for k in free):raise ValueError('自由球員與球隊名單衝突。')
    meta=data.get('player_meta',{})
    if not isinstance(meta,dict):raise ValueError('球員位置設定不符。')
    for k,v in meta.items():
        if not isinstance(k,str) or not isinstance(v,dict) or not isinstance(v.get('eligible',[]),list) or any(p not in ['PG','SG','SF','PF','C'] for p in v.get('eligible',[])):raise ValueError('球員位置設定不符。')
        if not isinstance(v.get('team',''),str) or len(v.get('team',''))>3:raise ValueError('NBA 隊伍格式不符。')
    output={'player_meta':copy.deepcopy(meta),'teams':copy.deepcopy(data['teams']),'free':list(set(free)),'capacity':cap,'revision':int(data.get('revision',0))}
    if allow_history and data.get('daily_rosters'):
        from datetime import date
        archives=data['daily_rosters']
        if not isinstance(archives,dict) or len(archives)>370:raise ValueError('日期快照格式不符。')
        clean={}
        for day,archive in archives.items():
            date.fromisoformat(day)
            if not isinstance(archive,dict) or not isinstance(archive.get('captured_at'),str):raise ValueError('快照資料不完整。')
            checked=validate_backup({'teams':archive.get('teams'),'capacity':cap,'free':[]},teams,False)
            clean[day]={'teams':checked['teams'],'captured_at':archive['captured_at'],'source':'Yahoo browser snapshot'}
        output['daily_rosters']=clean
        for key in ['sync_league','sync_mapping','sync_updated_at']:output[key]=copy.deepcopy(data.get(key))
    return output

def render_league_settings():
    snapshot,entries=load_data()
    from roster_import import render_import
    render_import(snapshot['players'],entries)
    data=state(entries)
    with st.expander('聯盟名單與備份',expanded=False):
        cap=st.number_input('一般名單席次（另有 3 個 IL）',10,25,int(data['capacity']),key='league_capacity')
        if st.button('儲存席次'):
            largest=max(sum(r.get('status')!='IL' for r in rows) for rows in data['teams'].values())
            if cap<largest:st.error(f'目前有隊伍使用 {largest} 席，請先調整名單。')
            else:data['capacity']=cap;persist(data);st.success('已更新。')
        st.download_button('下載我的聯盟備份',json.dumps(data,ensure_ascii=False,indent=2),'league_rosters.json','application/json')
        uploaded=st.file_uploader('還原聯盟備份',type=['json'],key='league_restore_file')
        if uploaded and st.button('確認還原共用名單'):
            try:
                restored=validate_backup(json.loads(uploaded.getvalue()),data['teams'])
                st.session_state['_league']=restored;persist(restored);st.rerun()
            except (ValueError,TypeError,KeyError) as exc:st.error('無法還原：'+str(exc))
        st.caption('每位雲端訪客各自保存於目前工作階段；重要變更請下載備份。這裡的修改不會提交 Yahoo。')
