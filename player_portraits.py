"""Name-based NBA portraits, independent of fantasy roster identity."""
import json,re
from pathlib import Path
from functools import lru_cache

def name_key(name):return re.sub(r'[^a-z0-9]','',str(name).lower())

@lru_cache(maxsize=1)
def portrait_ids():
    out={}
    for file in ('data.json','data_2026_27.json'):
        for p in json.loads((Path(__file__).parent/'ninecat_assets'/file).read_text()).get('players',[]):
            out[name_key(p['PLAYER_NAME'])]=str(p['PLAYER_ID'])
    return out

def portrait_id(player):
    return portrait_ids().get(name_key(player.get('name') or player.get('PLAYER_NAME',''))) or str(player.get('nba_id') or player.get('id') or player.get('PLAYER_ID') or '')
