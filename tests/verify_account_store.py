import os,sys,copy
from pathlib import Path
from unittest.mock import patch
os.environ['FANTASY_GM_STORAGE_MODE']='session'
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from streamlit.testing.v1 import AppTest
from ninecat_strategy import load_data
from account_store import owner_id,CloudError,CloudConflict,CloudClient
_,entries=load_data();teams=list(dict.fromkeys(e['fantasyTeam'] for e in entries))
A={'iss':'https://accounts.google.com','sub':'verified-sub-a','name':'Test A'}
B={'iss':'https://accounts.google.com','sub':'verified-sub-b','name':'Test B'}
assert owner_id(A)!=owner_id(B)
assert owner_id(dict(A,email='a@example.test'))==owner_id(dict(A,email='changed@example.test'))
for bad in [{},{'iss':'fake','sub':'verified-sub-a'}]:
 try:owner_id(bad);raise AssertionError('bad issuer accepted')
 except CloudError:pass
class FakeDB:
 def __init__(self):self.rows={};self.fail=False;self.writes=0
 def load(self,owner):
  if self.fail:raise CloudError('offline')
  return copy.deepcopy(self.rows.get(owner))
 def save(self,owner,revision,payload):
  if self.fail:raise CloudError('offline')
  current=self.rows.get(owner,{}).get('revision',0)
  if current!=revision:raise CloudConflict('conflict')
  self.rows[owner]={'revision':current+1,'payload':copy.deepcopy(payload),'updated_at':'test'};self.writes+=1
  return current+1
payload={'schema':1,'files':{'league_rosters.json':{'teams':{t:[] for t in teams},'team_names':{teams[0]:'Only account A'},'free':[],'capacity':14,'revision':1}},'prefs':{'_my_team':teams[0],'nc_weight_STL':1.0}}
db=FakeDB();db.save(owner_id(A),0,payload)
current=A
with patch('account_store.config',return_value={'configured':True}),patch('account_store.init_auth'),patch('account_store.client',return_value=db),patch('account_store.signed_user',side_effect=lambda:current):
 a=AppTest.from_file(str(ROOT/'app.py'),default_timeout=60).run();assert not a.exception,a.exception
 assert a.session_state['_league']['team_names'][teams[0]]=='Only account A'
 a.session_state['nc_weight_STL']=2.;a.run();assert not a.exception,a.exception
 assert db.rows[owner_id(A)]['payload']['prefs']['nc_weight_STL']==2.
 # Another browser for the same account receives the saved weights.
 same=AppTest.from_file(str(ROOT/'app.py'),default_timeout=60).run();assert not same.exception,same.exception
 assert same.session_state['nc_weight_STL']==2.
 # B cannot load A's profile and gets explicit first-use choices.
 current=B
 b=AppTest.from_file(str(ROOT/'app.py'),default_timeout=60).run();assert not b.exception,b.exception
 assert b.session_state['_account_new'] and not b.session_state.get('_account_loaded',False)
 assert 'Only account A' not in b.session_state['_league'].get('team_names',{}).values()
 assert any(x.label=='建立新的帳號紀錄' for x in b.button)
 guest=copy.deepcopy(payload);guest['files']['league_rosters.json']['team_names'][teams[0]]='Explicit guest import'
 b.session_state['_browser_guest_snapshot']=guest;b.run()
 next(x for x in b.button if x.label=='匯入此裝置既有紀錄').click().run();assert not b.exception,b.exception
 assert db.rows[owner_id(B)]['payload']['files']['league_rosters.json']['team_names'][teams[0]]=='Explicit guest import'
 assert db.rows[owner_id(A)]['payload']['files']['league_rosters.json']['team_names'][teams[0]]=='Only account A'
 # Deliberately stale A edits must not overwrite a newer remote revision.
 current=A;db.rows[owner_id(A)]['revision']+=1
 db.rows[owner_id(A)]['payload']['prefs']['nc_weight_STL']=1.2
 a.session_state['nc_weight_STL']=1.8;a.run();assert not a.exception,a.exception
 assert a.session_state['_account_conflict']
 assert db.rows[owner_id(A)]['payload']['prefs']['nc_weight_STL']==1.2
 # Offline save retains local edits and surfaces an error.
 db.fail=True;same.session_state['nc_weight_STL']=1.9;same.run();assert not same.exception,same.exception
 assert same.session_state['_account_save_error']=='offline'
 assert same.session_state['nc_weight_STL']==1.9
print('PASS verified-sub identity, account isolation, same-account reload, first-use consent, stale-write prevention and offline retention (mock profile store)')

from profile_preferences import capture_preferences,hydrate_preferences
state={'nc_weight_STL':1.7,'nc_ref_draft':['1641705']}
capture_preferences(state);state.pop('nc_weight_STL');state.pop('nc_ref_draft')
assert capture_preferences(state)['nc_weight_STL']==1.7
hydrate_preferences(state);assert state['nc_ref_draft']==['1641705']
print('PASS portable preference shadow survives widget cleanup and page changes')
