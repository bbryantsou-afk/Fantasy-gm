"""Independent strategy season data; never replaces other features' baselines."""
import json
from pathlib import Path
from datetime import date, timedelta
import streamlit as st
ROOT=Path(__file__).parent

def blended_players(logs,current):
    from ninecat_model import KEYS
    by={}
    for row in logs:
        by.setdefault(str(row['PLAYER_ID']),{})[str(row['GAME_ID'])]=row
    now={str(r['PLAYER_ID']):r for r in current}
    out=[]
    for pid in sorted(set(by)|set(now)):
        recent=sorted(by.get(pid,{}).values(),key=lambda r:(r['GAME_DATE'],str(r['GAME_ID'])),reverse=True)[:25]
        cur=now.get(pid,{})
        gp=len(recent)+int(cur.get('GP',0))
        if not gp:continue
        meta=cur or recent[0]
        row={k:meta.get(k) for k in ('PLAYER_ID','PLAYER_NAME','TEAM_ABBREVIATION')}
        row.update(GP=gp,PREV_GP=len(recent),CURRENT_GP=int(cur.get('GP',0)))
        for k in [*KEYS,'MIN']:
            row[k]=(sum(float(r.get(k) or 0) for r in recent)+float(cur.get(k) or 0))/gp
        out.append(row)
    return out

@st.cache_data(show_spinner=False)
def official_2026_data():
    assets = ROOT / 'ninecat_assets'
    season = json.loads((assets / 'matchup_2026_27.json').read_text())
    games = json.loads((assets / 'matchup_game_logs_2026_27.json').read_text())
    return season, games


def totals_from_games(season, games, end, days=None):
    from ninecat_model import KEYS
    start = (end - timedelta(days=days - 1)).isoformat() if days else ''
    end_date = end.isoformat()
    indexes = {key: games['fields'].index(key) for key in KEYS}
    metadata = {row['PLAYER_ID']: row for row in season['players']}
    players = {}
    for game in games['rows']:
        player_id, game_date = game[:2]
        if not start <= game_date <= end_date or player_id not in metadata:
            continue
        if player_id not in players:
            players[player_id] = {
                **{key: metadata[player_id][key] for key in ('PLAYER_ID', 'PLAYER_NAME', 'TEAM_ABBREVIATION')},
                'GP': 0, **dict.fromkeys(KEYS, 0),
            }
        player = players[player_id]
        player['GP'] += 1
        for key, index in indexes.items():
            player[key] += game[index]
    return list(players.values())


@st.cache_data(show_spinner=False)
def strategy_snapshot(season='2026-27', days=None):
    if season not in ('2026-27','2025-26','blended-25') or days not in (None, 7, 14, 30):
        raise ValueError('賽季或期間不符')
    if season == '2025-26':
        return {**json.loads((ROOT/'ninecat_assets/data.json').read_text()), 'source': 'NBA Stats 上季例行賽快照'}
    current, games = official_2026_data()
    through = date.fromisoformat(games['through'])
    meta = {'fetchedAt': current['fetchedAt'], 'through': games['through']}
    if season == 'blended-25':
        logs = json.loads((ROOT/'ninecat_assets/game_logs_2025_26.json').read_text())
        totals = totals_from_games(current, games, through)
        return {**meta, 'season': '上季最後25場＋本季全部',
                'source': 'NBA 官方逐場數據 · 依實際出賽加權',
                'players': blended_players(logs, totals)}
    if days is None:
        return {**current, **meta, 'source': 'NBA Stats 本季例行賽場均快照'}
    from ninecat_model import KEYS
    rows = totals_from_games(current, games, through, days)
    players = [{**row, **{key: row[key] / row['GP'] for key in KEYS}} for row in rows]
    return {**meta, 'season': season, 'source': f'NBA 官方逐場數據 · 最近 {days} 天', 'players': players}
