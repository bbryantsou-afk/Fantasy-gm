"""Same Google identity, independent league tabs and legacy migration."""
import sys,copy
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import streamlit as st
from streamlit.testing.v1 import AppTest
from account_store import CloudConflict,owner_id
from ninecat_strategy import load_data
_,entries=load_data();teams=list(dict.fromkeys(e['fantasyTeam'] for e in entries))
user={'iss':'https://accounts.google.com','sub':'multi-league-test','name':'Test'}
owner=owner_id(user)
def payload(league,weight):
 return {'schema':1,'files':{'league_rosters.json':{'teams':{t:[] for t in teams},'free':[],'capacity':14,'revision':1,'sync_league':league,'daily_rosters':{'2026-10-20':{'teams':{t:[] for t in teams},'captured_at':'test'}}},'player_watchlist.json':{'stars':[league]}},'prefs':{'nc_weight_STL':weight}}
rows={('fantasy-gm-profile-v1.json',owner):{'revision':7,'payload':payload('71585',1)}}
class Fake:
 NAME='fantasy-gm-profile-v1.json'
 def __init__(self,*args):pass
 def load(self,owner):return copy.deepcopy(rows.get((self.NAME,owner)))
 def save(self,owner,revision,payload):
  key=self.NAME,owner;current=rows.get(key,{}).get('revision',0)
  if revision!=current:raise CloudConflict('stale')
  rows[key]={'revision':current+1,'payload':copy.deepcopy(payload)}
  return current+1
script="""
import streamlit as st
from account_store import init_account,persist_account,create_profile
init_account()
if st.session_state.get('_account_new'):
 from ninecat_strategy import load_data
 _,entries=load_data();teams=list(dict.fromkeys(e['fantasyTeam'] for e in entries))
 create_profile({'schema':1,'files':{'league_rosters.json':{'teams':{t:[] for t in teams},'free':[],'capacity':14,'revision':1,'sync_league':st.session_state['_account_scope'],'daily_rosters':{'2026-10-20':{'teams':{t:[] for t in teams},'captured_at':'test'}}}},'prefs':{'nc_weight_STL':1}})
if st.button('edit'):
 st.session_state['nc_weight_STL']=2
 from matchup_records import save
 save({'W1':{'format':'fantasy-gm-simulation','version':1,'week_dates':['2026-10-'+str(i) for i in range(19,26)],'players':{'my':[],'opp':[]},'lineups':[{'my':{},'opp':{}} for i in range(7)],'daily_choices':{'my':{},'opp':{}},'selected_day':0}})
persist_account()
st.write(st.session_state.get('nc_weight_STL'))
"""
with patch('account_store.config',return_value={'configured':True}),patch('account_store.init_auth'),patch('account_store.signed_user',return_value=user),patch('account_store.CloudClient',Fake):
 a=AppTest.from_string(script).run();assert not a.exception,a.exception
 assert a.query_params['league'] in ('71585',['71585'])
 assert a.session_state['_account_scope']=='71585'
 assert rows[('fantasy-gm-profile-v1.json',owner)]['revision']==7
 b=AppTest.from_string(script);b.query_params['league']='99999';b.run();assert not b.exception,b.exception
 assert b.session_state['_league']['sync_league']=='99999'
 b.button[0].click().run();assert not b.exception,b.exception
 a.run();assert not a.exception,a.exception
 assert a.session_state['nc_weight_STL']==1
 assert 'simulations.json' not in rows[('fantasy-gm-league-71585-v1.json',owner)]['payload']['files']
 assert rows[('fantasy-gm-league-99999-v1.json',owner)]['payload']['prefs']['nc_weight_STL']==2
 same=AppTest.from_string(script);same.query_params['league']='99999';same.run();assert not same.exception,same.exception
 assert same.session_state['nc_weight_STL']==2
 assert 'W1' in rows[('fantasy-gm-league-99999-v1.json',owner)]['payload']['files']['simulations.json']
 b.query_params['league']='71585';b.run();assert not b.exception,b.exception
 assert b.session_state['nc_weight_STL']==1 and b.session_state['_league']['sync_league']=='71585'
print('PASS same-account league separation, same-league reload, legacy copy without modifying original, tab scope reset')
