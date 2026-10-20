"""Validated Yahoo weekly pairings, retained with the league roster profile."""
import copy
from datetime import date

def validate_schedule(value,teams):
    if not isinstance(value,dict) or not isinstance(value.get('weeks'),list) or len(value['weeks'])>40:raise ValueError('對戰排程格式不符。')
    out={'source':'Yahoo browser snapshot','captured_at':str(value.get('captured_at',''))[:80],'league':str(value.get('league',''))[:10],'weeks':[]}
    seen=set();previous=None
    for w in sorted(value['weeks'],key=lambda w:w['week']):
        n=w['week'];start=date.fromisoformat(w['start']);end=date.fromisoformat(w['end'])
        if type(n) is not int or not 1<=n<=40 or n in seen or not 0<=(end-start).days<=20 or (previous and start<=previous):raise ValueError('對戰週日期重疊或週次不符。')
        seen.add(n);previous=end;pairs=w.get('opponents')
        if not isinstance(pairs,dict) or any(t not in teams or o not in teams or t==o or pairs.get(o)!=t for t,o in pairs.items()):raise ValueError('對手配對不完整或不互相對應。')
        out['weeks'].append({'week':n,'start':str(start),'end':str(end),'opponents':copy.deepcopy(pairs)})
    return out

def import_schedule(raw,mapping,league,captured):
    weeks=[]
    if not isinstance(raw,list):raise ValueError('Yahoo 對戰排程格式不符。')
    for w in raw:
        pairs={}
        for a,b in w.get('pairs',[]):
            ta=mapping.get(league+':'+str(a));tb=mapping.get(league+':'+str(b))
            if not ta or not tb or ta in pairs or tb in pairs:raise ValueError('Yahoo 對戰隊伍重複或未配對。')
            pairs[ta]=tb;pairs[tb]=ta
        weeks.append({'week':w['week'],'start':w['start'],'end':w['end'],'opponents':pairs})
    return validate_schedule({'league':league,'captured_at':captured,'weeks':weeks},list(mapping.values()))

def week_for(league,day):
    return next((w for w in league.get('matchup_schedule',{}).get('weeks',[]) if w['start']<=str(day)<=w['end']),None)

def render_schedule(league):
    import streamlit as st
    from roster_store import team_label
    schedule=league.get('matchup_schedule',{})
    st.caption('Yahoo 每週對手排程；同步名單時一併讀取，未公布的季後賽不猜測。')
    if not schedule.get('weeks'):
        st.info('尚未取得對戰表。請更新同步工具，再到「聯盟同步」按同步。');return
    st.caption('來源：Yahoo · 最後同步 '+schedule.get('captured_at',''))
    team=st.selectbox('查看球隊',list(league['teams']),format_func=team_label,key='ds_schedule_team')
    st.dataframe([{'週次':w['week'],'開始':w['start'],'結束':w['end'],'對手':team_label(w['opponents'][team]) if team in w['opponents'] else '尚未公布／輪空'} for w in schedule['weeks']],hide_index=True,width='stretch')
