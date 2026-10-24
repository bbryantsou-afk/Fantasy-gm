import sys,copy
from pathlib import Path
from datetime import date
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from daily_roster_archive import store_day
from ninecat_model import KEYS
teams={'A':[{'id':'1','name':'One','slot':'G','status':'active','daily_stats':dict(dict.fromkeys(KEYS,0),PTS=10)}], 'B':[{'id':'2','name':'Two','slot':'BN','status':'bench','daily_stats':None}]}
a=store_day(None,teams,'2026-10-23','2026-10-23T08:12:00Z',date(2026,10,23),3)
assert a['roster_state']=='provisional'
nextday=copy.deepcopy(teams);nextday['A'][0]['slot']='Util'
b=store_day(a,nextday,'2026-10-23','2026-10-24T12:00:00Z',date(2026,10,24),3)
assert b['roster_state']=='final' and b['teams']['A'][0]['slot']=='Util'
changed=copy.deepcopy(teams);changed['A'][0]['slot']='BN';changed['A'][0]['daily_stats']['PTS']=11
c=store_day(b,changed,'2026-10-23','2026-10-25T12:00:00Z',date(2026,10,25),3)
assert c['teams']['A'][0]['slot']=='Util' and c['teams']['A'][0]['status']=='active'
assert c['teams']['A'][0]['daily_stats']['PTS']==11
assert c['teams']['B'][0]['slot']=='BN'
assert b['teams']['A'][0]['daily_stats']['PTS']==10
assert store_day(None,teams,'2026-10-23','2026-10-24T02:00:00Z',date(2026,10,24),3)['roster_state']=='provisional' # still Oct 23 in New York
assert store_day(None,teams,'2026-10-23','2026-10-24T12:00:00Z',date(2026,10,24),0)['roster_state']=='provisional'
from league_settings import validate_backup
profile={'teams':teams,'free':[],'capacity':14,'daily_rosters':{'2026-10-23':b}}
clean=validate_backup(profile,['A','B'])
assert clean['daily_rosters']['2026-10-23']['roster_state']=='final'
assert clean['daily_rosters']['2026-10-23']['roster_verified_at']==b['roster_verified_at']
print('PASS provisional day, next-day Yahoo confirmation, immutable slots/bench, stat correction, ET boundary and cloud validation')
