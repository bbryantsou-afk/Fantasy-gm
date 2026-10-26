"""Render the four-stage planner on both device layouts without private data/network."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from streamlit.testing.v1 import AppTest
SCRIPT='''
import streamlit as st,json
from pathlib import Path
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
from unittest.mock import patch
from weekly_planner import render_planner
rows=json.loads(Path('ninecat_assets/data.json').read_text())['players']
today=datetime.now(ZoneInfo('America/New_York')).date();monday=today-timedelta(days=today.weekday())
def r(p):return {'id':str(p['PLAYER_ID']),'name':p['PLAYER_NAME'],'team':p['TEAM_ABBREVIATION'],'eligible':['PG','SG','SF','PF','C'],'status':'active','games':1}
a=[r(p) for p in rows[:4]];b=[r(p) for p in rows[4:8]]
a[-1]['status']='IL'
st.session_state['_league']={'teams':{'A':a,'B':b},'capacity':14,'free':[str(rows[10]['PLAYER_ID'])],'revision':1,'daily_rosters':{str(monday+timedelta(days=i)):{'teams':{'A':[],'B':[]}} for i in range(7)},'matchup_schedule':{'weeks':[{'week':2,'start':str(monday),'end':str(monday+timedelta(days=6)),'opponents':{'A':'B','B':'A'}}]}}
st.session_state['_my_team']='A'
with patch('daily_evidence.nba_today',return_value={'players':{},'scheduled_teams':[],'error':'','updated_at':''}),patch('daily_evidence.refresh_live_page'):
 render_planner()
'''
for device in ['手機版','電腦版']:
 app=AppTest.from_string(SCRIPT,default_timeout=90)
 app.session_state['device_view']=device
 app.run()
 assert not app.exception,app.exception
 assert any(x.label=='哪一週' for x in app.selectbox)
 assert not any(x.label=='本週對手' for x in app.selectbox)
 assert any('整週補強流程' in x.value for x in app.markdown)
 print('PASS four-stage planner, automatic opponent, full IL roster picker and embedded simulator:',device)
