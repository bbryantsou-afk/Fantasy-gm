"""Keep confirmed dated Yahoo roster slots immutable; permit stat corrections."""
import copy
from datetime import date,datetime
from zoneinfo import ZoneInfo

def store_day(previous,teams,day,captured,today,version=0):
    stamp=datetime.fromisoformat(captured.replace('Z','+00:00'))
    capture_day=stamp.astimezone(ZoneInfo('America/New_York')).date()
    confirmed=version>=3 and date.fromisoformat(day)<min(capture_day,today)
    old=previous or {}
    if old.get('roster_state')=='final' and old.get('roster_version')==3 and set(old.get('teams',{}))==set(teams):
        result=copy.deepcopy(old)
        def key(r):return str(r.get('yahoo_id') or r.get('id') or r['name'])
        for team,rows in result['teams'].items():
            fresh={key(r):r for r in teams[team]}
            for row in rows:
                newer=fresh.get(key(row),{})
                for field in ('daily_stats','game_status'):
                    if field in newer and newer[field] is not None:row[field]=copy.deepcopy(newer[field])
        result['stats_updated_at']=captured
        return result
    return {'teams':copy.deepcopy(teams),'captured_at':captured,'source':'Yahoo browser snapshot',
            'roster_state':'final' if confirmed else 'provisional','roster_version':3 if version>=3 else 0,
            'roster_verified_at':captured if confirmed else '', 'stats_updated_at':captured}
