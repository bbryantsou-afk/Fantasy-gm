"""Dated Fantasy lineups and observed daily totals. Missing data is never a forecast."""
from datetime import date,datetime,timedelta
from zoneinfo import ZoneInfo
import streamlit as st
from ninecat_model import KEYS
ACTIVE={'PG','SG','G','SF','PF','F','C','Util','UTIL'}
SIM_KEYS={'FG3M':'3PM','TOV':'TO'}
def player_key(row):return str(row.get('id') or ('fantasy:'+str(row.get('yahoo_id') or row['name'])))
def timestamp(value):
    try:return datetime.fromisoformat(value.replace('Z','+00:00')).timestamp()
    except (ValueError,TypeError,AttributeError):return 0

@st.cache_data(ttl=25,show_spinner=False)
def nba_official_today(day):
    import requests
    base='https://cdn.nba.com/static/json/liveData/'
    try:
        def get(path):
            r=requests.get(base+path,timeout=6);r.raise_for_status();return r.json()
        board=get('scoreboard/todaysScoreboard_00.json')['scoreboard']
        if board['gameDate']!=str(day):raise ValueError('NBA 比分日期與所選美東日期不同')
        players={};statuses=[]
        fields={'PTS':'points','FG3M':'threePointersMade','REB':'reboundsTotal','AST':'assists','STL':'steals','BLK':'blocks','TOV':'turnovers','FGM':'fieldGoalsMade','FGA':'fieldGoalsAttempted','FTM':'freeThrowsMade','FTA':'freeThrowsAttempted'}
        for game in board['games']:
            statuses.append({'比賽':game['awayTeam']['teamTricode']+' @ '+game['homeTeam']['teamTricode'],'狀態':game['gameStatusText']})
            if int(game['gameStatus'])==1:continue
            box=get('boxscore/boxscore_'+game['gameId']+'.json')['game']
            for side in ['homeTeam','awayTeam']:
                for p in box[side]['players']:
                    if str(p.get('played'))!='1':continue
                    players[str(p['personId'])]={'PLAYER_ID':str(p['personId']),'PLAYER_NAME':p['name'],'TEAM_ABBREVIATION':box[side]['teamTricode'],'GP':1,**{k:float(p['statistics'][v]) for k,v in fields.items()}}
        return {'players':players,'statuses':statuses,'updated_at':datetime.now().astimezone().isoformat(),'error':''}
    except Exception as exc:
        return {'players':{},'statuses':[],'updated_at':'','error':f'{type(exc).__name__}: '+str(exc)[:180]}

@st.cache_data(ttl=25,show_spinner=False)
def nba_today(day):
    from live_espn import espn_day
    try:
        result=espn_day(str(day))
        if not result.get('error'):return result
    except Exception as exc:
        result={'players':{},'statuses':[],'updated_at':'','error':type(exc).__name__}
    fallback=nba_official_today(day)
    if fallback['players']:return dict(fallback,source='NBA 即時暫存')
    return result

def roster_for_day(league,team,day):
    archive=league.get('daily_rosters',{}).get(str(day),{})
    return archive.get('teams',{}).get(team)

def observed_day(league,day,live=None):
    """Yahoo is the Fantasy authority. NBA may freshen today's observed player totals."""
    archive=league.get('daily_rosters',{}).get(str(day),{})
    players={};stamp=archive.get('captured_at','')
    for rows in archive.get('teams',{}).values():
        for r in rows:
            if r.get('daily_stats') is None:continue
            key=player_key(r)
            players[key]={'PLAYER_ID':key,'PLAYER_NAME':r['name'],'TEAM_ABBREVIATION':r.get('team',''),'GP':1,**r['daily_stats']}
    source='Yahoo 單日實績' if players or archive.get('stats_scope')=='day' else ''
    if live and live.get('updated_at') and live.get('players'):
        from live_espn import identity
        # Match names unambiguously across providers. ESPN IDs differ from NBA IDs.
        aliases={}
        for rows in archive.get('teams',{}).values():
            for r in rows:aliases.setdefault(identity(r['name']),set()).add(player_key(r))
        used=False
        for key,p in live['players'].items():
            matches=aliases.get(identity(p.get('PLAYER_NAME','')),set())
            if len(matches)>1:continue
            target=next(iter(matches)) if matches else key
            # Only Yahoo snapshots captured after this game was observed final can confirm it.
            final=p.get('final_seen_at')
            if target in players and ((final and timestamp(stamp)>=timestamp(final)) or timestamp(stamp)>=timestamp(live['updated_at'])):continue
            players[target]=dict(p,PLAYER_ID=target);used=True
        if used:
            stamp=live['updated_at'];source=live.get('source','NBA 即時比分')+('＋Yahoo 每日排陣／已確認實績' if archive else '')
    return {'players':players,'source':source,'updated_at':stamp,'archive':archive}

def fantasy_period(league,team,start,end,today,live=None):
    grouped={};missing=[];sources=set();stamp=''
    for i in range(max(0,(min(end,today)-start).days+1)):
        day=start+timedelta(days=i)
        dated_live=live.get('by_date',{}).get(str(day)) if live and 'by_date' in live else (live if day==today else None)
        evidence=observed_day(league,day,dated_live)
        rows=roster_for_day(league,team,day)
        if rows is None:missing.append(str(day));continue
        if not evidence['source']:missing.append(str(day));continue
        sources.add(evidence['source'])
        if timestamp(evidence['updated_at'])>timestamp(stamp):stamp=evidence['updated_at']
        for r in rows:
            if r.get('slot') not in ACTIVE:continue
            actual=evidence['players'].get(player_key(r))
            if not actual:continue
            key=player_key(r);dest=grouped.setdefault(key,{**actual,'GP':0,**dict.fromkeys(KEYS,0.)})
            dest['GP']+=1
            for k in KEYS:dest[k]+=actual[k]
    return list(grouped.values()),missing,'／'.join(sorted(sources)),stamp

def unverified_period(league,team,start,end,today,by_date):
    """Current roster NBA totals on dates lacking a Fantasy lineup; never score them."""
    from live_espn import identity
    roster=league.get('teams',{}).get(team,[]);grouped={}
    for i in range(max(0,(min(end,today)-start).days+1)):
        day=start+timedelta(days=i)
        if roster_for_day(league,team,day) is not None:continue
        live=by_date.get(str(day),{});matches={}
        for p in live.get('players',{}).values():matches.setdefault(identity(p['PLAYER_NAME']),[]).append(p)
        for row in roster:
            candidates=matches.get(identity(row['name']),[])
            if len(candidates)!=1:continue
            p=candidates[0];key=player_key(row)
            dest=grouped.setdefault(key,{'球員':row['name'],'NBA球隊':p['TEAM_ABBREVIATION'],'場次':0,**dict.fromkeys(KEYS,0.)})
            dest['場次']+=1
            for k in KEYS:dest[k]+=p[k]
    return list(grouped.values())

def simulator_defaults(league,my,opp,days,players):
    """Include traded/dropped historical players, map the two C and Util seats in order."""
    import copy
    pool=copy.deepcopy(players);lineups={}
    for day in days:
        slots={};known=False
        for side,team in [('my',my),('opp',opp)]:
            rows=roster_for_day(league,team,day)
            if rows is None:continue
            known=True;slots[side]={};counts={'C':0,'UTIL':0}
            for r in rows:
                pid=f"{side}-{r.get('id') or r['name']}"
                if r.get('slot') in ACTIVE and not any(p['id']==pid for p in pool[side]):
                    pool[side].append({'id':pid,'nba_id':int(r['id']) if str(r.get('id','')).isdigit() else None,'evidence_id':player_key(r),'name':r['name'],'team':r.get('team',''),'eligible':r.get('eligible',[]),'rank':len(pool[side])+1,'stats':{}})
                pos=r.get('slot');pos='UTIL' if pos in ['Util','UTIL'] else pos
                if pos not in ACTIVE and pos!='UTIL':continue
                if pos in counts:
                    counts[pos]+=1;pos+=str(counts[pos])
                if pos in ['C3','UTIL3']:raise ValueError('Fantasy 先發席次超出兩個 C／Util。')
                slots[side][pos]=pid
        if known:lineups[str(day)]=slots
    return pool,lineups

@st.fragment(run_every='30s')
def refresh_live_page():
    import time
    now=time.monotonic();last=st.session_state.setdefault('_live_page_tick',now)
    if now-last>=28:
        st.session_state['_live_page_tick']=now
        st.rerun(scope='app')
