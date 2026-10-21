import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from live_espn import parse_box
from daily_evidence import observed_day,fantasy_period
from datetime import date
labels=['MIN','PTS','FG','3PT','FT','REB','AST','TO','STL','BLK']
p={'athlete':{'id':'900','displayName':'Ausar Thompson'},'stats':['12','9','4-5','0-0','1-2','8','2','1','1','0'],'didNotPlay':False}
d={'header':{'id':'1','competitions':[{'date':'2026-10-21T00:00Z','status':{'type':{'completed':False}}}]},'boxscore':{'players':[{'team':{'abbreviation':'DET'},'statistics':[{'labels':labels,'athletes':[p,dict(p,didNotPlay=True)]}]}]}}
players=parse_box(d,'2026-10-20','2026-10-21T01:00Z',{})
assert len(players)==1 and players['espn:900']['PTS']==9
row={'id':'1630703','name':'Ausar Thompson','team':'DET','slot':'SF'}
league={'daily_rosters':{'2026-10-20':{'captured_at':'2026-10-21T00:00Z','teams':{'A':[row]}}}}
live={'players':players,'updated_at':'2026-10-21T01:00Z','source':'ESPN 即時暫存'}
e=observed_day(league,'2026-10-20',live);assert e['players']['1630703']['PTS']==9
r,missing,_,_=fantasy_period(league,'A',date(2026,10,20),date(2026,10,20),date(2026,10,20),live)
assert len(r)==1 and r[0]['PTS']==9 and not missing
finals={};d['header']['competitions'][0]['status']['type']['completed']=True
live['players']=parse_box(d,'2026-10-20','2026-10-21T01:00Z',finals)
row['daily_stats']=dict(players['espn:900'],PTS=7)
# A stale Yahoo snapshot cannot override a game just observed final.
assert observed_day(league,'2026-10-20',live)['players']['1630703']['PTS']==9
league['daily_rosters']['2026-10-20']['captured_at']='2026-10-21T01:01Z'
assert observed_day(league,'2026-10-20',live)['players']['1630703']['PTS']==7
try:parse_box(d,'2026-10-19','',{})
except ValueError:pass
else:raise AssertionError('date mismatch')
print('PASS ESPN provider identity, full nine-cat, DNP exclusion, Fantasy starters, final Yahoo precedence and date validation')
# Yesterday's boxscore must count for every Fantasy team after Eastern midnight.
from ninecat_model import KEYS
second={'id':'2','name':'Second Player','team':'BOS','slot':'PG'}
league['daily_rosters']['2026-10-20']['teams']['B']=[second]
live['players']['espn:901']={'PLAYER_ID':'espn:901','PLAYER_NAME':'Second Player','TEAM_ABBREVIATION':'BOS','GP':1,**dict.fromkeys(KEYS,0.),'PTS':22}
dated={'by_date':{'2026-10-20':live}}
for team,expected in [('A',7),('B',22)]:
 rows,_,_,_=fantasy_period(league,team,date(2026,10,20),date(2026,10,21),date(2026,10,21),dated)
 assert sum(r['PTS'] for r in rows)==expected,(team,rows)
print('PASS both Fantasy teams retain prior-day totals after midnight')
from daily_evidence import unverified_period
fresh={'teams':{'A':[row]}}
refs=unverified_period(fresh,'A',date(2026,10,20),date(2026,10,20),date(2026,10,21),dated['by_date'])
assert len(refs)==1 and refs[0]['PTS']==9
counted,missing,_,_=fantasy_period(fresh,'A',date(2026,10,20),date(2026,10,20),date(2026,10,21),dated)
assert not counted and missing==['2026-10-20']
assert not unverified_period(league,'A',date(2026,10,20),date(2026,10,20),date(2026,10,21),dated['by_date'])
print('PASS first-use NBA reference totals visible without inventing Fantasy starters or points')
