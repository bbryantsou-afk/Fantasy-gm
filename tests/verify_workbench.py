import sys,json
from pathlib import Path
from datetime import date,timedelta
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from team_workbench import lineup_week,SLOTS
from ninecat_model import CATS,KEYS
ref={c:{'mean':.5 if c in ('FG','FT') else 1,'std':1} for c in CATS}
weights={c:1 for c in CATS}
def player(i,position):
    return {'PLAYER_ID':i,'PLAYER_NAME':str(i),'team':'AAA','eligible':{position},**{k:1 for k in KEYS}}
day=date(2026,10,20)
pool={str(i):player(i,'C') for i in range(1,7)}
roster=[{'id':str(i),'name':str(i),'status':'active'} for i in range(1,7)]
out=lineup_week(roster,pool,{'AAA':{day}},[day],weights,ref)
assert out['g']==4 and out['tot']['PTS']==4
roster[0]['status']='IL'
out=lineup_week(roster,pool,{'AAA':{day}},[day],weights,ref)
assert '1' not in out['counts']
pool={str(i):player(i,p) for i,p in enumerate(['PG','SG','PG','SF','PF','SF','C','C','C','C','C'],1)}
roster=[{'id':str(i),'name':str(i),'status':'active'} for i in range(1,12)]
assert lineup_week(roster,pool,{'AAA':{day}},[day],weights,ref)['g']==10
print('PASS: slot limits, IL exclusion and full lineup')
