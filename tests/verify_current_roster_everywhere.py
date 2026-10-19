"""Regression: a cached Yahoo roster must replace draft seeds before every page reads it."""
import os,sys,json,copy
from pathlib import Path
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
from unittest.mock import patch
os.environ['FANTASY_GM_STORAGE_MODE']='session'
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from streamlit.testing.v1 import AppTest
from ninecat_model import norm
players=json.loads((ROOT/'ninecat_assets/data.json').read_text())['players']
entries=json.loads((ROOT/'ninecat_assets/draft.json').read_text())['entries']
byname={norm(p['PLAYER_NAME']):p for p in players}
# Synthetic 16-player / 3-IL fixture; no user's private current roster is published.
expected=[(p['PLAYER_NAME'],'IL' if i>=11 else 'BN' if i>=9 else 'PG',p['TEAM_ABBREVIATION']) for i,p in enumerate(players[:14])]
expected += [('New Rookie Alpha','BN','OKC'),('New Rookie Beta','BN','ATL')]
expected_names={n for n,_,_ in expected};normal={norm(n) for n in expected_names}
day=datetime.now(ZoneInfo('America/New_York')).date().isoformat()
seed={}
for e in entries:seed.setdefault(e['fantasyTeam'],[]).append(e)
local=list(seed);mapping={'71585:14':local[0]};teams=[];counter=0
for i,t in enumerate(local):
 source='14' if i==0 else str(i)
 mapping['71585:'+source]=t
 src=expected if i==0 else [(e['name'],'BN','BOS') for e in seed[t] if norm(e['name']) not in normal]
 rows=[]
 for name,slot,nba in src:
  counter+=1;rows.append({'yahooPlayerId':str(700000+counter),'name':name,'position':slot,'eligible':['C'] if slot=='C' else ['PG'] if slot=='PG' else ['SF'],'nbaTeam':nba})
 teams.append({'id':source,'name':'Test team '+source,'date':day,'rows':rows})
payload={'schema':1,'league':'71585','date':day,'capturedAt':datetime.now(timezone.utc).isoformat(),'teams':teams}
result={'snapshot':payload,'mapping':mapping}
def capture_component(*args,**kwargs):
 def capture(**values):
  import streamlit as st
  st.session_state['sim_capture']=values['data']
 return capture
with patch('league_sync.bridge',return_value=result),patch('streamlit.components.v2.component',side_effect=capture_component):
 app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=90).run()
 for page in ['總覽 Dashboard','球員觀察室 Player Watch','每週補強 Weekly Planner','交易分析 Trade Lab','9-Cat Strategy','模擬對局 Matchup Simulator','Matchup Simulator Lite']:
  app.sidebar.radio[0].set_value(page).run()
  assert not app.exception,(page,app.exception)
  current=app.session_state['_league']['teams'][local[0]]
  assert {r['name'] for r in current}==expected_names,(page,[r['name'] for r in current])
  assert sum(r['status']=='IL' for r in current)==3
  assert app.session_state['_league']['roster_sources'][local[0]]['kind']=='yahoo'
  assert any('名單來源：Yahoo 同步' in c.value for c in app.caption)
  if page=='球員觀察室 Player Watch':assert len([b for b in app.button if b.label.startswith('⋯ 展開')])==16
  if page=='9-Cat Strategy':assert len(app.session_state['nc_roster'])==16
  if page in ['模擬對局 Matchup Simulator','Matchup Simulator Lite']:
   names={r['name'] for r in app.session_state['sim_capture']['players']['my']}
   assert {'New Rookie Alpha','New Rookie Beta'}<=names and len(names)==13
   assert not {n for n,slot,_ in expected if slot=='IL'} & names
 # New cloud session restores via the global receiver even without entering League Sync.
 fresh=AppTest.from_file(str(ROOT/'app.py'),default_timeout=90).run()
 assert len(fresh.session_state['_league']['teams'][local[0]])==16
print('PASS synthetic 16-player roster / 3 IL across all seven features, simulator new rookies, new-session restore and visible Yahoo provenance')
