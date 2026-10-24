"""Yahoo-displayed weekly acquisition usage, kept separate from manual preferences."""
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo

def quota_week(stamp):
    d=datetime.fromisoformat(stamp.replace('Z','+00:00')).astimezone(ZoneInfo('America/New_York')).date()
    return str(d-timedelta(days=d.weekday()))

def validate_quotas(values,teams):
    if not isinstance(values,dict):raise ValueError('加人額度格式不符')
    out={}
    for team,q in values.items():
        if team not in teams:continue
        if not isinstance(q,dict) or any(type(q.get(k)) is not int for k in ('used','limit')) or not 0<=q['used']<=q['limit']<=100:raise ValueError('加人額度不符')
        week=quota_week(q['updated_at'])
        out[team]={'used':q['used'],'limit':q['limit'],'remaining':q['limit']-q['used'],'week':week,'updated_at':q['updated_at']}
    return out
