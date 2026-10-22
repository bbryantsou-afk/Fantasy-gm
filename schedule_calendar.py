"""Shared NBA weekly calendar, available independently of the simulator."""
from datetime import date,datetime,timedelta
from zoneinfo import ZoneInfo
import streamlit as st
from team_schedule import load_team_schedule
from matchup_schedule_summary import schedule_summary,CSS

def render_calendar():
    from nba_api.stats.static.teams import get_teams
    team_ids={t['abbreviation']:t['id'] for t in get_teams()}
    today=datetime.now(ZoneInfo('America/New_York')).date()
    day=st.date_input('選擇當週日期（美東）',value=max(date(2026,10,20),min(date(2027,4,11),today)),min_value=date(2026,10,19),max_value=date(2027,4,18),key='calendar_date')
    if day is None:return
    monday=day-timedelta(days=day.weekday());days=[monday+timedelta(days=i) for i in range(7)]
    mode=st.segmented_control('週曆顯示',['B2B','全部球隊出賽'],default='全部球隊出賽',required=True,key='calendar_mode')
    schedule=st.session_state.get('v15_live_schedule') or load_team_schedule()
    cards,calendar,_=schedule_summary(schedule,days,team_ids,all_games=mode=='全部球隊出賽')
    st.markdown(f'**{monday:%m/%d}–{days[-1]:%m/%d} · NBA 出賽週曆**')
    st.markdown(CSS,unsafe_allow_html=True)
    st.markdown(calendar,unsafe_allow_html=True)
    with st.expander('本週出賽最多',expanded=False):st.markdown(cards,unsafe_allow_html=True)
    with st.expander('週曆說明',expanded=False):st.caption('日期採美東；✓ 為有賽程，B2B 模式只標連續兩天出賽，* 為跨週。球隊有賽程不代表球員確定上場。使用與模擬對局相同的賽程快照。')
