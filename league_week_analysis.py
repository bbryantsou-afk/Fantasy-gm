"""League-wide nine-category comparisons; standard deviation is population SD."""
import json,math,statistics
from datetime import date,timedelta
from pathlib import Path
import streamlit as st
from ninecat_model import CATS,KEYS,LABELS

@st.cache_data(ttl=3600,show_spinner=False)
def appearances():
    from nba_api.stats.endpoints import leaguegamelog
    frame=leaguegamelog.LeagueGameLog(season='2026-27',season_type_all_star='Regular Season',player_or_team_abbreviation='P',timeout=18).get_data_frames()[0]
    return {(str(r['PLAYER_ID']),str(r['GAME_DATE'])[:10]) for r in frame.to_dict('records')}

def values(total,games=None):
    return {c:(total[c+'M']/total[c+'A'] if total.get(c+'A',0)>0 else None) if c in ('FG','FT') else (float(total.get(c,0))/games if games else None) if games is not None else float(total.get(c,0)) for c in CATS}

def summary(rows):
    result={}
    for c in CATS:
        nums=[r['values'][c] for r in rows if r['values'].get(c) is not None]
        result[c]={'mean':statistics.mean(nums) if nums else None,'std':statistics.pstdev(nums) if nums else None,'n':len(nums)}
    return result

def league_comparison(league,saved,key,played=None):
    records=[league.get('yahoo_matchups',{}).get(key),saved.get('weeks',{}).get(key)]
    record=max((r for r in records if r and r.get('teams')),key=lambda r:r.get('updated_at',''),default={})
    if not record:return {'totals':[],'per_game':[],'total_summary':{},'game_summary':{},'stamp':'','note':'此週尚無保存的全聯盟總數。'}
    start=date.fromisoformat(record.get('start',key));end=date.fromisoformat(record.get('end',str(start+timedelta(days=6))))
    error=''
    if played is None:
        try:played=appearances()
        except Exception:played=set();error='NBA 出賽場次暫時無法取得；不以預估場次作分母。'
    totals=[];per=[]
    for team,row in record['teams'].items():
        games=0;missing=[]
        for n in range((end-start).days+1):
            day=str(start+timedelta(days=n))
            if not any(d==day for _,d in played):continue
            roster=league.get('daily_rosters',{}).get(day,{}).get('teams',{}).get(team)
            if roster is None:missing.append(day);continue
            games+=sum(1 for p in roster if p.get('status')=='active' and p.get('slot') in ('PG','SG','G','SF','PF','F','C','Util','UTIL') and (str(p.get('id')),day) in played)
        gp=None if error or missing or not played else games
        totals.append({'team':team,'games':gp,'values':values(row['totals'])})
        per.append({'team':team,'games':gp,'values':values(row['totals'],gp or 0) if gp else dict.fromkeys(CATS,None)})
    return {'totals':totals,'per_game':per,'total_summary':summary(totals),'game_summary':summary(per),'stamp':record.get('updated_at',''),'note':error,'start':str(start),'end':str(end)}

def render_league_comparison(league,saved,key):
    from roster_store import team_label
    import pandas as pd
    with st.spinner('整理全聯盟九項與出賽場次…'):result=league_comparison(league,saved,key)
    st.subheader('全聯盟九項比較')
    if not result['totals']:st.info(result['note']);return
    st.caption('週數據保存時間：'+result['stamp'])
    for field,stats,title in [('totals','total_summary','各隊週總數'),('per_game','game_summary','各隊每球員出賽場次平均')]:
        st.markdown('**'+title+'**')
        def fmt(v,c):return '—' if v is None else f'{v:.2%}' if c in ('FG','FT') else round(v,3)
        rows=[{'球隊':team_label(r['team']),'場次':r['games'] if r['games'] is not None else '—',**{LABELS[c]:fmt(r['values'][c],c) for c in CATS}} for r in result[field]]
        for stat,label in [('mean','聯盟平均'),('std','標準差')]:rows.append({'球隊':label,'場次':'—',**{LABELS[c]:fmt(result[stats][c][stat],c) for c in CATS}})
        st.dataframe(pd.DataFrame(rows),hide_index=True,width='stretch',height='auto')
    st.caption('場次＝當週每日先發球員的實際 NBA 出賽場次；板凳與 IL 不計。FG／FT 始終為總命中÷總出手，不再除以場次。平均與標準差跨球隊等權計算，採母體標準差；缺資料不當作 0。')
    if result['note']:st.warning(result['note'])
