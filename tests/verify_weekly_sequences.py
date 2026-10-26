"""Dated transactions, manual layouts, planned adds, IL returns, and immutable history."""
import copy,sys
from pathlib import Path
from datetime import date,timedelta
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from rotation_planner import rotation_workflow
from ninecat_model import KEYS,CATS,baseline
START=date(2026,10,26);DAYS=[START+timedelta(days=i) for i in range(7)]
def profile(key,team,pos='PG',points=10):
 return {'PLAYER_ID':key,'PLAYER_NAME':key,'GP':30,'TEAM_ABBREVIATION':team,'team':team,'eligible':{pos},**dict.fromkeys(KEYS,1.),'PTS':points,'FGA':2.,'FTA':2.}
pool={k:profile(k,t,points=pts) for k,t,pts in [('old','OLD',2),('a','A',20),('b','B',25),('c','C',30),('enemy','ENEMY',40)]}
def row(k,status='active'):return {'id':k,'name':k,'team':pool[k]['team'],'eligible':['PG'],'status':status}
league={'teams':{'mine':[row('old')],'other':[row('enemy')]},'capacity':1,'free':['a','b','c'],'daily_rosters':{}}
schedule={'OLD':set(),'A':set(DAYS[:2]),'B':set(DAYS[2:4]),'C':set(DAYS[4:]),'ENEMY':set(DAYS)}
ref=baseline(list(pool.values()),set(pool));weights=dict.fromkeys(CATS,0.);weights['PTS']=1.
def run(**kwargs):return rotation_workflow(kwargs.pop('league',league),pool,kwargs.pop('schedule',schedule),'mine','other',kwargs.pop('start',START),kwargs.pop('drops',['old']),kwargs.pop('remaining',3),ref,weights,**kwargs)
original=copy.deepcopy(league)
r=run();assert r['sequences']
p=r['sequences'][0]
assert p['adds']<=3 and p['remaining']==3-p['adds']
assert len({x['date'] for x in p['steps']})>=2,p
assert [x['add'] for x in p['steps']]==['a','b','c'],p
held={'old'}
for d in DAYS:
 for step in (x for x in p['steps'] if x['date']==str(d)):
  if step['drop']:assert step['drop'] in held;held.remove(step['drop'])
  if step['add']:assert step['add'] not in held;held.add(step['add'])
 assert len(held)<=1
 for player in next(x for x in p['calendar'] if x['date']==str(d))['lineup']:assert player['id'] in held
assert league==original

def layout():return {'format':'fantasy-gm-simulation','version':1,'selected_day':0,'context':{'season':'2026-27','my_team':'mine','opp_team':'other'},'week_dates':list(map(str,DAYS)),'players':{'my':[dict(row('old'),id='my-old',nba_id='old')],'opp':[dict(row('enemy'),id='opp-enemy',nba_id='enemy')]},'lineups':[{'my':{},'opp':{'PG':'opp-enemy'}} for _ in DAYS],'daily_choices':{'my':{},'opp':{}}}
l=layout();r=run(layout=l);assert all(not slots for slots in r['before']['lineups'].values())
# A UTIL vacancy admits a C too; named PG-only vacancy cannot.
pool['center']=profile('center','C','C',100)
l['players']['my'].append({'id':'my-a','nba_id':'a','name':'a','team':'A','eligible':['PG'],'added':True,'acquired_date':str(DAYS[1])})
l['lineups'][1]['my']['UTIL1']='my-a'
r=run(layout=l,remaining=2)
assert len(r['planned_adds'])==1 and r['sequences']
for p in r['sequences']:
 fixed=[s for s in p['steps'] if s.get('planned')];assert len(fixed)==1 and fixed[0]['add']=='a' and fixed[0]['date']==str(DAYS[1])
 assert not any(x['id']=='a' for x in p['calendar'][0]['lineup'])
 assert p['adds']<=2
 assert all(len({x['id'] for x in day['lineup']})==len(day['lineup']) for day in p['calendar'])
assert run(layout=l,remaining=0)['issues']
# Adding someone from another fantasy team never turns them into a free agent.
bad=layout();bad['players']['my'].append({'id':'my-e','nba_id':'enemy','name':'enemy','eligible':['PG'],'added':True})
assert run(layout=bad)['issues'] and not run(layout=bad)['sequences']
# An IL return requires a release at that date, with no add charged for the release.
pool['injured']=profile('injured','C','PG',30)
inj=copy.deepcopy(league);inj['teams']['mine'].append(row('injured','IL'))
l=layout();l['players']['my'].append({'id':'my-injured','nba_id':'injured','name':'injured','team':'C','eligible':['PG'],'status':'IL'})
for i in range(4,7):l['lineups'][i]['my']['PG']='my-injured'
r=run(league=inj,layout=l)
assert r['returns']['injured']==str(DAYS[4])
assert r['sequences'],r
for p in r['sequences']:
 releases=[x for x in p['steps'] if x.get('release_only')]
 assert releases and releases[0]['date']==str(DAYS[4]),p
 assert p['adds']==sum(x['add'] is not None for x in p['steps'])
 for entry in p['calendar'][:4]:assert not any(x['id']=='injured' for x in entry['lineup'])
# Historical roster/stats stay exact even if the current roster and manual layout differ.
old=copy.deepcopy(league);actual=dict.fromkeys(KEYS,4.);old['daily_rosters'][str(DAYS[0])]={'teams':{'mine':[{'id':'historic','name':'historic','slot':'PG','status':'active','daily_stats':actual}]}}
r=run(league=old,start=DAYS[1]);assert r['days'][0]['rows'][0]['id']=='historic'
assert all(x['date']>=str(DAYS[1]) for p in r['sequences'] for x in p['steps'])
# Wrong-week saved layouts must never take over the selected week.
l=layout();l['week_dates']=[str(d-timedelta(days=7)) for d in DAYS]
assert run(layout=l)['before']==run()['before']
print('PASS multi-day chained adds, no future backfill, budget, manual slots, UTIL flexibility, fixed planned adds, IL return release, ownership, historical roster and no writes')

locked=copy.deepcopy(league);locked['daily_rosters'][str(START)]={'teams':{'mine':[{**row('old'),'slot':'PG','daily_stats':dict.fromkeys(KEYS,3.)}]}}
r=run(league=locked)
assert r['before']['lineups'][str(START)][0]['PTS']==3
for plan in r['sequences']:
 assert all(s['date']>str(START) for s in plan['steps'] if s['drop']=='old')
 assert plan['calendar'][0]['lineup'][0]['id']=='old'
print('PASS started roster/stat line preserved and cannot be dropped on its locked day')

l=layout();l['players']['my'].append({'id':'my-c','nba_id':'c','name':'c','team':'C','eligible':['PG'],'added':True,'acquired_date':str(DAYS[4])})
l['lineups'][4]['my']['UTIL1']='my-c'
r=run(layout=l,remaining=1)
assert r['sequences']
assert all(p['adds']==1 and p['steps'][0]['add']=='c' and p['steps'][0]['date']==str(DAYS[4]) for p in r['sequences'])
r=run(pregame_teams=set())
assert all(not p['calendar'][0]['lineup'] for p in r['sequences'])
print('PASS reserve quota for later planned adds and exclude already-started free agents today')

l=layout();l['players']['my'].append({'id':'my-injured','nba_id':'injured','name':'injured','team':'C','eligible':['PG'],'status':'IL'})
for i in range(4,7):l['lineups'][i]['my']['PG']='my-injured'
r=run(league=inj,layout=l,remaining=0)
assert r['sequences'] and all(p['adds']==0 for p in r['sequences'])
assert all(any(s.get('release_only') for s in p['steps']) for p in r['sequences'])
print('PASS IL activation releases remain available even with zero adds')

locked_two=copy.deepcopy(locked);locked_two['capacity']=2
r=run(league=locked_two,pregame_teams={'A','B','C','ENEMY'})
assert r['sequences']
for p in r['sequences']:
 assert p['calendar'][0]['lineup'][0]['id']=='old'
print('PASS started positions stay reserved before filling new streamer slots')
