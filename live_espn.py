"""Read observed ESPN boxscores; ESPN athlete IDs are never treated as NBA IDs."""
from datetime import datetime
import re
import unicodedata
import streamlit as st

def identity(name):
    text=''.join(c for c in unicodedata.normalize('NFKD',name).lower() if not unicodedata.combining(c))
    return re.sub(r'[^a-z0-9]','',re.sub(r'\b(jr|sr|ii|iii|iv)\b','',text))

def team_code(code):return {'SA':'SAS','NY':'NYK','GS':'GSW','NO':'NOP','UTAH':'UTA','WSH':'WAS'}.get(code,code)

@st.cache_resource
def final_observations():return {}

def parse_box(data, day, stamp, finals):
    header=data['header'];games=header['competitions']
    if datetime.fromisoformat(games[0]['date'].replace('Z','+00:00')).astimezone(__import__('zoneinfo').ZoneInfo('America/New_York')).date().isoformat()!=day:
        raise ValueError('ESPN 比賽日期不符')
    complete=games[0]['status']['type'].get('completed',False)
    event=str(header['id'])
    if complete:finals.setdefault(event,stamp)
    result={}
    for team in data.get('boxscore',{}).get('players',[]):
        for group in team['statistics']:
            for p in group['athletes']:
                if p.get('didNotPlay') or not p.get('stats'):continue
                values=dict(zip(group['labels'],p['stats']))
                try:
                    stats={k:float(values[v]) for k,v in {'PTS':'PTS','REB':'REB','AST':'AST','STL':'STL','BLK':'BLK','TOV':'TO'}.items()}
                    for field,keys in [('FG',('FGM','FGA')),('FT',('FTM','FTA')),('3PT',('FG3M','FG3A'))]:
                        made,attempt=map(float,values[field].split('-'))
                        if not 0<=made<=attempt:raise ValueError('Invalid shooting totals')
                        stats.update(zip(keys,(made,attempt)))
                    if any(v<0 for v in stats.values()):raise ValueError('Negative totals')
                except (KeyError,ValueError):continue
                name=p['athlete']['displayName'];key='espn:'+str(p['athlete']['id'])
                result[key]={'PLAYER_ID':key,'PLAYER_NAME':name,'TEAM_ABBREVIATION':team_code(team['team']['abbreviation']),'GP':1,**stats,'final_seen_at':finals.get(event,'') if complete else ''}
    return result

@st.cache_data(ttl=25,show_spinner=False)
def espn_day(day):
    import requests
    base='https://site.api.espn.com/apis/site/v2/sports/basketball/nba/'
    def get(path):
        r=requests.get(base+path,timeout=8);r.raise_for_status();return r.json()
    players={};statuses=[];errors=[];scheduled=[];stamp=datetime.now().astimezone().isoformat()
    board=get('scoreboard?dates='+day.replace('-',''))
    for event in board.get('events',[]):
        status=event['status']['type'];statuses.append({'比賽':event['name'],'狀態':status['description']})
        if status.get('state')=='pre':
            scheduled.extend(team_code(c['team']['abbreviation']) for c in event.get('competitions',[{}])[0].get('competitors',[]))
            continue
        try:players.update(parse_box(get('summary?event='+event['id']),day,stamp,final_observations()))
        except Exception as exc:errors.append(type(exc).__name__)
    return {'players':players,'statuses':statuses,'scheduled_teams':sorted(set(scheduled)),'updated_at':stamp if players else '', 'source':'ESPN 即時暫存','error':'／'.join(errors)}
