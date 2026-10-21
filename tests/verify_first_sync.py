import sys,os
from pathlib import Path
os.environ['FANTASY_GM_STORAGE_MODE']='session'
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
from streamlit.testing.v1 import AppTest
script='''
import sys
sys.path.insert(0,ROOT)
import streamlit as st
from datetime import datetime
from zoneinfo import ZoneInfo
import league_sync
entries=[{'fantasyTeam':t,'name':n,'playerId':i,'position':'(SAS - C)'} for i,t,n in [(1,'A','One'),(2,'B','Two')]]
players=[{'PLAYER_ID':i,'PLAYER_NAME':n,'TEAM_ABBREVIATION':'SAS'} for i,n in [(1,'One'),(2,'Two')]]
league_sync.load_data=lambda:({'players':players},entries)
league_sync.phone_bridge=lambda **k:None
league_sync.bridge=lambda **k:st.session_state.pop('incoming',None)
st.session_state['_sync_requested_league']='7'
if 'seeded' not in st.session_state:
 today=str(datetime.now(ZoneInfo('America/New_York')).date())
 snapshot={'schema':1,'league':'7','date':today,'capturedAt':datetime.now().astimezone().isoformat(),'teams':[{'id':str(i),'name':n,'date':today,'rows':[{'yahooPlayerId':str(i),'name':n,'position':'C','eligible':['C'],'nbaTeam':'SAS'}]} for i,n in [(1,'One'),(2,'Two')]]}
 st.session_state['incoming']={'snapshot':snapshot,'mapping':{'7:1':'A','7:2':'B'}}
 st.session_state['seeded']=True
league_sync.render_sync_connection(full=False)
'''.replace('ROOT',repr(str(root)))
a=AppTest.from_string(script,default_timeout=60).run();assert not a.exception,a.exception
assert any(b.label=='確認隊伍配對並完成首次同步' for b in a.button) # extension mapping cannot bypass first confirmation
# A widget/page rerun must not lose the pending snapshot.
a.run();assert not a.exception,a.exception
next(b for b in a.button if b.label=='確認隊伍配對並完成首次同步').click().run()
assert not a.exception,a.exception
assert a.session_state['_league']['sync_mapping']=={'7:1':'A','7:2':'B'}
assert a.session_state['_league']['daily_rosters']
print('PASS desktop compact first confirmation, pending snapshot across reruns and complete dated roster apply')
