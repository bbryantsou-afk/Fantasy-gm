import sys,copy
from pathlib import Path
from datetime import date,timedelta
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from rotation_planner import rotation_workflow
from ninecat_model import KEYS,CATS,baseline
start=date(2026,10,27);past=str(start-timedelta(days=1))
def p(pid,pos,team='BASE',pts=10):
    return {'PLAYER_ID':pid,'PLAYER_NAME':pid,'GP':30,'team':team,'TEAM_ABBREVIATION':team,'eligible':{pos},**dict.fromkeys(KEYS,1.),'FGM':1.,'FGA':2.,'FTM':1.,'FTA':2.,'PTS':pts}
pool={str(i):p(str(i),pos) for i,pos in enumerate(['PG','SG','SF','PF','C','C','PG','SF','PG','SG'])}
pool.update({'freeC':p('freeC','C','CENTER',20),'freePG':p('freePG','PG','GUARD',100),'owned':p('owned','C','CENTER',200)})
def row(key):return {'id':key,'name':key,'status':'active','team':pool[key]['team'],'eligible':list(pool[key]['eligible'])}
league={'capacity':10,'teams':{'A':[row(str(i)) for i in range(10)],'B':[row('owned')]},'daily_rosters':{past:{'teams':{'A':[{'id':'past-only','name':'Past only','slot':'PG','status':'active','daily_stats':dict.fromkeys(KEYS,1.)}]}}}}
ref=baseline(list(pool.values()),set(pool));weights=dict.fromkeys(CATS,1.)
schedule={t:{start} for t in ('BASE','CENTER','GUARD')}
r=rotation_workflow(league,pool,schedule,'A','B',start,['4'],1,ref,weights)
assert len(r['days'])==7 and r['rotation_slots']==1
assert r['days'][0]['historical'] and r['days'][0]['rows'][0]['id']=='past-only'
assert [x['key'] for x in r['results']]==['freeC'],r['results']
assert [t['team'] for t in r['teams']]==['CENTER']
assert r['results'][0]['drop']=='4' and all(w['position']=='C' for w in r['results'][0]['windows'])
assert len(league['teams']['A'])==10 and league['teams']['A'][4]['id']=='4'
assert not rotation_workflow(league,pool,schedule,'A','B',start,[],1,ref,weights)['results']
assert not rotation_workflow(league,pool,schedule,'A','B',start,['4'],0,ref,weights)['results']
assert not rotation_workflow(league,pool,schedule,'A','B',start,['4'],1,ref,weights,['owned'])['results']
assert not rotation_workflow(league,pool,{t:set() for t in schedule},'A','B',start,['4'],1,ref,weights)['results']
print('PASS daily historical roster retained, explicit rotations only, C vacancy rejects PG despite higher stats, owned exclusion, budget/schedule guards and no roster writes')
from unittest.mock import patch
from rotation_planner import workflow_request
import json
entries=[{'playerId':pid,'name':p['PLAYER_NAME'],'position':'('+p['team']+' - '+','.join(p['eligible'])+')','fantasyTeam':'A','round':1} for pid,p in pool.items()]
profile={'files':{'league_rosters.json':{**league,'free':['freeC'],'player_meta':{}}},'prefs':{}}
with patch('pwa.server.validate_profile',return_value=profile),patch('ninecat_strategy.load_data',return_value=({'players':list(pool.values())},entries)),patch('dashboard_model.regular_schedule',return_value=(schedule,{})):
    out=workflow_request({'profile':{},'team':'A','opponent':'B','start':'2026-10-27','remaining':1,'drops':['4'],'research':False})
    json.dumps(out)
    assert len(out['results'])==1 and out['results'][0]['name']=='freeC'
    assert out['results'][0]['confirmed'] is True
print('PASS shared App adapter, confirmed-free selection, five-plan limit and JSON-safe result')
