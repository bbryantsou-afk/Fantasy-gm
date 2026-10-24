import sys,json
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from strategy_season import strategy_snapshot
from ninecat_model import KEYS,baseline
strategy_snapshot.clear()
with patch('player_detail_v14.league_stats',side_effect=RuntimeError('offline')):
    current=strategy_snapshot('2026-27')
assert current['season']=='2026-27' and len(current['players'])>300
assert all(p['GP']>0 and all(k in p for k in KEYS) for p in current['players'])
assert strategy_snapshot('2025-26')['season']=='2025-26'
assert baseline(current['players'],{str(p['PLAYER_ID']) for p in current['players']})['n']>0
print('PASS official current season snapshot, complete category counts, baseline and season-separated fallback')

from strategy_season import blended_players
logs=[{'PLAYER_ID':1,'PLAYER_NAME':'A','TEAM_ABBREVIATION':'ATL','GAME_ID':str(i),'GAME_DATE':f'2026-03-{i+1:02d}','PTS':i,'FGM':1,'FGA':2} for i in range(30)]
cur=[{'PLAYER_ID':1,'PLAYER_NAME':'A','GP':2,'PTS':100,'FGM':10,'FGA':20}]
x=blended_players(logs+[logs[-1]],cur)[0]
assert x['GP']==27 and x['PREV_GP']==25 and x['CURRENT_GP']==2
assert abs(x['PTS']-(sum(range(5,30))+100)/27)<1e-9
assert x['FGM']/x['FGA']==.5
assert blended_players([],cur)[0]['PTS']==50
assert blended_players(logs,[])[0]['GP']==25
print('PASS last 25 actual appearances plus exact current totals, duplicates, rookie and no-current-games cases')
