from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from league_week_analysis import league_comparison
from ninecat_model import KEYS
z=dict.fromkeys(KEYS,0)
a={**z,'PTS':20,'FGM':5,'FGA':10};b={**z,'PTS':40,'FGM':8,'FGA':10}
l={'yahoo_matchups':{'2026-10-19':{'start':'2026-10-19','end':'2026-10-25','teams':{'A':{'totals':a},'B':{'totals':b}}}},'daily_rosters':{'2026-10-20':{'teams':{'A':[{'id':'1','status':'active','slot':'PG'}],'B':[{'id':'2','status':'active','slot':'C'},{'id':'3','status':'IL','slot':'IL'}]}}}}
played={('1','2026-10-20'),('2','2026-10-20'),('3','2026-10-20')}
r=league_comparison(l,{},'2026-10-19',played)
assert r['total_summary']['PTS']['mean']==30
assert r['total_summary']['PTS']['std']==10
assert r['per_game'][1]['games']==1
assert r['game_summary']['FG']['mean']==.65
l['daily_rosters']['2026-10-20']['teams'].pop('B')
r=league_comparison(l,{},'2026-10-19',played)
assert r['per_game'][1]['games'] is None and r['per_game'][1]['values']['PTS'] is None
assert r['game_summary']['PTS']['n']==1
assert not league_comparison({}, {},'2026-10-19',played)['totals']
print('PASS totals, equal-team means, population SD, starter-only actual appearances, missing data and absent week')
