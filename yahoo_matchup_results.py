"""Validated official weekly category totals transported by the user's browser."""
import copy
from datetime import date,datetime,timedelta
from data_center import validate_totals

def import_results(raw,league,mapping,expected):
    if not isinstance(raw,dict) or type(raw.get('week')) is not int or not 1<=raw['week']<=40:raise ValueError('Yahoo 官方比分週次不符。')
    start,end=date.fromisoformat(raw['start']),date.fromisoformat(raw['end'])
    if not 0<=(end-start).days<=20:raise ValueError('Yahoo 官方比分日期不符。')
    stamp=datetime.fromisoformat(raw['capturedAt'].replace('Z','+00:00'))
    if stamp.tzinfo is None:raise ValueError('Yahoo 官方比分時間不符。')
    rows=raw.get('teams')
    if not isinstance(rows,list) or len(rows)!=len(expected):raise ValueError('Yahoo 官方比分隊伍不完整。')
    teams={}
    for r in rows:
        team=mapping.get(league+':'+str(r['id']));opp=mapping.get(league+':'+str(r['opponent']))
        if team not in expected or opp not in expected or team==opp or team in teams:raise ValueError('Yahoo 官方比分球隊配對不符。')
        teams[team]={'opponent':opp,'totals':validate_totals(r['totals'])}
    if set(teams)!=set(expected) or any(teams[r['opponent']]['opponent']!=t for t,r in teams.items()):raise ValueError('Yahoo 官方比分對手未互相對應。')
    monday=start-timedelta(days=start.weekday())
    return str(monday),{'week':raw['week'],'start':str(start),'end':str(end),'updated_at':raw['capturedAt'],'teams':teams,'source':'Yahoo 官方對局總表'}

def merge_into_store(data,league,today):
    for key,week in league.get('yahoo_matchups',{}).items():
        old=data['weeks'].get(key,{})
        if old.get('source')=='Yahoo 官方對局總表' and old.get('updated_at','')>=week['updated_at']:
            old['final']=date.fromisoformat(week['end'])<today
            continue
        row=copy.deepcopy(week);row['final']=date.fromisoformat(week['end'])<today
        data['weeks'][key]=row
    return data


def validate_stored_results(weeks,teams):
    from data_center import checked_week
    if not isinstance(weeks,dict) or len(weeks)>40:raise ValueError('Yahoo 比分備份格式不符。')
    out={}
    for key,week in weeks.items():
        monday=date.fromisoformat(key);start=date.fromisoformat(week['start']);end=date.fromisoformat(week['end'])
        if monday!=start-timedelta(days=start.weekday()) or not 0<=(end-start).days<=20:raise ValueError('Yahoo 比分備份日期不符。')
        stamp=datetime.fromisoformat(week['updated_at'].replace('Z','+00:00'))
        if stamp.tzinfo is None or type(week['week']) is not int or not 1<=week['week']<=40:raise ValueError('Yahoo 比分備份週次不符。')
        rows=[{'team':t,'opponent':r['opponent'],**r['totals']} for t,r in week['teams'].items()]
        out[key]={'week':week['week'],'start':week['start'],'end':week['end'],'updated_at':week['updated_at'],'teams':checked_week(rows,teams),'source':'Yahoo 官方對局總表'}
    return out
