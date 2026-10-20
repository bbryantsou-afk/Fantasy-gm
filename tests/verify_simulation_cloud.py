import os,sys,copy
from pathlib import Path
from unittest.mock import patch
os.environ['FANTASY_GM_STORAGE_MODE']='session'
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from matchup_records import validate_simulations
from fantasy_schedule import import_schedule,week_for,validate_schedule
from account_store import CloudConflict
from streamlit.testing.v1 import AppTest
payload={'format':'fantasy-gm-simulation','version':1,'week_dates':['2026-10-'+str(i) for i in range(19,26)],
 'players':{'my':[{'id':'my-1','name':'Player One','eligible':['C'],'stats':{'PTS':20}}],'opp':[]},
 'lineups':[{'my':{'C1':'my-1'},'opp':{}} for i in range(7)],'daily_choices':{'my':{},'opp':{}},'selected_day':1,
 'context':{'season':'2026-27','my_team':'球隊 01','opp_team':'球隊 02'}}
records={'Week 1':payload};assert validate_simulations(records)==records
for mutate in [lambda p:p['lineups'][0]['my'].update(PG='my-1'),lambda p:p['players']['my'][0]['stats'].update(PTS=float('nan')),lambda p:p['week_dates'].__setitem__(3,'2026-10-31')]:
 bad=copy.deepcopy(payload);mutate(bad)
 try:validate_simulations({'bad':bad});raise AssertionError('invalid simulation accepted')
 except ValueError:pass
mapping={'7:1':'A','7:2':'B'}
schedule=import_schedule([{'week':1,'start':'2026-10-20','end':'2026-10-25','pairs':[['1','2']]},{'week':2,'start':'2026-10-26','end':'2026-11-01','pairs':[]}],mapping,'7','now')
assert week_for({'matchup_schedule':schedule},'2026-10-21')['opponents']=={'A':'B','B':'A'}
assert week_for({'matchup_schedule':schedule},'2026-10-26')['opponents']=={}
assert week_for({'matchup_schedule':schedule},'2026-11-02') is None
bad=copy.deepcopy(schedule);bad['weeks'][0]['opponents']['B']='B'
try:validate_schedule(bad,['A','B']);raise AssertionError('self opponent accepted')
except ValueError:pass
class Profiles:
 def __init__(self):self.row={'revision':1,'payload':{'schema':1,'files':{},'prefs':{}}}
 def load(self,owner):return copy.deepcopy(self.row)
 def save(self,owner,revision,payload):
  if revision!=self.row['revision']:raise CloudConflict('stale')
  self.row={'revision':revision+1,'payload':copy.deepcopy(payload)};return revision+1
db=Profiles();user={'iss':'https://accounts.google.com','sub':'simulation-test'}
script='''
import sys
sys.path.insert(0,ROOT_PATH)
import streamlit as st
from account_store import init_account,poll_account,finish_account
from matchup_records import load,save
init_account();poll_account()
if 'incoming' in st.session_state:save(st.session_state.pop('incoming'))
st.json(load());finish_account()
'''.replace('ROOT_PATH',repr(str(ROOT)))
with patch('account_store.config',return_value={'configured':True}),patch('account_store.init_auth'),patch('account_store.client',return_value=db),patch('account_store.signed_user',return_value=user):
 desktop=AppTest.from_string(script,default_timeout=60).run();phone=AppTest.from_string(script,default_timeout=60).run()
 desktop.session_state['incoming']=records;desktop.run();assert not desktop.exception,desktop.exception
 assert db.row['payload']['files']['simulations.json']==records
 phone.run();assert not phone.exception,phone.exception
 import json
 assert json.loads(phone.json[0].value)==records
 phone.session_state['incoming']={};phone.run();desktop.run()
 assert json.loads(desktop.json[0].value)=={}
print('PASS simulator validation, full named-save cloud roundtrip and deletion across two sessions; known, unknown and missing weekly opponents')

# Exercise the actual simulator event bridge, not just its storage helper.
script='''
import sys
sys.path.insert(0,ROOT_PATH)
import streamlit as st
from nba_api.stats.endpoints import leaguedashplayerstats,scoreboardv2
def offline(*a,**k):raise RuntimeError('offline fixture')
leaguedashplayerstats.LeagueDashPlayerStats=offline
scoreboardv2.ScoreboardV2=offline
from account_store import init_account,finish_account
init_account()
def component(*args,**kwargs):
 def render(**values):
  st.session_state['board_data']=values['data']
  return st.session_state.pop('board_event',{})
 return render
st.components.v2.component=component
from matchup_simulator_v15 import render_matchup_simulator
render_matchup_simulator(lite=st.session_state.get('lite',False));finish_account()
'''.replace('ROOT_PATH',repr(str(ROOT)))
with patch('account_store.config',return_value={'configured':True}),patch('account_store.init_auth'),patch('account_store.client',return_value=db),patch('account_store.signed_user',return_value=user):
 board=AppTest.from_string(script,default_timeout=60).run();assert not board.exception,board.exception
 board.session_state['board_event']={'simulation_change':{'records':records,'active':payload,'name':'Week 1'}}
 board.run();assert not board.exception,board.exception
 assert db.row['payload']['files']['simulations.json']==records
 board.session_state['lite']=True;board.run();assert not board.exception,board.exception
 assert board.session_state['board_data']['saved_simulations']==records
 board.selectbox(key='sim_open_name').set_value('Week 1').run()
 next(b for b in board.button if b.key=='sim_open_saved').click().run()
 assert not board.exception,board.exception
 assert board.session_state['board_data']['restore']==payload
print('PASS actual simulator save event → Drive profile, desktop/Lite shared records and named restore')
