"""Season-aware trading prior. Draft is a league preference, not an objective price."""
import math,statistics
from datetime import date,datetime
from zoneinfo import ZoneInfo
import json
from pathlib import Path
import streamlit as st
from ninecat_model import CATS,KEYS,weighted_z
from dashboard_model import aggregate_logs

OPENING=date(2026,10,20)
ROOT=Path(__file__).resolve().parent
CACHE=ROOT/'ninecat_assets/game_logs_2026_27.json'

def market_model(pool,entries,ref,logs=(),asof=None):
    asof=asof or datetime.now(ZoneInfo('America/New_York')).date()
    picks={str(e['playerId']):i+1 for i,e in enumerate(entries) if e.get('playerId') is not None}
    eq={c:1 for c in CATS}
    old={k:weighted_z(p,ref,eq) for k,p in pool.items()}
    known=[k for k in pool if k in picks]
    raw=lambda pick:math.log((len(entries)+1)/(pick+.5))
    prior_raw=[raw(picks[k]) for k in known]
    mean=statistics.mean(prior_raw) if prior_raw else 0
    sd=statistics.pstdev(prior_raw) if len(prior_raw)>1 else 1
    old_mean=statistics.mean(old[k] for k in known) if known else 0
    old_sd=statistics.pstdev(old[k] for k in known) if len(known)>1 else 1
    current=aggregate_logs(logs,OPENING,asof) if asof>=OPENING else []
    actual={str(p['PLAYER_ID']):p for p in current}
    prices={};details={};effective={}
    for k,p in pool.items():
        record=actual.get(k);gp=int(record['GP']) if record else 0
        evidence=gp/(gp+20)
        draft_weight=.3*(1-evidence)
        historical_weight=.7*(1-evidence)
        draft=old_mean+(raw(picks.get(k,len(entries)+1))-mean)/(sd or 1)*(old_sd or 1)
        observed={**p,**{c:record[c]/gp for c in KEYS}} if gp else p
        new_score=weighted_z(observed,ref,eq) if gp else old[k]
        prices[k]=draft_weight*draft+historical_weight*old[k]+evidence*new_score
        effective[k]={**p,**{c:(1-evidence)*p[c]+evidence*observed[c] for c in KEYS}}
        details[k]={'pick':picks.get(k),'gp':gp,'draft_weight':draft_weight,'historical_weight':historical_weight,
                    'actual_weight':evidence,'draft_score':draft,'historical_score':old[k],'actual_score':new_score if gp else None,'value':prices[k]}
    return prices,details,effective

@st.cache_data(ttl=21600,show_spinner=False)
def current_logs(asof_iso):
    asof=date.fromisoformat(asof_iso)
    if asof<OPENING:
        return [],'開季前，尚無2026–27例行賽實績。',''
    saved={}
    if CACHE.exists():
        try:
            saved=json.loads(CACHE.read_text())
            if isinstance(saved,list):saved={'games':saved}
        except (ValueError,OSError):saved={}
    if saved.get('fetched_day')==asof_iso:
        return saved.get('games',[]),'',saved.get('fetched_at','')
    try:
        from nba_api.stats.endpoints.leaguegamelog import LeagueGameLog
        frame=LeagueGameLog(season='2026-27',player_or_team_abbreviation='P',season_type_all_star='Regular Season',timeout=15).get_data_frames()[0]
        needed=['PLAYER_ID','PLAYER_NAME','TEAM_ABBREVIATION','GAME_ID','GAME_DATE',*KEYS]
        if frame.empty:
            return [],'官方尚未回傳本季實績；維持選秀與歷史基準。',''
        frame=frame[needed]
        if frame.duplicated(['PLAYER_ID','GAME_ID']).any():
            raise ValueError('duplicate game rows')
        games=json.loads(frame.to_json(orient='records',date_format='iso'))
        stamp=datetime.now(ZoneInfo('Asia/Singapore')).isoformat()
        payload={'season':'2026-27','fetched_day':asof_iso,'fetched_at':stamp,'games':games}
        try:
            temp=CACHE.with_suffix('.tmp')
            temp.write_text(json.dumps(payload))
            temp.replace(CACHE)
        except OSError:
            return games,'本次實績可用，但快取未能儲存。',stamp
        return games,'',stamp
    except Exception as exc:
        if saved.get('games'):
            return saved['games'],'官方連線暫時失敗，使用最近實績快取；未補造新場次。',saved.get('fetched_at','')
        return [],'官方實績暫時無法取得，維持選秀與歷史基準；不依日曆自動降低選秀權重。',''
