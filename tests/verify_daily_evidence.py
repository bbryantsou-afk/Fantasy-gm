import copy,sys
from pathlib import Path
from datetime import date
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from daily_evidence import observed_day,fantasy_period,simulator_defaults
from ninecat_model import KEYS
from league_settings import validate_backup
def row(pid,name,slot,pts):
 return {'id':pid,'name':name,'team':'SAS','eligible':['C'],'slot':slot,'status':'bench' if slot=='BN' else 'IL' if slot=='IL' else 'active','daily_stats':dict(dict.fromkeys(KEYS,0.),PTS=pts),'yahoo_id':'999' if pid is None else pid}
a=row('1','A','C',10);bench=row('2','Bench','BN',99);il=row('3','IL','IL',88);dropped=row('4','Dropped','C',20);rookie=row(None,'Rookie','Util',7)
league={'teams':{'A':[a,bench,il],'B':[]},'free':[],'capacity':14,'daily_rosters':{
 '2026-10-20':{'captured_at':'2026-10-21T03:02:00Z','stats_scope':'day','teams':{'A':[a,bench,il,dropped],'B':[]}},
 '2026-10-21':{'captured_at':'2026-10-21T03:02:00Z','stats_scope':'day','teams':{'A':[dict(a,slot='BN'),rookie],'B':[]}}}}
records,missing,source,_=fantasy_period(league,'A',date(2026,10,20),date(2026,10,21),date(2026,10,21))
assert sum(r['PTS'] for r in records)==37 and not missing
assert {r['PLAYER_NAME'] for r in records}=={'A','Dropped','Rookie'}
assert next(r for r in records if r['PLAYER_NAME']=='A')['GP']==1
pool,lineups=simulator_defaults(league,'A','B',[date(2026,10,20),date(2026,10,21)],{'my':[],'opp':[]})
assert lineups['2026-10-20']['my']=={'C1':'my-1','C2':'my-4'}
assert lineups['2026-10-21']['my']=={'UTIL1':'my-Rookie'}
assert {p['name'] for p in pool['my']}=={'A','Bench','Dropped','Rookie'}
clean=validate_backup(league,['A','B']);assert clean['daily_rosters']['2026-10-20']['stats_scope']=='day'
assert clean['daily_rosters']['2026-10-21']['teams']['A'][1]['daily_stats']['PTS']==7
_,missing,_,_=fantasy_period(league,'A',date(2026,10,22),date(2026,10,22),date(2026,10,22));assert missing==['2026-10-22']
# Different timezone offsets must not cause an older live snapshot to overwrite Yahoo.
live={'updated_at':'2026-10-21T11:01:00+08:00','players':{'1':{'PTS':1}}}
assert observed_day(league,'2026-10-20',live)['players']['1']['PTS']==10
live={'updated_at':'2026-10-21T11:03:00+08:00','players':{'1':{'PLAYER_ID':'1','PLAYER_NAME':'A','TEAM_ABBREVIATION':'SAS','GP':1,**dict(dict.fromkeys(KEYS,0.),PTS=12)}}}
updated=observed_day(league,'2026-10-20',live);assert updated['players']['1']['PTS']==12
records,_,_,_=fantasy_period(league,'A',date(2026,10,20),date(2026,10,20),date(2026,10,20),live)
assert sum(r['PTS'] for r in records)==32 # replacement, not 10+12
print('PASS dated starters, bench/IL exclusion, historical dropped players, rookie identity, missing dates, backup roundtrip and live replacement/timezones')
