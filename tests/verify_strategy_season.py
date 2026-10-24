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
