import os,sys,copy
from pathlib import Path
from unittest.mock import patch
os.environ['FANTASY_GM_STORAGE_MODE']='session'
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from ninecat_strategy import load_data
from browser_records import validate_records
from streamlit.testing.v1 import AppTest
_,entries=load_data();teams=list(dict.fromkeys(e['fantasyTeam'] for e in entries))
rows={t:[] for t in teams}
for e in entries:
 if not rows[e['fantasyTeam']]:rows[e['fantasyTeam']]=[{'id':str(e['playerId']),'name':e['name'],'status':'active','eligible':['C'],'team':'SAS'}]
league={'teams':rows,'free':[],'capacity':14,'revision':12,'team_names':{teams[0]:'Restored club'}}
snapshot={'schema':1,'files':{'league_rosters.json':league,'league_results.json':{'weeks':{},'days':{}},'player_watchlist.json':{'ids':['1641705']}},'prefs':{'_my_team':teams[0],'nc_weight_STL':1.5,'yahoo_access_token':'never restore'}}
files,prefs=validate_records(snapshot,entries);assert 'yahoo_access_token' not in prefs
bad=copy.deepcopy(snapshot);bad['files']['../secrets.toml']={}
try:validate_records(bad,entries);raise AssertionError('unsafe filename accepted')
except ValueError:pass
with patch('browser_records.bridge',side_effect=lambda **kw:{'ready':True,'snapshot':snapshot} if kw.get('mode')=='read' else None):
 for _ in range(2):
  app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=60).run()
  assert not app.exception,app.exception
  assert app.session_state['_league']['team_names'][teams[0]]=='Restored club'
  assert len(app.session_state['_league']['teams'][teams[0]])==1
  assert app.session_state['nc_weight_STL']==1.5
  assert app.session_state['_browser_records_ready']
print('PASS browser backup validation, new-session restoration, roster/results/preferences, credential exclusion and filename allowlist')
