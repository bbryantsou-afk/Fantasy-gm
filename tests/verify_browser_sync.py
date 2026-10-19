import os,sys,copy,json
from datetime import date,datetime,timezone
from pathlib import Path
os.environ['FANTASY_GM_STORAGE_MODE']='session'
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from league_sync import validate_snapshot,match_snapshot,apply_snapshot,extension_zip
from league_settings import validate_backup
from streamlit.testing.v1 import AppTest
payload={'schema':1,'league':'7','date':'2026-10-20','capturedAt':datetime.now(timezone.utc).isoformat(),'teams':[]}
for i,name in enumerate(['Jimmy Butler III','Unknown Rookie'],1):
 payload['teams'].append({'id':str(i),'name':'Private '+str(i),'date':'2026-10-20','rows':[{'yahooPlayerId':str(i),'name':name,'position':'IL' if i==1 else 'BN','eligible':['SF'],'nbaTeam':'GSW'}]})
players=[{'PLAYER_ID':123,'PLAYER_NAME':'Jimmy Butler III','TEAM_ABBREVIATION':'GSW'}]
league={'teams':{'球隊 01':[],'球隊 02':[]},'free':[],'capacity':14,'revision':0}
raw=validate_snapshot(payload,'7',date(2026,10,20),2);rows,_=match_snapshot(raw,players,[])
assert rows[0]['id']=='123' and rows[0]['slot']=='IL' and rows[1]['id'] is None
mapping={'7:1':'球隊 01','7:2':'球隊 02'}
new=apply_snapshot(league,rows,mapping,payload,date(2026,10,20))
assert new['teams']['球隊 01'][0]['status']=='IL' and new['teams']['球隊 02'][0]['status']=='bench'
assert not league['teams']['球隊 01']
assert new['team_names']=={'球隊 01':'Private 1','球隊 02':'Private 2'}
renamed=copy.deepcopy(rows);renamed[0]['source_name']='Renamed Club'
assert apply_snapshot(new,renamed,mapping,payload,date(2026,10,20))['team_names']['球隊 01']=='Renamed Club'
old=apply_snapshot(league,rows,mapping,payload,date(2026,10,21))
assert old['teams']==league['teams'] and old['daily_rosters']['2026-10-20']['teams']==new['teams']
restored=validate_backup(new,league['teams']);assert restored['daily_rosters']==new['daily_rosters'] and restored['sync_mapping']==mapping
assert restored['team_names']==new['team_names']
for kind in ['missing','duplicate','date','league','position']:
 bad=copy.deepcopy(payload)
 if kind=='missing':bad['teams'].pop()
 if kind=='duplicate':bad['teams'][1]['rows'][0]['yahooPlayerId']='1'
 if kind=='date':bad['teams'][0]['date']='2026-10-19'
 if kind=='league':bad['league']='8'
 if kind=='position':bad['teams'][0]['rows'][0]['position']='UNKNOWN'
 try:validate_snapshot(bad,'7',date(2026,10,20),2);raise AssertionError(kind+' accepted')
 except ValueError:pass
assert extension_zip().startswith(b'PK')
app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=60).run()
app.sidebar.radio[0].set_value('聯盟同步 League Sync').run();assert not app.exception,app.exception
assert any(x.label=='Yahoo 聯盟 ID' for x in app.text_input)
print('PASS complete league/date validation, unknown player, IL/BN, atomic historical snapshot, backup roundtrip, installer ZIP, sync UI')
