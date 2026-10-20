import os,sys,json
from pathlib import Path
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
os.environ['FANTASY_GM_STORAGE_MODE']='session'
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from streamlit.testing.v1 import AppTest
script='''
import sys,copy
sys.path.insert(0,ROOT_PATH)
import streamlit as st
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
from ninecat_strategy import load_data
from roster_store import state
from ninecat_model import KEYS
from daily_evidence import player_key
import daily_evidence
daily_evidence.nba_today=lambda day:{'players':{},'updated_at':'','error':'fixture offline','statuses':[]}
today=datetime.now(ZoneInfo('America/New_York')).date()
_,entries=load_data();league=state(entries);team=list(league['teams'])[0]
if 'seeded' not in st.session_state:
 r=copy.deepcopy(league['teams'][team][0]);r.update(slot='C',status='active',daily_stats=dict(dict.fromkeys(KEYS,0.),PTS=8,FGM=4,FGA=6))
 league['daily_rosters']={str(today):{'teams':{team:[r]},'stats_scope':'day','captured_at':datetime.now().astimezone().isoformat()}}
 st.session_state['seeded']=True
from dashboard_overview import render_dashboard
render_dashboard()
'''.replace('ROOT_PATH',repr(str(ROOT)))
a=AppTest.from_string(script,default_timeout=60).run();assert not a.exception,a.exception
assert a.selectbox(key='dash_season').value=='2026-27'
today=datetime.now(ZoneInfo('America/New_York')).date()
assert a.date_input[0].value==today
table=next(t.value for t in a.dataframe if '狀態' in t.value.columns)
assert table.iloc[0]['PTS']==8 and table.iloc[0]['場次']==1
assert any('Yahoo 單日實績' in c.value for c in a.caption)
a.radio(key='dash_range').set_value('單日').run();assert not a.exception,a.exception
assert next(t.value for t in a.dataframe if '狀態' in t.value.columns).iloc[0]['PTS']==8
print('PASS dashboard defaults to current season/today and shows synced in-progress Fantasy starter production despite NBA outage')
