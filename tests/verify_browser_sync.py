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
scheduled=copy.deepcopy(payload)
scheduled['matchupSchedule']=[{'week':1,'start':'2026-10-20','end':'2026-10-25','pairs':[['1','2']]}]
with_schedule=apply_snapshot(league,rows,mapping,scheduled,date(2026,10,20))
checked=validate_backup(with_schedule,league['teams'])
assert checked['matchup_schedule']['weeks'][0]['opponents']=={'球隊 01':'球隊 02','球隊 02':'球隊 01'}
# Older extensions never erase a schedule already collected by a newer device.
assert apply_snapshot(with_schedule,rows,mapping,payload,date(2026,10,20))['matchup_schedule']==checked['matchup_schedule']
daily=copy.deepcopy(scheduled);daily['statsScope']='day'
from ninecat_model import KEYS
for t in daily['teams']:
 for r in t['rows']:r['daily_stats']=dict(dict.fromkeys(KEYS,0),PTS=5)
past=copy.deepcopy(daily);past['date']='2026-10-19';past.pop('matchupSchedule')
for t in past['teams']:t['date']=past['date']
daily['history']=[past]
raw_daily=validate_snapshot(daily,'7',date(2026,10,20),2);matched_daily,_=match_snapshot(raw_daily,players,[])
bundled=apply_snapshot(league,matched_daily,mapping,daily,date(2026,10,20))
assert set(bundled['daily_rosters'])=={'2026-10-19','2026-10-20'}
assert bundled['daily_rosters']['2026-10-20']['stats_scope']=='day'
assert bundled['daily_rosters']['2026-10-19']['teams']['球隊 01'][0]['daily_stats']['PTS']==5
# Older/mixed cached snapshots may advertise day scope but omit one row's stats.
legacy=copy.deepcopy(payload);legacy['statsScope']='day'
clean_rows=validate_snapshot(legacy,'7',date(2026,10,20),2)
assert all(r['daily_stats'] is None for r in clean_rows)
assert all(r['_daily_stats_missing'] for r in clean_rows)
assert all('daily_stats' not in r for t in legacy['teams'] for r in t['rows']) # no mutation of browser payload
legacy_matched,_=match_snapshot(clean_rows,players,[])
legacy_applied=apply_snapshot(league,legacy_matched,mapping,legacy,date(2026,10,20))
assert legacy_applied['daily_rosters']['2026-10-20']['teams']['球隊 01'][0]['daily_stats'] is None
for kind in ['missing','duplicate','date','league','position']:
 bad=copy.deepcopy(payload)
 if kind=='missing':bad['teams'].pop()
 if kind=='duplicate':bad['teams'][1]['rows'][0]['yahooPlayerId']='1'
 if kind=='date':bad['teams'][0]['date']='2026-10-19'
 if kind=='league':bad['league']='8'
 if kind=='position':bad['teams'][0]['rows'][0]['position']='UNKNOWN'
 try:validate_snapshot(bad,'7',date(2026,10,20),2);raise AssertionError(kind+' accepted')
 except ValueError:pass
# Abbreviated Yahoo names must share the NBA identity, while ambiguous initials stay unmatched.
from roster_import import match_rows
naw={'ID':'478.p.99','First Name':'N.','Last Name':'Alexander-Walker','Team ID':'478.l.7.t.1','Position':'SG','Eligible Positions':'PG,SG'}
naw_players=[{'PLAYER_ID':1629638,'PLAYER_NAME':'Nickeil Alexander-Walker','TEAM_ABBREVIATION':'ATL'}]
matched,_=match_rows([naw],naw_players,[])
assert matched[0]['id']=='1629638' and matched[0]['name']=='Nickeil Alexander-Walker' and matched[0]['matched']
ambiguous=naw_players+[{'PLAYER_ID':999,'PLAYER_NAME':'Nathan Alexander-Walker','TEAM_ABBREVIATION':'ATL'}]
assert not match_rows([naw],ambiguous,[])[0][0]['matched']
assert extension_zip().startswith(b'PK')
app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=60).run()
assert not any(t.value=='🏀 NBA Fantasy General Manager' for t in app.title)
assert any(e.label=='同步狀態／立即更新' for e in app.expander)
assert app.segmented_control(key='device_view').value in ['電腦版','手機版']
app.sidebar.radio[0].set_value('聯盟同步 League Sync').run();assert not app.exception,app.exception
assert any(x.label=='Yahoo 聯盟 ID' for x in app.text_input)
print('PASS complete league/date validation, unknown player, IL/BN, atomic historical snapshot, backup roundtrip, installer ZIP, sync UI')
