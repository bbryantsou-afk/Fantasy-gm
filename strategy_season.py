"""Independent strategy season data; never replaces other features' baselines."""
import json
from pathlib import Path
from datetime import datetime,timezone
import streamlit as st
ROOT=Path(__file__).parent
@st.cache_data(ttl=21600,show_spinner=False)
def strategy_snapshot(season='2026-27'):
    if season not in ('2026-27','2025-26'):raise ValueError('賽季不符')
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
