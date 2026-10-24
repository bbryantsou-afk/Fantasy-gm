"""Independent strategy season data; never replaces other features' baselines."""
import json
from pathlib import Path
from datetime import datetime,timezone
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

@st.cache_data(ttl=21600,show_spinner=False)
def current_totals():
    try:
        from nba_api.stats.endpoints import leaguedashplayerstats
        from ninecat_model import KEYS
        f=leaguedashplayerstats.LeagueDashPlayerStats(season='2026-27',season_type_all_star='Regular Season',per_mode_detailed='Totals',timeout=18).get_data_frames()[0]
        rows=json.loads(f[['PLAYER_ID','PLAYER_NAME','TEAM_ABBREVIATION','GP','MIN',*KEYS]].to_json(orient='records'))
        if not rows:raise ValueError('尚無數據')
        return {'fetchedAt':datetime.now(timezone.utc).isoformat(),'players':rows}
    except Exception:
        return json.loads((ROOT/'ninecat_assets/totals_2026_27.json').read_text())

@st.cache_data(ttl=21600,show_spinner=False)
def strategy_snapshot(season='2026-27'):
    if season not in ('2026-27','2025-26','blended-25'):raise ValueError('賽季不符')
    if season=='blended-25':
        current=current_totals()
        logs=json.loads((ROOT/'ninecat_assets/game_logs_2025_26.json').read_text())
        return {'season':'上季最後25場＋本季全部','fetchedAt':current['fetchedAt'],'players':blended_players(logs,current['players'])}
    if season=='2025-26':return json.loads((ROOT/'ninecat_assets/data.json').read_text())
    try:
        from player_detail_v14 import league_stats
        from ninecat_model import KEYS
        frame=league_stats(season)
        rows=json.loads(frame[['PLAYER_ID','PLAYER_NAME','TEAM_ABBREVIATION','GP','MIN',*KEYS]].to_json(orient='records'))
        if not rows:raise ValueError('本季尚無資料')
        return {'season':season,'fetchedAt':datetime.now(timezone.utc).isoformat(),'players':rows}
    except Exception:
        return json.loads((ROOT/'ninecat_assets/data_2026_27.json').read_text())
